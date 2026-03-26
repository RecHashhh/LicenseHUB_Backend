from datetime import datetime

from pydantic import BaseModel


class AuditRead(BaseModel):
    id: int
    user_id: int
    action: str
    entity: str
    entity_id: str
    details: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
