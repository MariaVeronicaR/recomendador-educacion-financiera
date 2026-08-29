# Plan de ajustes al generador de interacciones sintéticas

**Fecha:** 2026-08-28
**Estado:** ✅ **Implementado** (ver §12 "Registro de implementación").
**Ámbito:** Correcciones y mejoras sobre `data/scripts/generate_interactions.py` para que la data generada alimente correctamente la comparativa de modelos (`docs/Comparativa_modelos_recomendacion.md`).
**Base:** Auditoría de `docs/plan_generar_interacciones.md`, `data/scripts/generate_interactions.py` y `data/interactions_synthetic.csv` (seed 42, 2000 usuarios, 24845 interacciones).

---

## 0. Resumen ejecutivo

La auditoría detectó **un bloqueante** y **varios desajustes** entre el plan técnico, la implementación y lo que la comparativa de modelos necesita. Este plan los ordena por prioridad y especifica, para cada uno, el cambio concreto, el archivo/línea afectado y cómo validarlo.

| # | Prioridad | Cambio | Tipo |
|---|---|---|---|
| 1 | 🔴 Bloqueante | Persistir los perfiles de usuario (`users_synthetic.csv`) | Fidelidad plan↔comparativa |
| 2 | 🟠 Alta | Separar y etiquetar el cold start | Fidelidad comparativa |
| 3 | 🟠 Alta | Emitir `session_id` | Fidelidad plan↔implementación |
| 4 | 🟡 Media | Usar realmente los datos Big3 de la ECF para calibrar θ | Fidelidad plan↔implementación |
| 5 | 🟡 Media | Corregir la métrica de completado por dificultad | Corrección de validación |
| 6 | 🟡 Media | Reforzar la señal de aprendizaje temporal | Calibración |
| 7 | 🟡 Media | Ajustar la densidad a 1–5% | Calibración |
| 8 | 🟢 Baja | `position` realista / `outcome` de quiz | Mejora opcional |

---

## 1. 🔴 Bloqueante — Persistir los perfiles de usuario

### Problema
El script solo escribe `interactions_synthetic.csv` y los metadatos. Los perfiles latentes (edad, sexo, educación, empleo, productos, θ, nivel de conocimiento, intereses, riesgo, formato, actividad) se generan en `sample_user_profiles` pero **se descartan al final**. La comparativa necesita esas features para el feature-aware NeuMF (modelo propuesto), el content-based y el KG/reglas ([Comparativa §2](Comparativa_modelos_recomendacion.md#L45)). Sin ellas no se puede construir la matriz de features ni ejecutar los modelos.

### Cambio
En `main()` (FASE 5), tras escribir el CSV de interacciones, escribir `users_synthetic.csv` con una fila por usuario. Columnas:

- `user_id`
- `age`, `age_group`, `sex`
- `education_level`, `employment_status`
- `products` (lista separada por `;`)
- `theta` (conocimiento continuo), `knowledge_level` (bajo/medio/alto)
- `interests` (dict topic→valor, serializado como JSON)
- `risk`, `format_pref` (JSON), `activity`, `learn_rate`, `noise_level`
- `n_interactions` (nº de interacciones reales del usuario, para etiquetar cold start — ver §2)
- `n_completed` (nº de completados)

### Validación
- El CSV tiene 2000 filas (una por usuario).
- `user_id` es consistente con `interactions_synthetic.csv` (join sin huérfanos).
- `n_interactions` coincide con `value_counts` del CSV de interacciones.

---

## 2. 🟠 Alta — Separar y etiquetar el cold start

### Problema
La comparativa §4 exige dos escenarios: usuarios con historial en test y usuarios **fríos** (sin interacciones en test, solo features). El generador produce 36 usuarios con 0 interacciones y 419 con <5 de forma natural, pero **no los etiqueta ni garantiza un split** reproducible.

### Cambio
- Añadir la columna `n_interactions` al perfil (ya contemplada en §1).
- Añadir una columna `cold_start` (bool) al perfil: `True` si `n_interactions == 0`.
- Documentar en los metadatos (`generation_metadata.json`) el criterio de cold start y el número de usuarios fríos, para que la evaluación pueda reservarlos de forma reproducible.

### Validación
- `cold_start` es `True` exactamente para los 36 usuarios sin interacciones.
- El número de usuarios fríos queda registrado en los metadatos.

---

## 3. 🟠 Alta — Emitir `session_id`

### Problema
El plan §4.1 lista `session_id` como columna del dataset, pero el script no la emite. Además, la comparativa §3.3 justifica descartar los modelos secuenciales con "no hay secuencias reales de interacción"; si se emite `session_id`, esa justificación se debilita y hay que revisarla.

### Cambio
- En `simulate_user`, asignar un `session_id` único por sesión (p. ej. `f"{user_id}-{sess_idx}"` o un contador global).
- Añadir la columna al CSV de interacciones.
- **Revisar la justificación de la comparativa**: si se emiten sesiones, o bien se reformula el argumento de §3.3 (las sesiones existen pero no se usan para optimizar secuencias), o bien se decide no emitirlas. **Decisión a tomar antes de implementar** (ver §9).

### Validación
- Cada fila tiene `session_id` no nulo.
- El número de sesiones únicas por usuario es coherente con `build_sessions`.
- Las interacciones de una misma sesión comparten timestamp cercano.

---

## 4. 🟡 Media — Usar realmente los datos Big3 de la ECF para calibrar θ

### Problema
El plan §2.1/§2.2 dice que θ se imputa desde **Big3 + educación + productos**. El script calcula `big3_score` y `educ_big3` en `load_ecf_distributions`, pero **`educ_big3` es código muerto**: `sample_user_profiles` solo usa `educ_dist`, `work_dist` y `prod_rates`. El θ final se construye con pesos hardcodeados (`theta_educ_weights`) + bonus por productos + ruido, ignorando las respuestas reales de las Big3.

### Cambio
- En `load_ecf_distributions`, exponer la distribución de `big3_score` por nivel educativo (`educ_big3` ya existe) y, opcionalmente, la distribución global de `big3_score`.
- En `sample_user_profiles`, muestrear el `big3_score` del usuario condicionado a su educación (o usar la media `educ_big3[education]`), y usarlo como **base de θ** en lugar de (o combinado con) `theta_educ_weights`.
- Mantener el bonus por productos y el ruido.
- Documentar la imputación como limitación (plan §2.2 ya lo pide).

### Validación
- La distribución de `knowledge_level` resultante es plausible (p. ej. ~50–60% bajo, ~30% medio, ~10–15% alto, coherente con el README de la ECF).
- `educ_big3` deja de ser código muerto (se referencia en el muestreo).

---

## 5. 🟡 Media — Corregir la métrica de completado por dificultad

### Problema
**Nota de auditoría (corregida durante la implementación):** la afirmación original de que el script reportaba el *share* de completados era **incorrecta**. El código ya calculaba `completion_by_difficulty` como `groupby("difficulty")["completed"].mean()` (la **tasa** de completado), y el `validation_report.json` ya mostraba los valores correctos (0.658/0.27/0.057). El "share" (0.901/0.098/0.000) lo calculó la auditoría y lo atribuyó erróneamente al script. **No había bug.**

### Cambio
Solo se añadió un comentario aclaratorio en `validate()` para dejar explícito que la métrica es la tasa de completado, no el share. Sin cambio funcional.

### Validación
- `completion_by_difficulty` sigue siendo la tasa de completado por dificultad.
- El check `completion_decreasing_ok` sigue pasando.

---

## 6. 🟡 Media — Reforzar la señal de aprendizaje temporal

### Problema
`learning_trend` = 0.0057 (escala 0–2), esencialmente plano. El plan §5.7/§6.6 exige "conocimiento que mejora con el tiempo". La causa: casi todo lo completado es básico (dificultad media 0.099) y el término de competencia para contenidos avanzados usa `theta_global` (estático), no la maestría que evoluciona con BKT.

### Cambio (implementado)
Se aplicaron **tres** cambios combinados:

- **a)** En el logit de competencia, usar la **maestría media del usuario sobre los conceptos del contenido** (`theta_c`) en lugar de `theta_global` estático, para que el acceso a avanzados dependa del conocimiento que evoluciona.
- **b)** **Normalizar la escala de dificultad a [0,1]** (`diff_map`: básico 0.0, intermedio 0.5, avanzado 1.0). Antes era 0/1/2, incompatible con la maestría (0–1): para contenido intermedio (dificultad 1.0) la maestría nunca superaba 0.98, así que `theta_c − diff` era casi siempre negativo y los usuarios apenas completaban intermedio. Este fue el cambio decisivo.
- **c)** Añadir un **factor de novedad** a la selección de candidatos: el contenido cuyos conceptos ya domina el usuario se muestra menos (`interest_probs × (0.1 + 0.9·novelty)`), de modo que el usuario progrese a contenido nuevo en vez de repetir lo aprendido. También se añadió un factor de **preparación** (`w_readiness`) que pondera la maestría de prerrequisitos en la selección.

### Validación
- `learning_trend` es **positivo y estable** entre seeds: 0.024 (seed 42), 0.043 (seed 7), 0.030 (seed 123), todos > 0.02.
- La dificultad media de lo completado es ~0.35 (entre básico e intermedio), con 64% básico / 34% intermedio / 2% avanzado.
- No se rompen los demás checks (8/8 en los tres seeds).

---

## 7. 🟡 Media — Ajustar la densidad a 1–5%

### Problema
El plan §5.1/§6.1 fija sparsity en 1–5%; el código aceptaba hasta 10% y el resultado era 8.4%. Es un dataset denso para recomendación, lo que puede inflar las métricas de ranking.

### Cambio (implementado)
- **`activity_mu`** de `log(0.42)` a `log(0.15)` (interacciones/semana): es el principal control de la densidad. `logit_base` y `exposure_candidates` tienen poco efecto porque la densidad la domina el nº de interacciones por usuario.
- **`exposure_candidates`** de 12 a 4.
- **Umbral del check** `density_ok` a `0.01 <= density <= 0.05` (alineado con el plan).

### Validación
- `density` en ~3% (0.031 seed 42, 0.029 seed 7, 0.030 seed 123).
- Tasa de completado global ~64% (dentro de 40–70%).
- `content_coverage` = 1.0 (ningún contenido huérfano).

---

## 8. 🟢 Baja — `position` realista y `outcome` de quiz (opcional)

### Problema
- `position` es aleatorio (`rng.integers(1,11)`) sin relación con la posición real de recomendación, aunque el plan §4.1 dice que sirve "para modelar posición".
- `outcome` es un proxy fabricado (completado + slip/guess); no hay quizzes reales.

### Cambio (opcional, solo si aporta a la comparativa)
- **`position`**: asignar la posición según el orden de selección de candidatos en la sesión (los primeros candidatos expuestos tienen posición baja), para que sea modelable.
- **`outcome`**: documentar explícitamente que es un proxy (no hay quizzes en el catálogo), o eliminarlo si no se usa.

### Validación
- `position` correlaciona con el orden de exposición.
- La documentación aclara el carácter de proxy de `outcome`.

---

## 9. Decisiones pendientes antes de implementar

1. **`session_id` sí o no** (§3): **decidido — emitirlo.** Se emite `session_id` (formato `{user_id}-{sess_idx}`). **Pendiente:** revisar la justificación de la comparativa §3.3 (modelos secuenciales), que dice "no hay secuencias reales de interacción". Con `session_id` emitido, conviene reformularla como "las sesiones existen pero no se optimizan secuencias".
2. **Enfoque para reforzar el aprendizaje** (§6): **decidido — combinar (a) + (b) + (c).** Se usó `theta_c` en avanzados, se normalizó la dificultad a [0,1] y se añadió el factor de novedad. Resultado: señal de aprendizaje positiva y estable.
3. **Alcance de §8**: **decidido — no implementar por ahora.** `outcome` queda como proxy (documentado en los metadatos); `position` realista solo si la comparativa va a modelar position bias.

---

## 10. Orden de implementación y validación

1. **§1 + §2** (persistir perfiles + etiquetar cold start): bloqueante, sin riesgo para el resto. Validar joins y conteos.
2. **§5** (corregir métrica de completado): cambio aislado en `validate()`. Validar contra los valores reales.
3. **§4** (usar Big3): re-calibrar θ. Validar distribución de `knowledge_level`.
4. **§7** (densidad): ajustar parámetros. Validar densidad + completado + cobertura.
5. **§6** (aprendizaje): reforzar señal. Validar `learning_trend` y que no rompe otros checks.
6. **§3** (session_id): tras decidir §9.1. Validar coherencia de sesiones.
7. **§8** (opcional): al final, si se decide.

Tras cada cambio, re-ejecutar `python3 data/scripts/generate_interactions.py --seed 42` y comprobar que **todos los checks de `validation_report.json` pasan** y que los valores corregidos (§5, §6, §7) están en rango.

---

## 11. Criterio de aceptación

El generador se considera listo para alimentar la comparativa cuando:

1. `users_synthetic.csv` existe con los perfiles y la etiqueta de cold start (§1, §2).
2. `interactions_synthetic.csv` incluye `session_id` (si se decide §9.1) y las columnas del plan §4.1.
3. `validation_report.json` pasa todos los checks, con `completion_by_difficulty` como tasa real (§5), `learning_trend` claramente positivo (§6) y `density` en 1–5% (§7).
4. `generation_metadata.json` documenta seed, parámetros, criterio de cold start y limitaciones (imputación Big3, proxy de `outcome`).
5. La comparativa puede construir la matriz de features de usuario y separar los escenarios con historial / cold start sin tocar los datos a mano.

---

## 12. Registro de implementación

**Fecha:** 2026-08-28. Todos los cambios aplicados a `data/scripts/generate_interactions.py` y verificados con `python3 data/scripts/generate_interactions.py --seed 42`.

### Cambios aplicados

| § | Cambio | Detalle |
|---|---|---|
| 1 | `users_synthetic.csv` | Nueva función `build_users_df()`; escribe perfiles + `n_interactions`, `n_completed`, `cold_start`. |
| 2 | Etiqueta cold start | Columna `cold_start` (True si `n_interactions == 0`); `n_cold_start_users` y criterio en metadatos. |
| 3 | `session_id` | Columna `{user_id}-{sess_idx}` en cada interacción. |
| 4 | θ desde Big3 | `sample_user_profiles` muestrea `big3` condicionado a educación y deriva θ; nuevo parámetro `theta_big3_scale`; se elimina `theta_educ_weights`. |
| 5 | Métrica completado | Solo comentario aclaratorio (no había bug; ver §5). |
| 6 | Aprendizaje | `theta_c` en avanzados; dificultad normalizada a [0,1]; factor de novedad + `w_readiness` en selección. |
| 7 | Densidad | `activity_mu` → log(0.15), `exposure_candidates` → 4, umbral `density_ok` → 1–5%. |
| 8 | Opcional | No implementado (documentado como limitación). |

### Resultados de validación (seed 42)

| Métrica | Antes | Después |
|---|---|---|
| `density` | 0.084 | **0.031** ✓ |
| `completion_rate` | 0.575 | 0.639 |
| `completion_by_difficulty` | 0.66/0.27/0.06 | 0.72/0.54/0.41 |
| `learning_trend` | 0.0057 | **0.024** ✓ |
| `simple_model_auc` | 0.694 | 0.62 |
| `checks_passed` | 8/8 | **8/8** |

### Estabilidad entre seeds

| Seed | density | learning_trend | checks |
|---|---|---|---|
| 42 | 0.031 | 0.024 | 8/8 |
| 7 | 0.029 | 0.043 | 8/8 |
| 123 | 0.030 | 0.030 | 8/8 |

### Archivos de salida (seed 42)

- `data/interactions_synthetic.csv` — 9612 interacciones, 2000 usuarios, 103 contenidos, con `session_id`.
- `data/users_synthetic.csv` — 2000 perfiles con features del cuestionario + etiqueta cold start (214 usuarios fríos).
- `data/generation_metadata.json` — seed, parámetros, criterio de cold start, validación.

### Pendiente

- **Revisar la justificación de la comparativa §3.3** (modelos secuenciales) ahora que `session_id` se emite.
- **§8 opcional** (`position` realista, `outcome` de quiz) si la comparativa lo necesita.
