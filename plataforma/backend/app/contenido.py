"""Servicio de contenido: sirve el contenido enriquecido (tldr, key_points,
quiz) y el texto del contenido (scraped) al frontend.

Los JSONs ya existen en data/enriched/ y data/scraped/. Este módulo los carga
y los expone por la API, sin reconstruir nada.
"""

from __future__ import annotations

import json
from pathlib import Path

# Ruta a las carpetas de datos (data/enriched, data/scraped)
_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_ENRICHED_DIR = _PROJECT_ROOT / "data" / "enriched"
_SCRAPED_DIR = _PROJECT_ROOT / "data" / "scraped"


def get_enriched(content_id: str) -> dict | None:
    """Devuelve el contenido enriquecido (tldr, key_points, quiz) o None."""
    path = _ENRICHED_DIR / f"{content_id}.json"
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def get_scraped(content_id: str) -> dict | None:
    """Devuelve el texto/estructura del contenido (scraped) o None."""
    path = _SCRAPED_DIR / f"{content_id}.json"
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def get_content_payload(content_id: str) -> dict | None:
    """Combina el contenido enriquecido y el texto en un solo payload para el
    frontend. Devuelve None si no existe ninguno."""
    enriched = get_enriched(content_id)
    scraped = get_scraped(content_id)

    if enriched is None and scraped is None:
        return None

    payload: dict = {"content_id": content_id}

    if enriched:
        payload["tldr"] = enriched.get("tldr", "")
        payload["key_points"] = enriched.get("key_points", [])
        payload["quiz"] = enriched.get("quiz", [])

    if scraped:
        payload["title"] = scraped.get("title", "")
        payload["text"] = scraped.get("text", "")
        payload["sections"] = scraped.get("sections", [])
        payload["headings"] = scraped.get("headings", [])
        payload["blocks"] = scraped.get("blocks", [])
        payload["url"] = scraped.get("url", "")

    return payload
