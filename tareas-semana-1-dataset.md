# Tareas necesarias para una base de datos de calidad

## Semana 1 — Preparación, limpieza y validación del dataset

**Objetivo de la semana:** disponer de un dataset limpio, coherente, trazable, reproducible y documentado antes de implementar el sistema de recomendación.

---

## 1. Definir el contrato de datos

- [ ] Confirmar la finalidad de cada archivo del directorio `data/`.
- [ ] Documentar las columnas obligatorias de cada CSV.
- [ ] Documentar el tipo de dato esperado de cada columna.
- [ ] Documentar los valores permitidos para dificultad, riesgo, eventos y niveles de usuario.
- [ ] Confirmar los identificadores únicos de fuentes, contenidos, conceptos, usuarios e interacciones.
- [ ] Confirmar los mínimos del dataset: fuentes, contenidos, conceptos, usuarios e interacciones.
- [ ] Definir qué campos pueden quedar vacíos y cuáles son obligatorios.
- [ ] Establecer un vocabulario común para temas y subtemas.

**Criterio de finalización:** existe un esquema documentado y todos los archivos pueden validarse contra él.

---

## 2. Corregir la estructura de los archivos CSV

- [ ] Corregir `data/sources.csv` para que todas las filas tengan exactamente 8 columnas.
- [ ] Corregir `data/concepts.csv` para que todas las filas tengan exactamente 5 columnas.
- [ ] Confirmar que `data/contents.csv` tiene exactamente 13 columnas por fila.
- [ ] Confirmar que `data/prerequisites.csv` tiene exactamente 3 columnas por fila.
- [ ] Confirmar que `data/users_synthetic.csv` tiene exactamente 11 columnas por fila.
- [ ] Confirmar que `data/interactions_synthetic.csv` tiene exactamente 8 columnas por fila.
- [ ] Escapar correctamente las comas, comillas y caracteres especiales mediante un escritor CSV.
- [ ] Confirmar que todos los archivos usan UTF-8.
- [ ] Eliminar filas vacías, columnas sobrantes y cabeceras duplicadas.
- [ ] Detectar y corregir IDs duplicados.

**Criterio de finalización:** todos los CSV se abren correctamente con `csv.DictReader` sin columnas adicionales ni desplazamientos.

---

## 3. Revisar y normalizar las fuentes

- [ ] Confirmar que existen las fuentes `S1` a `S8`.
- [ ] Verificar que cada fuente tiene nombre, organización, URL, tipo, uso, fiabilidad y fecha de consulta.
- [ ] Comprobar que las URLs de las fuentes utilizan `https://`.
- [ ] Revisar que no existan URLs inventadas o incompletas.
- [ ] Normalizar la forma de referenciar las fuentes desde `contents.csv`.
- [ ] Preferir `source_id` como referencia estable entre archivos.
- [ ] Crear una correspondencia única entre cada contenido y su fuente.
- [ ] Revisar que la fuente declarada coincide con la organización que publica la URL.
- [ ] Registrar por separado las URLs que requieren revisión manual.
- [ ] Documentar la fecha y el método de verificación de las fuentes.

**Criterio de finalización:** cada contenido tiene una fuente identificable y trazable hasta una URL institucional.

---

## 4. Auditar el catálogo de contenidos

- [ ] Confirmar que hay al menos 50 contenidos reales.
- [ ] Revisar cada título, resumen y objetivo de aprendizaje.
- [ ] Confirmar que el contenido descrito coincide con la URL.
- [ ] Revisar que cada contenido tiene una URL específica o justificar si utiliza una página general.
- [ ] Identificar y corregir URLs claramente incongruentes con el título.
- [ ] Confirmar que cada contenido tiene una dificultad válida: `básico`, `intermedio` o `avanzado`.
- [ ] Confirmar que cada contenido tiene un nivel de riesgo pedagógico válido.
- [ ] Confirmar que los contenidos de inversión están marcados correctamente.
- [ ] Confirmar que los contenidos de inversión tienen prerrequisitos explícitos.
- [ ] Confirmar que no se ofrecen productos financieros concretos ni asesoramiento personalizado.
- [ ] Revisar que los contenidos repetidos o casi duplicados estén justificados.
- [ ] Revisar la distribución de contenidos por dificultad.
- [ ] Revisar la distribución de contenidos por tema.

**Criterio de finalización:** cada contenido es interpretable, trazable y adecuado para un contexto educativo.

---

## 5. Completar y normalizar la taxonomía de conceptos

- [ ] Confirmar que están incluidos los conceptos mínimos del plan de datos.
- [ ] Normalizar nombres como `interés simple` e `interés compuesto`.
- [ ] Diferenciar conceptos de temas generales.
- [ ] Confirmar que cada concepto tiene descripción, tema y dificultad.
- [ ] Revisar conceptos auxiliares como TAE, volatilidad, activos, seguros y protección de datos.
- [ ] Identificar conceptos que no tienen ningún contenido asociado.
- [ ] Decidir si esos conceptos son prerrequisitos, conceptos de apoyo o contenidos pendientes.
- [ ] Crear una matriz de cobertura concepto-contenido.
- [ ] Evitar conceptos duplicados o con nombres equivalentes sin explicación.
- [ ] Documentar los conceptos que se mantienen aunque todavía no tengan contenido directo.

**Criterio de finalización:** la taxonomía es coherente y se entiende qué papel cumple cada concepto.

---

## 6. Revisar el grafo de prerrequisitos

- [ ] Confirmar que cada relación utiliza IDs existentes en `concepts.csv`.
- [ ] Eliminar relaciones duplicadas.
- [ ] Detectar autorrelaciones.
- [ ] Detectar ciclos en el grafo.
- [ ] Confirmar las relaciones mínimas exigidas por el plan.
- [ ] Revisar que inversión requiere las bases definidas.
- [ ] Revisar que tarjetas, préstamos, hipotecas, diversificación y planificación tienen prerrequisitos coherentes.
- [ ] Confirmar que los prerrequisitos declarados en `contents.csv` también existen en la taxonomía.
- [ ] Evitar contradicciones entre `prerequisites.csv`, `contents.csv` y el generador de interacciones.
- [ ] Definir una única fuente de verdad para las relaciones.

**Criterio de finalización:** el grafo es válido, acíclico y está conectado con los contenidos.

---

## 7. Revisar los perfiles de usuarios sintéticos

- [ ] Confirmar que existen al menos 200 usuarios.
- [ ] Confirmar que los `user_id` son únicos.
- [ ] Validar los valores permitidos de edad, educación y empleo.
- [ ] Validar los niveles de conocimiento, comportamiento y actitud financiera.
- [ ] Revisar la coherencia entre conocimiento, hábito de ahorro y experiencia inversora.
- [ ] Revisar la distribución de usuarios por nivel de conocimiento.
- [ ] Documentar que los usuarios son sintéticos.
- [ ] Documentar las fuentes utilizadas para calibrar sus distribuciones.
- [ ] Revisar posibles sesgos introducidos por la generación sintética.
- [ ] Confirmar que ningún perfil se interpreta como una persona real identificable.

**Criterio de finalización:** los perfiles son válidos para pruebas iniciales y sus limitaciones están documentadas.

---

## 8. Revisar las interacciones sintéticas

- [ ] Confirmar que existen al menos 1.000 interacciones.
- [ ] Confirmar que los `interaction_id` son únicos.
- [ ] Confirmar que cada interacción referencia a un usuario existente.
- [ ] Confirmar que cada interacción referencia a un contenido existente.
- [ ] Validar los eventos permitidos: `viewed`, `completed`, `liked`, `disliked`, `quiz_passed` y `quiz_failed`.
- [ ] Validar que `score`, `completion_rate` y `quiz_score` están entre 0 y 1.
- [ ] Permitir `quiz_score` vacío solo cuando esté documentado.
- [ ] Validar el formato ISO de los `timestamp`.
- [ ] Confirmar que todos los contenidos aparecen al menos una vez.
- [ ] Confirmar que todos los usuarios tienen la cobertura mínima definida.
- [ ] Revisar la distribución de interacciones por dificultad y tema.
- [ ] Revisar si existen usuarios o contenidos sin interacciones.
- [ ] Confirmar que la generación es determinista con una semilla fija.

**Criterio de finalización:** las interacciones son válidas, reproducibles y cubren el universo definido para las pruebas iniciales.

---

## 9. Validar las reglas pedagógicas

- [ ] Confirmar que los usuarios de nivel bajo reciben principalmente contenidos básicos.
- [ ] Medir la proporción de contenidos avanzados mostrados a usuarios de nivel bajo.
- [ ] Confirmar que los usuarios principiantes no reciben inversión avanzada sin preparación.
- [ ] Confirmar que los contenidos de inversión aparecen después de sus conceptos base.
- [ ] Confirmar que los prerrequisitos aparecen antes que el contenido dependiente.
- [ ] Medir la exposición a contenidos de inversión sin prerrequisitos.
- [ ] Medir la adecuación entre nivel del usuario y dificultad del contenido.
- [ ] Documentar tolerancias y excepciones, si existen.
- [ ] Eliminar fallbacks que puedan saltarse las reglas pedagógicas.
- [ ] Guardar los resultados de estas comprobaciones en el resumen de validación.

**Criterio de finalización:** las reglas pedagógicas se comprueban sobre los datos generados y no solo sobre el código generador.

---

## 10. Implementar la validación automática

- [ ] Ampliar `data/validate.py` para validar estructura, dominio e integridad referencial.
- [ ] Añadir argumentos para indicar el directorio de datos y el archivo de resumen.
- [ ] Hacer que el validador devuelva código de error cuando detecte problemas.
- [ ] Incluir mensajes con archivo, fila y regla incumplida.
- [ ] Validar todos los CSV en una sola ejecución.
- [ ] Validar la cobertura de usuarios y contenidos.
- [ ] Validar las relaciones del grafo y los prerrequisitos de contenidos.
- [ ] Validar las métricas pedagógicas.
- [ ] Evitar depender de una conexión de red para las comprobaciones estructurales.
- [ ] Mantener una comprobación HTTP separada para las URLs.

**Criterio de finalización:** una única orden permite saber si el dataset está listo o qué problema queda pendiente.

---

## 11. Regenerar la documentación del dataset

- [ ] Regenerar `data/validation_summary.md` desde los datos actuales.
- [ ] Incluir recuentos reales de fuentes, contenidos, conceptos, prerrequisitos, usuarios e interacciones.
- [ ] Incluir distribución por tema y dificultad.
- [ ] Incluir cobertura de usuarios y contenidos.
- [ ] Incluir resultados de las validaciones pedagógicas.
- [ ] Incluir limitaciones del uso de datos sintéticos.
- [ ] Incluir riesgos metodológicos.
- [ ] Incluir la aclaración de que las interacciones sintéticas no representan comportamiento real.
- [ ] Eliminar cifras manuales que no procedan de los CSV actuales.
- [ ] Documentar las decisiones tomadas durante la limpieza.

**Criterio de finalización:** el resumen se puede regenerar y sus cifras coinciden con los archivos del dataset.

---

## 12. Comprobación final de la Semana 1

- [ ] Ejecutar todos los scripts desde la raíz del repositorio.
- [ ] Ejecutar `python -m py_compile data/*.py`.
- [ ] Ejecutar el validador completo.
- [ ] Comprobar que el validador termina correctamente.
- [ ] Ejecutar dos veces la generación y comparar los resultados.
- [ ] Confirmar que no aparecen cambios inesperados entre ejecuciones.
- [ ] Ejecutar `git diff --check`.
- [ ] Revisar manualmente una muestra de fuentes, contenidos, conceptos y recomendaciones.
- [ ] Registrar los problemas que se posponen para semanas posteriores.
- [ ] Dar por cerrada la Semana 1 solo cuando todos los criterios críticos estén cumplidos.

---

## Entregables de la Semana 1

- `data/sources.csv` limpio y trazable.
- `data/contents.csv` revisado y coherente.
- `data/concepts.csv` normalizado.
- `data/prerequisites.csv` validado.
- `data/users_synthetic.csv` validado y documentado.
- `data/interactions_synthetic.csv` reproducible y con cobertura comprobada.
- `data/validate.py` convertido en validador automático.
- `data/validation_summary.md` regenerado desde los datos.
- Documento de decisiones metodológicas y limitaciones.

## Criterio global para comenzar la Semana 2

La Semana 2 puede comenzar cuando:

1. Todos los CSV cumplen sus esquemas.
2. No existen referencias huérfanas ni IDs duplicados.
3. Las fuentes y contenidos son trazables.
4. El grafo de prerrequisitos es válido.
5. Las interacciones cubren los usuarios y contenidos definidos.
6. Las reglas pedagógicas se cumplen dentro de las tolerancias documentadas.
7. El resumen de validación coincide con los datos actuales.
8. La generación completa es reproducible.
