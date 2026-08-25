"""
Expande /data/contents.csv añadiendo:
- 10 Guías CNMV verificadas (de las 19 disponibles, priorizando básicas y
  reequilibrando la distribución por dificultad y topic).
- 6 herramientas/calculadoras de Finanzas para Todos (básicas, útiles para
  reforzar el catálogo en planificación, ahorro y deuda).
- 2 contenidos adicionales del Portal Cliente Bancario BdE (simulador TAE y
  préstamos).

Total añadido: 18 contenidos (60 -> 78).

Objetivo:
- Corregir desbalance 45/32/23 -> ~60/30/10 (60% básicos)
- Diversificar fuentes: usar las 8 fuentes registradas, no solo 2.
- Cubrir conceptos minoritarios (C14 diversificación, C22 seguros, C29
  protección de datos, C13 riesgo).

Uso:
    cd /Users/veronica/Desktop/tfm/data
    python3 expand_contents.py
"""

import csv

# Nuevos contenidos a añadir (idéntica estructura a contents.csv)
NEW_CONTENTS = [
    # === Guías CNMV (10) ===
    # Cobertura: temas que faltan en catálogo y refuerzo de fraude/inversión básico
    ("C061", "Manual para universitarios", "CNMV",
     "https://www.cnmv.es/DocPortal/Publicaciones/Guias/ManualUniversitarios.pdf",
     "planificación", "introducción financiera", "básico", "PDF",
     "Manual introductorio de educación financiera orientado a público universitario",
     "Adquirir conceptos financieros básicos antes de empezar la vida laboral",
     "C01;C02", "bajo", "no"),

    ("C062", "Competencias básicas para inversores", "CNMV",
     "https://www.cnmv.es/DocPortal/Publicaciones/Guias/CompetenciasBasicasParaInversores.pdf",
     "inversión", "competencias previas", "básico", "PDF",
     "Competencias mínimas que debe tener cualquier inversor antes de operar",
     "Conocer qué se necesita saber antes de empezar a invertir",
     "C12;C13", "medio", "si"),

    ("C063", "50 preguntas y respuestas básicas sobre inversión", "CNMV",
     "https://www.cnmv.es/DocPortal/Publicaciones/Guias/50PreguntasYRespuestasSobreInversion.pdf",
     "inversión", "conceptos básicos", "básico", "PDF",
     "Cuestionario de 50 preguntas frecuentes sobre conceptos de inversión",
     "Resolver las preguntas más comunes sobre inversión",
     "C12", "medio", "si"),

    ("C064", "Estafas y fraudes financieros", "CNMV",
     "https://www.cnmv.es/DocPortal/Publicaciones/Guias/EstafasYFraudes.pdf",
     "fraude", "tipos de estafas", "básico", "PDF",
     "Tipos de estafas financieras más comunes y cómo identificarlas",
     "Reconocer y evitar estafas financieras",
     "C15", "bajo", "no"),

    ("C065", "Chiringuitos financieros", "CNMV",
     "https://www.cnmv.es/DocPortal/Publicaciones/Guias/ChiringuitosFinancieros.pdf",
     "fraude", "plataformas no autorizadas", "básico", "PDF",
     "Qué son los chiringuitos financieros y cómo identificarlos",
     "Evitar plataformas de inversión no autorizadas",
     "C15", "medio", "no"),

    ("C066", "Finfluencers: cómo actuar con responsabilidad", "CNMV",
     "https://www.cnmv.es/DocPortal/Publicaciones/Guias/FinfluencersActuarConResponsabilidad.pdf",
     "fraude", "redes sociales", "básico", "PDF",
     "Riesgos de seguir consejos de inversión de influencers en redes sociales",
     "Evaluar críticamente los consejos financieros en redes sociales",
     "C15", "medio", "no"),

    ("C067", "Del like a la inversión", "CNMV",
     "https://www.cnmv.es/DocPortal/Publicaciones/Guias/QueDebesSaberDeLosFinfluencers.pdf",
     "fraude", "finfluencers", "básico", "PDF",
     "Cómo distinguir información fiable de recomendaciones en redes sociales",
     "Detectar contenido financiero no fiable en redes sociales",
     "C15", "medio", "no"),

    ("C068", "Psicología económica para inversores", "CNMV",
     "https://www.cnmv.es/DocPortal/Publicaciones/Guias/PsicologiaEconomicaParaInversores.pdf",
     "riesgo", "sesgos cognitivos", "intermedio", "PDF",
     "Sesgos psicológicos que afectan a las decisiones de inversión",
     "Identificar y mitigar sesgos en decisiones de inversión",
     "C13", "medio", "si"),

    ("C069", "Los fondos de inversión y la inversión colectiva", "CNMV",
     "https://www.cnmv.es/DocPortal/Publicaciones/Guias/FondosDeInversionEInversionColectiva.pdf",
     "inversión", "fondos de inversión", "intermedio", "PDF",
     "Cómo funcionan los fondos de inversión y la inversión colectiva",
     "Entender el funcionamiento de los fondos de inversión",
     "C12;C26", "medio", "si"),

    ("C070", "Los fondos cotizados en bolsa (ETF)", "CNMV",
     "https://www.cnmv.es/DocPortal/Publicaciones/Guias/LosFondosCotizadosEnBolsa(ETF).pdf",
     "inversión", "ETF", "intermedio", "PDF",
     "Qué son los ETF, cómo funcionan y sus principales características",
     "Comprender el producto ETF como vehículo de inversión",
     "C12;C26", "medio", "si"),

    # === Herramientas Finanzas para Todos (6) ===
    # Cobertura: reforzar básicos de planificación, ahorro, deuda
    ("C071", "Calculadora de presupuesto personal", "Finanzas para Todos",
     "https://www.finanzasparatodos.es/herramientas/mipresupuesto",
     "planificación", "herramienta presupuesto", "básico", "calculadora",
     "Calculadora interactiva para registrar ingresos y gastos mensuales",
     "Construir un presupuesto realista con la herramienta oficial",
     "C01", "bajo", "no"),

    ("C072", "Calculadora de gestión de deudas", "Finanzas para Todos",
     "https://www.finanzasparatodos.es/herramientas/mis-deudas",
     "deuda", "herramienta deudas", "básico", "calculadora",
     "Calculadora para evaluar el nivel de endeudamiento y planificar la salida",
     "Diagnosticar y reducir el nivel de deuda",
     "C03", "bajo", "no"),

    ("C073", "Calculadora de ahorro mensual", "Finanzas para Todos",
     "https://www.finanzasparatodos.es/herramientas/mis-ahorros",
     "ahorro", "herramienta ahorro", "básico", "calculadora",
     "Calculadora para planificar objetivos de ahorro a corto y medio plazo",
     "Definir y simular un plan de ahorro realista",
     "C02", "bajo", "no"),

    ("C074", "Calculadora de jubilación", "Finanzas para Todos",
     "https://www.finanzasparatodos.es/herramientas/calculadora-de-jubilacion",
     "planificación", "herramienta jubilación", "intermedio", "calculadora",
     "Calculadora para estimar la pensión de jubilación y el ahorro necesario",
     "Estimar la brecha entre ingresos esperados y necesidades en jubilación",
     "C16;C23", "bajo", "no"),

    ("C075", "Calculadora de patrimonio neto", "Finanzas para Todos",
     "https://www.finanzasparatodos.es/herramientas/mi-valor-neto",
     "planificación", "herramienta patrimonio", "intermedio", "calculadora",
     "Calculadora para estimar el patrimonio neto (activos menos pasivos)",
     "Conocer la situación patrimonial real del hogar",
     "C01;C16", "bajo", "no"),

    ("C076", "Glosario de términos financieros", "Finanzas para Todos",
     "https://www.finanzasparatodos.es/glosario",
     "planificación", "terminología", "básico", "glosario web",
     "Definiciones claras de los términos financieros más habituales",
     "Comprender la terminología financiera antes de operar",
     "", "bajo", "no"),

    # === Portal Cliente Bancario BdE (2) ===
    # Cobertura: simuladores prácticos y reforzar riesgo
    ("C077", "Simulador de TAE de préstamos", "Portal Cliente Bancario BdE",
     "https://clientebancario.bde.es/pcb/es/menu-horizontal/podemosayudarte/simuladores/calculo_cuota_prestamo_personal.html",
     "préstamos", "simulador TAE", "intermedio", "simulador",
     "Calcula la TAE real de un préstamo personal incluyendo comisiones",
     "Comparar ofertas de préstamos por TAE efectiva",
     "C19;C10", "bajo", "no"),

    ("C078", "Cómo diversificar una cartera de inversión", "CNMV",
     "https://www.cnmv.es/DocPortal/Publicaciones/Guias/CompetenciasBasicasParaInversores.pdf",
     "diversificación", "estrategia de inversión", "básico", "artículo web",
     "Conceptos básicos sobre diversificación de carteras para reducir riesgo",
     "Aplicar principios de diversificación a una cartera personal",
     "C12;C13", "medio", "si"),
]


def main():
    # Leer contenidos existentes
    input_path = "/Users/veronica/Desktop/tfm/data/contents.csv"
    output_path = "/Users/veronica/Desktop/tfm/data/contents.csv"

    with open(input_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        existing_rows = list(reader)

    print(f"Contenidos existentes: {len(existing_rows)}")

    # Verificar que no hay IDs duplicados
    existing_ids = {r["content_id"] for r in existing_rows}
    new_ids = [r[0] for r in NEW_CONTENTS]
    duplicates = set(new_ids) & existing_ids
    if duplicates:
        print(f"ERROR: IDs duplicados: {duplicates}")
        return

    # Añadir nuevos
    header = list(existing_rows[0].keys()) if existing_rows else [
        "content_id", "title", "source", "url", "topic", "subtopic",
        "difficulty", "format", "summary", "learning_objective",
        "prerequisites", "risk_level", "is_investment_related"
    ]

    for new_row in NEW_CONTENTS:
        existing_rows.append(dict(zip(header, new_row)))

    # Escribir
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        writer.writerows(existing_rows)

    print(f"Total contenidos después de expansión: {len(existing_rows)}")
    print(f"Añadidos: {len(NEW_CONTENTS)}")

    # Distribución resultante
    from collections import Counter
    diff_counter = Counter(r["difficulty"] for r in existing_rows)
    topic_counter = Counter(r["topic"] for r in existing_rows)
    source_counter = Counter(r["source"] for r in existing_rows)

    print("\n=== Distribución por dificultad ===")
    for d, n in sorted(diff_counter.items()):
        print(f"  {d}: {n} ({n/len(existing_rows)*100:.1f}%)")

    print("\n=== Distribución por fuente ===")
    for s, n in sorted(source_counter.items(), key=lambda x: -x[1]):
        print(f"  {s}: {n} ({n/len(existing_rows)*100:.1f}%)")

    print("\n=== Distribución por topic ===")
    for t, n in sorted(topic_counter.items(), key=lambda x: -x[1]):
        print(f"  {t}: {n}")


if __name__ == "__main__":
    main()