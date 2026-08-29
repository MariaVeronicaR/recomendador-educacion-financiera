# Comparativa de modelos de recomendación para el TFM

**Documento de trabajo** — Análisis del planteamiento y propuesta de selección de modelos para la comparativa del sistema de recomendación de contenidos de educación financiera.

> **Estado:** borrador. El documento `Trabajo_Final_de_Master_borrador.md` puede cambiar; este análisis se basa en su versión actual y debe revisarse si el planteamiento evoluciona.

---

## 1. Análisis del planteamiento actual

### 1.1. Qué tipo de problema es realmente

Esto es un **problema de ranking de contenidos educativos** (generar una lista ordenada de contenidos para cada usuario), no un problema de predicción de rating ni de clasificación. Tres rasgos lo definen:

- **Cold start severo**: el usuario nuevo no tiene historial; la personalización inicial debe salir del cuestionario de perfilado.
- **Restricciones pedagógicas duras**: los prerrequisitos entre conceptos no son una preferencia blanda, son una condición que *debe* cumplirse.
- **La "ground truth" no es la preferencia, sino la efectividad de aprendizaje**: un contenido "relevante" que el usuario no está preparado para entender es una mala recomendación aunque el usuario lo hubiera clicado.

Esto implica que **la comparativa no puede ser solo de métricas de ranking clásicas**; necesita una métrica de coherencia pedagógica, y esa métrica debe diseñarse con cuidado (ver §4).

### 1.2. Decisiones metodológicas que conviene modificar

**a) El problema central: datos sintéticos + filtrado colaborativo.** Un modelo colaborativo (NeuMF incluido) aprende de patrones de interacción usuario-contenido. Si esas interacciones son sintéticas, el modelo está aprendiendo las reglas que se inyectaron en el generador. La comparativa deja de medir "qué modelo generaliza mejor en el mundo real" y pasa a medir "qué modelo recupera mejor los patrones programados". Esto no invalida el TFM, pero obliga a:

- Describir y justificar el generador sintético (qué distribuciones usa, de dónde salen — p. ej. la ECF 2021 para que los perfiles sean realistas).
- Enmarcar los resultados como **comparación relativa de comportamiento bajo condiciones controladas**, no como cifras absolutas de rendimiento real.
- No afirmar en las conclusiones que el sistema "funciona en producción"; solo que "el enfoque es viable y las diferencias entre modelos son consistentes".

**Estado de la data generada (2026-08-29).** El generador (`data/scripts/generate_interactions.py`, seed 42) produce dos archivos:

- `data/interactions_synthetic.csv` — 9612 interacciones, 2000 usuarios, 104 contenidos, densidad ~3%, con `session_id`, `timestamp` global, `interaction_type`, `completed`, `outcome`, `source`, `position`, `concepts_covered`.
- `data/users_synthetic.csv` — 2000 perfiles con las features del cuestionario (edad, sexo, educación, empleo, productos, θ, nivel de conocimiento, intereses, riesgo, formato, actividad) más `n_interactions`, `n_completed` y la etiqueta `cold_start` (230 usuarios fríos).

Esto resuelve el bloqueante que impedía ejecutar la comparativa: **la matriz de features de usuario ya existe** y el cold start está etiquetado de forma reproducible. La densidad (~3%) está en el rango realista de recomendación (1–5%), y la señal de aprendizaje temporal es positiva y estable entre seeds (0.024–0.043), lo que sostiene la narrativa pedagógica.

**b) Desajuste entre objetivos y contribución real.** Los objetivos específicos 1 y 2 hablan de *perfilado/segmentación/clasificación* de perfiles financieros, pero la contribución científica declarada (finalidad 1.2.3) es sobre *recomendación* (NDCG@k, Precision@k, coherencia pedagógica). Son dos tareas distintas. Recomendación: o bien el perfilado es un **componente de apoyo** que alimenta al recomendador (y se describe como tal, no como objetivo central), o bien se separa como contribución secundaria. Tal como está, la pregunta de investigación queda difusa.

**c) La métrica de coherencia pedagógica es trivial si solo se mide sobre la salida filtrada.** Si el KG actúa como post-filtro, por construcción el 100% de las recomendaciones del sistema completo respetan prerrequisitos. La métrica no mide nada a menos que se calcule sobre el **ranking crudo de cada modelo, sin filtro**. El diseño correcto: medir la coherencia del ranking crudo de *todos* los modelos (ahí sí hay diferencias), y luego mostrar que el post-filtro la lleva a ~100% a costa de un pequeño coste en recall.

**d) La evaluación de cold start necesita un protocolo propio.** No basta con el split train/test estándar. Hay que reservar un conjunto de usuarios "fríos" (sin ninguna interacción en test, solo con sus features del cuestionario) y medir ahí específicamente. Es la única forma de validar la hipótesis central del feature-aware NeuMF.

**e) La promesa de "aprendizaje secuencial" no la cumple el modelo propuesto.** El borrador critica que los sistemas actuales no optimizan una *secuencia* de aprendizaje, pero NeuMF + post-filtro es un ranking punto a punto + filtro; no modela secuencias. O se reformula la promesa (el KG garantiza progresión, no optimiza secuencia) o se añade un componente secuencial, que para este dataset sería sobre-ingeniería. Recomendación: reformular la promesa.

**f) La ECF 2021 es datos de encuesta, no de interacción.** No puede entrenar un modelo colaborativo. Su papel legítimo es informar el generador sintético (perfiles realistas) y la validación del perfilado. Conviene que el borrador lo diga explícitamente para que no parezca que se entrena con datos reales.

**g) Error menor:** hay una sección duplicada (2.5 y 2.6 ambas "Selección de arquitectura y justificación del stack tecnológico"). Corregir.

---

## 2. Qué información tenemos y qué pueden aprovechar los modelos

| Información | Disponible | Qué modelo la aprovecha |
|---|---|---|
| Features del usuario (edad, sexo, educación, empleo, productos, θ, nivel, riesgo, intereses, formato) | `users_synthetic.csv` | Content-based, feature-aware NeuMF, KG/reglas |
| Features del contenido (tema, dificultad, formato, riesgo, inversión) | `contents.csv` | Content-based, feature-aware NeuMF |
| Conceptos + prerrequisitos (grafo) | `concepts.csv`, `prerequisites.csv` | KG/reglas, NeuMF+KG, (KGCN) |
| Interacciones usuario-contenido | `interactions_synthetic.csv` | MF, NeuMF, (KGCN) |
| Estado de maestría del usuario | Progreso (derivable de `interactions_synthetic.csv` + `content_concept_map.csv`) | KG/reglas, NeuMF+KG |

La clave: **tenemos features ricas y un grafo, pero interacciones sintéticas y escasas** (densidad ~3%). Eso favorece a los modelos que usan features y estructura (content-based, KG, feature-aware) frente a los que dependen solo de interacciones (MF puro, NeuMF puro). Esa es precisamente la hipótesis que la comparativa debe poder confirmar o refutar.

**Nota sobre el estado de maestría:** el generador no persiste el estado de maestría final por concepto (solo el `theta` global y el `knowledge_level` en `users_synthetic.csv`). Para el baseline KG/reglas, la maestría se puede **derivar** de las interacciones completadas (un concepto se considera dominado si el usuario completó contenidos que lo cubren), o usar `theta`/`knowledge_level` como proxy. Conviene documentar cuál de las dos se usa.

---

## 3. Selección propuesta de modelos

La comparativa se organiza en **dos capas**: baselines de paradigma + cadena de ablación del modelo propuesto. Así cada componente aporta algo medible.

### 3.1. Resumen

| # | Modelo | Paradigma | Información que usa | Veredicto |
|---|---|---|---|---|
| 1 | Most-Popular | Baseline trivial | Interacciones (frecuencia) | **Incluir** (suelo) |
| 2 | Content-Based Filtering | Basado en contenido | Features usuario + contenido | **Incluir** (baseline cold-start) |
| 3 | BPR-MF | Filtrado colaborativo clásico | Interacciones | **Incluir** (baseline CF) |
| 4 | KG / reglas pedagógicas | Basado en conocimiento | Grafo + maestría | **Incluir** (baseline pedagógico) |
| 5 | NeuMF puro | Deep CF | Interacciones | **Incluir** (ablación) |
| 6 | Feature-aware NeuMF | Deep híbrido | Interacciones + features | **Incluir** (modelo propuesto) |
| 7 | Feature-aware NeuMF + KG post-filtro | Híbrido + restricción | Todo | **Incluir** (sistema completo) |
| 8 | KGCN / NeuMF con embeddings del grafo | Deep KG | Todo | **Opcional** (extensión) |

### 3.2. Detalle por modelo

**1. Most-Popular.** Recomienda los contenidos más consumidos. No usa features ni grafo. Es el suelo de la comparativa: cualquier modelo debe superarlo para justificar su complejidad. Viable al instante. Hipótesis: todos los demás lo superan en ranking; sirve para calibrar la magnitud de las diferencias.

**2. Content-Based Filtering.** Recomienda contenidos similares al perfil del usuario (similitud coseno sobre vectores de features de tema/dificultad vs. perfil del cuestionario). No aprende de otros usuarios, así que **funciona en cold start** y usa exactamente la información que tenemos. Ventaja: simple, interpretable, robusto a datos escasos. Limitación: overspecialization (encasilla al usuario en su zona de confort) y no usa patrones colectivos. Hipótesis: supera a MF en cold start, pero queda por debajo de los modelos que combinan features + patrones colectivos. Viable: muy fácil.

**3. BPR-MF (Matrix Factorization con Bayesian Personalized Ranking).** El CF clásico para feedback implícito. Representa el paradigma tradicional. Ventaja: estándar, rápido, es el baseline que aparece en la literatura (Verma et al. lo usan). Limitación: **falla en cold start** (no puede recomendar a un usuario sin historial) y no incorpora features ni grafo. Hipótesis: el mejor de los "puros colaborativos" cuando hay interacciones, pero el peor en cold start — esto demuestra la necesidad del feature-aware. Viable: muy fácil (librerías estándar).

**4. KG / reglas pedagógicas (recomendador basado en conocimiento).** Sin ML: recomienda el siguiente contenido disponible según el grafo (conceptos dominados → contenidos cuyos prerrequisitos están cubiertos), ordenado por dificultad. Es el baseline pedagógico puro. Ventaja: 100% de coherencia por construcción, interpretable, cero entrenamiento. Limitación: **no personaliza** más allá del estado de maestría (ignora edad, ingresos, perfil de riesgo, intereses). Hipótesis: gana en coherencia pedagógica pero pierde en ranking personalizado — esto responde a la pregunta "¿la personalización más allá de seguir prerrequisitos aporta valor?". Viable: trivial con el grafo ya construido. **Este baseline es el que más falta en el borrador actual.**

**5. NeuMF puro.** El deep CF de He et al. (GMF+MLP). Aísla el valor de la función de interacción neuronal frente a MF lineal. Limitación: mismo problema de cold start que MF. Hipótesis: supera a BPR-MF en ranking (no linealidad) pero no resuelve cold start. Viable: ya está en el stack (PyTorch).

**6. Feature-aware NeuMF.** El modelo propuesto: añade las features del cuestionario al MLP. Es la contribución real del TFM. Hipótesis central: **resuelve el cold start** (puede recomendar a usuarios sin historial usando solo features) y mejora el ranking en perfiles heterogéneos. Viable: extensión directa del 5.

**7. Feature-aware NeuMF + KG post-filtro.** El sistema completo. Añade la restricción pedagógica. Hipótesis: mantiene el ranking del 6 pero eleva la coherencia pedagógica a ~100% (con un pequeño coste en recall). Viable: ya es la arquitectura del borrador.

**8. KGCN / NeuMF con embeddings del grafo (opcional).** Integra el grafo *dentro* del modelo (enriquecimiento de embeddings) en vez de como post-filtro. Es la comparación que el borrador ya insinúa en 2.6.4. Hipótesis: ¿la integración profunda supera al post-filtro? **Se marca como opcional y de riesgo**: para un dataset sintético pequeño, una GNN puede no mostrar ventaja y añade mucha complejidad de implementación y de justificación. Solo si el tiempo y el cómputo lo permiten, y como extensión, no como parte del núcleo.

### 3.3. Modelos que se descartan (y por qué)

- **Transformers secuenciales (SASRec, BERT4Rec)**: el dataset sí tiene `session_id` y `timestamp`, así que existen secuencias de interacción; pero el catálogo es pequeño (104 contenidos), los datos son sintéticos y la pregunta de investigación es sobre **ranking personalizado + coherencia pedagógica**, no sobre predicción de la siguiente interacción. Un modelo secuencial optimizaría la secuencia, que no es el objetivo; sería sobre-ingeniería y no respondería a la pregunta central.
- **Reinforcement Learning (estilo Verma et al.)**: difícil de entrenar, y el propio borrador señala que Verma no modela pedagogía. No aporta nada a la pregunta central y complica mucho el TFM.
- **GNNs como núcleo**: ver punto 8; solo como extensión opcional.
- **Otros deep CF (autoencoders, etc.)**: redundantes con NeuMF, sin valor añadido claro para esta pregunta.

---

## 4. Estrategia de evaluación común

Para que la comparación sea justa y metodológicamente sólida:

**Protocolo de datos.** El dataset sintético ya está generado con un generador documentado (distribuciones realistas basadas en ECF 2021; ver `docs/plan_generar_interacciones.md` y `docs/plan_ajustes_generador_interacciones.md`). Entradas: `interactions_synthetic.csv` + `users_synthetic.csv` + catálogos. Split en train/validación/test. **Dos escenarios de evaluación separados:**

- *Escenario con historial*: usuarios con interacciones en test (mide calidad de ranking).
- *Escenario cold start*: usuarios sin ninguna interacción en test, solo features (mide la hipótesis central). El generador ya etiqueta estos usuarios con `cold_start=True` en `users_synthetic.csv` (230 de 2000). Aquí MF y NeuMF puro no pueden predecir; se reporta como "no aplicable" o se les da un fallback (p. ej. popularidad) para poder compararlos.

**Split temporal.** El dataset tiene `timestamp` global y `session_id`, así que se puede usar un **Global Temporal Split (GTS)** por punto temporal (p. ej. primeros 9 meses train, últimos 3 test) para evitar data leakage temporal. Para el escenario cold start, los usuarios fríos se reservan aparte del split temporal (no tienen interacciones en test por definición).

**Coherencia del baseline KG/reglas con el split temporal.** El baseline pedagógico (§3.2, modelo 4) debe **derivar el estado de maestría de las interacciones completadas** (un concepto se considera dominado si el usuario completó contenidos que lo cubren en el periodo de train), **no** usar el `theta`/`knowledge_level` estático de `users_synthetic.csv`. Razón: `theta` es el conocimiento *inicial* del perfil y no captura el aprendizaje que sí ocurre en la simulación; si el baseline usara `theta` estático, ignoraría la progresión temporal que el generador produce y la comparativa no mediría la coherencia pedagógica real. Derivar la maestría de las interacciones es además lo que hace coherente al baseline con el split temporal (en test, el usuario "sabe" lo que aprendió en train).

**Métricas.**

- Ranking: **NDCG@k, Precision@k, Recall@k, MRR** (k=5 y k=10).
- Coherencia pedagógica: **% de recomendaciones del ranking crudo que respetan prerrequisitos**, calculada sobre la salida *sin filtro* de cada modelo. Solo así discrimina.
- (Opcional) Diversidad del catálogo recomendado, para capturar la overspecialization del content-based.

**Rigor estadístico.** Repetir con **varias semillas** (p. ej. 5) y reportar media ± desviación. Aplicar **test de significación pareado** (Wilcoxon) entre el modelo propuesto y cada baseline. Sin esto, las diferencias en datos sintéticos pueden ser ruido.

**Análisis de ablación.** La cadena 5→6→7 aísla cada contribución: valor de la no-linealidad (5 vs 3), valor de las features (6 vs 5), valor del KG (7 vs 6, y 7 vs 4). Este es el corazón del argumento científico.

**Reporte honesto de la limitación sintética.** Una sección explícita: los valores absolutos no son generalizables; la contribución es la *consistencia de las diferencias relativas* bajo condiciones controladas. Conviene reportar las características de la data generada (densidad ~3%, 2000 usuarios, 104 contenidos, 230 usuarios cold start, señal de aprendizaje positiva) para que el lector entienda el régimen en que se evalúa.

---

## 5. Veredicto sobre la selección actual

La selección actual del borrador (NeuMF + variantes + KG) es un **buen punto de partida pero incompleta como comparativa**. El argumento de "modularidad" (comparar GMF vs MLP vs NeuMF) es una ablación interna válida, pero **no es una comparativa de paradigmas**: sin baselines no-neuronales no se puede afirmar que NeuMF supera a las alternativas, y sin un baseline pedagógico puro no se puede demostrar que el KG aporta algo más que "seguir prerrequisitos".

**Recomendación concreta para el TFM:** mantener NeuMF como modelo propuesto, y **ampliar la comparativa** a los 7 modelos del núcleo (popularidad, content-based, BPR-MF, KG/reglas, NeuMF, feature-aware NeuMF, feature-aware NeuMF+KG). El KGCN queda como extensión opcional. Esto da una historia limpia y defendible: cada componente del sistema propuesto se justifica empíricamente frente a una alternativa de paradigma distinto, y la pregunta de investigación ("¿añadir estructura pedagógica a un recomendador personalizado mejora el ranking y la coherencia?") se responde de forma directa.
