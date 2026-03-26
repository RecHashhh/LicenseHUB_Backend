from fastapi import APIRouter

from app.api.v1.endpoints import (
    audit,
    auth,
    dashboard,
    enterprises,
    licenses,
    reports,
    requests,
    software,
    users,
)

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(enterprises.router, prefix="/enterprises", tags=["Enterprises"])
api_router.include_router(software.router, prefix="/software", tags=["Software"])
api_router.include_router(licenses.router, prefix="/licenses", tags=["Licenses"])
api_router.include_router(requests.router, prefix="/requests", tags=["Requests"])
api_router.include_router(reports.router, prefix="/reports", tags=["Reports"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(audit.router, prefix="/audit", tags=["Audit"])
