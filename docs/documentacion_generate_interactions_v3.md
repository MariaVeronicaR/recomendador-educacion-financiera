# Documentación: `data/scripts/generate_interactions_v3.py`

**TFM:** Plataforma inteligente para la recomendación personalizada de contenidos en educación financiera basada en IA  
**Fichero:** `data/scripts/generate_interactions_v3.py`  
**Propósito:** Genera el dataset de interacciones sintéticas `data/interactions_synthetic_v3.csv`, que es el fichero de entrada principal del evaluador `src/utils/evaluate_models.py`.

---

## 1. Rol en el pipeline

El evaluador de modelos (`evaluate_models.py`) entrena y valida los recomendadores sobre `interactions_synthetic_v3.csv`. Este script es el que **construye ese dataset desde cero**, sin leer ningún dataset de interacciones previo, a partir de los ficheros de catálogo y perfiles:

```
users_synthetic.csv ─┐
contents.csv ────────┤
concepts.csv ───────┼─► generate_interactions_v3.py ─► interactions_synthetic_v3.csv ─► evaluate_models.py
content_concept_map ─┤
prerequisites.csv ───┘
```

---

## 2. Datos de Entrada

| Fichero | Contenido |
| :--- | :--- |
| `data/users_synthetic.csv` | Perfiles reales de españoles 18-34 (muestreados de la ECF 2021 del Banco de España). |
| `data/contents.csv` | Catálogo de contenidos educativos (título, resumen, objetivo, topic, dificultad, formato). |
| `data/concepts.csv` | Conceptos de conocimiento del grafo pedagógico. |
| `data/content_concept_map.csv` | Asociación contenido → concepto (solo se usa la cobertura `directa`). |
| `data/prerequisites.csv` | Grafo de prerrequisitos entre conceptos. |

---

## 3. Diseño Metodológico

El generador implementa siete principios de diseño para producir datos realistas y con señal suficiente para entrenar modelos de deep learning:

### 3.1. Población realista
Cada usuario hereda su perfil ECF (conocimiento financiero, hábito de ahorro, experiencia inversora, `learning_goal`, edad, sexo). De ese perfil se deriva un **vector de interés por topic** y una **dificultad preferida**.

### 3.2. Long-tail de engagement
El número de interacciones por usuario sigue una distribución long-tail (pocos muy activos, muchos ligeros) con media ~25. La intensidad correlaciona con el perfil: más conocimiento + ahorro + interés inversor ⇒ usuario más activo. Esto replica la realidad y da señal a los modelos colaborativos.

### 3.3. Popularidad long-tail de contenido
Cada contenido tiene un **atractivo base** (topic popular, formato accesible, dificultad). La probabilidad de interacción es proporcional a ese atractivo, generando el sesgo de popularidad real.

### 3.4. Matching usuario-contenido
```
prob_interact = atractivo_base × topic_match × difficulty_match × formato_pref
```
Un usuario interactúa más con lo que le interesa y le queda a su nivel.

### 3.5. Secuenciación pedagógica (lo diferencial)
La restricción de prerrequisitos se aplica al **evento de dominio** (`completed` / `quiz_passed`), **no** al `view`. Un usuario puede *ver* cualquier contenido (exploración, `score < 0.5`), pero solo *completa* o *aprueba* un contenido si ya domina los prerrequisitos de sus conceptos. Esto genera caminos de aprendizaje realistas y un PVR (Prerequisite Violation Rate) medible y coherente.

### 3.6. Patrones temporales
Las interacciones se agrupan en sesiones con timestamps crecientes (minutos dentro de una sesión, días entre sesiones), con decaimiento de engagement. Distingue acciones pasivas (`view`) de activas (`completed`/`quiz`).

### 3.7. Esquema de salida (implicit feedback enriquecido)
```
user_id, content_id, timestamp, event, score, time_spent_seconds, session_id, is_recommended
```

---

## 4. Esquema de Salida

| Columna | Tipo | Descripción |
| :--- | :--- | :--- |
| `user_id` | str | Identificador del usuario. |
| `content_id` | str | Identificador del contenido. |
| `timestamp` | datetime | Marca temporal de la interacción. |
| `event` | str | `view` \| `started` \| `completed` \| `quiz_passed` \| `quiz_failed`. |
| `score` | float (0-1) | Los eventos de dominio (`completed`/`quiz_passed`) tienen `score >= 0.5` (relevantes); los pasivos (`view`/`started`) `score < 0.5`. |
| `time_spent_seconds` | int | Segundos dedicados según evento y formato. |
| `session_id` | str | Identificador de sesión (`{user_id}-S{nn}`). |
| `is_recommended` | int | `1` si la interacción vino de una recomendación del sistema (sesgo de posición/popularidad), `0` si fue exploración autónoma. |

> **Relevancia para el evaluador:** el umbral `score >= 0.5` es exactamente el que `evaluate_models.py` usa para definir el *ground truth* de relevancia en Test. La coherencia entre generador y evaluador es deliberada.

---

## 5. Componentes Clave

### 5.1. Perfil de interés por topic (`GOAL_TOPICS`)
Cada `learning_goal` activa un conjunto de topics con pesos. Ejemplos:

*   `prepararse para invertir` → inversión (1.0), mercado (0.9), riesgo (0.8), diversificación (0.8)…
*   `ahorrar` → ahorro (1.0), planificación (0.8), cuentas bancarias (0.7)…
*   `entender deuda` → deuda (1.0), préstamos (0.9), hipotecas (0.8), tarjetas (0.7)…

### 5.2. Dificultad preferida (`KNOWLEDGE_DIFFICULTY`)
Según el nivel de conocimiento financiero:

*   `bajo` → básico (1.0), intermedio (0.4), avanzado (0.1).
*   `medio` → básico (0.8), intermedio (1.0), avanzado (0.4).
*   `alto` → básico (0.5), intermedio (0.9), avanzado (1.0).
*   `NaN` (NS/NC en Big3) → perfil conservador: básico/intermedio.

### 5.3. Intensidad de engagement (`engagement_intensity`)
Factor de actividad en `[0.5, 2.0]` derivado del perfil ECF: conocimiento alto (×1.3), ahorro frecuente (×1.15), experiencia inversora básica (×1.2), objetivo de invertir (×1.15), grupo 18-24 (×1.1).

### 5.4. Número de interacciones (`sample_n_interactions`)
Base log-normal centrada en ~22 (`lognormal(mean=ln 22, sigma=0.55)`), escalada por la intensidad y recortada a `[4, 70]`.

### 5.5. Atractivo de contenido (`content_attractiveness`)
`topic_popularity × formato_pref × dificultad × ruido log-normal`. Se normaliza a `[0, 1]` para usarlo como probabilidad base.

### 5.6. Selección de contenido
Con probabilidad 0.85 se elige entre los contenidos **accesibles** (prerrequisitos dominados); con 0.15 se explora (puede ver contenido no accesible). Se pondera por matching con ruido y una **penalización por revisita** (×0.25) para no saturar de pares duplicados.

### 5.7. Evento y dominio (`pick_event`)
*   Si el contenido **no** es accesible → solo `view`/`started` (score < 0.5).
*   Si **sí** es accesible → con probabilidad lo completa/aprueba (dominio, score ≥ 0.5).

### 5.8. Conocimiento inicial (`initial_mastered`)
Los conceptos raíz (sin prerrequisitos) se consideran ya dominados si el usuario tiene conocimiento `alto`; parcialmente (2 raíces) si es `medio`. El muestreo para nivel `medio` usa una semilla derivada del `user_id` (no el RNG global) para que **generación y validación obtengan siempre el mismo resultado**.

---

## 6. Reproducibilidad

*   `RNG = random.Random(42)` y `NPRNG = np.random.default_rng(42)`.
*   El conocimiento inicial de nivel `medio` usa `random.Random(str(uid))` (semilla por usuario), independiente del estado secuencial del RNG.

---

## 7. Validación de Calidad (al final del script)

El script imprime una auditoría del dataset generado:

*   **Volumen:** total de interacciones, usuarios, contenidos con interacción, media/mediana por usuario, sparsity, % de positivos.
*   **Distribución de eventos** (normalizada).
*   **Long-tail de popularidad** (top 5 contenidos y nº de contenidos con <10 interacciones).
*   **PVR (Prerequisite Violation Rate):** debe ser **0.0%** por construcción, ya que la validación replica el mismo `initial_mastered` que la generación.
*   **Correlación conocimiento → dificultad** (media de dificultad dominada por nivel).
*   **Cobertura por topic.**

---

## 8. Uso

```bash
python3 data/scripts/generate_interactions_v3.py
```

**Requisitos:** `pandas`, `numpy`.

---

## 9. Notas

*   Existen versiones anteriores del generador en `data/scripts/` (`generate_interactions_v2.py`, `generate_interactions_realistic.py`) y en `archive/scripts_v1_v2/`. El evaluador actual usa la **v3**.
*   `generate_interactions_v4.py` es idéntico en tamaño a la v3 (misma longitud de archivo); la v3 es la que referencia el evaluador.
*   El dataset resultante (`interactions_synthetic_v3.csv`, ~3.7 MB) alimenta directamente el split Train/Test y Cold Start del evaluador.
