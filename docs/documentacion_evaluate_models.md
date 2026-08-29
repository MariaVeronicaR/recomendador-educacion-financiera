# Documentación: `src/utils/evaluate_models.py`

**TFM:** Plataforma inteligente para la recomendación personalizada de contenidos en educación financiera basada en IA  
**Fichero:** `src/utils/evaluate_models.py`  
**Propósito:** Análisis comparativo experimental de cuatro arquitecturas de recomendación en dos escenarios (arranque en caliente y arranque en frío).

---

## 1. Resumen

Este script implementa y evalúa de forma reproducible cuatro sistemas de recomendación sobre el catálogo de educación financiera del piloto. La evaluación mide tres dimensiones:

*   **Exactitud:** Precision@5, Recall@5 y NDCG@5.
*   **Cobertura del catálogo:** porcentaje de contenidos recomendados al menos una vez.
*   **Seguridad pedagógica:** Prerequisite Violation Rate (PVR) antes y después del filtro del grafo.

El script ejecuta dos fases independientes:

1.  **Warm Start:** usuarios con historial previo, partición Train/Test (80/20) por usuario.
2.  **Cold Start:** usuarios "nuevos" sin historial, evaluados únicamente con su perfil demográfico.

---

## 2. Modelos Evaluados

### 2.1. Warm Start

| # | Modelo | Clave en resultados | Descripción |
| :--- | :--- | :--- | :--- |
| 0 | **Random (baseline)** | `Random (baseline)` | Selecciona 5 contenidos al azar por usuario (excluye los vistos en Train). Sirve de cota inferior. |
| 1 | **Popularidad (PopRec)** | `Popularidad` | Recomienda los contenidos con más interacciones en Train. |
| 2 | **TF-IDF + Cosine** | `TF-IDF + Cosine` | Filtrado basado en contenido: vectoriza títulos/resúmenes/objetivos con TF-IDF (stopwords en español) y mide similitud de coseno contra el perfil de éxitos del usuario en Train. |
| 3 | **Híbrido SVD + Ridge** | `Híbrido SVD` | Factorización de matrices (TruncatedSVD, 10 componentes) combinada con regresión Ridge sobre features demográficas y de contenido. |
| 4 | **NCF-MLP (PyTorch)** | `NCF-MLP (PyTorch)` | Red neuronal de filtrado colaborativo (rama MLP del NeuMF) entrenada con MSELoss y Adam. |

### 2.2. Cold Start

| # | Modelo | Clave en resultados | Descripción |
| :--- | :--- | :--- | :--- |
| 0 | **Random (baseline)** | `Random (baseline)` | Selecciona 5 contenidos al azar de todo el catálogo (sin consultar el ground truth). |
| 1 | **Popularidad (PopRec)** | `Popularidad` | Misma lógica que Warm, pero la popularidad se calcula sobre el `train_pool`. |
| 2 | **TF-IDF + Cosine (perfil)** | `TF-IDF + Cosine (perfil)` | Construye el perfil del usuario a partir del texto de su cuestionario demográfico. |
| 3 | **Profile + Content Ridge** | `Profile + Content Ridge` | Variante del híbrido **sin señal colaborativa** (la componente SVD del usuario se fija a 0). No es comparable con el híbrido de Warm Start. |
| 4 | **NeuMF-Profile (variante)** | `NeuMF-Profile (variante)` | Variante del NCF que sustituye el `nn.Embedding` de usuario por un encoder MLP sobre las features demográficas. |

---

## 3. Metodología

### 3.1. Partición Train/Test (Warm Start)

La función `make_train_test_split` garantiza que **no haya fuga de datos**:

*   Agrupa por par `(user_id, content_id)` para que el mismo par nunca quede en ambos conjuntos.
*   Si hay `timestamp`, ordena cronológicamente por usuario y toma los últimos pares como Test (split temporal).
*   Si no hay `timestamp`, baraja los pares con semilla fija (split aleatorio reproducible).
*   Usuarios con un solo par → todo a Train.
*   Usuarios con ≥ 2 pares → al menos 1 par en Test.
*   **Validación anti-leakage:** se comprueba que la intersección de pares Train/Test sea vacía (assert).

### 3.2. Partición Cold Start

La función `make_cold_start_split`:

*   Selecciona `N_COLD_USERS` (≈20% de los usuarios) como "nuevos".
*   Sus interacciones van **íntegras** al Test (ninguna a Train).
*   El resto forma el `train_pool`.
*   **Validación anti-fuga:** ningún cold user aparece en el train_pool (assert).

### 3.3. Métricas

*   **Precision@5:** proporción de recomendaciones relevantes en el Top-5.
*   **Recall@5:** proporción de contenidos relevantes del Test que aparecen en el Top-5.
*   **NDCG@5:** calidad del ordenamiento (los relevantes deben aparecer primero).
*   **Coverage:** `(contenidos recomendados / total catálogo) × 100`.
*   **PVR Pre:** % de recomendaciones del ranking crudo que violan prerrequisitos.
*   **PVR Post:** % de violaciones tras el filtro pedagógico (debe ser **0%** por construcción).
*   **Filter Rate:** % del ranking crudo rechazado por el filtro pedagógico.
*   **Feasibility@5:** % de usuarios con relevantes en Test que obtienen al menos 5 recomendaciones tras el filtro.

> **Nota sobre relevancia:** una interacción se considera "relevante" si `score >= 0.5`. Se excluyen del promedio los usuarios sin interacciones relevantes en su Test.

### 3.4. Métricas RAW vs POST

Cada modelo se evalúa dos veces:

*   **RAW:** sobre el ranking crudo del modelo, sin filtro pedagógico.
*   **POST:** sobre el ranking tras aplicar el filtro de prerrequisitos del grafo.

Esto permite distinguir la calidad intrínseca del recomendador de la influencia de la capa de seguridad pedagógica.

---

## 4. Arquitecturas de Red Neuronal

### 4.1. `NCFMLP` (Warm Start)

Variante basada en MLP del Neural Collaborative Filtering (NCF). **No** implementa la rama GMF del NeuMF clásico de He et al. (2017); es únicamente la rama MLP.

```
user_embed (Embedding 8) ─┐
                          ├─ concat(16) → Linear(16) → ReLU → Dropout(0.2)
item_embed (Embedding 8) ─┘              → Linear(8)  → ReLU → Dropout(0.2)
                                         → Linear(1)  → Sigmoid
```

*   `latent_dim = 8`, `dropout = 0.2`, salida sigmoide, `MSELoss`, `Adam(lr=0.01, weight_decay=1e-4)`.
*   Entrenamiento: 15 épocas, `batch_size = 32`.

### 4.2. `NeuMFProfileMLP` (Cold Start)

Variante paralela que sustituye el `nn.Embedding` de usuario por un encoder MLP sobre las features demográficas del perfil. Permite recomendar a un usuario nuevo desde su primer acceso.

```
user_encoder (Linear 16 → ReLU → Linear 8) ─┐
                                              ├─ concat(16) → MLP (idéntico al NCFMLP)
item_embed (Embedding 8) ─��───────────────────┘
```

---

## 5. Datos de Entrada

| Fichero | Ruta | Contenido |
| :--- | :--- | :--- |
| Usuarios | `data/users_synthetic.csv` | Perfiles demográficos (edad, estudios, empleo, nivel financiero, hábito de ahorro, sexo, objetivo). |
| Contenidos | `data/contents.csv` | Catálogo educativo (título, resumen, objetivo, tema, dificultad, formato). |
| Interacciones | `data/interactions_synthetic_v3.csv` | Interacciones usuario-contenido con `score` y `event`. |
| Prerrequisitos | `data/prerequisites.csv` | Grafo de prerrequisitos entre conceptos. |
| Mapa | `data/content_concept_map.csv` | Asociación contenido → concepto (cobertura directa). |

---

## 6. Salidas

| Fichero | Contenido |
| :--- | :--- |
| `data/evaluation_metrics_warm.csv` | Métricas de los 5 modelos en Warm Start. |
| `data/evaluation_metrics_cold.csv` | Métricas de los 5 modelos en Cold Start. |

Ambos CSV incluyen las columnas: `modelo`, `precision_5`, `recall_5`, `ndcg_5`, `raw_precision_5`, `raw_recall_5`, `raw_ndcg_5`, `coverage_pct`, `pvr_pre_pct`, `pvr_post_pct`, `filter_rate_pct`, `feasibility_at_5_pct`.

---

## 7. Reproducibilidad

Se fijan semillas aleatorias para garantizar resultados idénticos en cada ejecución:

*   `random.seed(42)`, `np.random.seed(42)`, `torch.manual_seed(42)`.
*   Semillas específicas para los baselines Random: `123` (Warm) y `456` (Cold).
*   `TruncatedSVD(random_state=42)`.

---

## 8. Uso

```bash
python3 src/utils/evaluate_models.py
```

**Requisitos:** `pandas`, `numpy`, `scikit-learn`, `torch`.

---

## 9. Notas Metodológicas

*   **Nomenclatura del modelo neuronal:** el código renombra la clase a `NCFMLP` para reflejar fielmente que solo implementa la rama MLP del NeuMF, siendo académicamente defendible.
*   **Cold Start híbrido:** la variante `Profile + Content Ridge` elimina la señal colaborativa (componente SVD = 0) porque el usuario nuevo no tiene historial; es un modelo conceptualmente distinto del híbrido de Warm Start.
*   **PVR Post = 0%:** por construcción del filtro pedagógico, todas las recomendaciones post-filtro cumplen los prerrequisitos; reportar 0% confirma que el filtro funciona.
*   **Conocimiento inicial en Cold Start:** todos los cold users parten con `mastered = set()`; el nivel financiero declarado no se imputa al estado inicial para reflejar fielmente el escenario "usuario nuevo sin historial".
