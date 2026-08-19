"""
Genera /data/interactions_synthetic_realistic.csv con 1500 interacciones.

A diferencia de generate_interactions.py (modelo sigmoid genérico), este script
usa distribuciones REALES de comportamiento financiero de la ECF 2021 (BdE + CNMV)
para personalizar las interacciones por usuario:

- b0130a (50.5% sí): ¿tiene alguna forma de ahorro? → afecta probabilidad de
  consumir contenidos de ahorro/planificación.
- b0130b (86.3%): ¿tiene cuenta de ahorro? → afecta contenidos básicos de cuentas.
- b0130c (9.3%): ¿ahorro informal/familiar? → afecta contenidos avanzados.
- b1000b (60.6%): ¿puede pagar gasto imprevisto? → afecta contenidos de
  presupuesto y prevención de deuda.
- a0320 (20.6%): ¿ha dejado de cubrir gastos? → afecta contenidos de deuda/crédito.

Las 6 reglas pedagógicas del plan siguen vigentes:
1. Usuarios con nivel bajo -> contenidos básicos.
2. Usuarios principiantes no ven contenidos avanzados de inversión.
3. La inversión solo aparece si el usuario ya interactuó con ahorro, inflación,
   interés compuesto y riesgo.
4. Contenidos con prerrequisitos aparecen después de sus conceptos base.
5. Usuarios avanzados pueden recibir contenidos intermedios y avanzados.
6. No simular asesoría financiera personalizada.

Uso:
    cd /Users/veronica/Desktop/tfm/ECF-archivos
    python3 generate_interactions_realistic.py
"""

import csv
import random
from collections import defaultdict
from datetime import datetime, timedelta

import pandas as pd

random.seed(123)

N_INTERACTIONS = 1500
USERS = "/Users/veronica/Desktop/tfm/data/users_synthetic.csv"
CONTENTS = "/Users/veronica/Desktop/tfm/data/contents.csv"
ECF = "ecf_2021.csv"  # Debe estar descomprimido en la carpeta actual
OUT = "/Users/veronica/Desktop/tfm/data/interactions_synthetic_realistic.csv"

# Mapa: topic -> conceptos requeridos según grafo pedagógico
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


def load_ecf_behaviors():
    """Carga las 5 variables de comportamiento del ECF para los 250 usuarios muestreados.

    Estrategia: como users_synthetic.csv tiene user_id = U0001...U0250 y cada uno fue
    muestreado de un índice del ECF, podemos recuperar las variables ECF usando el
    mismo seed. Sin embargo, esto es complejo. Solución pragmática: cargar el ECF
    y muestrear 250 filas con el mismo seed, luego extraer las variables de
    comportamiento y asociarlas por índice de muestreo.
    """
    print("Cargando ECF 2021...")
    df = pd.read_csv(ECF, sep=";", low_memory=False)
    df['edad'] = 2021 - df['a0400']
    jovenes = df[(df['edad'] >= 18) & (df['edad'] <= 34)].copy().reset_index(drop=True)
    print(f"Jóvenes 18-34 disponibles: {len(jovenes)}")

    # Muestreo con el mismo seed que regenerate_users_from_ecf.py
    sampled = jovenes.sample(n=250, replace=True, random_state=42).reset_index(drop=True)

    # Extraer las 5 variables de comportamiento (binarias 0/1)
    behaviors = pd.DataFrame({
        'sampled_index': range(250),
        'b0130a_ahorro_cualquiera': sampled['b0130a'].fillna(0).astype(int),
        'b0130b_cuenta_ahorro': sampled['b0130b'].fillna(0).astype(int),
        'b0130c_ahorro_informal': sampled['b0130c'].fillna(0).astype(int),
        'b1000b_puede_pagar_imprevisto': sampled['b1000b'].fillna(0).astype(int),
        'a0320_no_cubre_gastos': sampled['a0320'].fillna(0).astype(int),
    })
    return behaviors


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


def topic_affinity(user_behavior, topic):
    """Calcula la afinidad de un usuario a un topic según su comportamiento ECF.

    Devuelve un peso entre 0 y 1 que representa la probabilidad relativa de
    que este usuario consuma un contenido de este topic, dado su comportamiento
    financiero real.

    Lógica con efecto más marcado:
    - Si tiene cuenta de ahorro (b0130b=1), es más afín a planificación/ahorro.
    - Si NO puede pagar imprevisto (b1000b=0), es más afín a presupuesto/deuda.
    - Si ha dejado de cubrir gastos (a0320=1), es más afín a deuda/crédito.
    - Si tiene ahorro informal (b0130c=1), es más afín a inversión/avanzado.
    - Si tiene alguna forma de ahorro (b0130a=1), afinidad media-alta a ahorro.

    Para evitar que el efecto se diluya, los pesos base son bajos y los boosts
    son fuertes (+/- 0.5 a 1.0). Así un cambio de comportamiento tiene un
    impacto real en la probabilidad de consumir ese topic.
    """
    weights = {
        # Topics de aprendizaje básico universal: todos los consumen
        # (afinidad alta para todos, no discrimina por comportamiento)
        "planificación": (0.8, []),
        "ahorro": (0.7, [
            ("b0130a_ahorro_cualquiera", 0.2),
            ("a0320_no_cubre_gastos", 0.3),  # quien no cubre, busca ahorrar
        ]),
        "fraude": (0.7, []),

        # Topics que SÍ discriminan por comportamiento
        "deuda": (0.1, [
            ("a0320_no_cubre_gastos", 1.0),  # si tiene problemas, muy afín
        ]),
        "crédito": (0.1, [
            ("a0320_no_cubre_gastos", 0.8),
            ("b1000b_puede_pagar_imprevisto", -0.1),
        ]),
        "préstamos": (0.1, [
            ("a0320_no_cubre_gastos", 0.6),
        ]),
        "tarjetas": (0.2, [
            ("a0320_no_cubre_gastos", 0.4),
        ]),

        # Productos bancarios: afines si ya operan
        "cuentas bancarias": (0.3, [
            ("b0130b_cuenta_ahorro", 0.5),
        ]),
        "hipotecas": (0.1, [
            ("b0130b_cuenta_ahorro", 0.3),
        ]),

        # Inversión: afinidad alta solo si ya tiene comportamiento inversor
        "inversión": (0.05, [
            ("b0130c_ahorro_informal", 1.0),  # si ahorra informalmente, muy afín
            ("b0130b_cuenta_ahorro", 0.2),
            ("a0320_no_cubre_gastos", -0.05),  # desincentivar si tiene problemas
        ]),
        "riesgo": (0.1, [
            ("b0130c_ahorro_informal", 0.6),
        ]),
        "diversificación": (0.05, [
            ("b0130c_ahorro_informal", 0.8),
        ]),

        # Conceptos técnicos: interés medio para todos
        "interés": (0.4, []),
        "inflación": (0.4, []),
    }

    base, adjustments = weights.get(topic, (0.3, []))
    affinity = base
    for var, adj in adjustments:
        if user_behavior.get(var, 0) == 1:
            affinity += adj

    # Clip a [0.05, 1.0]
    return max(0.05, min(1.0, affinity))


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
    behaviors = load_ecf_behaviors()
    rng = random.Random(7)

    # Mapear user_id -> comportamiento ECF
    user_behavior = {}
    for i, user in enumerate(users):
        b = behaviors.iloc[i]
        user_behavior[user["user_id"]] = {
            "b0130a_ahorro_cualquiera": int(b["b0130a_ahorro_cualquiera"]),
            "b0130b_cuenta_ahorro": int(b["b0130b_cuenta_ahorro"]),
            "b0130c_ahorro_informal": int(b["b0130c_ahorro_informal"]),
            "b1000b_puede_pagar_imprevisto": int(b["b1000b_puede_pagar_imprevisto"]),
            "a0320_no_cubre_gastos": int(b["a0320_no_cubre_gastos"]),
        }

    # Estado: conceptos ya interactuados por usuario
    interacted_concepts = defaultdict(set)

    # Pool por dificultad
    basic = [c for c in contents if c["difficulty"] == "básico"]
    inter = [c for c in contents if c["difficulty"] == "intermedio"]
    adv = [c for c in contents if c["difficulty"] == "avanzado"]

    # Patrón de dificultad para 1500 interacciones siguiendo 60/30/10
    pattern = (["básico"] * 6 + ["intermedio"] * 3 + ["avanzado"] * 1)
    pattern = (pattern * (N_INTERACTIONS // len(pattern) + 1))[:N_INTERACTIONS]
    rng.shuffle(pattern)

    interactions = []
    start = datetime(2025, 9, 1)

    # Cache de afinidades precalculadas para velocidad
    affinity_cache = {}
    for user in users:
        uid = user["user_id"]
        affinity_cache[uid] = {}
        for topic in set(c["topic"] for c in contents):
            affinity_cache[uid][topic] = topic_affinity(user_behavior[uid], topic)

    for i, target_diff in enumerate(pattern):
        if target_diff == "básico":
            pool = basic
        elif target_diff == "intermedio":
            pool = inter
        else:
            pool = adv
        if not pool:
            pool = contents

        # Selección basada en afinidad real del usuario
        # 1) Elegir usuario
        user = rng.choice(users)
        uid = user["user_id"]

        # 2) Filtrar pool por reglas pedagógicas
        qualified = [c for c in pool if user_qualifies(user, c, interacted_concepts)]
        if not qualified:
            qualified = [c for c in basic if user_qualifies(user, c, interacted_concepts)]
        if not qualified:
            user = rng.choice(users)
            qualified = basic

        # 3) Ponderar contenido por afinidad (sin filtro duro, solo modulación)
        # La afinidad modula la probabilidad de elección pero no restringe el pool,
        # para mantener cobertura del catálogo y dejar que el comportamiento
        # module sin sesgar la distribución global.
        weights = [affinity_cache[uid][c["topic"]] for c in qualified]
        total = sum(weights)
        if total > 0:
            probs = [w / total for w in weights]
            content = qualified[random.choices(range(len(qualified)), weights=probs, k=1)[0]]
        else:
            content = rng.choice(qualified)

        k = knowledge_to_num(user["financial_knowledge_level"])
        d = difficulty_to_num(content["difficulty"])

        # Modelo de engagement: sigmoid ajustado por afinidad
        gap = k - d
        affinity_boost = affinity_cache[uid][content["topic"]] - 0.5  # -0.4 a +0.5
        import math
        p_click = 1 / (1 + math.exp(-(1.5 + 0.8 * gap + 0.5 * affinity_boost + rng.uniform(-0.4, 0.4))))

        if rng.random() > p_click:
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

        p_complete = 1 / (1 + math.exp(-(1.0 + 0.7 * gap + 0.3 * affinity_boost + rng.uniform(-0.3, 0.3))))
        completion = 1 if rng.random() < p_complete else round(rng.random() * 0.7, 2)

        if completion == 1:
            q = 1 / (1 + math.exp(-(0.5 + 0.6 * gap + 0.2 * affinity_boost + rng.uniform(-0.3, 0.3))))
        else:
            q = 1 / (1 + math.exp(-(-0.5 + 0.6 * gap + rng.uniform(-0.3, 0.3))))
        quiz = round(q, 3) if rng.random() < 0.6 else None

        event = sample_event(rng, completion if isinstance(completion, float) else 1.0, quiz)

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

    print(f"\nGeneradas {len(interactions)} interacciones realistas en {OUT}")

    # Distribución final
    from collections import Counter
    event_counter = Counter(i["event"] for i in interactions)
    print(f"Eventos: {dict(event_counter)}")

    topic_counter = Counter(cidx[i["content_id"]]["topic"] for i in interactions
                            for cidx in [{c["content_id"]: c for c in contents}]
                            for _ in [0])  # hack


if __name__ == "__main__":
    main()
