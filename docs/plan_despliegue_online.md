# Plan de despliegue de la plataforma en la nube (Online)

Fecha: 2026-08-31
Objetivo: poner la plataforma de educación financiera online para que sea accesible públicamente por tutores y usuarios. El despliegue utiliza servicios gratuitos (free tier) y los modelos ganadores de la evaluación.

---

## 1. Servicios a utilizar

1. **Base de Datos y Auth**: **Supabase** (PostgreSQL y autenticación gestionada).
2. **Servicio IA / Backend (FastAPI)**: **Render** (despliegue mediante Docker).
3. **Frontend (React)**: **Vercel** o **Netlify** (hosting estático rápido para Vite).

---

## 2. Plan de ejecución paso a paso

### Paso 1: Configurar Git y el Dockerfile para producción (Actual)
- Modificar el `.gitignore` del backend para **forzar la inclusión** de los artefactos del modelo ganador (`neumf_profile.pt` [12 KB] y `.json` [5 KB]) en el repositorio de GitHub. Esto evita tener que entrenar en la nube y hace que el build en Render sea determinista.
- Actualizar `plataforma/backend/Dockerfile` para que instale **PyTorch** y **scikit-learn** (dependencias del modelo ganador).

### Paso 2: Subir los cambios a GitHub
- Comitear los archivos modificados y los artefactos del modelo en la rama actual (`clean-project`) y hacer push a GitHub.

### Paso 3: Desplegar el Backend (FastAPI) en Render
- Crear un nuevo **Web Service** en Render conectando el repositorio de GitHub.
- Configurar: Runtime = `Docker`, Rama = `clean-project`, Plan = `Free`.
- Variables de entorno en Render:
  - `RECO_MODEL` = `neumf_profile`
  - `GRAPH_BACKEND` = `inmemory`
  - `CORS_ORIGINS` = `*` (permite la comunicación con el frontend de forma abierta durante el prototipado).
- Guardar la URL pública generada por Render (ej. `https://tfm-reco-api.onrender.com`).

### Paso 4: Desplegar el Frontend (React) en Vercel
- Importar el repositorio en Vercel.
- Configurar:
  - Framework Preset = `Vite`.
  - Root Directory = `plataforma/frontend`.
- Variables de entorno en Vercel:
  - `VITE_SUPABASE_URL` = (URL de producción de Supabase).
  - `VITE_SUPABASE_ANON_KEY` = (Anon Key de producción de Supabase).
  - `VITE_API_URL` = (URL pública del backend obtenida de Render en el Paso 3).
- Ejecutar el Deploy y guardar la URL pública de la plataforma.
