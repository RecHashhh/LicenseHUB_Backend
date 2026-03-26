# Backend - Autodesk License Manager

API REST construida con FastAPI para gestion de licencias Autodesk.

## Requisitos

- Python 3.11 a 3.13 recomendado
- ODBC Driver 17 for SQL Server

## Configuracion

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
copy .env.example .env
```

## Variables de entorno

```env
APP_NAME=Autodesk License Manager API
API_V1_STR=/api/v1
SECRET_KEY=change-this-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=120
DATABASE_URL=mssql+pyodbc://agarzon:Ag.2025%23@10.0.0.9/SIG_DEV?driver=ODBC+Driver+17+for+SQL+Server
CORS_ORIGINS=http://localhost:5173
```

## Ejecutar API

```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Swagger UI: `http://localhost:8000/docs`

## Endpoints

- `/api/v1/auth`
- `/api/v1/users`
- `/api/v1/software`
- `/api/v1/licenses`
- `/api/v1/requests`
- `/api/v1/reports`
- `/api/v1/dashboard`
- `/api/v1/audit`

## Modulos

```text
app/
  api/        # Rutas y dependencias
  core/       # Configuracion y seguridad
  db/         # Sesion, base y seed
  models/     # Entidades SQLAlchemy
  schemas/    # DTOs Pydantic
  services/   # PDF y auditoria
  utils/      # Reglas de estado de licencia
```
