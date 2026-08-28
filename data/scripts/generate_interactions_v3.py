"""
generate_interactions_v3.py

Genera interacciones sintéticas usuario-contenido desde CERO (sin leer ningún
dataset de interacciones previo), a partir de:

  - data/users_synthetic.csv          (perfiles reales de españoles 18-34, ECF 2021)
  - data/contents.csv                 (catálogo de contenidos educativos)
  - data/concepts.csv                 (conceptos de conocimiento)
  - data/content_concept_map.csv      (contenido -> concepto directo)
  - data/prerequisites.csv            (grafo de prerrequisitos entre conceptos)

Diseño metodológico (calidad de la data para entrenar modelos de deep learning):

1. POBLACIÓN REALISTA. Cada usuario hereda su perfil ECF (conocimiento financiero,
   hábito de ahorro, experiencia inversora, learning_goal, edad, sexo). De ese perfil
   se deriva un vector de interés por topic y una dificultad preferida.

2. LONG-TAIL DE ENGAGEMENT. El número de interacciones por usuario sigue una
   distribución long-tail (pocos muy activos, muchos ligeros), con media ~25.
   La intensidad correlaciona con el perfil: más conocimiento + ahorro + interés
   inversor => usuario más activo. Esto replica la realidad y da señal a los
   modelos colaborativos.

3. POPULARIDAD LONG-TAIL DE CONTENIDO. Cada contenido tiene un atractivo base
   (topic popular, formato accesible, dificultad). La probabilidad de interacción
   es proporcional a ese atractivo, generando el sesgo de popularidad real.

4. MATCHING USUARIO-CONTENIDO. prob_interact = atractivo_base * topic_match *
   difficulty_match * formato_pref. Un usuario interactúa más con lo que le
   interesa y le queda a su nivel.

5. SECUENCIACIÓN PEDAGÓGICA (lo diferencial). La restricción de prerrequisitos se
   aplica al EVENTO DE DOMINIO (completed / quiz_passed), NO al view. Un usuario
   puede VER cualquier contenido (exploración, score < 0.5), pero solo COMPLETA o
   APRUEBA un contenido si ya domina los prerrequisitos de sus conceptos. Esto
   genera caminos de aprendizaje realistas y un PVR (Prerequisite Violation Rate)
   medible y coherente.

6. PATRONES TEMPORALES. Las interacciones se agrupan en sesiones con timestamps
   crecientes (minutos dentro de una sesión, días entre sesiones), con decaimiento
   de engagement. Distingue acciones pasivas (view) de activas (completed/quiz).

7. ESQUEMA DE SALIDA (implicit feedback enriquecido):
   user_id, content_id, timestamp, event, score, time_spent_seconds,
   session_id, is_recommended

   - event: view | started | completed | quiz_passed | quiz_failed
   - score: 0-1. Los eventos de dominio (completed/quiz_passed) tienen score >= 0.5
     (relevantes); los pasivos (view/started) score < 0.5.
   - is_recommended: 1 si la interacción vino de una recomendación del sistema
     (sesgo de posición/popularidad), 0 si fue exploración autónoma.

Uso:
    python3 data/scripts/generate_interactions_v3.py
"""

from pathlib import Path
import random
from datetime import datetime, timedelta

import pandas as pd
import numpy as np

# ---------------------------------------------------------------------------
# Configuración y rutas
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent  # data/scripts -> data -> raíz
DATA_DIR = PROJECT_ROOT / "data"

USERS_FILE = DATA_DIR / "users_synthetic.csv"
CONTENTS_FILE = DATA_DIR / "contents.csv"
CONCEPTS_FILE = DATA_DIR / "concepts.csv"
MAP_FILE = DATA_DIR / "content_concept_map.csv"
PREREQS_FILE = DATA_DIR / "prerequisites.csv"
OUTPUT_FILE = DATA_DIR / "interactions_synthetic_v3.csv"

# Reproducibilidad
RNG = random.Random(42)
NPRNG = np.random.default_rng(42)

# ---------------------------------------------------------------------------
# Carga de datos
# ---------------------------------------------------------------------------
users = pd.read_csv(USERS_FILE)
contents = pd.read_csv(CONTENTS_FILE)
concepts = pd.read_csv(CONCEPTS_FILE)
map_df = pd.read_csv(MAP_FILE)
prereqs_df = pd.read_csv(PREREQS_FILE)

# Mapeos
content_concepts = {}   # content_id -> [concept_id] (solo cobertura directa)
for _, row in map_df.iterrows():
    if row["coverage_type"] == "directa":
        content_concepts.setdefault(row["content_id"], []).append(row["concept_id"])

concept_prereqs = {}    # concept_id -> [prerequisite_concept_id]
for _, row in prereqs_df.iterrows():
    concept_prereqs.setdefault(row["concept_id"], []).append(row["prerequisite_concept_id"])

# ---------------------------------------------------------------------------
# 1. Perfil de interés por topic derivado del learning_goal y del perfil ECF
# ---------------------------------------------------------------------------
# Cada learning_goal activa un conjunto de topics con pesos.
GOAL_TOPICS = {
    "prepararse para invertir": {
        "inversión": 1.0, "mercado": 0.9, "riesgo": 0.8, "diversificación": 0.8,
        "interés": 0.7, "ahorro": 0.5, "planificación": 0.4, "inflación": 0.4,
    },
    "ahorrar": {
        "ahorro": 1.0, "planificación": 0.8, "cuentas bancarias": 0.7,
        "presupuesto": 0.6, "interés": 0.5, "inflación": 0.4,
    },
    "presupuestar": {
        "planificación": 1.0, "presupuesto": 0.9, "deuda": 0.6,
        "cuentas bancarias": 0.6, "ahorro": 0.5, "tarjetas": 0.4,
    },
    "planificar finanzas": {
        "planificación": 1.0, "ahorro": 0.8, "cuentas bancarias": 0.6,
        "presupuesto": 0.6, "jubilación": 0.4, "interés": 0.4,
    },
    "entender deuda": {
        "deuda": 1.0, "préstamos": 0.9, "hipotecas": 0.8, "tarjetas": 0.7,
        "interés": 0.6, "planificación": 0.4,
    },
}

# Dificultad preferida según nivel de conocimiento financiero.
# NaN (NS/NC en Big3) -> perfil conservador: básico/intermedio.
KNOWLEDGE_DIFFICULTY = {
    "bajo": {"básico": 1.0, "intermedio": 0.4, "avanzado": 0.1},
    "medio": {"básico": 0.8, "intermedio": 1.0, "avanzado": 0.4},
    "alto": {"básico": 0.5, "intermedio": 0.9, "avanzado": 1.0},
    np.nan: {"básico": 1.0, "intermedio": 0.7, "avanzado": 0.2},
}

# Preferencia de formato (artículo web y PDF son los más accesibles).
FORMAT_PREF = {
    "artículo web": 1.0, "artículo blog": 0.9, "glosario web": 0.8,
    "PDF": 0.7, "curso web": 0.6, "vídeo educativo": 0.6,
    "simulador": 0.5, "calculadora": 0.5, "herramienta": 0.4,
    "nota de prensa": 0.3,
}

# Atractivo base por topic (popularidad del tema en la población joven).
TOPIC_POPULARITY = {
    "inversión": 1.0, "planificación": 0.9, "ahorro": 0.85, "cuentas bancarias": 0.8,
    "presupuesto": 0.8, "interés": 0.7, "inflación": 0.7, "mercado": 0.7,
    "riesgo": 0.6, "diversificación": 0.6, "deuda": 0.6, "préstamos": 0.6,
    "hipotecas": 0.6, "tarjetas": 0.5, "fraude": 0.5, "contexto": 0.4,
}

# ---------------------------------------------------------------------------
# 2. Intensidad de engagement por usuario (long-tail, correlacionada con perfil)
# ---------------------------------------------------------------------------
def engagement_intensity(row):
    """Devuelve un factor de actividad en [0.5, 2.0] derivado del perfil ECF."""
    f = 1.0
    kn = row.get("financial_knowledge_level")
    if kn == "alto":
        f *= 1.3
    elif kn == "medio":
        f *= 1.1
    elif kn == "bajo":
        f *= 0.8
    if row.get("saving_habit") == "frecuente":
        f *= 1.15
    if row.get("investment_experience") == "básica":
        f *= 1.2
    if row.get("learning_goal") == "prepararse para invertir":
        f *= 1.15
    if row.get("age_group") == "18-24":
        f *= 1.1  # grupo más activo en formación online (TIC-H INE)
    return float(np.clip(f, 0.5, 2.0))


def sample_n_interactions(intensity):
    """Número de interacciones por usuario: long-tail con media ~25.

    Base log-normal centrada en ~22, escalada por la intensidad del perfil.
    """
    base = float(NPRNG.lognormal(mean=np.log(22), sigma=0.55))
    n = int(round(base * intensity))
    return int(np.clip(n, 4, 70))


# ---------------------------------------------------------------------------
# 3. Atractivo base de cada contenido (popularidad long-tail)
# ---------------------------------------------------------------------------
def content_attractiveness(row):
    topic = row["topic"]
    fmt = row["format"]
    diff = row["difficulty"]
    base = TOPIC_POPULARITY.get(topic, 0.5)
    fmt_w = FORMAT_PREF.get(fmt, 0.5)
    # Los contenidos básicos son más consumidos; los avanzados menos.
    diff_w = {"básico": 1.0, "intermedio": 0.75, "avanzado": 0.5}.get(diff, 0.7)
    # Ruido multiplicativo para romper la simetría y crear long-tail.
    noise = float(NPRNG.lognormal(mean=0.0, sigma=0.4))
    return base * fmt_w * diff_w * noise


contents = contents.copy()
contents["_attract"] = contents.apply(content_attractiveness, axis=1)
# Normalizar atractivo a [0,1] para usarlo como probabilidad base.
attract_min, attract_max = contents["_attract"].min(), contents["_attract"].max()
contents["_attract_norm"] = (contents["_attract"] - attract_min) / (attract_max - attract_min + 1e-9)

# Índices auxiliares
content_by_id = contents.set_index("content_id")
topic_of_content = contents.set_index("content_id")["topic"].to_dict()
diff_of_content = contents.set_index("content_id")["difficulty"].to_dict()
fmt_of_content = contents.set_index("content_id")["format"].to_dict()
attract_of_content = contents.set_index("content_id")["_attract_norm"].to_dict()

# ---------------------------------------------------------------------------
# 4. Generación de interacciones por usuario
# ---------------------------------------------------------------------------
def user_topic_weights(row):
    """Vector de interés por topic del usuario."""
    goal = row.get("learning_goal")
    weights = dict(GOAL_TOPICS.get(goal, GOAL_TOPICS["planificar finanzas"]))
    # La experiencia inversora refuerza el interés por inversión/mercado.
    if row.get("investment_experience") == "básica":
        for t in ("inversión", "mercado", "riesgo", "diversificación"):
            weights[t] = weights.get(t, 0.0) + 0.3
    return weights


def content_match_prob(cid, topic_weights, difficulty_weights):
    """Probabilidad de interacción usuario-contenido (matching)."""
    topic = topic_of_content[cid]
    diff = diff_of_content[cid]
    topic_w = topic_weights.get(topic, 0.2)
    diff_w = difficulty_weights.get(diff, 0.5)
    attract = attract_of_content[cid]
    # Suelo mínimo de cobertura: los topics poco populares (hipotecas, mercado,
    # diversificación, fraude...) reciben un piso de probabilidad para que ningún
    # contenido quede desierto. Sin esto, el topic "planificación" (común a casi
    # todos los learning_goals) acapararía la mayoría de interacciones y los
    # contenidos de cola no tendrían señal para los modelos de recomendación.
    floor = 0.10
    return max(attract * topic_w * diff_w, floor)


def concepts_mastered_for(cid, mastered):
    """¿El usuario domina los prerrequisitos de todos los conceptos del contenido?"""
    for concept in content_concepts.get(cid, []):
        for prereq in concept_prereqs.get(concept, []):
            if prereq not in mastered:
                return False
    return True


def pick_event(qualified, rng):
    """Elige el evento de la interacción.

    - Si el contenido NO es accesible (faltan prerrequisitos): solo exploración
      pasiva (view/started), score < 0.5. El usuario puede verlo pero no dominarlo.
    - Si SÍ es accesible: con cierta probabilidad lo completa/aprueba (dominio),
      score >= 0.5; si no, solo lo explora.
    """
    if not qualified:
        return rng.choices(["view", "started"], weights=[0.7, 0.3])[0], False
    r = rng.random()
    if r < 0.35:
        return "view", False
    elif r < 0.55:
        return "started", False
    elif r < 0.80:
        return "completed", True
    elif r < 0.95:
        return "quiz_passed", True
    else:
        return "quiz_failed", False


def score_for_event(event):
    """Score 0-1 coherente con el evento (>=0.5 = relevante)."""
    if event == "view":
        return round(NPRNG.uniform(0.1, 0.4), 3)
    if event == "started":
        return round(NPRNG.uniform(0.3, 0.5), 3)
    if event == "completed":
        return round(NPRNG.uniform(0.6, 0.9), 3)
    if event == "quiz_passed":
        return round(NPRNG.uniform(0.7, 1.0), 3)
    if event == "quiz_failed":
        return round(NPRNG.uniform(0.4, 0.6), 3)
    return 0.5


def time_spent_for(event, fmt):
    """Segundos dedicados según el tipo de evento y formato."""
    base = {"artículo web": 180, "artículo blog": 200, "glosario web": 120,
            "PDF": 300, "curso web": 600, "vídeo educativo": 420,
            "simulador": 240, "calculadora": 150, "herramienta": 200,
            "nota de prensa": 90}.get(fmt, 180)
    mult = {"view": 0.4, "started": 0.7, "completed": 1.0,
            "quiz_passed": 1.2, "quiz_failed": 0.8}.get(event, 0.8)
    return int(round(base * mult * NPRNG.uniform(0.7, 1.3)))


def initial_mastered(row, uid, rng):
    """Conocimiento inicial del usuario según su perfil ECF.

    Los conceptos raíz (sin prerrequisitos) se consideran ya dominados si el
    usuario tiene conocimiento financiero alto; parcialmente si es medio.
    Esta función se usa TANTO en la generación como en la validación para que
    el PVR sea fiel a la construcción.

    El muestreo de raíces para el nivel "medio" usa una semilla derivada del
    user_id (no el RNG global), de modo que generación y validación obtienen
    SIEMPRE el mismo resultado sin depender del estado secuencial del RNG.
    """
    mastered = set()
    kn = row.get("financial_knowledge_level")
    if kn == "alto":
        for concept in concepts["concept_id"]:
            if concept not in concept_prereqs:
                mastered.add(concept)
    elif kn == "medio":
        local_rng = random.Random(str(uid))
        roots = [c for c in concepts["concept_id"] if c not in concept_prereqs]
        for c in local_rng.sample(roots, min(2, len(roots))):
            mastered.add(c)
    return mastered


def generate_user_interactions(row, all_cids, rng):
    """Genera la secuencia de interacciones de un usuario."""
    uid = row["user_id"]
    intensity = engagement_intensity(row)
    n_target = sample_n_interactions(intensity)

    topic_weights = user_topic_weights(row)
    kn = row.get("financial_knowledge_level")
    difficulty_weights = dict(KNOWLEDGE_DIFFICULTY.get(kn, KNOWLEDGE_DIFFICULTY[np.nan]))

    # Conocimiento inicial según el perfil (compartido con la validación).
    mastered = initial_mastered(row, uid, rng)

    # Probabilidades de matching para todos los contenidos.
    probs = {cid: content_match_prob(cid, topic_weights, difficulty_weights) for cid in all_cids}

    interactions = []
    seen_contents = set()  # contenidos ya interactuados por este usuario
    # Sesiones: 1-8 por usuario. Cada sesión agrupa interacciones consecutivas.
    n_sessions = rng.randint(1, 8)
    session_start = datetime(2024, 1, 1) + timedelta(days=rng.randint(0, 700))
    session_id_counter = 0

    for _ in range(n_target):
        # --- Selección del contenido ---
        # Con probabilidad alta elegimos el contenido de mayor matching entre los
        # accesibles; con probabilidad baja exploramos (ruido) para no saturar.
        accessible = [cid for cid in all_cids if concepts_mastered_for(cid, mastered)]
        if accessible and rng.random() < 0.85:
            pool = accessible
        else:
            pool = all_cids  # exploración: puede ver contenido no accesible

        # Ponderar por matching (con un poco de ruido para no ser determinista).
        # Penalización por revisita: volver a un contenido ya interactuado es
        # realista (relectura, repaso) pero no debe dominar, o la diversidad
        # efectiva cae y los pares duplicados inflan el dataset sin aportar
        # señal nueva a los modelos de recomendación.
        weights = np.array([probs[cid] * rng.uniform(0.6, 1.4) for cid in pool])
        revisit_penalty = np.array([0.25 if cid in seen_contents else 1.0 for cid in pool])
        weights = weights * revisit_penalty
        weights = np.maximum(weights, 1e-6)
        weights = weights / weights.sum()
        cid = pool[int(rng.choices(range(len(pool)), weights=weights, k=1)[0])]
        seen_contents.add(cid)

        # --- Evento y dominio ---
        qualified = concepts_mastered_for(cid, mastered)
        event, mastered_now = pick_event(qualified, rng)
        if mastered_now:
            for concept in content_concepts.get(cid, []):
                mastered.add(concept)

        # --- Timestamp dentro de la sesión ---
        # Cada sesión tiene 1-6 interacciones; al agotarse, abrimos otra sesión.
        if session_id_counter == 0 or rng.random() < 0.25:
            session_id_counter += 1
            session_start = session_start + timedelta(days=rng.randint(1, 14))
            ts = session_start
        else:
            ts = ts + timedelta(minutes=rng.randint(2, 45))

        # --- Recomendación vs exploración ---
        # Los contenidos populares y accesibles tienen más probabilidad de haber
        # llegado por recomendación del sistema (sesgo de popularidad/posición).
        is_rec = 1 if rng.random() < (0.3 + 0.4 * attract_of_content[cid]) else 0

        interactions.append({
            "user_id": uid,
            "content_id": cid,
            "timestamp": ts.strftime("%Y-%m-%d %H:%M:%S"),
            "event": event,
            "score": score_for_event(event),
            "time_spent_seconds": time_spent_for(event, fmt_of_content[cid]),
            "session_id": f"{uid}-S{session_id_counter:02d}",
            "is_recommended": is_rec,
        })

    return interactions


# ---------------------------------------------------------------------------
# 5. Ejecución
# ---------------------------------------------------------------------------
all_cids = contents["content_id"].tolist()
all_rows = []

for _, row in users.iterrows():
    all_rows.extend(generate_user_interactions(row, all_cids, RNG))

interactions = pd.DataFrame(all_rows, columns=[
    "user_id", "content_id", "timestamp", "event", "score",
    "time_spent_seconds", "session_id", "is_recommended",
])

# Ordenar por usuario y timestamp para legibilidad.
interactions = interactions.sort_values(["user_id", "timestamp"]).reset_index(drop=True)
interactions.to_csv(OUTPUT_FILE, index=False)

# ---------------------------------------------------------------------------
# 6. Validación de calidad
# ---------------------------------------------------------------------------
print("=" * 70)
print("VALIDACIÓN DE CALIDAD — INTERACCIONES SINTÉTICAS v3")
print("=" * 70)

n_inter = len(interactions)
n_users = interactions["user_id"].nunique()
n_contents = interactions["content_id"].nunique()
sparsity = 1.0 - n_inter / (n_users * n_contents)
per_user = interactions.groupby("user_id").size()
per_content = interactions.groupby("content_id").size()
positives = interactions[interactions["score"] >= 0.5]

print(f"\nVolumen:")
print(f"  Interacciones totales: {n_inter}")
print(f"  Usuarios: {n_users} | Contenidos con interacción: {n_contents}/{len(contents)}")
print(f"  Media/mediana interacciones por usuario: {per_user.mean():.1f} / {per_user.median():.0f}")
print(f"  Rango por usuario: {per_user.min()}-{per_user.max()}")
print(f"  Sparsity user×content: {sparsity*100:.1f}%")
print(f"  Positivos (score>=0.5): {len(positives)} ({len(positives)/n_inter*100:.1f}%)")

print(f"\nDistribución de eventos:")
print(interactions["event"].value_counts(normalize=True).round(3).to_dict())

print(f"\nLong-tail de popularidad de contenido (top 5):")
print(per_content.sort_values(ascending=False).head(5).to_dict())
print(f"  Contenidos con <10 interacciones: {(per_content < 10).sum()}")

# --- Validación de prerrequisitos (PVR) ---
# Un usuario solo puede DOMINAR (completed/quiz_passed) un contenido si domina
# los prerrequisitos de sus conceptos. La validación replica el conocimiento
# inicial del perfil (mismo initial_mastered que la generación) para que el
# PVR sea fiel: debe ser 0.0% por construcción.
print(f"\nValidación de prerrequisitos (PVR):")
mastered_by_user = {}
violations = 0
dominated = 0
users_indexed = users.set_index("user_id")
for _, r in interactions.iterrows():
    uid = r["user_id"]
    if uid not in mastered_by_user:
        mastered_by_user[uid] = initial_mastered(users_indexed.loc[uid], uid, RNG)
    mastered = mastered_by_user[uid]
    if r["event"] in ("completed", "quiz_passed"):
        dominated += 1
        for concept in content_concepts.get(r["content_id"], []):
            for prereq in concept_prereqs.get(concept, []):
                if prereq not in mastered:
                    violations += 1
    # Actualizar dominio tras la interacción (solo si fue de dominio)
    if r["event"] in ("completed", "quiz_passed"):
        for concept in content_concepts.get(r["content_id"], []):
            mastered.add(concept)
pvr = violations / dominated * 100 if dominated else 0.0
print(f"  Eventos de dominio: {dominated} | Violaciones de prerrequisito: {violations}")
print(f"  PVR: {pvr:.2f}%  (debe ser 0.0% por construcción)")

# --- Correlación conocimiento -> dificultad ---
print(f"\nCorrelación conocimiento -> dificultad (media de dificultad dominada):")
kn_diff = interactions.merge(users[["user_id", "financial_knowledge_level"]], on="user_id", how="left")
kn_diff = kn_diff[kn_diff["event"].isin(["completed", "quiz_passed"])]
kn_diff["_diff_num"] = kn_diff["content_id"].map(
    {"básico": 1, "intermedio": 2, "avanzado": 3}.__getitem__ if False else
    lambda c: {"básico": 1, "intermedio": 2, "avanzado": 3}[diff_of_content[c]]
)
print(kn_diff.groupby("financial_knowledge_level")["_diff_num"].mean().round(2).to_dict())

# --- Cobertura de topics ---
print(f"\nCobertura por topic (n interacciones):")
topic_counts = interactions["content_id"].map(topic_of_content).value_counts()
print(topic_counts.to_dict())

print(f"\n✓ Archivo generado en: {OUTPUT_FILE}")
print("=" * 70)
