"""Repara concepts.csv y genera la matriz explícita contenido-concepto.

La matriz distingue conceptos enseñados de los prerrequisitos declarados en
contents.csv. Las relaciones se revisan por título/topic y quedan documentadas
con una nota breve para facilitar la auditoría manual.
"""

import csv
from pathlib import Path

DATA = Path("/Users/veronica/Desktop/tfm/data")
CONCEPTS = DATA / "concepts.csv"
CONTENTS = DATA / "contents.csv"
MAP = DATA / "content_concept_map.csv"

CANONICAL_CONCEPTS = [
    ("C01", "Presupuesto", "Planificar ingresos y gastos para equilibrar las finanzas personales", "planificación", "básico"),
    ("C02", "Ahorro", "Reservar una parte de los ingresos para imprevistos y objetivos futuros", "ahorro", "básico"),
    ("C03", "Deuda", "Obligación de pago contraída con un acreedor", "deuda", "básico"),
    ("C04", "Crédito", "Capacidad de obtener dinero prestado con compromiso de devolución", "crédito", "básico"),
    ("C05", "Interés simple", "Interés calculado únicamente sobre el capital inicial", "interés", "básico"),
    ("C06", "Interés compuesto", "Interés calculado sobre el capital más los intereses acumulados", "interés", "intermedio"),
    ("C07", "Inflación", "Aumento generalizado y sostenido de los precios que reduce el poder adquisitivo", "inflación", "intermedio"),
    ("C08", "Cuenta bancaria", "Producto financiero para gestionar ingresos, pagos y ahorro", "cuentas bancarias", "básico"),
    ("C09", "Tarjeta de crédito", "Medio de pago que permite aplazar el cobro con intereses", "tarjetas", "intermedio"),
    ("C10", "Préstamo", "Cantidad de dinero prestada que se devuelve con intereses en cuotas", "préstamos", "intermedio"),
    ("C11", "Hipoteca", "Préstamo a largo plazo garantizado con un inmueble", "hipotecas", "avanzado"),
    ("C12", "Inversión", "Asignación de recursos con el objetivo de obtener rentabilidad futura", "inversión", "intermedio"),
    ("C13", "Riesgo financiero", "Probabilidad de perder parte o todo el capital invertido", "riesgo", "intermedio"),
    ("C14", "Diversificación", "Estrategia de repartir el capital entre distintos activos para reducir riesgo", "diversificación", "intermedio"),
    ("C15", "Fraude financiero", "Engaño para obtener dinero o datos mediante prácticas financieras no autorizadas", "fraude", "básico"),
    ("C16", "Planificación financiera", "Conjunto de decisiones para alcanzar objetivos financieros a corto/medio y largo plazo", "planificación", "intermedio"),
    ("C17", "Tipo de cambio", "Relación de valor entre dos monedas distintas", "mercado", "intermedio"),
    ("C18", "Comisiones bancarias", "Cargos aplicados por entidades por servicios financieros", "cuentas bancarias", "básico"),
    ("C19", "Tasa Anual Equivalente (TAE)", "Indicador que refleja el coste o rendimiento efectivo de un producto financiero en un año", "crédito", "intermedio"),
    ("C20", "Producto Interior Bruto (PIB)", "Valor monetario total de los bienes y servicios producidos en un país", "contexto", "intermedio"),
    ("C21", "Impuestos", "Aportaciones obligatorias a las administraciones públicas", "planificación", "intermedio"),
    ("C22", "Seguros", "Productos financieros que cubren riesgos a cambio de una prima", "riesgo", "intermedio"),
    ("C23", "Plan de pensiones", "Instrumento de ahorro a largo plazo para la jubilación", "planificación", "avanzado"),
    ("C24", "Activos financieros", "Instrumentos en los que se puede invertir (acciones/bonos/fondos)", "inversión", "avanzado"),
    ("C25", "Volatilidad", "Grado de variación del precio de un activo en el tiempo", "riesgo", "avanzado"),
    ("C26", "Fondos de inversión", "Instrumento que agrupa el capital de varios inversores para invertir en una cartera diversificada", "inversión", "avanzado"),
    ("C27", "Criptomonedas", "Activos digitales basados en criptografía que operan en redes descentralizadas", "inversión", "avanzado"),
    ("C28", "Educación financiera", "Conjunto de conocimientos y habilidades para tomar decisiones financieras informadas", "planificación", "básico"),
    ("C29", "Protección de datos", "Medidas para salvaguardar la información personal frente a accesos no autorizados", "fraude", "básico"),
    ("C30", "Finanzas sostenibles", "Decisiones financieras que integran criterios ambientales/sociales y de gobernanza", "inversión", "avanzado"),
]

# Relaciones directas/claras para contenidos cuyo topic no basta para inferir
EXPLICIT = {
    "C004": [("C12", "La guía introduce fundamentos de inversión")],
    "C005": [("C23", "Trata ahorro para jubilación y planes a largo plazo")],
    "C010": [("C23", "Trata preparación de jubilación y ahorro previsional")],
    "C019": [("C09", "Explica tarjetas de crédito y débito")],
    "C020": [("C09", "Explica el crédito revolving y su coste")],
    "C021": [("C04", "Explica crédito al consumo"), ("C10", "Explica préstamos personales")],
    "C026": [("C05", "Explica tipos de interés y conceptos relacionados")],
    "C031": [("C04", "Explica coste/TAE de un préstamo personal"), ("C19", "Explica la TAE")],
    "C032": [("C19", "Explica la TAE de un préstamo hipotecario")],
    "C033": [("C05", "Explica el tipo de interés efectivo")],
    "C034": [("C04", "Explica coste financiero del crédito"), ("C10", "Explica coste financiero de un préstamo")],
    "C039": [("C26", "Explica qué son y cómo funcionan los fondos")],
    "C040": [("C24", "Explica acciones como activos financieros")],
    "C041": [("C13", "Explica riesgo"), ("C14", "Explica diversificación")],
    "C043": [("C28", "Es el plan institucional de educación financiera")],
    "C044": [("C28", "Presenta medición de competencias financieras")],
    "C045": [("C28", "Presenta un marco internacional de alfabetización financiera")],
    "C046": [("C28", "Presenta el marco de competencia financiera de PISA")],
    "C049": [("C05", "Introduce interés simple"), ("C06", "Introduce interés compuesto")],
    "C050": [("C01", "Explica elementos financieros de una nómina")],
    "C051": [("C21", "Explica conceptos básicos de impuestos/IRPF")],
    "C052": [("C22", "Explica tipos y coberturas de seguros")],
    "C053": [("C29", "Explica protección de datos en operaciones financieras")],
    "C054": [("C15", "Explica phishing y fraude"), ("C29", "Explica protección de datos")],
    "C055": [("C30", "Explica criterios ESG y finanzas sostenibles")],
    "C056": [("C27", "Explica riesgos de criptoactivos"), ("C24", "Presenta criptoactivos como clase de activo")],
    "C060": [("C11", "Explica referencia de tipos hipotecarios")],
    "C061": [("C28", "Manual introductorio de educación financiera para universitarios")],
    "C062": [("C12", "Introduce competencias para invertir")],
    "C063": [("C12", "Introduce conceptos básicos de inversión")],
    "C068": [("C13", "Explica sesgos y riesgo en inversión")],
    "C069": [("C26", "Explica fondos de inversión")],
    "C070": [("C26", "Explica ETF como vehículo de inversión colectiva")],
    "C074": [("C23", "Herramienta de planificación de jubilación")],
    "C078": [("C14", "Explica diversificación de cartera")],
}

TOPIC_DEFAULT = {
    "planificación": "C01",
    "ahorro": "C02",
    "deuda": "C03",
    "cuentas bancarias": "C08",
    "tarjetas": "C09",
    "préstamos": "C10",
    "hipotecas": "C11",
    "inversión": "C12",
    "riesgo": "C13",
    "diversificación": "C14",
    "fraude": "C15",
    "interés": "C05",
}


def repair_concepts():
    with CONCEPTS.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["concept_id", "concept_name", "description", "topic", "difficulty"])
        writer.writerows(CANONICAL_CONCEPTS)


def build_map():
    with CONTENTS.open(encoding="utf-8", newline="") as f:
        contents = list(csv.DictReader(f))
    concept_ids = {row[0] for row in CANONICAL_CONCEPTS}
    rows = []
    for content in contents:
        cid = content["content_id"]
        relations = EXPLICIT.get(cid)
        if relations is None:
            concept = TOPIC_DEFAULT.get(content["topic"])
            relations = [(concept, f"Concepto principal inferido del topic {content['topic']}")] if concept else []
        for concept_id, note in relations:
            if concept_id not in concept_ids:
                raise ValueError(f"Concepto desconocido en matriz: {concept_id}")
            rows.append({
                "content_id": cid,
                "concept_id": concept_id,
                "coverage_type": "directa",
                "evidence_note": note,
            })
    # Deduplicar relaciones manteniendo orden.
    unique = {(r["content_id"], r["concept_id"]): r for r in rows}
    with MAP.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["content_id", "concept_id", "coverage_type", "evidence_note"])
        writer.writeheader()
        writer.writerows(unique.values())
    return contents, list(unique.values())


def validate(contents, mapping):
    expected = {row[0] for row in CANONICAL_CONCEPTS}
    assert len(expected) == 30
    assert len(contents) == 78, len(contents)
    assert len({r["content_id"] for r in contents}) == len(contents)
    assert all(set(r) == {
        "content_id", "title", "source", "url", "topic", "subtopic",
        "difficulty", "format", "summary", "learning_objective",
        "prerequisites", "risk_level", "is_investment_related"
    } for r in contents)
    assert all(r["concept_id"] in expected for r in mapping)
    assert all(r["coverage_type"] == "directa" for r in mapping)
    assert {r["content_id"] for r in mapping} == {r["content_id"] for r in contents}

    counts = {concept_id: 0 for concept_id in expected}
    for row in mapping:
        counts[row["concept_id"]] += 1
    return counts


if __name__ == "__main__":
    repair_concepts()
    contents, mapping = build_map()
    counts = validate(contents, mapping)
    print(f"Conceptos reparados: {len(CANONICAL_CONCEPTS)}")
    print(f"Contenidos auditados: {len(contents)}")
    print(f"Relaciones directas creadas: {len(mapping)}")
    print("Cobertura directa por concepto:")
    for concept_id, count in counts.items():
        print(f"  {concept_id}: {count}")
