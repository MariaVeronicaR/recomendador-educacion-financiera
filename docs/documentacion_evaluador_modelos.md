# Documentación: `data/scripts/evaluate_models.py`

Harness de evaluación para la comparativa de modelos de recomendación de contenidos de educación financiera. Define el protocolo común de evaluación, las métricas y los baselines, y sirve para evaluar cualquier modelo sobre la data sintética generada por [`generate_interactions.py`](documentacion_generador_interacciones.md).

Implementa el protocolo de evaluación de [`docs/Comparativa_modelos_recomendacion.md`](Comparativa_modelos_recomendacion.md) §4.

---

## 1. Propósito

Evaluar y comparar modelos de recomendación sobre el dataset sintético, con un protocolo común y reproducible. Actualmente incluye **7 modelos**: 3 baselines triviales y 4 modelos de ML (incluidos el propuesto y el sistema completo).

La comparativa responde a la pregunta de investigación: *"¿añadir estructura pedagógica a un recomendador personalizado mejora el ranking y la coherencia?"*.

---

## 2. Uso

```bash
python3 data/scripts/evaluate_models.py [--seed S] [--k 5 10] [--models MODELOS...]
```

| Argumento | Default | Descripción |
|---|---|---|
| `--seed` | `42` | Semilla para los modelos de ML (inicialización aleatoria) |
| `--k` | `5 10` | Valores de k para las métricas @k |
| `--models` | los 7 modelos | Qué modelos evaluar (ver §4) |

### Dependencias

- `numpy`, `pandas`
- `torch` (para NeuMF y Feature-aware NeuMF)
- `sklearn` (no se usa en el harness en sí, pero está disponible)

---

## 3. Protocolo de evaluación

El protocolo concreto (alineado con el documento §4):

- **Ground truth de ranking**: `completed` = relevante (**etiqueta A**). Un contenido es relevante para un usuario si lo completó en el periodo de test.
- **Split temporal GTS**: primeros 9 meses train (`< 2026-06-01`), últimos 3 test (`≥ 2026-06-01`).
- **Dos escenarios**:
  - *Warm*: usuarios con historial en train (459 usuarios).
  - *Cold start*: usuarios sin historial en train pero con ≥1 relevante en test (167 usuarios). Se derivan sobre train, no de la etiqueta `cold_start` de `users_synthetic.csv`.
- **Métricas**: NDCG@k, Precision@k, Recall@k, MRR (k=5,10) + **coherencia pedagógica** sobre el ranking crudo.
- **Rigor**: el `--seed` se propaga a los modelos de ML; para el reporte final conviene repetir con varias seeds y aplicar Wilcoxon pareado.

### Funciones principales

| Función | Rol |
|---|---|
| `load_data()` | Carga interacciones, usuarios y catálogos; construye `concepts_of_content`, `prereq_of_concept`, `content_diff` |
| `make_split(data)` | Divide train/test por punto temporal y separa warm / cold start |
| `compute_mastery(train, data)` | Concepto dominado si el usuario completó ≥1 contenido en train que lo cubre |
| `content_is_coherent(cid, mastered, data)` | Un contenido respeta prerrequisitos si, para cada concepto que cubre, el usuario domina al menos un prerrequisito |
| `evaluate_ranking(pred, truth, ks)` | NDCG@k, Precision@k, Recall@k, MRR |
| `evaluate_pedagogy(pred, mastered, data, ks)` | % de recomendaciones del ranking crudo que respetan prerrequisitos |
| `run_evaluation(rank_fn, users, truth, mastery, data, ks)` | Agrega métricas sobre un conjunto de usuarios |

---

## 4. Modelos incluidos

| # | Clave (`--models`) | Modelo | Paradigma | Información que usa |
|---|---|---|---|---|
| 1 | `most_popular` | Most-Popular | Baseline trivial | Frecuencia de interacción en train |
| 2 | `content_based` | Content-Based Filtering | Basado en contenido | Intereses del usuario + topic del contenido |
| 3 | `kg_rules` | KG / reglas pedagógicas | Basado en conocimiento | Grafo + maestría |
| 4 | `bpr_mf` | BPR-MF | Filtrado colaborativo clásico | Interacciones |
| 5 | `neumf` | NeuMF puro | Deep CF | Interacciones |
| 6 | `feature_aware_neumf` | Feature-aware NeuMF | Deep híbrido (propuesto) | Interacciones + features del cuestionario |
| 7 | `feature_aware_neumf_kg` | Feature-aware NeuMF + KG post-filtro | Híbrido + restricción (sistema completo) | Todo |

### Detalle por modelo

**1. Most-Popular** (`baseline_most_popular`). Ranking global por frecuencia de interacción en train, igual para todos los usuarios. Es el suelo de la comparativa.

**2. Content-Based** (`baseline_content_based`). Similitud coseno entre el vector de intereses del usuario (de `users_synthetic.csv`) y el topic del contenido. Funciona en cold start (no necesita historial). Sufre overspecialization.

**3. KG / reglas pedagógicas** (`baseline_kg_rules`). Sin ML: recomienda los contenidos cuyos prerrequisitos están cubiertos (coherentes), ordenados por dificultad; los incoherentes van al final. Pedagogía 1.0 por construcción. No personaliza más allá de la maestría.

**4. BPR-MF** (`train_bpr` + `baseline_bpr_mf`). Matrix Factorization con Bayesian Personalized Ranking, entrenada con SGD sobre pares (positivo, negativo) de interacciones en train. Para usuarios sin historial (cold), usa **fallback de popularidad** (no puede recomendar sin factores).

**5. NeuMF puro** (`train_neumf` + `baseline_neumf`). Arquitectura de He et al. (GMF + MLP), entrenada con BCE y muestreo negativo sobre interacciones. Igual que BPR-MF, en cold usa fallback de popularidad.

**6. Feature-aware NeuMF** (`train_feature_aware_neumf` + `baseline_feature_aware_neumf`). Extiende el NeuMF añadiendo las **features del cuestionario** al MLP. Para usuarios sin historial usa un **embedding compartido de cold start** + sus features, por lo que **puede recomendar en cold start** (hipótesis central del TFM). Las features se construyen con `build_user_features` (θ, risk, activity, age z-score + one-hot de sexo/educación/empleo/conocimiento + vector de intereses por topic).

**7. Feature-aware NeuMF + KG post-filtro** (`baseline_feature_aware_neumf_kg`). Aplica el ranking del modelo 6 y luego **reordena** moviendo los contenidos incoherentes (prerrequisitos no cubiertos) al final. Sube la pedagogía a 1.0 a costa de un ranking peor.

---

## 5. Métricas

### Ranking

| Métrica | Fórmula |
|---|---|
| `NDCG@k` | DCG normalizado por el DCG ideal (relevantes primero) |
| `Precision@k` | Fracción de relevantes en el top-k |
| `Recall@k` | Fracción de relevantes recuperados en el top-k |
| `MRR` | Inversa de la posición del primer relevante |

### Coherencia pedagógica

`pedagogy@k` = % de recomendaciones del **ranking crudo** (sin filtro) que respetan prerrequisitos (`content_is_coherent`). Se mide sobre el ranking crudo, no sobre la salida filtrada, para que discrimine entre modelos (si se midiera sobre la salida ya filtrada sería 1.0 por construcción).

---

## 6. Salida

Escribe `data/evaluation_results.json` con:

```json
{
  "seed": 42,
  "split": { "train_end": "2026-06-01", "n_train": ..., "n_test": ...,
             "n_warm_eval": 459, "n_cold_eval": 167 },
  "ground_truth": "completed",
  "k": [5, 10],
  "models": {
    "warm": { "most_popular": {...}, "...": {...} },
    "cold": { "most_popular": {...}, "...": {...} }
  }
}
```

---

## 7. Resultados actuales (seed 42)

### Escenario warm (459 usuarios)

| Modelo | NDCG@5 | NDCG@10 | Recall@10 | MRR | Pedagogía@5 |
|---|---|---|---|---|---|
| Most-Popular | **0.102** | **0.155** | **0.285** | **0.170** | 0.367 |
| Content-Based | 0.087 | 0.133 | 0.251 | 0.152 | 0.733 |
| KG/reglas | 0.067 | 0.100 | 0.183 | 0.123 | **1.000** |
| BPR-MF | 0.101 | 0.143 | 0.257 | 0.158 | 0.416 |
| NeuMF | 0.094 | 0.146 | 0.275 | 0.160 | 0.309 |
| Feature-aware NeuMF | 0.091 | 0.145 | 0.276 | 0.153 | 0.292 |
| Feat-NeuMF + KG | 0.085 | 0.119 | 0.208 | 0.143 | **1.000** |

### Escenario cold (167 usuarios)

| Modelo | NDCG@5 | NDCG@10 | Recall@10 | MRR | Pedagogía@5 |
|---|---|---|---|---|---|
| Most-Popular | 0.103 | 0.161 | 0.309 | 0.172 | 0.200 |
| Content-Based | **0.132** | **0.174** | **0.331** | **0.174** | 0.624 |
| KG/reglas | 0.067 | 0.089 | 0.171 | 0.106 | **1.000** |
| BPR-MF | 0.103 | 0.161 | 0.309 | 0.172 | 0.200 |
| NeuMF | 0.103 | 0.161 | 0.309 | 0.172 | 0.200 |
| Feature-aware NeuMF | 0.104 | 0.159 | 0.299 | 0.167 | 0.000 |
| Feat-NeuMF + KG | 0.083 | 0.115 | 0.204 | 0.133 | **1.000** |

### Lectura de los resultados

- **Warm**: Most-Popular es el mejor en ranking; ningún modelo lo supera. El Feature-aware NeuMF (0.091) no mejora al NeuMF puro (0.094).
- **Cold**: Content-Based gana en ranking; el Feature-aware NeuMF (0.104) apenas supera a popularidad (0.103) y su pedagogía es 0.000.
- **El post-filtro KG** sube la pedagogía a 1.0 pero **hunde el ranking** (trade-off claro).

---

## 8. Hallazgo metodológico (importante)

El modelo propuesto (Feature-aware NeuMF) **no supera a los baselines**, y el sistema completo (con KG) es el peor en ranking. El diagnóstico (ver conversación) mostró que:

- El modelo **sí aprende** (AUC 0.72 sobre interacciones), pero eso no se traduce en ranking de completados.
- Las features del cuestionario apenas predicen `completed` (AUC 0.575 con regresión logística), casi azar.
- Cambiar la ground truth a `interaction` **no cambia el resultado**: el Feature-aware NeuMF sigue sin superar a los baselines.

**Conclusión:** el resultado bajo es **inherente al diseño** (la ground truth `completed` no es predecible desde las features), no un problema de configuración. Esto contradice la hipótesis central del TFM y requiere reenmarcar la narrativa (el Content-Based gana en cold start; el KG es un trade-off).

---

## 9. Estado y limitaciones

- El script actual tiene la ground truth **fija en `completed`** (la opción `--ground_truth interaction` que se probó experimentalmente fue revertida).
- El `--seed` afecta a los modelos de ML (BPR-MF, NeuMF, Feature-aware NeuMF); los baselines triviales son deterministas.
- El reporte final del TFM debería repetir con varias seeds y aplicar **test de significación pareado (Wilcoxon)** entre el modelo propuesto y cada baseline, como pide el documento §4.
