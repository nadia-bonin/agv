from datetime import datetime
from typing import Optional, List
from .base import BaseModel

class User(BaseModel):
    """Modelo de Usuário"""
    
    def __init__(
        self,
        id: Optional[int] = None,
        name: str = "",
        email: str = "",
        password_hash: Optional[str] = None,
        is_active: bool = True,
        is_superuser: bool = False,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        roles: Optional[List[str]] = None
    ):
        self.id = id
        self.name = name
        self.email = email
        self.password_hash = password_hash
        self.is_active = is_active
        self.is_superuser = is_superuser
        self.created_at = created_at
        self.updated_at = updated_at
        self.roles = roles or []
    
    def validate(self) -> bool:
        """Valida o modelo"""
        if not self.name or len(self.name) < 3:
            raise ValueError("Nome deve ter pelo menos 3 caracteres")
        
        if not self.email or '@' not in self.email:
            raise ValueError("Email inválido")
        
        return True
    
    def to_dict(self, include_password=False):
        """Converte para dict, excluindo senha por padrão"""
        data = super().to_dict()
        if not include_password and 'password_hash' in data:
            del data['password_hash']
        return data