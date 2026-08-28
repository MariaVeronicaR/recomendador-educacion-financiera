"""
evaluate_models.py

Realiza un análisis comparativo experimental de cuatro arquitecturas de recomendación:
1. Popularidad (PopRec)
2. Filtrado Basado en Contenido (TF-IDF + Cosine Similarity con stopwords en español)
3. Híbrido SVD + Ridge Regression (Colaborativo + Metadatos ECF)
4. Neural Collaborative Filtering (NeuMF / MLP en PyTorch)

Metodología:
- Partición Train/Test (80/20) realizada por usuario para evitar fugas.
- Los recomendadores se entrenan únicamente con el conjunto Train.
- La evaluación de exactitud (Precision@5, Recall@5, NDCG@5) se calcula contra
  las interacciones con score >= 0.5 presentes exclusivamente en el Test.
- Se excluyen del promedio los usuarios sin interacciones relevantes en su Test.
- PVR (Prerequisite Violation Rate) utiliza el progreso acumulado en Train.
- Salida guardada en data/evaluation_metrics_warm.csv (arranque en caliente) y
  data/evaluation_metrics_cold.csv (arranque en frío), y mostrada por consola.

Uso:
    python3 src/utils/evaluate_models.py
"""

import os
import csv
import math
import random
import numpy as np
import pandas as pd
from collections import defaultdict

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader

from sklearn.decomposition import TruncatedSVD
from sklearn.linear_model import Ridge
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import OneHotEncoder

# Semilla aleatoria fija para reproducibilidad
random.seed(42)
np.random.seed(42)
torch.manual_seed(42)

# Configuración de rutas
DATA_DIR = "/Users/veronica/Desktop/tfm/data"
USERS_FILE = os.path.join(DATA_DIR, "users_synthetic.csv")
CONTENTS_FILE = os.path.join(DATA_DIR, "contents.csv")
INTERACTIONS_FILE = os.path.join(DATA_DIR, "interactions_synthetic_v3.csv")
PREREQS_FILE = os.path.join(DATA_DIR, "prerequisites.csv")
MAP_FILE = os.path.join(DATA_DIR, "content_concept_map.csv")
METRICS_OUT_WARM = os.path.join(DATA_DIR, "evaluation_metrics_warm.csv")
METRICS_OUT_COLD = os.path.join(DATA_DIR, "evaluation_metrics_cold.csv")

# Stopwords en español integradas (evita dependencias de nltk)
STOPWORDS_ES = [
    'un', 'una', 'unas', 'unos', 'el', 'la', 'las', 'los', 'al', 'del', 'lo', 'alguno', 'algunos',
    'alguna', 'algunas', 'de', 'en', 'para', 'por', 'con', 'sin', 'sobre', 'bajo', 'entre',
    'hasta', 'desde', 'hacia', 'y', 'o', 'u', 'e', 'pero', 'mas', 'como', 'cuando', 'donde',
    'quien', 'que', 'cual', 'cuyo', 'donde', 'este', 'esta', 'estos', 'estas', 'ese', 'esa',
    'esos', 'esas', 'aquel', 'aquella', 'aquellos', 'aquellas', 'mi', 'tu', 'su', 'mis', 'tus',
    'sus', 'nuestro', 'nuestra', 'nuestros', 'nuestras', 'yo', 'tu', 'el', 'ella', 'nosotros',
    'nosotras', 'vosotros', 'vosotras', 'ellos', 'ellas', 'me', 'te', 'se', 'nos', 'os', 'lo',
    'la', 'los', 'las', 'le', 'les', 'mio', 'tuyo', 'suyo', 'míos', 'tuyos', 'suyos', 'miá',
    'tuá', 'suá', 'mías', 'tuyas', 'suyas', 'no', 'si', 'sí', 'muy', 'mucho', 'poco', 'mas',
    'menos', 'bastante', 'demasiado', 'casi', 'solo', 'también', 'tampoco', 'ser', 'estar',
    'hacer', 'tener', 'haber', 'poder', 'querer', 'ir', 'venir', 'ver', 'dar', 'saber', 'su',
    'sus', 'para', 'cómo', 'por qué', 'qué', 'cuál', 'cuándo', 'dónde'
]

# ============================================================
# CREADOR DEL DATASET PYTORCH PARA NeuMF
# ============================================================
class InteractionDataset(Dataset):
    def __init__(self, users, items, ratings):
        self.users = torch.tensor(users, dtype=torch.long)
        self.items = torch.tensor(items, dtype=torch.long)
        self.ratings = torch.tensor(ratings, dtype=torch.float32)

    def __len__(self):
        return len(self.users)

    def __getitem__(self, idx):
        return self.users[idx], self.items[idx], self.ratings[idx]

# ============================================================
# RED NEURONAL: NCF-MLP (Neural Collaborative Filtering basado en MLP)
# ============================================================
# NOTA METODOLÓGICA SOBRE EL NOMBRE:
# El modelo NeuMF clásico de He et al. (2017) combina dos submodelos:
#   1. GMF (Generalized Matrix Factorization): producto elemento a elemento
#      de los embeddings de usuario e item.
#   2. MLP (Multi-Layer Perceptron): concatenación de embeddings + capas densas.
# Esta implementación NO incluye el componente GMF (solo el MLP). Por tanto,
# arquitectónicamente es una "variante basada en MLP del NCF".
# Renombramos la clase a NCFMLP para que el nombre refleje fielmente lo que
# hace el código y sea académicamente defendible.
class NCFMLP(nn.Module):
    """Variante basada en MLP del Neural Collaborative Filtering (NCF).

    Arquitectura: nn.Embedding para usuario e item + concatenación + MLP.
    NO implementa la rama GMF del NeuMF clásico; es únicamente la rama MLP.
    Mantiene las mismas condiciones que el resto del experimento:
    latent_dim=8, dropout=0.2, sigmoid output, MSELoss, Adam.
    """
    def __init__(self, num_users, num_items, latent_dim=8):
        super(NCFMLP, self).__init__()
        self.user_embed = nn.Embedding(num_users, latent_dim)
        self.item_embed = nn.Embedding(num_items, latent_dim)
        self.mlp = nn.Sequential(
            nn.Linear(latent_dim * 2, 16),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(16, 8),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(8, 1),
            nn.Sigmoid()
        )

    def forward(self, user_indices, item_indices):
        u_emb = self.user_embed(user_indices)
        i_emb = self.item_embed(item_indices)
        x = torch.cat([u_emb, i_emb], dim=-1)
        return self.mlp(x).squeeze()


# ============================================================
# RED NEURONAL NeuMF-Profile (variante para Cold Start)
# ============================================================
class NeuMFProfileMLP(nn.Module):
    """Variante de NeuMF para Cold Start (sin nn.Embedding de usuario).

    Arquitectura paralela a NCFMLP (mismas latent_dim=8, mismo dropout=0.2,
    misma estructura MLP) pero sustituye el user embedding por un encoder MLP
    aplicado directamente sobre las features demográficas del perfil.
    Esto permite que un usuario nuevo sin historial histórico reciba
    recomendaciones desde su primer acceso.
    """
    def __init__(self, num_user_features, num_items, latent_dim=8):
        super(NeuMFProfileMLP, self).__init__()
        # Sustituye nn.Embedding por un encoder de features demográficas
        self.user_encoder = nn.Sequential(
            nn.Linear(num_user_features, 16),
            nn.ReLU(),
            nn.Linear(16, latent_dim)
        )
        self.item_embed = nn.Embedding(num_items, latent_dim)
        self.mlp = nn.Sequential(
            nn.Linear(latent_dim * 2, 16),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(16, 8),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(8, 1),
            nn.Sigmoid()
        )

    def forward(self, user_features, item_indices):
        u_emb = self.user_encoder(user_features)
        i_emb = self.item_embed(item_indices)
        x = torch.cat([u_emb, i_emb], dim=-1)
        return self.mlp(x).squeeze()

# ============================================================
# FUNCIONES AUXILIARES DE EVALUACIÓN
# ============================================================
def calculate_ndcg(recommended_ids, actual_relevant_ids, k=5):
    dcg = 0.0
    for i, cid in enumerate(recommended_ids[:k], 1):
        if cid in actual_relevant_ids:
            dcg += 1.0 / math.log2(i + 1)

    idcg = 0.0
    for i in range(1, min(len(actual_relevant_ids), k) + 1):
        idcg += 1.0 / math.log2(i + 1)

    return dcg / idcg if idcg > 0 else 0.0

def make_train_test_split(interactions_df, test_ratio=0.2, seed=42):
    """Split Train/Test SIN fuga de pares (user_id, content_id).

    Reglas:
    - Agrupa por (user_id, content_id) para que el mismo par no quede en ambos sets.
    - Si hay timestamp válido por usuario, ordena cronológicamente y toma los últimos
      pares como Test (split temporal dentro de cada usuario).
    - Si NO hay timestamp, baraja los pares del usuario con seed fija (random split
      reproducible por par).
    - Usuarios con un solo par (user_id, content_id) → todo a Train.
    - Usuarios con >= 2 pares: garantiza al menos 1 par en Test.
    """
    df = interactions_df.copy()
    has_timestamp = 'timestamp' in df.columns and df['timestamp'].notna().any()

    if has_timestamp:
        df['_ts_parsed'] = pd.to_datetime(df['timestamp'], errors='coerce')
    else:
        df['_ts_parsed'] = pd.NaT  # Marcador para no romper el sort por timestamp

    rng = random.Random(seed)
    train_mask = pd.Series(False, index=df.index)
    test_mask = pd.Series(False, index=df.index)

    for uid, group in df.groupby('user_id', sort=False):
        seen = set()
        unique_pairs = []
        for idx, row in group.iterrows():
            key = row['content_id']
            if key in seen:
                continue
            seen.add(key)
            unique_pairs.append(idx)

        n_pairs = len(unique_pairs)
        if n_pairs <= 1:
            for idx in unique_pairs:
                train_mask.loc[idx] = True
            continue

        # Ordenar los pares únicos: por timestamp si está disponible, o aleatorio si no
        if has_timestamp:
            # Orden estable por timestamp, desempate por el orden original del CSV
            sorted_idx = sorted(
                unique_pairs,
                key=lambda i: (df.loc[i, '_ts_parsed'], i)
            )
        else:
            sorted_idx = list(unique_pairs)
            rng.shuffle(sorted_idx)  # Baraja reproducible por usuario

        n_test = max(1, int(round(n_pairs * test_ratio)))
        # Tomar los últimos n_test pares (los más recientes según el orden elegido)
        for idx in sorted_idx[-n_test:]:
            test_mask.loc[idx] = True
        # El resto a Train
        for idx in sorted_idx[:-n_test]:
            train_mask.loc[idx] = True

    train_df = df[train_mask].drop(columns=['_ts_parsed'], errors='ignore').reset_index(drop=True)
    test_df = df[test_mask].drop(columns=['_ts_parsed'], errors='ignore').reset_index(drop=True)

    # Validación anti-leakage: ningún par (user_id, content_id) puede estar en ambos sets
    train_pairs = set(zip(train_df['user_id'], train_df['content_id']))
    test_pairs = set(zip(test_df['user_id'], test_df['content_id']))
    overlap = train_pairs & test_pairs
    assert len(overlap) == 0, f"LEAKAGE: {len(overlap)} pares (user_id, content_id) están en Train y Test"

    return train_df, test_df

def evaluate_predictions(preds_matrix, train_df, test_df, concept_prereqs, content_concepts, k=5):
    """Evalúa la exactitud y seguridad pedagógica sobre el split Train/Test."""
    all_users = preds_matrix.index.tolist()
    all_contents = preds_matrix.columns.tolist()

    # 1. Historial de entrenamiento (se excluye de las recomendaciones)
    train_history = defaultdict(set)
    for _, row in train_df.iterrows():
        train_history[row['user_id']].add(row['content_id'])

    # 2. Conceptos dominados en TRAIN (para calcular PVR real)
    user_mastered_train = defaultdict(set)
    for _, row in train_df.iterrows():
        if row['event'] in ['completed', 'quiz_passed']:
            for concept in content_concepts[row['content_id']]:
                user_mastered_train[row['user_id']].add(concept)

    # 3. Ground truth de TEST (relevancia: score >= 0.5)
    test_relevant = defaultdict(set)
    for _, row in test_df.iterrows():
        if row['score'] >= 0.5:
            test_relevant[row['user_id']].add(row['content_id'])

    # Separamos métricas RAW y POST: el ranking del modelo (sin filtro) se evalúa
    # en precisions_raw/recalls_raw/ndcgs_raw, y el ranking post-filtro en las
    # versiones _post. Esto permite distinguir la calidad del recomendador
    # de la influencia del filtro pedagógico.
    precisions_raw, recalls_raw, ndcgs_raw = [], [], []
    precisions, recalls, ndcgs = [], [], []
    recommended_set = set()

    violations_pre = 0
    total_recs_pre = 0
    violations_post = 0
    total_recs_post = 0

    raw_rejected_by_filter = 0
    raw_total_considered = 0

    # feasibility_at_5: % de usuarios con relevantes en Test que obtienen k=5
    # recomendaciones TRAS el filtro pedagógico (no tras el fallback). Si el filtro
    # deja menos de k, el usuario queda "no feasible" — esto es información
    # relevante para el TFM porque mide si el modelo tiene suficiente cobertura.
    users_full_count = 0
    users_eval_with_pos = 0

    users_evaluated = 0

    for uid in all_users:
        user_preds = preds_matrix.loc[uid]
        relevant_ids = test_relevant[uid]
        history = train_history[uid]
        mastered = user_mastered_train[uid]

        # --- RANKING CRUDO (sin filtro pedagógico) ---
        sorted_raw = user_preds.sort_values(ascending=False)
        raw_recs = [cid for cid in sorted_raw.index if cid not in history][:k]

        # Métricas RAW sobre el ranking sin filtro
        if len(relevant_ids) > 0:
            users_evaluated += 1
            hits_raw = len(set(raw_recs) & relevant_ids)
            precisions_raw.append(hits_raw / k)
            recalls_raw.append(hits_raw / len(relevant_ids))
            ndcgs_raw.append(calculate_ndcg(raw_recs, relevant_ids, k))

        # PVR Pre sobre el ranking crudo (cuántas del top-K violan)
        for cid in raw_recs:
            total_recs_pre += 1
            for concept in content_concepts[cid]:
                required = concept_prereqs[concept]
                if required and not set(required).issubset(mastered):
                    violations_pre += 1
                    break

        # --- POST-FILTRO (IA + Grafo Pedagógico) ---
        # Recorremos TODO el ranking crudo (sin cortar al llegar a k=5) para que
        # filter_rate_pct refleje correctamente qué proporción de candidatos fue
        # rechazada por el filtro pedagógico. Solo iteramos sobre items con score > 0
        # (los items con score 0 nunca serían recomendados por el modelo).
        # El filtro verifica prerequisites en cada candidato: si pasa, se incluye
        # en filtered_recs (hasta llegar a k). Si falla, se cuenta como rechazo.
        raw_rejected_by_filter = 0
        raw_total_considered = 0
        filtered_recs = []  # Inicializar por si el modelo no produce ranking con score>0
        for cid, score in sorted_raw.items():
            if score <= 0:
                break  # Los items con score 0 no son candidatos reales del modelo
            if cid in history:
                continue

            raw_total_considered += 1
            qualified = True
            for concept in content_concepts[cid]:
                required = concept_prereqs[concept]
                if required and not set(required).issubset(mastered):
                    qualified = False
                    break

            if qualified:
                if len(filtered_recs) < k:
                    filtered_recs.append(cid)
            else:
                raw_rejected_by_filter += 1

        # Métricas POST sobre el ranking tras filtro (solo si tiene relevantes en TEST)
        if len(relevant_ids) > 0:
            hits = len(set(filtered_recs) & relevant_ids)
            precisions.append(hits / k)  # k fijo
            recalls.append(hits / len(relevant_ids))
            ndcgs.append(calculate_ndcg(filtered_recs, relevant_ids, k))

        # feasibility_at_5: ¿el usuario tiene al menos k=5 recomendaciones tras el
        # filtro? Si no, el sistema no puede darle 5 sugerencias seguras.
        if len(relevant_ids) > 0:
            users_eval_with_pos += 1
            if len(filtered_recs) >= k:
                users_full_count += 1

        # PVR Post: por construcción del filtro pedagógico, TODAS las
        # recomendaciones en filtered_recs cumplen los prerequisites, así que el
        # conteo de violations_post sobre filtered_recs SIEMPRE será 0.
        # Reportar 0.0% confirma que el filtro funciona correctamente.
        for cid in filtered_recs:
            recommended_set.add(cid)
            total_recs_post += 1
            for concept in content_concepts[cid]:
                required = concept_prereqs[concept]
                if required and not set(required).issubset(mastered):
                    violations_post += 1
                    break

    # Promedios
    avg_precision_raw = np.mean(precisions_raw) if precisions_raw else 0.0
    avg_recall_raw = np.mean(recalls_raw) if recalls_raw else 0.0
    avg_ndcg_raw = np.mean(ndcgs_raw) if ndcgs_raw else 0.0

    avg_precision = np.mean(precisions) if precisions else 0.0
    avg_recall = np.mean(recalls) if recalls else 0.0
    avg_ndcg = np.mean(ndcgs) if ndcgs else 0.0
    coverage = (len(recommended_set) / len(all_contents)) * 100.0
    pvr_pre = (violations_pre / total_recs_pre) * 100.0 if total_recs_pre > 0 else 0.0
    pvr_post = (violations_post / total_recs_post) * 100.0 if total_recs_post > 0 else 0.0

    # filter_rate_pct: % del ranking crudo que fue RECHAZADO por el filtro pedagógico.
    # raw_total_considered excluye los contenidos ya consumidos en Train (no son candidatos).
    # raw_rejected_by_filter cuenta cuántos candidatos válidos fueron saltados por PVR.
    filter_rate_pct = (raw_rejected_by_filter / raw_total_considered) * 100.0 if raw_total_considered > 0 else 0.0

    # feasibility_at_5: % de usuarios con relevantes en Test que obtienen al menos k
    # recomendaciones TRAS el filtro (medido en el bucle principal).
    feasibility_at_5 = (users_full_count / users_eval_with_pos) * 100.0 if users_eval_with_pos > 0 else 0.0

    print(f"  [Debug] Usuarios evaluados en test (con interacciones positivas en test): {users_evaluated}/{len(all_users)}")

    return {
        "precision": avg_precision,
        "recall": avg_recall,
        "ndcg": avg_ndcg,
        "coverage": coverage,
        "pvr_pre": pvr_pre,
        "pvr_post": pvr_post,
        "filter_rate_pct": filter_rate_pct,
        "feasibility_at_5": feasibility_at_5,
        "precision_raw": avg_precision_raw,
        "recall_raw": avg_recall_raw,
        "ndcg_raw": avg_ndcg_raw,
    }


# ============================================================
# FUNCIONES ESPECÍFICAS PARA COLD START
# ============================================================
def make_cold_start_split(interactions_df, n_cold_users=200, seed=42):
    """Separa usuarios en train_pool y cold_users para evaluación Cold Start.

    - Selecciona n_cold_users usuarios aleatorios como "nuevos" (cold).
    - Sus interacciones van INTEGRAS al set de Test (ninguna a Train).
    - El resto de usuarios forman el train_pool.
    - Devuelve (train_pool_interactions_df, cold_test_interactions_df, cold_users_set).

    Validación anti-leakage: se comprueba que ningún cold_user aparece en train_pool.
    """
    rng = random.Random(seed)
    all_users = interactions_df['user_id'].unique().tolist()
    rng.shuffle(all_users)
    cold_users = set(all_users[:n_cold_users])
    train_pool_users = set(all_users[n_cold_users:])

    # Separar interacciones
    cold_mask = interactions_df['user_id'].isin(cold_users)
    cold_test_df = interactions_df[cold_mask].copy().reset_index(drop=True)
    train_pool_df = interactions_df[~cold_mask].copy().reset_index(drop=True)

    # VALIDACIÓN ANTI-FUGA: ningún cold_user puede estar en train_pool
    leakage = train_pool_users & cold_users
    assert len(leakage) == 0, f"FUGA DE DATOS: {len(leakage)} usuarios cold aparecen en train_pool"

    print(f"  Train pool: {len(train_pool_df)} interacciones de {len(train_pool_users)} usuarios")
    print(f"  Cold users:  {len(cold_test_df)} interacciones de {len(cold_users)} usuarios")
    print(f"  [OK] Validación anti-fuga: 0 cold users en train_pool")

    return train_pool_df, cold_test_df, cold_users, train_pool_users


def evaluate_predictions_cold(preds_matrix, train_pool_df, cold_test_df,
                              concept_prereqs, content_concepts,
                              cold_users, k=5,
                              initial_mastered=None):
    """Evalúa Cold Start: train_pool construye el historial y mastered; cold_test es el ground truth.

    Si initial_mastered es un dict {user_id: set(conceptos)} se usa como
    conocimiento inicial (basado en el perfil del cuestionario, no en interacciones).
    """
    cold_users_list = sorted(list(cold_users))
    all_contents = preds_matrix.columns.tolist()

    # 1. Historial de entrenamiento (SOLO de train_pool_users, NO de cold_users)
    train_history = defaultdict(set)
    for _, row in train_pool_df.iterrows():
        train_history[row['user_id']].add(row['content_id'])

    # 2. Conceptos dominados en train_pool (para PVR)
    user_mastered_train = defaultdict(set)
    for _, row in train_pool_df.iterrows():
        if row['event'] in ['completed', 'quiz_passed']:
            for concept in content_concepts[row['content_id']]:
                user_mastered_train[row['user_id']].add(concept)

    # 3. Ground truth Cold (relevancia: score >= 0.5)
    cold_relevant = defaultdict(set)
    for _, row in cold_test_df.iterrows():
        if row['score'] >= 0.5:
            cold_relevant[row['user_id']].add(row['content_id'])

    precisions = []
    recalls = []
    ndcgs = []
    recommended_set = set()

    violations_pre = 0
    total_recs_pre = 0
    violations_post = 0
    total_recs_post = 0

    users_evaluated = 0

    # Separar métricas RAW y POST en Cold también
    precisions_raw, recalls_raw, ndcgs_raw = [], [], []
    precisions, recalls, ndcgs = [], [], []
    recommended_set = set()

    # filter_rate_pct Cold: % del ranking crudo rechazado por el filtro pedagógico.
    raw_rejected_by_filter = 0
    raw_total_considered = 0

    # feasibility_at_5 Cold: % de cold users con relevantes en Test que obtienen
    # al menos k recomendaciones TRAS el filtro (medido en el bucle principal).
    users_full_count = 0
    users_eval_with_pos = 0

    for uid in cold_users_list:
        if uid not in preds_matrix.index:
            continue
        user_preds = preds_matrix.loc[uid]
        relevant_ids = cold_relevant[uid]
        # En cold start, history = {} (el usuario es nuevo)
        history = set()
        # Para PVR en cold start, asumimos mastery conservador desde el cuestionario:
        # knowledge_to_num ya trata NaN como 1. Para no-mastered usamos {}.
        # Si initial_mastered está disponible, lo fusionamos con train_pool (vacío para cold).
        profile_mastered = initial_mastered.get(uid, set()) if initial_mastered else set()
        mastered = profile_mastered | user_mastered_train.get(uid, set())

        # --- RANKING CRUDO (sin filtro pedagógico) ---
        sorted_raw = user_preds.sort_values(ascending=False)
        raw_recs = [cid for cid in sorted_raw.index if cid not in history][:k]

        if len(relevant_ids) > 0:
            users_evaluated += 1
            hits_raw = len(set(raw_recs) & relevant_ids)
            precisions_raw.append(hits_raw / k)
            recalls_raw.append(hits_raw / len(relevant_ids))
            ndcgs_raw.append(calculate_ndcg(raw_recs, relevant_ids, k))

        for cid in raw_recs:
            total_recs_pre += 1
            for concept in content_concepts[cid]:
                required = concept_prereqs[concept]
                if required and not set(required).issubset(mastered):
                    violations_pre += 1
                    break

        # --- POST-FILTRO (IA + Grafo Pedagógico) ---
        # Recorremos TODO el ranking crudo (sin cortar al llegar a k=5) para que
        # filter_rate_pct refleje correctamente qué proporción de candidatos fue
        # rechazada por el filtro pedagógico. Solo iteramos sobre items con score > 0
        # (los items con score 0 nunca serían recomendados por el modelo).
        # El filtro verifica prerequisites en cada candidato: si pasa, se incluye
        # en filtered_recs (hasta llegar a k). Si falla, se cuenta como rechazo.
        # Inicializar por si el modelo no produce ranking con score>0 (ej. Popularidad
        # inicializada con todos los scores = 0).
        filtered_recs = []
        for cid, score in sorted_raw.items():
            if score <= 0:
                break  # Los items con score 0 no son candidatos reales del modelo
            if cid in history:
                continue

            raw_total_considered += 1
            qualified = True
            for concept in content_concepts[cid]:
                required = concept_prereqs[concept]
                if required and not set(required).issubset(mastered):
                    qualified = False
                    break

            if qualified:
                if len(filtered_recs) < k:
                    filtered_recs.append(cid)
            else:
                raw_rejected_by_filter += 1

        if len(relevant_ids) > 0:
            hits = len(set(filtered_recs) & relevant_ids)
            precisions.append(hits / k)
            recalls.append(hits / len(relevant_ids))
            ndcgs.append(calculate_ndcg(filtered_recs, relevant_ids, k))

        # feasibility_at_5 Cold (medido en el bucle principal)
        if len(relevant_ids) > 0:
            users_eval_with_pos += 1
            if len(filtered_recs) >= k:
                users_full_count += 1

        # PVR Post: por construcción del filtro, TODAS las recomendaciones en
        # filtered_recs cumplen los prerequisites, así que violations_post SIEMPRE
        # será 0. Reportar 0.0% confirma que el filtro funciona correctamente.
        for cid in filtered_recs:
            recommended_set.add(cid)
            total_recs_post += 1
            for concept in content_concepts[cid]:
                required = concept_prereqs[concept]
                if required and not set(required).issubset(mastered):
                    violations_post += 1
                    break

    avg_precision_raw = np.mean(precisions_raw) if precisions_raw else 0.0
    avg_recall_raw = np.mean(recalls_raw) if recalls_raw else 0.0
    avg_ndcg_raw = np.mean(ndcgs_raw) if ndcgs_raw else 0.0

    avg_precision = np.mean(precisions) if precisions else 0.0
    avg_recall = np.mean(recalls) if recalls else 0.0
    avg_ndcg = np.mean(ndcgs) if ndcgs else 0.0
    coverage = (len(recommended_set) / len(all_contents)) * 100.0
    pvr_pre = (violations_pre / total_recs_pre) * 100.0 if total_recs_pre > 0 else 0.0
    pvr_post = (violations_post / total_recs_post) * 100.0 if total_recs_post > 0 else 0.0

    # filter_rate_pct: % del ranking crudo rechazado por el filtro pedagógico.
    filter_rate_pct = (raw_rejected_by_filter / raw_total_considered) * 100.0 if raw_total_considered > 0 else 0.0

    # feasibility_at_5 Cold (medido en el bucle principal).
    feasibility_at_5 = (users_full_count / users_eval_with_pos) * 100.0 if users_eval_with_pos > 0 else 0.0

    print(f"  [Debug] Cold users evaluados (con positivos en su test): {users_evaluated}/{len(cold_users_list)}")

    return {
        "precision": avg_precision,
        "recall": avg_recall,
        "ndcg": avg_ndcg,
        "coverage": coverage,
        "pvr_pre": pvr_pre,
        "pvr_post": pvr_post,
        "filter_rate_pct": filter_rate_pct,
        "feasibility_at_5": feasibility_at_5,
        "precision_raw": avg_precision_raw,
        "recall_raw": avg_recall_raw,
        "ndcg_raw": avg_ndcg_raw,
    }



# ============================================================
# MAIN PIPELINE
# ============================================================
def main():
    print("=" * 60)
    print("INICIANDO EVALUACIÓN CON SPLIT METODOLÓGICO (TRAIN/TEST)")
    print("=" * 60)

    # 1. Carga de archivos
    users_df = pd.read_csv(USERS_FILE)
    contents_df = pd.read_csv(CONTENTS_FILE)
    interactions_df = pd.read_csv(INTERACTIONS_FILE)
    prereqs_df = pd.read_csv(PREREQS_FILE)
    map_df = pd.read_csv(MAP_FILE)

    all_users = users_df['user_id'].tolist()
    all_contents = contents_df['content_id'].tolist()

    # 6. AUDITORÍA ESTADÍSTICA DEL DATASET
    print("\n" + "=" * 60)
    print("AUDITORÍA ESTADÍSTICA DEL DATASET")
    print("=" * 60)
    per_user = interactions_df.groupby('user_id').size()
    per_content = interactions_df.groupby('content_id').size()
    positives = interactions_df[interactions_df['score'] >= 0.5]
    pos_per_user = positives.groupby('user_id').size()
    n_users = interactions_df['user_id'].nunique()
    n_contents_with_inter = interactions_df['content_id'].nunique()
    n_inter = len(interactions_df)
    sparsity = 1.0 - (n_inter / (n_users * n_contents_with_inter))
    print(f"  Usuarios únicos: {n_users}")
    print(f"  Contenidos con interacción: {n_contents_with_inter} / {len(contents_df)} catalogados")
    print(f"  Interacciones totales: {n_inter}")
    print(f"  Media/mediana/mín/máx interacciones por usuario: {per_user.mean():.2f} / {per_user.median():.0f} / {per_user.min()} / {per_user.max()}")
    print(f"  Media/máx interacciones por contenido: {per_content.mean():.2f} / {per_content.max()}")
    print(f"  Positivos (score >= 0.5): {len(positives)} ({len(positives)/n_inter*100:.1f}%)")
    print(f"  Media positivos por usuario (con positivos): {pos_per_user.mean():.2f}")
    print(f"  Sparsity user×content (sobre contenidos con interacción): {sparsity*100:.1f}%")
    dup_pairs = interactions_df.duplicated(subset=['user_id', 'content_id']).sum()
    print(f"  Duplicados (user_id, content_id): {dup_pairs}")
    has_ts = 'timestamp' in interactions_df.columns and interactions_df['timestamp'].notna().any()
    print(f"  Timestamp disponible: {has_ts}")

    # Validaciones iniciales
    assert len(all_users) > 0, "Debe haber usuarios registrados."
    assert len(all_contents) == 104, "Debe haber 104 contenidos registrados."
    assert len(interactions_df) > 0, "El dataset de interacciones está vacío."

    # Partición Train/Test por usuario
    train_df, test_df = make_train_test_split(interactions_df, test_ratio=0.2, seed=42)
    print(f"  Split completado: Train={len(train_df)} interacciones, Test={len(test_df)} interacciones")

    # Diagnóstico detallado del split (requisito 7 del usuario)
    users_in_train = set(train_df['user_id'].unique())
    users_in_test = set(test_df['user_id'].unique())
    print("\n--- DIAGNÓSTICO DEL SPLIT ---")
    print(f"  Usuarios únicos en Train: {len(users_in_train)}")
    print(f"  Usuarios únicos en Test: {len(users_in_test)}")
    print(f"  Usuarios en ambos: {len(users_in_train & users_in_test)}")
    print(f"  Usuarios solo en Train (sin Test): {len(users_in_train - users_in_test)}")
    print(f"  Interacciones medias por usuario (Train): {len(train_df)/len(users_in_train):.2f}")
    print(f"  Interacciones medias por usuario (Test): {len(test_df)/len(users_in_test):.2f}")

    # Distribución de eventos
    print("\n  Distribución de eventos en Train:")
    print(train_df['event'].value_counts(normalize=True).round(3).to_dict())
    print("  Distribución de eventos en Test:")
    print(test_df['event'].value_counts(normalize=True).round(3).to_dict())

    # Distribución de knowledge_level (uniendo con users_synthetic.csv)
    users_for_split = pd.read_csv(USERS_FILE)[['user_id', 'financial_knowledge_level']]
    train_kn = train_df.merge(users_for_split, on='user_id', how='left')
    test_kn = test_df.merge(users_for_split, on='user_id', how='left')
    print("\n  Distribución de financial_knowledge_level en Train:")
    print(train_kn['financial_knowledge_level'].value_counts(dropna=False).to_dict())
    print("  Distribución de financial_knowledge_level en Test:")
    print(test_kn['financial_knowledge_level'].value_counts(dropna=False).to_dict())

    # Usuarios sin Test
    if len(users_in_train - users_in_test) > 0:
        users_no_test = users_in_train - users_in_test
        inters_counts = interactions_df.groupby('user_id').size()
        no_test_users = [(u, inters_counts.get(u, 0)) for u in list(users_no_test)[:5]]
        print(f"\n  Usuarios sin Test (mostrando 5): {no_test_users}")
        print(f"  Estos usuarios tienen 1 sola interacción (no se dividen).")

    # Construcción de mapas del grafo
    concept_prereqs = defaultdict(list)
    for _, row in prereqs_df.iterrows():
        concept_prereqs[row['concept_id']].append(row['prerequisite_concept_id'])

    content_concepts = defaultdict(list)
    for _, row in map_df.iterrows():
        if row['coverage_type'] == 'directa':
            content_concepts[row['content_id']].append(row['concept_id'])

    results = {}

    # ------------------------------------------------------------
    # MODELO 1: POPULARIDAD (PopRec)
    # ------------------------------------------------------------
    print("\n[1/4] Evaluando Popularidad (PopRec) con Train...")
    content_pop = train_df['content_id'].value_counts()

    pop_preds = []
    for uid in all_users:
        user_preds = []
        for cid in all_contents:
            user_preds.append(content_pop.get(cid, 0.0))
        pop_preds.append(user_preds)

    pop_preds_df = pd.DataFrame(pop_preds, index=all_users, columns=all_contents)
    results["Popularidad"] = evaluate_predictions(pop_preds_df, train_df, test_df, concept_prereqs, content_concepts)

    # ------------------------------------------------------------
    # MODELO 0 (BASELINE): RANDOM TOP-5 (Warm Start)
    # ------------------------------------------------------------
    # Selecciona 5 contenidos al azar por usuario, excluyendo los del Train.
    # Sirve como baseline para saber si los demás modelos superan al azar.
    print("\n[Baseline Warm] Random Top-5...")
    K = 5
    rng_random_warm = random.Random(123)
    random_warm_preds = []
    for uid in all_users:
        history = set(train_df[train_df['user_id'] == uid]['content_id'])
        candidates = [c for c in all_contents if c not in history]
        if len(candidates) >= K:
            chosen = rng_random_warm.sample(candidates, K)
        else:
            chosen = candidates[:K]
        # Construir vector con 1.0 para los elegidos, 0.0 para el resto
        row_vec = [1.0 if c in chosen else 0.0 for c in all_contents]
        random_warm_preds.append(row_vec)
    random_warm_df = pd.DataFrame(random_warm_preds, index=all_users, columns=all_contents)
    results["Random (baseline)"] = evaluate_predictions(random_warm_df, train_df, test_df, concept_prereqs, content_concepts)

    # ------------------------------------------------------------
    # MODELO 2: TF-IDF (Contenido Puro)
    # ------------------------------------------------------------
    print("\n[2/4] Evaluando TF-IDF + Cosine Similarity (Stopwords ES, Perfil Train)...")

    # Crear corpus en español
    corpus = []
    for _, row in contents_df.iterrows():
        text = f"{row['title']} {row['summary']} {row['learning_objective']}"
        corpus.append(text)

    # Vectorización usando stopwords integradas en español
    vectorizer = TfidfVectorizer(stop_words=STOPWORDS_ES)
    tfidf_matrix = vectorizer.fit_transform(corpus)
    item_similarity = cosine_similarity(tfidf_matrix)
    similarity_df = pd.DataFrame(item_similarity, index=all_contents, columns=all_contents)

    # Perfiles del usuario basados únicamente en sus éxitos de TRAIN
    tfidf_preds = []
    for uid in all_users:
        user_train = train_df[(train_df['user_id'] == uid) & (train_df['score'] >= 0.5)]
        user_profile = np.zeros(len(all_contents))

        if len(user_train) > 0:
            interacted_ids = user_train['content_id'].tolist()
            user_profile = similarity_df.loc[interacted_ids].mean().values

        tfidf_preds.append(user_profile)

    tfidf_preds_df = pd.DataFrame(tfidf_preds, index=all_users, columns=all_contents)
    results["TF-IDF + Cosine"] = evaluate_predictions(tfidf_preds_df, train_df, test_df, concept_prereqs, content_concepts)

    # ------------------------------------------------------------
    # MODELO 3: HÍBRIDO (SVD + Ridge)
    # ------------------------------------------------------------
    print("\n[3/4] Evaluando recomendador Híbrido SVD + Ridge con Train...")

    # Pivot de interacciones basándose únicamente en TRAIN
    interaction_matrix = train_df.pivot_table(index='user_id', columns='content_id', values='score', fill_value=0.0)
    interaction_matrix = interaction_matrix.reindex(index=all_users, columns=all_contents, fill_value=0.0)

    # SVD sobre TRAIN
    n_components = min(10, len(all_contents) - 1)
    svd = TruncatedSVD(n_components=n_components, random_state=42)
    user_features_cf = svd.fit_transform(interaction_matrix)
    content_features_cf = svd.components_.T

    # Encoders demográficos
    user_cat_cols = ['age_group', 'education_level', 'employment_status', 'financial_knowledge_level', 'saving_habit', 'sex']
    user_encoder = OneHotEncoder(handle_unknown='ignore', sparse_output=False)
    user_encoded = user_encoder.fit_transform(users_df[user_cat_cols])
    user_features_df = pd.DataFrame(user_encoded, index=users_df['user_id'])

    content_cat_cols = ['topic', 'difficulty', 'format', 'is_investment_related']
    content_encoder = OneHotEncoder(handle_unknown='ignore', sparse_output=False)
    content_encoded = content_encoder.fit_transform(contents_df[content_cat_cols])
    content_features_df = pd.DataFrame(content_encoded, index=contents_df['content_id'])

    # Entrenar Ridge únicamente sobre interacciones de TRAIN
    X_train, y_train = [], []
    for _, row in train_df.iterrows():
        uid, cid, score = row['user_id'], row['content_id'], row['score']
        u_idx, c_idx = all_users.index(uid), all_contents.index(cid)
        interaction_vector = np.concatenate([
            [np.dot(user_features_cf[u_idx], content_features_cf[c_idx])],
            user_features_df.loc[uid].values,
            content_features_df.loc[cid].values
        ])
        X_train.append(interaction_vector)
        y_train.append(score)

    recommender = Ridge(alpha=1.0)
    recommender.fit(X_train, y_train)

    # Predecir matriz completa
    hybrid_preds = []
    for uid in all_users:
        u_idx = all_users.index(uid)
        u_feat = user_features_df.loc[uid].values
        user_preds = []
        for cid in all_contents:
            c_idx = all_contents.index(cid)
            vector = np.concatenate([
                [np.dot(user_features_cf[u_idx], content_features_cf[c_idx])],
                u_feat,
                content_features_df.loc[cid].values
            ])
            user_preds.append(recommender.predict([vector])[0])
        hybrid_preds.append(user_preds)

    hybrid_preds_df = pd.DataFrame(hybrid_preds, index=all_users, columns=all_contents)
    results["Híbrido SVD"] = evaluate_predictions(hybrid_preds_df, train_df, test_df, concept_prereqs, content_concepts)

    # ------------------------------------------------------------
    # MODELO 4: RED NEURONAL (NeuMF PyTorch)
    # ------------------------------------------------------------
    print("\n[4/4] Evaluando Red Neuronal NeuMF (PyTorch) entrenada en Train...")

    user_to_idx = {uid: idx for idx, uid in enumerate(all_users)}
    content_to_idx = {cid: idx for idx, cid in enumerate(all_contents)}

    # Obtener arrays para PyTorch basados en TRAIN únicamente
    train_users = [user_to_idx[r['user_id']] for _, r in train_df.iterrows()]
    train_items = [content_to_idx[r['content_id']] for _, r in train_df.iterrows()]
    train_ratings = [r['score'] for _, r in train_df.iterrows()]

    dataset = InteractionDataset(train_users, train_items, train_ratings)
    dataloader = DataLoader(dataset, batch_size=32, shuffle=True)

    net = NCFMLP(len(all_users), len(all_contents), latent_dim=8)
    criterion = nn.MSELoss()
    optimizer = optim.Adam(net.parameters(), lr=0.01, weight_decay=1e-4)

    net.train()
    for epoch in range(15):
        for batch_users, batch_items, batch_ratings in dataloader:
            optimizer.zero_grad()
            outputs = net(batch_users, batch_items)
            loss = criterion(outputs, batch_ratings)
            loss.backward()
            optimizer.step()

    net.eval()
    nn_preds = []
    with torch.no_grad():
        for uid in all_users:
            u_idx = user_to_idx[uid]
            user_preds = []
            for cid in all_contents:
                c_idx = content_to_idx[cid]
                pred = net(torch.tensor([u_idx]), torch.tensor([c_idx])).item()
                user_preds.append(pred)
            nn_preds.append(user_preds)

    nn_preds_df = pd.DataFrame(nn_preds, index=all_users, columns=all_contents)
    results["NCF-MLP (PyTorch)"] = evaluate_predictions(nn_preds_df, train_df, test_df, concept_prereqs, content_concepts)

    # ============================================================
    # IMPRIMIR Y GUARDAR TABLA DE RESULTADOS
    # ============================================================
    print("\n" + "=" * 85)
    print(f"{'MODELO COMPARATIVO DE IA (TRAIN/TEST SPLIT)':^85}")
    print("=" * 85)
    print(f"{'Modelo':22s} | {'P@5 RAW':7s} | {'P@5':7s} | {'R@5 RAW':7s} | {'R@5':7s} | {'NDCG RAW':9s} | {'NDCG':7s} | {'Coverage':8s} | {'PVR Pre':7s} | {'Post':6s}")
    print("-" * 85)
    for model_name, metrics in results.items():
        print(f"{model_name:22s} | {metrics.get('precision_raw', 0):7.3f} | {metrics['precision']:7.3f} | {metrics.get('recall_raw', 0):7.3f} | {metrics['recall']:7.3f} | {metrics.get('ndcg_raw', 0):9.3f} | {metrics['ndcg']:7.3f} | {metrics['coverage']:7.1f}% | {metrics['pvr_pre']:7.1f}% | {metrics['pvr_post']:6.1f}%")
    print("=" * 85)

    # Guardar en CSV para validación y auditoría
    csv_rows = []
    for model_name, metrics in results.items():
        csv_rows.append({
            "modelo": model_name,
            "precision_5": round(metrics['precision'], 4),
            "recall_5": round(metrics['recall'], 4),
            "ndcg_5": round(metrics['ndcg'], 4),
            "raw_precision_5": round(metrics.get('precision_raw', 0.0), 4),
            "raw_recall_5": round(metrics.get('recall_raw', 0.0), 4),
            "raw_ndcg_5": round(metrics.get('ndcg_raw', 0.0), 4),
            "coverage_pct": round(metrics['coverage'], 2),
            "pvr_pre_pct": round(metrics['pvr_pre'], 2),
            "pvr_post_pct": round(metrics['pvr_post'], 2),
            "filter_rate_pct": round(metrics.get('filter_rate_pct', 0.0), 2),
            "feasibility_at_5_pct": round(metrics.get('feasibility_at_5', 0.0), 2)
        })

    with open(METRICS_OUT_WARM, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(csv_rows[0].keys()))
        writer.writeheader()
        writer.writerows(csv_rows)
    print(f"✓ Métricas Warm Start guardadas en: {METRICS_OUT_WARM}\n")

    # ============================================================
    # FASE 2: COLD START (usuarios nuevos sin historial)
    # ============================================================
    print("\n" + "=" * 85)
    print("FASE 2: COLD START (USUARIOS NUEVOS SIN HISTORIAL)")
    print("=" * 85)

    # N_COLD_USERS proporcional al número de usuarios del dataset (v3: 1916).
    # Mantiene la proporción original (~20% de usuarios como "nuevos" sin historial).
    N_COLD_USERS = max(1, int(round(len(all_users) * 0.2)))
    train_pool_df, cold_test_df, cold_users, train_pool_users = make_cold_start_split(
        interactions_df, n_cold_users=N_COLD_USERS, seed=42
    )

    # Cold users con perfil del cuestionario (única información disponible)
    cold_user_profiles = users_df[users_df['user_id'].isin(cold_users)].copy()

    results_cold = {}

    # ------------------------------------------------------------
    # COLD 1: POPULARIDAD
    # ------------------------------------------------------------
    print("\n[Cold 1/4] Popularidad (PopRec)...")
    content_pop_cold = train_pool_df['content_id'].value_counts()
    cold_pop_preds = []
    for _, user in cold_user_profiles.iterrows():
        uid = user['user_id']
        user_preds = []
        for cid in all_contents:
            user_preds.append(content_pop_cold.get(cid, 0.0))
        cold_pop_preds.append(user_preds)
    cold_pop_df = pd.DataFrame(cold_pop_preds, index=cold_user_profiles['user_id'].tolist(), columns=all_contents)

    # Conocimiento inicial para Cold Start.
    # TODOS los cold users empiezan con mastered = set().
    # La diferencia entre 'alto'/'medio'/'bajo' en financial_knowledge_level
    # se manifestará únicamente en su comportamiento futuro (interacciones),
    # no se imputa al estado inicial. Esto evita inflar PVR Post artificialmente
    # y refleja fielmente el escenario "nuevo usuario sin historial".
    initial_mastered = {uid: set() for uid in cold_user_profiles['user_id']}

    results_cold["Popularidad"] = evaluate_predictions_cold(
        cold_pop_df, train_pool_df, cold_test_df, concept_prereqs, content_concepts,
        cold_users, initial_mastered=initial_mastered
    )

    # ------------------------------------------------------------
    # COLD 0 (BASELINE): RANDOM TOP-5
    # ------------------------------------------------------------
    # Selecciona 5 contenidos al azar del catálogo completo. NO consulta
    # cold_test_df en ningún caso (corrección de data leakage). En un sistema
    # real Cold Start el recomendador no conoce nada sobre el futuro del usuario,
    # por lo que debe seleccionar de TODO el catálogo sin exclusiones informadas
    # por el ground truth. Se usa seed fija (456) para reproducibilidad.
    print("\n[Baseline Cold] Random Top-5...")
    rng_random_cold = random.Random(456)
    random_cold_preds = []
    for uid in cold_users:
        chosen = rng_random_cold.sample(all_contents, K)
        row_vec = [1.0 if c in chosen else 0.0 for c in all_contents]
        random_cold_preds.append(row_vec)
    random_cold_df = pd.DataFrame(random_cold_preds, index=list(cold_users), columns=all_contents)
    results_cold["Random (baseline)"] = evaluate_predictions_cold(
        random_cold_df, train_pool_df, cold_test_df, concept_prereqs, content_concepts,
        cold_users, initial_mastered=initial_mastered
    )

    # ------------------------------------------------------------
    # COLD 2: TF-IDF con perfil textual del cuestionario
    # ------------------------------------------------------------
    print("\n[Cold 2/4] TF-IDF con perfil de cuestionario...")
    vectorizer_cold = TfidfVectorizer(stop_words=STOPWORDS_ES)
    tfidf_matrix_cold = vectorizer_cold.fit_transform(corpus)
    item_similarity_cold = cosine_similarity(tfidf_matrix_cold)
    similarity_df_cold = pd.DataFrame(item_similarity_cold, index=all_contents, columns=all_contents)

    # Perfil textual del cold user a partir de su cuestionario
    profile_cols_for_text = ['age_group', 'education_level', 'employment_status',
                             'financial_knowledge_level', 'saving_habit', 'sex', 'learning_goal']
    cold_user_texts = []
    cold_user_ids_ordered = []
    for _, user in cold_user_profiles.iterrows():
        text_parts = []
        for col in profile_cols_for_text:
            val = user[col]
            if pd.notna(val) and val != 'nan':
                text_parts.append(str(val))
        cold_user_texts.append(" ".join(text_parts))
        cold_user_ids_ordered.append(user['user_id'])

    user_profiles_cold = vectorizer_cold.transform(cold_user_texts)
    user_sim_cold = cosine_similarity(user_profiles_cold, tfidf_matrix_cold)

    cold_tfidf_preds = []
    for i, uid in enumerate(cold_user_ids_ordered):
        scores = user_sim_cold[i]
        cold_tfidf_preds.append(scores)
    cold_tfidf_df = pd.DataFrame(cold_tfidf_preds, index=cold_user_ids_ordered, columns=all_contents)
    results_cold["TF-IDF + Cosine (perfil)"] = evaluate_predictions_cold(
        cold_tfidf_df, train_pool_df, cold_test_df, concept_prereqs, content_concepts,
        cold_users, initial_mastered=initial_mastered
    )

    # ------------------------------------------------------------
    # COLD 3: HÍBRIDO SVD + RIDGE (VARIANTE PERFIL + CONTENIDO)
    # DOCUMENTACIÓN METODOLÓGICA IMPORTANTE:
    # En Cold Start no hay historial del usuario, por lo que la SVD no puede
    # generar un user embedding específico. Esta variante ELIMINA la señal
    # colaborativa (user_features_cf se sustituye por 0) y conserva solo las
    # features demográficas del perfil + features del contenido.
    # Por tanto, NO es comparable con el Híbrido SVD de Warm Start; es un
    # modelo conceptualmente diferente (regresor Ridge sobre features).
    # ------------------------------------------------------------
    print("\n[Cold 3/4] Híbrido SVD + Ridge (VARIANTE perfil + contenido, SIN señal colaborativa)...")

    # SVD entrenada SOLO sobre train_pool
    interaction_matrix_cold = train_pool_df.pivot_table(
        index='user_id', columns='content_id', values='score', fill_value=0.0
    )
    interaction_matrix_cold = interaction_matrix_cold.reindex(
        index=list(train_pool_users), columns=all_contents, fill_value=0.0
    )

    n_components_cold = min(10, len(all_contents) - 1)
    svd_cold = TruncatedSVD(n_components=n_components_cold, random_state=42)
    svd_cold.fit(interaction_matrix_cold)
    user_features_cf_train = svd_cold.transform(interaction_matrix_cold)
    content_features_cf_cold = svd_cold.components_.T

    # Features demográficas (las mismas columnas)
    user_cat_cols_cold = ['age_group', 'education_level', 'employment_status',
                          'financial_knowledge_level', 'saving_habit', 'sex']
    user_encoder_cold = OneHotEncoder(handle_unknown='ignore', sparse_output=False)
    user_encoder_cold.fit(users_df[user_cat_cols_cold])
    cold_users_encoded = user_encoder_cold.transform(
        cold_user_profiles[user_cat_cols_cold].fillna('desconocido')
    )

    # Entrenar Ridge solo con train_pool_users
    X_train_cold, y_train_cold = [], []
    for _, row in train_pool_df.iterrows():
        uid, cid, score = row['user_id'], row['content_id'], row['score']
        if uid not in interaction_matrix_cold.index:
            continue
        u_idx = list(interaction_matrix_cold.index).index(uid)
        c_idx = all_contents.index(cid)
        u_feat = user_encoder_cold.transform(users_df[users_df['user_id']==uid][user_cat_cols_cold].fillna('desconocido'))[0]
        c_feat = content_features_df.loc[cid].values
        interaction_vector = np.concatenate([
            [np.dot(user_features_cf_train[u_idx], content_features_cf_cold[c_idx])],
            u_feat,
            c_feat
        ])
        X_train_cold.append(interaction_vector)
        y_train_cold.append(score)

    recommender_cold = Ridge(alpha=1.0)
    recommender_cold.fit(X_train_cold, y_train_cold)

    # Predicción para cold users: la componente SVD del usuario es 0 (es nuevo)
    # Variante basada en perfil + contenido. Se documenta explícitamente como tal.
    cold_hybrid_preds = []
    for i, uid in enumerate(cold_user_ids_ordered):
        u_feat = cold_users_encoded[i]
        user_preds = []
        for c_idx, cid in enumerate(all_contents):
            c_feat = content_features_df.loc[cid].values
            vector = np.concatenate([
                [0.0],  # Cold start: componente colaborativa = 0
                u_feat,
                c_feat
            ])
            user_preds.append(recommender_cold.predict([vector])[0])
        cold_hybrid_preds.append(user_preds)
    cold_hybrid_df = pd.DataFrame(cold_hybrid_preds, index=cold_user_ids_ordered, columns=all_contents)
    results_cold["Profile + Content Ridge"] = evaluate_predictions_cold(
        cold_hybrid_df, train_pool_df, cold_test_df, concept_prereqs, content_concepts,
        cold_users, initial_mastered=initial_mastered
    )

    # ------------------------------------------------------------
    # COLD 4: NeuMF-Profile (variante sin user embedding)
    # ------------------------------------------------------------
    print("\n[Cold 4/4] NeuMF-Profile (variante explícita sin user embedding)...")

    # Para esta variante, construimos un MLP desde cero que toma como entrada
    # únicamente features del perfil (one-hot demográficas) + features de contenido
    # (one-hot). NO reutilizamos el user embedding del NeuMF original porque
    # los cold users no tienen vector entrenado.
    num_items = len(all_contents)
    item_oh = np.eye(num_items, dtype=np.float32)

    # Dataset: por cada interacción de train_pool, vector = [perfil | item_onehot]
    train_user_features_arr = []
    train_item_indices_arr = []
    train_scores_arr = []
    user_feat_by_id_cold = {uid: cold_users_encoded[i] for i, uid in enumerate(cold_user_ids_ordered)}
    for uid in train_pool_users:
        # Tomar el perfil demográfico (mismo encoder)
        row = users_df[users_df['user_id'] == uid]
        if row.empty:
            continue
        u_feat = user_encoder_cold.transform(row[user_cat_cols_cold].fillna('desconocido'))[0].astype(np.float32)
        user_inter = train_pool_df[train_pool_df['user_id'] == uid]
        if user_inter.empty:
            continue
        for _, irow in user_inter.iterrows():
            c_idx = all_contents.index(irow['content_id'])
            train_user_features_arr.append(u_feat)
            train_item_indices_arr.append(c_idx)
            train_scores_arr.append(irow['score'])

    if not train_user_features_arr:
        print("  [Aviso] No hay datos de train_pool; saltando NeuMF-Profile")
        results_cold["NeuMF-Profile (variante)"] = {"precision": 0, "recall": 0, "ndcg": 0, "coverage": 0, "pvr_pre": 0, "pvr_post": 0}
    else:
        # Implementación PyTorch REAL de NeuMF-Profile (no Ridge)
        # Mantiene las MISMAS condiciones que el NeuMF original:
        # latent_dim=8, dropout=0.2, MSELoss, Adam(lr=0.01, weight_decay=1e-4),
        # 15 épocas, batch_size=32, sigmoid output.
        X_user = np.stack(train_user_features_arr).astype(np.float32)
        X_item = item_oh[np.array(train_item_indices_arr)]
        X_combined = np.concatenate([X_user, X_item], axis=1).astype(np.float32)
        y_train_arr = np.array(train_scores_arr, dtype=np.float32)
        num_user_features = X_user.shape[1]

        # Dataset PyTorch
        class ProfileInteractionDataset(Dataset):
            def __init__(self, X, y):
                self.X = torch.tensor(X)
                self.y = torch.tensor(y)
            def __len__(self):
                return len(self.X)
            def __getitem__(self, idx):
                return self.X[idx], self.y[idx]

        profile_dataset = ProfileInteractionDataset(X_combined, y_train_arr)
        profile_dataloader = DataLoader(profile_dataset, batch_size=32, shuffle=True)

        # Instanciar NeuMFProfileMLP (definida arriba, misma arquitectura que NeuMFMLP
        # salvo que sustituye user embedding por un MLP sobre perfil demográfico)
        np.random.seed(42)
        torch.manual_seed(42)
        profile_net = NeuMFProfileMLP(num_user_features, num_items, latent_dim=8)
        profile_criterion = nn.MSELoss()
        profile_optimizer = optim.Adam(profile_net.parameters(), lr=0.01, weight_decay=1e-4)

        profile_net.train()
        for epoch in range(15):  # mismas 15 épocas que el NeuMF original
            for batch_X, batch_y in profile_dataloader:
                profile_optimizer.zero_grad()
                batch_user_feats = batch_X[:, :num_user_features]
                # item_onehot -> item_index: el item está en la posición argmax
                batch_item_idx = batch_X[:, num_user_features:].long().argmax(dim=-1)
                outputs = profile_net(batch_user_feats, batch_item_idx)
                loss = profile_criterion(outputs, batch_y)
                loss.backward()
                profile_optimizer.step()

        # Predicción para cold users
        profile_net.eval()
        cold_neumf_profile_preds = []
        cold_users_list = []
        with torch.no_grad():
            for i, uid in enumerate(cold_user_ids_ordered):
                u_feat = torch.tensor(cold_users_encoded[i].astype(np.float32)).unsqueeze(0)  # (1, num_user_features)
                item_indices = torch.arange(num_items)  # (num_items,)
                u_expanded = u_feat.repeat(num_items, 1)  # (num_items, num_user_features)
                outputs = profile_net(u_expanded, item_indices).numpy()
                cold_neumf_profile_preds.append(outputs.tolist())
                cold_users_list.append(uid)

        cold_neumf_profile_df = pd.DataFrame(cold_neumf_profile_preds, index=cold_users_list, columns=all_contents)
        results_cold["NeuMF-Profile (variante)"] = evaluate_predictions_cold(
            cold_neumf_profile_df, train_pool_df, cold_test_df, concept_prereqs, content_concepts,
            cold_users, initial_mastered=initial_mastered
        )

    # ============================================================
    # TABLA COLD START
    # ============================================================
    print("\n" + "=" * 85)
    print(f"{'MODELO COMPARATIVO DE IA - ESCENARIO COLD START':^85}")
    print("=" * 85)
    print(f"{'Modelo':50s} | {'P@5 RAW':7s} | {'P@5':7s} | {'R@5 RAW':7s} | {'R@5':7s} | {'NDCG RAW':9s} | {'NDCG':7s} | {'Coverage':8s} | {'PVR Pre':7s} | {'Post':6s}")
    print("-" * 85)
    for model_name, metrics in results_cold.items():
        print(f"{model_name:50s} | {metrics.get('precision_raw', 0):7.3f} | {metrics['precision']:7.3f} | {metrics.get('recall_raw', 0):7.3f} | {metrics['recall']:7.3f} | {metrics.get('ndcg_raw', 0):9.3f} | {metrics['ndcg']:7.3f} | {metrics['coverage']:7.1f}% | {metrics['pvr_pre']:7.1f}% | {metrics['pvr_post']:6.1f}%")
    print("=" * 85)

    # CSV separado para Cold Start
    csv_rows_cold = []
    for model_name, metrics in results_cold.items():
        csv_rows_cold.append({
            "modelo": model_name,
            "precision_5": round(metrics['precision'], 4),
            "recall_5": round(metrics['recall'], 4),
            "ndcg_5": round(metrics['ndcg'], 4),
            "raw_precision_5": round(metrics.get('precision_raw', 0.0), 4),
            "raw_recall_5": round(metrics.get('recall_raw', 0.0), 4),
            "raw_ndcg_5": round(metrics.get('ndcg_raw', 0.0), 4),
            "coverage_pct": round(metrics['coverage'], 2),
            "pvr_pre_pct": round(metrics['pvr_pre'], 2),
            "pvr_post_pct": round(metrics['pvr_post'], 2),
            "filter_rate_pct": round(metrics.get('filter_rate_pct', 0.0), 2),
            "feasibility_at_5_pct": round(metrics.get('feasibility_at_5', 0.0), 2)
        })

    with open(METRICS_OUT_COLD, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(csv_rows_cold[0].keys()))
        writer.writeheader()
        writer.writerows(csv_rows_cold)
    print(f"✓ Métricas Cold Start guardadas en: {METRICS_OUT_COLD}\n")

if __name__ == "__main__":
    main()
