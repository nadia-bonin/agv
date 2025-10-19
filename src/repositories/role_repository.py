from typing import Optional, Dict, Any, List
from .base_repository import BaseRepository
from src.utils.database import DatabaseManager

class RoleRepository(BaseRepository):
    """Repositório de roles"""

    def __init__(self):
        super().__init__('roles')

    def find_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Busca role por nome"""
        query = f"SELECT * FROM {self.table_name} WHERE name = %s"

        with DatabaseManager.get_cursor() as (cursor, conn):
            cursor.execute(query, (name,))
            return cursor.fetchone()

    def get_role_permissions(self, role_id: int) -> List[str]:
        """Busca permissões da role"""
        query = """
        SELECT p.name
        FROM permissions p
        INNER JOIN role_permissions rp ON rp.permission_id = p.id
        WHERE rp.role_id = %s
        """

        with DatabaseManager.get_cursor() as (cursor, conn):
            cursor.execute(query, (role_id,))
            results = cursor.fetchall()
            return [row['name'] for row in results]

    def assign_permission(self, role_id: int, permission_id: int) -> bool:
        """Atribui permissão à role"""
        query = """
        INSERT INTO role_permissions (role_id, permission_id)
        VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE role_id = role_id
        """

        with DatabaseManager.get_cursor() as (cursor, conn):
            cursor.execute(query, (role_id, permission_id))
            conn.commit()
            return True
