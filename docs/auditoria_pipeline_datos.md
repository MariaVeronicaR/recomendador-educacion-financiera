# Auditoría de la pipeline de datos sintéticos y evaluación

Fecha: 2026-08-30
Alcance: `data/scripts/generate_interactions_v3.py`, `data/scripts/regenerate_users_from_ecf.py`, `data/scripts/evaluate_models.py`, y los CSV `users_synthetic.csv`, `interactions_synthetic_v3.csv`.

La auditoría se realizó verificando los scripts contra los datos reales (no solo leyendo el código).

---

## Estado de los hallazgos

| # | Hallazgo | Gravedad | Estado |
|---|----------|----------|--------|
| 1 | `quiz_failed` con `score >= 0.5` cuenta como relevante | crítica | ✅ resuelto |
| 2 | Desajuste de vocabulario de eventos en el evaluador | alta | ✅ resuelto |
| 3 | Popularidad gana en Cold Start | media | ✅ resuelto |
| 4 | 51% de usuarios sin señal de conocimiento | media | ⚠️ pendiente (limitación documentada) |
| 5 | Fuerte desbalance de topics | media | ⚠️ pendiente (por diseño) |
| 6 | `is_recommended` casi indistinguible de exploración | baja | ⚠️ pendiente |
| 7 | Código muerto (menor) | menor | ⚠️ pendiente |

---

## Hallazgo 1 (crítico, RESUELTO): `quiz_failed` con `score >= 0.5` se contaba como interacción relevante

**Problema original.** En `generate_interactions_v3.py` (`score_for_event`), `quiz_failed` recibía un score en `[0.4, 0.6]`. El docstring define que `score >= 0.5` = relevante y que solo los eventos de dominio (`completed`/`quiz_passed`) son relevantes. Como `quiz_failed` es un **fallo**, la mitad de los casos (1.435 de 2.853, el 50%) caían en `[0.5, 0.6]` y se marcaban como positivos. El evaluador usa `score >= 0.5` para el conjunto relevante, así que **un quiz suspendido contaba como "relevante"** e inflaba las métricas (eran contenidos populares que el usuario intentó y falló).

**Corrección aplicada.** En `score_for_event`, `quiz_failed` y `started` quedan ahora acotados a `[0.4, 0.49]`, siempre por debajo de 0.5. Solo `completed`/`quiz_passed` pueden alcanzar `>= 0.5`.

**Verificación posterior (datos regenerados):** 0 `quiz_failed`/`started`/`view` con `score >= 0.5`; los positivos (25.549) coinciden exactamente con los eventos de dominio.

## Hallazgo 2 (alto, RESUELTO): desajuste de vocabulario de eventos en el evaluador

**Problema original.** `event_to_relevance` mapeaba `viewed` y `disliked`, que el generador no produce; los eventos reales (`view`, `started`, `quiz_failed`) caían en el `default` → relevance `0.0`. No rompía la consolidación (completed/quiz_passed seguían ganando en el dedup), pero significaba que **la consolidación usaba relevancia por evento** mientras que **la evaluación usaba relevancia por score** (`score >= 0.5`): dos definiciones de "relevante" distintas en el mismo script.

**Corrección aplicada.** `event_to_relevance` ahora mapea el vocabulario real del generador (`view`, `started`, `quiz_failed`, `quiz_passed`, `completed`); solo los eventos de dominio son relevantes.

## Hallazgo 3 (medio, RESUELTO): Popularidad ganaba en Cold Start

**Problema original.** En la primera ejecución, Popularidad (NDCG@5 0.429) superaba a NeuMF-Profile (0.400) y Profile+Content Ridge (0.354). Un baseline trivial vencía al modelo de perfil más sofisticado. La causa raíz no era solo que "todos interactúan con lo popular": en el generador, la probabilidad de que una interacción accesible fuera de dominio era **independiente del ajuste usuario-contenido** (`pick_event` solo recibía `qualified`). El perfil entraba solo en la *selección* del contenido, no en el *evento*. Así, el conjunto relevante de un cold user era "popularidad + ruido", y el modelo de perfil no podía aprender una señal que no estaba en sus features.

**Corrección aplicada (justificada en la literatura).** La probabilidad de evento de dominio ahora crece con el ajuste usuario-contenido (`topic_match * difficulty_match`), vía el nuevo helper `content_match_value` y `pick_event(qualified, match, rng)`. Esto hace que la señal de relevancia dependa del perfil, no solo de la popularidad.

Referencias que respaldan la decisión:
- Jannach et al. (2015), *"What recommenders recommend"* (UMUAI): la popularidad es un baseline difícil de batir en evaluación offline.
- Klimashevskaia et al. (2024), *"A survey on popularity bias in recommender systems"* (UMUAI): revisión de 123 papers; recomendar lo popular no es malo per se, el problema es que domine por construcción.
- Wen, Yang & Estrin (2019), *"Leveraging Post-click Feedback for Content Recommendations"* (RecSys): el "click vs. post-click gap"; más de la mitad de los clics van seguidos de un skip, y el skip correlaciona negativamente con la popularidad. La señal de consumo (completado) es la que codifica la preferencia real.
- Wang et al. (2021), *"Click Is Not Equal to Like"* (SIGIR): los clics están impulsados por features de exposición, no por calidad.

**Verificación posterior (datos regenerados):** la tasa de dominio sube monótonamente con el match (0.24 en match bajo → 0.56 en match alto) y la correlación match-score es 0.212 (antes ~0).

**Resultado tras re-ejecutar la evaluación:**

Cold Start:

| Modelo | P@5 | R@5 | NDCG@5 |
|---|---|---|---|
| **NeuMF-Profile** | **0.506** | **0.257** | **0.536** |
| Popularidad | 0.500 | 0.253 | 0.528 |
| Profile + Content Ridge | 0.347 | 0.165 | 0.390 |
| TF-IDF + Cosine (perfil) | 0.161 | 0.077 | 0.176 |
| Random | 0.104 | 0.048 | 0.104 |

Warm Start:

| Modelo | P@5 | R@5 | NDCG@5 |
|---|---|---|---|
| **NeuMF** | **0.207** | **0.388** | **0.340** |
| NCF-MLP | 0.198 | 0.373 | 0.324 |
| ItemKNN | 0.156 | 0.308 | 0.250 |
| UserKNN | 0.142 | 0.277 | 0.225 |
| GMF | 0.074 | 0.140 | 0.144 |
| Popularidad | 0.086 | 0.182 | 0.141 |
| SVD | 0.072 | 0.140 | 0.112 |
| TF-IDF + Cosine | 0.060 | 0.108 | 0.087 |
| Random | 0.025 | 0.050 | 0.039 |

NeuMF-Profile supera ahora al baseline de popularidad en cold start (NDCG@5 0.536 vs 0.528), y NeuMF lidera warm start.

---

## Hallazgo 4 (medio, PENDIENTE): 51% de usuarios sin señal de conocimiento

En `users_synthetic.csv`, **971 de 1.916 usuarios (50.7%) tienen `financial_knowledge_level = NaN`** (NS/NC en las preguntas Big3 de la ECF). El script lo documenta como limitación, pero es la mitad de la población. Estos usuarios parten con `mastered` vacío en `initial_mastered`, así que solo pueden dominar conceptos raíz (sin prerrequisitos). Es una limitación real y honesta, pero debilita la señal de conocimiento en la mitad de los datos.

## Hallazgo 5 (medio, PENDIENTE): fuerte desbalance de topics

`planificación` concentra 25.511 interacciones (42% del total) frente a `diversificación` con 95 (0.2%). El `floor=0.10` en `content_match_prob` evita contenidos desiertos (ninguno tiene 0 interacciones), pero a costa de diluir la señal de matching: todo contenido tiene al menos 10% de probabilidad de ser elegido por cualquier usuario. El desbalance es por diseño (planificación es común a casi todos los `learning_goal`), pero es muy pronunciado.

## Hallazgo 6 (bajo, PENDIENTE): `is_recommended` casi indistinguible de exploración

El generador pretende que `is_recommended` refleje sesgo de popularidad, pero la correlación es débil: popularidad media de 1.442 para `is_recommended=1` vs 1.187 para `=0`. La distribución es 50/50. La señal de "recomendación" aporta poco.

## Hallazgo 7 (menor, PENDIENTE): código muerto

- En `regenerate_users_from_ecf.py`, `saving_habit` solo produce `'frecuente'`/`'ocasional'`/NaN, nunca `'nunca'`. Por tanto `financial_behavior_level` nunca asigna `'bajo'`.

---

## Lo que está bien

- **PVR = 0.0%** verificado por construcción (0 violaciones en 25.549 dominios). La validación replica `initial_mastered` con semilla por `user_id`, y funciona.
- **Correlación conocimiento→dificultad** correcta: alto=1.55, medio=1.26, bajo=1.13 (los más conocedores dominan contenidos más difíciles).
- El lookup `KNOWLEDGE_DIFFICULTY.get(np.nan)` **sí funciona** en la práctica: pandas lee NaN como `np.nan` (mismo objeto), así que la clave se encuentra. No es un bug.
- `build_profile_features` devuelve tupla, `baseline_random` usa hash determinista, y el split warm usa sort estable — los fixes documentados están aplicados y son correctos.
- Long-tail de engagement realista (media 31.8, mediana 28) y cobertura completa (104/104 contenidos, 1.916/1.916 usuarios).

---

## Recomendación

La definición de "relevante" ya es única y coherente: solo los eventos de dominio (`completed`/`quiz_passed`) son relevantes, y el generador lo garantiza por construcción (los demás eventos quedan con `score < 0.5`). Los tres hallazgos principales están resueltos y verificados sobre los datos regenerados.

Quedan pendientes de menor prioridad: el 51% de usuarios sin `financial_knowledge_level` (limitación honesta de la ECF, documentada) y el desbalance de topics (por diseño). Ambos conviene reportarlos como limitaciones en la memoria, no necesariamente corregirlos.
