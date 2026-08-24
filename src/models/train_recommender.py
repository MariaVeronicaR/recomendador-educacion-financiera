"""
train_recommender.py

Entrena un recomendador híbrido de contenidos de educación financiera para el MVP.
Utiliza scikit-learn (TruncatedSVD) para factorización matricial colaborativa
y regresión lineal/Ridge para incorporar metadatos de usuario y contenido (híbrido).

Salida:
- data/predictions_matrix.csv (Matriz de predicciones usuario-contenido para el post-filtro)
- data/recommender_model.pkl (Modelo serializado para inferencia en tiempo real)

Uso:
    python3 src/models/train_recommender.py
"""

import os
import pickle
import numpy as np
import pandas as pd
from sklearn.decomposition import TruncatedSVD
from sklearn.linear_model import Ridge
from sklearn.preprocessing import OneHotEncoder

# Configuración de rutas
DATA_DIR = "/Users/veronica/Desktop/tfm/data"
USERS_FILE = os.path.join(DATA_DIR, "users_synthetic.csv")
CONTENTS_FILE = os.path.join(DATA_DIR, "contents.csv")
INTERACTIONS_FILE = os.path.join(DATA_DIR, "interactions_synthetic.csv")
MODEL_OUT = os.path.join(DATA_DIR, "recommender_model.pkl")
PREDS_OUT = os.path.join(DATA_DIR, "predictions_matrix.csv")

def main():
    print("=" * 60)
    print("ENTRENAMIENTO DEL RECOMENDADOR HÍBRIDO")
    print("=" * 60)

    # 1. Carga de datos
    print("\n[1/5] Cargando archivos del catálogo...")
    users_df = pd.read_csv(USERS_FILE)
    contents_df = pd.read_csv(CONTENTS_FILE)
    interactions_df = pd.read_csv(INTERACTIONS_FILE)

    print(f"  Usuarios registrados: {len(users_df)}")
    print(f"  Contenidos catalogados: {len(contents_df)}")
    print(f"  Interacciones registradas: {len(interactions_df)}")

    # 2. Factorización Matricial Colaborativa (SVD)
    print("\n[2/5] Aplicando Factorización Matricial (SVD) sobre interacciones...")
    interaction_matrix = interactions_df.pivot_table(
        index='user_id',
        columns='content_id',
        values='score',
        fill_value=0.0
    )

    all_users = users_df['user_id'].tolist()
    all_contents = contents_df['content_id'].tolist()
    interaction_matrix = interaction_matrix.reindex(index=all_users, columns=all_contents, fill_value=0.0)

    print(f"  Matriz de interacciones: {interaction_matrix.shape} (Usuarios x Contenidos)")
    sparsity = 1.0 - (np.count_nonzero(interaction_matrix) / interaction_matrix.size)
    print(f"  Dispersión de la matriz: {sparsity*100:.1f}%")

    n_components = min(10, interaction_matrix.shape[1] - 1)
    svd = TruncatedSVD(n_components=n_components, random_state=42)
    user_features_cf = svd.fit_transform(interaction_matrix)
    content_features_cf = svd.components_.T

    print(f"  Factores latentes extraídos: {n_components}")
    print(f"  Varianza explicada acumulada: {svd.explained_variance_ratio_.sum()*100:.1f}%")

    # 3. Procesamiento de features (Híbrido)
    print("\n[3/5] Preprocesando características de usuarios y contenidos...")
    user_cat_cols = ['age_group', 'education_level', 'employment_status',
                     'financial_knowledge_level', 'saving_habit', 'sex']
    user_encoder = OneHotEncoder(handle_unknown='ignore', sparse_output=False)
    user_encoded = user_encoder.fit_transform(users_df[user_cat_cols])
    user_features_df = pd.DataFrame(user_encoded, index=users_df['user_id'])

    content_cat_cols = ['topic', 'difficulty', 'format', 'is_investment_related']
    content_encoder = OneHotEncoder(handle_unknown='ignore', sparse_output=False)
    content_encoded = content_encoder.fit_transform(contents_df[content_cat_cols])
    content_features_df = pd.DataFrame(content_encoded, index=contents_df['content_id'])

    # 4. Entrenamiento (Ridge Regression)
    print("\n[4/5] Entrenando regresor híbrido (Colaborativo + Contenido)...")
    X_train = []
    y_train = []

    for _, row in interactions_df.iterrows():
        uid = row['user_id']
        cid = row['content_id']
        score = row['score']

        u_idx = all_users.index(uid)
        c_idx = all_contents.index(cid)

        u_cf = user_features_cf[u_idx]
        c_cf = content_features_cf[c_idx]

        u_feat = user_features_df.loc[uid].values
        c_feat = content_features_df.loc[cid].values

        interaction_vector = np.concatenate([
            [np.dot(u_cf, c_cf)],
            u_feat,
            c_feat
        ])

        X_train.append(interaction_vector)
        y_train.append(score)

    X_train = np.array(X_train)
    y_train = np.array(y_train)

    recommender = Ridge(alpha=1.0)
    recommender.fit(X_train, y_train)

    train_preds = recommender.predict(X_train)
    mae = np.mean(np.abs(y_train - train_preds))
    rmse = np.sqrt(np.mean((y_train - train_preds) ** 2))
    print(f"  Error Absoluto Medio (MAE): {mae:.3f}")
    print(f"  Error Cuadrático Medio (RMSE): {rmse:.3f}")

    # 5. Generación de predicciones (Matriz completa)
    print("\n[5/5] Generando matriz de predicciones para el post-filtro...")
    predictions = []

    for uid in all_users:
        u_idx = all_users.index(uid)
        u_cf = user_features_cf[u_idx]
        u_feat = user_features_df.loc[uid].values

        user_preds = []
        for cid in all_contents:
            c_idx = all_contents.index(cid)
            c_cf = content_features_cf[c_idx]
            c_feat = content_features_df.loc[cid].values

            vector = np.concatenate([
                [np.dot(u_cf, c_cf)],
                u_feat,
                c_feat
            ])

            pred = recommender.predict([vector])[0]
            pred_clipped = max(0.0, min(1.0, pred))
            user_preds.append(pred_clipped)

        predictions.append(user_preds)

    predictions_df = pd.DataFrame(predictions, index=all_users, columns=all_contents)
    predictions_df.to_csv(PREDS_OUT)
    print(f"  Matriz de predicciones guardada en: {PREDS_OUT}")

    model_pack = {
        'recommender': recommender,
        'svd': svd,
        'user_encoder': user_encoder,
        'content_encoder': content_encoder,
        'user_features_cf': user_features_cf,
        'content_features_cf': content_features_cf,
        'user_features_df': user_features_df,
        'content_features_df': content_features_df,
        'all_users': all_users,
        'all_contents': all_contents
    }

    with open(MODEL_OUT, 'wb') as f:
        pickle.dump(model_pack, f)
    print(f"  Modelo serializado guardado en: {MODEL_OUT}")

    print("\n✓ Entrenamiento completado con éxito. El recomendador está listo para la Fase 2.")
    print("=" * 60)

if __name__ == "__main__":
    main()
