from datetime import datetime
from typing import Optional
from .base import BaseModel

class Permission(BaseModel):
    """Modelo de Permissão"""
    
    def __init__(
        self,
        id: Optional[int] = None,
        name: str = "",
        resource: str = "",
        action: str = "",
        description: Optional[str] = None,
        created_at: Optional[datetime] = None
    ):
        self.id = id
        self.name = name
        self.resource = resource
        self.action = action
        self.description = description
        self.created_at = created_at
        