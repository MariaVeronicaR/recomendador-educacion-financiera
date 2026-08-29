"""
Harness de evaluación para la comparativa de modelos de recomendación.

Define el protocolo común de evaluación y las métricas, y valida el harness con
los tres baselines triviales (Most-Popular, Content-Based, KG/reglas). Los
modelos de ML (BPR-MF, NeuMF, feature-aware NeuMF) se añaden como funciones que
devuelven un ranking por usuario y se evalúan con la misma infraestructura.

Protocolo (docs/Comparativa_modelos_recomendacion.md §4):
  - Ground truth de ranking: `completed` = relevante (etiqueta A).
  - Split temporal GTS: primeros 9 meses train, últimos 3 test.
  - Dos escenarios: warm (con historial en train) y cold start (sin historial).
  - Métricas: NDCG@k, Precision@k, Recall@k, MRR (k=5,10) + coherencia
    pedagógica sobre el ranking crudo (sin filtro).
  - Rigor: varias seeds, media ± desviación, Wilcoxon pareado.

Uso:
    python3 data/scripts/evaluate_models.py [--seed S] [--k 5 10] [--models ...]
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
DATA_DIR = PROJECT_ROOT / "data"

# Ventana temporal (coincide con el generador: 2025-09-01, 365 días)
WINDOW_START = pd.Timestamp("2025-09-01")
TRAIN_MONTHS = 9
TEST_MONTHS = 3
TRAIN_END = WINDOW_START + pd.DateOffset(months=TRAIN_MONTHS)  # 2026-06-01


# ---------------------------------------------------------------------------
# Carga de datos
# ---------------------------------------------------------------------------
def load_data():
    interactions = pd.read_csv(DATA_DIR / "interactions_synthetic.csv")
    users = pd.read_csv(DATA_DIR / "users_synthetic.csv")
    contents = pd.read_csv(DATA_DIR / "contents.csv")
    concepts = pd.read_csv(DATA_DIR / "concepts.csv")
    ccm = pd.read_csv(DATA_DIR / "content_concept_map.csv")
    prereqs = pd.read_csv(DATA_DIR / "prerequisites.csv")

    interactions["ts"] = pd.to_datetime(interactions["timestamp"])

    # conceptos por contenido
    concepts_of_content = ccm.groupby("content_id")["concept_id"].apply(list).to_dict()
    # prerrequisitos por concepto
    prereq_of_concept = prereqs.groupby("concept_id")["prerequisite_concept_id"].apply(list).to_dict()
    # dificultad ordinal -> numérica (para el baseline KG)
    diff_map = {"básico": 0, "intermedio": 1, "avanzado": 2}
    content_diff = contents.set_index("content_id")["difficulty"].map(diff_map).to_dict()

    return {
        "interactions": interactions,
        "users": users,
        "contents": contents,
        "concepts": concepts,
        "ccm": ccm,
        "prereqs": prereqs,
        "concepts_of_content": concepts_of_content,
        "prereq_of_concept": prereq_of_concept,
        "content_diff": content_diff,
    }


# ---------------------------------------------------------------------------
# Split temporal + escenarios
# ---------------------------------------------------------------------------
def make_split(data):
    """Divide en train/test por punto temporal y separa warm / cold start."""
    inter = data["interactions"]
    train = inter[inter["ts"] < TRAIN_END]
    test = inter[inter["ts"] >= TRAIN_END]

    # Usuarios con historial en train (warm) vs sin historial (cold start).
    # La etiqueta cold_start de users_synthetic.csv es sobre TODO el dataset;
    # aquí la re-derivamos sobre train para que el escenario sea reproducible
    # con el split temporal.
    train_users = set(train["user_id"].unique())
    test_users = set(test["user_id"].unique())

    # Evaluación de ranking: usuarios con >=1 completado en test (ground truth).
    test_comp = test[test["completed"]]
    eval_users = set(test_comp["user_id"].unique())

    warm_eval = sorted(u for u in eval_users if u in train_users)
    cold_eval = sorted(u for u in eval_users if u not in train_users)

    return {
        "train": train,
        "test": test,
        "train_users": train_users,
        "eval_users": eval_users,
        "warm_eval": warm_eval,
        "cold_eval": cold_eval,
    }


# ---------------------------------------------------------------------------
# Maestría de conceptos (para coherencia pedagógica y baseline KG)
# ---------------------------------------------------------------------------
def compute_mastery(train, data):
    """Concepto dominado si el usuario completó >=1 contenido en train que lo cubre."""
    completed = train[train["completed"]]
    mastery = {}
    for uid, g in completed.groupby("user_id"):
        concepts = set()
        for cid in g["content_id"]:
            concepts.update(data["concepts_of_content"].get(cid, []))
        mastery[uid] = concepts
    return mastery


def content_is_coherent(cid, mastered_concepts, data):
    """Un contenido respeta prerrequisitos si, para cada concepto que cubre, el
    usuario domina al menos un prerrequisito de ese concepto. Conceptos sin
    prerrequisitos siempre son coherentes."""
    for k in data["concepts_of_content"].get(cid, []):
        prereqs = data["prereq_of_concept"].get(k, [])
        if prereqs and not (mastered_concepts & set(prereqs)):
            return False
    return True


# ---------------------------------------------------------------------------
# Métricas de ranking
# ---------------------------------------------------------------------------
def dcg(ranks, k):
    """DCG@k sobre una lista de 0/1 (relevancia) ya ordenada."""
    return sum(rel / math.log2(i + 2) for i, rel in enumerate(ranks[:k]))


def ndcg_at_k(pred, truth, k):
    """pred: lista ordenada de content_ids; truth: set de relevantes."""
    ranks = [1 if c in truth else 0 for c in pred[:k]]
    if not truth:
        return 0.0
    idcg = dcg([1] * min(len(truth), k), k)
    return dcg(ranks, k) / idcg if idcg > 0 else 0.0


def precision_at_k(pred, truth, k):
    if k == 0:
        return 0.0
    return sum(1 for c in pred[:k] if c in truth) / k


def recall_at_k(pred, truth, k):
    if not truth:
        return 0.0
    return sum(1 for c in pred[:k] if c in truth) / len(truth)


def mrr(pred, truth):
    for i, c in enumerate(pred):
        if c in truth:
            return 1.0 / (i + 1)
    return 0.0


def evaluate_ranking(pred, truth, ks=(5, 10)):
    """Métricas de ranking para un usuario. pred: lista ordenada; truth: set."""
    return {
        **{f"ndcg@{k}": ndcg_at_k(pred, truth, k) for k in ks},
        **{f"precision@{k}": precision_at_k(pred, truth, k) for k in ks},
        **{f"recall@{k}": recall_at_k(pred, truth, k) for k in ks},
        "mrr": mrr(pred, truth),
    }


def evaluate_pedagogy(pred, mastered_concepts, data, ks=(5, 10)):
    """% de recomendaciones del ranking crudo que respetan prerrequisitos."""
    return {
        f"pedagogy@{k}": (
            sum(1 for c in pred[:k] if content_is_coherent(c, mastered_concepts, data)) / k
            if k > 0 else 0.0
        )
        for k in ks
    }


# ---------------------------------------------------------------------------
# Baselines
# ---------------------------------------------------------------------------
def baseline_most_popular(train, data):
    """Ranking global por frecuencia de interacción en train (mismo para todos)."""
    counts = train["content_id"].value_counts()
    all_ids = list(data["contents"]["content_id"])
    # Contenidos sin interacción van al final (orden estable)
    ranked = list(counts.index) + [c for c in all_ids if c not in counts.index]
    return ranked


def baseline_content_based(users, data):
    """Similitud coseno entre el perfil de intereses del usuario y el topic del contenido."""
    # Vector de intereses por usuario (topic -> valor)
    user_interests = {}
    for _, row in users.iterrows():
        user_interests[row["user_id"]] = json.loads(row["interests"])

    # Vector de topic por contenido (one-hot)
    topics = sorted(data["contents"]["topic"].unique())
    content_vec = {}
    for _, row in data["contents"].iterrows():
        v = np.zeros(len(topics))
        v[topics.index(row["topic"])] = 1.0
        content_vec[row["content_id"]] = v

    def rank_for_user(uid):
        ui = user_interests.get(uid, {})
        uvec = np.array([ui.get(t, 0.0) for t in topics])
        norm_u = np.linalg.norm(uvec)
        if norm_u == 0:
            return list(data["contents"]["content_id"])
        scores = {
            cid: float(np.dot(uvec, cvec) / (norm_u * np.linalg.norm(cvec)))
            for cid, cvec in content_vec.items()
        }
        return sorted(scores, key=scores.get, reverse=True)

    return rank_for_user


def baseline_kg_rules(train, data, mastery):
    """Recomienda contenidos cuyos prerrequisitos están cubiertos, ordenados por dificultad."""
    all_ids = list(data["contents"]["content_id"])

    def rank_for_user(uid):
        mastered = mastery.get(uid, set())
        coherent = [c for c in all_ids if content_is_coherent(c, mastered, data)]
        incoherent = [c for c in all_ids if c not in coherent]
        coherent.sort(key=lambda c: data["content_diff"].get(c, 0))
        incoherent.sort(key=lambda c: data["content_diff"].get(c, 0))
        return coherent + incoherent

    return rank_for_user


# ---------------------------------------------------------------------------
# BPR-MF (Bayesian Personalized Ranking, Matrix Factorization)
# ---------------------------------------------------------------------------
def train_bpr(train, data, dim=32, epochs=30, lr=0.05, reg=0.01, seed=42):
    """Entrena BPR-MF con SGD sobre pares (positivo, negativo).

    Positivos: interacciones en train (lo que un sistema real ve: clics, no
    completados). Devuelve user_factors, item_factors, item_bias y los mapeos
    de id -> índice.
    """
    rng = np.random.default_rng(seed)
    user_ids = sorted(train["user_id"].unique())
    item_ids = list(data["contents"]["content_id"])
    u_idx = {u: i for i, u in enumerate(user_ids)}
    i_idx = {c: i for i, c in enumerate(item_ids)}

    n_users, n_items = len(user_ids), len(item_ids)
    U = rng.normal(0, 0.1, (n_users, dim))
    V = rng.normal(0, 0.1, (n_items, dim))
    bias = np.zeros(n_items)

    # Positivos por usuario (interacciones en train)
    pos = {}
    for uid, g in train.groupby("user_id"):
        pos[u_idx[uid]] = [i_idx[c] for c in g["content_id"]]

    for epoch in range(epochs):
        # Muestrear un lote de pares (u, i+, i-)
        batch = 512
        for _ in range(batch):
            u = int(rng.integers(n_users))
            if not pos[u]:
                continue
            i = int(rng.choice(pos[u]))
            j = int(rng.integers(n_items))
            x = np.dot(U[u], V[i]) + bias[i] - np.dot(U[u], V[j]) - bias[j]
            sig = 1.0 / (1.0 + math.exp(-x))
            # Gradientes BPR
            dU = (1 - sig) * (V[i] - V[j]) - reg * U[u]
            dVi = (1 - sig) * U[u] - reg * V[i]
            dVj = -(1 - sig) * U[u] - reg * V[j]
            U[u] += lr * dU
            V[i] += lr * dVi
            V[j] += lr * dVj
            bias[i] += lr * (1 - sig)
            bias[j] -= lr * (1 - sig)

    return {"U": U, "V": V, "bias": bias, "u_idx": u_idx, "i_idx": i_idx,
            "item_ids": item_ids}


def baseline_bpr_mf(train, data, seed=42):
    """Ranking por score BPR. Usuarios sin factores (cold) -> fallback popularidad."""
    model = train_bpr(train, data, seed=seed)
    U, V, bias = model["U"], model["V"], model["bias"]
    u_idx, i_idx = model["u_idx"], model["i_idx"]
    item_ids = model["item_ids"]

    # Fallback popularidad para usuarios sin factores (cold start)
    pop_rank = baseline_most_popular(train, data)

    def rank_for_user(uid):
        if uid not in u_idx:
            return pop_rank
        u = u_idx[uid]
        scores = np.dot(V, U[u]) + bias
        order = np.argsort(-scores)
        return [item_ids[i] for i in order]

    return rank_for_user


# ---------------------------------------------------------------------------
# NeuMF (Neural Matrix Factorization, He et al. 2017)
# ---------------------------------------------------------------------------
def train_neumf(train, data, dim=16, layers=(32, 16, 8), epochs=20, lr=0.005,
                batch=256, neg_per_pos=4, seed=42):
    """Entrena NeuMF (GMF + MLP) con BCE y muestreo negativo sobre interacciones.

    Devuelve el modelo y los mapeos id -> índice. Los usuarios sin interacciones
    en train no tienen embedding y se tratan como cold start (fallback).
    """
    import torch
    import torch.nn as nn

    torch.manual_seed(seed)
    user_ids = sorted(train["user_id"].unique())
    item_ids = list(data["contents"]["content_id"])
    u_idx = {u: i for i, u in enumerate(user_ids)}
    i_idx = {c: i for i, c in enumerate(item_ids)}
    n_users, n_items = len(user_ids), len(item_ids)

    # Positivos por usuario
    pos = {}
    for uid, g in train.groupby("user_id"):
        pos[u_idx[uid]] = [i_idx[c] for c in g["content_id"]]

    class NeuMF(nn.Module):
        def __init__(self):
            super().__init__()
            self.user_gmf = nn.Embedding(n_users, dim)
            self.item_gmf = nn.Embedding(n_items, dim)
            self.user_mlp = nn.Embedding(n_users, layers[0])
            self.item_mlp = nn.Embedding(n_items, layers[0])
            mlp = [nn.Linear(2 * layers[0], layers[1]), nn.ReLU()]
            for i in range(1, len(layers) - 1):
                mlp.append(nn.Linear(layers[i], layers[i + 1]))
                mlp.append(nn.ReLU())
            self.mlp = nn.Sequential(*mlp)
            self.gmf_out = nn.Linear(dim, 1)
            self.mlp_out = nn.Linear(layers[-1], 1)
            self.final = nn.Linear(2, 1)

        def forward(self, u, i):
            gmf = self.user_gmf(u) * self.item_gmf(i)
            gmf_score = self.gmf_out(gmf)
            mlp_in = torch.cat([self.user_mlp(u), self.item_mlp(i)], dim=-1)
            mlp_score = self.mlp_out(self.mlp(mlp_in))
            out = torch.cat([gmf_score, mlp_score], dim=-1)
            return torch.sigmoid(self.final(out)).squeeze(-1)

    model = NeuMF()
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    loss_fn = nn.BCELoss()

    rng = np.random.default_rng(seed)
    all_items = list(range(n_items))
    for epoch in range(epochs):
        model.train()
        total_loss = 0.0
        n_batches = 0
        for _ in range(batch):
            # Muestrear un lote de (u, i+) y negativos
            us, is_pos, is_neg = [], [], []
            for _ in range(batch // (neg_per_pos + 1)):
                u = int(rng.integers(n_users))
                if not pos[u]:
                    continue
                i = int(rng.choice(pos[u]))
                us.append(u)
                is_pos.append(i)
                for _ in range(neg_per_pos):
                    j = int(rng.integers(n_items))
                    us.append(u)
                    is_neg.append(j)
            if not us:
                continue
            u_t = torch.tensor(us)
            i_pos_t = torch.tensor(is_pos)
            i_neg_t = torch.tensor(is_neg)
            # Positivos: target 1; negativos: target 0
            y = torch.cat([torch.ones(len(is_pos)), torch.zeros(len(is_neg))])
            idx = torch.cat([i_pos_t, i_neg_t])
            pred = model(u_t, idx)
            loss = loss_fn(pred, y)
            opt.zero_grad()
            loss.backward()
            opt.step()
            total_loss += loss.item()
            n_batches += 1
        if (epoch + 1) % 5 == 0:
            print(f"    [NeuMF] epoch {epoch+1}/{epochs} loss={total_loss/max(n_batches,1):.4f}")

    return {"model": model, "u_idx": u_idx, "i_idx": i_idx, "item_ids": item_ids}


def baseline_neumf(train, data, seed=42):
    """Ranking por score NeuMF. Usuarios sin embedding (cold) -> fallback popularidad."""
    import torch

    trained = train_neumf(train, data, seed=seed)
    model = trained["model"]
    u_idx, i_idx = trained["u_idx"], trained["i_idx"]
    item_ids = trained["item_ids"]
    n_items = len(item_ids)
    pop_rank = baseline_most_popular(train, data)

    model.eval()
    with torch.no_grad():
        all_items = torch.arange(n_items)
        # Precomputar scores por usuario (solo los que tienen embedding)
        scores_by_user = {}
        for uid, ui in u_idx.items():
            u_t = torch.full((n_items,), ui, dtype=torch.long)
            scores = model(u_t, all_items).numpy()
            scores_by_user[uid] = scores

    def rank_for_user(uid):
        if uid not in scores_by_user:
            return pop_rank
        order = np.argsort(-scores_by_user[uid])
        return [item_ids[i] for i in order]

    return rank_for_user


# ---------------------------------------------------------------------------
# Feature-aware NeuMF (modelo propuesto)
# ---------------------------------------------------------------------------
def build_user_features(users, data):
    """Construye un vector de features numérico por usuario (del cuestionario).

    Features: theta, risk, activity, age (z-score) + one-hot de sex, educación,
    empleo, nivel de conocimiento + vector de intereses por topic. Devuelve
    (dict uid->vector, n_features).
    """
    topics = sorted(data["contents"]["topic"].unique())
    cat_cols = {
        "sex": ["hombre", "mujer"],
        "education_level": ["posgrado", "universidad", "bachillerato", "secundaria", "primaria"],
        "employment_status": ["empleado", "estudiante", "desempleado", "autónomo"],
        "knowledge_level": ["bajo", "medio", "alto"],
    }
    num_cols = ["theta", "risk", "activity", "age"]

    # Normalización z-score de las numéricas
    num_stats = {}
    for c in num_cols:
        s = users[c]
        num_stats[c] = (s.mean(), s.std() if s.std() > 0 else 1.0)

    # Intereses por usuario (topic -> valor)
    interests = {}
    for _, row in users.iterrows():
        interests[row["user_id"]] = json.loads(row["interests"])

    feat = {}
    for _, row in users.iterrows():
        uid = row["user_id"]
        v = []
        for c in num_cols:
            mu, sd = num_stats[c]
            v.append((row[c] - mu) / sd)
        for col, cats in cat_cols.items():
            for cat in cats:
                v.append(1.0 if row[col] == cat else 0.0)
        for t in topics:
            v.append(interests.get(uid, {}).get(t, 0.0))
        feat[uid] = np.array(v, dtype=np.float32)

    n_features = len(next(iter(feat.values())))
    return feat, n_features


def train_feature_aware_neumf(train, users, data, dim=16, layers=(32, 16, 8),
                              epochs=20, lr=0.005, batch=256, neg_per_pos=4, seed=42):
    """Entrena Feature-aware NeuMF: GMF + MLP, donde el MLP recibe además las
    features del usuario. Los usuarios sin historial (cold) comparten un embedding
    de cold start y usan solo sus features para predecir."""
    import torch
    import torch.nn as nn

    torch.manual_seed(seed)
    user_ids = sorted(train["user_id"].unique())
    item_ids = list(data["contents"]["content_id"])
    u_idx = {u: i for i, u in enumerate(user_ids)}
    i_idx = {c: i for i, c in enumerate(item_ids)}
    n_users, n_items = len(user_ids), len(item_ids)
    COLD_IDX = n_users  # embedding compartido para usuarios sin historial

    feat, n_features = build_user_features(users, data)

    # Positivos por usuario
    pos = {}
    for uid, g in train.groupby("user_id"):
        pos[u_idx[uid]] = [i_idx[c] for c in g["content_id"]]

    class FeatureAwareNeuMF(nn.Module):
        def __init__(self):
            super().__init__()
            self.user_gmf = nn.Embedding(n_users + 1, dim)
            self.item_gmf = nn.Embedding(n_items, dim)
            self.user_mlp = nn.Embedding(n_users + 1, layers[0])
            self.item_mlp = nn.Embedding(n_items, layers[0])
            mlp = [nn.Linear(2 * layers[0] + n_features, layers[1]), nn.ReLU()]
            for i in range(1, len(layers) - 1):
                mlp.append(nn.Linear(layers[i], layers[i + 1]))
                mlp.append(nn.ReLU())
            self.mlp = nn.Sequential(*mlp)
            self.gmf_out = nn.Linear(dim, 1)
            self.mlp_out = nn.Linear(layers[-1], 1)
            self.final = nn.Linear(2, 1)

        def forward(self, u, i, f):
            gmf = self.user_gmf(u) * self.item_gmf(i)
            gmf_score = self.gmf_out(gmf)
            mlp_in = torch.cat([self.user_mlp(u), self.item_mlp(i), f], dim=-1)
            mlp_score = self.mlp_out(self.mlp(mlp_in))
            out = torch.cat([gmf_score, mlp_score], dim=-1)
            return torch.sigmoid(self.final(out)).squeeze(-1)

    model = FeatureAwareNeuMF()
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    loss_fn = nn.BCELoss()

    rng = np.random.default_rng(seed)
    for epoch in range(epochs):
        model.train()
        total_loss, n_batches = 0.0, 0
        for _ in range(batch):
            us, is_pos, is_neg = [], [], []
            for _ in range(batch // (neg_per_pos + 1)):
                u = int(rng.integers(n_users))
                if not pos[u]:
                    continue
                i = int(rng.choice(pos[u]))
                us.append(u)
                is_pos.append(i)
                for _ in range(neg_per_pos):
                    us.append(u)
                    is_neg.append(int(rng.integers(n_items)))
            if not us:
                continue
            u_t = torch.tensor(us)
            idx = torch.tensor(is_pos + is_neg)
            y = torch.cat([torch.ones(len(is_pos)), torch.zeros(len(is_neg))])
            # Features del usuario (por índice de train)
            f_t = torch.stack([torch.tensor(feat[user_ids[u]]) for u in us])
            pred = model(u_t, idx, f_t)
            loss = loss_fn(pred, y)
            opt.zero_grad()
            loss.backward()
            opt.step()
            total_loss += loss.item()
            n_batches += 1
        if (epoch + 1) % 5 == 0:
            print(f"    [FeatNeuMF] epoch {epoch+1}/{epochs} loss={total_loss/max(n_batches,1):.4f}")

    return {"model": model, "u_idx": u_idx, "i_idx": i_idx, "item_ids": item_ids,
            "feat": feat, "COLD_IDX": COLD_IDX}


def baseline_feature_aware_neumf(train, users, data, seed=42):
    """Ranking por score Feature-aware NeuMF. Cold start usa features + embedding cold."""
    import torch

    trained = train_feature_aware_neumf(train, users, data, seed=seed)
    model = trained["model"]
    u_idx, i_idx = trained["u_idx"], trained["i_idx"]
    item_ids = trained["item_ids"]
    feat = trained["feat"]
    COLD_IDX = trained["COLD_IDX"]
    n_items = len(item_ids)

    model.eval()
    with torch.no_grad():
        all_items = torch.arange(n_items)
        # Precomputar scores por usuario (train: embedding propio; cold: embedding cold + features)
        scores_by_user = {}
        for uid, f in feat.items():
            ui = u_idx.get(uid, COLD_IDX)
            u_t = torch.full((n_items,), ui, dtype=torch.long)
            f_t = torch.tensor(f).unsqueeze(0).expand(n_items, -1)
            scores = model(u_t, all_items, f_t).numpy()
            scores_by_user[uid] = scores

    def rank_for_user(uid):
        if uid not in scores_by_user:
            return baseline_most_popular(train, data)
        order = np.argsort(-scores_by_user[uid])
        return [item_ids[i] for i in order]

    return rank_for_user


# ---------------------------------------------------------------------------
# Feature-aware NeuMF + KG post-filtro (sistema completo, modelo 7)
# ---------------------------------------------------------------------------
def baseline_feature_aware_neumf_kg(train, users, data, seed=42):
    """Feature-aware NeuMF + post-filtro pedagógico: reordena el ranking crudo
    moviendo los contenidos incoherentes (prerrequisitos no cubiertos) al final."""
    base = baseline_feature_aware_neumf(train, users, data, seed=seed)
    mastery = compute_mastery(train, data)

    def rank_for_user(uid):
        pred = base(uid)
        mastered = mastery.get(uid, set())
        coherent = [c for c in pred if content_is_coherent(c, mastered, data)]
        incoherent = [c for c in pred if not content_is_coherent(c, mastered, data)]
        return coherent + incoherent

    return rank_for_user


# ---------------------------------------------------------------------------
# Evaluación de un modelo sobre un conjunto de usuarios
# ---------------------------------------------------------------------------
def run_evaluation(rank_fn, users, truth, mastery, data, ks=(5, 10)):
    """rank_fn(uid) -> lista ordenada de content_ids. Devuelve métricas agregadas."""
    agg = {f"ndcg@{k}": [] for k in ks}
    agg.update({f"precision@{k}": [] for k in ks})
    agg.update({f"recall@{k}": [] for k in ks})
    agg["mrr"] = []
    agg.update({f"pedagogy@{k}": [] for k in ks})

    for uid in users:
        pred = rank_fn(uid)
        t = truth.get(uid, set())
        m = evaluate_ranking(pred, t, ks)
        p = evaluate_pedagogy(pred, mastery.get(uid, set()), data, ks)
        for k, v in m.items():
            agg[k].append(v)
        for k, v in p.items():
            agg[k].append(v)

    return {k: float(np.mean(v)) for k, v in agg.items()}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Harness de evaluación de modelos")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--k", type=int, nargs="+", default=[5, 10])
    parser.add_argument("--models", type=str, nargs="+",
                        default=["most_popular", "content_based", "kg_rules", "bpr_mf",
                                 "neumf", "feature_aware_neumf", "feature_aware_neumf_kg"])
    args = parser.parse_args()
    ks = tuple(args.k)

    data = load_data()
    split = make_split(data)
    mastery = compute_mastery(split["train"], data)

    # Ground truth de ranking: contenidos completados en test por usuario
    test_comp = split["test"][split["test"]["completed"]]
    truth = test_comp.groupby("user_id")["content_id"].apply(set).to_dict()

    print("=" * 70)
    print("HARNESS DE EVALUACIÓN — COMPARATIVA DE MODELOS")
    print("=" * 70)
    print(f"Split GTS: train < {TRAIN_END.date()} | test >= {TRAIN_END.date()}")
    print(f"  train: {len(split['train'])} interacciones | test: {len(split['test'])}")
    print(f"  usuarios eval (>=1 completado en test): {len(split['eval_users'])}")
    print(f"    warm: {len(split['warm_eval'])} | cold start: {len(split['cold_eval'])}")
    print(f"Ground truth: completed (etiqueta A) | k = {ks}")
    print()

    # Construir los modelos seleccionados
    models = {}
    if "most_popular" in args.models:
        ranked = baseline_most_popular(split["train"], data)
        models["most_popular"] = (lambda uid, r=ranked: r)
    if "content_based" in args.models:
        cb = baseline_content_based(data["users"], data)
        models["content_based"] = cb
    if "kg_rules" in args.models:
        kg = baseline_kg_rules(split["train"], data, mastery)
        models["kg_rules"] = kg
    if "bpr_mf" in args.models:
        models["bpr_mf"] = baseline_bpr_mf(split["train"], data, seed=args.seed)
    if "neumf" in args.models:
        models["neumf"] = baseline_neumf(split["train"], data, seed=args.seed)
    if "feature_aware_neumf" in args.models:
        models["feature_aware_neumf"] = baseline_feature_aware_neumf(
            split["train"], data["users"], data, seed=args.seed)
    if "feature_aware_neumf_kg" in args.models:
        models["feature_aware_neumf_kg"] = baseline_feature_aware_neumf_kg(
            split["train"], data["users"], data, seed=args.seed)

    # Evaluar en ambos escenarios
    for scenario, users in [("warm", split["warm_eval"]), ("cold", split["cold_eval"])]:
        if not users:
            continue
        print(f"--- Escenario {scenario} ({len(users)} usuarios) ---")
        for name, rank_fn in models.items():
            res = run_evaluation(rank_fn, users, truth, mastery, data, ks)
            line = "  ".join(f"{k}={v:.3f}" for k, v in res.items())
            print(f"  {name:14s} {line}")
        print()

    # Guardar resultados
    out = DATA_DIR / "evaluation_results.json"
    results = {
        "seed": args.seed,
        "split": {"train_end": str(TRAIN_END), "n_train": len(split["train"]),
                  "n_test": len(split["test"]),
                  "n_warm_eval": len(split["warm_eval"]),
                  "n_cold_eval": len(split["cold_eval"])},
        "ground_truth": "completed",
        "k": list(ks),
        "models": {},
    }
    for scenario, users in [("warm", split["warm_eval"]), ("cold", split["cold_eval"])]:
        if not users:
            continue
        results["models"][scenario] = {}
        for name, rank_fn in models.items():
            results["models"][scenario][name] = run_evaluation(
                rank_fn, users, truth, mastery, data, ks)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"✓ {out}")


if __name__ == "__main__":
    main()
