# Plan de Evaluación Experimental de Modelos de IA (Recomendador TFM)

**Fecha:** 2026-08-23  
**TFM:** Plataforma inteligente para la recomendación personalizada de contenidos en educación financiera basada en IA  
**Público Objetivo:** Jóvenes profesionales españoles (18-34 años / 22-30 años)  

---

## 1. Contexto y Objetivos

Este plan define la metodología experimental para comparar y evaluar científicamente diferentes arquitecturas de sistemas de recomendación (RecSys) sobre el catálogo de educación financiera del piloto del TFM. El objetivo es determinar de forma empírica qué modelo proporciona el mejor balance entre exactitud de recomendación, cobertura del catálogo y seguridad pedagógica, antes de su integración final en la plataforma web interactiva.

El piloto cuenta con:
*   **250 usuarios reales** muestreados individualmente de la Encuesta de Competencias Financieras (ECF 2021) del Banco de España.
*   **99 contenidos educativos reales** con URLs oficiales y operacionales de la CNMV y el Banco de España.
*   **1.500 interacciones realistas** moduladas por el comportamiento de los usuarios en la ECF.

---

## 2. Modelos a Comparar

Para garantizar el rigor metodológico exigido por el tribunal, se evaluarán cuatro modelos diferentes:

1.  **Popularidad (PopRec) - Baseline 1:**  
    *   *Funcionamiento:* Recomienda los contenidos con mayor número de interacciones en el dataset, excluyendo los ya vistos por el usuario.
    *   *Propósito:* Sirve como benchmark base de control.
2.  **Filtrado Basado en Contenido (TF-IDF + Cosine Similarity) - Baseline 2:**  
    *   *Funcionamiento:* Representa los contenidos mediante vectores TF-IDF calculados sobre los resúmenes y objetivos de aprendizaje en `contents.csv`. Mide la similitud del coseno respecto al histórico del usuario.
    *   *Propósito:* Evalúa la calidad de la recomendación basada puramente en texto y metadatos.
3.  **Factorización de Matrices Híbrida (SVD + Ridge Regression) - Modelo A:**  
    *   *Funcionamiento:* Extrae 10 factores latentes de la matriz de interacciones mediante Descomposición en Valores Singulares (`TruncatedSVD`). Combina estos factores con las características demográficas de la ECF (`sex`, `education_level`, `employment_status`, `financial_knowledge_level`, `saving_habit`) usando regresión Ridge.
    *   *Propósito:* Combina comportamiento colaborativo y metadatos de usuario (híbrido).
4.  **Neural Collaborative Filtering (NeuMF / MLP) - Modelo B:**  
    *   *Funcionamiento:* Implementa una red neuronal de factorización matricial profunda (Multi-Layer Perceptron) en PyTorch o scikit-learn (`MLPRegressor`).
    *   *Propósito:* Representa el enfoque no lineal profundo propuesto en el borrador original del TFM.

---

## 3. Métricas de Evaluación

La evaluación medirá el rendimiento de los modelos en tres dimensiones:

### A. Métricas de Exactitud (Relevance)
Miden la precisión matemática de las sugerencias basándose en el histórico de prueba:
*   **Precision@K:** Proporción de recomendaciones útiles en el Top-K de sugerencias.
*   **Recall@K:** Proporción de contenidos de interés recomendados respecto al total de contenidos útiles disponibles para el usuario.
*   **NDCG@K (Normalized Discounted Cumulative Gain):** Mide la calidad del ordenamiento de las recomendaciones (los contenidos más relevantes deben aparecer primero).

### B. Métricas de Calidad de Catálogo (Beyond-Accuracy)
Evitan que el recomendador cometa sesgos de popularidad o sobreespecialización:
*   **Catalog Coverage:** Porcentaje de contenidos del catálogo total (99) que el sistema es capaz de recomendar al menos una vez al conjunto de usuarios.
*   **Intra-List Diversity (ILD):** Medida de la variedad de temas (topics) dentro de la lista de recomendación del usuario para evitar burbujas de filtro.

### C. Métricas de Seguridad Pedagógica (Específicas del Grafo)
Miden la adherencia del sistema al diseño de aprendizaje secuencial:
*   **Prerequisite Violation Rate (PVR) [Pre-Filtro]:** Porcentaje de contenidos recomendados por el recomendador de IA que intentaron violar las reglas de prerrequisitos del grafo (ej: recomendar inversión a un usuario que no domina interés compuesto o inflación).
*   **Prerequisite Violation Rate (PVR) [Post-Filtro]:** Debe ser del **0%** en todos los modelos tras aplicar la capa de seguridad del grafo pedagógico.

---

## 4. Coherencia con el PDF del TFM

*   **NDCG@K y Precision@K:** El PDF original propone estas dos métricas en el Capítulo 1.2.3 y el Capítulo 2.6. El plan es **100% coherente** y da soporte matemático directo a esa declaración.
*   **Coherencia Pedagógica:** El PDF habla cualitativamente de garantizar una "progresión didáctica coherente". Al introducir la métrica cuantitativa **Prerequisite Violation Rate (PVR)**, transformamos un objetivo subjetivo en una métrica matemática auditable por el tribunal.
*   **Catalog Coverage y Diversidad (Novedad):** Estas métricas no se mencionan en el borrador del PDF. Añadirlas enriquece la sección de resultados (Capítulo 4) y demuestra el conocimiento del alumno sobre las limitaciones de los recomendadores clásicos frente a datos dispersos.

---

## 5. Estructura de la Tabla de Resultados (para el Capítulo 4)

El experimento generará una tabla con la siguiente estructura para comparar el rendimiento de los cuatro modelos:

| Modelo | Precision@5 | NDCG@5 | Catalog Coverage | Prereq. Violations (Pre-Filtro) | Prereq. Violations (Post-Filtro) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Popularidad (PopRec)** | *Calculado* | *Calculado* | *Calculado* | *Calculado* | 0% (Forzado) |
| **TF-IDF + Cosine** | *Calculado* | *Calculado* | *Calculado* | *Calculado* | 0% (Forzado) |
| **Híbrido SVD + Ridge** | *Calculado* | *Calculado* | *Calculado* | *Calculado* | 0% (Forzado) |
| **NeuMF (Red Neuronal)** | *Calculado* | *Calculado* | *Calculado* | *Calculado* | 0% (Forzado) |

---

## 6. Próximos Pasos de Ejecución

1.  **Crear el script de evaluación:** Escribir `/src/utils/evaluate_models.py` para entrenar los cuatro modelos sobre `interactions_synthetic.csv` y calcular la tabla de métricas.
2.  **Calibración y regularización:** Ajustar hiperparámetros (alpha en Ridge, número de componentes en SVD y capas/regularización en NeuMF) para optimizar el rendimiento del piloto.
3.  **Generación de conclusiones:** Analizar la tabla de resultados para justificar técnicamente en la memoria del TFM la elección del modelo final integrado en el prototipo Streamlit.
