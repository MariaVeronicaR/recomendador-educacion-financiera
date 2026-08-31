"""Implementaciones del recomendador (interfaz Recomendador).

Los baselines reutilizan las funciones del harness de evaluación existente
(data/scripts/evaluate_models.py). Los modelos ML (NeuMF, feature-aware NeuMF)
se registran en la factory pero se activan por configuración (RECO_MODEL) cuando
el modelo esté entrenado.
"""

from __future__ import annotations

import json

import numpy as np

from .. import datos
from ..interfaces import Recomendador
from ..schemas import UserProfile


class RuleBasedRecomendador(Recomendador):
    """Recomienda por reglas simples: prioriza contenidos del topic de interés
    del usuario, ordenados por dificultad. No usa ML ni historial."""

    name = "rule_based"

    def rank(self, profile: UserProfile) -> list[str]:
        contents = datos.get_contents_df()
        # Intereses del usuario (topic -> valor)
        interests = profile.interests or {}
        # Ordenar por: interés en el topic (desc) y dificultad (asc)
        diff = datos.get_content_diff()
        scored = []
        for _, row in contents.iterrows():
            topic_score = interests.get(row["topic"], 0.0)
            scored.append((row["content_id"], topic_score, diff.get(row["content_id"], 0)))
        scored.sort(key=lambda x: (-x[1], x[2]))
        return [c for c, _, _ in scored]


class MostPopularRecomendador(Recomendador):
    """Ranking global por frecuencia de interacción (mismo para todos)."""

    name = "most_popular"

    def __init__(self) -> None:
        # Reutiliza baseline_most_popular del harness (sys.path lo expone datos)
        import evaluate_models as em

        train = datos.get_data()["interactions"]
        self._ranked = em.baseline_most_popular(train, datos.get_data())

    def rank(self, profile: UserProfile) -> list[str]:
        return list(self._ranked)


class ContentBasedRecomendador(Recomendador):
    """Similitud coseno entre el perfil de intereses del usuario y el topic del
    contenido. Funciona en cold start (no necesita historial)."""

    name = "content_based"

    def __init__(self) -> None:
        import evaluate_models as em

        users = datos.get_data()["users"]
        self._rank_for_user = em.baseline_content_based(users, datos.get_data())

    def rank(self, profile: UserProfile) -> list[str]:
        # El baseline usa el user_id para buscar intereses en users_synthetic.csv.
        # Para un usuario nuevo (no en el CSV), construimos un perfil sintético
        # con sus intereses y lo evaluamos con la misma lógica coseno.
        uid = profile.user_id
        if uid in self._user_ids():
            return self._rank_for_user(uid)
        return self._rank_from_interests(profile)

    def _user_ids(self) -> set[str]:
        return set(datos.get_data()["users"]["user_id"])

    def _rank_from_interests(self, profile: UserProfile) -> list[str]:
        """Ranking coseno usando solo los intereses del perfil (para usuarios
        nuevos que no están en users_synthetic.csv)."""
        contents = datos.get_contents_df()
        topics = sorted(contents["topic"].unique())
        uvec = np.array([profile.interests.get(t, 0.0) for t in topics])
        norm_u = np.linalg.norm(uvec)
        if norm_u == 0:
            return list(contents["content_id"])
        scores = {}
        for _, row in contents.iterrows():
            cvec = np.zeros(len(topics))
            cvec[topics.index(row["topic"])] = 1.0
            scores[row["content_id"]] = float(np.dot(uvec, cvec) / (norm_u * np.linalg.norm(cvec)))
        return sorted(scores, key=scores.get, reverse=True)


class KgRulesRecomendador(Recomendador):
    """Baseline pedagógico puro: recomienda contenidos cuyos prerrequisitos
    están cubiertos, ordenados por dificultad. No personaliza más allá de la
    maestría."""

    name = "kg_rules"

    def __init__(self) -> None:
        import evaluate_models as em

        data = datos.get_data()
        train = data["interactions"]
        mastery = em.compute_mastery(train, data)
        self._rank_for_user = em.baseline_kg_rules(train, data, mastery)

    def rank(self, profile: UserProfile) -> list[str]:
        # Usa los conceptos dominados del perfil (progreso real del usuario)
        mastered = set(profile.mastered_concepts)
        # Si el perfil no trae mastery, usamos el del harness (train) como fallback
        if not mastered:
            mastered = self._mastery_for(profile.user_id)
        return self._rank_for_user_with_mastery(mastered)

    def _mastery_for(self, uid: str) -> set[str]:
        import evaluate_models as em

        data = datos.get_data()
        train = data["interactions"]
        mastery = em.compute_mastery(train, data)
        return mastery.get(uid, set())

    def _rank_for_user_with_mastery(self, mastered: set[str]) -> list[str]:
        from ..grafo.inmemory import InMemoryGrafo

        grafo = InMemoryGrafo()
        all_ids = [c.content_id for c in grafo.all_contents()]
        coherent = [c for c in all_ids if grafo.is_accessible(c, mastered)]
        incoherent = [c for c in all_ids if c not in coherent]
        diff = datos.get_content_diff()
        coherent.sort(key=lambda c: diff.get(c, 0))
        incoherent.sort(key=lambda c: diff.get(c, 0))
        return coherent + incoherent
