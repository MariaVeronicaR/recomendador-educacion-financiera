"""
Genera /data/interactions_synthetic.csv con 1500 interacciones.

Reglas del plan aplicadas:
1. Usuarios con nivel bajo -> contenidos básicos.
2. Usuarios principiantes no ven contenidos avanzados de inversión.
3. La inversión solo aparece si el usuario ya interactuó con ahorro, inflación,
   interés compuesto y riesgo.
4. Contenidos con prerrequisitos aparecen después de sus conceptos base.
5. Usuarios avanzados pueden recibir contenidos intermedios y avanzados.
6. No simular asesoría financiera personalizada.

Distribución: 60% básicos, 30% intermedios, 10% avanzados.
"""

import csv
import random
from collections import defaultdict
from datetime import datetime, timedelta

random.seed(123)

N_INTERACTIONS = 1500
USERS = "/Users/veronica/Desktop/tfm/data/users_synthetic.csv"
CONTENTS = "/Users/veronica/Desktop/tfm/data/contents.csv"
OUT = "/Users/veronica/Desktop/tfm/data/interactions_synthetic.csv"

# Mapa: topic -> conceptos requeridos según grafo
TOPIC_TO_CONCEPTS = {
    "planificación": ["C01", "C16", "C02"],
    "ahorro": ["C02", "C01"],
    "deuda": ["C03", "C01"],
    "crédito": ["C04", "C03"],
    "interés": ["C05", "C06"],
    "inflación": ["C07"],
    "cuentas bancarias": ["C08", "C18"],
    "tarjetas": ["C09", "C01", "C03"],
    "préstamos": ["C10", "C01", "C03", "C19"],
    "hipotecas": ["C11", "C10", "C19", "C05"],
    "inversión": ["C12", "C02", "C07", "C06", "C13", "C14"],
    "riesgo": ["C13", "C22"],
    "diversificación": ["C14", "C12", "C13"],
    "fraude": ["C15", "C29"],
}


def load_users():
    with open(USERS, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_contents():
    with open(CONTENTS, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        r["is_investment_related"] = r["is_investment_related"] == "si"
    return rows


def knowledge_to_num(k):
    return {"bajo": 1, "medio": 2, "alto": 3}[k]


def difficulty_to_num(d):
    return {"básico": 1, "intermedio": 2, "avanzado": 3}[d]


def sigmoid(x):
    import math
    return 1 / (1 + math.exp(-x))


def user_qualifies(user, content, interacted_concepts):
    """Devuelve True si el usuario puede recibir el contenido (reglas del plan)."""
    k = knowledge_to_num(user["financial_knowledge_level"])
    d = difficulty_to_num(content["difficulty"])

    # Regla 1: nivel bajo no recibe avanzados (excepto si ya tiene experiencia inversora)
    if k == 1 and d == 3 and user["investment_experience"] == "ninguna":
        return False

    # Regla 2: principiantes no ven inversión avanzada
    if (content["is_investment_related"] and d == 3
            and user["investment_experience"] in ("ninguna", "básica")):
        return False

    # Regla 3: inversión solo si ya interactuó con ahorro, inflación, interés compuesto, riesgo
    if content["is_investment_related"] and content["difficulty"] != "básico":
        required = {"C02", "C07", "C06", "C13"}
        if not required.issubset(interacted_concepts[user["user_id"]]):
            return False

    # Regla 4: prerrequisitos del tema -> el usuario ya vio conceptos base
    topic = content["topic"]
    base_required = TOPIC_TO_CONCEPTS.get(topic, [])
    if not all(c in interacted_concepts[user["user_id"]] for c in base_required[:2]):
        # Permitimos el primer contacto si el contenido es básico
        if content["difficulty"] != "básico":
            return False

    return True


def sample_event(rng, completion_rate, quiz_score):
    """Asigna un evento según las métricas."""
    if quiz_score is not None and quiz_score >= 0.6:
        if completion_rate >= 0.9:
            return rng.random() < 0.7 and "quiz_passed" or "completed"
        return "quiz_passed"
    if completion_rate >= 0.9:
        return "completed"
    if completion_rate >= 0.5:
        return "viewed"
    if completion_rate < 0.2:
        return "disliked"
    return "viewed"


def main():
    users = load_users()
    contents = load_contents()
    rng = random.Random(7)

    # Estado: conceptos ya interactuados por usuario
    interacted_concepts = defaultdict(set)

    # Distribución forzada: 60% básicos, 30% intermedios, 10% avanzados
    # El muestreo por turno (i % 10) refleja esa distribución, pero al elegir
    # contenido solo por topic, los avanzados aparecen proporcionalmente menos.
    # Para acercarnos al 60/30/10, asignamos pesos explícitos por turno.
    basic = [c for c in contents if c["difficulty"] == "básico"]
    inter = [c for c in contents if c["difficulty"] == "intermedio"]
    adv = [c for c in contents if c["difficulty"] == "avanzado"]

    # Patrón de dificultad para 1500 interacciones siguiendo 60/30/10
    pattern = (["básico"] * 6 + ["intermedio"] * 3 + ["avanzado"] * 1)
    pattern = (pattern * (N_INTERACTIONS // len(pattern) + 1))[:N_INTERACTIONS]
    rng.shuffle(pattern)

    interactions = []
    start = datetime(2025, 9, 1)
    for i, target_diff in enumerate(pattern):
        if target_diff == "básico":
            pool = basic
        elif target_diff == "intermedio":
            pool = inter
        else:
            pool = adv
        # Si el pool está vacío, caer al siguiente
        if not pool:
            pool = contents

        # Buscar usuario y contenido compatibles
        for _ in range(50):
            user = rng.choice(users)
            content = rng.choice(pool)
            if user_qualifies(user, content, interacted_concepts):
                break
        else:
            # fallback: cualquier contenido básico
            user = rng.choice(users)
            content = rng.choice(basic)

        k = knowledge_to_num(user["financial_knowledge_level"])
        d = difficulty_to_num(content["difficulty"])

        # Modelo generativo
        gap = k - d  # positivo = usuario preparado, negativo = contenido difícil
        p_click = sigmoid(1.5 + 0.8 * gap + rng.uniform(-0.4, 0.4))
        if rng.random() > p_click:
            # Si no hace click, registramos un 'viewed' con score bajo
            interactions.append({
                "interaction_id": f"I{i + 1:05d}",
                "user_id": user["user_id"],
                "content_id": content["content_id"],
                "event": "viewed",
                "score": round(0.1 + rng.random() * 0.2, 3),
                "completion_rate": round(rng.random() * 0.1, 3),
                "quiz_score": "",
                "timestamp": (start + timedelta(hours=i * 2)).isoformat(),
            })
            continue

        p_complete = sigmoid(1.0 + 0.7 * gap + rng.uniform(-0.3, 0.3))
        completion = 1 if rng.random() < p_complete else round(rng.random() * 0.7, 2)

        # Quiz score: más alto si el gap es favorable
        if completion == 1:
            q = sigmoid(0.5 + 0.6 * gap + rng.uniform(-0.3, 0.3))
        else:
            q = sigmoid(-0.5 + 0.6 * gap + rng.uniform(-0.3, 0.3))
        quiz = round(q, 3) if rng.random() < 0.6 else None

        event = sample_event(rng, completion if isinstance(completion, float) else 1.0, quiz)

        # Score final combinado
        score = round(0.4 * (completion if isinstance(completion, float) else 1.0)
                      + 0.4 * (quiz if quiz is not None else 0.0)
                      + 0.2 * rng.uniform(0.3, 0.9), 3)

        interactions.append({
            "interaction_id": f"I{i + 1:05d}",
            "user_id": user["user_id"],
            "content_id": content["content_id"],
            "event": event,
            "score": score,
            "completion_rate": completion if isinstance(completion, float) else 1.0,
            "quiz_score": quiz if quiz is not None else "",
            "timestamp": (start + timedelta(hours=i * 2)).isoformat(),
        })

        # Actualizar conceptos interactuados
        topic = content["topic"]
        for cid in TOPIC_TO_CONCEPTS.get(topic, []):
            interacted_concepts[user["user_id"]].add(cid)

    with open(OUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["interaction_id", "user_id", "content_id", "event",
                        "score", "completion_rate", "quiz_score", "timestamp"])
        writer.writeheader()
        writer.writerows(interactions)

    print(f"Generadas {len(interactions)} interacciones en {OUT}")


if __name__ == "__main__":
    main()
