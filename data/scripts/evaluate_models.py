"""
evaluate_models.py

Evaluación experimental de sistemas de recomendación.

ESCENARIOS
----------
1. WARM START
   Usuarios con historial disponible en Train.
   Se utiliza el historial de Train para generar recomendaciones
   y se evalúan contra interacciones futuras de Test.

2. COLD START
   Usuarios completamente nuevos.
   Ninguna interacción de estos usuarios aparece en Train.
   Se utilizan únicamente características del perfil/contenido.

MODELOS WARM START
------------------
1. Popularidad
2. Random
3. TF-IDF + Cosine personalizado
4. SVD
5. ItemKNN
6. UserKNN
7. GMF
8. NCF-MLP
9. NeuMF

MODELOS COLD START
------------------
1. Popularidad
2. Random
3. TF-IDF + perfil
4. Profile + Content Ridge
5. NeuMF-Profile

MÉTRICAS
--------
Precision@5
Recall@5
NDCG@5
Coverage

Opcionalmente:
PVR
Filter Rate
Feasibility@5

Autor: TFM - Recomendador de Educación Financiera

NOTA DE MANTENIMIENTO (fixes aplicados):
- build_profile_features ahora devuelve SIEMPRE una tupla
  (features, columnas_candidatas), en vez de un único DataFrame.
  Antes, todas las llamadas lo desempaquetaban en dos variables,
  lo cual fallaba (o daba resultados incorrectos) porque un
  DataFrame se itera por nombres de columna al desempaquetarlo.
- build_profile_features ahora construye las columnas dummy
  (one-hot) sobre TODO users_df, para que usuarios cold-start y
  usuarios de train queden en el mismo espacio de features.
- build_profile_features acepta un parámetro opcional
  `stats_ids`: la media/desviación estándar para normalizar se
  calcula solo sobre esa población (train_pool), y esa misma
  transformación se aplica a los usuarios cold-start. Antes se
  normalizaba con poblaciones distintas para train y para cold,
  lo que dejaba al modelo entrenando y prediciendo en escalas
  distintas.
- baseline_random ahora usa un hash determinista (hashlib) en
  vez de hash() de Python, cuya semilla varía entre procesos
  (PYTHONHASHSEED) y rompía la reproducibilidad de ese baseline.
- create_warm_split usa un sort estable (kind="mergesort") cuando
  no hay timestamp, para no perder el orden original de las
  interacciones de cada usuario.
"""

# ============================================================
# IMPORTS
# ============================================================

import os
import math
import random
import hashlib
import warnings

import numpy as np
import pandas as pd

from collections import defaultdict

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader

from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.linear_model import Ridge
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline

warnings.filterwarnings("ignore")


# ============================================================
# CONFIGURACIÓN
# ============================================================

SEED = 42

random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)

if torch.cuda.is_available():
    torch.cuda.manual_seed_all(SEED)

DATA_DIR = "data"

USERS_FILE = os.path.join(
    DATA_DIR,
    "users_synthetic.csv"
)

CONTENTS_FILE = os.path.join(
    DATA_DIR,
    "contents.csv"
)

INTERACTIONS_FILE = os.path.join(
    DATA_DIR,
    "interactions_synthetic_v3.csv"
)

OUTPUT_WARM = os.path.join(
    DATA_DIR,
    "evaluation_metrics_warm.csv"
)

OUTPUT_COLD = os.path.join(
    DATA_DIR,
    "evaluation_metrics_cold.csv"
)

OUTPUT_ALL = os.path.join(
    DATA_DIR,
    "evaluation_metrics_all_models.csv"
)

K = 5

WARM_TEST_RATIO = 0.20

COLD_USER_RATIO = 0.10

NEURAL_EPOCHS = 15
NEURAL_BATCH_SIZE = 32
NEURAL_LR = 0.01
NEURAL_WEIGHT_DECAY = 1e-4

# Learning rate específico para NeuMF-Profile (Cold Start).
# Con NEURAL_LR=0.01 el loss se estancaba de forma idéntica
# entre epochs (0.0630 en las epochs 5, 10 y 15), señal de que
# el optimizador estaba dando pasos demasiado grandes y
# quedándose atrapado cerca de un mínimo trivial (básicamente
# predecir la media). Un LR más bajo permite un descenso más
# gradual.
NEURAL_LR_PROFILE = 0.001

LATENT_DIM = 8

# scikit-learn NO trae un stop_words="spanish" incorporado
# (solo soporta el string "english"); por eso usamos una lista
# explícita de stopwords en español, compartida por todos los
# TfidfVectorizer del script.
SPANISH_STOP_WORDS = [
    "un", "una", "unas", "unos",
    "el", "la", "las", "los",
    "al", "del", "lo",
    "de", "en", "para", "por",
    "con", "sin", "sobre",
    "bajo", "entre", "hasta",
    "desde", "hacia", "y", "o",
    "u", "e", "pero", "mas",
    "como", "cuando", "donde",
    "quien", "que", "cual",
    "cuyo"
]


# ============================================================
# RELEVANCIA
# ============================================================

def event_to_relevance(event):
    """
    Convierte eventos en relevancia pedagógica.

    El vocabulario de eventos coincide con el que genera
    generate_interactions_v3.py: view, started, completed,
    quiz_passed, quiz_failed.

    Solo los eventos de dominio (completed/quiz_passed) son
    relevantes. Los pasivos (view/started) y los fallos
    (quiz_failed) tienen relevancia 0.

    Puedes modificar estos pesos únicamente si forman parte
    de la metodología definida en el TFM.
    """

    mapping = {
        "view": 0.0,
        "started": 0.0,
        "quiz_failed": 0.0,
        "quiz_passed": 0.7,
        "completed": 1.0,
    }

    return mapping.get(
        str(event).lower(),
        0.0
    )


def add_relevance_column(df):
    """
    Añade relevance si no existe.
    """

    df = df.copy()

    if "relevance" not in df.columns:

        if "event" in df.columns:
            df["relevance"] = df["event"].apply(
                event_to_relevance
            )

        elif "score" in df.columns:
            df["relevance"] = df["score"]

        else:
            raise ValueError(
                "No existe ni 'event', ni 'score' "
                "para calcular relevance."
            )

    if "score" not in df.columns:
        df["score"] = df["relevance"]

    return df


# ============================================================
# CONSOLIDACIÓN DE INTERACCIONES
# ============================================================

def consolidate_interactions(df):
    """
    Consolida múltiples eventos del mismo
    user_id-content_id.

    Se conserva el evento de mayor relevancia.

    Esto evita que el mismo par usuario-contenido
    aparezca repetido en Train/Test.
    """

    df = df.copy()

    df = add_relevance_column(df)

    print(
        f"Interacciones originales: {len(df)}"
    )

    duplicated = df.duplicated(
        subset=["user_id", "content_id"],
        keep=False
    ).sum()

    print(
        f"Duplicados user_id-content_id: {duplicated}"
    )

    # Ordenamos por relevancia
    df = df.sort_values(
        "relevance",
        ascending=False
    )

    # Conservamos una sola interacción
    # por usuario-contenido
    df = df.drop_duplicates(
        subset=["user_id", "content_id"],
        keep="first"
    )

    print(
        f"Pares únicos usuario-contenido: {len(df)}"
    )

    return df.reset_index(drop=True)


# ============================================================
# SPLIT WARM START
# ============================================================

def create_warm_split(
    interactions_df,
    test_ratio=0.20
):
    """
    Split temporal/ordenado por usuario.

    Para cada usuario:
        primeras interacciones -> Train
        últimas interacciones -> Test

    Si timestamp existe, se utiliza timestamp.
    """

    df = interactions_df.copy()

    if "timestamp" in df.columns:

        df["timestamp"] = pd.to_datetime(
            df["timestamp"],
            errors="coerce"
        )

        if df["timestamp"].notna().any():

            df = df.sort_values(
                ["user_id", "timestamp"]
            )

    else:

        # Orden original si no existe timestamp.
        # Usamos kind="mergesort" porque es un sort ESTABLE:
        # así conservamos el orden original de las interacciones
        # de cada usuario (el sort por defecto de pandas,
        # quicksort, no garantiza estabilidad y podía mezclar
        # el orden interno de cada grupo de usuario).
        df = df.sort_values(
            ["user_id"],
            kind="mergesort"
        )

    train_indices = []
    test_indices = []

    for uid, group in df.groupby(
        "user_id",
        sort=False
    ):

        group_indices = group.index.tolist()

        n = len(group_indices)

        if n <= 1:

            train_indices.extend(
                group_indices
            )

            continue

        n_test = max(
            1,
            int(np.ceil(n * test_ratio))
        )

        # Garantizamos al menos una interacción
        # para train cuando sea posible
        if n_test >= n:
            n_test = n - 1

        train_indices.extend(
            group_indices[:-n_test]
        )

        test_indices.extend(
            group_indices[-n_test:]
        )

    train_df = df.loc[
        train_indices
    ].copy()

    test_df = df.loc[
        test_indices
    ].copy()

    return (
        train_df.reset_index(drop=True),
        test_df.reset_index(drop=True)
    )


# ============================================================
# SPLIT COLD START
# ============================================================

def create_cold_split(
    interactions_df,
    cold_ratio=0.10
):
    """
    Selecciona usuarios completos como Cold Start.

    IMPORTANTE:
    Ninguna interacción de un cold user aparece en Train.

    Esto evita leakage.
    """

    df = interactions_df.copy()

    users = sorted(
        df["user_id"].unique()
    )

    rng = np.random.RandomState(SEED)

    n_cold = max(
        1,
        int(round(len(users) * cold_ratio))
    )

    cold_users = rng.choice(
        users,
        size=n_cold,
        replace=False
    )

    cold_users = set(
        cold_users.tolist()
    )

    cold_test_df = df[
        df["user_id"].isin(cold_users)
    ].copy()

    train_pool_df = df[
        ~df["user_id"].isin(cold_users)
    ].copy()

    return (
        train_pool_df.reset_index(drop=True),
        cold_test_df.reset_index(drop=True),
        sorted(cold_users)
    )


# ============================================================
# DIAGNÓSTICO
# ============================================================

def print_dataset_diagnostics(
    interactions_df,
    train_df,
    test_df
):

    print("\n")
    print("=" * 60)
    print("AUDITORÍA ESTADÍSTICA DEL DATASET")
    print("=" * 60)

    users = interactions_df[
        "user_id"
    ].nunique()

    contents = interactions_df[
        "content_id"
    ].nunique()

    positives = (
        interactions_df["score"] >= 0.5
    ).sum()

    print(
        f"  Usuarios únicos: {users}"
    )

    print(
        f"  Contenidos con interacción: {contents}"
    )

    print(
        f"  Interacciones consolidadas: "
        f"{len(interactions_df)}"
    )

    print(
        f"  Positivos (score >= 0.5): "
        f"{positives} "
        f"({positives / len(interactions_df) * 100:.1f}%)"
    )

    print(
        f"  Train: {len(train_df)}"
    )

    print(
        f"  Test: {len(test_df)}"
    )

    train_users = set(
        train_df["user_id"]
    )

    test_users = set(
        test_df["user_id"]
    )

    print(
        f"  Usuarios únicos Train: "
        f"{len(train_users)}"
    )

    print(
        f"  Usuarios únicos Test: "
        f"{len(test_users)}"
    )

    print(
        f"  Usuarios en ambos: "
        f"{len(train_users & test_users)}"
    )

    print(
        f"  Usuarios solo Train: "
        f"{len(train_users - test_users)}"
    )

    print(
        f"  Usuarios solo Test: "
        f"{len(test_users - train_users)}"
    )


# ============================================================
# MÉTRICAS
# ============================================================

def calculate_ndcg(
    recommended_ids,
    actual_relevant_ids,
    k=5
):

    recommended_ids = list(
        recommended_ids[:k]
    )

    actual_relevant_ids = set(
        actual_relevant_ids
    )

    dcg = 0.0

    for i, cid in enumerate(
        recommended_ids,
        start=1
    ):

        if cid in actual_relevant_ids:

            dcg += (
                1.0 /
                math.log2(i + 1)
            )

    ideal_hits = min(
        len(actual_relevant_ids),
        k
    )

    idcg = sum(
        1.0 /
        math.log2(i + 1)
        for i in range(1, ideal_hits + 1)
    )

    if idcg == 0:
        return 0.0

    return dcg / idcg


def evaluate_ranking(
    ranking,
    relevant,
    k=5
):

    ranking = list(ranking)

    top_k = ranking[:k]

    hits = len(
        set(top_k) & set(relevant)
    )

    precision = hits / k

    recall = (
        hits / len(relevant)
        if relevant
        else 0.0
    )

    ndcg = calculate_ndcg(
        ranking,
        relevant,
        k
    )

    return (
        precision,
        recall,
        ndcg
    )


# ============================================================
# POPULARIDAD
# ============================================================

def baseline_popularidad(
    train_df,
    contents_df
):

    counts = (
        train_df
        .groupby("content_id")
        .size()
        .sort_values(
            ascending=False
        )
    )

    catalog = contents_df[
        "content_id"
    ].tolist()

    ranking = [
        cid
        for cid in counts.index
        if cid in catalog
    ]

    # Agregar contenidos sin interacciones
    ranking += [
        cid
        for cid in catalog
        if cid not in ranking
    ]

    def rank_for_user(uid):
        return ranking

    return rank_for_user


# ============================================================
# RANDOM
# ============================================================

def baseline_random(
    train_df,
    contents_df
):

    catalog = contents_df[
        "content_id"
    ].tolist()

    def rank_for_user(uid):

        # Usamos un hash determinista (md5) en vez de hash()
        # de Python: hash() de strings está aleatorizado por
        # proceso (PYTHONHASHSEED) salvo que se desactive, lo
        # que rompía la reproducibilidad de este baseline entre
        # ejecuciones distintas aunque SEED estuviera fijo.
        digest = hashlib.md5(
            str(uid).encode("utf-8")
        ).hexdigest()

        user_hash = int(digest, 16) % 100000

        rng = random.Random(
            SEED + user_hash
        )

        ranking = catalog.copy()

        rng.shuffle(ranking)

        return ranking

    return rank_for_user


# ============================================================
# TF-IDF PERSONALIZADO
# ============================================================

def baseline_tfidf(
    train_df,
    contents_df
):

    content_ids = contents_df[
        "content_id"
    ].tolist()

    texts = (
        contents_df["title"].fillna("").astype(str)
        + " "
        + contents_df["summary"].fillna("").astype(str)
    )

    vectorizer = TfidfVectorizer(
        stop_words=SPANISH_STOP_WORDS
    )

    tfidf_matrix = vectorizer.fit_transform(
        texts
    )

    sim_matrix = cosine_similarity(
        tfidf_matrix
    )

    sim_df = pd.DataFrame(
        sim_matrix,
        index=content_ids,
        columns=content_ids
    )

    history_by_user = (
        train_df[
            train_df["score"] >= 0.5
        ]
        .groupby("user_id")["content_id"]
        .apply(list)
        .to_dict()
    )

    def rank_for_user(uid):

        history = history_by_user.get(
            uid,
            []
        )

        history = [
            cid
            for cid in history
            if cid in sim_df.index
        ]

        if not history:

            return list(
                sim_df.mean(axis=0)
                .sort_values(
                    ascending=False
                )
                .index
            )

        user_scores = (
            sim_df.loc[history]
            .mean(axis=0)
            .sort_values(
                ascending=False
            )
        )

        ranking = user_scores.index.tolist()

        # Quitar contenidos ya vistos
        ranking = [
            cid
            for cid in ranking
            if cid not in history
        ]

        return ranking

    return rank_for_user


# ============================================================
# SVD
# ============================================================

def baseline_svd(
    train_df,
    contents_df
):

    positive_df = train_df[
        train_df["score"] >= 0.5
    ]

    user_item = pd.pivot_table(
        positive_df,
        index="user_id",
        columns="content_id",
        values="score",
        aggfunc="max",
        fill_value=0
    )

    if user_item.shape[0] < 2:
        return baseline_popularidad(
            train_df,
            contents_df
        )

    n_components = min(
        20,
        user_item.shape[0] - 1,
        user_item.shape[1] - 1
    )

    if n_components < 1:
        return baseline_popularidad(
            train_df,
            contents_df
        )

    svd = TruncatedSVD(
        n_components=n_components,
        random_state=SEED
    )

    latent = svd.fit_transform(
        user_item
    )

    reconstructed = svd.inverse_transform(
        latent
    )

    reconstructed_df = pd.DataFrame(
        reconstructed,
        index=user_item.index,
        columns=user_item.columns
    )

    history_by_user = (
        positive_df
        .groupby("user_id")["content_id"]
        .apply(set)
        .to_dict()
    )

    def rank_for_user(uid):

        if uid not in reconstructed_df.index:

            return list(
                user_item.columns
            )

        scores = reconstructed_df.loc[
            uid
        ].sort_values(
            ascending=False
        )

        history = history_by_user.get(
            uid,
            set()
        )

        ranking = [
            cid
            for cid in scores.index
            if cid not in history
        ]

        return ranking

    return rank_for_user


# ============================================================
# ITEM KNN
# ============================================================

def baseline_item_knn(
    train_df,
    contents_df
):

    positive_df = train_df[
        train_df["score"] >= 0.5
    ]

    user_item = pd.pivot_table(
        positive_df,
        index="user_id",
        columns="content_id",
        values="score",
        aggfunc="max",
        fill_value=0
    )

    if user_item.shape[1] < 2:

        return baseline_popularidad(
            train_df,
            contents_df
        )

    sim_matrix = cosine_similarity(
        user_item.T
    )

    sim_df = pd.DataFrame(
        sim_matrix,
        index=user_item.columns,
        columns=user_item.columns
    )

    def rank_for_user(uid):

        if uid not in user_item.index:

            return list(
                user_item.columns
            )

        seen_items = (
            user_item.loc[uid]
            [user_item.loc[uid] > 0]
            .index
            .tolist()
        )

        scores = defaultdict(float)

        for item in seen_items:

            for other, sim in (
                sim_df[item].items()
            ):

                if other not in seen_items:

                    scores[other] += sim

        ranking = [
            cid
            for cid, _ in sorted(
                scores.items(),
                key=lambda x: -x[1]
            )
        ]

        return ranking

    return rank_for_user


# ============================================================
# USER KNN
# ============================================================

def baseline_user_knn(
    train_df,
    contents_df,
    n_neighbors=20
):

    positive_df = train_df[
        train_df["score"] >= 0.5
    ]

    user_item = pd.pivot_table(
        positive_df,
        index="user_id",
        columns="content_id",
        values="score",
        aggfunc="max",
        fill_value=0
    )

    if user_item.shape[0] < 2:

        return baseline_popularidad(
            train_df,
            contents_df
        )

    sim_matrix = cosine_similarity(
        user_item
    )

    sim_df = pd.DataFrame(
        sim_matrix,
        index=user_item.index,
        columns=user_item.index
    )

    def rank_for_user(uid):

        if uid not in user_item.index:

            return list(
                user_item.columns
            )

        neighbors = (
            sim_df.loc[uid]
            .sort_values(
                ascending=False
            )
            .index
            .tolist()
        )

        neighbors = [
            u
            for u in neighbors
            if u != uid
        ][:n_neighbors]

        seen = set(
            user_item.loc[uid]
            [user_item.loc[uid] > 0]
            .index
        )

        scores = defaultdict(float)

        for neighbor in neighbors:

            for item, value in (
                user_item.loc[neighbor].items()
            ):

                if (
                    item not in seen
                    and value > 0
                ):

                    scores[item] += value

        ranking = [
            cid
            for cid, _ in sorted(
                scores.items(),
                key=lambda x: -x[1]
            )
        ]

        return ranking

    return rank_for_user


# ============================================================
# DATASET NEURAL
# ============================================================

class InteractionDataset(Dataset):

    def __init__(
        self,
        users,
        items,
        scores
    ):

        self.users = torch.tensor(
            users,
            dtype=torch.long
        )

        self.items = torch.tensor(
            items,
            dtype=torch.long
        )

        self.scores = torch.tensor(
            scores,
            dtype=torch.float32
        )

    def __len__(self):

        return len(self.scores)

    def __getitem__(self, idx):

        return (
            self.users[idx],
            self.items[idx],
            self.scores[idx]
        )


# ============================================================
# GMF
# ============================================================

class GMF(nn.Module):

    def __init__(
        self,
        num_users,
        num_items,
        latent_dim=8
    ):

        super().__init__()

        self.user_embedding = nn.Embedding(
            num_users,
            latent_dim
        )

        self.item_embedding = nn.Embedding(
            num_items,
            latent_dim
        )

        self.output = nn.Sequential(
            nn.Linear(
                latent_dim,
                1
            ),
            nn.Sigmoid()
        )

    def forward(
        self,
        user_indices,
        item_indices
    ):

        u = self.user_embedding(
            user_indices
        )

        i = self.item_embedding(
            item_indices
        )

        x = u * i

        return self.output(
            x
        ).squeeze(-1)


# ============================================================
# NCF-MLP
# ============================================================

class NCFMLP(nn.Module):

    def __init__(
        self,
        num_users,
        num_items,
        latent_dim=8
    ):

        super().__init__()

        self.user_embedding = nn.Embedding(
            num_users,
            latent_dim
        )

        self.item_embedding = nn.Embedding(
            num_items,
            latent_dim
        )

        self.mlp = nn.Sequential(
            nn.Linear(
                latent_dim * 2,
                16
            ),
            nn.ReLU(),

            nn.Dropout(0.2),

            nn.Linear(
                16,
                8
            ),
            nn.ReLU(),

            nn.Dropout(0.2),

            nn.Linear(
                8,
                1
            ),

            nn.Sigmoid()
        )

    def forward(
        self,
        user_indices,
        item_indices
    ):

        u = self.user_embedding(
            user_indices
        )

        i = self.item_embedding(
            item_indices
        )

        x = torch.cat(
            [u, i],
            dim=-1
        )

        return self.mlp(
            x
        ).squeeze(-1)


# ============================================================
# NEUMF
# ============================================================

class NeuMF(nn.Module):

    def __init__(
        self,
        num_users,
        num_items,
        latent_dim=8
    ):

        super().__init__()

        # GMF branch
        self.gmf_user = nn.Embedding(
            num_users,
            latent_dim
        )

        self.gmf_item = nn.Embedding(
            num_items,
            latent_dim
        )

        # MLP branch
        self.mlp_user = nn.Embedding(
            num_users,
            latent_dim
        )

        self.mlp_item = nn.Embedding(
            num_items,
            latent_dim
        )

        self.mlp = nn.Sequential(
            nn.Linear(
                latent_dim * 2,
                16
            ),
            nn.ReLU(),

            nn.Dropout(0.2),

            nn.Linear(
                16,
                8
            ),
            nn.ReLU(),

            nn.Dropout(0.2)
        )

        self.output = nn.Sequential(
            nn.Linear(
                latent_dim + 8,
                1
            ),
            nn.Sigmoid()
        )

    def forward(
        self,
        user_indices,
        item_indices
    ):

        # GMF
        gu = self.gmf_user(
            user_indices
        )

        gi = self.gmf_item(
            item_indices
        )

        gmf = gu * gi

        # MLP
        mu = self.mlp_user(
            user_indices
        )

        mi = self.mlp_item(
            item_indices
        )

        mlp_input = torch.cat(
            [mu, mi],
            dim=-1
        )

        mlp_output = self.mlp(
            mlp_input
        )

        # Fusion
        x = torch.cat(
            [gmf, mlp_output],
            dim=-1
        )

        return self.output(
            x
        ).squeeze(-1)


# ============================================================
# ENTRENAMIENTO NEURAL
# ============================================================

def train_neural_model(
    model,
    train_df,
    user_to_idx,
    item_to_idx,
    epochs=15
):

    data = train_df[
        train_df["user_id"].isin(
            user_to_idx
        )
        &
        train_df["content_id"].isin(
            item_to_idx
        )
    ].copy()

    users = data[
        "user_id"
    ].map(user_to_idx).values

    items = data[
        "content_id"
    ].map(item_to_idx).values

    scores = data[
        "score"
    ].astype(float).values

    dataset = InteractionDataset(
        users,
        items,
        scores
    )

    loader = DataLoader(
        dataset,
        batch_size=NEURAL_BATCH_SIZE,
        shuffle=True
    )

    criterion = nn.MSELoss()

    optimizer = optim.Adam(
        model.parameters(),
        lr=NEURAL_LR,
        weight_decay=NEURAL_WEIGHT_DECAY
    )

    model.train()

    for epoch in range(
        epochs
    ):

        total_loss = 0.0

        for (
            batch_users,
            batch_items,
            batch_scores
        ) in loader:

            optimizer.zero_grad()

            outputs = model(
                batch_users,
                batch_items
            )

            loss = criterion(
                outputs,
                batch_scores
            )

            loss.backward()

            optimizer.step()

            total_loss += (
                loss.item()
                * len(batch_scores)
            )

        avg_loss = (
            total_loss /
            len(dataset)
        )

        if (
            (epoch + 1) % 5 == 0
            or epoch == 0
        ):

            print(
                f"    Epoch "
                f"{epoch + 1:02d}/{epochs} "
                f"- Loss: {avg_loss:.4f}"
            )

    return model


# ============================================================
# RANKING NEURAL WARM
# ============================================================

def neural_rank_function(
    model,
    user_to_idx,
    item_to_idx,
    contents_df,
    train_df
):

    catalog = contents_df[
        "content_id"
    ].tolist()

    history = (
        train_df
        .groupby("user_id")["content_id"]
        .apply(set)
        .to_dict()
    )

    model.eval()

    def rank_for_user(uid):

        if uid not in user_to_idx:

            return catalog

        user_idx = user_to_idx[
            uid
        ]

        candidates = [
            cid
            for cid in catalog
            if cid in item_to_idx
            and cid not in history.get(
                uid,
                set()
            )
        ]

        if not candidates:

            return []

        user_tensor = torch.tensor(
            [user_idx] * len(candidates),
            dtype=torch.long
        )

        item_tensor = torch.tensor(
            [
                item_to_idx[cid]
                for cid in candidates
            ],
            dtype=torch.long
        )

        with torch.no_grad():

            scores = model(
                user_tensor,
                item_tensor
            ).cpu().numpy()

        ranking = [
            cid
            for cid, _ in sorted(
                zip(candidates, scores),
                key=lambda x: -x[1]
            )
        ]

        return ranking

    return rank_for_user


# ============================================================
# EVALUACIÓN WARM
# ============================================================

def evaluate_warm_model(
    model,
    train_df,
    test_df,
    contents_df,
    k=5
):

    precisions = []
    recalls = []
    ndcgs = []

    recommended_set = set()

    users_evaluated = 0

    relevant_by_user = (
        test_df[
            test_df["score"] >= 0.5
        ]
        .groupby("user_id")["content_id"]
        .apply(set)
        .to_dict()
    )

    test_users = test_df[
        "user_id"
    ].unique()

    for uid in test_users:

        relevant = relevant_by_user.get(
            uid,
            set()
        )

        if not relevant:
            continue

        ranking = model(uid)

        top_k = ranking[:k]

        recommended_set.update(
            top_k
        )

        precision, recall, ndcg = (
            evaluate_ranking(
                ranking,
                relevant,
                k
            )
        )

        precisions.append(
            precision
        )

        recalls.append(
            recall
        )

        ndcgs.append(
            ndcg
        )

        users_evaluated += 1

    catalog_size = len(
        contents_df["content_id"].unique()
    )

    coverage = (
        len(recommended_set)
        / catalog_size
        * 100
        if catalog_size > 0
        else 0.0
    )

    return {
        "precision_5": np.mean(
            precisions
        ) if precisions else 0.0,

        "recall_5": np.mean(
            recalls
        ) if recalls else 0.0,

        "ndcg_5": np.mean(
            ndcgs
        ) if ndcgs else 0.0,

        "coverage": coverage,

        "users_evaluated":
            users_evaluated
    }


# ============================================================
# FEATURES DE PERFIL
# ============================================================

def build_profile_features(
    users_df,
    user_ids,
    stats_ids=None
):
    """
    Construye variables de perfil para los usuarios en `user_ids`.

    Devuelve SIEMPRE una tupla (features, columnas_candidatas):
        - features: DataFrame (float32) indexado por user_id,
          con las columnas numéricas/one-hot normalizadas.
        - columnas_candidatas: lista de nombres de columnas
          "crudas" detectadas en users_df (antes de one-hot),
          útil para funciones que necesitan trabajar con los
          valores originales (p. ej. TF-IDF por perfil).

    Detalles importantes:
    - Las columnas dummy (one-hot) se generan a partir de TODO
      users_df, no solo de `user_ids`. Así los usuarios
      cold-start quedan en el mismo espacio de features que los
      usuarios de entrenamiento (mismas columnas, mismo orden).
    - Si se pasa `stats_ids`, la media/desviación estándar usada
      para normalizar se calcula SOLO sobre esos usuarios
      (típicamente el train_pool). Esa misma transformación se
      aplica después a todos los usuarios de `user_ids`
      (incluidos los cold-start). Si no se pasa `stats_ids`, se
      normaliza usando la propia población de `user_ids` (
      comportamiento anterior, útil cuando no hay riesgo de
      mezclar poblaciones distintas).
    - Solo se aplica z-score (media/std) a las columnas
      numéricas originales. Las columnas dummy (one-hot,
      valores 0/1) generadas a partir de variables categóricas
      NO se normalizan: aplicarles z-score no aporta nada frente
      a dejarlas en 0/1 y puede exagerar la escala de categorías
      poco frecuentes.
    - No utiliza información de interacciones, para evitar fuga
      de información.
    """

    user_ids = list(user_ids)

    if "user_id" not in users_df.columns:
        raise ValueError(
            "users_df debe contener la columna 'user_id'."
        )

    # ---------------------------------------------------------
    # 1. Detectar variables de perfil sobre TODO users_df
    # ---------------------------------------------------------

    excluded_columns = {
        "user_id",
        "id",
        "userid",
        "user"
    }

    candidate_columns = [
        col
        for col in users_df.columns
        if col.lower() not in excluded_columns
    ]

    # Eliminar columnas completamente vacías
    candidate_columns = [
        col
        for col in candidate_columns
        if users_df[col].notna().any()
    ]

    # ---------------------------------------------------------
    # 2. Si no existen variables de perfil
    # ---------------------------------------------------------

    if len(candidate_columns) == 0:

        print(
            "\n[WARNING] users_df no contiene variables de perfil "
            "utilizables."
        )

        print(
            "[WARNING] Se utilizará un perfil neutro para Cold Start."
        )

        return pd.DataFrame(index=user_ids), []

    print(
        f"\n[Cold Start] Variables de perfil detectadas: "
        f"{candidate_columns}"
    )

    # ---------------------------------------------------------
    # 3. Construir la matriz de features sobre TODOS los
    #    usuarios de users_df (garantiza mismo espacio de
    #    columnas dummy para train y cold start)
    # ---------------------------------------------------------

    full_df = users_df.set_index("user_id")

    X_full = full_df[candidate_columns].copy()

    numeric_columns = []
    categorical_columns = []

    for col in X_full.columns:

        if pd.api.types.is_numeric_dtype(X_full[col]):
            numeric_columns.append(col)

        else:
            categorical_columns.append(col)

    # Variables numéricas
    for col in numeric_columns:

        X_full[col] = pd.to_numeric(
            X_full[col],
            errors="coerce"
        )

        median = X_full[col].median()

        if pd.isna(median):
            median = 0.0

        X_full[col] = X_full[col].fillna(median)

    # Variables categóricas
    if categorical_columns:

        X_full[categorical_columns] = (
            X_full[categorical_columns]
            .fillna("unknown")
            .astype(str)
        )

        # Guardamos qué columnas existían ANTES del one-hot,
        # para poder distinguir después las columnas dummy
        # (0/1) de las numéricas reales.
        columns_before_dummies = set(
            X_full.columns
        )

        X_full = pd.get_dummies(
            X_full,
            columns=categorical_columns,
            dummy_na=False
        )

        dummy_columns = [
            col
            for col in X_full.columns
            if col not in columns_before_dummies
        ]

    else:

        dummy_columns = []

    # Convertir todo a numérico
    X_full = X_full.apply(
        pd.to_numeric,
        errors="coerce"
    ).fillna(0.0)

    # ---------------------------------------------------------
    # 4. Normalización: media/std calculadas SOLO sobre
    #    stats_ids (o sobre user_ids si no se especifica).
    #    Solo se normalizan las columnas numéricas ORIGINALES;
    #    las columnas dummy (one-hot, 0/1) se dejan tal cual.
    # ---------------------------------------------------------

    stats_pop = stats_ids if stats_ids is not None else user_ids

    stats_pop = [
        uid
        for uid in stats_pop
        if uid in X_full.index
    ]

    if not stats_pop:
        stats_pop = X_full.index.tolist()

    for col in numeric_columns:

        ref_values = X_full.loc[stats_pop, col]

        mean = ref_values.mean()
        std = ref_values.std()

        if pd.notna(std) and std > 0:

            X_full[col] = (
                X_full[col] - mean
            ) / std

        else:

            X_full[col] = 0.0

    # Las columnas dummy (en dummy_columns) no se tocan: quedan
    # en 0/1 tal como las generó pd.get_dummies.

    # ---------------------------------------------------------
    # 5. Devolver solo las filas solicitadas (user_ids)
    # ---------------------------------------------------------

    X = X_full.reindex(user_ids).fillna(0.0)

    return X.astype(np.float32), candidate_columns

# ============================================================
# TF-IDF COLD START
# ============================================================

def cold_tfidf_profile(
    users_df,
    contents_df,
    cold_user_ids
):

    profile_features, profile_cols = (
        build_profile_features(
            users_df,
            cold_user_ids
        )
    )

    content_ids = contents_df[
        "content_id"
    ].tolist()

    texts = (
        contents_df["title"]
        .fillna("")
        .astype(str)
        + " "
        +
        contents_df["summary"]
        .fillna("")
        .astype(str)
    )

    vectorizer = TfidfVectorizer(
        stop_words=SPANISH_STOP_WORDS
    )

    content_matrix = vectorizer.fit_transform(
        texts
    )

    # Convertir cada perfil categórico
    # en una consulta textual sencilla.
    users_subset = users_df[
        users_df["user_id"].isin(
            cold_user_ids
        )
    ].copy()

    for col in profile_cols:

        users_subset[col] = (
            users_subset[col]
            .fillna("desconocido")
            .astype(str)
        )

    profile_text = {}

    for _, row in users_subset.iterrows():

        tokens = []

        for col in profile_cols:

            tokens.append(
                f"{col}_{row[col]}"
            )

        profile_text[
            row["user_id"]
        ] = " ".join(tokens)

    # Si los atributos del perfil no comparten
    # vocabulario con los contenidos, TF-IDF
    # no podrá relacionarlos directamente.
    # Por eso utilizamos también una señal
    # global basada en contenido.

    global_scores = np.asarray(
        content_matrix.mean(axis=1)
    ).ravel()

    def rank_for_user(uid):

        # Ranking base
        scores = global_scores.copy()

        # Perfil textual
        text = profile_text.get(
            uid,
            ""
        )

        if text.strip():

            profile_vec = vectorizer.transform(
                [text]
            )

            if profile_vec.nnz > 0:

                similarity = (
                    cosine_similarity(
                        profile_vec,
                        content_matrix
                    )
                    .ravel()
                )

                scores = similarity

        order = np.argsort(
            -scores
        )

        return [
            content_ids[i]
            for i in order
        ]

    return rank_for_user


# ============================================================
# PROFILE + CONTENT RIDGE
# ============================================================

def cold_profile_content_ridge(
    users_df,
    contents_df,
    train_pool_df,
    cold_user_ids
):

    profile_features, profile_cols = (
        build_profile_features(
            users_df,
            cold_user_ids
        )
    )

    content_ids = contents_df[
        "content_id"
    ].tolist()

    content_to_idx = {
        cid: i
        for i, cid in enumerate(
            content_ids
        )
    }

    texts = (
        contents_df["title"]
        .fillna("")
        .astype(str)
        + " "
        +
        contents_df["summary"]
        .fillna("")
        .astype(str)
    )

    tfidf = TfidfVectorizer(
        stop_words=SPANISH_STOP_WORDS
    )

    content_matrix = tfidf.fit_transform(
        texts
    ).toarray()

    # Características de contenido reducidas
    if content_matrix.shape[1] > 30:

        svd = TruncatedSVD(
            n_components=30,
            random_state=SEED
        )

        content_matrix = svd.fit_transform(
            content_matrix
        )

    content_features = pd.DataFrame(
        content_matrix,
        index=content_ids
    )

    # Crear entrenamiento a partir de usuarios
    # que sí están en train_pool.
    #
    # El perfil se cruza con el contenido.
    profile_map = {}

    users_subset = users_df[
        users_df["user_id"].isin(
            train_pool_df["user_id"].unique()
        )
    ].copy()

    for col in profile_cols:

        users_subset[col] = (
            users_subset[col]
            .fillna("desconocido")
            .astype(str)
        )

    encoder = OneHotEncoder(
        handle_unknown="ignore",
        sparse_output=False
    )

    user_encoded = encoder.fit_transform(
        users_subset[profile_cols]
    )

    user_feature_map = {
        uid: feat
        for uid, feat in zip(
            users_subset["user_id"],
            user_encoded
        )
    }

    X_train = []
    y_train = []

    for _, row in train_pool_df.iterrows():

        uid = row["user_id"]
        cid = row["content_id"]

        if uid not in user_feature_map:
            continue

        if cid not in content_to_idx:
            continue

        ufeat = user_feature_map[uid]

        cfeat = content_features.loc[
            cid
        ].values

        X_train.append(
            np.concatenate(
                [ufeat, cfeat]
            )
        )

        y_train.append(
            float(row["score"])
        )

    if not X_train:

        # Fallback
        return cold_tfidf_profile(
            users_df,
            contents_df,
            cold_user_ids
        )

    X_train = np.asarray(
        X_train,
        dtype=np.float32
    )

    y_train = np.asarray(
        y_train,
        dtype=np.float32
    )

    model = Ridge(
        alpha=1.0
    )

    model.fit(
        X_train,
        y_train
    )

    cold_profile_map = {}

    users_cold = users_df[
        users_df["user_id"].isin(
            cold_user_ids
        )
    ].copy()

    for col in profile_cols:

        users_cold[col] = (
            users_cold[col]
            .fillna("desconocido")
            .astype(str)
        )

    cold_encoded = encoder.transform(
        users_cold[profile_cols]
    )

    for uid, feat in zip(
        users_cold["user_id"],
        cold_encoded
    ):

        cold_profile_map[
            uid
        ] = feat

    def rank_for_user(uid):

        if uid not in cold_profile_map:

            return content_ids

        ufeat = cold_profile_map[
            uid
        ]

        candidates = []

        for cid in content_ids:

            cfeat = content_features.loc[
                cid
            ].values

            x = np.concatenate(
                [ufeat, cfeat]
            ).reshape(1, -1)

            score = model.predict(
                x
            )[0]

            candidates.append(
                (cid, score)
            )

        candidates.sort(
            key=lambda x: -x[1]
        )

        return [
            cid
            for cid, _ in candidates
        ]

    return rank_for_user


# ============================================================
# NEUMF PROFILE COLD START
# ============================================================

class NeuMFProfile(nn.Module):

    def __init__(
        self,
        num_user_features,
        num_items,
        latent_dim=8
    ):

        super().__init__()

        # Encoder de perfil
        self.user_encoder = nn.Sequential(

            nn.Linear(
                num_user_features,
                16
            ),

            nn.ReLU(),

            nn.Linear(
                16,
                latent_dim
            )
        )

        # Embedding de contenido
        self.item_embed = nn.Embedding(
            num_items,
            latent_dim
        )

        # MLP
        self.mlp = nn.Sequential(

            nn.Linear(
                latent_dim * 2,
                16
            ),

            nn.ReLU(),

            nn.Dropout(0.2),

            nn.Linear(
                16,
                8
            ),

            nn.ReLU(),

            nn.Dropout(0.2),

            nn.Linear(
                8,
                1
            ),

            nn.Sigmoid()
        )

    def forward(
        self,
        user_features,
        item_indices
    ):

        u_emb = self.user_encoder(
            user_features
        )

        i_emb = self.item_embed(
            item_indices
        )

        x = torch.cat(
            [u_emb, i_emb],
            dim=-1
        )

        return self.mlp(
            x
        ).squeeze(-1)


class ProfileInteractionDataset(
    Dataset
):

    def __init__(
        self,
        X_user,
        X_item,
        y
    ):

        self.X_user = torch.tensor(
            X_user,
            dtype=torch.float32
        )

        self.X_item = torch.tensor(
            X_item,
            dtype=torch.long
        )

        self.y = torch.tensor(
            y,
            dtype=torch.float32
        )

    def __len__(self):

        return len(self.y)

    def __getitem__(self, idx):

        return (
            self.X_user[idx],
            self.X_item[idx],
            self.y[idx]
        )


def train_neumf_profile(
    users_df,
    contents_df,
    train_pool_df,
    cold_user_ids
):

    # --------------------------------------------------------
    # Features de perfil: se calculan en UNA sola llamada para
    # la unión de usuarios de train_pool y cold_user_ids, con
    # las estadísticas de normalización (media/std) calculadas
    # SOLO sobre train_pool_df. Así:
    #   - train y cold quedan en el mismo espacio de columnas
    #     (mismas dummies, mismo orden).
    #   - ambos se normalizan con la misma escala, la que "ve"
    #     el modelo durante el entrenamiento.
    #   - no hay fuga de estadísticas de los cold users hacia
    #     el entrenamiento.
    # --------------------------------------------------------

    train_pool_user_ids = (
        train_pool_df["user_id"].unique().tolist()
    )

    all_relevant_ids = sorted(
        set(train_pool_user_ids) | set(cold_user_ids)
    )

    all_users_profile, profile_cols = (
        build_profile_features(
            users_df,
            all_relevant_ids,
            stats_ids=train_pool_user_ids
        )
    )

    profile_dim = (
        all_users_profile.shape[1]
    )

    content_ids = contents_df[
        "content_id"
    ].tolist()

    item_to_idx = {
        cid: idx
        for idx, cid in enumerate(
            content_ids
        )
    }

    # --------------------------------------------------------
    # Features de usuarios de Train Pool
    # --------------------------------------------------------

    user_feature_map = {}

    for uid in train_pool_df[
        "user_id"
    ].unique():

        if uid in all_users_profile.index:

            user_feature_map[
                uid
            ] = all_users_profile.loc[
                uid
            ].values.astype(
                np.float32
            )

    X_user = []
    X_item = []
    y = []

    for _, row in train_pool_df.iterrows():

        uid = row["user_id"]
        cid = row["content_id"]

        if uid not in user_feature_map:
            continue

        if cid not in item_to_idx:
            continue

        X_user.append(
            user_feature_map[uid]
        )

        X_item.append(
            item_to_idx[cid]
        )

        y.append(
            float(row["score"])
        )

    X_user = np.asarray(
        X_user,
        dtype=np.float32
    )

    X_item = np.asarray(
        X_item,
        dtype=np.int64
    )

    y = np.asarray(
        y,
        dtype=np.float32
    )

    print(
        f"  Interacciones entrenamiento: "
        f"{len(y)}"
    )

    print(
        f"  Features de usuario: "
        f"{profile_dim}"
    )

    print(
        f"  Contenidos: "
        f"{len(content_ids)}"
    )

    dataset = ProfileInteractionDataset(
        X_user,
        X_item,
        y
    )

    loader = DataLoader(
        dataset,
        batch_size=32,
        shuffle=True
    )

    torch.manual_seed(SEED)
    np.random.seed(SEED)

    model = NeuMFProfile(
        num_user_features=profile_dim,
        num_items=len(content_ids),
        latent_dim=LATENT_DIM
    )

    criterion = nn.MSELoss()

    optimizer = optim.Adam(
        model.parameters(),
        lr=NEURAL_LR_PROFILE,
        weight_decay=NEURAL_WEIGHT_DECAY
    )

    model.train()

    for epoch in range(
        NEURAL_EPOCHS
    ):

        total_loss = 0.0

        for (
            batch_user,
            batch_item,
            batch_y
        ) in loader:

            optimizer.zero_grad()

            outputs = model(
                batch_user,
                batch_item
            )

            loss = criterion(
                outputs,
                batch_y
            )

            loss.backward()

            optimizer.step()

            total_loss += (
                loss.item()
                * len(batch_y)
            )

        avg_loss = (
            total_loss /
            len(dataset)
        )

        if (
            (epoch + 1) % 5 == 0
        ):

            print(
                f"    Epoch "
                f"{epoch + 1:02d}/"
                f"{NEURAL_EPOCHS} "
                f"- Loss: "
                f"{avg_loss:.4f}"
            )

    # --------------------------------------------------------
    # Ranking function
    # --------------------------------------------------------

    model.eval()

    cold_profile_map = {
        uid:
        all_users_profile.loc[
            uid
        ].values.astype(
            np.float32
        )
        for uid in cold_user_ids
        if uid in all_users_profile.index
    }

    def rank_for_user(uid):

        if uid not in cold_profile_map:

            return content_ids

        user_feat = torch.tensor(
            np.repeat(
                cold_profile_map[uid][
                    None, :
                ],
                len(content_ids),
                axis=0
            ),
            dtype=torch.float32
        )

        item_idx = torch.tensor(
            np.arange(
                len(content_ids)
            ),
            dtype=torch.long
        )

        with torch.no_grad():

            scores = model(
                user_feat,
                item_idx
            ).cpu().numpy()

        ranking = [
            cid
            for cid, _ in sorted(
                zip(
                    content_ids,
                    scores
                ),
                key=lambda x: -x[1]
            )
        ]

        return ranking

    return rank_for_user


# ============================================================
# EVALUACIÓN COLD
# ============================================================

def evaluate_cold_model(
    model,
    train_df,
    test_df,
    contents_df,
    cold_users,
    k=5
):

    precisions = []
    recalls = []
    ndcgs = []

    recommended_set = set()

    relevant_by_user = (
        test_df[
            test_df["score"] >= 0.5
        ]
        .groupby("user_id")["content_id"]
        .apply(set)
        .to_dict()
    )

    users_evaluated = 0

    for uid in cold_users:

        relevant = relevant_by_user.get(
            uid,
            set()
        )

        if not relevant:
            continue

        ranking = model(uid)

        precision, recall, ndcg = (
            evaluate_ranking(
                ranking,
                relevant,
                k
            )
        )

        precisions.append(
            precision
        )

        recalls.append(
            recall
        )

        ndcgs.append(
            ndcg
        )

        recommended_set.update(
            ranking[:k]
        )

        users_evaluated += 1

    catalog_size = len(
        contents_df[
            "content_id"
        ].unique()
    )

    coverage = (
        len(recommended_set)
        / catalog_size
        * 100
        if catalog_size > 0
        else 0.0
    )

    return {
        "precision_5": np.mean(
            precisions
        ) if precisions else 0.0,

        "recall_5": np.mean(
            recalls
        ) if recalls else 0.0,

        "ndcg_5": np.mean(
            ndcgs
        ) if ndcgs else 0.0,

        "coverage": coverage,

        "users_evaluated":
            users_evaluated
    }


# ============================================================
# ENTRENAR Y EVALUAR MODELOS WARM
# ============================================================

def run_warm_evaluation(
    train_df,
    test_df,
    contents_df
):

    print("\n")
    print("=" * 80)
    print("FASE 1: WARM START")
    print("=" * 80)

    results = []

    # --------------------------------------------------------
    # 1. Popularidad
    # --------------------------------------------------------

    print(
        "\n[Warm 1/9] Popularidad..."
    )

    model = baseline_popularidad(
        train_df,
        contents_df
    )

    metrics = evaluate_warm_model(
        model,
        train_df,
        test_df,
        contents_df,
        K
    )

    metrics["modelo"] = "Popularidad"
    results.append(metrics)

    # --------------------------------------------------------
    # 2. Random
    # --------------------------------------------------------

    print(
        "\n[Warm 2/9] Random baseline..."
    )

    model = baseline_random(
        train_df,
        contents_df
    )

    metrics = evaluate_warm_model(
        model,
        train_df,
        test_df,
        contents_df,
        K
    )

    metrics["modelo"] = "Random"
    results.append(metrics)

    # --------------------------------------------------------
    # 3. TF-IDF
    # --------------------------------------------------------

    print(
        "\n[Warm 3/9] TF-IDF + Cosine personalizado..."
    )

    model = baseline_tfidf(
        train_df,
        contents_df
    )

    metrics = evaluate_warm_model(
        model,
        train_df,
        test_df,
        contents_df,
        K
    )

    metrics["modelo"] = (
        "TF-IDF + Cosine"
    )

    results.append(metrics)

    # --------------------------------------------------------
    # 4. SVD
    # --------------------------------------------------------

    print(
        "\n[Warm 4/9] SVD..."
    )

    model = baseline_svd(
        train_df,
        contents_df
    )

    metrics = evaluate_warm_model(
        model,
        train_df,
        test_df,
        contents_df,
        K
    )

    metrics["modelo"] = "SVD"
    results.append(metrics)

    # --------------------------------------------------------
    # 5. ItemKNN
    # --------------------------------------------------------

    print(
        "\n[Warm 5/9] ItemKNN..."
    )

    model = baseline_item_knn(
        train_df,
        contents_df
    )

    metrics = evaluate_warm_model(
        model,
        train_df,
        test_df,
        contents_df,
        K
    )

    metrics["modelo"] = "ItemKNN"
    results.append(metrics)

    # --------------------------------------------------------
    # 6. UserKNN
    # --------------------------------------------------------

    print(
        "\n[Warm 6/9] UserKNN..."
    )

    model = baseline_user_knn(
        train_df,
        contents_df
    )

    metrics = evaluate_warm_model(
        model,
        train_df,
        test_df,
        contents_df,
        K
    )

    metrics["modelo"] = "UserKNN"
    results.append(metrics)

    # --------------------------------------------------------
    # Mapas para modelos neuronales
    # --------------------------------------------------------

    all_users = sorted(
        train_df["user_id"].unique()
    )

    all_items = contents_df[
        "content_id"
    ].tolist()

    user_to_idx = {
        uid: i
        for i, uid in enumerate(
            all_users
        )
    }

    item_to_idx = {
        cid: i
        for i, cid in enumerate(
            all_items
        )
    }

    # --------------------------------------------------------
    # 7. GMF
    # --------------------------------------------------------

    print(
        "\n[Warm 7/9] GMF..."
    )

    torch.manual_seed(SEED)

    gmf = GMF(
        num_users=len(user_to_idx),
        num_items=len(item_to_idx),
        latent_dim=LATENT_DIM
    )

    gmf = train_neural_model(
        gmf,
        train_df,
        user_to_idx,
        item_to_idx
    )

    model = neural_rank_function(
        gmf,
        user_to_idx,
        item_to_idx,
        contents_df,
        train_df
    )

    metrics = evaluate_warm_model(
        model,
        train_df,
        test_df,
        contents_df,
        K
    )

    metrics["modelo"] = "GMF"
    results.append(metrics)

    # --------------------------------------------------------
    # 8. NCF MLP
    # --------------------------------------------------------

    print(
        "\n[Warm 8/9] NCF-MLP..."
    )

    torch.manual_seed(SEED)

    ncf = NCFMLP(
        num_users=len(user_to_idx),
        num_items=len(item_to_idx),
        latent_dim=LATENT_DIM
    )

    ncf = train_neural_model(
        ncf,
        train_df,
        user_to_idx,
        item_to_idx
    )

    model = neural_rank_function(
        ncf,
        user_to_idx,
        item_to_idx,
        contents_df,
        train_df
    )

    metrics = evaluate_warm_model(
        model,
        train_df,
        test_df,
        contents_df,
        K
    )

    metrics["modelo"] = "NCF-MLP"
    results.append(metrics)

    # --------------------------------------------------------
    # 9. NeuMF
    # --------------------------------------------------------

    print(
        "\n[Warm 9/9] NeuMF..."
    )

    torch.manual_seed(SEED)

    neumf = NeuMF(
        num_users=len(user_to_idx),
        num_items=len(item_to_idx),
        latent_dim=LATENT_DIM
    )

    neumf = train_neural_model(
        neumf,
        train_df,
        user_to_idx,
        item_to_idx
    )

    model = neural_rank_function(
        neumf,
        user_to_idx,
        item_to_idx,
        contents_df,
        train_df
    )

    metrics = evaluate_warm_model(
        model,
        train_df,
        test_df,
        contents_df,
        K
    )

    metrics["modelo"] = "NeuMF"
    results.append(metrics)

    return pd.DataFrame(
        results
    )


# ============================================================
# ENTRENAR Y EVALUAR COLD
# ============================================================

def run_cold_evaluation(
    train_pool_df,
    cold_test_df,
    users_df,
    contents_df,
    cold_users
):

    print("\n")
    print("=" * 80)
    print("FASE 2: COLD START")
    print("=" * 80)

    print(
        f"  Train pool: "
        f"{len(train_pool_df)} interacciones"
    )

    print(
        f"  Cold users: "
        f"{len(cold_users)} usuarios"
    )

    # --------------------------------------------------------
    # Anti leakage
    # --------------------------------------------------------

    leakage = (
        set(train_pool_df["user_id"])
        &
        set(cold_users)
    )

    if leakage:

        raise RuntimeError(
            f"ERROR: {len(leakage)} "
            f"cold users aparecen en Train."
        )

    print(
        "  [OK] Validación anti-fuga: "
        "0 cold users en train_pool"
    )

    results = []

    # --------------------------------------------------------
    # 1. Popularidad
    # --------------------------------------------------------

    print(
        "\n[Cold 1/5] Popularidad..."
    )

    model = baseline_popularidad(
        train_pool_df,
        contents_df
    )

    metrics = evaluate_cold_model(
        model,
        train_pool_df,
        cold_test_df,
        contents_df,
        cold_users,
        K
    )

    metrics["modelo"] = "Popularidad"

    results.append(metrics)

    # --------------------------------------------------------
    # 2. Random
    # --------------------------------------------------------

    print(
        "\n[Cold 2/5] Random baseline..."
    )

    model = baseline_random(
        train_pool_df,
        contents_df
    )

    metrics = evaluate_cold_model(
        model,
        train_pool_df,
        cold_test_df,
        contents_df,
        cold_users,
        K
    )

    metrics["modelo"] = "Random"

    results.append(metrics)

    # --------------------------------------------------------
    # 3. TF-IDF perfil
    # --------------------------------------------------------

    print(
        "\n[Cold 3/5] TF-IDF + perfil..."
    )

    model = cold_tfidf_profile(
        users_df,
        contents_df,
        cold_users
    )

    metrics = evaluate_cold_model(
        model,
        train_pool_df,
        cold_test_df,
        contents_df,
        cold_users,
        K
    )

    metrics["modelo"] = (
        "TF-IDF + Cosine (perfil)"
    )

    results.append(metrics)

    # --------------------------------------------------------
    # 4. Profile + Content Ridge
    # --------------------------------------------------------

    print(
        "\n[Cold 4/5] Profile + Content Ridge..."
    )

    model = cold_profile_content_ridge(
        users_df,
        contents_df,
        train_pool_df,
        cold_users
    )

    metrics = evaluate_cold_model(
        model,
        train_pool_df,
        cold_test_df,
        contents_df,
        cold_users,
        K
    )

    metrics["modelo"] = (
        "Profile + Content Ridge"
    )

    results.append(metrics)

    # --------------------------------------------------------
    # 5. NeuMF Profile
    # --------------------------------------------------------

    print(
        "\n[Cold 5/5] NeuMF-Profile..."
    )

    model = train_neumf_profile(
        users_df,
        contents_df,
        train_pool_df,
        cold_users
    )

    metrics = evaluate_cold_model(
        model,
        train_pool_df,
        cold_test_df,
        contents_df,
        cold_users,
        K
    )

    metrics["modelo"] = (
        "NeuMF-Profile"
    )

    results.append(metrics)

    return pd.DataFrame(
        results
    )


# ============================================================
# IMPRESIÓN DE RESULTADOS
# ============================================================

def print_results(
    df,
    title
):

    print("\n")
    print("=" * 100)
    print(title)
    print("=" * 100)

    print(
        f"{'Modelo':25} | "
        f"{'P@5':>8} | "
        f"{'R@5':>8} | "
        f"{'NDCG@5':>9} | "
        f"{'Coverage':>10}"
    )

    print("-" * 100)

    for _, row in df.iterrows():

        print(
            f"{row['modelo']:25} | "
            f"{row['precision_5']:8.4f} | "
            f"{row['recall_5']:8.4f} | "
            f"{row['ndcg_5']:9.4f} | "
            f"{row['coverage']:9.2f}%"
        )

    print("=" * 100)

    best_idx = df[
        "ndcg_5"
    ].idxmax()

    best = df.loc[
        best_idx
    ]

    print(
        "\nMEJOR MODELO SEGÚN NDCG@5"
    )

    print(
        f"Modelo: {best['modelo']}"
    )

    print(
        f"Precision@5: "
        f"{best['precision_5']:.4f}"
    )

    print(
        f"Recall@5: "
        f"{best['recall_5']:.4f}"
    )

    print(
        f"NDCG@5: "
        f"{best['ndcg_5']:.4f}"
    )

    print(
        f"Coverage: "
        f"{best['coverage']:.2f}%"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 80)
    print(
        "INICIANDO EVALUACIÓN "
        "CON WARM START + COLD START"
    )
    print("=" * 80)

    # ========================================================
    # CARGAR DATOS
    # ========================================================

    print("\n")
    print("=" * 80)
    print(
        "PREPARACIÓN DEL DATASET"
    )
    print("=" * 80)

    users_df = pd.read_csv(
        USERS_FILE
    )

    contents_df = pd.read_csv(
        CONTENTS_FILE
    )

    interactions_df = pd.read_csv(
        INTERACTIONS_FILE
    )

    # ========================================================
    # CONSOLIDACIÓN
    # ========================================================

    interactions_df = (
        consolidate_interactions(
            interactions_df
        )
    )

    # ========================================================
    # DISTRIBUCIONES
    # ========================================================

    print(
        "\nDistribución de relevance:"
    )

    print(
        interactions_df[
            "relevance"
        ].value_counts(
            sort=False
        ).sort_index()
    )

    if "event" in interactions_df.columns:

        print(
            "\nDistribución de eventos:"
        )

        print(
            interactions_df[
                "event"
            ].value_counts(
                normalize=True
            ).round(3)
        )

    # ========================================================
    # WARM SPLIT
    # ========================================================

    warm_train, warm_test = (
        create_warm_split(
            interactions_df,
            WARM_TEST_RATIO
        )
    )

    print_dataset_diagnostics(
        interactions_df,
        warm_train,
        warm_test
    )

    # ========================================================
    # WARM EVALUATION
    # ========================================================

    warm_results = run_warm_evaluation(
        warm_train,
        warm_test,
        contents_df
    )

    # Ordenar por NDCG
    warm_results = warm_results.sort_values(
        "ndcg_5",
        ascending=False
    ).reset_index(
        drop=True
    )

    # Guardar
    warm_results.to_csv(
        OUTPUT_WARM,
        index=False
    )

    print_results(
        warm_results,
        "MODELO COMPARATIVO - WARM START"
    )

    print(
        f"\n[OK] Métricas Warm Start guardadas en:"
        f"\n{OUTPUT_WARM}"
    )

    # ========================================================
    # COLD SPLIT
    # ========================================================

    (
        cold_train_pool,
        cold_test,
        cold_users
    ) = create_cold_split(
        interactions_df,
        COLD_USER_RATIO
    )

    # ========================================================
    # COLD EVALUATION
    # ========================================================

    cold_results = run_cold_evaluation(
        cold_train_pool,
        cold_test,
        users_df,
        contents_df,
        cold_users
    )

    cold_results = cold_results.sort_values(
        "ndcg_5",
        ascending=False
    ).reset_index(
        drop=True
    )

    cold_results.to_csv(
        OUTPUT_COLD,
        index=False
    )

    print_results(
        cold_results,
        "MODELO COMPARATIVO - COLD START"
    )

    print(
        f"\n[OK] Métricas Cold Start guardadas en:"
        f"\n{OUTPUT_COLD}"
    )

    # ========================================================
    # COMPARATIVO GENERAL
    # ========================================================

    warm_export = warm_results.copy()

    warm_export[
        "escenario"
    ] = "Warm Start"

    cold_export = cold_results.copy()

    cold_export[
        "escenario"
    ] = "Cold Start"

    all_results = pd.concat(
        [
            warm_export,
            cold_export
        ],
        ignore_index=True
    )

    all_results = all_results[
        [
            "escenario",
            "modelo",
            "precision_5",
            "recall_5",
            "ndcg_5",
            "coverage",
            "users_evaluated"
        ]
    ]

    all_results.to_csv(
        OUTPUT_ALL,
        index=False
    )

    # ========================================================
    # RESUMEN FINAL
    # ========================================================

    print("\n")
    print("=" * 100)
    print(
        "RESUMEN FINAL: WARM START VS COLD START"
    )
    print("=" * 100)

    print(
        f"{'Escenario':15} | "
        f"{'Modelo':25} | "
        f"{'P@5':>8} | "
        f"{'R@5':>8} | "
        f"{'NDCG@5':>9} | "
        f"{'Coverage':>10}"
    )

    print("-" * 100)

    for _, row in all_results.iterrows():

        print(
            f"{row['escenario']:15} | "
            f"{row['modelo']:25} | "
            f"{row['precision_5']:8.4f} | "
            f"{row['recall_5']:8.4f} | "
            f"{row['ndcg_5']:9.4f} | "
            f"{row['coverage']:9.2f}%"
        )

    print("=" * 100)

    # ========================================================
    # GANADORES
    # ========================================================

    best_warm = warm_results.iloc[0]
    best_cold = cold_results.iloc[0]

    print("\n")
    print("=" * 80)
    print("GANADORES POR ESCENARIO")
    print("=" * 80)

    print(
        "\nWARM START"
    )

    print(
        f"  Modelo: "
        f"{best_warm['modelo']}"
    )

    print(
        f"  P@5: "
        f"{best_warm['precision_5']:.4f}"
    )

    print(
        f"  R@5: "
        f"{best_warm['recall_5']:.4f}"
    )

    print(
        f"  NDCG@5: "
        f"{best_warm['ndcg_5']:.4f}"
    )

    print(
        f"  Coverage: "
        f"{best_warm['coverage']:.2f}%"
    )

    print(
        "\nCOLD START"
    )

    print(
        f"  Modelo: "
        f"{best_cold['modelo']}"
    )

    print(
        f"  P@5: "
        f"{best_cold['precision_5']:.4f}"
    )

    print(
        f"  R@5: "
        f"{best_cold['recall_5']:.4f}"
    )

    print(
        f"  NDCG@5: "
        f"{best_cold['ndcg_5']:.4f}"
    )

    print(
        f"  Coverage: "
        f"{best_cold['coverage']:.2f}%"
    )

    print(
        "\n"
        "[OK] Evaluación finalizada correctamente."
    )

    print(
        f"\nArchivos generados:"
        f"\n  - {OUTPUT_WARM}"
        f"\n  - {OUTPUT_COLD}"
        f"\n  - {OUTPUT_ALL}"
    )


# ============================================================
# EJECUCIÓN
# ============================================================

if __name__ == "__main__":

    main()
