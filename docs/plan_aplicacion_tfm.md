# Plan de la aplicación del TFM

Fecha: 2026-08-31
Contexto: la aplicación es la plataforma de educación financiera que usa los **modelos ganadores** de la evaluación — **NeuMF-Profile** (cold start, el servible hoy) y **NeuMF** (warm, requiere reentrenar). Este documento describe la arquitectura, el estado actual y el despliegue.

La adaptación de la plataforma al proyecto se documenta en `docs/plan_adaptacion_plataforma.md`.

---

## Arquitectura

```
plataforma/
  backend/            # Servicio de recomendación (FastAPI) — motor de IA
    app/
      schemas.py          # Esquemas de dominio (Pydantic v2) — el contrato
      interfaces.py       # Recomendador y GrafoPedagogico (ABC)
      datos.py            # Capa de datos (lee los CSV del proyecto, autónoma)
      config.py           # Configuración (pydantic-settings)
      orquestador.py      # RecoOrchestrator: ranking → filtro → explicación
      main.py             # FastAPI: /health, /catalog, /content/{id}, /recommend
      grafo/              # Grafo pedagógico (inmemory, neo4j)
      recomendadores/     # Baselines + modelos ML (NeuMF-Profile, NeuMF)
      modelos/            # Arquitecturas NN + transformador de features
    scripts/
      train_serving_models.py   # Entrena y serializa NeuMF-Profile
      import_neo4j.py           # Puebla el grafo en Neo4j (opcional)
    models/             # Artefactos del modelo (gitignored, regenerables)
    tests/              # 14 tests (pytest)
  frontend/           # React + Vite + TypeScript
    src/
      lib/supabase.ts     # Cliente Supabase (auth + datos)
      lib/auth.tsx        # Contexto de autenticación
      lib/api.ts          # Cliente del servicio de recomendación
      lib/profile.ts      # Lee el perfil de Supabase → UserProfile
      lib/events.ts       # Registra interacciones (esquema de eventos)
      pages/              # Login, Inicio, Cuestionario, Recomendaciones, Progreso, Contenido
  supabase/           # schema.sql + migraciones
```

## Modelos

- **NeuMF-Profile** (`RECO_MODEL=neumf_profile`): modelo ganador del cold start. Funciona por features de perfil, así que sirve para un usuario real nuevo tras el cuestionario. Es el modelo servible hoy.
- **NeuMF** (`RECO_MODEL=neumf`): modelo ganador del warm start. Aprende embeddings de `user_id` sobre los usuarios sintéticos; un usuario real no está en ese mapeo, así que requiere reentrenar con interacciones reales (feedback loop).

### Entrenar y servir NeuMF-Profile

```bash
# 1. Entrenar y serializar (desde la raíz del proyecto):
python3 plataforma/backend/scripts/train_serving_models.py
#    Genera en plataforma/backend/models/:
#      neumf_profile.pt, neumf_profile_features.json, neumf_profile_meta.json

# 2. Configurar el backend:
cd plataforma/backend
cp .env.example .env   # RECO_MODEL=neumf_profile
.venv/bin/python -m pip install -e ".[dev,ml]"   # incluye torch y scikit-learn
.venv/bin/uvicorn app.main:app --reload
```

### Feedback loop (reentrenar con datos reales)

El frontend registra interacciones en Supabase con el esquema de eventos del generador (`view/started/completed/quiz_passed/quiz_failed` + `score`). Para reentrenar con datos reales, exportar esas interacciones a un CSV con el mismo formato que `interactions_synthetic_v3.csv` y ejecutar `train_serving_models.py` apuntando a ese CSV.

---

## Endpoints del backend

- `GET /health` — estado y modelo activo
- `GET /catalog` — catálogo de contenidos (con conceptos y prerrequisitos)
- `GET /content/{id}` — contenido enriquecido (tldr, key_points, quiz, texto)
- `POST /recommend` — recomendaciones personalizadas (body: `{profile, top_k}`)

El frontend **no conoce el modelo**: recibe `RecommendationResponse` con `source_model` y `explanations`. Cambiar de modelo = cambiar `RECO_MODEL`, sin tocar el frontend.

---

## Datos de usuario

El perfil que alimenta a NeuMF-Profile se alinea con `users_synthetic.csv`. El cuestionario recoge: edad, sexo, educación, situación laboral, **learning_goal** (objetivo financiero), nivel de conocimiento (Big Three de Lusardi) e intereses. Los campos no recogidos se imputan con mediana/"unknown" (coherente con el onboarding mínimo). Ver `docs/datos_usuario_para_aplicacion.md`.

---

## Despliegue

### Backend (Render, free tier)
- `plataforma/backend/Dockerfile` ya existe.
- Variables de entorno: `RECO_MODEL=neumf_profile`, `GRAPH_BACKEND=inmemory`, `CORS_ORIGINS=<url del frontend>`.
- Los artefactos del modelo (`models/`) deben estar presentes en el build (no están en git; se generan con `train_serving_models.py` o se suben al servicio).

### Frontend (Vercel/Netlify, free tier)
- Build estático (`npm run build`).
- Variables: `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`, `VITE_API_URL=<url del backend>`.

### Supabase
- Ejecutar `supabase/schema.sql` en el SQL Editor.
- Si ya existía un esquema anterior, aplicar las migraciones en `supabase/` (`migracion_learning_goal.sql`, `migracion_interacciones_eventos.sql`, etc.).

---

## Estado actual (2026-08-31)

- ✅ Fase 1: backend desacoplado del harness (baselines autónomos).
- ✅ Fase 2: NeuMF-Profile integrado y serializado.
- ✅ Fase 3: lógica pedagógica alineada con el generador; perfil ampliado.
- ✅ Fase 4: feedback loop (eventos) e item cold start (TF-IDF).
- ✅ Fase 5: limpieza y documentación.
- 14 tests del backend pasan; frontend compila (`tsc` limpio).
