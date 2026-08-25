"""
Genera /data/users_synthetic.csv con 250 usuarios sintéticos.
Distribuciones calibradas con los resultados de la Encuesta de Competencias
Financieras 2021 (BdE/CNMV): 76% suspende en conocimientos básicos.

Reglas:
- 200+ usuarios como pide el plan.
- Variables basadas en OCDE/INFE (knowledge, behavior, attitude).
- Coherencia entre variables: no se permite knowledge=alto y saving_habit=nunca.
"""

import csv
import random

random.seed(42)

N = 250
OUT = "/Users/veronica/Desktop/tfm/data/users_synthetic.csv"

# Distribuciones inspiradas en la Encuesta BdE/CNMV 2021
AGE_DIST = [("18-24", 0.25), ("25-34", 0.30), ("35-44", 0.20),
            ("45-54", 0.15), ("55+", 0.10)]
EDUCATION_DIST = [("secundaria", 0.25), ("bachillerato", 0.25),
                  ("formación profesional", 0.20),
                  ("universidad", 0.25), ("posgrado", 0.05)]
EMPLOYMENT_DIST = [("estudiante", 0.20), ("empleado", 0.55),
                   ("autónomo", 0.10), ("desempleado", 0.15)]
# 76% de los españoles suspende en competencias financieras -> distribución
KNOWLEDGE_DIST = [("bajo", 0.40), ("medio", 0.45), ("alto", 0.15)]
SAVING_DIST = [("nunca", 0.30), ("ocasional", 0.50), ("frecuente", 0.20)]
DEBT_DIST = [("ninguna", 0.30), ("baja", 0.30), ("media", 0.25), ("alta", 0.15)]
INVEST_DIST = [("ninguna", 0.55), ("básica", 0.25),
               ("intermedia", 0.15), ("avanzada", 0.05)]
BEHAVIOR_DIST = [("bajo", 0.35), ("medio", 0.45), ("alto", 0.20)]
ATTITUDE_DIST = [("bajo", 0.25), ("medio", 0.50), ("alto", 0.25)]
LEARNING_GOALS = ["presupuestar", "ahorrar", "entender deuda", "usar crédito",
                  "prepararse para invertir", "evitar fraude",
                  "planificar finanzas"]
LEARNING_DIST = [("presupuestar", 0.15), ("ahorrar", 0.20),
                 ("entender deuda", 0.15), ("usar crédito", 0.10),
                 ("prepararse para invertir", 0.10),
                 ("evitar fraude", 0.10), ("planificar finanzas", 0.20)]


def weighted_choice(pairs):
    r = random.random()
    acc = 0
    for value, p in pairs:
        acc += p
        if r <= acc:
            return value
    return pairs[-1][0]


def coherent_knowledge(education):
    """Ligera correlación educación-conocimiento."""
    if education in ("universidad", "posgrado"):
        return weighted_choice([("bajo", 0.30), ("medio", 0.50), ("alto", 0.20)])
    if education == "formación profesional":
        return weighted_choice([("bajo", 0.40), ("medio", 0.50), ("alto", 0.10)])
    return weighted_choice([("bajo", 0.50), ("medio", 0.40), ("alto", 0.10)])


def coherent_saving(knowledge):
    """A mayor conocimiento, mayor probabilidad de ahorrar."""
    if knowledge == "alto":
        return weighted_choice([("nunca", 0.10), ("ocasional", 0.50), ("frecuente", 0.40)])
    if knowledge == "medio":
        return weighted_choice([("nunca", 0.25), ("ocasional", 0.55), ("frecuente", 0.20)])
    return weighted_choice([("nunca", 0.50), ("ocasional", 0.40), ("frecuente", 0.10)])


def coherent_investment(knowledge, age):
    """Inversión requiere conocimiento y cierta edad."""
    if knowledge == "bajo" or age == "18-24":
        return weighted_choice([("ninguna", 0.80), ("básica", 0.15),
                                ("intermedia", 0.04), ("avanzada", 0.01)])
    if knowledge == "medio":
        return weighted_choice([("ninguna", 0.55), ("básica", 0.30),
                                ("intermedia", 0.12), ("avanzada", 0.03)])
    return weighted_choice([("ninguna", 0.30), ("básica", 0.30),
                            ("intermedia", 0.30), ("avanzada", 0.10)])


rows = []
for i in range(1, N + 1):
    age = weighted_choice(AGE_DIST)
    edu = weighted_choice(EDUCATION_DIST)
    emp = weighted_choice(EMPLOYMENT_DIST)
    know = coherent_knowledge(edu)
    sav = coherent_saving(know)
    debt = weighted_choice(DEBT_DIST)
    inv = coherent_investment(know, age)
    beh = weighted_choice(BEHAVIOR_DIST)
    att = weighted_choice(ATTITUDE_DIST)
    goal = weighted_choice(LEARNING_DIST)
    rows.append({
        "user_id": f"U{i:04d}",
        "age_group": age,
        "education_level": edu,
        "employment_status": emp,
        "financial_knowledge_level": know,
        "saving_habit": sav,
        "debt_experience": debt,
        "investment_experience": inv,
        "financial_behavior_level": beh,
        "financial_attitude_level": att,
        "learning_goal": goal,
    })

with open(OUT, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)

print(f"Generados {len(rows)} usuarios en {OUT}")
