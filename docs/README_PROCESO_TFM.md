# Guía Completa del Proceso de Datos y Evaluación del TFM

> **Para quién es esta guía:** para ti, cuando vuelvas a este proyecto en 3 meses y no te acuerdes de nada. También para el tribunal, si pregunta "¿cómo generaste los datos?".

---

## 🎯 El objetivo del TFM (en una frase)

Construir un sistema que recomiende **contenidos de educación financiera** (artículos de bancos, guías de la CNMV, etc.) a **jóvenes de 18 a 34 años** de forma personalizada, **respetando un orden pedagógico** (no puedes recomendarle "inversión en bolsa" a alguien que aún no sabe qué es un ahorro).

---

## 🎬 La película completa (resumen de 1 minuto)

```
1. El BdE publica la ECF 2021 (encuesta a 7.764 personas)
   ↓
2. La ECF tiene una pregunta tipo test para cada joven (Big Three: inflación, interés compuesto, diversificación)
   ↓
3. Tomamos SOLO los 1.916 jóvenes de 18-34 años de esa encuesta
   ↓
4. Construimos 1.916 perfiles de usuario "como si vinieran de la ECF"
   (con su edad, sexo, nivel educativo, sus respuestas al Big Three, etc.)
   ↓
5. Simulamos cómo cada uno leería los contenidos durante 12-14 interacciones
   (con afinidad al tema según su perfil + reglas pedagógicas: si no dominas inflación,
    no puedes ver inversión avanzada)
   ↓
6. Para cada modelo de IA (Popularidad, TF-IDF, SVD+Ridge, Red Neuronal),
   medimos:
   - ¿Cuánto acierta prediciendo lo que el usuario va a leer?
   - ¿Cuánto viola el orden pedagógico?
   - ¿Cuánto contenido distinto recomienda?
   ↓
7. Aplicamos el filtro pedagógico (muro de prerequisites) y volvemos a medir.
```

Eso es todo. Si entiendes esto, entiendes el TFM.

---

## 📦 Los datos: qué hay en cada archivo

### Lo que produce el BdE (input externo)
- **`ECF-archivos/ecf_2021.csv`**: 7.764 entrevistas. Tiene una fila por persona con 429 columnas (cada pregunta de la encuesta). Nosotros usamos solo unas pocas.

### Lo que produce mi proyecto (output del trabajo)
| Archivo | Qué es | Quién lo genera |
|---|---|---|
| `data/concepts.csv` | Los 30 conceptos (C01-C30) que el sistema enseña: ahorro, inflación, hipoteca, etc. | Creado a mano al inicio del proyecto |
| `data/contents.csv` | Los **104 contenidos** (C001-C114, artículos y PDFs) con su tema, dificultad y conceptos que enseñan | Recopilado de BdE + CNMV |
| `data/prerequisites.csv` | Las **34 reglas pedagógicas**: "para ver X, primero debes saber Y" | Definido por el diseño pedagógico |
| `data/content_concept_map.csv` | Qué conceptos enseña cada contenido (122 asignaciones, refinadas manualmente con evidencia) | Revisado a mano tras el scraping |
| `data/sources.csv` | Las **8 fuentes** oficiales (Finanzas para Todos, CNMV, BdE, OCDE, PISA…) con su fiabilidad | Documentado al inicio |
| `data/scraped/*.json` | El **texto crudo extraído** de cada URL (HTML con Trafilatura, PDF con PyMuPDF) | `ingest_contents.py` |
| `data/enriched/*.json` | Cada contenido **enriquecido con LLM**: TLDR, puntos clave y 3 preguntas de quiz etiquetadas por concepto | `enrich_contents.py` |
| `data/users_synthetic.csv` | Los **1.916 perfiles de usuario** inventados a partir de la ECF real | `regenerate_users_from_ecf.py` |
| `data/interactions_synthetic.csv` | Las **23.000 lecturas simuladas** que esos usuarios harían (symlink al fichero v2 validado) | `generate_interactions_v2.py` |
| `data/evaluation_metrics_*.csv` | Las **métricas de calidad** de cada modelo | `evaluate_models.py` |

### Lo que NO debes tocar (archivado en `archive/`)
- `archive/dataset_v3/`: CSVs y binarios de iteraciones anteriores (v2-v5). Útil solo para ver la historia.
- `archive/scripts_v1_v2/`: versiones antiguas de los scripts del generador. No se usan.
- `archive/reports_v3/`: informes antiguos.

---

## 🎬 La película paso a paso (la versión larga, la que necesitas recordar)

### PASO 1: Elegir los datos de origen

El Banco de España (BdE) y la CNMV publicaron en 2021 la **Encuesta de Competencias Financieras** (ECF): 7.764 personas respondieron preguntas sobre sus conocimientos financieros.

**Nuestro universo:** solo los **1.916 jóvenes de 18 a 34 años**.

Por qué solo estos:
- El TFM está dirigido a este segmento (jóvenes profesionales).
- Las preguntas que nos interesan (Big Three: inflación, interés compuesto, diversificación) se hicieron a adultos de 18-79, pero solo los 18-34 tienen suficiente muestra estadística para extraer perfiles fiables.

---

### PASO 2: Crear los 1.916 perfiles de usuario

**Script:** `data/scripts/regenerate_users_from_ecf.py`

**Qué hace:**
1. Lee el ECF-archivos/ecf_2021.csv (la encuesta real).
2. Filtra: solo los 1.916 que tienen entre 18 y 34 años.
3. Toma **todos** (no muestra aleatoria) para preservar las proporciones reales.
4. Para cada joven, asigna:
   - **edad** y **sexo** (del ECF real).
   - **nivel educativo** (de su respuesta a la pregunta QD9).
   - **situación laboral** (de QD10).
   - **financial_knowledge_level**: lo calculo del Big Three.
   - **saving_habit** y **investment_experience**: del ECF real.

**Detalle clave del Big Three:**
La encuesta BdE hace estas 3 preguntas:
- k0600 = Inflación → respuesta correcta = 3 ("Menos")
- k0100 = Interés compuesto → respuesta correcta = 3 ("Más de 110")
- k1003 = Diversificación → respuesta correcta = 1 ("Verdadero")

Si el joven acertó 0 → nivel **bajo**.
Si acertó 1-2 → **medio**.
Si acertó 3 → **alto**.

Si no contestó alguna (NS/NC), su nivel queda como **NaN** (ausente). Esto es honesto: no inventamos un valor.

**Por qué esto es importante:** si la respuesta correcta es 3 y el joven respondió otra cosa (incluido NS/NC), no lo cuento como fallo. Solo cuento aciertos. Si respondió NS/NC, queda como NaN y el sistema lo trata como "sin evidencia de conocimiento", que es conservador.

**Resultado:** 1.916 usuarios en `data/users_synthetic.csv`.

---

### PASO 3: Generar las 23.000 lecturas simuladas

**Script:** `data/scripts/generate_interactions_v2.py` (v2, la versión actual)

**Qué hace:**
Para cada uno de los 1.916 usuarios, simula entre 10 y 14 lecturas de contenidos del catálogo (media 12, total 23.000).

**Lógica de la simulación (por cada lectura):**

1. **¿Qué tema le interesa?** (afinidad)
   - El usuario "joven con cuenta de ahorro" tiene más afinidad por *planificación/ahorro/cuentas*.
   - El que "no cubre gastos" tiene más afinidad por *deuda/crédito/presupuesto*.
   - Esto se modela con pesos aprendidos del ECF (función `topic_affinity`).

2. **¿Qué dificultad?** (60% básico / 30% intermedio / 10% avanzado)
   - Pero esto es por **usuario**, no global. Cada usuario tiene su propia distribución de dificultad (más básico si sabe poco, más avanzado si sabe mucho).

3. **¿Pasa el filtro pedagógico?**
   - Si el contenido es de **inversión avanzada**, el usuario debe tener dominados los conceptos `C02 (ahorro) + C07 (inflación) + C06 (interés compuesto) + C13 (riesgo)`.
   - Si no los tiene dominados (porque nunca interactuó con ellos antes), el contenido se descarta.

4. **¿Hace clic?** (probabilidad logística)
   - El usuario hace clic con probabilidad `1 / (1 + e^-x)` donde `x` depende de:
     - `gap = su_nivel - dificultad_contenido` (si el contenido es muy difícil, no hace clic).
     - `afinidad` (si le gusta el tema, más clic).
     - ruido aleatorio.

5. **¿Termina la lectura y aprueba el quiz?**
   - Calculamos un score = `0.4 × completion + 0.4 × quiz + 0.2 × ruido`.

**Resultado:** 23.000 filas en `data/interactions_synthetic_v2_validated.csv`. El fichero `data/interactions_synthetic.csv` es un **symlink** a este, por lo que el pipeline siempre lee la versión vigente. El script además imprime 7 validaciones (relevancia, distribución de scores, KL entre perfiles, completion por cuartil de afinidad, eventos, topics y resumen).

Formato de cada fila:

| Columna | Ejemplo | Significado |
|---|---|---|
| interaction_id | I00001 | ID único |
| user_id | U0001 | Quién leyó |
| content_id | C800 | Qué leyó |
| topic | cuentas bancarias | Tema del contenido |
| affinity | 1.0 | Afinidad del usuario por ese tema |
| completion | 1 | Cuánto consumió (0-1) |
| relevant | 1 | Si la lectura se considera relevante para el usuario |
| event | completed | Tipo de interacción |
| score | 1.0 | Calidad de la lectura (0-1) |
| timestamp | 2025-01-00:00:00 | Cuándo leyó |

**Detalle técnico:** el timestamp se genera **por usuario**, con un offset aleatorio (cada usuario tiene su propia línea temporal en los primeros 60 días desde el inicio). Esto permite hacer un split Train/Test **temporal** válido (los pares más recientes van a Test).

---

### PASO 4: Dividir en Train / Test (split)

**Script:** parte de `evaluate_models.py`, función `make_train_test_split`.

**Qué hace:**

Para evitar **leakage** (que un mismo par (user, contenido) esté en Train y en Test), agrupamos las interacciones por `(user_id, content_id)` y luego:

1. Si el par aparece solo 1 vez → va a Train (no hay nada que dividir).
2. Si aparece ≥2 veces → toma las más recientes para Test, las demás a Train.
3. Al final, una **validación anti-leakage** con `assert` comprueba que ningún par `(user_id, content_id)` está en ambos conjuntos; si ocurriera, el script aborta.

Resultado: ~20.000 interacciones en Train, ~5.000 en Test, **sin que ningún par se repita entre ambos**.

Para el cold start hay un split diferente: **200 usuarios completos** se reservan como "usuarios nuevos" sin que ninguna de sus interacciones entrene ningún modelo.

---

### PASO 5: Evaluar los modelos (la parte crítica del TFM)

**Script:** `src/utils/evaluate_models.py`

Para cada modelo, hacemos:

1. **Entrenar el modelo con Train** (sin ver Test).
2. **Generar Top-5 recomendaciones por usuario** para Test.
3. **Calcular métricas**:
   - ¿Cuánto acierta? (P@5, R@5, NDCG@5)
   - ¿Cuánto viola el orden pedagógico? (PVR Pre y PVR Post)
   - ¿Cuánto contenido distinto recomienda? (Coverage)

---

### ¿Qué modelos comparamos?

1. **Popularidad** (baseline)
   - Recomienda los 5 contenidos más consumidos por todos.
   - No usa el perfil del usuario.
   - Es el "tonto" de la comparación.

2. **Random** (baseline inferior)
   - Recomienda 5 contenidos al azar.
   - Sirve para saber si los modelos "inteligentes" realmente son mejores que el azar.

3. **TF-IDF + Cosine Similarity** (filtrado por contenido)
   - Construye un perfil del usuario basado en los textos que leyó.
   - Recomienda contenidos similares.
   - Es el "lector de biblioteca".

4. **Híbrido SVD + Ridge** (colaborativo + demográfico)
   - **SVD**: factoriza la matriz usuarios×contenidos en 10 dimensiones latentes.
   - **Ridge**: añade features demográficos (edad, sexo, educación).
   - Es el "que combina conocimiento colectivo + datos del usuario".

5. **NCF-MLP** (red neuronal)
   - Embeddings aprendidos para cada usuario e item.
   - Una red neuronal (MLP) que predice la interacción.
   - Es el "deep learning".

---

### 🛡️ El filtro pedagógico (muro de seguridad)

Antes de devolver las recomendaciones, aplicamos un **filtro basado en grafo de prerrequisitos**:

```
Concepto C02 (ahorro) → C07 (inflación) → C06 (interés compuesto) → C13 (riesgo) → C12 (inversión)

Si el usuario no domina C02, no puede ver contenidos que requieran C02.
```

Por ejemplo, un usuario que nunca leyó sobre ahorro NO verá contenido de inversión avanzada (porque ese contenido enseña inversión, que requiere haber dominado ahorro).

**PVR Pre** (Pedagogical Violation Rate, pre-filtro): qué porcentaje de las recomendaciones del modelo violan las reglas pedagógicas ANTES del filtro.

**PVR Post** (post-filtro): mismo cálculo DESPUÉS de aplicar el filtro. Si el filtro funciona, PVR Post ≈ 0%.

---

### Las métricas

| Métrica | Qué mide | Rango |
|---|---|---|
| **Precision@5** | De las 5 recomendaciones, cuántas eran relevantes (en su historial real de Test) | 0-1 |
| **Recall@5** | De sus lecturas relevantes en Test, cuántas aparecieron en las 5 recomendaciones | 0-1 |
| **NDCG@5** | Como Recall pero ponderado: posición 1 vale más que posición 5 | 0-1 |
| **Coverage** | Qué porcentaje del catálogo total (104 contenidos) fue recomendado a al menos un usuario | 0-100% |
| **PVR Pre** | % de recomendaciones que violan las reglas pedagógicas (antes del filtro) | 0-100% |
| **PVR Post** | Mismo, después del filtro (debe ser 0% si el filtro funciona) | 0-100% |
| **Filter Rate** | % de posiciones del ranking crudo que fueron rechazadas por el filtro | 0-100% |
| **Feasibility@5** | % de usuarios con Test relevante que obtuvieron 5 recomendaciones **tras el filtro** (no tras el fallback). Si el filtro deja menos de 5, el usuario queda "no feasible" | 0-100% |

---

### 🆚 Warm vs Cold Start

El script evalúa dos escenarios:

| Escenario | Hipótesis |
|---|---|
| **Warm Start** | El usuario ya ha interactuado, el modelo tiene historial. |
| **Cold Start** | El usuario es nuevo, el modelo solo tiene el perfil del cuestionario. |

Se prueban los 5 modelos en ambos, y se reportan por separado.

---

## 📊 Los archivos que se generan tras la evaluación

Tras ejecutar `python3 src/utils/evaluate_models.py`:

| Archivo | Qué contiene |
|---|---|
| `data/evaluation_metrics_warm.csv` | Resultados de Warm para los 5 modelos (incluye RAW + POST + filter + feasibility) |
| `data/evaluation_metrics_cold.csv` | Resultados de Cold para los 5 modelos |

Las columnas son:
```
modelo, precision_5, recall_5, ndcg_5, raw_precision_5, raw_recall_5, raw_ndcg_5,
coverage_pct, pvr_pre_pct, pvr_post_pct, filter_rate_pct, feasibility_at_5_pct
```

---

## 📋 Cómo reproducir el experimento desde cero

```bash
# 1. (Opcional) Re-scrapear los contenidos del catálogo → data/scraped/
#    Requiere: pip3 install trafilatura lxml pymupdf httpx beautifulsoup4
python3 /Users/veronica/Desktop/tfm/data/scripts/ingest_contents.py

# 2. (Opcional) Enriquecer con LLM → data/enriched/
#    Requiere: pip3 install anthropic  y  export ANTHROPIC_API_KEY=...
python3 /Users/veronica/Desktop/tfm/data/scripts/enrich_contents.py

# 3. Generar usuarios (1.916 perfiles)
python3 /Users/veronica/Desktop/tfm/data/scripts/regenerate_users_from_ecf.py

# 4. Generar interacciones (23.000 lecturas simuladas) → interactions_synthetic_v2_validated.csv
python3 /Users/veronica/Desktop/tfm/data/scripts/generate_interactions_v2.py

# 5. Evaluar los 5 modelos
cd /Users/veronica/Desktop/tfm/ECF-archivos
python3 /Users/veronica/Desktop/tfm/src/utils/evaluate_models.py

# 6. Leer resultados
cat /Users/veronica/Desktop/tfm/data/evaluation_metrics_warm.csv
cat /Users/veronica/Desktop/tfm/data/evaluation_metrics_cold.csv
```

Si todo funciona, verás las tablas con P@5, R@5, NDCG@5, PVR Pre/Post, Filter Rate, Feasibility para los 5 modelos.

---

## 🕷️ El pipeline de contenidos reales (scraping + enriquecimiento)

Este es el trabajo más reciente del proyecto: en lugar de depender solo de resúmenes escritos a mano, los contenidos del catálogo ahora se obtienen **directamente de las fuentes oficiales** (Finanzas para Todos, CNMV, Banco de España).

1. **`ingest_contents.py`** descarga cada URL de `data/contents.csv`:
   - Si es **HTML**, extrae el texto con **Trafilatura** (conserva títulos, secciones y enlaces).
   - Si es **PDF**, extrae el texto con **PyMuPDF**.
   - Escribe un JSON por contenido en `data/scraped/<content_id>.json` más dos reportes (`ingest_report.json` y `ingest_summary.csv`). Es reanudable y tolerante a fallos (si una URL falla, sigue con las demás).

2. **`enrich_contents.py`** usa **Claude (Haiku 4.5)** para generar, a partir del texto scrapeado:
   - `tldr`: resumen de 2-4 frases.
   - `key_points`: 3-5 puntos clave.
   - `quiz`: 3 preguntas tipo test (4 opciones, 1 correcta, explicación), **cada una etiquetada con el `concept_id` que evalúa**.
   - Escribe en `data/enriched/<content_id>.json` (capa paralela a `scraped/`, no se mezclan). Es reanudable (`--force` para regenerar, `--pilot` para probar con unos pocos).

> **Nota:** el scraping y el enriquecimiento alimentan el **catálogo** (qué contenidos existen y qué enseñan). No cambian el pipeline de evaluación de modelos, que sigue leyendo `interactions_synthetic.csv`.

---

## 🎯 Lo que puedes afirmar en el TFM (y lo que NO)

### ✅ Puedes afirmar:
- "El dataset sintético refleja las proporciones reales de la ECF 2021 para jóvenes de 18-34 años."
- "El filtro pedagógico reduce la tasa de violaciones pedagógicas (PVR) a 0% en todos los modelos."
- "Popularidad supera a los modelos personalizados en P@5 en Warm Start, lo que es consistente con la literatura sobre datasets dispersos."
- "TF-IDF muestra mayor cobertura (diversidad) que Popularidad en ambos escenarios."
- "La separación Train/Test por (user_id, content_id) evita leakage, y un `assert` lo garantiza."
- "En Cold Start, Popularidad también lidera P@5 (0.146), seguida de la variante NeuMF (0.123)."

### ❌ NO puedes afirmar:
- "Los modelos personalizados son significativamente mejores que Popularidad" (sin pruebas estadísticas).
- "El sistema está listo para producción" (es un piloto de TFM).
- "Estos resultados se generalizan a la población española" (es un dataset sintético).

---

## 🗺️ Mapa rápido del proyecto

```
TFM/
├── Trabajo_Final_de_Master.pdf    ← Borrador principal del TFM
├── cronograma-4-semanas.md          ← Planificación inicial
├── plan-datos.md                    ← Plan de generación de datos
├── tareas-semana-1-dataset.md       ← Tareas semana 1
│
├── ECF-archivos/                    ← DATOS ORIGINALES (BdE)
│   └── ecf_2021.csv                 ← La encuesta completa (7.764 entrevistas)
│
├── data/
│   ├── scripts/                     ← Scripts del generador (orden cronológico)
│   │   ├── regenerate_users_from_ecf.py    ← PASO 2: crear usuarios
│   │   ├── generate_interactions_v2.py     ← PASO 3: crear interacciones (v2 actual)
│   │   ├── ingest_contents.py              ← scraping de URLs → data/scraped/
│   │   ├── enrich_contents.py              ← enriquecimiento LLM → data/enriched/
│   │   └── repair_catalog_structure.py     ← (herramienta de catálogo)
│   ├── scraped/                     ← texto crudo extraído de cada URL (JSON)
│   ├── enriched/                    ← TLDR + key_points + quiz por contenido (JSON)
│   ├── users_synthetic.csv           ← output del PASO 2
│   ├── interactions_synthetic*.csv ← output del PASO 3 (v2_validated es el vigente)
│   ├── concepts.csv, contents.csv, prerequisites.csv, content_concept_map.csv, sources.csv ← datos pedagógicos
│   ├── evaluation_metrics_*.csv     ← output del PASO 5
│   └── README.md                     ← este archivo para ti misma
│
├── src/
│   └── utils/
│       └── evaluate_models.py       ← SCRIPT PRINCIPAL (PASO 5)
│
├── docs/                             ← Documentación adicional
│   ├── README.md                     ← te apunta a este archivo
│   ├── README_PROCESO_TFM.md         ← ESTÁS AQUÍ
│   ├── informe_detallado_evaluacion.md
│   └── plan_evaluacion_modelos.md
│
├── archive/                          ← No tocar (histórico)
│
└── pdfs/                            ← PDFs de referencia del TFM
```

---

## ❓ FAQ (preguntas frecuentes)

**P: ¿Por qué 1.916 usuarios y no 7.764?**
R: El TFM está enfocado en jóvenes de 18-34 años. 7.764 incluye personas mayores, cuyo perfil financiero es distinto.

**P: ¿Por qué 23.000 interacciones y no más?**
R: El script genera entre 10 y 14 interacciones por usuario (media 12). Con 1.916 × 12 = ~23.000. Aumentar más no aporta señal significativa y ralentiza la evaluación.

**P: ¿Dónde está el texto real de los contenidos?**
R: En `data/scraped/` (texto crudo extraído de las URLs oficiales) y en `data/enriched/` (resumen, puntos clave y quiz generados con LLM). El catálogo `contents.csv` solo guarda los metadatos (tema, dificultad, URL).

**P: ¿Qué es el symlink `interactions_synthetic.csv`?**
R: Es un enlace simbólico a `interactions_synthetic_v2_validated.csv`, la versión vigente del generador. Así el pipeline siempre lee la versión correcta sin tocar el nombre del fichero. La versión anterior (`v1_backup`) se conserva como respaldo.

**P: ¿Por qué el filtro pedagógico se llama "muro de seguridad"?**
R: Porque **garantiza** que el sistema nunca recomiende algo inadecuado, sin importar lo que diga el modelo de IA. El modelo puede equivocarse; el filtro no.

**P: ¿Por qué el gate de inversión exige 4 prerrequisitos y no 2?**
R: Seguridad pedagógica. Con 4 prerrequisitos (C02+C07+C06+C13) se asegura que el usuario tiene fundamentos sólidos antes de invertir. Reducir a 2 comprometería la seguridad.

**P: ¿Qué es "raw_precision" vs "precision"?**
R: RAW es la calidad del ranking crudo del modelo. POST es la calidad después del filtro pedagógico. Si RAW es bajo, el modelo es malo. Si POST es aún menor, el filtro está bloqueando contenido que era relevante.

**P: ¿Qué es `filter_rate_pct`?**
R: Porcentaje de posiciones del ranking crudo del modelo que fueron RECHAZADAS por el filtro pedagógico antes del fallback. Mide cuánto "trabaja" el filtro.

**P: ¿Por qué el script evalúa 5 modelos si el TFM solo recomienda uno?**
R: El TFM compara 5 arquitecturas para **justificar** cuál recomendar en producción. Los resultados experimentales (no las justificaciones) muestran que Popularidad es muy fuerte, pero los modelos personalizados pueden competir bajo ciertas condiciones.

---

## 🎯 TL;DR (para el tribunal si pregunta "¿de qué va el TFM?")

> *"He construido un sistema de recomendación de contenidos de educación financiera para jóvenes de 18-34 años. El sistema genera recomendaciones personalizadas y las filtra por un grafo de prerrequisitos pedagógicos para garantizar que el usuario nunca reciba contenidos para los que no está preparado. He comparado cinco modelos de recomendación — desde el más básico (Popularidad) hasta una red neuronal — y he medido la calidad de sus recomendaciones y su seguridad pedagógica. Los resultados muestran que el filtro garantiza el 0% de violaciones pedagógicas en todos los modelos, y que los modelos personalizados pueden competir con Popularidad cuando el dataset tiene suficiente densidad."*
