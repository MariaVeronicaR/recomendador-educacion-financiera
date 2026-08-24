"""
Regenera users_synthetic.csv a partir de datos REALES de la ECF 2021 (BdE + CNMV).

IMPORTANTE — Notas metodológicas sobre esta versión:
- Este script NO genera el indicador oficial de conocimiento financiero publicado por el
  Banco de España. Calcula una clasificación sintética en tres niveles (bajo / medio / alto)
  utilizando las tres preguntas del "Big Three" de Lusardi (inflación, interés compuesto y
  diversificación). Los valores "No sabe / No contesta" (-97, -98, -99, NaN) se conservan
  como NaN y NO se imputan como fallo. Si un usuario respondió NS/NC a alguna pregunta,
  su financial_knowledge_level queda como NaN, lo que se reporta explícitamente como
  limitación del estudio. Esto evita tanto el sesgo de selección (excluir a quien no
  contestó) como la imputación artificial (contar NS/NC como fallo).
- La distribución por sexo NO se modifica: se preserva la distribución observada en la
  submuestra de jóvenes 18-34 de la ECF (aproximadamente 85% hombres / 15% mujeres).
  Esto refleja fielmente la composición del dataset original.
- Las distribuciones de edad, educación, situación laboral, ahorro e inversión reflejan
  las proporciones reales observadas en la submuestra de jóvenes 18-34 de la ECF 2021.

Fuentes:
- ecf_2021.csv (BdE + CNMV): 7.764 entrevistas, 1.916 son jóvenes 18-34
- DOI del informe: 10.53479/34752

Uso:
    cd /Users/veronica/Desktop/tfm/ECF-archivos
    python3 regenerate_users_from_ecf.py
"""

import pandas as pd
import numpy as np

# Configuración
np.random.seed(42)  # Reproducibilidad
ECF_PATH = "ecf_2021.csv"
OUTPUT_PATH = "/Users/veronica/Desktop/tfm/data/users_synthetic.csv"

# Códigos de valores missing según la documentación estándar de la ECF
MISSING_CODES = [-97, -98, -99]

# Cargar ECF 2021
print(f"Cargando {ECF_PATH}...")
df = pd.read_csv(ECF_PATH, sep=";", low_memory=False)
print(f"Total registros: {len(df)}")

# Calcular edad y filtrar jóvenes 18-34
df['edad'] = 2021 - df['a0400']
jovenes = df[(df['edad'] >= 18) & (df['edad'] <= 34)].copy()
print(f"Jóvenes 18-34: {len(jovenes)}")

# Utilizar TODOS los jóvenes 18-34 de la ECF (sin muestreo ni filtro restrictivo).
# Esto preserva fielmente la heterogeneidad de la población real, incluyendo los
# registros con NS/NC en las preguntas Big3.
sampled = jovenes.reset_index(drop=True).copy()
print(f"Total usuarios en el dataset sintético: {len(sampled)}\n")

# ============================================================
# MAPEO DE VARIABLES ECF → FORMATO users_synthetic.csv
# ============================================================

# 1. user_id
sampled['user_id'] = [f"U{i:04d}" for i in range(1, len(sampled) + 1)]

# 2. age_group
sampled['age_group'] = sampled['edad'].apply(
    lambda x: "18-24" if 18 <= x <= 24 else "25-34"
)

# 3. sex (a0100: 1=hombre, 0=mujer) - Distribución observada en la ECF sin modificar
sampled['sex'] = sampled['a0100'].map({1: 'hombre', 0: 'mujer'}).fillna(np.nan)

# 3. education_level (e0100: QD9)
# 1=postgrado, 2=universitario, 3=secundario alto, 4=secundario bajo, 5=primaria
def educ_to_level(val):
    if pd.isna(val) or val in MISSING_CODES:
        return 'secundaria'
    mapping = {
        1: 'posgrado',
        2: 'universidad',
        3: 'bachillerato',
        4: 'secundaria',
        5: 'primaria'
    }
    return mapping.get(int(val), 'secundaria')

sampled['education_level'] = sampled['e0100'].apply(educ_to_level)

# 4. employment_status (a1500: QD10)
def work_status(val):
    if pd.isna(val) or val in MISSING_CODES:
        return 'empleado'
    val = int(val)
    if val == 9:
        return 'estudiante'
    elif val == 5:
        return 'desempleado'
    elif val in [1, 2]:
        return 'empleado'
    elif val in [3, 4]:
        return 'empleado'
    elif val == 8:
        return 'desempleado'
    else:
        return 'empleado'

sampled['employment_status'] = sampled['a1500'].apply(work_status)

# 5. financial_knowledge_level (clasificación sintética basada en las 3 preguntas Big3)
# k0600: Inflación (correcta = 3 = "Menos")
# k0100: Interés compuesto (correcta = 3 = "Más de 110")
# k1003: Diversificación (correcta = 1 = "Verdadero")
# NS/NC (-97, -98, -99, NaN) NO se cuentan como fallo, para no inflar el grupo "bajo".
def knowledge_level(row):
    aciertos = 0
    aciertos_posibles = 0
    for col, correcta in [('k0600', 3), ('k0100', 3), ('k1003', 1)]:
        val = row[col]
        if pd.isna(val) or val in MISSING_CODES:
            continue
        aciertos_posibles += 1
        if val == correcta:
            aciertos += 1

    if aciertos_posibles == 0:
        return np.nan
    if aciertos == 0:
        return 'bajo'
    if aciertos < aciertos_posibles:
        return 'medio'
    return 'alto'

sampled['financial_knowledge_level'] = sampled.apply(knowledge_level, axis=1)

# 6. saving_habit (b0130b: QF3 item 2)
def saving_habit(val):
    if pd.isna(val) or val in MISSING_CODES:
        return np.nan
    val = int(val)
    if val == 1:
        return 'frecuente'
    elif val == 0:
        return 'ocasional'
    else:
        return np.nan

sampled['saving_habit'] = sampled['b0130b'].apply(saving_habit)

# 7. investment_experience (b1000c: Qprod1_b item 7)
def investment_exp(val):
    if pd.isna(val) or val in MISSING_CODES:
        return np.nan
    val = int(val)
    if val == 1:
        return 'básica'
    else:
        return 'ninguna'

sampled['investment_experience'] = sampled['b1000c'].apply(investment_exp)

# 8. debt_experience (placeholder coherente con nivel de conocimiento)
def debt_level(row):
    if row['financial_knowledge_level'] == 'bajo':
        return np.random.choice(['baja', 'media'], p=[0.4, 0.6])
    elif row['financial_knowledge_level'] == 'medio':
        return np.random.choice(['ninguna', 'baja'], p=[0.5, 0.5])
    else:
        return 'ninguna'

sampled['debt_experience'] = sampled.apply(debt_level, axis=1)

# 9. financial_behavior_level
def behavior_level(row):
    if row['saving_habit'] == 'frecuente':
        return 'alto'
    elif row['saving_habit'] == 'ocasional':
        return 'medio'
    elif row['saving_habit'] == 'nunca':
        return 'bajo'
    else:
        return np.nan

sampled['financial_behavior_level'] = sampled.apply(behavior_level, axis=1)

# 10. financial_attitude_level
def attitude_level(row):
    if row['financial_knowledge_level'] == 'alto':
        return 'alto'
    elif row['financial_knowledge_level'] == 'medio':
        return np.random.choice(['medio', 'alto'], p=[0.7, 0.3])
    elif row['financial_knowledge_level'] == 'bajo':
        return np.random.choice(['bajo', 'medio'], p=[0.6, 0.4])
    else:
        return np.nan

sampled['financial_attitude_level'] = sampled.apply(attitude_level, axis=1)

# 11. learning_goal
def learning_goal(row):
    if row['investment_experience'] == 'básica':
        return 'prepararse para invertir'
    elif row['saving_habit'] == 'nunca':
        return 'ahorrar'
    elif row['debt_experience'] in ['media', 'alta']:
        return 'entender deuda'
    else:
        return np.random.choice(['presupuestar', 'ahorrar', 'planificar finanzas'],
                               p=[0.3, 0.4, 0.3])

sampled['learning_goal'] = sampled.apply(learning_goal, axis=1)

# ============================================================
# ESCRITURA DEL CSV FINAL
# ============================================================
output_cols = [
    'user_id', 'age_group', 'education_level', 'employment_status',
    'financial_knowledge_level', 'saving_habit', 'debt_experience',
    'investment_experience', 'financial_behavior_level',
    'financial_attitude_level', 'learning_goal', 'sex'
]

final = sampled[output_cols].copy()
final.to_csv(OUTPUT_PATH, index=False)

# ============================================================
# VALIDACIÓN FINAL DE DISTRIBUCIONES
# ============================================================
print("=" * 60)
print("VALIDACIÓN DE DISTRIBUCIONES DEL DATASET SINTÉTICO")
print("=" * 60)

print(f"\nGénero (sex):")
print(final['sex'].value_counts())
print(f"\nTotal hombres: {(final['sex']=='hombre').sum()} ({(final['sex']=='hombre').mean()*100:.1f}%)")
print(f"Total mujeres:  {(final['sex']=='mujer').sum()} ({(final['sex']=='mujer').mean()*100:.1f}%)")

print(f"\nNivel de conocimiento financiero (clasificación sintética Big3):")
print(final['financial_knowledge_level'].value_counts(dropna=False))

print(f"\nHábito de ahorro:")
print(final['saving_habit'].value_counts(dropna=False))

print(f"\nExperiencia inversora:")
print(final['investment_experience'].value_counts(dropna=False))

print(f"\nNivel educativo:")
print(final['education_level'].value_counts(dropna=False))

print(f"\nSituación laboral:")
print(final['employment_status'].value_counts(dropna=False))

print(f"\nGrupo de edad:")
print(final['age_group'].value_counts())

print(f"\n✓ Archivo generado en: {OUTPUT_PATH}")
print("=" * 60)
