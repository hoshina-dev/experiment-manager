from typing import Any
from pydantic import BaseModel

class FormSummary(BaseModel):
    id: str
    title: str
    description: str | None = None


class FormPayload(BaseModel):
    id: str
    title: str
    description: str | None = None
    userForm: dict[str, Any]
    workerForm: dict[str, Any]
    calculations: dict[str, str]
    template: str

class FormsListResponse(BaseModel):
    forms: list[FormSummary]