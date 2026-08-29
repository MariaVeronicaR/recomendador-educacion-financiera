"""
Generador de interacciones sintéticas usuario–contenido (educación financiera).

Implementa el plan técnico `docs/plan_generar_interacciones.md`:

  FASE 0  Preparación: carga de catálogos (contents, concepts, content_concept_map,
          prerequisites) y construcción de estructuras.
  FASE 1  Perfiles de usuario latentes calibrados con los microdatos de la ECF 2021
          (conocimiento, intereses temáticos, tolerancia al riesgo, actividad, ruido).
  FASE 2  Línea temporal global y calendarios de actividad por usuario.
  FASE 3  Simulación temporal causal de interacciones:
            - preferencia usuario–contenido (factores latentes + atributos + exposición)
            - competencia/dificultad (IRT) que modula el completado y el abandono
            - progresión del aprendizaje (BKT) sobre el grafo de prerrequisitos
            - ruido (misclick, curiosidad, popularidad) y no-determinismo
  FASE 4  Validación: batería de tests estadísticos y de coherencia.
  FASE 5  Salida: interactions_synthetic.csv + reporte de validación + metadatos.

Restricción: se construye desde cero. No se lee ningún dataset de interacciones previo.

Uso:
    python3 data/scripts/generate_interactions.py [--users N] [--seed S] [--out DIR]
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent          # data/scripts -> data -> raíz
DATA_DIR = PROJECT_ROOT / "data"
DOCS_DIR = PROJECT_ROOT / "docs"
ECF_PATH = PROJECT_ROOT / "ECF-archivos" / "ecf_2021.csv"

MISSING_CODES = {-97, -98, -99, -96, -5, -4, -3}

# Parámetros del generador (calibrados para producir patrones realistas)
PARAMS = {
    "n_users": 2000,
    "window_days": 365,          # ventana temporal global (12 meses)
    # Actividad: interacciones por semana, log-normal (cola larga)
    # Media ~0.15/semana -> ~8 interacciones/año -> densidad ~4-5%
    "activity_mu": math.log(0.15),
    "activity_sigma": 0.6,
    # Sesiones
    "session_size_alpha": 1.6,   # forma de la distribución del tamaño de sesión
    "session_size_scale": 2.2,   # escala (media ~ alpha*scale)
    # Preferencia (coeficientes del logit)
    "w_topic": 1.6,              # peso de la afinidad temática
    "w_format": 0.7,             # peso de la afinidad de formato
    "w_risk": 1.1,               # peso de la tolerancia al riesgo
    "w_invest": 0.8,             # peso del interés inversor
    "w_popularity": 0.9,         # peso de la popularidad del contenido
    "w_prereq": 1.8,             # penalización por prerrequisitos no dominados
    "w_competence": 2.0,         # peso de la competencia (dificultad vs conocimiento)
    "logit_base": -2.4,          # intercepto (controla la densidad global)
    # IRT
    "irt_discrimination": 1.4,   # a (discriminación)
    "irt_guess": 0.10,           # c (probabilidad de adivinar)
    # BKT
    "bkt_learn_base": 0.55,      # p(T) base por interacción completada
    "bkt_slip": 0.10,            # p(S)
    "bkt_guess": 0.15,           # p(G)
    "bkt_prereq_decay": 0.5,     # reducción de p(T) por prerrequisito no dominado
    # Exposición
    "exposure_candidates": 4,    # nº de contenidos expuestos por sesión
    "exposure_popular_share": 0.35,  # fracción de candidatos por popularidad
    "w_readiness": 1.2,          # peso de la preparación (maestría de prerrequisitos) en la selección
    # Ruido
    "noise_misclick": 0.06,      # prob. base de misclick
    "noise_curiosity": 0.05,     # prob. base de curiosidad
    "noise_popularity": 0.08,    # prob. base de interacción por popularidad pura
    # Popularidad de contenidos (cola larga)
    "popularity_alpha": 1.8,     # exponente power-law
    "popularity_min": 1.0,
    # Duración (log-normal)
    "duration_mu": math.log(180.0),
    "duration_sigma": 0.7,
    # Conocimiento inicial (bajo para dejar margen de progresión)
    "theta_big3_scale": 2.0,     # escala del Big3 (0-1) a θ (centrado en 0.5)
    "theta_product_bonus": 0.10, # bonus por producto financiero contratado
    "theta_noise": 0.4,          # ruido en θ
    # Intereses temáticos
    "interest_noise": 0.5,       # ruido en el vector de intereses
    "interest_extra": 0.4,       # interés residual en temas no derivados
    # Riesgo
    "risk_theta_corr": 0.4,      # correlación tolerancia al riesgo <-> conocimiento
    "risk_noise": 0.5,
    # Formato
    "format_noise": 0.4,
    # Timestamps
    "hour_weights": {9: 1.0, 10: 1.2, 11: 1.3, 12: 1.2, 13: 1.0, 14: 0.8,
                     15: 0.9, 16: 1.1, 17: 1.2, 18: 1.3, 19: 1.2, 20: 1.0,
                     21: 0.9, 22: 0.7, 23: 0.5, 0: 0.3, 1: 0.2, 2: 0.1,
                     3: 0.1, 4: 0.1, 5: 0.2, 6: 0.4, 7: 0.6, 8: 0.8},
    "weekend_factor": 0.8,       # menos actividad en fin de semana
}

# ---------------------------------------------------------------------------
# FASE 0 — Preparación
# ---------------------------------------------------------------------------
def load_catalogs():
    contents = pd.read_csv(DATA_DIR / "contents.csv")
    concepts = pd.read_csv(DATA_DIR / "concepts.csv")
    ccm = pd.read_csv(DATA_DIR / "content_concept_map.csv")
    prereqs = pd.read_csv(DATA_DIR / "prerequisites.csv")

    # Dificultad ordinal -> escala continua en [0,1], compatible con la maestría
    # (P(domina) en [0,1]) para que el término de competencia IRT sea comparable.
    diff_map = {"básico": 0.0, "intermedio": 0.5, "avanzado": 1.0}
    risk_map = {"bajo": 0.0, "medio": 1.0, "alto": 2.0}

    contents["diff_num"] = contents["difficulty"].map(diff_map)
    contents["risk_num"] = contents["risk_level"].map(risk_map)
    concepts["diff_num"] = concepts["difficulty"].map(diff_map)

    # conceptos por contenido
    concepts_of_content = ccm.groupby("content_id")["concept_id"].apply(list).to_dict()

    # prerrequisitos por concepto
    prereq_of_concept = prereqs.groupby("concept_id")["prerequisite_concept_id"].apply(list).to_dict()

    # dificultad de concepto
    concept_diff = concepts.set_index("concept_id")["diff_num"].to_dict()

    # topic de contenido y de concepto
    content_topic = contents.set_index("content_id")["topic"].to_dict()
    concept_topic = concepts.set_index("concept_id")["topic"].to_dict()

    # format de contenido
    content_format = contents.set_index("content_id")["format"].to_dict()

    # popularidad base de contenido (cola larga) — se genera con seed fijo
    return {
        "contents": contents,
        "concepts": concepts,
        "ccm": ccm,
        "prereqs": prereqs,
        "concepts_of_content": concepts_of_content,
        "prereq_of_concept": prereq_of_concept,
        "concept_diff": concept_diff,
        "content_topic": content_topic,
        "concept_topic": concept_topic,
        "content_format": content_format,
        "diff_map": diff_map,
        "risk_map": risk_map,
    }


# ---------------------------------------------------------------------------
# FASE 1 — Perfiles de usuario calibrados con la ECF
# ---------------------------------------------------------------------------
def load_ecf_distributions():
    """Extrae distribuciones empíricas de la ECF 2021 para jóvenes 18-34."""
    df = pd.read_csv(ECF_PATH, sep=";", low_memory=False)
    df["edad"] = 2021 - df["a0400"]
    j = df[(df["edad"] >= 18) & (df["edad"] <= 34)].copy()

    # --- educación (e0100) ---
    educ_map = {1: "posgrado", 2: "universidad", 3: "bachillerato",
                4: "secundaria", 5: "primaria"}
    j["educ"] = j["e0100"].map(educ_map)
    educ_valid = j["educ"].dropna()
    educ_dist = educ_valid.value_counts(normalize=True).to_dict()

    # --- empleo (a1500) ---
    def work(v):
        if v in MISSING_CODES or pd.isna(v):
            return None
        v = int(v)
        if v == 9:
            return "estudiante"
        if v == 5:
            return "desempleado"
        if v in (1, 2, 3, 4):
            return "empleado"
        if v == 8:
            return "desempleado"
        return "empleado"
    j["work"] = j["a1500"].apply(work)
    work_valid = j["work"].dropna()
    work_dist = work_valid.value_counts(normalize=True).to_dict()

    # --- conocimiento Big3 (k0600 inflación, k0100 interés compuesto, k1003 diversif) ---
    def big3_score(row):
        aciertos, posibles = 0, 0
        for col, correcta in (("k0600", 3), ("k0100", 3), ("k1003", 1)):
            val = row[col]
            if pd.isna(val) or val in MISSING_CODES:
                continue
            posibles += 1
            if val == correcta:
                aciertos += 1
        if posibles == 0:
            return np.nan
        return aciertos / posibles
    j["big3"] = j.apply(big3_score, axis=1)

    # --- tenencia de productos (b1000a-j) ---
    prod_cols = ["b1000a", "b1000b", "b1000c", "b1000d", "b1000e",
                 "b1000f", "b1000g", "b1000h", "b1000i"]
    prod_names = ["cuenta_corriente", "cuenta_ahorro", "acciones", "bonos",
                  "fondos", "cripto", "seguro", "pensiones", "otro"]
    prod_rates = {}
    for col, name in zip(prod_cols, prod_names):
        s = j[col]
        prod_rates[name] = float((s == 1).mean()) if (s == 1).any() else 0.0

    # --- correlación educación <-> conocimiento (para imputar θ) ---
    educ_big3 = j.groupby("educ")["big3"].mean().to_dict()

    return {
        "educ_dist": educ_dist,
        "work_dist": work_dist,
        "prod_rates": prod_rates,
        "educ_big3": educ_big3,
    }


def sample_user_profiles(n, ecf, rng):
    """Genera n perfiles de usuario latentes calibrados con la ECF."""
    educ_levels = list(ecf["educ_dist"].keys())
    educ_probs = [ecf["educ_dist"][k] for k in educ_levels]
    work_levels = list(ecf["work_dist"].keys())
    work_probs = [ecf["work_dist"][k] for k in work_levels]

    profiles = []
    for i in range(n):
        # Sexo rebalanceado a ~50/50 (corrige el sesgo muestral de la ECF)
        sex = rng.choice(["hombre", "mujer"], p=[0.5, 0.5])
        # Edad
        age = rng.integers(18, 35)
        age_group = "18-24" if age <= 24 else "25-34"

        # Educación y empleo (distribuciones ECF)
        education = rng.choice(educ_levels, p=educ_probs)
        employment = rng.choice(work_levels, p=work_probs)

        # Tenencia de productos (tasas ECF)
        products = [p for p, r in ecf["prod_rates"].items() if rng.random() < r]

        # Conocimiento continuo θ: imputado desde Big3 (condicionado a educación)
        # + bonus por productos + ruido. El Big3 se muestrea de la distribución
        # empírica por nivel educativo (plan §2.2: imputar NS/NC, no contar como fallo).
        big3_mean = ecf["educ_big3"].get(education, 0.65)
        big3 = float(np.clip(rng.normal(big3_mean, 0.3), 0.0, 1.0))
        theta = PARAMS["theta_big3_scale"] * (big3 - 0.5)
        theta += PARAMS["theta_product_bonus"] * len(products)
        theta += rng.normal(0, PARAMS["theta_noise"])
        # Conocimiento categórico (para validación)
        if theta > 0.8:
            knowledge_level = "alto"
        elif theta > 0.0:
            knowledge_level = "medio"
        else:
            knowledge_level = "bajo"

        # Intereses temáticos: derivados de productos + empleo + ruido
        interests = {}
        for p in products:
            for topic in product_to_topics(p):
                interests[topic] = interests.get(topic, 0.0) + 1.0
        if employment == "estudiante":
            interests["planificación"] = interests.get("planificación", 0.0) + 0.8
            interests["ahorro"] = interests.get("ahorro", 0.0) + 0.6
        if employment == "empleado":
            interests["planificación"] = interests.get("planificación", 0.0) + 0.4
        # Ruido en intereses
        for topic in ALL_TOPICS:
            interests[topic] = interests.get(topic, 0.0) + rng.normal(0, PARAMS["interest_noise"])
            interests[topic] += PARAMS["interest_extra"] * rng.random()

        # Tolerancia al riesgo (correlacionada con conocimiento)
        risk = PARAMS["risk_theta_corr"] * theta + rng.normal(0, PARAMS["risk_noise"])
        risk = float(np.clip(risk, -2.0, 2.0))

        # Preferencia de formato
        format_pref = {f: rng.normal(0, PARAMS["format_noise"]) for f in ALL_FORMATS}
        # Los usuarios con interés inversor prefieren PDFs/guías; los generalistas, artículos
        if "inversión" in interests and interests["inversión"] > 1.0:
            format_pref["PDF"] += 0.6
            format_pref["curso web"] += 0.4
        if employment == "estudiante":
            format_pref["artículo web"] += 0.4
            format_pref["calculadora"] += 0.3

        # Actividad (interacciones/semana, log-normal cola larga)
        activity = float(np.exp(rng.normal(PARAMS["activity_mu"], PARAMS["activity_sigma"])))

        # Tasa de aprendizaje (heterogénea)
        learn_rate = float(np.clip(rng.beta(2.0, 3.0) * 1.4, 0.2, 0.95))

        # Nivel de ruido (propensión a misclick/curiosidad)
        noise_level = float(rng.beta(2.0, 5.0))

        profiles.append({
            "user_id": f"U{i+1:04d}",
            "age": age,
            "age_group": age_group,
            "sex": sex,
            "education_level": education,
            "employment_status": employment,
            "products": products,
            "theta": theta,
            "knowledge_level": knowledge_level,
            "interests": interests,
            "risk": risk,
            "format_pref": format_pref,
            "activity": activity,
            "learn_rate": learn_rate,
            "noise_level": noise_level,
        })
    return profiles


def product_to_topics(product):
    """Mapea un producto financiero a los temas de contenido que le interesan."""
    mapping = {
        "cuenta_corriente": ["cuentas bancarias", "planificación"],
        "cuenta_ahorro": ["ahorro", "cuentas bancarias"],
        "acciones": ["inversión", "riesgo", "mercado"],
        "bonos": ["inversión", "riesgo"],
        "fondos": ["inversión", "diversificación"],
        "cripto": ["inversión", "riesgo", "mercado"],
        "seguro": ["riesgo"],
        "pensiones": ["planificación", "ahorro"],
        "otro": ["planificación"],
    }
    return mapping.get(product, [])


# ---------------------------------------------------------------------------
# FASE 2 — Línea temporal y calendario de actividad
# ---------------------------------------------------------------------------
def build_sessions(profile, rng, window_days):
    """Genera las sesiones de un usuario a lo largo de la ventana temporal."""
    # Interacciones totales en el año
    n_interactions = int(np.random.poisson(profile["activity"] * 52.0))
    if n_interactions == 0:
        return []
    # Tamaño medio de sesión
    mean_session = PARAMS["session_size_alpha"] * PARAMS["session_size_scale"]
    n_sessions = max(1, int(round(n_interactions / mean_session)))

    sessions = []
    for _ in range(n_sessions):
        # Día (con estacionalidad semanal)
        day = rng.integers(0, window_days)
        # Hora (con pesos)
        hours = list(PARAMS["hour_weights"].keys())
        hw = [PARAMS["hour_weights"][h] for h in hours]
        hour = int(rng.choice(hours, p=np.array(hw) / np.sum(hw)))
        minute = rng.integers(0, 60)
        # Tamaño de sesión (cola larga)
        size = max(1, int(rng.gamma(PARAMS["session_size_alpha"], PARAMS["session_size_scale"])))
        sessions.append({"day": int(day), "hour": hour, "minute": int(minute), "size": size})
    return sessions


# ---------------------------------------------------------------------------
# FASE 3 — Simulación temporal causal
# ---------------------------------------------------------------------------
def simulate_user(profile, cat, rng, window_days, start_date):
    """Simula las interacciones de un usuario, actualizando su conocimiento (BKT)."""
    contents = cat["contents"]
    content_ids = list(contents["content_id"])
    n_content = len(content_ids)

    # Popularidad de contenidos (cola larga) — fija por contenido
    # (se genera una vez globalmente, ver simulate_all)
    popularity = cat["_popularity"]

    # Estado de dominio por concepto (BKT): P(domina k)
    mastery = {}
    for k, d in cat["concept_diff"].items():
        # Conocimiento inicial del concepto desde θ y dificultad del concepto
        p0 = 1.0 / (1.0 + math.exp(-(profile["theta"] - d)))
        mastery[k] = float(np.clip(p0, 0.02, 0.98))

    # Precomputar atributos de contenido
    topic_arr = contents["topic"].values
    format_arr = contents["format"].values
    risk_arr = contents["risk_num"].values
    invest_arr = contents["is_investment_related"].map({"si": 1.0, "no": 0.0}).values
    diff_arr = contents["diff_num"].values
    pop_arr = np.array([popularity[c] for c in content_ids])
    log_pop = np.log(pop_arr + 1.0)

    # Precomputar conceptos y prerrequisitos por contenido
    content_concepts = [cat["concepts_of_content"].get(c, []) for c in content_ids]
    content_prereqs = []
    for ccs in content_concepts:
        prereqs = set()
        for k in ccs:
            for p in cat["prereq_of_concept"].get(k, []):
                prereqs.add(p)
        content_prereqs.append(prereqs)

    # Precomputar afinidades del usuario
    topic_aff = np.array([profile["interests"].get(t, 0.0) for t in contents["topic"]])
    format_aff = np.array([profile["format_pref"].get(f, 0.0) for f in contents["format"]])

    sessions = build_sessions(profile, rng, window_days)
    interactions = []

    for sess_idx, sess in enumerate(sessions, start=1):
        session_id = f"{profile['user_id']}-{sess_idx}"
        # Candidatos expuestos: mezcla de temas de interés + populares + aleatorios.
        # Filtro de prerrequisitos: un contenido avanzado solo se expone si el usuario
        # domina al menos un prerrequisito de sus conceptos (salvo pequeña curiosidad),
        # igual que un sistema de recomendación no muestra contenidos para los que
        # el usuario no está preparado.
        n_cand = min(PARAMS["exposure_candidates"], n_content)
        # Popularidad-driven
        n_pop = int(n_cand * PARAMS["exposure_popular_share"])
        # Interés-driven: contenidos de los topics con mayor afinidad, ponderados
        # además por la preparación (maestría de prerrequisitos) para que el usuario
        # progrese a contenidos intermedios/avanzados a medida que aprende.
        n_interest = n_cand - n_pop
        readiness = np.array([
            sum(1 for p in content_prereqs[i] if mastery.get(p, 0.5) >= 0.5)
            / max(len(content_prereqs[i]), 1)
            for i in range(n_content)
        ])
        # Novedad: contenido cuyos conceptos ya domina se muestra menos, de modo que
        # el usuario progrese a contenido nuevo en vez de repetir lo ya aprendido.
        novelty = np.array([
            1.0 - np.mean([mastery.get(k, 0.5) for k in content_concepts[i]])
            if content_concepts[i] else 0.5
            for i in range(n_content)
        ])
        interest_probs = np.clip(topic_aff, 0, None) + 0.05
        interest_probs = interest_probs * (1.0 + PARAMS["w_readiness"] * readiness)
        interest_probs = interest_probs * (0.1 + 0.9 * novelty)
        if interest_probs.sum() == 0:
            interest_probs = np.ones(n_content) / n_content
        else:
            interest_probs = interest_probs / interest_probs.sum()
        cand_interest = rng.choice(n_content, size=min(n_interest, n_content), replace=False, p=interest_probs)
        # Seleccionar por popularidad
        pop_probs = log_pop / log_pop.sum()
        cand_pop = rng.choice(n_content, size=min(n_pop, n_content), replace=False, p=pop_probs)
        candidates = np.unique(np.concatenate([cand_interest, cand_pop]))

        # Filtrar por preparación (prerrequisitos) para contenidos avanzados
        filtered = []
        for c_idx in candidates:
            ccs = content_concepts[c_idx]
            prereqs = content_prereqs[c_idx]
            if diff_arr[c_idx] >= 1.0 and prereqs:
                # Dominar al menos un prerrequisito, o pequeña probabilidad de curiosidad
                mastered_any = any(mastery.get(p, 0.5) >= 0.5 for p in prereqs)
                if not mastered_any and rng.random() > 0.10:
                    continue
            filtered.append(c_idx)
        candidates = np.array(filtered, dtype=int) if filtered else np.array([], dtype=int)

        # Timestamp de la sesión
        ts = start_date + pd.Timedelta(days=int(sess["day"]), hours=int(sess["hour"]), minutes=int(sess["minute"]))

        for _ in range(sess["size"]):
            if len(candidates) == 0:
                break
            c_idx = int(rng.choice(candidates))
            c_id = content_ids[c_idx]

            # --- Probabilidad de interacción (logit) ---
            # Competencia: conocimiento del usuario sobre los conceptos del contenido
            ccs = content_concepts[c_idx]
            if ccs:
                theta_c = np.mean([mastery.get(k, 0.5) for k in ccs])
            else:
                theta_c = 0.5
            # Prerrequisitos no dominados
            n_unmastered = sum(1 for p in content_prereqs[c_idx] if mastery.get(p, 0.5) < 0.5)

            logit = PARAMS["logit_base"]
            logit += PARAMS["w_topic"] * topic_aff[c_idx]
            logit += PARAMS["w_format"] * format_aff[c_idx]
            logit += PARAMS["w_risk"] * (profile["risk"] - risk_arr[c_idx])
            logit += PARAMS["w_invest"] * invest_arr[c_idx] * max(profile["interests"].get("inversión", 0.0), 0.0)
            logit += PARAMS["w_popularity"] * log_pop[c_idx]
            logit -= PARAMS["w_prereq"] * n_unmastered
            # La competencia pesa más en contenidos avanzados (acceso condicionado al
            # conocimiento). Se usa la maestría del usuario sobre los conceptos del
            # contenido (theta_c), que evoluciona con BKT, para que el acceso a
            # avanzados dependa del conocimiento aprendido y no de un valor estático.
            if diff_arr[c_idx] >= 1.0:
                logit += PARAMS["w_competence"] * 1.8 * (theta_c - diff_arr[c_idx])
            else:
                logit += PARAMS["w_competence"] * (theta_c - diff_arr[c_idx])

            p_interact = 1.0 / (1.0 + math.exp(-logit))

            # Ruido: misclick / curiosidad / popularidad pura
            r = rng.random()
            interacted = False
            source = "browse"
            if r < p_interact:
                interacted = True
                source = rng.choice(["recommended", "browse", "search"], p=[0.5, 0.35, 0.15])
            elif rng.random() < profile["noise_level"] * PARAMS["noise_misclick"]:
                interacted = True
                source = "browse"  # misclick
            elif rng.random() < PARAMS["noise_curiosity"] * (1.0 - min(n_unmastered, 3) * 0.2) \
                    * (1.0 - 0.5 * diff_arr[c_idx]):
                interacted = True
                source = "search"  # curiosidad (menos probable si no domina prerrequisitos o es avanzado)
            elif rng.random() < PARAMS["noise_popularity"] * (log_pop[c_idx] / log_pop.max()) \
                    * (1.0 - min(n_unmastered, 3) * 0.25) * (1.0 - 0.5 * diff_arr[c_idx]):
                interacted = True
                source = "recommended"  # popularidad pura (menos probable sin prerrequisitos o avanzado)

            if not interacted:
                continue

            # --- Probabilidad de completar (IRT + penalización por prerrequisitos) ---
            p_complete = PARAMS["irt_guess"] + (1 - PARAMS["irt_guess"]) * (
                1.0 / (1.0 + math.exp(-PARAMS["irt_discrimination"] * (theta_c - diff_arr[c_idx])))
            )
            # Sin prerrequisitos dominados, es mucho menos probable completar
            if n_unmastered > 0:
                p_complete *= math.exp(-PARAMS["w_prereq"] * 0.5 * n_unmastered)
            completed = rng.random() < p_complete

            # --- Tipo de interacción ---
            fmt = format_arr[c_idx]
            if fmt in ("calculadora", "simulador", "herramienta"):
                itype = "tool"
            elif fmt in ("glosario web", "artículo web", "artículo blog", "nota de prensa"):
                itype = "read"
            elif fmt in ("PDF", "curso web", "vídeo educativo"):
                # Contenidos largos: si no se completan, es una "vista" superficial
                itype = "read" if completed else "view"
            else:
                itype = "view"

            # --- Duración (log-normal) ---
            duration = float(np.exp(rng.normal(PARAMS["duration_mu"], PARAMS["duration_sigma"])))
            if not completed:
                duration *= rng.uniform(0.1, 0.5)  # abandono -> más corto

            # --- Outcome (solo si hay quiz; aquí usamos completado como proxy) ---
            outcome = "na"
            if itype == "tool":
                outcome = "na"
            elif completed:
                outcome = "correct" if rng.random() < (1 - PARAMS["bkt_slip"]) else "incorrect"
            else:
                outcome = "incorrect" if rng.random() < PARAMS["bkt_guess"] else "na"

            # --- Actualizar conocimiento (BKT) si completó ---
            if completed:
                for k in ccs:
                    # p(T) reducida por prerrequisitos no dominados
                    n_unm = sum(1 for p in cat["prereq_of_concept"].get(k, []) if mastery.get(p, 0.5) < 0.5)
                    pt = profile["learn_rate"] * math.exp(-PARAMS["bkt_prereq_decay"] * n_unm)
                    # BKT update: evidencia positiva (completó)
                    p_known = mastery[k]
                    # P(domina | evidencia) con slip
                    p_obs = (1 - PARAMS["bkt_slip"]) * p_known + PARAMS["bkt_guess"] * (1 - p_known)
                    p_post = ((1 - PARAMS["bkt_slip"]) * p_known) / p_obs
                    # Aprender
                    mastery[k] = p_post + (1 - p_post) * pt

            interactions.append({
                "user_id": profile["user_id"],
                "content_id": c_id,
                "timestamp": ts,
                "session_id": session_id,
                "interaction_type": itype,
                "duration_seconds": round(duration, 1),
                "completed": completed,
                "outcome": outcome,
                "source": source,
                "position": int(rng.integers(1, 11)),
                "concepts_covered": ";".join(ccs),
            })

    return interactions


def simulate_all(profiles, cat, rng, start_date):
    """Simula todos los usuarios y devuelve el dataframe de interacciones."""
    # Popularidad de contenidos (cola larga) — fija y compartida
    contents = cat["contents"]
    content_ids = list(contents["content_id"])
    n = len(content_ids)
    # Power-law truncada
    u = rng.random(n)
    pop = PARAMS["popularity_min"] * (1.0 - u) ** (-1.0 / (PARAMS["popularity_alpha"] - 1.0))
    pop = np.clip(pop, 1.0, 1e4)
    cat["_popularity"] = dict(zip(content_ids, pop))

    all_rows = []
    for prof in profiles:
        rows = simulate_user(prof, cat, rng, PARAMS["window_days"], start_date)
        all_rows.extend(rows)

    df = pd.DataFrame(all_rows)
    if len(df) > 0:
        df = df.sort_values("timestamp").reset_index(drop=True)
        df.insert(0, "interaction_id", range(1, len(df) + 1))
    return df


# ---------------------------------------------------------------------------
# FASE 4 — Validación
# ---------------------------------------------------------------------------
def validate(df, cat, profiles, out_dir):
    """Ejecuta la batería de tests de validación y escribe un reporte."""
    report = {}
    contents = cat["contents"]
    n_users = len(profiles)
    n_content = len(contents)

    # 1. Sparsity (sobre pares únicos usuario-contenido)
    n_unique_pairs = df[["user_id", "content_id"]].drop_duplicates().shape[0]
    density = n_unique_pairs / (n_users * n_content)
    report["n_interactions"] = len(df)
    report["n_unique_pairs"] = n_unique_pairs
    report["density"] = round(density, 5)
    report["density_ok"] = 0.01 <= density <= 0.05

    # 2. Popularidad de contenidos (cola larga)
    pop_counts = df["content_id"].value_counts()
    report["popularity_gini"] = round(gini(pop_counts.values), 3)
    report["popularity_top10_share"] = round(pop_counts.head(10).sum() / len(df), 3)
    report["popularity_ok"] = report["popularity_gini"] > 0.3

    # 3. Actividad de usuarios (cola larga)
    user_counts = df["user_id"].value_counts()
    report["user_activity_gini"] = round(gini(user_counts.values), 3)
    report["user_activity_ok"] = report["user_activity_gini"] > 0.2

    # 4. Tasa de completado global y por dificultad.
    #    completion_by_difficulty es la TASA de completado (media de completed) por
    #    dificultad, no el share de completados por dificultad.
    report["completion_rate"] = round(df["completed"].mean(), 3)
    merged = df.merge(contents[["content_id", "difficulty", "topic", "risk_level",
                                "is_investment_related"]], on="content_id", how="left")
    comp_by_diff = merged.groupby("difficulty")["completed"].mean().to_dict()
    report["completion_by_difficulty"] = {k: round(v, 3) for k, v in comp_by_diff.items()}
    report["completion_decreasing_ok"] = (
        comp_by_diff.get("básico", 1) > comp_by_diff.get("intermedio", 0) >
        comp_by_diff.get("avanzado", -1)
    )

    # 5. Conocimiento <-> dificultad completada
    prof_df = pd.DataFrame([{k: p[k] for k in ("user_id", "knowledge_level", "theta")} for p in profiles])
    m2 = merged.merge(prof_df, on="user_id", how="left")
    m2["diff_num"] = m2["difficulty"].map({"básico": 0, "intermedio": 1, "avanzado": 2})
    completed_only = m2[m2["completed"]]
    if len(completed_only) > 0:
        corr = completed_only[["theta", "diff_num"]].corr().iloc[0, 1]
        report["theta_diff_corr"] = round(corr, 3)
        report["theta_diff_ok"] = corr > 0.1
    else:
        report["theta_diff_corr"] = None
        report["theta_diff_ok"] = False

    # 6. Coherencia con prerrequisitos: la tasa de acceso a contenidos AVANZADOS debe
    #    ser creciente con el nivel de conocimiento. Se mide la fracción de interacciones
    #    que son avanzadas para cada nivel de conocimiento y se exige que sea monótona
    #    (bajo < medio < alto). Esto captura "los usuarios sin base no acceden a
    #    contenidos avanzados" sin verse distorsionado por la proporción de cada nivel.
    m2["is_advanced"] = m2["difficulty"] == "avanzado"
    adv_rate_by_level = {}
    for lvl in ["bajo", "medio", "alto"]:
        sub = m2[m2["knowledge_level"] == lvl]
        adv_rate_by_level[lvl] = round(sub["is_advanced"].mean(), 3) if len(sub) else 0.0
    report["advanced_rate_by_knowledge"] = adv_rate_by_level
    report["prereq_ok"] = (
        adv_rate_by_level["bajo"] < adv_rate_by_level["medio"] < adv_rate_by_level["alto"]
    )

    # 7. No-determinismo: AUC de un modelo simple (regresión logística)
    try:
        from sklearn.linear_model import LogisticRegression
        from sklearn.metrics import roc_auc_score
        # Construir features observables
        feat = m2.copy()
        feat["is_invest"] = feat["is_investment_related"].map({"si": 1, "no": 0})
        feat["risk_num"] = feat["risk_level"].map({"bajo": 0, "medio": 1, "alto": 2})
        feat["diff_num"] = feat["difficulty"].map({"básico": 0, "intermedio": 1, "avanzado": 2})
        # One-hot topic
        topic_dummies = pd.get_dummies(feat["topic"], prefix="topic")
        X = pd.concat([feat[["is_invest", "risk_num", "diff_num"]], topic_dummies], axis=1)
        y = feat["completed"].astype(int)
        # Muestrear para velocidad
        if len(X) > 20000:
            idx = np.random.RandomState(0).choice(len(X), 20000, replace=False)
            X, y = X.iloc[idx], y.iloc[idx]
        clf = LogisticRegression(max_iter=500)
        clf.fit(X, y)
        auc = roc_auc_score(y, clf.predict_proba(X)[:, 1])
        report["simple_model_auc"] = round(auc, 3)
        report["nondeterminism_ok"] = auc < 0.90
    except Exception as e:
        report["simple_model_auc"] = None
        report["nondeterminism_ok"] = None
        report["sklearn_error"] = str(e)

    # 8. Temporal: progresión de la dificultad completada (aprendizaje).
    #    Para cada usuario con >=6 completados, se compara la dificultad media de los
    #    primeros 3 completados vs los últimos 3 (robusto a la variabilidad).
    comp = m2[m2["completed"]].copy()
    comp = comp.sort_values("timestamp")
    diffs = []
    for uid, g in comp.groupby("user_id"):
        if len(g) >= 6:
            first = g["diff_num"].iloc[:3].mean()
            last = g["diff_num"].iloc[-3:].mean()
            diffs.append(last - first)
    if diffs:
        report["learning_trend"] = round(float(np.mean(diffs)), 4)
        report["learning_ok"] = report["learning_trend"] > 0
    else:
        report["learning_trend"] = None
        report["learning_ok"] = None

    # 9. Cobertura de contenidos
    report["content_coverage"] = round(pop_counts.shape[0] / n_content, 3)

    # Resumen
    checks = [k for k in report if k.endswith("_ok")]
    passed = sum(1 for k in checks if bool(report[k]))
    report["checks_passed"] = f"{passed}/{len(checks)}"

    # Escribir reporte
    with open(out_dir / "validation_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2, default=str)
    return report


def gini(x):
    x = np.sort(np.asarray(x, dtype=float))
    n = len(x)
    if n == 0 or x.sum() == 0:
        return 0.0
    cum = np.cumsum(x)
    return float((n + 1 - 2 * np.sum(cum) / cum[-1]) / n)


def build_users_df(profiles, df):
    """Construye el dataframe de perfiles de usuario (features del cuestionario).

    Añade los conteos reales de interacciones y la etiqueta de cold start, de modo
    que la comparativa pueda separar usuarios con historial de usuarios fríos.
    """
    counts = df.groupby("user_id")["completed"].agg(["count", "sum"]).rename(
        columns={"count": "n_interactions", "sum": "n_completed"}
    )
    rows = []
    for p in profiles:
        uid = p["user_id"]
        n_int = int(counts.loc[uid, "n_interactions"]) if uid in counts.index else 0
        n_comp = int(counts.loc[uid, "n_completed"]) if uid in counts.index else 0
        rows.append({
            "user_id": uid,
            "age": p["age"],
            "age_group": p["age_group"],
            "sex": p["sex"],
            "education_level": p["education_level"],
            "employment_status": p["employment_status"],
            "products": ";".join(p["products"]),
            "theta": round(p["theta"], 4),
            "knowledge_level": p["knowledge_level"],
            "interests": json.dumps(p["interests"], ensure_ascii=False),
            "risk": round(p["risk"], 4),
            "format_pref": json.dumps(p["format_pref"], ensure_ascii=False),
            "activity": round(p["activity"], 4),
            "learn_rate": round(p["learn_rate"], 4),
            "noise_level": round(p["noise_level"], 4),
            "n_interactions": n_int,
            "n_completed": n_comp,
            "cold_start": n_int == 0,
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# FASE 5 — Salida
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Generador de interacciones sintéticas")
    parser.add_argument("--users", type=int, default=PARAMS["n_users"], help="Nº de usuarios")
    parser.add_argument("--seed", type=int, default=42, help="Semilla aleatoria")
    parser.add_argument("--out", type=str, default=None, help="Directorio de salida")
    args = parser.parse_args()

    PARAMS["n_users"] = args.users
    rng = np.random.default_rng(args.seed)
    np.random.seed(args.seed)

    out_dir = Path(args.out) if args.out else DATA_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("GENERADOR DE INTERACCIONES SINTÉTICAS")
    print("=" * 60)

    # FASE 0
    print("\n[FASE 0] Cargando catálogos...")
    cat = load_catalogs()
    print(f"  {len(cat['contents'])} contenidos, {len(cat['concepts'])} conceptos, "
          f"{len(cat['ccm'])} mapeos, {len(cat['prereqs'])} prerrequisitos")

    # FASE 1
    print("\n[FASE 1] Cargando ECF y generando perfiles...")
    ecf = load_ecf_distributions()
    profiles = sample_user_profiles(PARAMS["n_users"], ecf, rng)
    print(f"  {len(profiles)} perfiles generados")

    # FASE 2 + 3
    print("\n[FASE 2+3] Simulando interacciones (temporal causal)...")
    start_date = pd.Timestamp("2025-09-01")
    df = simulate_all(profiles, cat, rng, start_date)
    print(f"  {len(df)} interacciones generadas")

    # FASE 4
    print("\n[FASE 4] Validando...")
    report = validate(df, cat, profiles, out_dir)
    for k, v in report.items():
        print(f"  {k}: {v}")

    # FASE 5
    print("\n[FASE 5] Escribiendo salida...")
    out_csv = out_dir / "interactions_synthetic.csv"
    df.to_csv(out_csv, index=False)
    print(f"  ✓ {out_csv}")

    # Perfiles de usuario (features del cuestionario) + etiqueta de cold start
    users_df = build_users_df(profiles, df)
    out_users = out_dir / "users_synthetic.csv"
    users_df.to_csv(out_users, index=False)
    print(f"  ✓ {out_users}")

    # Metadatos
    n_cold = int(users_df["cold_start"].sum())
    meta = {
        "seed": args.seed,
        "n_users": PARAMS["n_users"],
        "n_interactions": len(df),
        "n_cold_start_users": n_cold,
        "cold_start_criterion": "usuario sin ninguna interacción (n_interactions == 0)",
        "window_start": str(start_date),
        "window_days": PARAMS["window_days"],
        "params": PARAMS,
        "validation": report,
        "note": "Generado desde cero según docs/plan_generar_interacciones.md. "
                "No usa datasets de interacciones previos.",
    }
    with open(out_dir / "generation_metadata.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2, default=str)
    print(f"  ✓ {out_dir / 'generation_metadata.json'}")

    print("\n" + "=" * 60)
    print("COMPLETADO")
    print("=" * 60)


# Topics y formatos globales (para muestreo de intereses)
ALL_TOPICS = ["planificación", "ahorro", "deuda", "crédito", "interés", "inflación",
              "cuentas bancarias", "tarjetas", "préstamos", "hipotecas", "inversión",
              "riesgo", "diversificación", "fraude", "mercado", "contexto"]
ALL_FORMATS = ["artículo web", "PDF", "simulador", "curso web", "calculadora",
               "glosario web", "artículo blog", "nota de prensa", "vídeo educativo",
               "herramienta"]


if __name__ == "__main__":
    main()
