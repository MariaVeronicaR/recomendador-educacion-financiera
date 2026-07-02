# Resumen para la junta con el tutor

## ¿Qué tenemos?

7 archivos en `/data/`. Cifras redondas para llevarlas a la cabeza:

| Archivo                        | Qué es                                     | Cantidad |
| ------------------------------ | ------------------------------------------- | -------- |
| `sources.csv`                | Fuentes oficiales registradas (con URL)     | 8        |
| `contents.csv`               | Contenidos reales con URL verificable       | 60       |
| `concepts.csv`               | Taxonomía de conceptos financieros         | 30       |
| `prerequisites.csv`          | Relaciones de prerrequisito entre conceptos | 33       |
| `users_synthetic.csv`        | Usuarios sintéticos                        | 250      |
| `interactions_synthetic.csv` | Interacciones sintéticas                   | 1.500    |
| `validation_summary.md`      | Validaciones y limitaciones                 | —       |

- **100% de los contenidos tienen URL https oficial** (BdE, CNMV, OECD).
- **1 piloto real previsto** con ~30 usuarios para validación externa (no incluido aún en el dataset).

## ¿Cómo obtuvimos los datos?

**Parte real (contenidos, conceptos, marco institucional):**

1. Identificadas 8 fuentes oficiales: Finanzas para Todos (CNMV+BdE), Guías CNMV, Portal Cliente Bancario (BdE), Plan Ed. Financiera 2022-2025, OECD/INFE, PISA 2022, OECD/INFE 2020 Survey, Encuesta BdE/CNMV 2021.
2. Verificadas con `WebFetch` antes de incluirlas.
3. 60 contenidos extraídos de esas fuentes y etiquetados a mano (tema, dificultad, prerrequisitos, riesgo, si es de inversión).
4. Taxonomía de 30 conceptos inspirada en PISA Financial Literacy + Encuesta BdE.
5. 33 relaciones de prerrequisito (las 14 mínimas del plan + 19 adicionales para enriquecer el grafo).

**Parte sintética (usuarios e interacciones):**

- **Usuarios (250):** distribución calibrada con la Encuesta BdE/CNMV 2021 (76% suspende → 41.6% conocimiento bajo, 43.6% medio, 14.8% alto). Coherencia entre variables (no se permite knowledge=alto + saving_habit=nunca).
- **Interacciones (1.500):** generadas con un modelo sigmoid sobre el gap conocimiento-dificultad que aplica las 6 reglas del plan. Distribución final: 64.7% básicas, 28.5% intermedias, 6.8% avanzadas.

## Honestidad ante el tribunal

- No inventamos URLs. Todo es verificable.
- Las interacciones sintéticas **no** demuestran efectividad real; validan la viabilidad técnica.
- La encuesta OECD/INFE 2023 fue cancelada; usamos la de 2020.
- El dataset es **defendible como prototipo**, no como sistema listo para producción.

---

## Preguntas

(Ordenadas por prioridad. Las 5 primeras son las que más urge aclarar.)

### 1. Sobre la validez del piloto real

- Con solo ~30 usuarios en el piloto, ¿es defendible entrenarlo por separado y compararlo con el modelo entrenado con sintéticos, o conviene que el piloto se use solo como evaluación subjetiva?
- ¿Qué tamaño muestral mínimo considerarías aceptable para hablar de "validación con usuarios reales" en un TFM?

### 2. Sobre la arquitectura del modelo

- Con 1.500 interacciones y 250 usuarios, ¿NeuMF va a funcionar o deberíamos arrancar con un baseline más simple (popularidad + filtrado por contenido con TF-IDF + LightFM)?
- ¿Tiene sentido defender un modelo "más simple" como contribución en sí mismo, dado lo ajustado del dataset?

### 3. Sobre el grafo de conocimiento

- ¿Es razonable tener 30 conceptos y 33 prerrequisitos como un grafo útil, o se queda corto para que el post-filtro pedagógico marque diferencias?
- ¿Debería el grafo ser jerárquico (tema → subtema → concepto) o plano como está ahora?

### 4. Sobre las fuentes

- ¿La Encuesta BdE/CNMV 2021 basta como anclaje para los perfiles sintéticos, o necesito también la Encuesta de Condiciones de Vida (ECV) del INE?
- ¿La OECD/INFE 2020 es una fuente aceptable o hay alguna otra más reciente que deba citar?

### 6. Sobre riesgos

- ¿Cómo de crítico es el riesgo de que el modelo aprenda los patrones del generador sintético en vez de preferencias reales? ¿Cómo lo presentarías en la memoria?
