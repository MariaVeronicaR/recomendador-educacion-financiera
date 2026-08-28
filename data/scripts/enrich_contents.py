"""
Enriquecimiento de contenidos scrapeados con LLM (Claude).

Genera para cada contenido de data/scraped/*.json:
  * tldr: resumen conciso (2-4 frases) de lo mas importante
  * key_points: 3-5 puntos clave
  * quiz: 3 preguntas tipo test (4 opciones, 1 correcta, explicacion),
    cada pregunta etiquetada con el concept_id que evalua

Salida: data/enriched/<content_id>.json (una capa paralela a data/scraped/,
no se mezclan para poder regenerar el enriquecimiento sin re-scrapear).

Reanudable: salta los content_id que ya tienen JSON en data/enriched/
(a menos que se pase --force). Piloto: --pilot C001,C020,C015,C004,C030

Dependencias:
    pip3 install anthropic

Variables de entorno:
    ANTHROPIC_API_KEY  (requerida)

Uso:
    python3 /Users/veronica/Desktop/tfm/data/scripts/enrich_contents.py
    python3 /Users/veronica/Desktop/tfm/data/scripts/enrich_contents.py --pilot C001,C020,C015,C004,C030
    python3 /Users/veronica/Desktop/tfm/data/scripts/enrich_contents.py --force
"""

import argparse
import json
import re
import sys
import time
from pathlib import Path

import anthropic

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent  # data/scripts -> data -> raiz

SCRAPED_DIR = PROJECT_ROOT / "data" / "scraped"
ENRICHED_DIR = PROJECT_ROOT / "data" / "enriched"
CONCEPTS_CSV = PROJECT_ROOT / "data" / "concepts.csv"

MODEL = "claude-haiku-4-5-20251001"
MAX_TOKENS = 4000
# Texto maximo que se envia al modelo (chars). Los contenidos muy largos se
# recortan: el TLDR y el quiz no necesitan los 190KB del manual universitario.
MAX_TEXT_CHARS = 30000
# Pausa entre llamadas para no saturar la API
PAUSE_S = 0.5

PROMPT_VERSION = 1

SYSTEM_PROMPT = """Eres un editor de contenidos de educación financiera para jóvenes de 18-34 años en España. Tu tarea es generar material de estudio a partir de un artículo scrapeado.

Generas SIEMPRE un JSON válido con esta estructura exacta:
{
  "tldr": "resumen conciso del contenido en 2-4 frases, en español",
  "key_points": ["punto clave 1", "punto clave 2", "..."],
  "quiz": [
    {
      "question": "pregunta tipo test en español",
      "options": ["opción A", "opción B", "opción C", "opción D"],
      "correct_index": 0,
      "explanation": "por qué es correcta, 1-2 frases",
      "concept_id": "C07"
    }
  ]
}

Reglas:
- tldr: captura lo ESENCIAL del contenido. Para contenidos largos, condensa; para cortos, no inventes ni rellenes.
- key_points: entre 3 y 5, cada uno una frase corta y autocontenida.
- quiz: exactamente 3 preguntas de opción múltiple (4 opciones, exactamente 1 correcta).
- Las preguntas deben evaluar COMPRENSIÓN del contenido, no memoria literal de frases.
- concept_id: elige de la lista de conceptos disponibles que te doy el que mejor corresponde a cada pregunta.
- Las preguntas y opciones deben ser claras para un joven de 18-34 años. Distractores plausibles pero claramente incorrectos para quien entendió el contenido.
- IGNORA cualquier texto de navegación, redes sociales, suscripciones, llamadas a la acción ("síguenos", "visítanos", "abre en ventana nueva"), footers legales o URLs sueltas: no son parte del contenido educativo.
- Si el contenido es una calculadora o simulador (no un artículo), genera el quiz sobre el CONCEPTO que la herramienta enseña, usando la descripción.
- Si el contenido es un glosario, genera preguntas sobre términos y definiciones representativos.
- No inventes información que no esté en el contenido. Si el contenido es demasiado corto para 3 preguntas, genera las que tenga sentido generar (mínimo 1).
- Responde SOLO con el JSON, sin texto adicional ni markdown fences."""


def load_concepts():
    """Carga concepts.csv para dar al modelo la lista de conceptos validos."""
    import csv
    concepts = []
    with open(CONCEPTS_CSV, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            concepts.append(f"{row['concept_id']} ({row['concept_name']})")
    return concepts


def build_user_prompt(record, concepts_list):
    """Construye el prompt de usuario con el contenido y contexto pedagogico."""
    meta = record.get("csv_meta", {})
    text = record.get("text", "")
    if len(text) > MAX_TEXT_CHARS:
        text = text[:MAX_TEXT_CHARS] + "\n\n[...texto truncado...]"

    # Headings como guia de estructura
    headings = [h["text"] for h in record.get("headings", [])][:20]
    headings_str = "\n".join(f"- {h}" for h in headings) if headings else "(sin encabezados)"

    # Bloques glossary: material excelente para el quiz
    glossary_entries = []
    for b in record.get("blocks", []):
        if b.get("type") == "glossary":
            glossary_entries.extend(b.get("entries", []))
    glossary_str = ""
    if glossary_entries:
        lines = [f"- {e['term']}: {e['definition'][:200]}" for e in glossary_entries[:40] if e.get("term")]
        glossary_str = "\n\nGLOSARIO (terminos y definiciones):\n" + "\n".join(lines)

    concepts_str = "; ".join(concepts_list)

    return f"""CONTENIDO A ENRIQUECER

Metadatos pedagógicos (del catálogo del sistema):
- Título: {meta.get('title', '')}
- Tema: {meta.get('topic', '')} / {meta.get('subtopic', '')}
- Dificultad: {meta.get('difficulty', '')}
- Objetivo de aprendizaje: {meta.get('learning_objective', '')}
- Objetivo del quiz: verificar que el usuario comprendió lo necesario para lograr ese objetivo de aprendizaje.

Conceptos válidos para concept_id (usa el ID exacto, p.ej. "C07"):
{concepts_str}
{glossary_str}

ENCABEZADOS del contenido:
{headings_str}

TEXTO DEL CONTENIDO:
{text}

Genera el JSON con tldr, key_points y quiz."""


def validate_enrichment(data, concepts_valid):
    """Valida la estructura del JSON devuelto por el modelo.
    Devuelve (ok, errores[], data_normalizada)."""
    errors = []
    if not isinstance(data, dict):
        return False, ["respuesta no es un objeto JSON"], None
    if not isinstance(data.get("tldr"), str) or len(data["tldr"].strip()) < 20:
        errors.append("tldr ausente o demasiado corto")
    kp = data.get("key_points")
    if not isinstance(kp, list) or not (2 <= len(kp) <= 6):
        errors.append("key_points debe ser lista de 2-6 elementos")
    else:
        data["key_points"] = [str(x).strip() for x in kp if str(x).strip()][:6]
    quiz = data.get("quiz")
    if not isinstance(quiz, list) or len(quiz) < 1:
        errors.append("quiz ausente o vacio")
    else:
        clean_quiz = []
        for i, q in enumerate(quiz):
            if not isinstance(q, dict):
                errors.append(f"quiz[{i}] no es objeto")
                continue
            opts = q.get("options")
            ci = q.get("correct_index")
            if not isinstance(opts, list) or len(opts) < 2 or len(opts) > 6:
                errors.append(f"quiz[{i}].options invalidas")
                continue
            if not isinstance(ci, int) or not (0 <= ci < len(opts)):
                errors.append(f"quiz[{i}] correct_index fuera de rango")
                continue
            if not q.get("question") or not q.get("explanation"):
                errors.append(f"quiz[{i}] sin question o explanation")
                continue
            concept = q.get("concept_id")
            if concept not in concepts_valid:
                q["concept_id"] = None  # no valido: anular, no rechazar
            clean_quiz.append({
                "question": str(q["question"]).strip(),
                "options": [str(o).strip() for o in opts],
                "correct_index": ci,
                "explanation": str(q["explanation"]).strip(),
                "concept_id": q.get("concept_id"),
            })
        data["quiz"] = clean_quiz
        if not clean_quiz:
            errors.append("quiz vacio tras validacion")
    return len(errors) == 0, errors, data


def enrich_one(client, record, concepts_list, concepts_valid):
    """Llama a la API para un contenido. Devuelve (data, errores[], meta)."""
    prompt = build_user_prompt(record, concepts_list)
    started = time.monotonic()
    try:
        resp = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
    except anthropic.APIStatusError as e:
        return None, [f"api_error: {e.status_code}: {e.message}"], {}
    except anthropic.APIConnectionError as e:
        return None, [f"api_connection_error: {e}"], {}
    elapsed = int((time.monotonic() - started) * 1000)

    # Extraer TODO el texto de la respuesta (el proxy puede devolver los
    # bloques en otro orden o intercalar bloques no-texto)
    parts = []
    for block in resp.content:
        txt = getattr(block, "text", None)
        if txt:
            parts.append(txt)
    raw = "".join(parts).strip()

    # Extraer el JSON (tolerar fences por si el modelo los pone)
    m = re.search(r"```(?:json)?\s*(\{.*\})\s*```", raw, re.DOTALL)
    if m:
        raw = m.group(1)
    else:
        # Si no hay fences, tomar desde la primera llave a la ultima
        i = raw.find("{")
        j = raw.rfind("}")
        if i >= 0 and j > i:
            raw = raw[i:j + 1]
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        # Fallback: reparar JSON roto (comillas sin escapar en espanol,
        # truncamientos menores) con json_repair.
        from json_repair import repair_json
        try:
            repaired = repair_json(raw)
            data = json.loads(repaired)
        except Exception:
            return None, [f"json_decode_error: {e}"], {
                "elapsed_ms": elapsed, "stop_reason": resp.stop_reason, "raw_start": raw[:300]
            }

    ok, errors, data = validate_enrichment(data, concepts_valid)
    meta = {
        "elapsed_ms": elapsed,
        "input_tokens": resp.usage.input_tokens,
        "output_tokens": resp.usage.output_tokens,
    }
    return (data if ok else None), errors, meta


def main():
    import os

    ap = argparse.ArgumentParser(description="Enriquece contenidos scrapeados con tldr + key_points + quiz")
    ap.add_argument("--pilot", type=str, default="", help="IDs separados por coma para un piloto (p.ej. C001,C020)")
    ap.add_argument("--force", action="store_true", help="Regenerar aunque ya exista el JSON enriquecido")
    ap.add_argument("--limit", type=int, default=0, help="Procesar como maximo N contenidos")
    args = ap.parse_args()

    print("=" * 60)
    print("ENRIQUECIMIENTO DE CONTENIDOS CON CLAUDE")
    print("=" * 60)
    print(f"Modelo:      {MODEL}")
    print(f"Entrada:     {SCRAPED_DIR}")
    print(f"Salida:      {ENRICHED_DIR}")
    print()

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    auth_token = os.environ.get("ANTHROPIC_AUTH_TOKEN")
    base_url = os.environ.get("ANTHROPIC_BASE_URL")
    if not api_key and not auth_token:
        print("ERROR: falta autenticacion. Define una de:")
        print("  export ANTHROPIC_API_KEY=sk-ant-...")
        print("  # o (proxy/gateway):")
        print("  export ANTHROPIC_AUTH_TOKEN=<token>")
        print("  export ANTHROPIC_BASE_URL=https://<gateway>/api")
        return

    import csv

    client = anthropic.Anthropic(
        api_key=api_key,
        auth_token=auth_token,
        base_url=base_url,
    )
    if base_url:
        print(f"Gateway:     {base_url}")

    concepts_list = load_concepts()
    concepts_valid = {c.split(" ")[0] for c in concepts_list}

    # Cargar contenidos scrapeados
    pilot_ids = set(p.strip().upper() for p in args.pilot.split(",") if p.strip()) if args.pilot else None
    records = []
    for f in sorted(SCRAPED_DIR.glob("C*.json")):
        if pilot_ids and f.stem not in pilot_ids:
            continue
        records.append(json.load(open(f)))
    if not records:
        print("ERROR: no hay JSONs scrapeados que enriquecer.")
        return
    if args.limit:
        records = records[:args.limit]
    print(f"Contenidos a enriquecer: {len(records)}")
    if pilot_ids:
        print(f"Piloto: {sorted(pilot_ids)}")
    print()

    ENRICHED_DIR.mkdir(parents=True, exist_ok=True)

    results = []
    for i, rec in enumerate(records, start=1):
        cid = rec["content_id"]
        out_path = ENRICHED_DIR / f"{cid}.json"
        if out_path.exists() and not args.force:
            print(f"[{i}/{len(records)}] {cid}  SKIP (ya existe, usa --force para regenerar)")
            results.append({"content_id": cid, "status": "skipped"})
            continue
        meta = rec.get("csv_meta", {})
        print(f"[{i}/{len(records)}] {cid}  {meta.get('format','')}  text_len={rec.get('text_len', 0)}")
        data, errors, api_meta = enrich_one(client, rec, concepts_list, concepts_valid)
        if data is None:
            print(f"  ERROR: {errors}")
            if api_meta.get("stop_reason"):
                print(f"  stop_reason={api_meta['stop_reason']}  raw={api_meta.get('raw_start', '')[:200]!r}")
            results.append({"content_id": cid, "status": "error", "errors": errors})
        else:
            out = {
                "content_id": cid,
                "tldr": data["tldr"],
                "key_points": data["key_points"],
                "quiz": data["quiz"],
                "generated": {
                    "model": MODEL,
                    "date": time.strftime("%Y-%m-%d"),
                    "prompt_version": PROMPT_VERSION,
                    **api_meta,
                },
            }
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(out, f, ensure_ascii=False, indent=2)
            n_q = len(data["quiz"])
            print(f"  OK: tldr={len(data['tldr'])}c, {len(data['key_points'])} puntos, {n_q} preguntas  ({api_meta.get('input_tokens', '?')}in/{api_meta.get('output_tokens', '?')}out)")
            results.append({"content_id": cid, "status": "ok", "quiz_count": n_q})
        time.sleep(PAUSE_S)

    # Resumen
    ok = sum(1 for r in results if r["status"] == "ok")
    skip = sum(1 for r in results if r["status"] == "skipped")
    err = sum(1 for r in results if r["status"] == "error")
    print()
    print("=" * 60)
    print(f"RESUMEN: ok={ok}  skip={skip}  error={err}  total={len(results)}")
    print("=" * 60)
    if err:
        print("\nContenidos con error:")
        for r in results:
            if r["status"] == "error":
                print(f"  {r['content_id']}: {r['errors']}")


if __name__ == "__main__":
    main()