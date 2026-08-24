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

N_INTERACTIONS = 23000
USERS = "/Users/veronica/Desktop/tfm/data/users_synthetic.csv"
CONTENTS = "/Users/veronica/Desktop/tfm/data/contents.csv"
ECF = "ecf_2021.csv"  # Debe estar descomprimido en la carpeta actual
OUT = "/Users/veronica/Desktop/tfm/data/interactions_synthetic_realistic_v2.csv"

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
    """Carga las 5 variables de comportamiento del ECF para los usuarios del dataset.

    Estrategia: users_synthetic.csv ahora contiene los 1.916 jóvenes de 18-34
    de la ECF en el mismo orden en que regenerate_users_from_ecf.py los procesa
    (jovenes.reset_index(drop=True), sin muestreo). Por tanto, basta con tomar
    los 1.916 jóvenes en ese mismo orden y extraer las variables de comportamiento.
    """
    print("Cargando ECF 2021...")
    df = pd.read_csv(ECF, sep=";", low_memory=False)
    df['edad'] = 2021 - df['a0400']
    jovenes = df[(df['edad'] >= 18) & (df['edad'] <= 34)].copy().reset_index(drop=True)
    print(f"Jóvenes 18-34 disponibles: {len(jovenes)}")

    # Sin muestreo: el orden coincide con users_synthetic.csv
    behaviors = pd.DataFrame({
        'sampled_index': range(len(jovenes)),
        'b0130a_ahorro_cualquiera': jovenes['b0130a'].fillna(0).astype(int),
        'b0130b_cuenta_ahorro': jovenes['b0130b'].fillna(0).astype(int),
        'b0130c_ahorro_informal': jovenes['b0130c'].fillna(0).astype(int),
        'b1000b_puede_pagar_imprevisto': jovenes['b1000b'].fillna(0).astype(int),
        'a0320_no_cubre_gastos': jovenes['a0320'].fillna(0).astype(int),
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
    """Convierte financial_knowledge_level a un entero 1-3 para uso interno del filtro.

    IMPORTANTE — Tratamiento de NaN y valores vacíos:
    Si el valor es NaN o cadena vacía (jóvenes que omitieron alguna pregunta
    Big3 en la ECF), NO se modifica users_synthetic.csv ni se afirma que su
    conocimiento real es bajo. Aquí se trata como 'sin evidencia suficiente'
    para que el filtro pedagógico del recomendador actúe de forma conservadora:
    ante la duda, asume el menor nivel conocido (1 = bajo) y limita al usuario
    a contenidos básicos/intermedios. Esto es una regla del recomendador, no
    una imputación del dato original.
    """
    if pd.isna(k) or k == "":
        return 1
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
            ("b1000b_puede_pagar_imprevisto", 0.2),  # Si puede pagar, crédito más afín (antes -0.1 bug)
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

        # Conceptos técnicos: interés medio para todos,
        # pero con boost para perfiles financieramente activos
        "interés": (0.4, [
            ("b0130b_cuenta_ahorro", 0.2),  # Tener cuenta de ahorro indica interés en finanzas
        ]),
        "inflación": (0.3, [
            ("a0320_no_cubre_gastos", 0.4),  # Quien no cubre gastos aprende inflación
        ]),
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

    # Patrón de dificultad global (60/30/10) para todo el dataset
    pattern = (["básico"] * 6 + ["intermedio"] * 3 + ["avanzado"] * 1)
    pattern = (pattern * (N_INTERACTIONS // len(pattern) + 1))[:N_INTERACTIONS]
    rng.shuffle(pattern)

    # Cache de afinidades precalculadas para velocidad
    affinity_cache = {}
    for user in users:
        uid = user["user_id"]
        affinity_cache[uid] = {}
        for topic in set(c["topic"] for c in contents):
            affinity_cache[uid][topic] = topic_affinity(user_behavior[uid], topic)

    # Construir cola global: garantizar mínimo 2 interacciones por usuario (para
    # que todos los 1.916 aparezcan en el dataset), y luego distribuir las restantes
    # de forma variable entre 0 y 12 adicionales para mantener ~N_INTERACTIONS totales.
    # Los usuarios sin financial_knowledge_level también participan; el filtro
    # pedagógico los trata conservadoramente (knowledge_to_num -> 1).
    MIN_PER_USER = 2
    MAX_PER_USER = 14
    MAX_ADDITIONAL = MAX_PER_USER - MIN_PER_USER  # 12 adicionales

    n_users = len(users)
    user_ids = [u["user_id"] for u in users]  # lista separada para evitar agotar el iterador
    user_interaction_counts = {uid: MIN_PER_USER for uid in user_ids}
    total_planned = MIN_PER_USER * n_users  # mínimo garantizado

    # Distribuir las interacciones restantes (N_INTERACTIONS - mínimo total)
    remaining_total = N_INTERACTIONS - total_planned
    if remaining_total < 0:
        remaining_total = 0

    # Asignar adicionales variables (0..MAX_ADDITIONAL) aleatoriamente hasta agotar remaining_total
    additional_counts = {uid: 0 for uid in user_ids}
    claimed = 0
    while claimed < remaining_total:
        uid = user_ids[rng.randrange(n_users)]  # randrange(n) devuelve [0, n), evita off-by-one
        if additional_counts[uid] < MAX_ADDITIONAL:
            additional_counts[uid] += 1
            claimed += 1

    for uid in user_ids:
        user_interaction_counts[uid] += additional_counts[uid]

    interactions = []
    start = datetime(2025, 9, 1)
    interaction_counter = 0
    pattern_idx = 0

    # Para mantener la lógica idéntica, procesamos usuario por usuario.
    # Cada usuario consume una dificultad extraída secuencialmente del patrón barajado.
    # Cada usuario tiene su propia semilla temporal (determinista por uid)
    # para que el split cronológico en evaluate_models sea válido.
    for user in users:
        uid = user["user_id"]
        rng_user = random.Random(int(hash(uid) & 0xffffffff))
        # Base temporal por usuario: dentro de los primeros 60 días para todos
        base_day = rng_user.uniform(0, 60)
        target_n = user_interaction_counts.get(uid, 0)
        user_intra_counter = 0
        for _ in range(target_n):
            if pattern_idx >= len(pattern):
                pattern_idx = 0  # wrap-around defensivo
            target_diff = pattern[pattern_idx]
            pattern_idx += 1

            if target_diff == "básico":
                pool = basic
            elif target_diff == "intermedio":
                pool = inter
            else:
                pool = adv
            if not pool:
                pool = contents

            # Filtrar pool por reglas pedagógicas
            qualified = [c for c in pool if user_qualifies(user, c, interacted_concepts)]
            if not qualified:
                qualified = [c for c in basic if user_qualifies(user, c, interacted_concepts)]
            if not qualified:
                qualified = basic

            # Ponderar contenido por afinidad POR CONTENIDO (no por topic).
            # Esto permite que dentro del mismo topic los contenidos se diferencien
            # por dificultad, tipo (inversión vs no) y características del usuario.
            weights = []
            for c in qualified:
                base = affinity_cache[uid][c["topic"]]
                # Boost por dificultad (usuarios con conocimiento alto prefieren avanzados)
                diff_boost = {"básico": 0.0, "intermedio": 0.1, "avanzado": 0.3}.get(c["difficulty"], 0)
                # Penalizar inversión avanzada si no tiene experiencia inversora
                invest_penalty = 0
                if c["is_investment_related"] == "si" and c["difficulty"] == "avanzado":
                    invest_penalty = -0.2
                weights.append(max(0.05, base + diff_boost + invest_penalty))
            total = sum(weights)
            if total > 0:
                probs = [w / total for w in weights]
                content = qualified[random.choices(range(len(qualified)), weights=probs, k=1)[0]]
            else:
                content = rng.choice(qualified)

            k = knowledge_to_num(user["financial_knowledge_level"])
            d = difficulty_to_num(content["difficulty"])

            gap = k - d
            # El affinity_boost se mantiene coherente con la afinidad por topic
            affinity_boost = affinity_cache[uid][content["topic"]] - 0.5
            import math
            p_click = 1 / (1 + math.exp(-(1.5 + 0.8 * gap + 0.5 * affinity_boost + rng.uniform(-0.4, 0.4))))

            if rng.random() > p_click:
                interactions.append({
                    "interaction_id": f"I{interaction_counter + 1:05d}",
                    "user_id": uid,
                    "content_id": content["content_id"],
                    "event": "viewed",
                    "score": round(0.1 + rng_user.random() * 0.2, 3),
                    "completion_rate": round(rng_user.random() * 0.1, 3),
                    "quiz_score": "",
                    "timestamp": (start + timedelta(days=base_day + user_intra_counter * 0.5, hours=rng_user.uniform(0, 24))).isoformat(),
                })
                interaction_counter += 1
                user_intra_counter += 1
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
                          + 0.2 * rng_user.uniform(0.3, 0.9), 3)

            interactions.append({
                "interaction_id": f"I{interaction_counter + 1:05d}",
                "user_id": uid,
                "content_id": content["content_id"],
                "event": event,
                "score": score,
                "completion_rate": completion if isinstance(completion, float) else 1.0,
                "quiz_score": quiz if quiz is not None else "",
                "timestamp": (start + timedelta(days=base_day + user_intra_counter * 0.5, hours=rng_user.uniform(0, 24))).isoformat(),
            })
            interaction_counter += 1
            user_intra_counter += 1

            topic = content["topic"]
            for cid in TOPIC_TO_CONCEPTS.get(topic, []):
                interacted_concepts[uid].add(cid)

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
