from typing import Any
from pydantic import BaseModel


class StandardResponse(BaseModel):
    success: bool
    data: Any = None
    error: str | None = None


def ok(data: Any = None) -> dict:
    return {"success": True, "data": data, "error": None}


def err(message: str) -> dict:
    return {"success": False, "data": None, "error": message}
