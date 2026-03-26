from datetime import date, datetime

from pydantic import BaseModel

from app.models.license_request import RequestStatusEnum, RequestTypeEnum


class RequestBase(BaseModel):
    request_type: RequestTypeEnum
    user_id: int
    software_id: int
    project_name: str
    justification: str
    required_date: date
    payment_method: str | None = None
    contact_info: str | None = None
    process_owner: str | None = None


class RequestCreate(RequestBase):
    pass


class RequestUpdateStatus(BaseModel):
    status: RequestStatusEnum


class RequestRead(RequestBase):
    id: int
    status: RequestStatusEnum
    created_at: datetime
    software_name: str
    user_name: str

    model_config = {"from_attributes": True}
