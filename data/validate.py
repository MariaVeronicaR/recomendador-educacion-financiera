"""Calcula estadísticas para validation_summary.md."""

import csv
from collections import Counter

DATA = "/Users/veronica/Desktop/tfm/data"


def main():
    # Sources
    with open(f"{DATA}/sources.csv", encoding="utf-8") as f:
        sources = list(csv.DictReader(f))

    # Concepts
    with open(f"{DATA}/concepts.csv", encoding="utf-8") as f:
        concepts = list(csv.DictReader(f))

    # Prerequisites
    with open(f"{DATA}/prerequisites.csv", encoding="utf-8") as f:
        prereqs = list(csv.DictReader(f))

    # Contents
    with open(f"{DATA}/contents.csv", encoding="utf-8") as f:
        contents = list(csv.DictReader(f))

    # Users
    with open(f"{DATA}/users_synthetic.csv", encoding="utf-8") as f:
        users = list(csv.DictReader(f))

    # Interactions
    with open(f"{DATA}/interactions_synthetic.csv", encoding="utf-8") as f:
        inter = list(csv.DictReader(f))

    diff = Counter(c["difficulty"] for c in contents)
    topic = Counter(c["topic"] for c in contents)
    invest = sum(1 for c in contents if c["is_investment_related"] == "si")

    # Validación: % contenidos con URL oficial
    official = [c for c in contents if c["url"].startswith("https://")]

    # Interacciones por evento y por dificultad de contenido
    with open(f"{DATA}/contents.csv", encoding="utf-8") as f:
        cidx = {c["content_id"]: c for c in csv.DictReader(f)}
    event_counter = Counter(i["event"] for i in inter)
    inter_diff = Counter(cidx[i["content_id"]]["difficulty"] for i in inter)

    # Distribución de usuarios por nivel de conocimiento
    know = Counter(u["financial_knowledge_level"] for u in users)

    # % recomendaciones que respetan nivel (regla 1 y 2):
    # para usuarios con knowledge=bajo, cuántas interacciones son con básicos
    user_map = {u["user_id"]: u for u in users}
    user_diff_count = Counter()
    for i in inter:
        u = user_map[i["user_id"]]
        if u["financial_knowledge_level"] == "bajo":
            user_diff_count[cidx[i["content_id"]]["difficulty"]] += 1

    print(f"Fuentes: {len(sources)}")
    print(f"Contenidos: {len(contents)} (con URL https: {len(official)})")
    print(f"Conceptos: {len(concepts)}")
    print(f"Prerrequisitos: {len(prereqs)}")
    print(f"Usuarios: {len(users)}")
    print(f"Interacciones: {len(inter)}")
    print(f"Dificultad contenidos: {dict(diff)}")
    print(f"Contenidos de inversión: {invest}")
    print(f"Eventos: {dict(event_counter)}")
    print(f"Interacciones por dificultad contenido: {dict(inter_diff)}")
    print(f"Usuarios por conocimiento: {dict(know)}")
    print(f"Usuarios nivel bajo -> dificultad contenido: {dict(user_diff_count)}")
    print(f"Top 5 topics: {topic.most_common(5)}")
    print(f"% contenidos con URL https: {len(official)/len(contents)*100:.1f}%")


if __name__ == "__main__":
    main()
