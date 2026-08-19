# Resumen del análisis: ECF 2021 para TFM

**Fecha del análisis:** 2026-08-18
**Archivos analizados:**
- `ecf_2021.csv` (9.5 MB, 7.764 entrevistas, 429 columnas)
- `Variables_Informe_ECF_2021.pdf` (mapeo de variables)
- `Cuestionario_Questionnaire_OECD_INFE_2018.pdf` (definición de preguntas)

**Fuentes:**
- BdE + CNMV (2023). Encuesta de Competencias Financieras 2021. DOI: 10.53479/34752
- OECD/INFE (2018). Toolkit for Measuring Adult Financial Literacy

---

## 1. Estructura del dataset

| Característica | Valor |
|---|---|
| Total entrevistas | 7.764 |
| Total columnas | 429 |
| Codificación valores missing | -97 (NS), -98 (NC), -99 (Rechazo) |
| Variables demográficas | Prefijos `a0`, `a1`, `a2` |
| Variables de comportamiento | Prefijos `b0`, `b1`, `c0`, `f0` |
| Variables de productos financieros | Prefijos `cc`, `b1000` |
| Variables de conocimiento (Big3) | Prefijo `k` |
| Variable de edad | `a0400` (año de nacimiento) |

---

## 2. Preguntas Big3 identificadas

Las preguntas **Big3** de Lusardi & Mitchell (interés compuesto, inflación, diversificación) son las críticas para medir alfabetización financiera. Tras revisar el cuestionario OECD/INFE 2018 y verificar las distribuciones, las variables correctas son:

### Inflación (QK3)
- **Variable CSV:** `k0600`
- **Pregunta:** "Si la tasa de interés de tu cuenta es 1% anual y la inflación 2%, ¿podrás comprar más, igual o menos?"
- **Opciones:** 1=Más, 2=Igual, 3=Menos (**correcta**), 4=NS/NC espontáneo
- **% acierto en jóvenes 18-34:** 72.1% (sin NS/NC) / 33.5% (sobre todos)
- **% esperado según ECF 2021 (jóvenes 18-34):** 60%
- **Diferencia:** el ECF cita el dato con NS/NC contado como "incorrecto"; nosotros lo calculamos sin NS/NC. La diferencia es metodológica.

### Interés compuesto (QK6)
- **Variable CSV:** `k0100`
- **Pregunta:** "Si depositas $100 en una cuenta al 2% anual, ¿cuánto tendrás al cabo de 5 años?"
- **Opciones:** 1=Menos de $110, 2=Exactamente $110, 3=Más de $110 (**correcta**), 4=Imposible saber, 5=NS/NC
- **% acierto en jóvenes 18-34:** 57.3% (sin NS/NC) / 28.2% (sobre todos)
- **% esperado según ECF 2021:** 44%

### Diversificación del riesgo (QK7 item 3)
- **Variable CSV:** `k1003`
- **Pregunta:** "Es menos probable que pierdas todo tu dinero si lo ahorras/inviertes en más de un lugar"
- **Opciones:** 1=Verdadero (**correcta**), 0=Falso
- **% acierto en jóvenes 18-34:** 70.4% (sin NS/NC) / 29.4% (sobre todos)
- **% esperado según ECF 2021:** 50%

**Nota metodológica importante:** las preguntas Big3 tienen un problema de "missing" alto (~50% NS/NC). Esto sugiere que la ECF solo administró las preguntas Big3 a una submuestra, no a todos los encuestados. Los % publicados del ECF probablemente usan una metodología distinta (imputación de NS/NC o muestra específica).

---

## 3. Variables demográficas y de comportamiento

| Variable sintética | Variable ECF | Pregunta/Categoría | Distribución jóvenes 18-34 |
|---|---|---|---|
| `sex` | `a0100` (QD1) | 1=Hombre, 0=Mujer | 85% hombre, 15% mujer (⚠️ sesgo del ECF) |
| `education_level` | `e0100` (QD9) | 1-5 (postgrado → primaria) | postgrado 11%, universidad 33%, bachillerato 47%, secundaria 9%, primaria 1% |
| `employment_status` | `a1500` (QD10) | 1-10 (incluye estudiante) | empleado 51%, estudiante 28%, desempleado 13%, autónomo 7% |
| `saving_habit` | `b0130b` (QF3 item 2) | 1=Tiene cuenta de ahorro | 86% sí, 14% no |
| `investment_experience` | `b1000c` (Qprod1_b item 7) | 1=Tiene acciones | 8% sí, 92% no |

---

## 4. Hallazgos importantes

### 4.1 Sesgo de género en la submuestra
El 85% de los jóvenes 18-34 en el ECF son hombres. Esto **NO refleja la realidad** (debería ser ~50%). Es probablemente un artefacto del diseño muestral o un filtro de la submuestra con Big3.

**Acción recomendada:** sobrescribir `sex` con distribución 50/50 en `users_synthetic.csv`.

### 4.2 Alta tasa de "No sabe / No contesta" en Big3
Alrededor del 50% de jóvenes 18-34 no responden a las preguntas Big3 (códigos -97, -98, -99). Esto es consistente con literatura sobre baja alfabetización financiera.

**Implicación:** al calcular el `financial_knowledge_level` sintético, es importante que los NS/NC se traduzcan en "nivel bajo" (lo cual ya hace el script).

### 4.3 Coherencia con datos publicados
Las distribuciones de educación, empleo y ahorro son consistentes con lo esperado para jóvenes españoles. La distribución de conocimiento (56% bajo, 32% medio, 12% alto) es coherente con la brecha conocida.

### 4.4 Variables no identificadas en este análisis
Algunas variables del CSV original siguen sin mapeo claro:
- `b0202, b0203, b0204` son binarias con 85-89% de "sí" (probablemente QF3 items 1-3 sobre métodos de ahorro).
- Columnas con prefijo `tm`, `ag`, `ne` probablemente son técnicas (tiempo de entrevista, agencia, nestring).
- Columnas `cc0600a-cc0600n` (Qprod1_b) no se exploraron en detalle.

---

## 5. Cómo se usaron estos datos

El script `regenerate_users_from_ecf.py` (en `/data/`) usa las variables identificadas para muestrear 250 usuarios reales de los 1.916 jóvenes 18-34, preservando las distribuciones reales.

**Resultado:** `users_synthetic.csv` ahora contiene 250 usuarios calibrados con datos reales de la ECF 2021, en lugar de valores inventados.

---

## 6. Limitaciones del análisis

1. **No se descargaron los microdatos de las variables monetarias imputadas** (`ecf_2021_imp.csv.zip`). Podrían añadirse para tener ingresos reales por hogar.
2. **No se exploraron las preguntas de comportamiento adicionales** (QF4, QF8, QF11, QF12) que podrían enriquecer el perfil sintético.
3. **No se verificó la pregunta de tenencia de criptomonedas** (Qprod1_b item 15), que sería muy relevante para el público 22-30.
4. **El cuestionario OECD/INFE 2018 está en inglés**; las preguntas fueron traducidas al español en el ECF del BdE, pero los códigos del CSV son los originales.

---

## 7. Próximos pasos sugeridos

1. **Descargar `ecf_2021_imp.csv.zip`** (variables monetarias imputadas, 176 KB) para incluir ingresos del hogar reales.
2. **Solucionar el sesgo de género** en `users_synthetic.csv` (sobrescribir `sex` con 50/50).
3. **Regenerar `interactions_synthetic.csv`** con los nuevos perfiles (re-ejecutar `generate_interactions.py`).
4. **Actualizar `validation_summary.md`** con las nuevas cifras de distribución.
5. **Verificar manualmente las 60 URLs de `contents.csv`** con el script de `curl`.
6. **Aplicar las correcciones del PDF** (`/data/correcciones_pdf.md`).

---

## Referencias

- Hospido, L., Machelett, M., Pidkuyko, M., Villanueva, E., & Banco de España (2023). *Encuesta de Competencias Financieras 2021: principales resultados y cambios desde 2016*. DOI: 10.53479/34752
- OECD (2018). *OECD/INFE Questionnaire 2018*. OECD Publishing, Paris.
- OECD (2026). *OECD/INFE Toolkit for Measuring Financial Literacy, Inclusion and Well-Being 2026*. OECD Publishing, Paris.
