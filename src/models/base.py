from typing import Dict, Any, Optional
from datetime import datetime

class BaseModel:
    """Classe base para todos os modelos"""
    
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte modelo para dicionário"""
        return {
            key: value for key, value in self.__dict__.items()
            if not key.startswith('_')
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """Cria instância a partir de dicionário"""
        return cls(**data)
    
    def __repr__(self):
        attrs = ', '.join(f"{k}={v!r}" for k, v in self.to_dict().items())
        return f"{self.__class__.__name__}({attrs})"