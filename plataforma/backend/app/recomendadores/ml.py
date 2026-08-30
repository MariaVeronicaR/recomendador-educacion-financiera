"""Implementaciones ML del recomendador (NeuMF, feature-aware NeuMF).

Estos son los candidatos del borrador. Se registran en la factory pero se
activan por configuración (RECO_MODEL) cuando el modelo esté entrenado y el
artefacto (checkpoint) esté disponible. Hasta entonces, la app usa los baselines.

El refactor de los train_* del harness (extraer las clases nn.Module, separar
fit de predict, serializar checkpoint) se completa en la Fase 4 cuando se
entrene el modelo final. Aquí dejamos la estructura y la carga desde checkpoint.
"""

from __future__ import annotations

from pathlib import Path

from ..config import settings
from ..interfaces import Recomendador
from ..schemas import UserProfile


class _ModeloCheckpoint(Recomendador):
    """Base para recomendadores que cargan un modelo desde checkpoint."""

    name = "modelo"

    def __init__(self, artifact_name: str) -> None:
        self._artifact_path = Path(settings.model_artifact_path) / artifact_name
        self._model = None
        self._load()

    def _load(self) -> None:
        """Carga el checkpoint (state_dict + mapeos + features). Se implementa
        en la Fase 4 cuando se defina el formato del artefacto."""
        if not self._artifact_path.exists():
            raise FileNotFoundError(
                f"Artefacto del modelo no encontrado: {self._artifact_path}. "
                "Entrena el modelo o usa un baseline (RECO_MODEL=content_based)."
            )
        # TODO(Fase 4): cargar state_dict, u_idx/i_idx, COLD_IDX, n_features,
        # normalizadores y rehidratar el modelo sin re-entrenar.
        raise NotImplementedError(
            "Carga de checkpoint pendiente de implementar en la Fase 4."
        )

    def rank(self, profile: UserProfile) -> list[str]:
        raise NotImplementedError


class BprMfRecomendador(_ModeloCheckpoint):
    """BPR-MF (Matrix Factorization con Bayesian Personalized Ranking).
    En cold start usa fallback de popularidad."""

    name = "bpr_mf"

    def __init__(self) -> None:
        super().__init__("bpr_mf.npz")


class NeumfRecomendador(_ModeloCheckpoint):
    """NeuMF puro (GMF + MLP). Requiere historial; en cold usa fallback."""

    name = "neumf"

    def __init__(self) -> None:
        super().__init__("neumf.pt")


class FeatureAwareNeumfRecomendador(_ModeloCheckpoint):
    """Feature-aware NeuMF: añade features del cuestionario al MLP. Resuelve
    cold start usando solo features. Es el modelo propuesto del borrador."""

    name = "feature_aware_neumf"

    def __init__(self) -> None:
        super().__init__("feature_aware_neumf.pt")
