from typing import Optional, Dict, Any
from .base_repository import BaseRepository
from src.utils.database import DatabaseManager

class PermissionRepository(BaseRepository):
    """Repositório de permissões"""
    
    def __init__(self):
        super().__init__('permissions')
    
    def find_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Busca permissão por nome"""
        query = f"SELECT * FROM {self.table_name} WHERE name = %s"
        
        with DatabaseManager.get_cursor() as (cursor, conn):
            cursor.execute(query, (name,))
            return cursor.fetchone()
    
    def find_by_resource_action(self, resource: str, action: str) -> Optional[Dict[str, Any]]:
        """Busca permissão por recurso e ação"""
        query = f"SELECT * FROM {self.table_name} WHERE resource = %s AND action = %s"
        
        with DatabaseManager.get_cursor() as (cursor, conn):
            cursor.execute(query, (resource, action))
            return cursor.fetchone()