"""
pedagogical_filter.py

Implementa el post-filtro pedagógico para el recomendador del MVP.
Toma la matriz de predicciones generada por train_recommender.py
y filtra las recomendaciones violando los prerrequisitos definidos
en prerequisites.csv y modelados en el grafo.

Salida:
- data/filtered_recommendations.csv (Recomendaciones finales por usuario)

Uso:
    python3 src/models/pedagogical_filter.py
"""

import os
import csv
from collections import defaultdict
import pandas as pd

# Configuración de rutas
DATA_DIR = "/Users/veronica/Desktop/tfm/data"
CONTENTS_FILE = os.path.join(DATA_DIR, "contents.csv")
PREREQS_FILE = os.path.join(DATA_DIR, "prerequisites.csv")
MAP_FILE = os.path.join(DATA_DIR, "content_concept_map.csv")
INTERACTIONS_FILE = os.path.join(DATA_DIR, "interactions_synthetic.csv")
PREDS_FILE = os.path.join(DATA_DIR, "predictions_matrix.csv")
OUT_FILE = os.path.join(DATA_DIR, "filtered_recommendations.csv")

def main():
    print("=" * 60)
    print("EJECUCIÓN DEL FILTRO PEDAGÓGICO (POST-FILTRO)")
    print("=" * 60)

    # 1. Carga de archivos
    print("\n[1/4] Cargando archivos y matriz de predicciones...")
    preds_df = pd.read_csv(PREDS_FILE, index_col=0)
    contents_df = pd.read_csv(CONTENTS_FILE)
    prereqs_df = pd.read_csv(PREREQS_FILE)
    map_df = pd.read_csv(MAP_FILE)
    interactions_df = pd.read_csv(INTERACTIONS_FILE)

    print(f"  Matriz de predicciones cargada: {preds_df.shape} (Usuarios x Contenidos)")
    print(f"  Conceptos con prerrequisitos: {len(prereqs_df)}")
    print(f"  Asociaciones contenido-concepto cargadas: {len(map_df)}")

    # 2. Grafo de prerrequisitos y estado de los usuarios
    print("\n[2/4] Construyendo grafo de prerrequisitos y mapa de aprendizaje...")
    concept_prereqs = defaultdict(list)
    for _, row in prereqs_df.iterrows():
        concept_prereqs[row['concept_id']].append(row['prerequisite_concept_id'])

    content_concepts = defaultdict(list)
    for _, row in map_df.iterrows():
        if row['coverage_type'] == 'directa':
            content_concepts[row['content_id']].append(row['concept_id'])

    user_mastered_concepts = defaultdict(set)
    for _, row in interactions_df.iterrows():
        uid = row['user_id']
        cid = row['content_id']
        event = row['event']

        if event in ['completed', 'quiz_passed']:
            for concept in content_concepts[cid]:
                user_mastered_concepts[uid].add(concept)

    # 3. Aplicación del filtro
    print("\n[3/4] Aplicando post-filtro pedagógico sobre las predicciones...")
    content_details = {r['content_id']: r for _, r in contents_df.iterrows()}

    recommendations = []
    violations_prevented = 0
    total_recommendations_made = 0

    for uid in preds_df.index:
        user_scores = preds_df.loc[uid]
        sorted_contents = user_scores.sort_values(ascending=False)

        user_recommendations = []
        mastered = user_mastered_concepts[uid]

        for cid, score in sorted_contents.items():
            # Excluir contenidos ya vistos
            if cid in [i['content_id'] for _, i in interactions_df[interactions_df['user_id'] == uid].iterrows()]:
                continue

            prereqs = content_concepts[cid]

            qualified = True
            for concept in prereqs:
                required = concept_prereqs[concept]
                if required and not set(required).issubset(mastered):
                    qualified = False
                    violations_prevented += 1
                    break

            if qualified:
                user_recommendations.append((cid, score))
                if len(user_recommendations) == 5:
                    break

        total_recommendations_made += len(user_recommendations)

        for rank, (cid, score) in enumerate(user_recommendations, 1):
            recommendations.append({
                "user_id": uid,
                "rank": rank,
                "content_id": cid,
                "predicted_score": round(score, 4),
                "title": content_details[cid]["title"],
                "topic": content_details[cid]["topic"],
                "difficulty": content_details[cid]["difficulty"]
            })

    # 4. Guardar resultados
    print("\n[4/4] Guardando recomendaciones filtradas en CSV...")
    rec_df = pd.DataFrame(recommendations)
    rec_df.to_csv(OUT_FILE, index=False)

    print(f"  Recomendaciones totales generadas (Top-5): {len(rec_df)}")
    print(f"  Archivo guardado en: {OUT_FILE}")
    print(f"  Violaciones de prerrequisitos pedagógicos prevenidas por el post-filtro: {violations_prevented}")
    print(f"  Ratio medio de acierto del filtro: {violations_prevented / (violations_prevented + total_recommendations_made) * 100:.1f}% de descarte pedagógico")

    print("\n✓ Post-filtro completado con éxito. Las recomendaciones respetan la jerarquía del grafo.")
    print("=" * 60)

if __name__ == "__main__":
    main()
