# Plan técnico: generación de interacciones sintéticas usuario–contenido

**Fecha:** 2026-08-28
**Ámbito:** Diseño y metodología (sin implementación de modelos de recomendación ni generación del dataset)
**Objetivo:** Producir un dataset de interacciones sintéticas de alta calidad entre usuarios jóvenes españoles (18–34) y contenidos de educación financiera, apto para entrenar y evaluar sistemas de recomendación.

> **Restricción de partida:** este plan se construye **desde cero**. No se utiliza ni se consulta ningún dataset de interacciones sintéticas previo (`interactions_synthetic.csv` ni variantes). Las únicas fuentes de información son los microdatos de la **ECF 2021** y los catálogos `concepts.csv`, `content_concept_map.csv`, `contents.csv` y `prerequisites.csv`.

---

## 0. Resumen ejecutivo

Se propone un **generador probabilístico híbrido** que combina cuatro bloques:

1. **Perfiles de usuario latentes** calibrados con los microdatos de la ECF 2021 (conocimiento, comportamiento, actitud, demografía, tenencia de productos e intereses temáticos).
2. **Modelo de preferencia usuario–contenido** basado en factores latentes + atributos observables del contenido (tema, formato, dificultad, riesgo, relación con inversión).
3. **Modelo de competencia/dificultad tipo IRT** (Teoría de Respuesta al Ítem) que modula la probabilidad de *completar* un contenido según el conocimiento previo del usuario y la dificultad del contenido.
4. **Progresión del aprendizaje tipo BKT** (Bayesian Knowledge Tracing) sobre el grafo de prerrequisitos, de modo que el conocimiento evoluciona con las interacciones y los prerrequisitos condicionan el acceso a contenidos avanzados.

Sobre esta base se inyectan **ruido y comportamiento imperfecto** (misclicks, curiosidad, popularidad, abandono, no-exposición) y **distribuciones de cola larga** (popularidad de contenidos y nivel de actividad de usuarios), y se genera una **línea temporal global** con timestamps realistas para permitir evaluaciones temporales sin data leakage.

La prioridad es que el dataset **no sea artificialmente fácil de predecir**: la preferencia no debe ser una función determinista de atributos observables, debe haber factores latentes no observables, ruido sustancial y heterogeneidad entre usuarios.

---

## 1. Revisión de literatura y metodologías relevantes

### 1.1 Generación de datos sintéticos de interacciones en recomendación

La literatura converge en un conjunto de patrones metodológicos:

- **Modelos generativos probabilísticos** (HYDRA, KDD 2025): generan interacciones a partir de tres factores — *user–item matching* (afinidad latente), *user engagement level* (nivel de actividad) e *item popularity* — modelando engagement y popularidad como **mezclas de distribuciones de cola larga** (power-law, log-normal, exponencial, stretched-exponential). Es el marco más directamente aplicable a nuestro caso.
- **Factores latentes + atributos** (SPUP, McGill 2017; LAFS, 2024): se genera una matriz de preferencia densa `R ≈ UᵀV` (Probabilistic Matrix Factorization) y luego se **esparcifica** usando presupuestos de actividad por usuario (exponencial) y popularidad por ítem (power-law). Reproduce fielmente datasets reales (MovieLens, Epinions).
- **Expansiones fractales / Kronecker** (Google AI, 2019): preservan distribuciones de cola gruesa de actividad, popularidad y espectro de valores singulares al escalar datasets.
- **Métodos generativos profundos** (GANs, VAEs, diffusion — GANRS, SDRM): útiles pero requieren datos reales de partida y son menos controlables; no son la mejor opción cuando se parte de cero y se quiere control explícito de los mecanismos.

**Conclusión para nuestro caso:** el enfoque más adecuado es el **probabilístico híbrido** (factores latentes + atributos + cola larga + ruido), porque permite control explícito de cada mecanismo, es reproducible, no requiere un dataset real de interacciones de partida y evita los patrones artificiales de los generadores puramente deterministas.

### 1.2 Generación de datos de interacción en e-learning y aprendizaje personalizado

- **IRT (Teoría de Respuesta al Ítem)** es el estándar para modelar la probabilidad de respuesta correcta en función de la habilidad del estudiante (θ) y la dificultad del ítem (b): `P(correcto) = c + (1−c)·σ(a(θ−b))`. Es la base para modelar *dificultad del contenido* y *conocimiento previo*.
- **BKT (Bayesian Knowledge Tracing)** modela el dominio de una habilidad como un estado latente binario (HMM) con parámetros `p(L₀)` (probabilidad inicial de dominio), `p(T)` (probabilidad de aprender), `p(S)` (slip) y `p(G)` (guess). Es el estándar para modelar **progresión del aprendizaje**.
- **Prerrequisitos en BKT** (Mu, Wang, Andersen, Brunskill — L@S 2018): se estructuran las habilidades en un grafo de prerrequisitos y se **reduce la probabilidad de aprender** un concepto en función del número de prerrequisitos no dominados. Esto es exactamente lo que necesitamos para `prerequisites.csv`.
- **Simulación de estudiantes** (DAISim, CIKM 2023; SynthEd, 2026; SynEdu-HEDL, 2026): agentes con persona y trayectorias de aprendizaje; validan con fidelidad estadística y utilidad analítica (modelos dentro de 1–5% del rendimiento sobre datos reales).
- **Dificultad por atributos** (Schütt et al., 2023): generaliza la dificultad IRT a partir de atributos del ejercicio, útil cuando hay pocos datos por ítem — aplicable a nuestros 105 contenidos.

### 1.3 Ruido, abandono y comportamiento imperfecto

- **ANCHOR** (arXiv): modela cinco tipos de ruido no basado en preferencia — *misclick*, *curiosity-driven*, *caption-biased*, *popularity-biased* y *position-biased*.
- **UDT** (RecSys 2024): separa *willingness* (intención) de *action* (acción) mediante un proceso de Markov, modelando la inconsistencia usuario-específica (clics descuidados, misclicks).
- **Exposure bias** (WSDM 2024): las interacciones dependen de qué ítems se *exponen* al usuario; modelar la exposición es clave para no confundir "no le gusta" con "no lo vio".

### 1.4 Evaluación y data leakage

- **Ji et al. (ACM TOIS 2022)**: los splits aleatorios, por usuario y leave-one-out **filtran información temporal**; solo el **split por punto temporal global** evita el leakage. El impacto puede cambiar la precisión hasta ±89,5%.
- **Time to Split** (RecSys 2025): para recomendadores secuenciales, el **Global Temporal Split (GTS)** con target *successive* es el más realista.
- **SplitLight** (2026): audita splits por cold-start, leakage temporal, distribution shift y colisiones de timestamp.
- **Sun (SIGIR 2023)**: el 59% de los papers usan splits que ignoran la línea temporal global; el baseline de popularidad está mal definido bajo splits no temporales.

**Implicación directa:** nuestro generador debe producir **timestamps globales realistas** y documentar el proceso para que la evaluación pueda usar splits temporales sin leakage.

### 1.5 Alfabetización financiera de jóvenes españoles (ECF 2021)

Datos publicados del BdE/CNMV (Hospido et al., 2023) relevantes para calibrar perfiles:

- **Conocimiento (Big3)**: inflación 65% correctas, interés compuesto 41%, diversificación 52%; solo 19% acierta las tres. Jóvenes 18–34: ~52% promedio; los 18–24 tienen la mayor tasa de error en interés compuesto (47,5%) y diversificación (36,3%).
- **Brechas**: género (58% hombres vs 48% mujeres), educación (43% primaria → 64% universitaria), ingresos (43% <15k€ → 67% >47k€).
- **Comportamiento**: 70% ahorró en los últimos 12 meses; 25% vive en hogares con gastos > ingresos; 6% solo aguantaría <1 semana sin endeudarse; 41% recibió formación financiera.
- **Cripto**: los jóvenes 18–34 son el grupo con mayor familiaridad (93% las conocen; 13% las han adquirido).
- **Determinantes en jóvenes** (estudio Zaragoza): la **inclusión financiera** (número de productos contratados) es un mecanismo de aprendizaje más intenso que la renta o la demografía.

---

## 2. Aprovechamiento de los microdatos de la ECF 2021

La ECF proporciona **1.916 jóvenes 18–34** con variables reales. Se usará para **calibrar los perfiles de usuario sintéticos**, no para copiar filas.

### 2.1 Variables ECF → perfil de usuario

| Dimensión del perfil | Variable(s) ECF | Uso |
|---|---|---|
| Edad / grupo | `a0400` (año nacimiento) | `age_group` 18–24 / 25–34 |
| Sexo | `a0100` | `sex` — **corregir sesgo** (ver §2.2) |
| Educación | `e0100` (QD9) | `education_level` (posgrado/universidad/bachillerato/secundaria/primaria) |
| Empleo | `a1500` (QD10) | `employment_status` (empleado/estudiante/desempleado/autónomo) |
| Conocimiento financiero | `k0600` (inflación), `k0100` (interés compuesto), `k1003` (diversificación) | `financial_knowledge_level` (bajo/medio/alto) + **puntuación continua θ** |
| Comportamiento de ahorro | `b0130b` (QF3) | `saving_habit` |
| Tenencia de productos | `b1000a`–`b1000j` (cuenta corriente, ahorro, acciones, bonos, fondos, cripto, seguro, pensiones) | `product_ownership` → **intereses temáticos** |
| Actitud | `i0100`, `j0100`, `j0110`, `j0200`, `j0400`, `j0600`, `j0810` | `financial_attitude_level`, tolerancia al riesgo |
| Ingresos | `f0900a`, `f1000a`, `f1100`, `f1200`, `f1300` | `income_band` (opcional, para matizar intereses) |

### 2.2 Decisiones metodológicas sobre la ECF

1. **Corregir el sesgo de género.** La submuestra de jóvenes 18–34 de la ECF está fuertemente sesgada a hombres (~85/15), un artefacto muestral que **no refleja la realidad** (~50/50). Para que los perfiles sean representativos de la población joven española, se **rebalanceará el sexo a ~50/50** manteniendo el resto de correlaciones (educación, empleo, conocimiento) condicionadas al sexo según los datos reales. Esto evita que los recomendadores aprendan un sesgo de género artificial.

2. **Tratar los NS/NC de las preguntas Big3 con cuidado.** ~50% de los jóvenes no responden a las Big3 (códigos −97/−98/−99). No deben contarse como "fallo" (inflaría el grupo "bajo") ni excluirse (sesgo de selección). Se propone: (a) para la **puntuación continua θ**, imputar con un modelo condicionado a educación/empleo/productos; (b) para la **etiqueta categórica**, usar la puntuación imputada. Documentar la imputación como limitación.

3. **Derivar intereses temáticos desde la tenencia de productos** (mecanismo de aprendizaje por inclusión financiera, según la literatura): quien tiene acciones → interés en inversión/riesgo; quien tiene hipoteca → interés en hipotecas; quien tiene deuda → interés en deuda/préstamos; estudiante → presupuesto/ahorro; etc. Esto ancla los intereses en comportamiento real, no en valores inventados.

4. **No copiar filas, sino calibrar distribuciones y correlaciones.** Se muestrean perfiles que respetan las distribuciones marginales y las correlaciones observadas (p. ej. educación↔conocimiento, empleo↔ingresos), pero cada usuario sintético es una combinación nueva con ruido, para no duplicar registros reales.

5. **Nivel de actividad y tolerancia al riesgo** no están directamente en la ECF; se modelan como variables latentes con distribuciones de cola larga (ver §4.2), correlacionadas débilmente con conocimiento y empleo.

---

## 3. Uso de los catálogos de contenido

### 3.1 `contents.csv` (105 contenidos)

Proporciona los **atributos observables** de cada ítem que alimentan la preferencia y la dificultad:

- `topic` y `subtopic` → **afinidad temática** (el usuario tiene un vector de interés por topic).
- `difficulty` (básico/intermedio/avanzado) → **parámetro de dificultad b** en el modelo IRT (mapeo ordinal a escala continua).
- `format` (artículo web, PDF, simulador, calculadora, vídeo, curso web, glosario, blog, herramienta) → **afinidad de formato** (algunos usuarios prefieren interactivos, otros lectura).
- `risk_level` (bajo/medio/alto) → modula la interacción según la **tolerancia al riesgo** del usuario (un usuario conservador evita contenidos de alto riesgo).
- `is_investment_related` (si/no) → refuerza la afinidad con usuarios con interés inversor.
- `prerequisites` (conceptos) → enlaza con el grafo de prerrequisitos.
- `source` → puede usarse como factor de popularidad base (contenidos de fuentes más conocidas, p. ej. Finanzas para Todos, tienden a ser más visitados).

### 3.2 `concepts.csv` (30 conceptos)

Define el **espacio de conocimiento** sobre el que opera la progresión del aprendizaje:

- `topic` → agrupa conceptos en temas (coherente con `contents.topic`).
- `difficulty` (básico/intermedio/avanzado) → nivel de partida del concepto en el grafo de conocimiento.
- Cada usuario tiene un **estado de dominio por concepto** (probabilidad de dominarlo), que evoluciona con BKT.

### 3.3 `content_concept_map.csv` (123 mapeos)

Conecta cada contenido con los conceptos que cubre (`coverage_type: directa`). Es el puente entre **interacción con contenido** y **aprendizaje de conceptos**:

- Al interactuar/completar un contenido, el usuario **aprende** los conceptos que cubre (con probabilidad `p(T)`).
- La **dificultad efectiva** de un contenido se agrega desde la dificultad de sus conceptos (p. ej. media ponderada).
- Un contenido que cubre varios conceptos (p. ej. C021 cubre C04 y C10) enseña varios a la vez.

### 3.4 `prerequisites.csv` (35 aristas)

Define el **grafo de prerrequisitos entre conceptos** (p. ej. C12 Inversión requiere C02 Ahorro, C07 Inflación, C06 Interés compuesto, C13 Riesgo). Se usa para:

- **Reducir la probabilidad de interactuar** con contenidos cuyos conceptos tienen prerrequisitos no dominados (el usuario "no está preparado").
- **Reducir la probabilidad de aprender** un concepto si sus prerrequisitos no están dominados (siguiendo Mu et al., L@S 2018).
- **Modelar progresión lógica**: los usuarios tienden a interactuar primero con conceptos básicos y luego con avanzados, respetando el grafo.

---

## 4. Metodología de generación

### 4.1 Variables de cada interacción

Cada fila del dataset de interacciones contendrá:

| Variable | Tipo | Descripción |
|---|---|---|
| `interaction_id` | int | Identificador único |
| `user_id` | str | `U0001`… |
| `content_id` | str | `C001`… |
| `timestamp` | datetime | Marca temporal global (para splits temporales) |
| `session_id` | int | Agrupación de interacciones en sesiones |
| `interaction_type` | cat | `view` (vista), `read` (lectura/completado), `tool` (uso de calculadora/simulador), `quiz` (respuesta a pregunta) |
| `duration_seconds` | float | Tiempo dedicado (log-normal) |
| `completed` | bool | Si completó el contenido (1) o lo abandonó (0) |
| `outcome` | cat | `correct`/`incorrect`/`na` — solo si hay quiz |
| `source` | cat | `recommended` / `search` / `browse` / `direct` |
| `position` | int | Posición en la lista si fue recomendado (para modelar posición) |
| `concepts_covered` | list | Conceptos del contenido (derivado del mapa) — útil para validación |

**Nota:** `user_id` y `content_id` se referencian a los catálogos; el dataset de interacciones **no** duplica los atributos de usuario/contenido (se unen en la fase de modelado), evitando redundancia y facilitando splits limpios.

### 4.2 Perfiles de usuario (capa latente)

Cada usuario sintético `u` tiene:

- **Atributos observables** (de la ECF): `age_group`, `sex`, `education_level`, `employment_status`, `income_band`, `product_ownership`.
- **Conocimiento inicial** `θ_u` (escalar continuo) y **estado de dominio por concepto** `P(domina c)` inicial, derivados de la ECF (Big3 imputados) y coherentes con educación/empleo.
- **Vector de interés temático** `α_u ∈ R^K` (K = nº de topics), derivado de `product_ownership` + empleo + ruido. Alto en los temas que le tocan (inversión si tiene acciones, deuda si tiene deuda, etc.), con ruido para no ser determinista.
- **Preferencia de formato** `φ_u` (vector sobre formatos).
- **Tolerancia al riesgo** `ρ_u ∈ [0,1]` (latente, correlacionada con conocimiento y actitud).
- **Nivel de actividad** `λ_u` (interacciones/semana) muestreado de una **distribución de cola larga** (log-normal o power-law truncada) — pocos usuarios muy activos, muchos poco activos.
- **Tasa de aprendizaje** `p(T)_u` (velocidad de aprendizaje, heterogénea).
- **Nivel de ruido** `η_u` (propensión a misclicks/curiosidad, heterogénea).

### 4.3 Probabilidad de interacción

La probabilidad de que el usuario `u` interactúe con el contenido `c` en el instante `t` se descompone en factores multiplicativos (logit):

```
P(interactuar | u, c, t) = σ( logit_base + preferencia + competencia + exposición + popularidad + ruido )
```

donde:

- **`preferencia`** = `α_u · topic_c` (afinidad temática) + `φ_u · format_c` (afinidad de formato) + `β_riesgo · (ρ_u − riesgo_c)` (tolerancia al riesgo vs riesgo del contenido) + `β_inv · I(investment_c) · interés_inversor_u`.
- **`competencia`** = término IRT: si el contenido es demasiado difícil para el conocimiento actual del usuario sobre sus conceptos, la probabilidad de *completarlo* baja (y la de abandono sube). La **dificultad efectiva** `b_c` se agrega desde la dificultad de los conceptos que cubre.
- **`prerrequisitos`** = penalización si el usuario no domina los prerrequisitos de los conceptos del contenido: `−γ · nº_prerrequisitos_no_dominados`. Esto hace que un usuario "no preparado" tenga menos probabilidad de entrar en contenidos avanzados.
- **`exposición`** = no todos los contenidos son visibles. Se modela un mecanismo de exposición: el usuario "ve" un subconjunto de contenidos (los de sus temas de interés + los populares + los recomendados). Si no está expuesto, no puede interactuar. Esto separa "no le gusta" de "no lo vio" (exposure bias).
- **`popularidad`** = `β_pop · log(popularidad_c)`, donde `popularidad_c` sigue una **distribución de cola larga** (pocos contenidos muy populares). La popularidad es un atributo del contenido, no del usuario, e introduce no-determinismo.
- **`ruido`** = término estocástico por usuario (misclicks, curiosidad) que permite interactuar con contenidos fuera de interés.

### 4.4 Modelo de competencia y dificultad (IRT)

Para modelar la probabilidad de **completar** un contenido (no solo de entrar):

```
P(completar | u, c) = c_guess + (1 − c_guess) · σ( a_c · (θ_u,c − b_c) )
```

- `θ_u,c` = conocimiento del usuario sobre los conceptos de `c` (agregado de su estado de dominio por concepto).
- `b_c` = dificultad del contenido (de `contents.difficulty` + dificultad de conceptos).
- `a_c` = discriminación (cuánto separa el contenido entre usuarios con distinto conocimiento).
- `c_guess` = probabilidad de "adivinar" (baja para contenidos largos, mayor para quizzes).

Si `P(completar)` es baja, el usuario **abandona** (interacción `view` sin `completed`). Esto modela el **abandono/no-interacción** de forma realista: los usuarios entran en contenidos demasiado difíciles y los dejan a medias.

### 4.5 Progresión del aprendizaje (BKT + prerrequisitos)

Tras cada interacción completada con el contenido `c`, el estado de dominio de cada concepto `k` cubierto por `c` se actualiza:

```
P(domina k | nueva evidencia)  ←  BKT update con p(T)_u
```

- Si el usuario **completa** el contenido, hay evidencia positiva de dominio (con slip `p(S)`).
- Si **abandona** o falla un quiz, hay evidencia negativa (con guess `p(G)`).
- La **probabilidad de aprender** `p(T)_u` se **reduce** si los prerrequisitos de `k` no están dominados (Mu et al., L@S 2018): `p(T)_k = p(T)_u · exp(−δ · nº_prerrequisitos_no_dominados)`.

**Efecto emergente:** los usuarios progresan de conceptos básicos a avanzados, respetando el grafo de prerrequisitos, y su conocimiento mejora con el tiempo. Esto produce la **evolución temporal** del aprendizaje de forma natural, sin forzarla.

### 4.6 Evolución temporal y sesiones

- Se define una **ventana temporal global** (p. ej. 12 meses) con timestamps realistas.
- Cada usuario tiene un **calendario de actividad** (días y horas en que suele interactuar, con estacionalidad semanal y horaria).
- Las interacciones se agrupan en **sesiones** (ráfagas de actividad con pausas), con longitud de sesión de cola larga.
- **Eventos de vida** opcionales (p. ej. un usuario que empieza a buscar hipoteca) pueden disparar picos de interés en un tema concreto, añadiendo realismo temporal.

### 4.7 Ruido y variabilidad realista

Se inyectan explícitamente los siguientes tipos de ruido (basados en ANCHOR y UDT):

1. **Misclick**: interacción `view` sin intención real (probabilidad `η_u`), sin completado.
2. **Curiosidad**: interacción con un contenido fuera de los temas de interés (probabilidad baja), a veces completada.
3. **Popularidad-driven**: interactuar con un contenido solo porque es popular, aunque no encaje con el perfil.
4. **Abandono**: entrar y no completar (ya cubierto por IRT).
5. **No-exposición**: no interactuar porque el contenido no se mostró (cubierto por el mecanismo de exposición).
6. **Variabilidad entre usuarios**: todos los parámetros (`λ_u`, `η_u`, `p(T)_u`, `ρ_u`, `α_u`) son heterogéneos, muestreados de distribuciones, no fijos.
7. **Variabilidad temporal**: la actividad no es uniforme; hay días/momentos de mayor uso.

### 4.8 Evitar data leakage

- **Timestamps globales realistas**: cada interacción tiene un timestamp en una línea temporal global coherente. El generador **no usa información futura** de un usuario para generar interacciones pasadas (el estado de conocimiento en `t` solo depende de interacciones en `t' < t`).
- **Separación de capas**: la generación de perfiles (ECF) y la generación de interacciones son procesos separados y documentados. Los perfiles no "miran" las interacciones.
- **Documentación del proceso**: se registra el seed, los parámetros y el orden de generación para que la evaluación pueda reproducir splits temporales válidos (GTS) sin leakage.
- **No usar el dataset para decidir el split**: el split temporal se define por los timestamps, no por un criterio que dependa del contenido generado.

### 4.9 Evitar que el dataset sea artificialmente fácil de predecir

- **Factores latentes no observables**: la preferencia depende de `α_u` (latente) y de `ρ_u`, `η_u`, `p(T)_u` (no observables directamente). Un modelo que solo vea atributos observables (topic, dificultad, demografía) **no puede** predecir perfectamente.
- **Ruido sustancial**: misclicks, curiosidad y popularidad introducen interacciones que contradicen la preferencia pura.
- **No determinismo por atributo**: ningún atributo único (topic, dificultad, formato) predice la interacción por sí solo; la combinación de factores + ruido lo impide.
- **Popularidad y exposición** añaden no-determinismo y hacen que el baseline de popularidad no sea trivial.
- **Heterogeneidad**: los parámetros varían entre usuarios, evitando que un modelo global "encaje" todos los patrones con una regla simple.

### 4.10 Pseudocódigo del algoritmo

```
ENTRADA: contents.csv, concepts.csv, content_concept_map.csv, prerequisites.csv, ECF 2021
SALIDA:  interactions_synthetic.csv

# FASE 0 — Preparación
1. Cargar catálogos y construir:
   - topics_c, format_c, difficulty_c, risk_c, investment_c  (por contenido)
   - concepts_of_content[c]  (del content_concept_map)
   - prereq_graph[concept]   (del prerequisites)
   - difficulty_concept[k]   (de concepts.csv)

# FASE 1 — Perfiles de usuario (calibrados con ECF)
2. Muestrear N usuarios (p. ej. 2.000–5.000):
   for u in usuarios:
     - muestrear demografía (edad, sexo rebalanceado, educación, empleo, ingresos)
       respetando distribuciones y correlaciones de la ECF
     - muestrear product_ownership (b1000a-j) condicionado a demografía
     - imputar θ_u (conocimiento continuo) desde Big3 + educación + productos
     - derivar α_u (interés temático) desde product_ownership + empleo + ruido
     - muestrear φ_u (formato), ρ_u (riesgo), λ_u (actividad, cola larga),
       p(T)_u (aprendizaje), η_u (ruido)
     - inicializar P(domina concepto k) desde θ_u y dificultad_concept[k]

# FASE 2 — Línea temporal y calendario de actividad
3. Definir ventana temporal global [T0, T1] (12 meses)
4. Para cada usuario, generar calendario de sesiones según λ_u y estacionalidad

# FASE 3 — Generación de interacciones (simulación temporal)
5. Ordenar todos los eventos de sesión por tiempo
6. Para cada sesión (en orden temporal global):
   for contenido c en candidatos_expuestos(u):
     - calcular P(interactuar | u, c, t)  (ecuación §4.3)
     - muestrear si interactúa (Bernoulli)
     - si interactúa:
         - muestrear interaction_type, source, position
         - calcular P(completar | u, c)  (IRT §4.4)
         - muestrear completed, duration, outcome
         - si completed: actualizar P(domina k) para k en concepts_of_content[c]
           (BKT con p(T)_u y penalización por prerrequisitos §4.5)
         - registrar interacción con timestamp t
   # el estado de conocimiento evoluciona, afectando interacciones futuras

# FASE 4 — Validación (ver §6)
7. Ejecutar batería de tests estadísticos y de coherencia
8. Si no pasa, ajustar parámetros y regenerar (iteración controlada)

# FASE 5 — Salida
9. Escribir interactions_synthetic.csv con las columnas de §4.1
10. Escribir reporte de validación y metadatos (seed, parámetros, limitaciones)
```

---

## 5. Distribuciones y patrones esperados en un dataset realista

Un dataset de interacciones realista debe exhibir estos patrones (y el generador debe producirlos):

1. **Sparsity alta**: la matriz usuario–contenido es muy dispersa (típicamente 1–5% de celdas con interacción). La mayoría de pares usuario–contenido no se observan.
2. **Popularidad de contenidos con cola larga**: pocos contenidos concentran muchas interacciones; la mayoría tienen pocas. Ajuste a power-law/log-normal.
3. **Actividad de usuarios con cola larga**: pocos usuarios muy activos, muchos con poca actividad.
4. **Longitud de sesión sesgada**: la mayoría de sesiones cortas, algunas largas.
5. **Duración de interacción log-normal**: tiempos de lectura/uso con cola a la derecha.
6. **Tasa de completado decreciente con la dificultad**: contenidos avanzados se completan menos, sobre todo por usuarios con bajo conocimiento.
7. **Conocimiento que mejora con el tiempo**: los usuarios interactúan con contenidos progresivamente más difíciles a medida que aprenden (correlación positiva entre tiempo y dificultad media de lo que completan).
8. **Respeto de prerrequisitos**: los usuarios rara vez completan contenidos avanzados sin haber interactuado antes con los prerrequisitos.
9. **Correlación conocimiento↔dificultad**: usuarios con alto conocimiento interactúan más con contenidos difíciles; los de bajo conocimiento, con básicos.
10. **Correlación intereses↔productos**: quien tiene acciones interactúa más con contenidos de inversión; quien tiene deuda, con deuda/hipotecas.
11. **No-determinismo**: ningún atributo observable predice perfectamente la interacción; hay ruido residual sustancial.
12. **Distribución de fuentes**: la mayoría de interacciones vienen de recomendación/navegación, menos de búsqueda directa.

---

## 6. Tests de validación del dataset sintético (antes de entrenar modelos)

### 6.1 Tests estadísticos de distribución

- **Sparsity**: verificar que la densidad de la matriz está en el rango esperado (1–5%).
- **Ajuste de cola larga**: ajustar la distribución de popularidad de contenidos y de actividad de usuarios a power-law/log-normal (test de Kolmogorov–Smirnov o comparación de colas); verificar que no son uniformes ni normales.
- **Distribución de duración**: verificar log-normalidad de `duration_seconds`.
- **Distribución de completado**: tasa global de completado en un rango plausible (p. ej. 40–70%), decreciente con dificultad.
- **Distribución de tipos de interacción**: proporciones plausibles de view/read/tool/quiz.

### 6.2 Tests de coherencia con prerrequisitos

- **Acceso a avanzados**: verificar que la proporción de usuarios que completan un contenido avanzado **sin** haber interactuado antes con sus prerrequisitos es baja (por debajo de un umbral, p. ej. <10%).
- **Orden de conceptos**: verificar que, en promedio, los usuarios interactúan con conceptos básicos antes que con avanzados (respetando el grafo).

### 6.3 Tests de correlación y perfil

- **Conocimiento↔dificultad**: correlación positiva entre `financial_knowledge_level` y la dificultad media de los contenidos completados.
- **Intereses↔productos**: correlación entre tenencia de productos y temas de interacción (inversión↔acciones, deuda↔préstamos, etc.).
- **Por perfil de usuario**: comparar las distribuciones de interacción entre grupos (estudiantes vs empleados, alto vs bajo conocimiento, 18–24 vs 25–34) y verificar que difieren de forma plausible y no idéntica.

### 6.4 Tests de diversidad

- **Cobertura de topics por usuario**: los usuarios interactúan con varios temas, no solo uno (diversidad razonable).
- **Gini / concentración**: medir la concentración de interacciones (no todo en un puñado de contenidos ni uniforme).
- **Cobertura de contenidos**: la mayoría de los 105 contenidos reciben al menos alguna interacción (no hay contenidos huérfanos salvo los muy de nicho).

### 6.5 Tests de no-determinismo / no artificialidad

- **Predictibilidad**: entrenar un modelo simple (p. ej. regresión logística con atributos observables) y verificar que el AUC no es excesivamente alto (p. ej. <0.85–0.90). Un AUC ~1 indica determinismo artificial.
- **Ruido residual**: verificar que hay interacciones que contradicen la preferencia pura (misclicks/curiosidad) en la proporción esperada.
- **Popularidad no trivial**: verificar que el baseline de popularidad no explica todo (hay interacciones de nicho).

### 6.6 Tests temporales

- **Evolución del conocimiento**: verificar que la dificultad media de lo completado aumenta con el tiempo (aprendizaje).
- **Sin saltos temporales imposibles**: no hay interacciones con timestamps fuera de la ventana ni estados de conocimiento que "salten" sin evidencia.
- **Estacionalidad**: la actividad muestra patrones semanales/horarios plausibles.

### 6.7 Tests de robustez del generador

- **Reproducibilidad**: con el mismo seed, el dataset es idéntico.
- **Estabilidad**: con seeds distintos, las distribuciones agregadas son estables (no dependen de un sorteo concreto).

---

## 7. Problemas y decisiones metodológicas que podrían invalidar la evaluación

1. **Data leakage temporal** (el más crítico): si los timestamps no son globales o el generador usa información futura, cualquier split temporal o secuencial queda invalidado. **Mitigación:** timestamps globales, generación estrictamente causal, documentación del proceso.

2. **Determinismo excesivo**: si la preferencia es una función determinista de atributos observables, los modelos alcanzan AUC ~1 y la evaluación no discrimina nada. **Mitigación:** factores latentes no observables + ruido sustancial (§4.9).

3. **Popularity bias artificial**: si la popularidad se genera de forma que el baseline de popularidad predice perfectamente, la evaluación de cualquier recomendador queda sesgada. **Mitigación:** popularidad con cola larga + ruido + exposición.

4. **Cold start mal definido**: si no se separan explícitamente usuarios/contenidos nuevos (cold) de los que tienen historia (warm), la evaluación mezcla regímenes incomparables. **Mitigación:** documentar y permitir splits warm/cold; reportar métricas por separado.

5. **Sesgo de género/educación no corregido**: si se copia el sesgo de género de la ECF (~85/15), los recomendadores aprenden un sesgo artificial. **Mitigación:** rebalancear sexo a ~50/50 (§2.2).

6. **Falta de heterogeneidad**: si todos los usuarios tienen parámetros similares, el dataset no representa la diversidad real y los modelos no generalizan. **Mitigación:** parámetros heterogéneos muestreados de distribuciones.

7. **Sparsity irreal**: si la matriz es demasiado densa (todo el mundo interactúa con todo) o demasiado dispersa (nadie interactúa con nada), la evaluación no es representativa. **Mitigación:** calibrar la densidad al rango realista (1–5%).

8. **Confusión entre "no le gusta" y "no lo vio"**: si no se modela la exposición, el dataset confunde no-preferencia con no-exposición, sesgando la evaluación de recomendadores. **Mitigación:** mecanismo de exposición explícito (§4.3).

9. **Imputación de NS/NC mal hecha**: si los NS/NC de las Big3 se tratan como fallo o se excluyen, el conocimiento queda sesgado. **Mitigación:** imputación condicionada documentada (§2.2).

10. **Sobreajuste del generador a un modelo concreto**: si se valida el dataset solo con un tipo de modelo, se puede optimizar para ese modelo. **Mitigación:** validar con varios modelos y con tests estadísticos independientes del modelo.

11. **Falta de metadatos/reproducibilidad**: sin seed y parámetros documentados, el dataset no es reproducible ni auditable. **Mitigación:** registrar todo en un reporte de metadatos.

---

## 8. Criterios para considerar la data lista para entrenar/evaluar modelos

El dataset se considera de calidad suficiente para pasar a la fase de modelos cuando **todos** los siguientes criterios se cumplen:

1. **Validación estadística completa**: pasan los tests de §6.1 (sparsity, cola larga, duración, completado) dentro de los rangos esperados.
2. **Coherencia con prerrequisitos**: los tests de §6.2 pasan (acceso a avanzados sin prerrequisitos por debajo del umbral).
3. **Correlaciones plausibles**: los tests de §6.3 confirman las correlaciones esperadas (conocimiento↔dificultad, intereses↔productos).
4. **Diversidad adecuada**: los tests de §6.4 confirman cobertura y no-concentración excesiva.
5. **No-determinismo**: el test de predictibilidad (§6.5) muestra AUC < 0.85–0.90 con un modelo simple; hay ruido residual.
6. **Temporalidad válida**: los tests de §6.6 confirman evolución del aprendizaje y ausencia de saltos imposibles; el dataset soporta splits temporales sin leakage.
7. **Reproducibilidad**: el generador es reproducible con seed y los metadatos están documentados.
8. **Revisión manual**: una inspección cualitativa de una muestra de interacciones (p. ej. 100 filas) resulta plausible (usuario con acciones → contenidos de inversión; estudiante → presupuesto/ahorro; etc.).

Solo cuando estos criterios se cumplen de forma conjunta se procede a la fase de entrenamiento y evaluación de los recomendadores. Si algún test falla, se ajustan los parámetros del generador y se itera (sin tocar los datos a mano, para no introducir sesgos).

---

## 9. Riesgos y sesgos del plan

| Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|
| Data leakage temporal | Media | Alto | Timestamps globales, generación causal, documentación |
| Determinismo artificial | Media | Alto | Factores latentes + ruido + test de predictibilidad |
| Sesgo de género ECF | Alta | Medio | Rebalanceo a ~50/50 |
| Imputación NS/NC sesgada | Media | Medio | Imputación condicionada documentada |
| Sparsity mal calibrada | Media | Medio | Calibración iterativa contra rangos realistas |
| Confusión exposición/no-preferencia | Media | Medio | Mecanismo de exposición explícito |
| Sobreajuste a un modelo | Baja | Medio | Validación multi-modelo + tests independientes |
| Popularidad no realista | Media | Medio | Cola larga + ruido + baseline no trivial |

---

## 10. Referencias

- Mungari, Coppolillo, Ritacco, Manco. *HYDRA: Flexible Generation of Preference Data for Recommendation Analysis*. KDD 2025. https://arxiv.org/html/2407.16594v2
- *SPUP: Sparse Probabilistic User Preference Model*. McGill University, 2017.
- *Scalable Realistic Recommendation Datasets through Fractal Expansions*. Google AI, 2019. https://arxiv.org/pdf/1901.08910
- Ji et al. *A Critical Study on Data Leakage in Recommender System Offline Evaluation*. ACM TOIS 2022.
- Gusak et al. *Time to Split*. RecSys 2025.
- Volodkevich et al. *SplitLight*. 2026.
- Sun. *Take a Fresh Look at Recommender Systems from an Evaluation Standpoint*. SIGIR 2023.
- Mu, Wang, Andersen, Brunskill. *Combining Adaptivity with Progression Ordering*. L@S 2018.
- *pyBKT* (UC Berkeley). https://github.com/CAHLR/pyBKT
- Pardos & Heffernan. *KT-IDEM: Introducing Item Difficulty to the Knowledge Tracing Model*.
- Schütt et al. *Fast Dynamic Difficulty Adjustment for Intelligent Tutoring Systems*. 2023.
- *ANCHOR: Agentic Noise Creation Framework for Human Simulation and Denoising Recommendation*. arXiv.
- *Unified Denoising Training for Recommendation*. RecSys 2024.
- *Debiasing Sequential Recommenders through Distributionally Robust Optimization over System Exposure*. WSDM 2024.
- *DAISim: Simulating Student Interactions with Two-stage Imitation Learning*. CIKM 2023.
- *SynEdu-HEDL: Privacy-Preserving Synthetic Learner Dataset*. Scientific Reports, 2026.
- Hospido, Machelett, Pidkuyko, Villanueva. *Encuesta de Competencias Financieras 2021*. BdE/CNMV, 2023. DOI: 10.53479/34752. https://www.bde.es/wbe/es/publicaciones/analisis-economico-investigacion/encuesta-de-competencias-financieras/encuesta-de-competencias-financieras-2021.html
- OECD/INFE. *Toolkit for Measuring Financial Literacy, Inclusion and Well-Being*. 2018/2026.
