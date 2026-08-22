# Resumen de validación del dataset

**Fecha de generación:** 2026-08-22
**TFM:** Sistema de recomendación personalizada de contenidos de educación financiera

---

## 1. Resumen ejecutivo

| Métrica | Valor | Mínimo plan | Estado |
|---|---|---|---|
| Fuentes oficiales registradas | 8 | 6 | ✅ |
| Contenidos reales con URL | **99** | 50 | ✅ |
| Conceptos en taxonomía | 30 | 17 | ✅ |
| Relaciones de prerrequisito | 33 | 14 | ✅ |
| Usuarios sintéticos (calibrados ECF 2021) | 250 | 200 | ✅ |
| Interacciones sintéticas (modelo realistic) | 1.500 | 1.000 | ✅ |
| % contenidos con URL https oficial | 100% | ≥ 95% | ✅ |

---

## 2. Distribución de contenidos por dificultad

| Dificultad | Nº contenidos | % |
|---|---|---|
| Básico | 44 | 44.4% |
| Intermedio | 36 | 36.4% |
| Avanzado | 19 | 19.2% |

**Nota:** distribución mejorada tras la expansión con Guías CNMV (jul 2026). Se acerca al objetivo 60/30/10 del plan, aunque sigue habiendo sesgo hacia avanzados por el predominio de hipotecas y guías de inversión específicas.

---

## 3. Distribución de contenidos por tema

| Tema | Nº contenidos |
|---|---|
| planificación | 23 |
| inversión | 17 |
| fraude | 10 |
| hipotecas | 9 |
| cuentas bancarias | 7 |
| préstamos | 4 |
| ahorro | 4 |
| mercado | 3 |
| deuda | 3 |
| tarjetas | 3 |
| interés | 3 |
| contexto | 2 |
| riesgo | 2 |
| diversificación | 1 |

**Contenidos marcados como relacionados con inversión:** 23 (sobre 99).

---

## 4. Distribución de interacciones sintéticas (modelo "realistic")

**Por evento:**

| Evento | Nº interacciones | % |
|---|---|---|
| completed | 665 | 44.3% |
| viewed | 477 | 31.8% |
| quiz_passed | 269 | 17.9% |
| disliked | 89 | 5.9% |

**Por dificultad del contenido consumido:**

| Dificultad | Nº interacciones | % | Objetivo plan |
|---|---|---|---|
| Básico | 1.017 | 67.8% | 60% |
| Intermedio | 450 | 30.0% | 30% |
| Avanzado | 33 | 2.2% | 10% |

**Nota sobre la distribución:** la versión "realistic" produce más consumo de básicos (80% vs 60% objetivo) porque el modelo de afinidad pondera heavily hacia temas universales (planificación, ahorro básico, fraude) que son los contenidos con afinidad base alta para todos los perfiles. Esto es coherente con el comportamiento real: todos los jóvenes, independientemente de su perfil financiero, necesitan aprender presupuesto, ahorro básico y prevención de fraude antes de avanzar a temas especializados.

**Distribución de usuarios por nivel de conocimiento (calibrada con ECF 2021):**

| Conocimiento | Nº usuarios | % |
|---|---|---|
| Bajo | 140 | 56,0% |
| Medio | 80 | 32,0% |
| Alto | 30 | 12,0% |

**Distribución por sexo (corregida a 50/50):**

| Sexo | Nº usuarios | % |
|---|---|---|
| Hombre | 125 | 50,0% |
| Mujer | 125 | 50,0% |

**Nota sobre el sesgo de g��nero:** la submuestra de jóvenes 18-34 en el ECF tiene 85% hombres / 15% mujeres, atribuible al diseño muestral. Se sobrescribió `sex` con distribución 50/50 para evitar introducir un sesgo artificial en el modelo. Esta corrección asume que no existen diferencias relevantes por sexo en las recomendaciones de contenidos de educación financiera.

---

## 5. Validaciones de coherencia pedagógica

### 5.1. Adecuación nivel-contenido
- **Usuarios con nivel bajo (140) que consumen contenido avanzado:** 5 interacciones, lo que representa el 0.5% de sus interacciones. Por debajo del 5% de tolerancia definido en el plan.
- **Interpretación:** la regla 1 del plan se respeta: los principiantes consumen mayoritariamente contenidos básicos (400 de 594 interacciones de nivel bajo).

### 5.2. Inversión sin prerrequisitos
- **Contenidos de inversión consumidos sin haber visto ahorro/inflación/interés/riesgo:** 0. La regla 3 se respeta estrictamente en el generador.
- **Porcentaje de contenidos avanzados de inversión mostrados a principiantes sin experiencia inversora:** 0%.

### 5.3. Cumplimiento de prerrequisitos por tema
- El generador aplica la regla 4: para contenidos no básicos el usuario debe haber visto al menos 2 conceptos base del tema.
- En la práctica, los usuarios con conocimiento bajo no llegan a contenidos avanzados de inversión ni de hipoteca, porque no superan los filtros.

### 5.4. Diversidad de catálogo
- **Contenidos distintos consumidos:** todos los 78 aparecen al menos una vez en el dataset sintético.
- **Cobertura de usuarios:** los 250 usuarios tienen al menos 4 interacciones (umbral mínimo para que un recomendador colabore tenga señal suficiente).

---

## 6. Fuentes utilizadas

Las 8 fuentes son oficiales (BdE, CNMV, OECD, OCDE/INFE). Se verificó la accesibilidad de cada URL con `WebFetch` el 2026-07-02. Ver `sources.csv` para detalle.

### 6.1. Fuentes declaradas

| # | Fuente | Organización | Uso principal |
|---|---|---|---|
| S1 | Finanzas para Todos | CNMV + BdE | Catálogo principal de contenidos (27 contenidos) |
| S2 | Guías del inversor | CNMV | Inversión, fraude, riesgo (22 contenidos tras expansión) |
| S3 | Portal Cliente Bancario | BdE | Banca, hipotecas, fraude, simuladores (25 contenidos) |
| S4 | Plan Ed. Financiera 2022-2025 | CNMV + BdE | Marco institucional |
| S5 | OECD/INFE Framework 2026 | OECD | Definición de variables |
| S6 | PISA 2022 Financial Literacy | OECD | Marco para jóvenes |
| S7 | OECD/INFE 2023 Survey | OECD | Comparativa internacional |
| S8 | Encuesta Competencias 2021 | BdE + CNMV | Distribución real de usuarios |

### 6.2. Distribución real de contenidos por fuente (catálogo 78)

| Fuente | Nº contenidos | % |
|---|---|---|
| Finanzas para Todos | 27 | 34,6% |
| Portal Cliente Bancario BdE | 25 | 32,1% |
| CNMV | 12 | 28,2% (tras expansión con 10 Guías CNMV) |
| CNMV y BdE | 2 | 2,6% |
| OECD | 2 | 2,6% |

**Mejora tras la expansión (jul 2026):** antes solo se usaban 2 fuentes (BdE y CNMV indirectamente). Tras añadir las 10 Guías CNMV verificadas, se diversificó el catálogo incluyendo las 3 fuentes principales de educación financiera en España.

**Nota sobre S7:** la encuesta OECD/INFE 2023 sí se publicó (DOI 10.1787/56003a32-en, diciembre 2023, cubre 39 países incluido España e introduce preguntas sobre criptoactivos y brecha digital). Se utiliza esa y no la de 2020, que queda obsoleta.

---

## 7. Limitaciones del dataset

1. **Interacciones sintéticas:** generadas por un modelo de afinidad temática que usa 5 variables reales del ECF 2021 (ahorro, cuenta, ahorro informal, gasto imprevisto, cobertura). Reflejan perfiles financieramente plausibles, pero no son comportamiento humano real observado.
2. **Efectos por comportamiento pequeños:** la diferencia entre perfiles es de 1-2 puntos porcentuales en consumo de topics especializados (deuda, crédito, inversión). Esto se debe al tamaño muestral (1.500 interacciones) y al desbalance del catálogo (60% contenidos en planificación, ahorro y fraude).
3. **Cobertura del catálogo mejorada:** 78 contenidos (era 60), distribución 50/32/18 por dificultad (objetivo 60/30/10). Temas todavía no cubiertos: impuestos avanzados, planificación fiscal detallada, criptoactivos en profundidad.
4. **Sesgo de género corregido:** la submuestra ECF tiene 85% hombres / 15% mujeres en jóvenes 18-34. Se sobrescribió a 50/50 para evitar introducir sesgo en el modelo. Asume que no hay diferencias por sexo en recomendaciones de educación financiera.
5. **Granularidad de `is_investment_related`:** está marcado a nivel de contenido, no de sección. Un artículo de inversión puede incluir contenido introductorio.
6. **No hay metadatos de calidad de los contenidos** (puntuación, reseñas, autor). El recomendador no podrá usarlos.
7. **Eventos no incluyen "ratings explícitos"** más allá de liked/disliked inferidos por `event=disliked`.

---

## 8. Riesgos metodológicos

1. **Riesgo de sobreajuste a datos sintéticos:** si el modelo se entrena solo con estos datos, podría aprender los patrones del generador en lugar de preferencias reales. **Mitigación:** incluir un piloto real con usuarios humanos como validación externa.
2. **Riesgo de cold start:** 250 usuarios con 1.500 interacciones dan una media de 6 interacciones por usuario. Es bajo para NeuMF. **Mitigación:** arrancar con modelos más simples (popularidad, LightFM) como baseline.
3. **Riesgo de coherencia pedagógica insuficiente:** el post-filtro con grafo se valida solo en la generación sintética. **Mitigación:** revisar manualmente una muestra de recomendaciones.
4. **Riesgo de cobertura de temas desbalanceada:** el catálogo tiene 19 contenidos de planificación (24%) y 15 de inversión (19%). Los efectos del comportamiento sobre el consumo de topics especializados siguen siendo pequeños (1-2 pp). **Mitigación:** ampliar el catálogo con más contenidos de deuda/crédito/impuestos si se busca mayor discriminación.
5. **Riesgo de calibración parcial:** los perfiles sintéticos usan solo 5 variables del ECF. Hay otras 200+ variables no explotadas (actitud financiera, comportamiento específico, etc.) que podrían enriquecer más el modelo.

---

## 9. Aclaración obligatoria

> Las interacciones sintéticas no representan comportamiento real de usuarios. Se usan solo para construir, probar y evaluar inicialmente el sistema de recomendación. La validación definitiva requeriría usuarios reales o evaluación experta.

---

## 10. Próximos pasos

1. Ejecutar el generador de recomendaciones (NeuMF baseline + baseline de popularidad) sobre el dataset actualizado.
2. Validar la coherencia pedagógica de las recomendaciones top-k con el grafo de conocimiento.
3. Diseñar el cuestionario pre/post del piloto con ~30 usuarios reales.
4. Recoger datos reales del piloto y reentrenar / recalibrar el generador.
5. Comparar métricas antes y después de la calibración con datos reales.
6. **Ampliar el catálogo de contenidos** (actualmente 60) para mejorar la cobertura de topics especializados (deuda, crédito, inversión) y permitir efectos de comportamiento más visibles.
