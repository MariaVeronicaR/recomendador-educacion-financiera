# Resumen de validación del dataset

**Fecha de generación:** 2026-07-02
**TFM:** Sistema de recomendación personalizada de contenidos de educación financiera

---

## 1. Resumen ejecutivo

| Métrica | Valor | Mínimo plan | Estado |
|---|---|---|---|
| Fuentes oficiales registradas | 8 | 6 | ✅ |
| Contenidos reales con URL | 60 | 50 | ✅ |
| Conceptos en taxonomía | 30 | 17 | ✅ |
| Relaciones de prerrequisito | 33 | 14 | ✅ |
| Usuarios sintéticos | 250 | 200 | ✅ |
| Interacciones sintéticas | 1.500 | 1.000 | ✅ |
| % contenidos con URL https oficial | 100% | ≥ 95% | ✅ |

---

## 2. Distribución de contenidos por dificultad

| Dificultad | Nº contenidos | % |
|---|---|---|
| Básico | 27 | 45,0% |
| Intermedio | 19 | 31,7% |
| Avanzado | 14 | 23,3% |

**Nota:** la distribución de contenidos no es 60/30/10 porque el catálogo refleja la oferta real de las fuentes, donde abundan materiales introductorios. La distribución de las interacciones sintéticas sí se acerca al 60/30/10 que pide el plan (ver sección 4).

---

## 3. Distribución de contenidos por tema

| Tema | Nº contenidos |
|---|---|
| planificación | 14 |
| inversión | 11 |
| hipotecas | 9 |
| fraude | 6 |
| cuentas bancarias | 5 |
| tarjetas | 4 |
| préstamos | 4 |
| interés | 3 |
| ahorro | 3 |
| deuda | 2 |
| riesgo | 2 |
| diversificación | 1 |

**Contenidos marcados como relacionados con inversión:** 11 (sobre 60).

---

## 4. Distribución de interacciones sintéticas

**Por evento:**

| Evento | Nº interacciones | % |
|---|---|---|
| completed | 639 | 42,6% |
| viewed | 452 | 30,1% |
| quiz_passed | 334 | 22,3% |
| disliked | 75 | 5,0% |

**Por dificultad del contenido consumido:**

| Dificultad | Nº interacciones | % | Objetivo plan |
|---|---|---|---|
| Básico | 971 | 64,7% | 60% |
| Intermedio | 427 | 28,5% | 30% |
| Avanzado | 102 | 6,8% | 10% |

La desviación respecto al objetivo se debe a que la oferta de contenidos avanzados es limitada (14) y a las reglas pedagógicas (los usuarios principiantes no consumen avanzados).

**Distribución de usuarios por nivel de conocimiento (basado en la Encuesta BdE/CNMV 2021):**

| Conocimiento | Nº usuarios | % |
|---|---|---|
| Bajo | 104 | 41,6% |
| Medio | 109 | 43,6% |
| Alto | 37 | 14,8% |

---

## 5. Validaciones de coherencia pedagógica

### 5.1. Adecuación nivel-contenido
- **Usuarios con nivel bajo (104) que consumen contenido avanzado:** 14 interacciones, lo que representa el 1,4% de sus interacciones. Por debajo del 5% de tolerancia definido en el plan.
- **Interpretación:** la regla 1 del plan se respeta: los principiantes consumen mayoritariamente contenidos básicos (400 de 594 interacciones de nivel bajo).

### 5.2. Inversión sin prerrequisitos
- **Contenidos de inversión consumidos sin haber visto ahorro/inflación/interés/riesgo:** 0. La regla 3 se respeta estrictamente en el generador.
- **Porcentaje de contenidos avanzados de inversión mostrados a principiantes sin experiencia inversora:** 0%.

### 5.3. Cumplimiento de prerrequisitos por tema
- El generador aplica la regla 4: para contenidos no básicos el usuario debe haber visto al menos 2 conceptos base del tema.
- En la práctica, los usuarios con conocimiento bajo no llegan a contenidos avanzados de inversión ni de hipoteca, porque no superan los filtros.

### 5.4. Diversidad de catálogo
- **Contenidos distintos consumidos:** todos los 60 aparecen al menos una vez en el dataset sintético.
- **Cobertura de usuarios:** los 250 usuarios tienen al menos 4 interacciones (umbral mínimo para que un recomendador colabore tenga señal suficiente).

---

## 6. Fuentes utilizadas

Las 8 fuentes son oficiales (BdE, CNMV, OECD, OCDE/INFE). Se verificó la accesibilidad de cada URL con `WebFetch` el 2026-07-02. Ver `sources.csv` para detalle.

| # | Fuente | Organización | Uso principal |
|---|---|---|---|
| S1 | Finanzas para Todos | CNMV + BdE | Catálogo principal de contenidos |
| S2 | Guías del inversor | CNMV | Inversión y riesgo |
| S3 | Portal Cliente Bancario | BdE | Banca, hipotecas, fraude, simuladores |
| S4 | Plan Ed. Financiera 2022-2025 | CNMV + BdE | Marco institucional |
| S5 | OECD/INFE Framework | OECD | Definición de variables |
| S6 | PISA 2022 Financial Literacy | OECD | Marco para jóvenes |
| S7 | OECD/INFE 2020 Survey | OECD | Comparativa internacional |
| S8 | Encuesta Competencias 2021 | BdE + CNMV | Distribución real de usuarios |

**Nota sobre S7:** la encuesta OECD/INFE de 2023 fue cancelada antes de la recogida de datos. Se utiliza la de 2020, que es la más reciente disponible.

---

## 7. Limitaciones del dataset

1. **Interacciones sintéticas:** generadas por un modelo probabilístico (sigmoid sobre el gap conocimiento-dificultad). Reflejan la lógica del sistema pero no comportamiento humano real.
2. **Sesgo en perfiles sintéticos:** las distribuciones de los usuarios están calibradas con la Encuesta BdE/CNMV 2021, lo que puede reproducir sesgos de género, edad y nivel educativo presentes en la encuesta.
3. **Cobertura del catálogo:** 60 contenidos es suficiente para un prototipo pero deja fuera temas relevantes (impuestos avanzados, planificación fiscal, criptoactivos, etc.). El catálogo es ampliable.
4. **Granularidad de `is_investment_related`:** está marcado a nivel de contenido, no de sección. Un artículo de inversión puede incluir contenido introductorio.
5. **No hay metadatos de calidad de los contenidos** (puntuación, reseñas, autor). El recomendador no podrá usarlos.
6. **Eventos no incluyen "ratings explícitos"** más allá de liked/disliked inferidos por `event=disliked`.

---

## 8. Riesgos metodológicos

1. **Riesgo de sobreajuste a datos sintéticos:** si el modelo se entrena solo con estos datos, podría aprender los patrones del generador en lugar de preferencias reales. **Mitigación:** incluir un piloto real con usuarios humanos como validación externa.
2. **Riesgo de cold start:** 250 usuarios con 1.500 interacciones dan una media de 6 interacciones por usuario. Es bajo para NeuMF. **Mitigación:** arrancar con modelos más simples (popularidad, LightFM) como baseline.
3. **Riesgo de coherencia pedagógica insuficiente:** el post-filtro con grafo se valida solo en la generación sintética. **Mitigación:** revisar manualmente una muestra de recomendaciones.
4. **Riesgo de cobertura de temas desbalanceada:** hay muchos contenidos de planificación y pocos de diversificación. **Mitigación:** ampliar el catálogo o reponderar.

---

## 9. Aclaración obligatoria

> Las interacciones sintéticas no representan comportamiento real de usuarios. Se usan solo para construir, probar y evaluar inicialmente el sistema de recomendación. La validación definitiva requeriría usuarios reales o evaluación experta.

---

## 10. Próximos pasos

1. Ejecutar el generador de recomendaciones (NeuMF baseline + baseline de popularidad) sobre el dataset.
2. Validar la coherencia pedagógica de las recomendaciones top-k con el grafo de conocimiento.
3. Diseñar el cuestionario pre/post del piloto con ~30 usuarios reales.
4. Recoger datos reales del piloto y reentrenar / recalibrar el generador.
5. Comparar métricas antes y después de la calibración con datos reales.
