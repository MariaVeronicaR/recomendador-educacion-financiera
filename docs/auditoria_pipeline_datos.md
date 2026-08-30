# Auditoría de la pipeline de datos sintéticos y evaluación

Fecha: 2026-08-30
Alcance: `data/scripts/generate_interactions_v3.py`, `data/scripts/regenerate_users_from_ecf.py`, `data/scripts/evaluate_models.py`, y los CSV `users_synthetic.csv`, `interactions_synthetic_v3.csv`.

La auditoría se realizó verificando los scripts contra los datos reales (no solo leyendo el código).

---

## Hallazgo crítico: `quiz_failed` con `score >= 0.5` se cuenta como interacción relevante

Este es el problema más serio, y es una **inconsistencia interna del propio generador** que el evaluador hereda.

En `generate_interactions_v3.py` (`score_for_event`), `quiz_failed` recibe un score en `[0.4, 0.6]`:

```python
if event == "quiz_failed":
    return round(NPRNG.uniform(0.4, 0.6), 3)
```

Pero el docstring del script define que `score >= 0.5` = relevante, y que solo los eventos de dominio (`completed`/`quiz_passed`) son relevantes. Un `quiz_failed` es un **fallo**, no una interacción positiva. Sin embargo, la mitad de los `quiz_failed` (1.435 de 2.853, el 50%) caen en `[0.5, 0.6]` y por tanto se marcan como positivos.

El evaluador (`evaluate_models.py`) usa `score >= 0.5` para definir el conjunto relevante en `evaluate_warm_model` y `evaluate_cold_model`. Resultado: **un quiz suspendido cuenta como "relevante"** para Precision/Recall/NDCG. En el test warm, 226 de 4.624 relevantes (4.9%) son `quiz_failed`. Esto infla las métricas: son contenidos populares que el usuario intentó y falló, fáciles de recomendar.

**Verificación en datos:** 979 pares consolidados `quiz_failed` con `score>=0.5` quedan como relevantes en el dataset completo.

## Hallazgo alto: desajuste de vocabulario de eventos en el evaluador

`event_to_relevance` en `evaluate_models.py` mapea `viewed` y `disliked`, pero el generador produce `view`, `started` y `quiz_failed`:

```python
mapping = {"disliked": 0.0, "viewed": 0.2, "quiz_passed": 0.7, "completed": 1.0}
```

Los tres eventos reales `view`, `started`, `quiz_failed` caen en el `default` → relevance `0.0`. Esto no rompe la consolidación (completed/quiz_passed siguen ganando en el dedup), pero significa que la **consolidación usa relevancia por evento** mientras que la **evaluación usa relevancia por score** (`score>=0.5`). Son dos definiciones de "relevante" distintas dentro del mismo script, y la de evaluación es la que cuenta `quiz_failed` como positivo.

## Hallazgo medio: Popularidad gana en Cold Start

En `evaluation_metrics_all_models.csv`, en Cold Start **Popularidad (NDCG@5 0.429) supera a NeuMF-Profile (0.400)** y a Profile+Content Ridge (0.354). Un baseline trivial de popularidad vence al modelo de perfil más sofisticado. Esto es una señal de que el **sesgo de popularidad sintético domina sobre la señal de perfil** en los datos: como el generador hace que todos interactúen con los contenidos populares, recomendar lo popular a un usuario nuevo "funciona" mejor que usar su perfil. Cuestiona la validez del escenario cold start como prueba de los modelos de perfil.

## Hallazgo medio: 51% de usuarios sin señal de conocimiento

En `users_synthetic.csv`, **971 de 1.916 usuarios (50.7%) tienen `financial_knowledge_level = NaN`** (NS/NC en las preguntas Big3 de la ECF). El script lo documenta como limitación, pero es la mitad de la población. Estos usuarios parten con `mastered` vacío en `initial_mastered`, así que solo pueden dominar conceptos raíz (sin prerrequisitos). Es una limitación real y honesta, pero debilita la señal de conocimiento en la mitad de los datos.

## Hallazgo medio: fuerte desbalance de topics

`planificación` concentra 24.764 interacciones (40% del total) frente a `diversificación` con 78 (0.1%). El `floor=0.10` en `content_match_prob` evita contenidos desiertos (ninguno tiene 0 interacciones), pero a costa de diluir la señal de matching: todo contenido tiene al menos 10% de probabilidad de ser elegido por cualquier usuario. El desbalance es por diseño (planificación es común a casi todos los `learning_goal`), pero es muy pronunciado.

## Hallazgo bajo: `is_recommended` casi indistinguible de exploración

El generador pretende que `is_recommended` refleje sesgo de popularidad, pero la correlación es débil: popularidad media de 1.442 para `is_recommended=1` vs 1.187 para `=0`. La distribución es 50/50. La señal de "recomendación" aporta poco.

## Hallazgos menores (código muerto)

- En `regenerate_users_from_ecf.py`, `saving_habit` solo produce `'frecuente'`/`'ocasional'`/NaN, nunca `'nunca'`. Por tanto `financial_behavior_level` nunca asigna `'bajo'`.
- `event_to_relevance` incluye `viewed`/`disliked` que no existen en los datos.

---

## Lo que está bien

- **PVR = 0.0%** verificado por construcción (0 violaciones en 22.223 dominios). La validación replica `initial_mastered` con semilla por `user_id`, y funciona.
- **Correlación conocimiento→dificultad** correcta: alto=1.49, medio=1.26, bajo=1.14 (los más conocedores dominan contenidos más difíciles).
- El lookup `KNOWLEDGE_DIFFICULTY.get(np.nan)` **sí funciona** en la práctica: pandas lee NaN como `np.nan` (mismo objeto), así que la clave se encuentra. No es un bug.
- `build_profile_features` devuelve tupla, `baseline_random` usa hash determinista, y el split warm usa sort estable — los fixes documentados están aplicados y son correctos.
- Long-tail de engagement realista (media 31.8, mediana 28) y cobertura completa (104/104 contenidos, 1.916/1.916 usuarios).

---

## Recomendación prioritaria

Decidir una única definición de "relevante". La más coherente con el diseño pedagógico del generador sería que `quiz_failed` **nunca** sea positivo (p. ej. `score_for_event` para `quiz_failed` en `[0.3, 0.5)`), o que el evaluador derive la relevancia del evento en lugar del score. Esto cambiaría las métricas reportadas, sobre todo en cold start.
