# Documentación: `data/scripts/generate_interactions.py`

Generador de interacciones sintéticas usuario–contenido para un sistema de recomendación de educación financiera. Implementa el plan técnico [`docs/plan_generar_interacciones.md`](plan_generar_interacciones.md) y las correcciones de [`docs/plan_ajustes_generador_interacciones.md`](plan_ajustes_generador_interacciones.md).

La data generada alimenta la comparativa de modelos de recomendación (ver [`docs/Comparativa_modelos_recomendacion.md`](Comparativa_modelos_recomendacion.md)).

---

## 1. Propósito

Producir un dataset de interacciones sintéticas de alta calidad entre usuarios jóvenes españoles (18–34) y contenidos de educación financiera, apto para entrenar y evaluar sistemas de recomendación. Se construye **desde cero**: no lee ningún dataset de interacciones previo. Las únicas fuentes son los **microdatos de la ECF 2021** (para calibrar los perfiles de usuario) y los **catálogos** de contenido (`contents.csv`, `concepts.csv`, `content_concept_map.csv`, `prerequisites.csv`).

---

## 2. Uso

```bash
python3 data/scripts/generate_interactions.py [--users N] [--seed S] [--out DIR]
```

| Argumento | Default | Descripción |
|---|---|---|
| `--users` | `2000` | Nº de usuarios sintéticos a generar |
| `--seed` | `42` | Semilla de aleatoriedad (reproducibilidad) |
| `--out` | `data/` | Directorio de salida de los archivos generados |

### Dependencias

- `numpy`, `pandas`
- `sklearn` (solo para el test de no-determinismo en la validación)
- Archivo ECF en `ECF-archivos/ecf_2021.csv` (ruta relativa al proyecto, no depende de la máquina)

---

## 3. Fuentes de datos

| Fuente | Ruta | Contenido |
|---|---|---|
| Microdatos ECF 2021 | `ECF-archivos/ecf_2021.csv` | Encuesta de Competencias Financieras del BdE/CNMV; se usa para calibrar perfiles (no se copian filas) |
| Catálogo de contenidos | `data/contents.csv` | 104 contenidos con topic, subtopic, dificultad, formato, riesgo, si es de inversión, prerrequisitos |
| Catálogo de conceptos | `data/concepts.csv` | 30 conceptos con topic y dificultad |
| Mapa contenido→concepto | `data/content_concept_map.csv` | Qué conceptos cubre cada contenido (`coverage_type: directa`) |
| Prerrequisitos | `data/prerequisites.csv` | Grafo de prerrequisitos entre conceptos |

---

## 4. Arquitectura: las 5 fases

El script se organiza en 5 fases, cada una con funciones específicas.

### FASE 0 — Preparación (`load_catalogs`)

Carga los catálogos y construye las estructuras auxiliares:

- **Dificultad ordinal → continua en [0,1]**: `básico=0.0`, `intermedio=0.5`, `avanzado=1.0`. Se usa esta escala porque es **compatible con la maestría** (probabilidad de dominio en [0,1]) para el término de competencia IRT.
- **Riesgo ordinal → numérico**: `bajo=0`, `medio=1`, `alto=2`.
- `concepts_of_content` (conceptos por contenido), `prereq_of_concept` (prerrequisitos por concepto), `concept_diff`, `content_topic`, `concept_topic`, `content_format`.

### FASE 1 — Perfiles de usuario calibrados con la ECF (`load_ecf_distributions`, `sample_user_profiles`)

Extrae distribuciones empíricas de la ECF 2021 para jóvenes 18–34:

- **Educación** (`e0100`), **empleo** (`a1500`), **tenencia de productos** (`b1000a`–`b1000i`), **correlación educación↔conocimiento**.
- **Conocimiento Big3** (`k0600` inflación, `k0100` interés compuesto, `k1003` diversificación): se calcula el % de acierto, **imputando los NS/NC** (no contarlos como fallo ni excluirlos).

Luego genera `N` perfiles latentes, cada uno con:

| Variable | Descripción |
|---|---|
| `age`, `age_group` | Edad y grupo (18–24 / 25–34) |
| `sex` | **Rebalanceado a ~50/50** (corrige el sesgo muestral de la ECF, que es ~85/15) |
| `education_level`, `employment_status` | De las distribuciones ECF |
| `products` | Tenencia de productos (tasas ECF) |
| `theta` | Conocimiento continuo, **imputado desde Big3** condicionado a educación + bonus por productos + ruido |
| `knowledge_level` | Categórico (bajo/medio/alto) derivado de `theta` |
| `interests` | Vector de intereses temáticos, derivado de productos + empleo + ruido |
| `risk` | Tolerancia al riesgo, correlacionada con `theta` |
| `format_pref` | Preferencia de formato |
| `activity` | Nivel de actividad (interacciones/semana), log-normal de cola larga |
| `learn_rate` | Tasa de aprendizaje (heterogénea, beta) |
| `noise_level` | Propensión a misclicks/curiosidad (heterogénea, beta) |

El mapeo producto→temas está en `product_to_topics` (p. ej. `acciones → [inversión, riesgo, mercado]`).

### FASE 2 — Línea temporal y calendario de actividad (`build_sessions`)

Genera las sesiones de cada usuario a lo largo de la ventana temporal (12 meses):

- Nº de interacciones anual = Poisson(actividad × 52).
- Nº de sesiones = interacciones / tamaño medio de sesión.
- Cada sesión tiene día (uniforme), hora (con pesos por hora del día), minuto y **tamaño de cola larga** (gamma).
- Se define `session_id` como `{user_id}-{sess_idx}`.

### FASE 3 — Simulación temporal causal (`simulate_user`, `simulate_all`)

Simula las interacciones en orden temporal global. Para cada sesión:

1. **Selección de candidatos expuestos** (mecanismo de exposición): mezcla de contenidos por interés (ponderados por afinidad temática × preparación × **novedad**) y por popularidad. El factor de **novedad** hace que el contenido cuyos conceptos ya domina el usuario se muestre menos, produciendo progresión de aprendizaje.
2. **Filtro de prerrequisitos**: los contenidos avanzados solo se exponen si el usuario domina al menos un prerrequisito (salvo pequeña probabilidad de curiosidad).
3. **Probabilidad de interacción** (logit, §4.3 del plan):
   ```
   P(interactuar) = σ(logit_base + preferencia + competencia + popularidad − penalización_prerrequisitos)
   ```
   donde `preferencia` combina afinidad temática, de formato, riesgo vs. riesgo del contenido, e interés inversor; y `competencia` usa la maestría del usuario sobre los conceptos del contenido (para avanzados pesa más).
4. **Ruido** (misclick, curiosidad, popularidad pura) que permite interactuar fuera de interés.
5. **Probabilidad de completar** (IRT, §4.4 del plan): `P(completar) = c_guess + (1−c_guess)·σ(a·(θ_c − b_c))`, penalizada si hay prerrequisitos no dominados. Si no completa, es un abandono (duración más corta).
6. **Tipo de interacción** según formato, **duración** log-normal, **outcome** (proxy de quiz).
7. **Actualización del conocimiento** (BKT, §4.5 del plan): si completa, actualiza la maestría de los conceptos cubiertos, con `p(T)` reducida por prerrequisitos no dominados.

La **popularidad de contenidos** sigue una power-law truncada, fija y compartida por todos los usuarios (`simulate_all`).

### FASE 4 — Validación (`validate`)

Ejecuta 9 baterías de tests y escribe `validation_report.json`. Ver §6.

### FASE 5 — Salida (`main`)

Escribe los archivos de salida. Ver §5.

---

## 5. Archivos de salida

| Archivo | Contenido |
|---|---|
| `data/interactions_synthetic.csv` | Una fila por interacción (ver columnas abajo) |
| `data/users_synthetic.csv` | Una fila por usuario: features del cuestionario + conteos + etiqueta de cold start |
| `data/validation_report.json` | Resultado de los tests de validación |
| `data/generation_metadata.json` | Seed, parámetros, criterio de cold start, validación |

### Columnas de `interactions_synthetic.csv`

| Columna | Tipo | Descripción |
|---|---|---|
| `interaction_id` | int | Identificador único |
| `user_id` | str | `U0001`… |
| `content_id` | str | `C001`… |
| `timestamp` | datetime | Marca temporal global |
| `session_id` | str | `{user_id}-{sess_idx}` |
| `interaction_type` | cat | `view` / `read` / `tool` |
| `duration_seconds` | float | Tiempo dedicado (log-normal) |
| `completed` | bool | Si completó el contenido (1) o lo abandonó (0) |
| `outcome` | cat | `correct` / `incorrect` / `na` (proxy de quiz) |
| `source` | cat | `recommended` / `search` / `browse` |
| `position` | int | Posición (aleatoria 1–10) |
| `concepts_covered` | str | Conceptos del contenido, separados por `;` |

### Columnas de `users_synthetic.csv`

Features del cuestionario (`age`, `age_group`, `sex`, `education_level`, `employment_status`, `products`, `theta`, `knowledge_level`, `interests` (JSON), `risk`, `format_pref` (JSON), `activity`, `learn_rate`, `noise_level`) más:

| Columna | Descripción |
|---|---|
| `n_interactions` | Nº real de interacciones del usuario en el dataset |
| `n_completed` | Nº real de completados |
| `cold_start` | `True` si `n_interactions == 0` (usuario frío) |

---

## 6. Tests de validación

El script ejecuta 9 checks que deben pasar para considerar la data lista. El resumen se reporta como `checks_passed` (p. ej. `8/8`).

| # | Test | Criterio de aprobación |
|---|---|---|
| 1 | **Sparsity** | Densidad de la matriz usuario–contenido en `[0.01, 0.05]` (1–5%) |
| 2 | **Popularidad cola larga** | Gini de popularidad de contenidos > 0.3 |
| 3 | **Actividad cola larga** | Gini de actividad de usuarios > 0.2 |
| 4 | **Completado por dificultad** | Tasa de completado decreciente: básico > intermedio > avanzado |
| 5 | **Conocimiento ↔ dificultad** | Correlación `theta` vs. dificultad completada > 0.1 |
| 6 | **Coherencia prerrequisitos** | Tasa de acceso a avanzados creciente con el nivel de conocimiento (bajo < medio < alto) |
| 7 | **No-determinismo** | AUC de una regresión logística simple < 0.90 (la preferencia no es determinista) |
| 8 | **Aprendizaje temporal** | `learning_trend` > 0 (la dificultad completada aumenta con el tiempo) |
| 9 | **Cobertura** | Fracción de contenidos que reciben al menos una interacción |

---

## 7. Parámetros clave (`PARAMS`)

Los hiperparámetros del generador están en el dict `PARAMS` y se pueden ajustar para calibrar patrones. Los más relevantes:

| Parámetro | Valor | Efecto |
|---|---|---|
| `n_users` | 2000 | Nº de usuarios |
| `window_days` | 365 | Ventana temporal (12 meses) |
| `activity_mu` | `log(0.15)` | Media de interacciones/semana (controla la densidad) |
| `exposure_candidates` | 4 | Contenidos expuestos por sesión |
| `logit_base` | -2.4 | Intercepto del logit (controla la densidad global) |
| `w_topic`, `w_format`, `w_risk`, `w_invest`, `w_popularity`, `w_prereq`, `w_competence` | 1.6/0.7/1.1/0.8/0.9/1.8/2.0 | Pesos de los factores del logit |
| `irt_discrimination` | 1.4 | Discriminación del modelo IRT |
| `irt_guess` | 0.10 | Probabilidad de "adivinar" |
| `bkt_learn_base` | 0.55 | p(T) base de aprendizaje |
| `bkt_slip`, `bkt_guess` | 0.10/0.15 | Slip y guess del BKT |
| `w_readiness` | 1.2 | Peso de la preparación (maestría de prerrequisitos) en la selección de candidatos |
| `noise_misclick`, `noise_curiosity`, `noise_popularity` | 0.06/0.05/0.08 | Probabilidades base de ruido |
| `popularity_alpha` | 1.8 | Exponente de la power-law de popularidad |
| `theta_big3_scale` | 2.0 | Escala del Big3 (0–1) a θ |

---

## 8. Estado actual y limitaciones

### Resultados de validación (seed 42)

| Métrica | Valor |
|---|---|
| Interacciones | 9612 |
| Densidad | ~3% |
| Tasa de completado | 64% |
| Señal de aprendizaje | 0.024 (positiva) |
| Checks | 8/8 |

### Limitaciones conocidas

- **`position` es aleatoria** (1–10), no refleja la posición real de recomendación; no se puede modelar position bias.
- **`outcome` es un proxy** fabricado a partir del completado (no hay quizzes reales en el catálogo).
- **El estado de maestría final por concepto no se persiste** (solo `theta` global y `knowledge_level` en `users_synthetic.csv`). Para el baseline KG/reglas de la comparativa, la maestría se deriva de las interacciones completadas.
- **`bkt_learn_base` es código efectivamente inerte**: el update BKT usa `profile["learn_rate"]` directamente, no este parámetro. No afecta al resultado.
- **`weekend_factor` está definido pero no se aplica** en la generación de sesiones (la estacionalidad semanal no se implementa realmente).

### Reproducibilidad

Con el mismo `--seed`, el dataset es idéntico. Con seeds distintos, las distribuciones agregadas son estables (densidad ~3%, señal de aprendizaje positiva), verificadas en seeds 42, 7 y 123.
