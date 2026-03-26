from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.db.base import Base
from app.db.init_db import seed_admin_user, seed_software_catalog
from app.db.session import engine, SessionLocal

settings = get_settings()

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_admin_user(db)
        seed_software_catalog(db)


@app.get("/")
def healthcheck():
    return {"status": "ok", "service": settings.app_name}


app.include_router(api_router, prefix=settings.api_v1_str)
