# Datos de usuario para la aplicación con los modelos ganadores

Fecha: 2026-08-30
Contexto: la aplicación utilizará los modelos ganadores de la evaluación — **NeuMF** (warm start) y **NeuMF-Profile** (cold start). Este documento define qué datos de usuario necesita la app.

---

## Los dos modelos ganadores consumen datos distintos

| Escenario | Modelo | Datos que consume |
|---|---|---|
| **Cold start** (usuario nuevo, sin historial) | NeuMF-Profile | **Perfil** (features de `users_synthetic.csv`) + contenido |
| **Warm start** (usuario con historial) | NeuMF | **Historial de interacciones** (embeddings user_id/content_id) |

La aplicación necesita **ambas cosas**: el perfil para el arranque en frío y el registro de interacciones para los usuarios con historial (y para reentrenar).

---

## 1. Datos de perfil (para cold start / NeuMF-Profile)

El modelo consume exactamente las columnas de `users_synthetic.csv`:

- `age_group` (18-24 / 25-34)
- `education_level`
- `employment_status`
- `financial_knowledge_level` (bajo / medio / alto / NaN)
- `saving_habit`
- `debt_experience`
- `investment_experience`
- `financial_behavior_level`
- `financial_attitude_level`
- `learning_goal`
- `sex`

**Punto clave:** no pedir estas categorías directamente. Varias se **derivan** de preguntas más simples, como hace el generador:

- `financial_knowledge_level` ← las **3 preguntas Big3** de Lusardi (inflación, interés compuesto, diversificación). Preguntar esas 3 y derivar el nivel.
- `saving_habit` y `financial_behavior_level` ← una pregunta sobre hábito de ahorro.
- `investment_experience` ← una pregunta sobre si ha invertido.
- `education_level`, `employment_status`, `age_group`, `sex` ��� preguntas directas.

**Cuidado con tres campos que el generador asigna con aleatoriedad** (`np.random.choice`): `debt_experience`, `financial_attitude_level` y `learning_goal`. No se pueden reproducir de forma determinista desde las demás. Para la app, definirlos de forma determinista (o preguntarlos directamente) — el modelo no necesita que coincidan con el generador, solo que el vector de features esté lleno de forma coherente.

**Matiz importante:** el modelo está entrenado para tolerar datos faltantes. El 51% de los usuarios sintéticos tienen `financial_knowledge_level = NaN`, y `build_profile_features` rellena lo categórico con `"unknown"`. Es decir, se puede arrancar con un onboarding **mínimo** (p. ej. solo `learning_goal` y `age_group`) y aun así obtener recomendaciones de cold start razonables, e ir completando el perfil con el tiempo.

**No re-derivar las features en la app:** el vector que alimenta al modelo debe construirse con el mismo `build_profile_features` y, sobre todo, con el **mismo OneHotEncoder y las mismas medias/desviaciones de normalización con que se entrenó**. Si se recalcula por usuario, el espacio de features no coincide con el entrenamiento. Hay que serializarlo junto al modelo.

---

## 2. Datos de interacción (para warm start / NeuMF y para reentrenar)

NeuMF aprende embeddings de `user_id` × `content_id` a partir del historial. La app debe **registrar cada evento** con el mismo esquema de `interactions_synthetic_v3.csv`:

- `user_id`, `content_id`
- `timestamp`
- `event` (view / started / completed / quiz_passed / quiz_failed)
- `score` (relevancia, con la convención ya corregida: solo completed/quiz_passed ≥ 0.5)
- `time_spent_seconds`
- `session_id`
- `is_recommended`

Esto es doblemente útil: sirve para recomendar a usuarios warm y es la **materia prima para reentrenar** el modelo cuando se acumulen interacciones reales (lo que de verdad importa a largo plazo, porque el modelo se entrenó con datos sintéticos).

---

## 3. Datos del catálogo y del grafo pedagógico (para servir y secuenciar)

La app necesita el catálogo con los mismos campos que usa el modelo de contenido (TF-IDF de `title` + `summary`, `topic`, `difficulty`, `format`). Y, para aprovechar el diferenciador pedagógico del TFM, también el grafo de prerrequisitos:

- `concepts.csv`
- `content_concept_map.csv`
- `prerequisites.csv`

Con eso se puede, en tiempo real, **no recomendar como "completable" un contenido cuyos prerrequisitos el usuario no domina** — exactamente la lógica de PVR que el generador construye. Es lo que hace que la app sea un "recomendador de educación financiera" y no un Netflix de artículos.

---

## 4. Vacíos que la app debe resolver (los modelos ganadores no los cubren)

- **Contenido nuevo (item cold start):** tanto NeuMF como NeuMF-Profile usan embeddings de `content_id` aprendidos del entrenamiento. **Un contenido que no estaba en el entrenamiento no tiene embedding** — la app necesita un fallback (p. ej. recomendar por TF-IDF/perfil de contenido hasta reentrenar). Es el hueco más importante a planificar.
- **Feedback loop:** `is_recommended` y los eventos reales deben volver al modelo para reentrenar; si no, las recomendaciones se quedan congeladas en lo aprendido de datos sintéticos.

---

## Resumen práctico

Para el onboarding, pedir **pocas preguntas**: las 3 Big3 (para derivar conocimiento), hábito de ahorro, experiencia inversora, edad, educación y objetivo de aprendizaje (`learning_goal`). Derivar el resto de forma determinista. Registrar **cada interacción** con el esquema de eventos. Guardar el **OneHotEncoder + stats de normalización** junto al modelo. Y tener un **fallback de contenido** para ítems nuevos.
