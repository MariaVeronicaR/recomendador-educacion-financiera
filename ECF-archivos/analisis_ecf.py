"""
Análisis exploratorio de la Encuesta de Competencias Financieras (ECF) 2021.

Identifica las variables clave para regenerar users_synthetic.csv:
- Big3 (QK3, QK6, QK7): Inflación, Interés compuesto, Diversificación
- QD9 (Nivel educativo): e0100
- QD10 (Situación laboral): a1500
- QD1 (Sexo): a0100
- QF3 (Hábito de ahorro): b0130b
- Qprod1_b item 7 (Tenencia de acciones): b1000c
- Edad: calculada como 2021 - a0400

Total entrevistas: 7.764
Jóvenes 18-34: 1.916

Uso:
    cd /Users/veronica/Desktop/tfm/ECF-archivos
    python3 analisis_ecf.py
"""

import pandas as pd

# Cargar ECF 2021
print("=" * 60)
print("ANÁLISIS EXPLORATORIO ECF 2021")
print("=" * 60)

df = pd.read_csv("ecf_2021.csv", sep=";", low_memory=False)
print(f"\nTotal registros: {len(df)}")
print(f"Total columnas: {len(df.columns)}")

# Filtrar jóvenes 18-34
df['edad'] = 2021 - df['a0400']
jovenes = df[(df['edad'] >= 18) & (df['edad'] <= 34)].copy()
print(f"Jóvenes 18-34: {len(jovenes)}\n")

# ============================================================
# 1. VARIABLES BIG3 (Conocimiento financiero)
# ============================================================
print("=" * 60)
print("1. PREGUNTAS BIG3 (Conocimiento financiero)")
print("=" * 60)

print("\nINFLACIÓN (QK3) - Variable: k0600")
print("Pregunta: '¿Podrás comprar más, igual o menos dentro de un año?'")
print("Opciones: 1=Más, 2=Igual, 3=Menos (correcta)")
print(f"Distribución jóvenes 18-34:")
print(jovenes['k0600'].value_counts(dropna=False).sort_index())
correctas = (jovenes['k0600'] == 3).sum()
validas = jovenes[jovenes['k0600'].isin([1,2,3])]
print(f"\n% acierto (sobre todos): {correctas/len(jovenes)*100:.1f}%")
print(f"% acierto (sin NS/NC): {correctas/len(validas)*100:.1f}%")
print(f"Esperado según ECF 2021 (jóvenes 18-34): 60%")

print("\n" + "-" * 60)
print("\nINTERÉS COMPUESTO (QK6) - Variable: k0100")
print("Pregunta: '¿Cuánto dinero tendrás tras 5 años con 100€ al 2% anual?'")
print("Opciones: 1=Menos de 110, 2=Exactamente 110, 3=Más de 110 (correcta), 4=Imposible saber")
print(f"Distribución jóvenes 18-34:")
print(jovenes['k0100'].value_counts(dropna=False).sort_index())
correctas = (jovenes['k0100'] == 3).sum()
validas = jovenes[jovenes['k0100'].isin([1,2,3,4,5])]
print(f"\n% acierto (sobre todos): {correctas/len(jovenes)*100:.1f}%")
print(f"% acierto (sin NS/NC): {correctas/len(validas)*100:.1f}%")
print(f"Esperado según ECF 2021 (jóvenes 18-34): 44%")

print("\n" + "-" * 60)
print("\nDIVERSIFICACIÓN (QK7 item 3) - Variable: k1003")
print("Pregunta: 'Es menos probable que pierdas todo tu dinero si lo ahorras/inviertes en más de un lugar'")
print("Opciones: 1=Verdadero (correcta), 0=Falso")
print(f"Distribución jóvenes 18-34:")
print(jovenes['k1003'].value_counts(dropna=False).sort_index())
correctas = (jovenes['k1003'] == 1).sum()
validas = jovenes[jovenes['k1003'].isin([0,1])]
print(f"\n% acierto (sobre todos): {correctas/len(jovenes)*100:.1f}%")
print(f"% acierto (sin NS/NC): {correctas/len(validas)*100:.1f}%")
print(f"Esperado según ECF 2021 (jóvenes 18-34): 50%")

# ============================================================
# 2. VARIABLES DEMOGRÁFICAS
# ============================================================
print("\n" + "=" * 60)
print("2. VARIABLES DEMOGRÁFICAS")
print("=" * 60)

print("\nSEXO (QD1) - Variable: a0100")
print("1=Hombre, 0=Mujer")
print(f"Distribución jóvenes 18-34:")
print(jovenes['a0100'].value_counts(dropna=False).sort_index())
print(f"\n% hombres: {jovenes['a0100'].value_counts(normalize=True).get(1, 0)*100:.1f}%")
print(f"% mujeres: {jovenes['a0100'].value_counts(normalize=True).get(0, 0)*100:.1f}%")

print("\n" + "-" * 60)
print("\nNIVEL EDUCATIVO (QD9) - Variable: e0100")
print("1=Postgrado, 2=Universitario, 3=Secundario alto, 4=Secundario bajo, 5=Primaria")
print(f"Distribución jóvenes 18-34:")
print(jovenes['e0100'].value_counts(dropna=False).sort_index())
print(f"\n% por nivel (sin NS/NC):")
for v in [1, 2, 3, 4, 5]:
    pct = jovenes[jovenes['e0100'] == v].shape[0] / jovenes[jovenes['e0100'].isin([1,2,3,4,5])].shape[0] * 100
    nivel = {1: 'Postgrado', 2: 'Universitario', 3: 'Secundario alto',
             4: 'Secundario bajo', 5: 'Primaria'}[v]
    print(f"  {nivel}: {pct:.1f}%")

print("\n" + "-" * 60)
print("\nSITUACIÓN LABORAL (QD10) - Variable: a1500")
print("1=Autónomo, 2=Empleado, 3=Aprendiz, 4=Labores del hogar,")
print("5=Desempleado, 6=Jubilado, 7=Incapacidad, 8=No trabaja ni busca,")
print("9=Estudiante, 10=Otros")
print(f"Distribución jóvenes 18-34:")
print(jovenes['a1500'].value_counts(dropna=False).sort_index())
print(f"\n% principales:")
for v in [2, 9, 5, 1]:
    pct = jovenes['a1500'].value_counts(normalize=True).get(v, 0) * 100
    cat = {2: 'Empleado', 9: 'Estudiante', 5: 'Desempleado', 1: 'Autónomo'}[v]
    print(f"  {cat}: {pct:.1f}%")

# ============================================================
# 3. VARIABLES DE COMPORTAMIENTO
# ============================================================
print("\n" + "=" * 60)
print("3. VARIABLES DE COMPORTAMIENTO")
print("=" * 60)

print("\nHÁBITO DE AHORRO (QF3 item 2) - Variable: b0130b")
print("Pregunta: '¿En los últimos 12 meses has ahorrado en cuenta/depósito?'")
print("1=Sí, 0=No")
print(f"Distribución jóvenes 18-34:")
print(jovenes['b0130b'].value_counts(dropna=False).sort_index())
print(f"\n% ahorran en cuenta: {jovenes['b0130b'].value_counts(normalize=True).get(1, 0)*100:.1f}%")

print("\n" + "-" * 60)
print("\nTENENCIA DE ACCIONES (Qprod1_b item 7) - Variable: b1000c")
print("Pregunta: '¿Actualmente tienes acciones/participaciones?'")
print("1=Sí, 0=No")
print(f"Distribución jóvenes 18-34:")
print(jovenes['b1000c'].value_counts(dropna=False).sort_index())
print(f"\n% tienen acciones: {jovenes['b1000c'].value_counts(normalize=True).get(1, 0)*100:.1f}%")

# ============================================================
# 4. RESUMEN DE VARIABLES IDENTIFICADAS
# ============================================================
print("\n" + "=" * 60)
print("4. RESUMEN DE VARIABLES IDENTIFICADAS PARA USERS_SYNTHETIC")
print("=" * 60)

mapeo = {
    'user_id': 'sintético (U0001-U0250)',
    'age_group': "calculado: 18-24 / 25-34 desde edad = 2021 - a0400",
    'sex': 'a0100 (1=hombre, 0=mujer)',
    'education_level': 'e0100 (QD9: 1-5)',
    'employment_status': 'a1500 (QD10: 1-10)',
    'financial_knowledge_level': 'calculado desde Big3 (k0600, k0100, k1003)',
    'saving_habit': 'b0130b (QF3 item 2)',
    'investment_experience': 'b1000c (Qprod1_b item 7)',
    'debt_experience': 'placeholder coherente con knowledge',
    'financial_behavior_level': 'calculado desde saving_habit',
    'financial_attitude_level': 'calculado desde knowledge',
    'learning_goal': 'placeholder derivado de perfil'
}

for var, fuente in mapeo.items():
    print(f"\n{var:30s} ← {fuente}")

print("\n" + "=" * 60)
print("ANÁLISIS COMPLETADO")
print("=" * 60)
