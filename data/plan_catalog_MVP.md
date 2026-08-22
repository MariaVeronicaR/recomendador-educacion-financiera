# Plan: completar y sanear el catálogo educativo

## Contexto

Se eligió la opción completa: que los 30 conceptos financieros tengan cobertura suficiente, idealmente al menos dos contenidos por concepto, y que el catálogo siga siendo útil para el MVP. La auditoría ha detectado que la cobertura calculada hasta ahora no es completamente fiable: `concepts.csv` tenía filas con comas sin entrecomillar; `contents.csv` usa `prerequisites` tanto para prerrequisitos como, implícitamente, para inferir cobertura; varias URLs son landings genéricas o no corresponden al título; y los generadores de interacciones no leen el grafo declarado.

Por tanto, no se deben añadir contenidos a ciegas. El resultado debe distinguir entre contenido que **enseña directamente** un concepto y contenido que solo lo usa como prerrequisito o lo menciona de forma contextual. Se conservarán los datos actuales y los scripts de generación, pero se evitará ejecutar `regenerate_contents.py` después de la expansión porque ese script sobrescribe el catálogo ampliado.

## Objetivo

Entregar un catálogo validado que:

- tenga un CSV correcto y estable;
- mantenga los 78 contenidos actuales salvo correcciones justificadas;
- añada contenidos nuevos con IDs estables desde `C079` en adelante;
- cubra los 30 conceptos directamente, con al menos dos contenidos por concepto cuando existan fuentes oficiales adecuadas;
- marque honestamente los conceptos que no tengan dos fuentes/contenidos adecuados;
- use URLs oficiales y suficientemente específicas;
- mantenga sincronizados contenidos, conceptos, prerrequisitos, generador y validación;
- regenere las interacciones sobre el catálogo final y documente su cobertura real.

## Fases de implementación

### 1. Crear una copia/versionado del estado actual

Antes de modificar el catálogo, conservar los artefactos actuales:

- `data/contents.csv` (78 filas);
- `data/concepts.csv` ya corregido;
- `data/interactions_synthetic.csv` y `data/interactions_synthetic_realistic.csv`;
- `data/expand_contents.py` y `data/generate_interactions_realistic.py`.

No ejecutar `data/regenerate_contents.py` sobre el catálogo ampliado, porque reconstruye únicamente `C001`–`C060` y elimina `C061`–`C078`. Si se mantiene ese script, documentar que es un generador histórico de la base inicial o adaptarlo posteriormente para que no sobrescriba sin confirmación.

### 2. Reparar y validar el esquema CSV

- Confirmar que `concepts.csv` tiene exactamente cinco columnas por fila y que las descripciones con puntuación no rompen el CSV.
- Mantener el contenido semántico original de las descripciones, incluyendo “gestionar ingresos, pagos y ahorro” en `C08`; usar `csv.writer`/`csv.DictWriter` con quoting correcto en vez de reemplazar información.
- Validar `contents.csv` con exactamente 13 columnas por fila y vocabularios permitidos para `difficulty`, `risk_level` e `is_investment_related`.
- Validar IDs uniques, referencias a conceptos existentes y ausencia de prerrequisitos autorreferentes o ciclos.
- No usar `fix_contents.py` como validador: su comportamiento de truncar/reunir columnas puede ocultar corrupción.

### 3. Definir una matriz explícita de cobertura

Crear una matriz auditable (preferiblemente `data/content_concept_map.csv`) con al menos:

```text
content_id,concept_id,coverage_type,evidence_note
```

`coverage_type` tendrá valores controlados, por ejemplo:

- `directa`: el contenido enseña el concepto;
- `prerequisito`: el concepto se exige antes, pero no se enseña;
- `contextual`: se menciona sin enseñanza suficiente.

Usar esta matriz para calcular cobertura, no contar simplemente cada ID que aparece en `contents.prerequisites`. Revisar especialmente:

- `C049`, que no debe exigir como prerrequisito el interés compuesto que pretende introducir;
- `C055`, que no debe exigir `C30` si es el contenido introductorio de finanzas sostenibles;
- `C004`, que no debe exigir `C12` a una guía que introduce inversión básica;
- `C050`, `C051` y otros registros cuya URL no corresponde claramente al título.

Aprovechar como cobertura potencial, pero verificar el texto y ajustar objetivo/prerrequisitos: contenidos sobre crédito/préstamos, jubilación (`C005`, `C010`), activos (`C039`, `C040`, `C056`), educación financiera (`C043`–`C045`) y criptoactivos (`C056`).

### 4. Completar los huecos con contenidos oficiales específicos

Añadir nuevos IDs únicamente desde `C079` y registrar cada URL antes de incorporarla. Prioridad:

1. **Sin cobertura directa y críticos:** crédito (`C04`), inflación (`C07`), criptomonedas (`C27`), activos financieros (`C24`), educación financiera (`C28`).
2. **Sin cobertura directa pero secundarios:** tipo de cambio (`C17`) y PIB (`C20`). Si no se encuentra material educativo oficial adecuado, no fabricar una cobertura artificial: documentar el concepto como fuera de alcance o retirarlo del MVP.
3. **Cobertura mínima:** interés compuesto (`C06`), seguros (`C22`), plan de pensiones (`C23`) y finanzas sostenibles (`C30`), añadiendo un segundo contenido directo cuando exista una fuente oficial distinta o un recurso suficientemente distinto.

Para cada nuevo contenido comprobar manualmente:

- que el título y el objetivo coinciden con la página/PDF;
- que la URL devuelve el documento o página concreta, no solo una landing genérica;
- que la fuente puede mapearse a una fuente de `sources.csv` mediante un identificador estable;
- que la dificultad y los prerrequisitos son pedagógicamente coherentes;
- que el campo de inversión y el nivel de riesgo son correctos.

No reutilizar una misma guía como varios contenidos con títulos distintos salvo que se divida en unidades claramente identificables y se documente esa decisión.

### 5. Normalizar fuentes y URLs

- Mantener un mapeo estable entre `contents.source` y `sources.csv` (preferiblemente añadir `source_id` al catálogo o un archivo de correspondencia), porque los nombres libres actuales no siempre coinciden con `S1`–`S8`.
- Marcar URLs repetidas como recursos derivados de la misma página y revisar si realmente constituyen contenidos distintos.
- Sustituir o marcar como “landing institucional” las entradas CNMV que no apuntan a una guía concreta.
- Corregir URLs que no corresponden al tema del título; no conservarlas solo porque devuelvan HTTP 200.

### 6. Sincronizar el grafo y los generadores

Modificar `generate_interactions_realistic.py` y, si se mantiene activo, `generate_interactions.py` para que:

- carguen la matriz de cobertura y/o `contents.prerequisites` en vez de depender únicamente de `TOPIC_TO_CONCEPTS` hardcoded;
- incluyan rutas para inflación (`C07`), crédito (`C04`), mercado/tipo de cambio (`C17`) y contexto/PIB (`C20`), o dejen explícito que esos conceptos están fuera del alcance;
- actualicen conceptos aprendidos según el contenido realmente completado y su mapeo, no según todos los conceptos del topic;
- no hagan inalcanzable la inversión no básica por exigir `C07` cuando no existe una ruta de inflación;
- escriban de forma inequívoca el archivo principal y el archivo histórico, evitando validar un artefacto distinto del generado.

La estrategia de post-filtro debe seguir siendo la del grafo pedagógico, pero debe usar una única fuente de verdad y no tres copias divergentes.

### 7. Regenerar y validar interacciones

Después de completar y corregir el catálogo:

- regenerar `interactions_synthetic_realistic.csv` desde `ECF-archivos`;
- copiarlo al archivo principal solo después de verificarlo;
- conservar la versión sigmoid como histórico independiente;
- comprobar cobertura real de contenidos, usuarios únicos y mínimo de interacciones;
- no afirmar que todos los contenidos aparecen ni que cada usuario tiene cuatro interacciones si no se verifica realmente;
- revisar específicamente que existan rutas para aprender inflación y que después sea posible recomendar inversión intermedia/avanzada a usuarios elegibles.

### 8. Ampliar la validación

Actualizar `validate.py` o añadir un validador específico que compruebe:

- estructura y encoding de todos los CSV;
- IDs duplicados y referencias rotas;
- vocabularios y rangos;
- cobertura directa por concepto y cobertura mínima;
- contenidos sin URL o con URL duplicada/no específica;
- contenidos de inversión sin prerrequisitos;
- prerrequisitos autorreferentes/cíclicos;
- consistencia entre la matriz, `prerequisites.csv`, contenidos y generadores;
- cobertura de interacciones y distribución real por dificultad/evento.

El validador debe producir un informe reproducible con fecha y cifras calculadas directamente de los archivos, no valores escritos manualmente.

### 9. Actualizar documentación del TFM

Actualizar después de pasar todas las validaciones:

- `data/validation_summary.md`;
- `data/resumen_actual.md`;
- `data/correcciones_pdf.md`;
- el capítulo de metodología/requisitos de datos del PDF del TFM.

La documentación debe explicar que la cobertura se midió con una matriz explícita y distinguir contenido real de interacciones sintéticas. Si PIB o tipo de cambio quedan fuera por falta de contenidos oficiales adecuados, declararlo como decisión de alcance, no ocultarlo.

## Verificación final

Ejecutar en este orden:

1. Validador de estructura CSV y matriz de cobertura.
2. Verificador de URLs oficiales.
3. Validador de prerrequisitos y referencias.
4. Regenerador de interacciones realistas desde el ECF.
5. Validador de interacciones y cobertura.
6. Revisión manual de una muestra de contenidos nuevos y recomendaciones top-k.
7. Actualización de los documentos de validación y notas del PDF.

Criterio de éxito: 30 conceptos correctamente clasificados por cobertura directa/prerrequisito/contextual; al menos dos contenidos directos para cada concepto incluido en el alcance del MVP; ningún concepto declarado como cubierto sin evidencia; URLs trazables; y generador/validador sincronizados.
