# Informe de cobertura de conceptos

**Fecha:** 2026-08-21
**Catálogo:** 87 contenidos
**Matriz:** `content_concept_map.csv`

## Criterio

La cobertura se calcula únicamente con la matriz explícita `content_concept_map.csv`. El campo `contents.csv:prerequisites` no se cuenta como contenido enseñado: expresa dependencias pedagógicas.

- `directa`: el contenido enseña explícitamente el concepto según título, objetivo y evidencia anotada.
- La matriz actual es una primera auditoría; las relaciones inferidas por topic deben revisarse manualmente antes de presentar el resultado como definitivo.

## Resultado

| Estado | Conceptos |
|---|---:|
| Al menos 2 contenidos directos | 24 |
| Exactamente 1 contenido directo | 4 |
| Sin contenido directo | 2 |

## Conceptos con dos o más contenidos directos

C01, C02, C03, C04, C05, C06, C08, C09, C10, C11, C12, C13, C14, C15, C19, C21, C22, C23, C24, C26, C27, C28, C29 y C30 según la matriz actual.

## Conceptos con un contenido directo

- C07 — Inflación: C079.
- C16 — Planificación financiera: C081.
- C18 — Comisiones bancarias: C082.
- C25 — Volatilidad: C083.
- C30 — Finanzas sostenibles: C055/C087 aparecen como dos relaciones en la matriz actual; requieren revisión semántica porque ambas usan material CNMV que puede solaparse.

> La cifra anterior debe recalcularse automáticamente tras la revisión manual de la matriz; este informe no sustituye al validador.

## Conceptos sin contenido directo específico

- C17 — Tipo de cambio.
- C20 — Producto Interior Bruto (PIB).

No se añadieron contenidos inventados para estos conceptos. Los recursos consultados no permitieron verificar una página oficial suficientemente específica y pedagógica que los cubra de forma defendible. Hay que decidir si se incorporan mediante nuevas fuentes oficiales verificadas o si se eliminan del alcance del MVP.

## Contenidos añadidos en esta iteración

| ID | Concepto principal | Fuente |
|---|---|---|
| C079 | Inflación | OECD/INFE Toolkit 2026 |
| C080 | Interés compuesto | OECD/INFE Toolkit 2026 |
| C081 | Planificación financiera | Finanzas para Todos |
| C082 | Comisiones bancarias | Portal Cliente Bancario BdE |
| C083 | Volatilidad/riesgo | CNMV, Competencias básicas para inversores |
| C084 | Seguros | Finanzas para Todos |
| C085 | Impuestos/fiscalidad | CNMV, Fiscalidad de fondos de inversión en IRPF |
| C086 | Criptoactivos | OECD/INFE Toolkit 2026 |
| C087 | Finanzas sostenibles/ESG | CNMV, Competencias básicas para inversores |

## Limitaciones y acciones pendientes

1. Revisar manualmente cada relación inferida por topic y cambiarla a `directa`, eliminarla o marcarla como `contextual`.
2. Buscar fuentes específicas y verificables para C17 y C20 antes de añadir contenidos.
3. Añadir una segunda fuente claramente diferenciada para C07, C16, C18 y C25 si se mantiene el criterio de dos contenidos por concepto.
4. Corregir los prerrequisitos autorreferentes o demasiado fuertes (por ejemplo, contenidos introductorios que exigen el concepto que introducen).
5. Actualizar los generadores para leer la matriz, no solo `TOPIC_TO_CONCEPTS`.
6. Regenerar las interacciones solo después de cerrar la matriz y el catálogo.
