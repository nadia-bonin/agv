from typing import Optional, Dict, Any, List
from .base_repository import BaseRepository
from src.utils.database import DatabaseManager

class UserRepository(BaseRepository):
    """Repositório de usuários"""
    
    def __init__(self):
        super().__init__('users')
    
    def find_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Busca usuário por email"""
        query = f"SELECT * FROM {self.table_name} WHERE email = %s"
        
        with DatabaseManager.get_cursor() as (cursor, conn):
            cursor.execute(query, (email,))
            return cursor.fetchone()
    
    def email_exists(self, email: str, exclude_id: Optional[int] = None) -> bool:
        """Verifica se email já existe"""
        query = f"SELECT id FROM {self.table_name} WHERE email = %s"
        params = [email]
        
        if exclude_id:
            query += " AND id != %s"
            params.append(exclude_id)
        
        with DatabaseManager.get_cursor() as (cursor, conn):
            cursor.execute(query, tuple(params))
            return cursor.fetchone() is not None
    
    def get_user_roles(self, user_id: int) -> List[str]:
        """Busca roles do usuário"""
        query = """
        SELECT r.name
        FROM roles r
        INNER JOIN user_roles ur ON ur.role_id = r.id
        WHERE ur.user_id = %s
        """
        
        with DatabaseManager.get_cursor() as (cursor, conn):
            cursor.execute(query, (user_id,))
            results = cursor.fetchall()
            return [row['name'] for row in results]
    
    def get_user_permissions(self, user_id: int) -> List[str]:
        """Busca permissões do usuário"""
        query = """
        SELECT DISTINCT p.name
        FROM permissions p
        INNER JOIN role_permissions rp ON rp.permission_id = p.id
        INNER JOIN user_roles ur ON ur.role_id = rp.role_id
        WHERE ur.user_id = %s
        """
        
        with DatabaseManager.get_cursor() as (cursor, conn):
            cursor.execute(query, (user_id,))
            results = cursor.fetchall()
            return [row['name'] for row in results]
    
    def assign_role(self, user_id: int, role_id: int) -> bool:
        """Atribui role ao usuário"""
        query = """
        INSERT INTO user_roles (user_id, role_id)
        VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE user_id = user_id
        """
        
        with DatabaseManager.get_cursor() as (cursor, conn):
            cursor.execute(query, (user_id, role_id))
            conn.commit()
            return True
    
    def remove_role(self, user_id: int, role_id: int) -> bool:
        """Remove role do usuário"""
        query = "DELETE FROM user_roles WHERE user_id = %s AND role_id = %s"
        
        with DatabaseManager.get_cursor() as (cursor, conn):
            cursor.execute(query, (user_id, role_id))
            conn.commit()
            return cursor.rowcount > 0
            