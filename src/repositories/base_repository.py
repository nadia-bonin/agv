from typing import List, Optional, Dict, Any
from abc import ABC, abstractmethod
from src.utils.database import DatabaseManager
from src.utils.exceptions import RecordNotFoundError, DuplicateRecordError
from mysql.connector import Error, IntegrityError
from loguru import logger

class BaseRepository(ABC):
    """Repositório base com operações CRUD"""
    
    def __init__(self, table_name: str):
        self.table_name = table_name
    
    def find_by_id(self, id: int) -> Optional[Dict[str, Any]]:
        """Busca registro por ID"""
        query = f"SELECT * FROM {self.table_name} WHERE id = %s"
        
        with DatabaseManager.get_cursor() as (cursor, conn):
            cursor.execute(query, (id,))
            result = cursor.fetchone()
            
            if not result:
                raise RecordNotFoundError(f"Registro com ID {id} não encontrado")
            
            return result
    
    def find_all(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Lista todos os registros"""
        query = f"SELECT * FROM {self.table_name} LIMIT %s OFFSET %s"
        
        with DatabaseManager.get_cursor() as (cursor, conn):
            cursor.execute(query, (limit, offset))
            return cursor.fetchall()
    
    def create(self, data: Dict[str, Any]) -> int:
        """Cria novo registro"""
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['%s'] * len(data))
        query = f"INSERT INTO {self.table_name} ({columns}) VALUES ({placeholders})"
        
        try:
            with DatabaseManager.get_cursor() as (cursor, conn):
                cursor.execute(query, tuple(data.values()))
                conn.commit()
                return cursor.lastrowid
        except IntegrityError as e:
            logger.error(f"Erro de integridade: {e}")
            raise DuplicateRecordError("Registro duplicado")
        except Error as e:
            logger.error(f"Erro ao criar registro: {e}")
            raise
    
    def update(self, id: int, data: Dict[str, Any]) -> bool:
        """Atualiza registro"""
        set_clause = ', '.join([f"{key} = %s" for key in data.keys()])
        query = f"UPDATE {self.table_name} SET {set_clause} WHERE id = %s"
        values = tuple(data.values()) + (id,)
        
        with DatabaseManager.get_cursor() as (cursor, conn):
            cursor.execute(query, values)
            conn.commit()
            return cursor.rowcount > 0
    
    def delete(self, id: int) -> bool:
        """Deleta registro"""
        query = f"DELETE FROM {self.table_name} WHERE id = %s"
        
        with DatabaseManager.get_cursor() as (cursor, conn):
            cursor.execute(query, (id,))
            conn.commit()
            return cursor.rowcount > 0
    
    def count(self) -> int:
        """Conta registros"""
        query = f"SELECT COUNT(*) as total FROM {self.table_name}"
        
        with DatabaseManager.get_cursor() as (cursor, conn):
            cursor.execute(query)
            result = cursor.fetchone()
            return result['total'] if result else 0