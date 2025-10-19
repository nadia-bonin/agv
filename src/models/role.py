from datetime import datetime
from typing import Optional, List
from .base import BaseModel

class Role(BaseModel):
    """Modelo de Role/Perfil"""

    def __init__(
        self,
        id: Optional[int] = None,
        name: str = "",
        description: Optional[str] = None,
        created_at: Optional[datetime] = None,
        permissions: Optional[List[str]] = None
    ):
        self.id = id
        self.name = name
        self.description = description
        self.created_at = created_at
        self.permissions = permissions or []
