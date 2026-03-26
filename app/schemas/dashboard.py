from pydantic import BaseModel


class DashboardSummary(BaseModel):
    total_licenses: int
    active_licenses: int
    expired_licenses: int
    expiring_licenses: int
