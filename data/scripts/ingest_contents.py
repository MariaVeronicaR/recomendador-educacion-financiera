"""
Ingesta piloto de contenidos del catalogo.

Procesa un subconjunto pequeno de URLs de data/contents.csv. Para cada URL:
  * Si es HTML, descarga con httpx y extrae con Trafilatura.
  * Si es PDF, descarga con httpx y extrae con PyMuPDF.
El objetivo es evaluar la calidad de la extraccion antes de procesar
el catalogo completo.

No modifica data/contents.csv. Escribe un JSON por articulo en
data/scraped/<content_id>.json y dos reportes consolidados
(ingest_report.json y ingest_summary.csv) en el mismo directorio.

Dependencias:
    pip3 install trafilatura lxml pymupdf

Uso:
    python3 /Users/veronica/Desktop/tfm/data/scripts/ingest_contents.py
"""

import csv
import io
import json
import re
import time
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

import httpx
import pymupdf
import trafilatura
from bs4 import BeautifulSoup


# ---------------------------------------------------------------------------
# Rutas y configuracion
# ---------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent  # data/scripts -> data -> raiz

CONTENTS_CSV = PROJECT_ROOT / "data" / "contents.csv"
OUT_DIR = PROJECT_ROOT / "data" / "scraped"

# Piloto: 7 URLs representativas. Cubre HTML (articulo web, BdE, simulador,
# blog, prensa) y 2 PDFs (Finanzas para Todos y CNMV). Si alguna falla el
# script sigue con las demas.
#   C001  articulo web   finanzasparatodos.es
#   C003  nota de prensa finanzasparatodos.es
#   C004  PDF            finanzasparatodos.es  (10 consejos de inversion)
#   C017  articulo web   clientebancario.bde.es
#   C020  simulador HTML clientebancario.bde.es
#   C024  articulo blog  clientebancario.bde.es
#   C062  PDF            cnmv.es                (Guia basica para inversores)
PILOT_IDS = ["C001", "C003", "C004", "C017", "C020", "C024", "C062"]

TIMEOUT_S = 20
MIN_TEXT_LEN = 200  # umbral para clasificar como "ok" vs "short"
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)

# Palabras que delatan un menu/navegacion (heuristica simple).
NAV_WORDS = {
    "menu", "menú", "inicio", "footer", "saltar", "skip", "subir",
    "contacto", "aviso", "legal", "privacidad", "cookies", "compartir",
    "imprimir", "descargar", "twitter", "facebook", "instagram", "youtube",
    "newsletter", "subscrib", "política de cookies",
}


# ---------------------------------------------------------------------------
# Descarga
# ---------------------------------------------------------------------------

def fetch_url(url, timeout=TIMEOUT_S):
    """Devuelve (bytes, status, error_str, elapsed_ms). Nunca lanza excepciones."""
    started = time.monotonic()
    try:
        with httpx.Client(
            follow_redirects=True,
            timeout=timeout,
            headers={"User-Agent": USER_AGENT, "Accept-Language": "es-ES,es;q=0.9"},
        ) as client:
            resp = client.get(url)
        elapsed_ms = int((time.monotonic() - started) * 1000)
        if resp.status_code >= 400:
            return resp.content, resp.status_code, f"http_{resp.status_code}", elapsed_ms
        return resp.content, resp.status_code, None, elapsed_ms
    except httpx.TimeoutException:
        return b"", 0, "timeout", int((time.monotonic() - started) * 1000)
    except httpx.ConnectError as e:
        return b"", 0, f"connection_error: {e}", int((time.monotonic() - started) * 1000)
    except httpx.HTTPError as e:
        return b"", 0, f"http_error: {type(e).__name__}", int((time.monotonic() - started) * 1000)
    except Exception as e:  # red de seguridad final
        return b"", 0, f"exception: {type(e).__name__}: {e}", int((time.monotonic() - started) * 1000)


# ---------------------------------------------------------------------------
# Extraccion con Trafilatura
# ---------------------------------------------------------------------------

_HEADING_TAG_RE = re.compile(r"^head$")
_HEADING_REND_RE = re.compile(r"^h([1-6])$")


def _parse_xml_headings(xml_text):
    """Devuelve lista de {level, text} parseando el XML de Trafilatura.

    Trafilatura emite los encabezados como <head rend="h1|h2|...">texto</head>,
    no como <h1>texto</h1>. Aceptamos ambas formas.
    """
    out = []
    if not xml_text:
        return out
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return out
    for el in root.iter():
        tag = el.tag.split("}", 1)[-1]  # quitar namespace
        level = None
        if _HEADING_TAG_RE.match(tag):
            rend = el.attrib.get("rend", "")
            m = _HEADING_REND_RE.match(rend)
            if m:
                level = int(m.group(1))
        m2 = re.match(r"^h([1-6])$", tag)
        if level is None and m2:
            level = int(m2.group(1))
        if level is not None:
            text = "".join(el.itertext()).strip()
            if text:
                out.append({"level": level, "text": text})
    return out


def _metadata_to_dict(doc):
    """Convierte un Document de Trafilatura a dict limpio (omite campos None)."""
    if doc is None:
        return {}
    d = doc.as_dict()
    # No queremos el body lxml ni fingerprint en el JSON
    for k in ("body", "commentsbody", "fingerprint"):
        d.pop(k, None)
    # Limpiar None
    return {k: v for k, v in d.items() if v not in (None, "", [], {})}


def detect_video(html_bytes, url):
    """Detecta si una pagina HTML contiene un video embebido.

    Devuelve dict con:
      has_video: bool
      video_urls: lista de URLs encontradas (mp4/webm directo, o embed)
      platforms: lista de plataformas detectadas (youtube/vimeo/wistia/direct)
      schema_type: "VideoObject" si hay JSON-LD con @type VideoObject, si no None
      mime: Content-Type que devolvio el servidor (si esta en los headers
            guardados por el caller; por defecto None)
    Estrategia:
      1. Parsear con BeautifulSoup.
      2. Buscar <video> y <source src> dentro de <video>.
      3. Buscar <iframe src> que apunte a youtube/vimeo/wistia/player.
      4. Buscar JSON-LD con @type: VideoObject.
      5. Devolver todo consolidado, deduplicado.
    """
    info = {
        "has_video": False,
        "video_urls": [],
        "platforms": [],
        "schema_type": None,
    }
    if not html_bytes:
        return info
    try:
        soup = BeautifulSoup(html_bytes, "lxml")
    except Exception:
        return info

    seen = set()
    platforms = set()

    def _add(url, platform):
        if not url:
            return
        # Normalizar URLs protocolo-relativas (//dominio/...) a https
        if url.startswith("//"):
            url = "https:" + url
        if url in seen:
            return
        seen.add(url)
        info["video_urls"].append(url)
        if platform:
            platforms.add(platform)

    # 1) <video> directos y sus <source>
    for video in soup.find_all("video"):
        src = video.get("src")
        if src:
            _add(src, "direct")
        for source in video.find_all("source"):
            s = source.get("src")
            if s:
                _add(s, "direct")
        # A veces el poster revela plataforma (menos util)
    # 2) <iframe> embeds
    for iframe in soup.find_all("iframe"):
        src = (iframe.get("src") or "").strip()
        if not src:
            continue
        low = src.lower()
        if "youtube.com" in low or "youtube-nocookie.com" in low or "youtu.be" in low:
            _add(src, "youtube")
        elif "vimeo.com" in low or "player.vimeo.com" in low:
            _add(src, "vimeo")
        elif "wistia" in low or "wistia.net" in low:
            _add(src, "wistia")
        else:
            # iframe generico, no asumimos plataforma
            _add(src, None)
    # 3) JSON-LD con @type: VideoObject
    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        try:
            import json as _json
            data = _json.loads(script.string or "{}")
        except Exception:
            continue
        # JSON-LD puede ser un objeto o una lista
        items = data if isinstance(data, list) else [data]
        for item in items:
            if not isinstance(item, dict):
                continue
            t = item.get("@type")
            if t == "VideoObject" or (isinstance(t, list) and "VideoObject" in t):
                info["schema_type"] = "VideoObject"
                # A veces contentUrl aparece aqui
                content_url = item.get("contentUrl") or item.get("url")
                if content_url:
                    _add(content_url, "direct")
                # Y el embedUrl
                embed_url = item.get("embedUrl")
                if embed_url:
                    _add(embed_url, None)

    info["has_video"] = bool(info["video_urls"]) or info["schema_type"] == "VideoObject"
    info["platforms"] = sorted(platforms)
    return info


def extract_with_trafilatura(html_bytes, url):
    """Ejecuta Trafilatura sobre HTML. Devuelve dict con campos o {} si falla."""
    if not html_bytes:
        return {}
    try:
        html_text = html_bytes.decode("utf-8", errors="replace")
    except Exception:
        return {}

    # 1) Texto principal
    text = trafilatura.extract(
        html_text,
        url=url,
        output_format="txt",
        include_comments=False,
        include_tables=True,
        include_images=False,
        target_language="es",
        favor_precision=False,
        favor_recall=False,
    ) or ""

    # 2) XML con estructura (para sacar headings)
    xml_text = trafilatura.extract(
        html_text,
        url=url,
        output_format="xml",
        include_comments=False,
        include_tables=True,
        include_images=False,
        target_language="es",
        favor_precision=False,
        favor_recall=False,
    ) or ""
    headings = _parse_xml_headings(xml_text)

    # 3) Metadatos (autor, fecha, descripcion, etc.)
    try:
        meta_doc = trafilatura.extract_metadata(html_text, default_url=url)
    except Exception:
        meta_doc = None
    metadata = _metadata_to_dict(meta_doc)

    # 4) Titulo (de metadata si esta, si no del primer heading de nivel 1)
    title = metadata.get("title") or (headings[0]["text"] if headings else "")

    sections = build_sections_offsets(text, headings)
    blocks = build_blocks(text, headings)
    video_info = detect_video(html_bytes, url)

    return {
        "title": title,
        "text": text,
        "text_len": len(text),
        "headings": headings,
        "num_headings": len(headings),
        "sections": sections,
        "blocks": blocks,
        "metadata": metadata,
        "video_info": video_info,
    }


# ---------------------------------------------------------------------------
# Clasificacion heuristica
# ---------------------------------------------------------------------------

def _nav_word_density(text):
    if not text:
        return 0.0
    words = re.findall(r"\w+", text.lower())
    if not words:
        return 0.0
    hits = sum(1 for w in words if w in NAV_WORDS)
    return hits / len(words)


def classify_extraction(text, text_len):
    if text_len == 0:
        return "empty"
    if text_len < MIN_TEXT_LEN:
        return "short"
    density = _nav_word_density(text)
    # Si mas del 4% de las palabras son terminos de menu y ademas es corto,
    # probablemente es solo navegacion.
    if density > 0.04 and text_len < 2000:
        return "navigation_only"
    return "ok"


# ---------------------------------------------------------------------------
# Estructura semantica: sections (offsets) + blocks (anidado)
# ---------------------------------------------------------------------------

def _norm_for_match(s):
    """Normaliza para matching flexible: minusculas, espacios colapsados,
    comillas tipograficas -> rectas, sin espacios extremos."""
    if s is None:
        return ""
    s = s.replace("“", '"').replace("”", '"').replace("’", "'").replace("‘", "'")
    s = re.sub(r"\s+", " ", s).strip().lower()
    return s


def build_sections_offsets(text, headings):
    """Devuelve lista de secciones con offsets de caracteres sobre `text`.

    Estrategia: para cada heading, busca su texto (normalizado) dentro de
    `text` a partir del offset del heading anterior. Si no lo encuentra, se
    anota `found=False` y la seccion queda con offsets -1.
    El start de la primera seccion es 0; el end de cada seccion es el start
    de la siguiente (o len(text) para la ultima).
    """
    sections = []
    if not text or not headings:
        return sections
    cursor = 0
    n = len(text)
    for i, h in enumerate(headings):
        needle = _norm_for_match(h["text"])
        # Si el heading ya incluye un ":" o "?" al final, el match estricto
        # lo encontro exacto. Si no, lo busca por prefijo.
        start = -1
        end = -1
        if needle:
            idx = _norm_for_match(text[cursor:]).find(needle)
            if idx >= 0:
                start = cursor + idx
                end = start + len(h["text"])
        # Calcular end provisional (lo recalcularemos al final)
        sections.append({
            "level": h["level"],
            "heading": h["text"],
            "start": start,
            "end": end,
            "found": start >= 0,
        })
        if start >= 0:
            cursor = end
    # Recalcular ends: el end de cada seccion es el start de la siguiente
    # (o len(text) para la ultima). Si una seccion no se encontro, su end
    # se queda en -1 y la siguiente se ancla al cursor real.
    last_valid_end = 0
    for i, s in enumerate(sections):
        if s["found"]:
            # Buscar la siguiente seccion con start valido
            next_start = len(text)
            for j in range(i + 1, len(sections)):
                if sections[j]["start"] >= 0:
                    next_start = sections[j]["start"]
                    break
            s["end"] = next_start
            last_valid_end = s["end"]
        else:
            s["end"] = -1
    return sections


_LIST_DASH_RE = re.compile(r"^\s*[-•·]\s+")
_LIST_NUM_RE = re.compile(r"^\s*\d+[.)]\s+")


def build_blocks(text, headings):
    """Devuelve lista de bloques semanticos.

    Cada bloque es uno de:
      {"type": "heading", "level": int, "text": str}
      {"type": "paragraph", "text": str}
      {"type": "list", "style": "ul"|"ol", "items": [str, ...]}

    Estrategia: trabaja linea a linea. Para cada linea no vacia:
      - Si coincide con un heading pendiente -> emite bloque heading y lo
        consume de la cola de pendientes.
      - Si es item de lista y las siguientes tambien -> agrupa como lista.
      - En cualquier otro caso -> acumula en un buffer de parrafo.
    Lineas en blanco cierran el parrafo actual.
    """
    if not text:
        return []
    heading_pending = list(headings or [])
    # Mapa rapido de heading normalizado -> heading
    head_index = {_norm_for_match(h["text"]): h for h in heading_pending}

    blocks = []
    para_buf = []  # lineas del parrafo en curso
    list_buf = []  # items de lista en curso (con su estilo)

    def flush_para():
        nonlocal para_buf
        if para_buf:
            blocks.append({"type": "paragraph", "text": "\n".join(para_buf).strip()})
            para_buf = []

    def flush_list():
        nonlocal list_buf
        if list_buf:
            style = list_buf[0][0]
            items = [t for _, t in list_buf]
            blocks.append({"type": "list", "style": style, "items": items})
            list_buf = []

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            # Linea en blanco: cierra parrafo y lista en curso
            flush_para()
            flush_list()
            continue
        # ¿Es un heading pendiente?
        n = _norm_for_match(stripped)
        if heading_pending and _norm_for_match(heading_pending[0]["text"]) == n and n in head_index:
            flush_para()
            flush_list()
            h = heading_pending.pop(0)
            blocks.append({"type": "heading", "level": h["level"], "text": h["text"]})
            continue
        # ¿Es un item de lista? (comprobar antes de agregar a parrafo)
        if _LIST_DASH_RE.match(line):
            flush_para()
            list_buf.append(("ul", _LIST_DASH_RE.sub("", line).strip()))
            continue
        if _LIST_NUM_RE.match(line):
            flush_para()
            list_buf.append(("ol", _LIST_NUM_RE.sub("", line).strip()))
            continue
        # Si estamos en una lista y la linea ya no es item -> cerrarla
        if list_buf:
            flush_list()
        para_buf.append(stripped)

    flush_para()
    flush_list()
    return blocks


# ---------------------------------------------------------------------------
# Extraccion PDF con PyMuPDF
# ---------------------------------------------------------------------------

def is_pdf_url(url):
    """Heuristica simple: la URL apunta a un .pdf (ignorando query/fragmento)."""
    path = urlparse(url).path.lower()
    return path.endswith(".pdf")


def _pdf_date_to_iso(s):
    """Normaliza fechas PDF tipo D:YYYYMMDD... o YYYY-MM-DD... a ISO."""
    if not s:
        return None
    s = str(s).strip()
    if s.startswith("D:"):
        s = s[2:]
    # Limpiar zona horaria tipo +02'00'
    s = re.sub(r"[+\-]\d{2}'\d{2}'?$", "", s).strip()
    digits = re.match(r"^(\d{4})(?:\D?(\d{2})(?:\D?(\d{2}))?)?", s)
    if not digits:
        return s
    y, mo, d = digits.group(1), digits.group(2), digits.group(3)
    if not mo:
        return y
    if not d:
        return f"{y}-{mo}"
    return f"{y}-{mo}-{d}"


def _pdf_metadata_to_dict(doc):
    """Extrae metadata del documento PyMuPDF."""
    meta = doc.metadata or {}
    out = {}
    if meta.get("title"):
        out["title"] = meta["title"].strip()
    if meta.get("author"):
        out["author"] = meta["author"].strip()
    if meta.get("subject"):
        out["subject"] = meta["subject"].strip()
    if meta.get("keywords"):
        out["keywords"] = meta["keywords"].strip()
    if meta.get("creator"):
        out["creator"] = meta["creator"].strip()
    if meta.get("producer"):
        out["producer"] = meta["producer"].strip()
    cd = _pdf_date_to_iso(meta.get("creationDate"))
    if cd:
        out["creation_date"] = cd
    md = _pdf_date_to_iso(meta.get("modDate"))
    if md:
        out["mod_date"] = md
    return out


def _is_page_header(line, page_num):
    """Detecta si una linea es un header/footer de pagina: numero solo,
    numero+palabra corta, o texto repetido conocido."""
    s = line.strip()
    if not s:
        return True
    if re.match(r"^\d{1,3}$", s):
        return True
    if re.match(r"^\d{1,3}\s+[A-Z][\w\s]{1,40}$", s) and len(s) < 50:
        # Patrones tipo "1 Guía de CNMV", "3 Página web", etc.
        return True
    if s.lower() in {"guía de cnmv", "competencias básicas para inversores"}:
        # Header repetido conocido de C062
        return True
    return False


def _pdf_extract_page_clean(page):
    """Extrae el texto de una pagina descartando bandas superior e inferior
    (donde suelen estar los headers/footers repetidos)."""
    rect = page.rect
    h = rect.height
    # Bandas: 4% superior y 4% inferior suelen ser header/footer
    header_band = h * 0.04
    footer_band = h * 0.96
    clip = pymupdf.Rect(0, header_band, rect.width, footer_band)
    try:
        return page.get_text("text", clip=clip) or ""
    except Exception:
        return page.get_text("text") or ""


def _pdf_dominant_body_size(doc, n_sample_pages=3):
    """Estima el tamano de fuente del cuerpo del PDF mirando las paginas
    iniciales. Devuelve el tamano mas frecuente entre los bloques de texto."""
    sizes = Counter()
    for i in range(min(n_sample_pages, doc.page_count)):
        try:
            d = doc[i].get_text("dict")
        except Exception:
            continue
        for block in d.get("blocks", []):
            if block.get("type") != 0:
                continue
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    s = round(span.get("size", 0), 1)
                    if s > 0:
                        sizes[s] += len(span.get("text", ""))
    if not sizes:
        return 11.0
    return sizes.most_common(1)[0][0]


def _pdf_detect_headings_by_size(doc, body_size, level_map=None):
    """Detecta headings de un PDF midiendo el tamano de fuente relativo al
    cuerpo. Devuelve lista [(page_idx, level, text)].

    Estrategia: agrupa spans consecutivos con Y similar (mismo line visual,
    PyMuPDF a veces rompe una linea en multiples entradas) y evalua cada
    grupo por su tamano de fuente medio.

    level_map: lista de (ratio_min, level). Por defecto:
        ratio >= 1.8 -> h1
        ratio >= 1.35 -> h2
        ratio >= 1.25 -> h3
    """
    if level_map is None:
        level_map = [(2.2, 1), (1.7, 2), (1.5, 3)]
    headings = []
    for pno in range(doc.page_count):
        try:
            d = doc[pno].get_text("dict")
        except Exception:
            continue
        # Recoger todos los spans de esta pagina con (y0, size, text, bbox)
        spans = []
        for block in d.get("blocks", []):
            if block.get("type") != 0:
                continue
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    txt = span.get("text", "").strip()
                    if not txt:
                        continue
                    y = span.get("bbox", [0, 0, 0, 0])[1]
                    size = span.get("size", 0)
                    spans.append((y, size, txt, span.get("bbox", [0, 0, 0, 0])))
        if not spans:
            continue
        # Ordenar por y
        spans.sort(key=lambda s: s[0])
        # Agrupar spans con y similares (dentro de 5 puntos)
        groups = []
        for s in spans:
            if groups and abs(s[0] - groups[-1][-1][0]) < 5:
                groups[-1].append(s)
            else:
                groups.append([s])
        # Evaluar cada grupo
        for g in groups:
            line_text = " ".join(s[2] for s in g).strip()
            line_text = re.sub(r"\s+", " ", line_text)
            if not line_text or len(line_text) > 200 or len(line_text) < 3:
                continue
            sizes = [s[1] for s in g if s[1] > 0]
            if not sizes:
                continue
            avg_size = sum(sizes) / len(sizes)
            ratio = avg_size / body_size if body_size else 1.0
            if ratio < 1.5:
                continue
            level = None
            for thresh, lv in sorted(level_map, reverse=True):
                if ratio >= thresh:
                    level = lv
                    break
            if level is None:
                continue
            if _is_page_header(line_text, pno + 1):
                continue
            if re.match(r"^\d+$", line_text):
                continue
            if len(line_text.split()) == 1 and len(line_text) <= 4:
                continue
            if line_text.lower() in {"índice", "indice", "guía", "guia", "€"}:
                continue
            # Filtro adicional: descartar lineas que parecen texto de cuerpo
            # partido. Criterios: contienen coma seguida de minusculas, o
            # tienen 8+ palabras pequenas, o son fragmentos (< 12 chars) que
            # no son titulo de seccion.
            if "," in line_text and any(c.islower() for c in line_text):
                continue
            if len(line_text) < 12:
                continue
            headings.append((pno, level, line_text))
    return headings


def _pdf_guess_title(doc, body_size):
    """Saca el titulo visible del PDF a partir de las primeras paginas.

    Estrategia: leer el texto plano de las 2 primeras paginas, juntar las
    primeras lineas no vacias y devolver la mas larga que no sea header.
    Esto es robusto frente a PDFs con portadas visualmente complejas donde
    los grupos de spans por Y no reconstruyen bien el titulo.
    """
    if doc.page_count == 0:
        return ""
    # Recoger texto plano de las 2 primeras paginas
    first_lines = []
    for pno in range(min(2, doc.page_count)):
        try:
            text = doc[pno].get_text("text") or ""
        except Exception:
            continue
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped or len(stripped) < 5:
                continue
            if _is_page_header(stripped, pno + 1):
                continue
            # Filtrar lineas que son solo simbolos o numeros
            if not any(c.isalpha() for c in stripped):
                continue
            if re.match(r"^\d+$", stripped):
                continue
            first_lines.append(stripped)
            if len(first_lines) >= 6:
                break
        if len(first_lines) >= 6:
            break
    if not first_lines:
        return ""
    # El titulo suele ser la linea mas larga (en caracteres) entre las
    # primeras 6 lineas validas. Empate -> la primera.
    first_lines.sort(key=len, reverse=True)
    return first_lines[0]


def _pdf_clean_full_text(doc):
    """Extrae el texto completo del PDF, pagina a pagina, filtrando headers."""
    parts = []
    for pno in range(doc.page_count):
        page_text = _pdf_extract_page_clean(doc[pno])
        if not page_text.strip():
            continue
        # Filtrar lineas que son headers repetidos conocidos
        clean_lines = []
        for line in page_text.splitlines():
            if _is_page_header(line, pno + 1):
                continue
            clean_lines.append(line)
        clean_page = "\n".join(clean_lines).strip()
        if clean_page:
            parts.append(clean_page)
    full = "\n\n".join(parts)
    full = re.sub(r"[ \t]+", " ", full)
    full = re.sub(r"\n{3,}", "\n\n", full).strip()
    return full


def extract_pdf(pdf_bytes, url):
    """Extrae texto, headings (por font size) y metadata de un PDF con PyMuPDF.

    Devuelve dict con title/text/headings/sections/blocks/metadata/extra o
    un dict con '__error__' si falla la apertura.
    """
    if not pdf_bytes:
        return {}
    try:
        doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    except Exception as e:
        return {"__error__": f"pdf_open_error: {type(e).__name__}: {e}"}

    n_pages = doc.page_count
    metadata = _pdf_metadata_to_dict(doc)
    body_size = _pdf_dominant_body_size(doc)

    # Titulo: metadata PDF > guess por longitud de las primeras lineas.
    # (El titulo canonico del contenido esta en el CSV; esto es un fallback.)
    title = (
        metadata.get("title")
        or _pdf_guess_title(doc, body_size)
        or ""
    )

    # Headings por tamano de fuente
    raw_headings = _pdf_detect_headings_by_size(doc, body_size)
    # Deduplicar manteniendo orden: si el mismo texto aparece en multiples
    # paginas consecutivas, conservamos solo la primera (es el heading real;
    # los demas suelen ser repeticiones en headers de seccion).
    seen = set()
    headings = []
    for pno, level, text in raw_headings:
        key = _norm_for_match(text)
        if key in seen:
            continue
        seen.add(key)
        headings.append({"level": level, "text": text})

    # Texto completo (con headers filtrados)
    full_text = _pdf_clean_full_text(doc)
    sections = build_sections_offsets(full_text, headings)
    blocks = build_blocks(full_text, headings)

    return {
        "title": title,
        "text": full_text,
        "text_len": len(full_text),
        "headings": headings,
        "num_headings": len(headings),
        "sections": sections,
        "blocks": blocks,
        "metadata": metadata,
        "extra": {
            "n_pages": n_pages,
            "body_size": round(body_size, 1),
            "extractor": "pymupdf",
        },
    }


# ---------------------------------------------------------------------------
# Procesamiento de un registro
# ---------------------------------------------------------------------------

def _host_of(url):
    try:
        return urlparse(url).hostname or ""
    except Exception:
        return ""


def _titles_match_loosely(a, b):
    """Compara titulos del CSV y extraido sin acentos y por subcadena."""
    if not a or not b:
        return False
    norm = lambda s: re.sub(r"\s+", " ", s).strip().lower()
    na, nb = norm(a), norm(b)
    if na == nb:
        return True
    if na in nb or nb in na:
        return True
    return False


def process_one(content_id, url, csv_meta):
    """Procesa una URL. Bifurca a HTML o PDF segun la extension."""
    record = {
        "content_id": content_id,
        "url": url,
        "source": csv_meta.get("source", ""),
        "host": _host_of(url),
        "url_type": "pdf" if is_pdf_url(url) else "html",
        "fetch": {"status": 0, "ok": False, "error": None, "elapsed_ms": 0, "bytes": 0},
        "title": "",
        "headings": [],
        "sections": [],
        "blocks": [],
        "text": "",
        "text_len": 0,
        "num_headings": 0,
        "metadata": {},
        "video_info": {"has_video": False, "video_urls": [], "platforms": [], "schema_type": None},
        "classification": "empty",
        "errors": [],
        "title_match": False,
        "csv_meta": {
            "title": csv_meta.get("title", ""),
            "topic": csv_meta.get("topic", ""),
            "subtopic": csv_meta.get("subtopic", ""),
            "difficulty": csv_meta.get("difficulty", ""),
            "format": csv_meta.get("format", ""),
            "summary": csv_meta.get("summary", ""),
            "learning_objective": csv_meta.get("learning_objective", ""),
        },
    }
    errors = record["errors"]

    # 1) Descarga
    body, status, err, elapsed = fetch_url(url)
    record["fetch"] = {
        "status": status,
        "ok": err is None and body != b"",
        "error": err,
        "elapsed_ms": elapsed,
        "bytes": len(body),
    }
    if err is not None or not body:
        record["classification"] = "fetch_error"
        errors.append(err or "empty_body")
        return record

    # 2) Extraccion segun tipo de URL
    is_pdf = record["url_type"] == "pdf"
    try:
        if is_pdf:
            extracted = extract_pdf(body, url)
            if extracted.get("__error__"):
                errors.append(extracted.pop("__error__"))
                record["classification"] = "extract_error"
                return record
            if not extracted or not extracted.get("text"):
                errors.append("pdf_no_text")
                record["classification"] = "empty"
                return record
        else:
            extracted = extract_with_trafilatura(body, url)
            if not extracted or not extracted.get("text"):
                errors.append("trafilatura_no_text")
                record["classification"] = "empty"
                return record
    except Exception as e:
        errors.append(f"extract_exception: {type(e).__name__}: {e}")
        record["classification"] = "extract_error"
        return record

    record["title"] = extracted["title"]
    record["headings"] = extracted["headings"]
    record["sections"] = extracted.get("sections", [])
    record["blocks"] = extracted.get("blocks", [])
    record["text"] = extracted["text"]
    record["text_len"] = extracted["text_len"]
    record["num_headings"] = extracted["num_headings"]
    record["metadata"] = extracted["metadata"]
    # video_info solo se rellena para HTML; PDFs no contienen video
    if is_pdf:
        record["video_info"] = {"has_video": False, "video_urls": [], "platforms": [], "schema_type": None}
    else:
        record["video_info"] = extracted.get("video_info", {"has_video": False, "video_urls": [], "platforms": [], "schema_type": None})
    if is_pdf and "extra" in extracted:
        record["pdf_info"] = extracted["extra"]
    record["title_match"] = _titles_match_loosely(record["title"], csv_meta.get("title", ""))

    record["classification"] = classify_extraction(record["text"], record["text_len"])
    return record


# ---------------------------------------------------------------------------
# Reportes
# ---------------------------------------------------------------------------

def _short_title(t, max_len=60):
    if not t:
        return ""
    t = t.replace("\n", " ").strip()
    if len(t) <= max_len:
        return t
    return t[: max_len - 1] + "…"


def _format_summary_table(records):
    headers = ["content_id", "type", "fmt", "status", "title", "len", "h", "class", "error"]
    rows = []
    for r in records:
        rows.append([
            r["content_id"],
            r.get("url_type", "?"),
            (r["csv_meta"].get("format") or "")[:12],
            str(r["fetch"]["status"] or "-"),
            _short_title(r["title"], 40),
            str(r["text_len"]),
            str(r["num_headings"]),
            r["classification"],
            r["fetch"]["error"] or "",
        ])
    widths = [max(len(str(row[i])) for row in [headers] + rows) for i in range(len(headers))]
    line = "  ".join(headers[i].ljust(widths[i]) for i in range(len(headers)))
    sep = "  ".join("-" * widths[i] for i in range(len(headers)))
    out = [line, sep]
    for row in rows:
        out.append("  ".join(str(row[i]).ljust(widths[i]) for i in range(len(headers))))
    return "\n".join(out)


def write_summary_csv(records, path):
    fields = [
        "content_id", "url", "url_type", "fuente", "format", "status", "ok",
        "title_extracted", "title_csv", "title_match",
        "text_len", "num_headings", "classification", "error",
    ]
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in records:
            w.writerow({
                "content_id": r["content_id"],
                "url": r["url"],
                "url_type": r.get("url_type", ""),
                "fuente": r["source"],
                "format": r["csv_meta"].get("format", ""),
                "status": r["fetch"]["status"],
                "ok": r["fetch"]["ok"],
                "title_extracted": r["title"],
                "title_csv": r["csv_meta"].get("title", ""),
                "title_match": r["title_match"],
                "text_len": r["text_len"],
                "num_headings": r["num_headings"],
                "classification": r["classification"],
                "error": r["fetch"]["error"] or "",
            })


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def load_pilot(csv_path, pilot_ids):
    """Lee el CSV y devuelve {content_id: row} solo para los IDs del piloto."""
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = {row["content_id"]: row for row in reader if row["content_id"] in pilot_ids}
    return rows


def main():
    print("=" * 60)
    print("INGESTA PILOTO DE CONTENIDOS CON TRAFILATURA")
    print("=" * 60)
    print(f"CSV de entrada:  {CONTENTS_CSV}")
    print(f"Directorio out:  {OUT_DIR}")
    print(f"IDs piloto ({len(PILOT_IDS)}): {', '.join(PILOT_IDS)}")
    print(f"Timeout:         {TIMEOUT_S}s")
    print(f"Min text len:    {MIN_TEXT_LEN} chars")
    print()

    if not CONTENTS_CSV.exists():
        print(f"ERROR: no se encuentra {CONTENTS_CSV}")
        return
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    catalog = load_pilot(CONTENTS_CSV, PILOT_IDS)
    missing = [cid for cid in PILOT_IDS if cid not in catalog]
    if missing:
        print(f"AVISO: IDs del piloto no encontrados en el CSV: {missing}")
    if not catalog:
        print("ERROR: no hay IDs validos en el CSV. Abortando.")
        return

    records = []
    total = len(catalog)
    for i, (cid, row) in enumerate(catalog.items(), start=1):
        url = row["url"]
        url_type = "pdf" if is_pdf_url(url) else "html"
        print(f"\n[{i}/{total}] {cid}  [{url_type}]  {row.get('format','')}")
        print(f"  URL:    {url}")
        print(f"  CSV title: {row.get('title','')}")
        rec = process_one(cid, url, row)
        records.append(rec)
        status = rec["fetch"]["status"] or "-"
        cls = rec["classification"]
        err = rec["fetch"]["error"] or ""
        title_short = _short_title(rec["title"], 50)
        print(f"  fetch:  status={status}  bytes={rec['fetch']['bytes']}  ms={rec['fetch']['elapsed_ms']}  err={err or '-'}")
        print(f"  extract: title='{title_short}'")
        extra = ""
        if url_type == "pdf" and "pdf_info" in rec:
            extra = f"  pages={rec['pdf_info'].get('n_pages')}({rec['pdf_info'].get('n_pages_with_text')})"
        print(f"  text_len={rec['text_len']}  headings={rec['num_headings']}  class={cls}{extra}")

    # Guardar un JSON por articulo
    for r in records:
        per_path = OUT_DIR / f"{r['content_id']}.json"
        with open(per_path, "w", encoding="utf-8") as f:
            json.dump(r, f, ensure_ascii=False, indent=2)
    print(f"\n✓ {len(records)} JSON individuales guardados en {OUT_DIR}/")

    # Reporte consolidado JSON
    report_path = OUT_DIR / "ingest_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
    print(f"✓ Reporte JSON: {report_path}")

    # Resumen CSV
    summary_path = OUT_DIR / "ingest_summary.csv"
    write_summary_csv(records, summary_path)
    print(f"✓ Resumen CSV:  {summary_path}")

    # Tabla en pantalla
    print()
    print("=" * 60)
    print("RESUMEN DE LA INGESTA PILOTO")
    print("=" * 60)
    print(_format_summary_table(records))
    print()
    n_ok = sum(1 for r in records if r["classification"] == "ok")
    n_short = sum(1 for r in records if r["classification"] == "short")
    n_empty = sum(1 for r in records if r["classification"] in ("empty", "navigation_only"))
    n_err = sum(1 for r in records if r["classification"] in ("fetch_error", "extract_error"))
    print(f"ok={n_ok}  short={n_short}  empty/nav={n_empty}  errores={n_err}  total={len(records)}")
    print()
    print("Para revisar: abre data/scraped/<content_id>.json y el CSV resumen.")


if __name__ == "__main__":
    main()
