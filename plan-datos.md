

# Objetivo

Construir de forma urgente los datos necesarios para desarrollar y evaluar un sistema de recomendación personalizada de contenidos de educación financiera.

El sistema debe recomendar contenidos educativos según el perfil, nivel, progreso y prerrequisitos del usuario. No debe dar asesoramiento financiero personalizado ni recomendar productos financieros concretos [4].

---

## 1. Estrategia de datos

No se espera encontrar un dataset público que incluya al mismo tiempo usuarios, educación financiera, contenidos educativos, interacciones usuario-contenido y resultados de aprendizaje [5].

Por tanto, se construirá un dataset híbrido:

1. **Contenidos reales** desde fuentes institucionales.
2. **Conceptos y prerrequisitos** basados en marcos oficiales de educación financiera.
3. **Usuarios sintéticos** basados en variables de encuestas financieras.
4. **Interacciones sintéticas** para entrenar y evaluar inicialmente el recomendador.

---

## 2. Fuentes confiables a usar

Buscar y registrar URLs oficiales de estas fuentes:

1. Finanzas para Todos.
2. CNMV — Guías del inversor.
3. Banco de España — Portal del Cliente Bancario.
4. Plan de Educación Financiera.
5. OECD/INFE Financial Literacy Framework.
6. PISA Financial Literacy Framework.
7. OECD/INFE 2023 International Survey of Adult Financial Literacy.
8. Encuesta de Competencias Financieras — Banco de España / CNMV.

Estas fuentes servirán para definir contenidos, conceptos, niveles de dificultad, temas, subtemas, prerrequisitos y rutas de aprendizaje [5].

---

## 3. Archivos que se deben generar

Generar todo dentro de una carpeta `/data`:

```txt
/data
  sources.csv
  contents.csv
  concepts.csv
  prerequisites.csv
  users_synthetic.csv
  interactions_synthetic.csv
  validation_summary.md
```

---

## 4. sources.csv

Registrar todas las fuentes usadas.

Columnas:

```csv
source_id,source_name,organization,url,type,use,reliability,access_date
```

Reglas:

- Usar solo fuentes oficiales, institucionales o académicas.
- No inventar URLs.
- No usar blogs comerciales como fuente principal.
- Registrar fecha de consulta.

---

## 5. contents.csv

Crear mínimo 50 contenidos reales.

Columnas:

```csv
content_id,title,source,url,topic,subtopic,difficulty,format,summary,learning_objective,prerequisites,risk_level,is_investment_related
```

Temas mínimos:

```txt
presupuesto
ahorro
deuda
crédito
interés simple
interés compuesto
inflación
cuentas bancarias
tarjetas
préstamos
hipotecas
inversión
riesgo
diversificación
fraude financiero
planificación financiera
```

Dificultad:

```txt
básico
intermedio
avanzado
```

Riesgo pedagógico:

```txt
bajo
medio
alto
```

Reglas:

- Todo contenido debe tener URL verificable.
- Todo contenido debe tener fuente confiable.
- Los contenidos de inversión deben tener prerrequisitos.
- No incluir recomendaciones de productos financieros.

---

## 6. concepts.csv

Crear la taxonomía de conceptos financieros.

Columnas:

```csv
concept_id,concept_name,description,topic,difficulty
```

Conceptos mínimos:

```txt
presupuesto
ahorro
deuda
crédito
interés simple
interés compuesto
inflación
cuenta bancaria
tarjeta de crédito
préstamo
hipoteca
inversión
riesgo
diversificación
fraude financiero
planificación financiera
```

---

## 7. prerequisites.csv

Crear relaciones de prerrequisito.

Columnas:

```csv
concept_id,prerequisite_concept_id,reason
```

Reglas mínimas:

```txt
inversión requiere ahorro
inversión requiere inflación
inversión requiere interés compuesto
inversión requiere riesgo
tarjeta de crédito requiere presupuesto
tarjeta de crédito requiere deuda
préstamo requiere presupuesto
préstamo requiere deuda
hipoteca requiere préstamo
hipoteca requiere interés
hipoteca requiere deuda
diversificación requiere inversión
diversificación requiere riesgo
planificación financiera requiere presupuesto
planificación financiera requiere ahorro
```

---

## 8. users_synthetic.csv

Crear mínimo 200 usuarios sintéticos.

Columnas:

```csv
user_id,age_group,education_level,employment_status,financial_knowledge_level,saving_habit,debt_experience,investment_experience,financial_behavior_level,financial_attitude_level,learning_goal
```

Variables basadas en el enfoque OCDE/INFE: conocimientos financieros, comportamiento financiero y actitud financiera [4].

Valores sugeridos:

```txt
age_group: 18-24, 25-34, 35-44, 45-54, 55+
education_level: secundaria, bachillerato, formación profesional, universidad, posgrado
employment_status: estudiante, empleado, autónomo, desempleado
financial_knowledge_level: bajo, medio, alto
saving_habit: nunca, ocasional, frecuente
debt_experience: ninguna, baja, media, alta
investment_experience: ninguna, básica, intermedia, avanzada
financial_behavior_level: bajo, medio, alto
financial_attitude_level: bajo, medio, alto
learning_goal: presupuestar, ahorrar, entender deuda, usar crédito, prepararse para invertir, evitar fraude, planificar finanzas
```

---

## 9. interactions_synthetic.csv

Crear mínimo 1,000 interacciones sintéticas.

Columnas:

```csv
interaction_id,user_id,content_id,event,score,completion_rate,quiz_score,timestamp
```

Eventos:

```txt
viewed
completed
liked
disliked
quiz_passed
quiz_failed
```

Reglas de generación:

1. Usuarios con nivel bajo deben recibir principalmente contenidos básicos.
2. Usuarios principiantes no deben recibir contenidos avanzados de inversión.
3. La inversión solo puede aparecer si el usuario ya interactuó con ahorro, inflación, interés compuesto y riesgo.
4. Los contenidos con prerrequisitos deben aparecer después de sus conceptos base.
5. Usuarios avanzados pueden recibir contenidos intermedios y avanzados.
6. No simular asesoría financiera personalizada.

Distribución sugerida:

```txt
60% contenidos básicos
30% contenidos intermedios
10% contenidos avanzados
```

---

## 10. Datos necesarios para evaluar el modelo

El dataset debe permitir evaluar:

```txt
precision@k
recall@k
coverage
diversity
cumplimiento de prerrequisitos
adecuación nivel-contenido
exposición indebida a contenidos de inversión
```

Validaciones mínimas:

1. Porcentaje de contenidos con URL oficial.
2. Número de contenidos por tema.
3. Número de contenidos por dificultad.
4. Porcentaje de recomendaciones que respetan prerrequisitos.
5. Porcentaje de contenidos avanzados mostrados a principiantes.
6. Porcentaje de contenidos de inversión mostrados sin prerrequisitos.

---

## 11. validation_summary.md

Crear un resumen con:

```txt
número de fuentes usadas
número de contenidos reales
número de conceptos
número de usuarios sintéticos
número de interacciones sintéticas
distribución por dificultad
distribución por tema
limitaciones del dataset
riesgos metodológicos
```

Debe incluir esta aclaración:

> Las interacciones sintéticas no representan comportamiento real de usuarios. Se usan solo para construir, probar y evaluar inicialmente el sistema de recomendación. La validación definitiva requeriría usuarios reales o evaluación experta.

---

## 12. Prompt para ejecutar en Claude

Ejecuta este plan de datos urgente.

Objetivo: construir los datos necesarios para desarrollar y evaluar un recomendador personalizado de contenidos de educación financiera.

Prioridad:

1. Buscar fuentes oficiales.
2. Crear sources.csv.
3. Crear contents.csv con mínimo 50 contenidos reales y URLs verificables.
4. Crear concepts.csv.
5. Crear prerequisites.csv.
6. Crear users_synthetic.csv con mínimo 200 usuarios.
7. Crear interactions_synthetic.csv con mínimo 1,000 interacciones.
8. Crear validation_summary.md.

Reglas:

- No inventes URLs.
- No uses blogs financieros comerciales como fuente principal.
- Todo contenido debe tener fuente verificable.
- No recomiendes productos financieros.
- No generes asesoría financiera personalizada.
- Las recomendaciones deben respetar nivel, progreso y prerrequisitos.
- Los contenidos de inversión solo deben aparecer si el usuario domina conceptos previos.

Entrega final:

```txt
/data/sources.csv
/data/contents.csv
/data/concepts.csv
/data/prerequisites.csv
/data/users_synthetic.csv
/data/interactions_synthetic.csv
/data/validation_summary.md
```

---

## Riesgo clave

Lo más importante ahora es `contents.csv`.

Sin contenidos reales con URL verificable, el modelo no será defendible.
