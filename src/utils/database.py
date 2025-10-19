import mysql.connector
from mysql.connector import pooling, Error
from contextlib import contextmanager
from typing import Generator
from loguru import logger
from config.settings import settings

class DatabaseManager:
    """Gerenciador de conexões com MySQL usando Connection Pool"""

    _pool = None

    @classmethod
    def initialize_pool(cls):
        """Inicializa o connection pool"""
        if cls._pool is None:
            try:
                cls._pool = pooling.MySQLConnectionPool(
                    pool_name="mypool",
                    pool_size=settings.DB_POOL_SIZE,
                    pool_reset_session=True,
                    host=settings.DB_HOST,
                    port=settings.DB_PORT,
                    user=settings.DB_USER,
                    password=settings.DB_PASSWORD,
                    database=settings.DB_NAME,
                    charset=settings.DB_CHARSET
                )
                logger.info("Connection pool inicializado com sucesso")
            except Error as e:
                logger.error(f"Erro ao criar connection pool: {e}")
                raise

    @classmethod
    @contextmanager
    def get_connection(cls) -> Generator:
        """Context manager para obter conexão do pool"""
        if cls._pool is None:
            cls.initialize_pool()

        connection = None
        try:
            connection = cls._pool.get_connection()
            yield connection
        except Error as e:
            logger.error(f"Erro na conexão: {e}")
            raise
        finally:
            if connection and connection.is_connected():
                connection.close()

    @classmethod
    @contextmanager
    def get_cursor(cls, dictionary=True):
        """Context manager para obter cursor"""
        with cls.get_connection() as connection:
            cursor = connection.cursor(dictionary=dictionary)
            try:
                yield cursor, connection
            finally:
                cursor.close()

# Inicializa o pool ao importar
DatabaseManager.initialize_pool()