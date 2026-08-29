# Análisis comparativo crítico: `veronica-v2` (rama actual) vs `veronica`

**Fecha:** 2026-08-29
**Ámbito:** Auditoría metodológica y de rendimiento de las dos versiones del pipeline de generación de datos sintéticos y evaluación de modelos de recomendación.

---

## Resumen ejecutivo

**La rama actual (`veronica-v2`) es la mejor base para el TFM, sin discusión.** Es metodológicamente superior en el generador, en el evaluador y en el protocolo experimental. La rama `veronica` produce métricas más altas, pero esas métricas están **infladas por el diseño del dataset sintético** (concentración extrema de popularidad), no por una mejor calidad de los modelos. En ambas ramas, además, el hallazgo de fondo es el mismo y honesto: **la popularidad (baseline trivial) es casi imposible de superar**, y el modelo de IA propuesto no la supera de forma clara.

Lo que hay que hacer: tomar `veronica-v2` como base, e **importar de `veronica` los elementos que aportan validez** (esquema de eventos con PVR medible, coverage, métricas de filtro pedagógico, baseline Random), **descartando su generador** (que es la causa de las métricas infladas).

---

## 1. Auditoría del generador

### Rama `veronica-v2` — `data/scripts/generate_interactions.py`

**Diseño (sólido):** simulación temporal causal en 5 fases. Perfiles latentes calibrados con microdatos ECF 2021 (educación, empleo, tenencia de productos, Big3). La generación de interacciones usa un modelo logit de preferencia, un modelo IRT para el completado (con *guess*), y un modelo BKT para la actualización del conocimiento sobre el grafo de prerrequisitos. Hay un mecanismo de exposición con novedad y preparación, y ruido controlado (misclick, curiosidad, popularidad). Se valida con **9 tests estadísticos** (densidad, Gini de popularidad y actividad, completado decreciente por dificultad, correlación theta-dificultad, coherencia de prerrequisitos, no-determinismo con AUC, progresión temporal, cobertura) y se reporta `checks_passed 8/8`.

**Puntos débiles (reconocidos en la propia documentación):**
- `position` es aleatoria (no modela position bias).
- `outcome` es un proxy fabricado del completado (no hay quizzes reales).
- La maestría final por concepto no se persiste.
- `bkt_learn_base` es código inerte; `weekend_factor` está definido pero no se aplica.

**Problema de señal (el más importante):** el completado (`completed`) resulta **difícil de predecir desde las features** (la doc reporta AUC 0.575 con regresión logística, casi azar). Esto hace que las métricas finales sean bajas (NDCG@5 warm ≈ 0.10). No es un error, pero el dataset generado tiene poca señal de personalización en el objetivo `completed`.

### Rama `veronica` — `data/scripts/generate_interactions_v3.py`

**Diseño (más simple):** matching multiplicativo `prob = atractivo × topic_match × difficulty_match × formato_pref`. La restricción de prerrequisitos se aplica al *evento de dominio* (no al view), lo que produce un PVR medible. Esquema de eventos rico (`view/started/completed/quiz_passed/quiz_failed`).

**Problema crítico (causa de las métricas infladas):** el atractivo de contenido está **extremadamente concentrado**. Verificado sobre los datos reales:

| Métrica de popularidad | `veronica` (v3) | `veronica-v2` |
|---|---|---|
| Top-1 contenido | 4.4% del total | 3.3% |
| Top-5 contenidos | **19.8%** | 15.1% |
| Top-10 contenidos | **35.0%** | 28.2% |
| Contenido C001 interactuado por | **1658 / 1916 usuarios (87%)** | — |
| Contenidos con <10 interacciones | 0 de 104 | 3 de 104 |

Los 5 contenidos más populares son interactuados por más de 1500 de 1916 usuarios. Esto no es una cola larga realista: es una **colapso de diversidad**. Con `content_match_prob` teniendo un *floor* de 0.10 y un atractivo multiplicativo, casi todos los usuarios terminan interactuando y completando los mismos contenidos populares. Consecuencia directa: **el ground truth de test está dominado por esos pocos contenidos**, y un modelo que recomiende los 5 contenidos más populares acierta el 43% (P@5 cold de Popularidad = 0.4358).

**Por qué importa:** el "mejor" modelo cold de `veronica` es **Popularidad con NDCG@5 = 0.4548**, y el NeuMF-Profile (0.3515) no lo supera. Es decir, incluso en la rama con métricas altas, el modelo neuronal propuesto **pierde contra la popularidad**. Las métricas altas no provienen de una mejor IA, sino de que el dataset es casi trivial para la popularidad.

---

## 2. Auditoría del evaluador

### Rama `veronica-v2` — `data/scripts/evaluate_models.py`

**Protocolo (el más sólido):**
- **Split temporal global GTS** (9 meses train / 3 meses test, umbral 2026-06-01). Es un split por tiempo, no por par — la opción metodológicamente correcta para un sistema de recomendación.
- Warm/cold **re-derivados sobre el split** (459 warm, 167 cold con ≥1 completado en test), no de la etiqueta predefinida. Esto evita que la etiqueta esté desalineada con el split.
- 7 modelos (3 baselines + BPR-MF + NeuMF + Feature-aware NeuMF + sistema completo con KG).
- Métricas NDCG@k, Precision@k, Recall@k, MRR + **pedagogía@k sobre el ranking crudo** (para que discrimine entre modelos, no sea 1.0 por construcción).
- Diagnóstico honesto: documenta explícitamente que el modelo propuesto no supera a los baselines y que el resultado bajo es inherente al diseño.

**Puntos débiles:**
- En cold start, BPR-MF y NeuMF caen al *fallback* de popularidad, por lo que sus métricas cold son **idénticas** a Most-Popular (verificado en el JSON: `bpr_mf`, `neumf` y `most_popular` tienen exactamente los mismos valores en cold). Esto hace que el escenario cold de los modelos colaborativos no sea informativo.
- El Feature-aware NeuMF en cold tiene **pedagogía@5 = 0.0** — recomienda contenidos incoherentes, un punto débil del modelo propuesto.
- No hay baseline Random ni test de significación (la doc lo menciona como pendiente).

### Rama `veronica` — `src/utils/evaluate_models.py`

**Protocolo (más débil en el split, más rico en métricas de seguridad):**
- Split **80/20 por par `(user_id, content_id)`** con timestamp, por usuario. Es un split por par, no un split temporal global. Válido anti-leakage (assert de intersección vacía), pero metodológicamente inferior al GTS de v2.
- Cold start con `train_pool` separado (20% de usuarios "nuevos", sus interacciones íntegras a test). Explícito y correcto.
- **Métricas más completas:** Precision/Recall/NDCG@5 (RAW y POST), **coverage**, **PVR pre/post**, **filter_rate**, **feasibility@5**. Esto es valioso y falta en v2.
- Incluye **baseline Random** (cota inferior), que falta en v2.

**Puntos débiles:**
- **PVR Post = 0% "por construcción"** y **feasibility@5 = 99.57-100%**: son tautológicos. El filtro elimina las violaciones y casi nunca deja a un usuario sin 5 recomendaciones. Reportarlos como logro no aporta información.
- **Coverage cold = 4.81%** para Popularidad: el modelo solo recomienda ~5 contenidos y aún así logra NDCG 0.45 — confirmación directa de la falta de diversidad del dataset.
- **Rutas absolutas hardcoded** (`DATA_DIR = "/Users/veronica/Desktop/tfm/data"`): rompe la portabilidad/reproducibilidad en otra máquina. v2 usa rutas relativas.
- El TF-IDF cold, el híbrido y el NeuMF-Profile capturan una señal artificialmente fuerte porque el generador v3 usó `learning_goal` y `financial_knowledge_level` (presentes en el texto del perfil) para generar las interacciones. No es leakage de código, pero es una ventaja de diseño.

---

## 3. Comparación de resultados

### Rendimiento (métricas reportadas)

| Escenario | `veronica` (v3) | `veronica-v2` |
|---|---|---|
| Warm — mejor NDCG@5 | Popularidad **0.276** | Most-Popular **0.102** |
| Warm — mejor P@5 | Popularidad **0.149** | Most-Popular 0.052 |
| Cold — mejor NDCG@5 | Popularidad **0.455** | Content-Based **0.132** |
| Cold — mejor P@5 | Popularidad **0.436** | Content-Based 0.067 |

Las métricas de `veronica` son **3-4× más altas**. Pero este es exactamente el caso que el prompt advierte: la mejora de métricas proviene de un mecanismo que hace que la evaluación no sea fiable — **el dataset con popularidad colapsada**, no de un mejor modelo. La prueba definitiva: en `veronica`, el modelo neuronal (NeuMF-Profile, 0.35) **no supera a la popularidad (0.45)** ni en el escenario donde la neurona está diseñada para destacar (cold start). El mismo patrón se repite en v2 (el Feature-aware no supera a los baselines). **Ninguna de las dos ramas demuestra que la IA propuesta supere a un baseline trivial** — y eso es un hallazgo coherente y honesto en ambas.

### Validez metodológica (resumen)

| Criterio | `veronica-v2` | `veronica` |
|---|---|---|
| Split | Temporal global GTS (más limpio) | Por par 80/20 (más débil) |
| Warm/cold | Derivado del split temporal | train_pool separado (explícito) |
| Generador | Causal IRT/BKT, calibrado ECF, 9 checks | Matching multiplicativo, popularidad colapsada |
| Señal de personalización | Baja pero honesta | Inflada por concentración |
| Métricas de seguridad | Solo pedagogía@k | PVR, coverage, filter_rate (más ricas) |
| Baseline Random | No | Sí |
| PVR Post / feasibility | — | Tautológicos (0% / ~100%) |
| Reproducibilidad | Rutas relativas, seed | Rutas absolutas hardcoded |
| Honestidad del diagnóstico | Alta (reconoce no superar baselines) | Media (presenta métricas altas sin advertir su causa) |

---

## 4. Consolidación final: recomendación

### 1. Versión base
**`veronica-v2` (rama actual).** Es la única defendible ante un tribunal: split temporal global, generador causal con validación estadística, reproducibilidad por seed, rutas relativas, y un diagnóstico honesto. La rama `veronica` no puede usarse como base porque sus métricas descansan sobre un dataset con diversidad colapsada.

### 2. Aspectos de la base a conservar
- **Generador v2** (simulación causal, IRT/BKT, calibración ECF) y sus 9 checks de validación.
- **Split temporal global GTS** y warm/cold derivados del split.
- **Pedagogía@k sobre el ranking crudo** (no la salida filtrada) para que discrimine.
- **Los 3 baselines + 4 modelos ML** y el protocolo de 7 modelos.
- **Documentación rigurosa y honesta** del diagnóstico.

### 3. Elementos de `veronica` a incorporar (mejoran métricas o metodología)
1. **Esquema de eventos con PVR medible** (`view/started/completed/quiz_passed/quiz_failed` y PVR sobre eventos de dominio). v2 solo tiene `completed` binario + `outcome` proxy; el TFM necesita PVR explícito. **Este es el elemento más valioso a importar.**
2. **Métricas de seguridad:** coverage, PVR pre/post, filter_rate, feasibility@5. Faltan en v2 y son exactamente lo que pide un TFM de recomendación pedagógica.
3. **Baseline Random** como cota inferior en warm y cold.
4. **La separación explícita cold/train_pool** como *forma alternativa* de validar cold start (puede ser un segundo experimento, complementario al GTS).

### 4. Elementos de `veronica` a descartar
1. **El generador v3** (matching multiplicativo con floor 0.10 y atractivo concentrado). Es la causa de las métricas infladas y de la pérdida de señal de personalización. **No importar.**
2. **PVR Post = 0% / feasibility ~100% como métricas de éxito**: son tautológicas. Pueden reportarse como verificación del filtro, nunca como logro comparativo.
3. **El split por par 80/20** como protocolo principal: inferior al GTS. Como mucho, un análisis secundario.
4. **Las rutas absolutas** `DATA_DIR = "/Users/veronica/.../"`.

### 5. Modificaciones concretas para el mejor pipeline final
1. **Portar el esquema de eventos a v2**: añadir `started`/`quiz_passed`/`quiz_failed` y un `score` continuo, manteniendo el motor causal IRT/BKT. Medir **PVR real** como métrica principal de coherencia.
2. **Aumentar la señal de personalización en el generador**: el problema de v2 no es el protocolo sino que `completed` es casi impredecible desde las features (AUC 0.575). Recalibrar los pesos del logit (subir `w_topic`/`w_competence`, bajar `w_popularity`) y/o reducir el ruido para que `theta` e `interests` predigan mejor el completado, **sin** reproducir el colapso de v3 (mantener el Gini de popularidad ~0.3-0.4 y la densidad ~3-5%). Verificar con los checks que la señal de aprendizaje y la correlación theta-dificultad se mantienen.
3. **Persistir la maestría final por concepto** en `users_synthetic.csv` (v2 no lo hace) para que el baseline KG y el PVR sean computables de forma no derivada.
4. **Añadir al evaluador**: baseline Random, coverage, PVR pre/post, filter_rate, feasibility; **y test de significación Wilcoxon pareado** entre el modelo propuesto y cada baseline (ya lo pide la propia doc de v2).
5. **Repetir con varias seeds** (p. ej. 42, 7, 123) y reportar media ± desviación, en lugar de un único seed.
6. **Corregir el cold start de los modelos colaborativos**: el fallback de popularidad hace que BPR/NeuMF en cold sean indistinguibles de Most-Popular. Para que el escenario cold sea informativo, reportar los modelos colaborativos solo en warm, y dejar que en cold compitan el Content-Based, el Feature-aware y el KG (los que sí usan perfil).
7. **Reenmarcar la narrativa del TFM** en torno al hallazgo honesto: *la popularidad es difícil de superar en ranking, pero el componente pedagógico (KG) eleva la coherencia de 0.3 a 1.0 a costa de un trade-off en ranking*. Eso es un resultado defendible y coherente con la pregunta de investigación; no hay que forzar que "el modelo gana".

---

## Anexo: datos de respaldo verificados

### Popularidad de contenido (veronica v3, `interactions_synthetic_v3.csv`)
- Total interacciones: 60 937 | Usuarios: 1916 | Contenidos: 104
- Top-1: C001 con 2705 (4.4%) | Top-5: 12 095 (19.8%) | Top-10: 21 355 (35.0%)
- Contenidos con <10 interacciones: 0 de 104
- C001 interactuado por 1658/1916 usuarios (87%)
- Duplicados (revisitas del mismo par): 12 164 (20.0%)
- Interacciones por usuario: media 31.8, mediana 28, min 4, max 70
- Positivos (score ≥ 0.5): 23 692 (38.9%)

### Popularidad de contenido (veronica-v2, `interactions_synthetic.csv`)
- Total interacciones: 9612 | Usuarios: 1770 | Contenidos: 104
- Top-1: 3.3% | Top-5: 15.1% | Top-10: 28.2%
- Contenidos con <10 interacciones: 3 de 104
- Densidad (pares únicos): 3.11% | Duplicados: 3152
- Tasa de completado: 0.639

### Resultados fríos (cold) de veronica — evidencia de trivialidad del dataset
- Popularidad: NDCG@5 = 0.455, P@5 = 0.436, coverage = 4.81%
- NeuMF-Profile: NDCG@5 = 0.352 (no supera a popularidad)
- Random: NDCG@5 = 0.089

### Resultados de veronica-v2
- Warm: Most-Popular NDCG@5 = 0.102 (mejor); Feature-aware NeuMF = 0.091 (no supera)
- Cold: Content-Based NDCG@5 = 0.132 (mejor); Feature-aware NeuMF = 0.104
- Cold colaborativos (BPR-MF, NeuMF) idénticos a Most-Popular por fallback
- Pedagogía@5: KG = 1.0; post-filtro KG = 1.0; resto 0.0-0.73
