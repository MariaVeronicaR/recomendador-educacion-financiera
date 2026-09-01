# Plan de adaptación de la plataforma al proyecto

Fecha: 2026-08-30
Contexto: `plataforma/` es un prototipo (backend FastAPI + frontend React/Vite + schema Supabase) construido antes de decidir los modelos ganadores. Este plan lo adapta al resto del proyecto, que usará **NeuMF** (warm start) y **NeuMF-Profile** (cold start) como modelos ganadores.

---

## Análisis previo

### Lo que ya está bien (reutilizable)
- **Arquitectura desacoplada**: interfaces `Recomendador` / `GrafoPedagogico`, factory por configuración (`RECO_MODEL`, `GRAPH_BACKEND`). Cambiar de modelo = cambiar una variable de entorno.
- **Orquestador** (`orquestador.py`): ranking crudo → filtro pedagógico → explicación.
- **Grafo pedagógico** (`inmemory.py`): carga los CSV y valida prerrequisitos.
- **Frontend**: cuestionario con las Big Three de Lusardi, registro de progreso, conceptos dominados, explicaciones.
- **Supabase schema**: `profiles`, `interactions`, `progress`, `mastered_concepts`, con RLS.

### Problemas a resolver
1. **CRÍTICO — El backend no arranca**: importa de `evaluate_models` funciones que no existen en el harness actual (`load_data`, `baseline_content_based`, `baseline_most_popular`, `baseline_kg_rules`, `compute_mastery`). Se construyó contra una versión antigua del harness.
2. **El modelo ganador no está integrado**: `ml.py` define `NeumfRecomendador` y `FeatureAwareNeumfRecomendador` pero la carga de checkpoint es `NotImplementedError`. NeuMF/NeuMF-Profile no están serializados ni hay código que los cargue.
3. **La lógica pedagógica difiere del generador**: el orquestador dice "accesible si dominas al menos un prerrequisito de cada concepto"; el generador exige dominar **todos** los prerrequisitos de todos los conceptos. El PVR=0 validado en los datos no se preserva en la app.
4. **`datos.py` acoplado al harness**: espera un `load_data()` que no existe; el harness es un script de evaluación, no una librería estable.
5. **Discrepancias menores**: `plan_aplicacion_tfm.md` no existe (los README lo referencian); `data/structured/` sí existe; `plataforma/` no está trackeada en git.

---

## Plan por fases

### Fase 1 — Desacoplar el backend del harness (arregla el bloqueo crítico)
- Crear un módulo de datos propio (`app/datos.py`) que **lea directamente los CSV** (`contents.csv`, `concepts.csv`, `content_concept_map.csv`, `prerequisites.csv`) en vez de importar funciones inexistentes de `evaluate_models`.
- **Reimplementar los baselines de forma autónoma** (decisión del usuario): `most_popular` (frecuencia de interacción) y `content_based` (coseno topic-interés), sin depender de `em.baseline_*`.
- **Resultado:** el backend arranca, los tests de la Fase 1 pasan, y el frontend vuelve a funcionar con `content_based`.

### Fase 2 — Integrar los modelos ganadores (NeuMF + NeuMF-Profile) ✅ HECHA
- Extraer del harness las clases `NeuMF`, `NeuMFProfile` y el preprocesado (`build_profile_features`, mapeos user/item, normalización) a un módulo reutilizable, sin tocar el script de evaluación.
- **Serializar los modelos entrenados** en `models/`: `state_dict` de NeuMF-Profile, **transformador de features** (media/std/one-hot), y meta (mapeos content_id->idx, profile cols).
- Implementar la carga de checkpoint en `ml.py` (`NeumfProfileRecomendador`, `NeumfRecomendador`), con fallback a popularidad para ítems sin embedding.
- **Resultado:** `RECO_MODEL=neumf_profile` (cold start, modelo servible hoy) funciona y rankea todo el catálogo.

**Nota de diseño (importante):** NeuMF (warm) aprende embeddings de `user_id` sobre los usuarios sintéticos `U0001`–`U1916`. Un usuario real de la app (UUID de Supabase) no está en ese mapeo, así que NeuMF warm **no es servible para usuarios nuevos** sin reentrenar con interacciones reales. El modelo servible hoy es **NeuMF-Profile** (cold start), que funciona por features de perfil. NeuMF warm queda documentado como "requiere reentrenar" (Fase 4, feedback loop).

**Artefactos generados** en `plataforma/backend/models/`:
- `neumf_profile.pt` — state_dict del modelo
- `neumf_profile_features.json` — transformador de features serializable
- `neumf_profile_meta.json` — meta (content_ids, item_to_idx, feature_dim, profile_cols)

**Script de entrenamiento:** `plataforma/backend/scripts/train_serving_models.py` (reproduce el split cold y los hiperparámetros de la evaluación).

### Fase 3 — Alinear la lógica pedagógica y los datos de perfil ✅ HECHA
- Corregir `is_accessible` en `inmemory.py` (y `neo4j.py`) para que exija dominar **todos** los prerrequisitos de todos los conceptos, como el generador. Verificado: 0 mismatches contra `concepts_mastered_for` del generador (200 muestras × 104 contenidos).
- Alinear `UserProfile` con las columnas reales de `users_synthetic.csv`: añadidos `learning_goal`, `saving_habit`, `investment_experience`, `debt_experience`, `financial_behavior_level`, `financial_attitude_level`. `_profile_to_row` los mapea al transformador.
- Extender el cuestionario para recoger `learning_goal` (el campo más informativo para NeuMF-Profile). Schema de Supabase + migración `migracion_learning_goal.sql` + tipos de frontend actualizados. Un perfil completo cambia el ranking en 28/104 posiciones frente a uno mínimo.
- **Resultado:** el perfil que manda el frontend alimenta correctamente a NeuMF-Profile (los campos no recogidos se imputan con mediana/"unknown", coherente con el onboarding mínimo).

### Fase 4 — Cerrar el feedback loop y el item cold start ✅ HECHA
- Registrar interacciones con el **esquema de eventos** del generador (`view/started/completed/quiz_passed/quiz_failed` + `score`). Reescribida la tabla `interactions` de Supabase (migración `migracion_interacciones_eventos.sql`) y creado el helper `frontend/src/lib/events.ts` que asigna el score coherente con el evento. El frontend registra: `view` al abrir un contenido, `quiz_failed` al fallar el quiz, `quiz_passed` al aprobarlo, `completed` al marcar completado (con `is_recommended=true`).
- **Feedback loop:** el historial real de interacciones ahora tiene el formato del generador, así que se puede reentrenar NeuMF-Profile con datos reales (mismo script `train_serving_models.py`, apuntando al CSV consolidado de interacciones reales).
- **Item cold start:** creado `app/recomendadores/fallback.py` (`TfidfFallback`, TF-IDF sobre `title`+`summary`). Integrado en `NeumfProfileRecomendador`: los contenidos nuevos (sin embedding en el modelo) se rankean por TF-IDF al perfil y se intercalan al final del ranking. Verificado: NeuMF-Profile rankea los 104 contenidos del catálogo.
- **Resultado:** la app puede reentrenar con datos reales y no se rompe con contenido nuevo.

### Fase 5 — Limpieza y documentación ✅ HECHA
- Crear `docs/plan_aplicacion_tfm.md` (el que los README referencian y no existía). Documenta arquitectura, modelos, entrenamiento, feedback loop, endpoints, datos de usuario y despliegue.
- `plataforma/` **sí está trackeada** en git (se verificó). Se creó `plataforma/backend/.gitignore` para excluir `.venv/`, `models/` (artefactos regenerables), `__pycache__/`, `.pytest_cache/` y `.env`. El frontend ya tenía `.gitignore` (node_modules, dist, .env.local).
- Actualizar READMEs para reflejar los modelos reales (NeuMF-Profile, no "feature_aware_neumf") y quitar la referencia a "Fase 7" inexistente.

---

## Decisión del usuario
Reimplementar los baselines de forma autónoma en la Fase 1 (desacoplarlos del todo del harness), en lugar de eliminarlos o solo cablear los modelos ML.
