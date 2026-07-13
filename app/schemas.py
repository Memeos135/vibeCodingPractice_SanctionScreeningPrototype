from typing import Optional

from pydantic import BaseModel


class ScreenResponse(BaseModel):
    status: str
    case_id: Optional[str] = None
    decision: Optional[str] = None
    match: Optional[dict] = None
    matches: Optional[list] = None


class ResolveResponse(BaseModel):
    status: str
    decision: str
    case_id: str
