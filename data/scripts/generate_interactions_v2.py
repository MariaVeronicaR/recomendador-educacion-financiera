import numpy as np
import pandas as pd
import random
from collections import Counter

def topic_affinity(user_behavior, topic):
    weights = {
        "planificacion": (0.8, []),
        "ahorro": (0.7, [("b0130a_ahorro_cualquiera", 0.4)]),
        "fraude": (0.7, []),
        "deuda": (0.1, [("a0320_no_cubre_gastos", 1.5)]),
        "credito": (0.1, [("a0320_no_cubre_gastos", 1.2)]),
        "prestamos": (0.1, [("a0320_no_cubre_gastos", 1.0)]),
        "tarjetas": (0.2, [("a0320_no_cubre_gastos", 0.6)]),
        "cuentas bancarias": (0.3, [("b0130b_cuenta_ahorro", 1.0)]),
        "hipotecas": (0.1, [("b0130b_cuenta_ahorro", 0.6)]),
        "inversion": (0.05, [("b0130c_ahorro_informal", 1.5), ("b0130b_cuenta_ahorro", 0.4)]),
        "riesgo": (0.1, [("b0130c_ahorro_informal", 1.0)]),
        "diversificacion": (0.05, [("b0130c_ahorro_informal", 1.5)]),
        "interes": (0.4, [("b0130b_cuenta_ahorro", 0.4)]),
        "inflacion": (0.3, [("a0320_no_cubre_gastos", 0.6)]),
    }
    base, adj = weights.get(topic, (0.3, []))
    affinity = base
    for var, w in adj:
        if user_behavior.get(var, 0) == 1:
            affinity = affinity + w
    return max(0.05, min(1.0, affinity))

users = pd.read_csv('/Users/veronica/Desktop/tfm/data/users_synthetic.csv')
topic_list = [
    "planificacion", "ahorro", "fraude", "deuda", "credito", "prestamos",
    "tarjetas", "cuentas bancarias", "hipotecas", "inversion", "riesgo",
    "diversificacion", "interes", "inflacion"
]

profile_cols = {
    "b0130a_ahorro_cualquiera": lambda row: 1 if row.get("financial_behavior_level") in ["frecuente", "alto"] else 0,
    "b0130b_cuenta_ahorro": lambda row: 1 if row.get("financial_behavior_level") in ["frecuente", "alto"] else 0,
    "b0130c_ahorro_informal": lambda row: 1 if row.get("financial_knowledge_level") == "alto" else 0,
    "b1000b_puede_pagar_imprevisto": lambda row: 1,
    "a0320_no_cubre_gastos": lambda row: 1 if row.get("financial_knowledge_level") == "bajo" else 0,
}

def get_profile(user_row):
    return {k: fn(user_row) for k, fn in profile_cols.items()}

N_INTERACTIONS = 23000
MIN_PER_USER = 10
MAX_PER_USER = 14
n_users = len(users)
rng = random.Random(42)

user_interaction_counts = {uid: MIN_PER_USER for uid in users['user_id']}
total_planned = MIN_PER_USER * n_users
remaining = N_INTERACTIONS - total_planned
MAX_ADD = MAX_PER_USER - MIN_PER_USER

if remaining > 0:
    additional = {uid: 0 for uid in users['user_id']}
    idx = 0
    while remaining > 0:
        uid = users['user_id'].iloc[idx % n_users]
        if additional[uid] < MAX_ADD:
            additional[uid] = additional[uid] + 1
            remaining = remaining - 1
        idx = idx + 1
    user_interaction_counts = {uid: MIN_PER_USER + additional[uid] for uid in users['user_id']}

difficulty_pool = ["basico"] * 6 + ["intermedio"] * 3 + ["avanzado"] * 1
rng_diff = random.Random(42)
diff_per_user = {}
for uid, cnt in user_interaction_counts.items():
    if cnt <= len(difficulty_pool):
        diff_per_user[uid] = rng_diff.sample(difficulty_pool, k=cnt)
    else:
        sampled = rng_diff.sample(difficulty_pool, k=len(difficulty_pool))
        extra = rng_diff.choices(difficulty_pool, k=cnt - len(difficulty_pool))
        diff_per_user[uid] = sampled + extra

interactions = []
iid_counter = 0
rng_choice = np.random.RandomState(123)
noise_rng = np.random.RandomState(42)

for uid in users['user_id']:
    user_row = users[users['user_id'] == uid].iloc[0]
    profile = get_profile(user_row)
    diffs = diff_per_user[uid]
    for d_idx in range(len(diffs)):
        weights = np.array([topic_affinity(profile, t) for t in topic_list])
        weights = weights / weights.sum()
        topic_idx = rng_choice.choice(len(weights), p=weights)
        topic = topic_list[topic_idx]
        affinity = topic_affinity(profile, topic)
        bias = (affinity - 0.5) * 1.5
        prob_complete = 1.0 / (1.0 + np.exp(-(0.5 + bias)))
        completed = 1 if noise_rng.random() < prob_complete else 0
        if completed == 1:
            event = "quiz_passed" if noise_rng.random() < 0.6 else "completed"
        else:
            event = "viewed" if noise_rng.random() < 0.85 else "disliked"
        score_base = completed * affinity
        noise_score = noise_rng.uniform(0, 0.15)
        score = min(1.0, score_base + noise_score) if completed else noise_score
        relevant = int((completed == 1) and (affinity >= 0.5))
        interactions.append({
            "interaction_id": f"I{iid_counter+1:05d}",
            "user_id": uid,
            "content_id": f"C{noise_rng.randint(100, 999):03d}",
            "topic": topic,
            "affinity": round(affinity, 4),
            "completion": completed,
            "relevant": relevant,
            "event": event,
            "score": round(score, 4),
            "timestamp": f"2025-{(d_idx % 30)+1:02d}-{(d_idx * 2) % 24:02d}:00:00",
        })
        iid_counter = iid_counter + 1

df = pd.DataFrame(interactions)
out_path = '/Users/veronica/Desktop/tfm/data/interactions_synthetic_v2_validated.csv'
df.to_csv(out_path, index=False)

print("=" * 70)
print("GENERADAS {0} INTERACCIONES".format(len(df)))
print("=" * 70)

print()
print("=== VALIDACION 1: Relevancia ===")
print("Porcentaje relevantes: {0:.1f}%".format(df['relevant'].mean() * 100))
print()

print("=== VALIDACION 2: Score ===")
print("Score medio: {0:.3f}".format(df['score'].mean()))
print("Score >= 0.5: {0:.1f}%".format((df['score'] >= 0.5).mean() * 100))
print("Score medio si relevant=1: {0:.3f}".format(df[df['relevant']==1]['score'].mean()))
print("Score medio si relevant=0: {0:.3f}".format(df[df['relevant']==0]['score'].mean()))
print()

# KL entre perfiles extremos (ahorrador vs aleatorio como proxy)
np.random.seed(42)
ahorrador_sample = df[df['affinity'] > 0.65].sample(1000, random_state=42)
inversor_sample = df.sample(1000, random_state=43)
dist_a = ahorrador_sample['topic'].value_counts(normalize=True)
dist_b = inversor_sample['topic'].value_counts(normalize=True)
all_t = sorted(set(dist_a.index) | set(dist_b.index))
P = np.array([dist_a.get(t, 0) for t in all_t])
Q = np.array([dist_b.get(t, 0) for t in all_t])
kl_val = sum(p * np.log2(p / q) for p, q in zip(P, Q) if p > 0 and q > 0)
print("=== VALIDACION 3: KL entre perfiles (afinidad>0.65 vs aleatorio) ===")
print("KL estimado: {0:.4f} bits".format(kl_val))
print("Top-5 afinidad>0.65: {0}".format(dict(dist_a.head(5))))
print("Top-5 aleatorio: {0}".format(dict(dist_b.head(5))))
print()

df['q_affin'] = pd.qcut(df['affinity'], q=4, duplicates='drop', labels=['Q1(baja)','Q2','Q3','Q4(alta)'])
ct = df.groupby('q_affin', observed=True).agg(
    completion_rate=('completion', 'mean'),
    relevance_rate=('relevant', 'mean'),
)
print("=== VALIDACION 4: Completion y relevance por cuartil de afinidad ===")
print(ct.round(3))
print()

print("=== VALIDACION 5: Eventos ===")
print(df['event'].value_counts(normalize=True).round(3).to_dict())
print()

print("=== VALIDACION 6: Top 10 topics ===")
print(df['topic'].value_counts(normalize=True).head(10).round(3).to_dict())
print()

print("=== VALIDACION 7: Resumen ===")
print("Total: {0}".format(len(df)))
print("Users: {0}, Items unicos: {1}".format(df['user_id'].nunique(), df['content_id'].nunique()))
print("Relevantes: {0:.1f}%".format(df['relevant'].mean() * 100))
print("Completion: {0:.1f}%".format(df['completion'].mean() * 100))
print("Quiz_passed: {0:.1f}%".format((df['event']=='quiz_passed').mean() * 100))
print("Disliked: {0:.1f}%".format((df['event']=='disliked').mean() * 100))
