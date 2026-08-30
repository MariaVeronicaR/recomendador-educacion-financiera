"""Capa de datos del servicio de recomendación.

Reutiliza el harness de evaluación existente (data/scripts/evaluate_models.py)
para cargar el catálogo, los conceptos, los prerrequisitos y los índices
derivados (concepts_of_content, prereq_of_concept, content_diff). No se
reconstruye nada: se importa la función load_data() ya existente.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ruta al harness de evaluación existente (data/scripts/evaluate_models.py).
# Se busca subiendo desde este archivo hasta encontrar la carpeta data/scripts,
# de modo que el código funcione independientemente de dónde se ubique la app.
def _find_scripts_dir() -> Path:
    current = Path(__file__).resolve().parent
    for _ in range(6):  # subir hasta 6 niveles
        candidate = current / "data" / "scripts"
        if (candidate / "evaluate_models.py").exists():
            return candidate
        current = current.parent
    raise FileNotFoundError(
        "No se encontró data/scripts/evaluate_models.py. "
        "El servicio IA necesita el harness de evaluación del proyecto."
    )


_SCRIPTS_DIR = _find_scripts_dir()
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import evaluate_models  # noqa: E402  (import tras ajustar sys.path)

# Cargar los datos una sola vez (módulo singleton). El catálogo es estático.
_DATA = evaluate_models.load_data()


def get_data() -> dict:
    """Devuelve el dict de datos cargado (interacciones, catálogos, índices)."""
    return _DATA


def get_contents_df():
    """DataFrame del catálogo de contenidos."""
    return _DATA["contents"]


def get_concepts_df():
    """DataFrame de conceptos."""
    return _DATA["concepts"]


def get_prereqs_df():
    """DataFrame de prerrequisitos."""
    return _DATA["prereqs"]


def get_concepts_of_content() -> dict:
    """{content_id: [concept_id, ...]} — conceptos que enseña cada contenido."""
    return _DATA["concepts_of_content"]


def get_prereq_of_concept() -> dict:
    """{concept_id: [prerequisite_concept_id, ...]} — prerrequisitos por concepto."""
    return _DATA["prereq_of_concept"]


def get_content_diff() -> dict:
    """{content_id: 0|1|2} — dificultad ordinal (básico/intermedio/avanzado)."""
    return _DATA["content_diff"]
