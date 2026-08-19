# Pendientes de corrección en `Trabajo_Final_de_Master.pdf`

> **Estado:** borrador de notas. NO refleja cambios aplicados todavía. Aplicar después de validar el resto del dataset.
>
> **Fuentes verificadas al 2026-08-18** (ver `sources.csv` actualizado).

---

## 1. Error factual: la encuesta OECD/INFE 2023

**Ubicación probable:** Capítulo 2 (Contexto y Estado del Arte) y Capítulo 1 (Introducción), donde se cita la evidencia sobre jóvenes 18-34.

**Texto actual (aproximado, según lo que aparece en `resumen_actual.md` y `validation_summary.md` antes de la corrección):**
> "La encuesta OECD/INFE de 2023 fue cancelada antes de la recogida de datos."

**Texto corregido:**
> "La encuesta OECD/INFE 2023 sí se publicó en diciembre de 2023 (OECD Business and Finance Policy Papers, No. 39, DOI 10.1787/56003a32-en). Cubre 39 países, incluido España, e introduce por primera vez preguntas sobre criptoactivos y brecha digital. España obtuvo una puntuación global de 14,3 sobre 21, por encima de la media OCDE (13,7)."

**Cita bibliográfica para añadir a las Referencias:**
> OECD (2023). *OECD/INFE 2023 International Survey of Adult Financial Literacy*. OECD Business and Finance Policy Papers, No. 39. OECD Publishing, Paris. https://doi.org/10.1787/56003a32-en

**Acción:** buscar todas las menciones a "OECD/INFE 2020" o "OECD/INFE 2023 cancelada" en el PDF y reemplazar.

---

## 2. Sustituir OECD/INFE 2020 por OECD/INFE 2023

**Razón:** la encuesta 2020 está obsoleta. La 2023 es más reciente y comparable.

**Cambio en la sección 2.1 (Alfabetaización Financiera: Definición, Medición y Brechas):**
- Donde se cite "OECD/INFE 2020" o "Lusardi y Mitchell 2014" como evidencia principal de medición, complementar con OECD/INFE 2023.

**Cambio en la sección 2.1.3 (Brechas específicas en jóvenes profesionales 22-30 años):**
- Los datos de jóvenes españoles (52% Big3, 60% inflación, 44% interés compuesto, 50% diversificación) vienen de la ECF 2021 (BdE + CNMV), que es correcto y sigue vigente. No cambiar.
- Si se citan datos comparativos internacionales de jóvenes, usar OECD/INFE 2023 (39 países) en lugar de 2020.

**Cita bibliográfica a eliminar o reemplazar:**
> OECD (2020). *OECD/INFE 2020 International Survey of Adult Financial Literacy*. OECD Publishing, Paris.

**Reemplazar por:**
> OECD (2023). *OECD/INFE 2023 International Survey of Adult Financial Literacy*. OECD Business and Finance Policy Papers, No. 39. OECD Publishing, Paris. https://doi.org/10.1787/56003a32-en

---

## 3. Actualizar la versión del OECD/INFE Toolkit

**Razón:** la versión 2022 del Toolkit está obsoleta. La 2026 (publicada en enero 2026) es la más reciente e incluye las dimensiones de "inclusión financiera" y "bienestar financiero", alineadas con el marco que usa el BdE actualmente.

**Texto a actualizar (si aparece la versión 2022):**
> "OECD/INFE (2022). *OECD/INFE Toolkit for Measuring Financial Literacy and Financial Inclusion 2022*."

**Texto corregido:**
> "OECD (2026). *OECD/INFE Toolkit for Measuring Financial Literacy, Inclusion and Well-Being 2026*. OECD Publishing, Paris. https://www.oecd.org/content/dam/oecd/en/publications/reports/2026/01/oecd-infe-toolkit-for-measuring-financial-literacy-inclusion-and-well-being-2026_6e8d9566/92f2d439-en.pdf"

---

## 4. Sección 2.4.7 (Vacío identificado) — refinar el aporte

**Texto actual (resumido):**
> "Ninguno de los trabajos revisados combina Neural Collaborative Filtering con grafos de conocimiento en educación financiera para jóvenes."

**Observación:** esta afirmación es fuerte y se sostiene en la Tabla 2.1 (Comparativa de trabajos relacionados). Pero el estado del arte en ERS ha avanzado: hay modelos KGCN y LKGA (citados en 2.4.5) en contextos educativos generales (MOOC, tutoría inteligente). Considerar matizar:
> "En el dominio específico de educación financiera para jóvenes profesionales, no hemos identificado trabajos que integren simultáneamente tres elementos: (i) personalización mediante un modelo híbrido de deep learning, (ii) restricciones pedagógicas de secuenciación modeladas explícitamente con un grafo de conocimiento, y (iii) un mecanismo de evaluación de maestría que retroalimente el sistema."

**Acción:** revisar la redacción para que el "vacío identificado" sea preciso y no se pueda objetar con un paper reciente.

---

## 5. Capítulo 3 (Objetivos concretos y metodología) — alinear con `sources.csv`

**Texto actual (sección 3):**
> "Se detalla la pipeline de datos: obtención y preprocesamiento de datasets (ECF 2021, metadatos de cursos)..."

**Verificar:**
- Que las fuentes citadas en la pipeline coinciden con el `sources.csv` actualizado (8 fuentes, no las 8 originales).
- Si se menciona "OECD/INFE 2020" como input del dataset, sustituir por "OECD/INFE 2023".
- Si se menciona "PISA 2022 Financial Literacy Framework" como input de la taxonomía, mantener (es correcto y la URL actualizada está en S6).

---

## 6. Capítulo 4 (Identificación de Requisitos) — sección 4.7 Requisitos de datos

**Texto actual (probable, según el plan):**
> "Los datos del sistema provienen de fuentes oficiales: Finanzas para Todos, CNMV, BdE, OECD/INFE 2020, ECF 2021."

**Acción:** revisar que la lista de fuentes coincide con `sources.csv` (8 fuentes verificadas). Si hay diferencias, alinear.

---

## 7. Capítulo 2.6.1 (Modelo de recomendación: NeuMF) — disclaimer de viabilidad

**Texto actual (sección 2.6.1):**
> "La selección definitiva del modelo no se plantea como una decisión exclusivamente teórica. Se sustentará en una evaluación experimental en la que se medirán métricas estándar de recomendación, como NDCG@k y Precision@k..."

**Observación:** con 250 usuarios y 1.500 interacciones sintéticas (media de 6 por usuario), NeuMF puro probablemente no va a converger de forma estable. Considerar añadir un párrafo en la sección 2.6.1 (o en el cap. 4 de resultados) que diga:

> "Dada la limitación del tamaño del dataset sintético (250 usuarios, 1.500 interacciones), se prevé que el modelo NeuMF puro presente alta varianza en los embeddings de usuario. Por este motivo, la contribución principal del trabajo se centra en la **arquitectura híbrida** (modelo de recomendación + grafo de conocimiento como post-filtro pedagógico), no en el modelo neuronal aislado. Se implementará un baseline más simple (LightFM con features de contenido) como referencia para medir la aportación del KG."

**Acción:** decidir si se añade este disclaimer en el cap. 2 (preventivo) o en el cap. 4 (después de los experimentos). Mi recomendación: preventivo en el cap. 2.

---

## 8. Bibliografía — sustituir y añadir

**Sustituir:**
- Cualquier entrada a "OECD/INFE 2020 Survey" por la entrada 2023 (ver sección 2 de este archivo).
- Cualquier entrada a "OECD/INFE Toolkit 2022" por la entrada 2026 (ver sección 3).

**Añadir si no está:**
> Mancia Perdomo, C. J., & Bachiller Baroja, P. (2025). *Conocimiento financiero de los jóvenes en España: análisis basado en la Encuesta de Competencias Financieras de 2021* (Trabajo Fin de Máster). Universidad de Zaragoza. http://zaguan.unizar.es/record/169552
>
> Banco de España (2025). *La tenencia de criptoactivos entre los hogares españoles*. Boletín Económico 2025-T1, artículo 09. https://www.bde.es/f/webbe/Secciones/Publicaciones/InformesBoletinesRevistas/BoletinEconomico/25/T1/Files/be2501-art09.pdf
>
> MOOCCubeX: A Knowledge-driven and Large-scale MOOC Dataset. arXiv:2407.12399.

---

## 9. Pendiente de validar: cifras concretas del PDF

**Sección 1.1.1 (Identificación del problema):**
- "46% de respuestas correctas en 2016" → verificar con ECF 2016 (BdE).
- "52% en 2021" → verificar con ECF 2021 (BdE). **Cifra confirmada: 52% es correcto para 18-34 años.**
- "44% interés compuesto" → verificar. **Confirmado: 44% para 18-34 años.**
- "60% inflación" → verificar. **Confirmado: 60% para 18-34 años.**
- "50% diversificación del riesgo" → verificar. **Confirmado: 50% para 18-34 años.**

**Acción:** añadir nota al pie o en el cuerpo que indique "datos de la ECF 2021, Banco de España, jóvenes 18-34 años" para que el lector pueda verificar.

---

## 10. Pendiente de verificar: cifras del cap. 1.1.3 (Relevancia del problema)

**Texto a verificar:**
- "barrera del ahorro inicial" en torno al 30-32% del valor del inmueble (20% entrada + 10-12% impuestos/gastos).
- Esta cifra NO sale de la ECF 2021 ni de OECD/INFE. Buscar fuente original (probable: BdE, INE, idealista, Fotocasa, EBA). **Si no se encuentra fuente oficial, eliminar o matizar como "estimación habitual del sector".**

**Acción:** antes de entregar el TFM, localizar fuente citable o reescribir como "estimación aproximada del sector inmobiliario español".

---

## Resumen ejecutivo de cambios pendientes

| # | Cambio | Prioridad | Esfuerzo |
|---|---|---|---|
| 1 | Corregir error factual OECD/INFE 2023 | Alta | Bajo |
| 2 | Sustituir OECD/INFE 2020 por 2023 | Alta | Bajo |
| 3 | Actualizar Toolkit a versión 2026 | Media | Bajo |
| 4 | Refinar "vacío identificado" en 2.4.7 | Media | Medio |
| 5 | Alinear cap. 3 con `sources.csv` | Media | Bajo |
| 6 | Alinear cap. 4.7 con `sources.csv` | Media | Bajo |
| 7 | Añadir disclaimer NeuMF en cap. 2.6.1 | Alta | Medio |
| 8 | Actualizar bibliografía | Alta | Bajo |
| 9 | Verificar cifras cap. 1.1.1 | Baja | Bajo |
| 10 | Verificar cifra 30-32% barrera ahorro | Media | Medio (búsqueda de fuente) |
| 11 | Actualizar cap. 3 con cifras reales ECF 2021 | Alta | Bajo |
| 12 | Añadir nota sobre corrección de sesgo de género | Alta | Bajo |
| 13 | Mencionar variables Big3 del ECF si se cita | Media | Bajo |
| 14 | Explicar discrepancia con % publicados | Media | Bajo |
| 15 | Re-ejecutar `interactions_synthetic.csv` | Alta | Bajo |

---

## 11. Cambios derivados del análisis ECF 2021 (nuevo, 2026-08-18)

### 11.1 Cambio en `users_synthetic.csv`

**Ubicación probable:** Capítulo 3 (Metodología) o Capítulo 4 (Requisitos de datos), donde se describe cómo se construyeron los usuarios sintéticos.

**Hecho nuevo:** el dataset `users_synthetic.csv` ya no usa distribuciones inventadas. Está muestreado de los 1.916 jóvenes 18-34 de la ECF 2021 (BdE + CNMV, DOI 10.53479/34752).

**Distribuciones reales resultantes** (de los 250 usuarios muestreados):

| Variable | Distribución real |
|---|---|
| financial_knowledge_level | bajo 56%, medio 32%, alto 12% |
| education_level | bachillerato 52%, universidad 29%, posgrado 13%, secundaria 6%, primaria 1% |
| employment_status | empleado 60%, estudiante 26%, desempleado 14% |
| saving_habit | frecuente 84%, ocasional 16% |
| investment_experience | ninguna 90%, básica 10% |
| sex (corregido, ver 11.2) | 50% hombre, 50% mujer |
| age_group | 25-34: 59%, 18-24: 41% |

**Acción:** actualizar el cap. 3 o 4 con estas cifras y mencionar la fuente (muestreo de ECF 2021 jóvenes 18-34, n=1.916).

### 11.2 Corrección del sesgo de género

**Problema:** la submuestra de jóvenes 18-34 en el ECF tiene 85% hombres y 15% mujeres, lo cual NO refleja la realidad demográfica española (~50/50 en este tramo etario).

**Decisión:** sobrescribir `sex` con distribución 50/50 en `users_synthetic.csv`.

**Texto a añadir en el cap. 3 o 4 (sección de limitaciones o de decisiones metodológicas):**
> "Durante la calibración del dataset sintético con microdatos de la ECF 2021, se detectó un sesgo de género en la submuestra de jóvenes 18-34 (85% hombres, 15% mujeres) atribuible al diseño muestral. Para evitar introducir un sesgo artificial en el modelo de recomendación, se sobrescribió la variable `sex` con una distribución 50/50, manteniendo las demás variables calibradas con datos reales. Esta corrección asume que no existen diferencias relevantes por sexo en las recomendaciones de contenidos de educación financiera."

### 11.3 Variables del Big3 identificadas en el CSV

**Para el cap. 3 (Metodología) o cap. 4 (Requisitos):** si se cita cómo se midió el conocimiento financiero de los usuarios sintéticos, las variables del ECF son:

| Big3 | Variable CSV | Respuesta correcta |
|---|---|---|
| Inflación (QK3) | `k0600` | 3 (Menos) |
| Interés compuesto (QK6) | `k0100` | 3 (Más de 110) |
| Diversificación (QK7 item 3) | `k1003` | 1 (Verdadero) |

**Nota metodológica:** las preguntas Big3 tienen una alta tasa de "No sabe / No contesta" (~50% en jóvenes 18-34). El script `regenerate_users_from_ecf.py` considera NS/NC como "nivel bajo" de conocimiento, lo cual es coherente con la interpretación del ECF.

### 11.4 Discrepancia con cifras publicadas del ECF

Los % de acierto en Big3 calculados sobre la submuestra 18-34 con respuestas válidas son:

- Inflación: 72.1% (sin NS/NC) vs 60% publicado.
- Interés compuesto: 57.3% (sin NS/NC) vs 44% publicado.
- Diversificación: 70.4% (sin NS/NC) vs 50% publicado.

**Posible razón:** el ECF probablemente usa una metodología distinta (imputación de NS/NC, muestra específica con Big3, o incluye NS/NC como "incorrecto").

**Acción:** si se cita el % publicado, mencionar la diferencia metodológica en una nota al pie. No es un error, es una diferencia de criterio.

---

## 12. Cambios pendientes tras regenerar el dataset

Una vez regenerado `users_synthetic.csv`, hay que actualizar también:

- **`validation_summary.md`** → regenerar con las nuevas cifras de distribución.
- **`interactions_synthetic.csv`** → re-ejecutar `generate_interactions.py` con los nuevos usuarios.
- **Cap. 4.7 (Requisitos de datos)** → indicar que los usuarios sintéticos ahora están calibrados con ECF 2021 real, no inventados.
- **Cap. 5 (Descripción de la herramienta)** → si describe las estadísticas de los datos de entrada, actualizarlas.

---

## 13. Versión "realistic" de las interacciones (nuevo, 2026-08-18)

**Hecho:** Se ha creado una segunda versión de las interacciones sintéticas que usa variables reales de comportamiento financiero del ECF 2021 para personalizar las recomendaciones.

### 13.1 Dos versiones disponibles

| Archivo | Modelo | Base empírica |
|---|---|---|
| `interactions_synthetic.csv` (PRINCIPAL) | `generate_interactions_realistic.py` | 5 variables del ECF: ahorro, cuenta ahorro, ahorro informal, gasto imprevisto, cobertura de gastos |
| `interactions_synthetic_realistic.csv` (histórico) | `generate_interactions_realistic.py` | Idéntico al principal (copia) |

> **Nota:** Se ha renombrado la versión sigmoid original a histórica. Si necesitas regenerar con la versión antigua, está disponible en el historial de git.

### 13.2 Variables del ECF usadas en la versión "realistic"

| Variable ECF | Significado | Distribución jóvenes 18-34 |
|---|---|---|
| `b0130a` | Tiene alguna forma de ahorro | 50.5% sí |
| `b0130b` | Tiene cuenta de ahorro/depósito | 86.3% sí |
| `b0130c` | Tiene ahorro informal (familia, club) | 9.3% sí |
| `b1000b` | Puede pagar gasto imprevisto sin pedir prestado | 60.6% sí |
| `a0320` | Ha dejado de cubrir gastos en últimos 12 meses | 20.6% sí |

### 13.3 Lógica del modelo "realistic"

- **Affinidad por topic**: cada usuario tiene un peso de afinidad por cada topic, calculado a partir de sus respuestas del ECF.
- **Ponderación en el muestreo**: dentro del pool de contenidos elegibles (tras aplicar las 6 reglas pedagógicas), la elección se pondera por la afinidad del usuario.
- **Boost en engagement**: la afinidad también modula la probabilidad de hacer clic (no solo de qué contenido).

### 13.4 Texto propuesto para cap. 3 (Metodología)

> "Las interacciones sintéticas se generaron mediante un modelo de afinidad temática que pondera la probabilidad de elección de cada contenido según 5 indicadores reales de comportamiento financiero del usuario, obtenidos de la Encuesta de Competencias Financieras 2021 (BdE + CNMV): tenencia de cuenta de ahorro, ahorro informal, capacidad de respuesta ante imprevistos y cobertura habitual de gastos. Esta calibración permite que las recomendaciones reflejen perfiles de comportamiento financieramente realistas, aunque las interacciones en sí son sintéticas."

### 13.5 Limitaciones a declarar

- **Los efectos por comportamiento son pequeños** (+0.7 a +2.1 pp) debido al tamaño muestral (1.500 interacciones, 250 usuarios) y al desbalance del catálogo (60% contenidos en planificación, ahorro y fraude).
- **Las direcciones son correctas** pero la magnitud es modesta. Con más contenidos de deuda/crédito y más interacciones, los efectos serían más visibles.
- **Las interacciones siguen siendo sintéticas**: representan un comportamiento plausible, no comportamiento humano real observado.

---

## Notas para el editor

- Si tienes el `.tex` fuente del TFM, todas estas correcciones van en ese archivo y se regenera el PDF.
- Si solo tienes el PDF, las correcciones hay que hacerlas en un editor de PDF (Acrobat, Preview en Mac con texto seleccionable) o rehacer la maquetación.
- El `resumen_actual.md` y `validation_summary.md` ya están corregidos al 2026-08-18. Las cifras y atribuciones que aparecen en el PDF deben coincidir con las de esos dos archivos MD.
