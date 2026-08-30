"""Factory de recomendadores: selecciona la implementación por configuración.

RECO_MODEL=rule_based | most_popular | content_based | kg_rules | bpr_mf |
           neumf | feature_aware_neumf

Cambiar de modelo = cambiar RECO_MODEL, sin tocar el resto de la app.
"""

from __future__ import annotations

from ..config import settings
from ..interfaces import Recomendador
from .baselines import (
    ContentBasedRecomendador,
    KgRulesRecomendador,
    MostPopularRecomendador,
    RuleBasedRecomendador,
)


def build_recomendador() -> Recomendador:
    key = settings.reco_model.lower()
    if key == "rule_based":
        return RuleBasedRecomendador()
    if key == "most_popular":
        return MostPopularRecomendador()
    if key == "content_based":
        return ContentBasedRecomendador()
    if key == "kg_rules":
        return KgRulesRecomendador()
    if key == "bpr_mf":
        from .ml import BprMfRecomendador

        return BprMfRecomendador()
    if key == "neumf":
        from .ml import NeumfRecomendador

        return NeumfRecomendador()
    if key == "feature_aware_neumf":
        from .ml import FeatureAwareNeumfRecomendador

        return FeatureAwareNeumfRecomendador()
    raise ValueError(
        f"RECO_MODEL desconocido: {key}. "
        "Valores válidos: rule_based, most_popular, content_based, kg_rules, "
        "bpr_mf, neumf, feature_aware_neumf."
    )
