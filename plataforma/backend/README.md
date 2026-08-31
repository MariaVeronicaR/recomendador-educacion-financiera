# Servicio de Recomendación (motor de IA del TFM)

Backend FastAPI que genera recomendaciones personalizadas de contenidos de
educación financiera. Es el **motor de IA** del TFM: la auth y los datos de
usuario los gestiona Supabase (el frontend se conecta a Supabase directamente).

## Arquitectura (desacoplada)

El servicio solo conoce dos **interfaces** (`Recomendador` y `GrafoPedagogico`),
no sus implementaciones. El modelo concreto se selecciona por configuración:

- `RECO_MODEL` → qué recomendador usar (`content_based`, `kg_rules`, `neumf`, …)
- `GRAPH_BACKEND` → qué grafo pedagógico (`inmemory` por defecto, `neo4j` opcional)

**Cambiar de modelo = cambiar una variable de entorno, no reescribir la app.**

```
app/
  schemas.py          # Esquemas de dominio (Pydantic v2) — el contrato
  interfaces.py       # Recomendador y GrafoPedagogico (ABC)
  datos.py            # Capa de datos (reutiliza data/scripts/evaluate_models.py)
  config.py           # Configuración (pydantic-settings)
  orquestador.py      # RecoOrchestrator: ranking → filtro → explicación
  main.py             # FastAPI: /health, /catalog, /recommend
  grafo/              # Implementaciones del grafo (inmemory, neo4j)
  recomendadores/     # Implementaciones del recomendador (baselines, ml)
```

## Puesta en marcha

```bash
cd backend
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
cp .env.example .env   # ajustar RECO_MODEL, etc.
.venv/bin/uvicorn app.main:app --reload
```

Endpoints:
- `GET /health` — estado y modelo activo
- `GET /catalog` — catálogo de contenidos
- `POST /recommend` — recomendaciones (body: `{profile, top_k}`)

## Tests

```bash
.venv/bin/python -m pytest -q
```

## Modelos ML (NeuMF, feature-aware NeuMF)

Los modelos ML se registran en la factory pero se activan por configuración
(`RECO_MODEL=neumf` / `feature_aware_neumf`) cuando el modelo esté entrenado y
el artefacto (checkpoint) esté en `models/`. Hasta entonces se usan los
baselines (`content_based` por defecto). El refactor de los `train_*` del
harness (extraer clases `nn.Module`, separar fit de predict, serializar
checkpoint) se completa en la Fase 4.

## Grafo Neo4j (opcional)

Por defecto se usa `InMemoryGrafo` (sin infraestructura). Para validar el grafo
real con Neo4j:

```bash
.venv/bin/pip install neo4j
.venv/bin/python scripts/import_neo4j.py --password TU_PASSWORD
# y en .env: GRAPH_BACKEND=neo4j
```

## Despliegue

El servicio se despliega a Render (free tier) con un Dockerfile. Ver
`../../docs/plan_aplicacion_tfm.md` (Fase 7) para el despliegue completo.
