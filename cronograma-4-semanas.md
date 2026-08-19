# Cronograma de trabajo: 4 semanas

## Semana 1 — Cierre y depuración del dataset

### Objetivos

- Corregir la estructura de los archivos CSV.
- Revisar las fuentes, URLs y contenidos.
- Resolver las discrepancias entre el plan de datos, los CSV y el resumen de validación.
- Unificar conceptos, prerrequisitos y metadatos de contenidos.
- Garantizar que el dataset sea reproducible y trazable.

### Entregables

- `data/sources.csv` corregido y validado.
- Esquema común revisado para todos los archivos CSV.
- Catálogo de contenidos revisado, con temas, URLs y fuentes verificadas.
- Taxonomía de conceptos y relaciones de prerrequisito unificadas.
- Script de validación actualizado.
- `data/validation_summary.md` regenerado con las cifras reales.
- Informe breve de decisiones metodológicas y limitaciones del dataset.

### Hito de control

Dataset coherente, trazable y reproducible.

---

## Semana 2 — Implementación del sistema de recomendación

### Objetivos

- Construir los primeros modelos de recomendación.
- Integrar las reglas de nivel, progreso y prerrequisitos.
- Impedir recomendaciones pedagógicamente inadecuadas.
- Preparar una interfaz común para comparar modelos.

### Entregables

- Baseline de popularidad implementado.
- Recomendador basado en contenido implementado.
- Módulo de filtrado por nivel de conocimiento y dificultad.
- Módulo de comprobación de prerrequisitos.
- Filtro específico para contenidos de inversión.
- Interfaz común para generar recomendaciones.
- Ejemplos reproducibles para distintos perfiles de usuario.
- Documento breve de arquitectura del sistema.

### Hito de control

Sistema funcional capaz de generar recomendaciones reproducibles respetando las restricciones pedagógicas.

---

## Semana 3 — Evaluación experimental

### Objetivos

- Definir el protocolo experimental.
- Ejecutar los modelos sobre una partición reproducible de los datos.
- Comparar los modelos mediante métricas cuantitativas.
- Analizar errores, sesgos y casos límite.

### Entregables

- División reproducible de los datos en entrenamiento, validación y prueba.
- Script de evaluación automática.
- Resultados de `precision@k` y `recall@k`.
- Resultados de cobertura y diversidad.
- Métricas de cumplimiento de prerrequisitos.
- Métricas de adecuación entre usuario y dificultad del contenido.
- Métricas de exposición indebida a contenidos avanzados o de inversión.
- Tabla comparativa entre el baseline y el recomendador basado en contenido.
- Informe de errores y casos límite.

### Hito de control

Resultados cuantitativos reproducibles y comparables entre los modelos implementados.

---

## Semana 4 — Validación final y memoria

### Objetivos

- Validar la calidad de las recomendaciones.
- Redactar y cerrar la memoria del TFM.
- Documentar las limitaciones y el trabajo futuro.
- Preparar la entrega y la defensa.

### Entregables

- Revisión experta de una muestra de recomendaciones.
- Evaluación preliminar con usuarios reales, si es viable, o cuestionario de valoración.
- Tablas y gráficos definitivos.
- Capítulos de metodología, arquitectura, experimentos y resultados redactados.
- Sección de limitaciones y trabajo futuro.
- Conclusiones alineadas con los objetivos iniciales.
- Anexo con instrucciones de reproducción.
- Repositorio limpio y ejecución completa desde cero.
- Presentación final.
- Documento con posibles preguntas y respuestas del tribunal.

### Hito de control

Sistema, resultados, memoria y defensa preparados para la entrega final.

---

## Hitos generales

| Momento              | Resultado esperado                                               |
| -------------------- | ---------------------------------------------------------------- |
| Final de la semana 1 | Dataset coherente, trazable y reproducible.                      |
| Final de la semana 2 | Sistema de recomendación funcional con reglas pedagógicas.     |
| Final de la semana 3 | Evaluación cuantitativa reproducible y comparación de modelos. |
| Final de la semana 4 | Memoria, sistema y defensa listos para la entrega.               |
|                      |                                                                  |

## Resultado final esperado

Un recomendador educativo funcional, evaluado mediante métricas reproducibles, con sus limitaciones claramente documentadas y una memoria defendible desde el punto de vista académico y metodológico.
