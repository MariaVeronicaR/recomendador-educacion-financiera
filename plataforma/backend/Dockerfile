# Dockerfile del servicio de recomendación (despliegue a Render)
# Contexto de build: la raíz del proyecto (para poder copiar plataforma/ y data/).
#   docker build -f plataforma/backend/Dockerfile -t tfm-reco .
FROM python:3.11-slim

WORKDIR /app

# Copiar el código del servicio y los datos del catálogo
COPY plataforma/backend/app/ ./app/
COPY plataforma/backend/pyproject.toml ./
COPY data/ ./data/

# Instalar dependencias (sin extras ML/Neo4j por defecto; se activan por config)
RUN pip install --no-cache-dir "fastapi>=0.115" "uvicorn[standard]>=0.30" \
    "pydantic>=2.7" "pydantic-settings>=2.3" "numpy>=1.26" "pandas>=2.2" \
    "python-multipart>=0.0.9"

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
