import json

from typing import Any, Optional, Dict, List, Union
from .base_repository import BaseRepository
from src.utils.database import DatabaseManager
from enum import Enum
from datetime import datetime
from contextlib import contextmanager

class ConfigScope(Enum):
    """Escopo da configuração"""
    GLOBAL = "GLOBAL"           # Configuração geral do sistema
    INSTANCE = "INSTANCE"       # Configuração por instância/servidor
    USER = "USER"               # Configuração específica do usuário

class ConfigType(Enum):
    """Tipo de dado da configuração"""
    BOOLEAN = "BOOLEAN"
    INTEGER = "INTEGER"
    FLOAT = "FLOAT"
    STRING = "STRING"

class ConfigRepository(BaseRepository):
    """Repositório de configurações"""

    def __init__(self):
        super().__init__('configurations')

    @classmethod
    @contextmanager
    def get_connection(cls):
        """Context manager para conexão"""
        if cls._pool is None:
            raise Exception("Pool não inicializado. Chame initialize_pool() primeiro.")

        connection = None
        try:
            connection = cls._pool.get_connection()
            yield connection
        except Error as e:
            print(f"✗ Erro na conexão: {e}")
            raise
        finally:
            if connection and connection.is_connected():
                connection.close()

    @classmethod
    @contextmanager
    def get_cursor(cls, dictionary=True):
        """Context manager para cursor"""
        with cls.get_connection() as connection:
            cursor = connection.cursor(dictionary=dictionary)
            try:
                yield cursor, connection
            finally:
                cursor.close()

# =====================================================
# GERENCIADOR DE CONFIGURAÇÕES
# =====================================================

class ConfigManager:
    """Gerencia configurações do sistema"""

    def __init__(self):
        pass

    def _get_valor_column(self, tipo: ConfigType) -> str:
        """Retorna o nome da coluna de valor baseado no tipo"""
        mapping = {
            ConfigType.BOOLEAN: 'valor_booleano',
            ConfigType.INTEGER: 'valor_inteiro',
            ConfigType.FLOAT: 'valor_real',
            ConfigType.STRING: 'valor_string'
        }
        return mapping[tipo]

    def _convert_value(self, valor: Any, tipo: ConfigType) -> Any:
        """Converte valor para o tipo apropriado"""
        if tipo == ConfigType.BOOLEAN:
            if isinstance(valor, bool):
                return valor
            return str(valor).lower() in ('true', '1', 'yes', 'sim')
        elif tipo == ConfigType.INTEGER:
            return int(valor)
        elif tipo == ConfigType.FLOAT:
            return float(valor)
        else:  # STRING
            return str(valor)

    def set_config(
        self,
        nome: str,
        tela: str,
        valor: Any,
        tipo: ConfigType = ConfigType.STRING,
        escopo: ConfigScope = ConfigScope.GLOBAL,
        instance_id: Optional[str] = None,
        user_id: Optional[int] = None,
        descricao: Optional[str] = None,
        criado_por: str = 'SYSTEM'
    ) -> bool:
        """Define uma configuração"""

        # Validações
        if escopo == ConfigScope.INSTANCE and not instance_id:
            raise ValueError("instance_id é obrigatório para escopo INSTANCE")

        if escopo == ConfigScope.USER and not user_id:
            raise ValueError("user_id é obrigatório para escopo USER")

        # Converter valor
        valor_convertido = self._convert_value(valor, tipo)
        coluna_valor = self._get_valor_column(tipo)

        # Verificar se já existe
        existing = self.get_config(nome, tela, escopo, instance_id, user_id)

        with DatabaseManager.get_cursor() as (cursor, conn):
            try:
                if existing:
                    # UPDATE
                    query = f"""
                    UPDATE configurations
                    SET {coluna_valor} = %s,
                        tipo = %s,
                        descricao = %s,
                        atualizado_por = %s,
                        atualizado_em = NOW()
                    WHERE nome = %s
                      AND tela = %s
                      AND escopo = %s
                      AND (instance_id = %s OR (instance_id IS NULL AND %s IS NULL))
                      AND (user_id = %s OR (user_id IS NULL AND %s IS NULL))
                    """

                    cursor.execute(query, (
                        valor_convertido, tipo.value, descricao, criado_por,
                        nome, tela, escopo.value,
                        instance_id, instance_id,
                        user_id, user_id
                    ))

                    # Registrar no histórico
                    self._add_to_history(
                        cursor,
                        existing['id'],
                        nome,
                        tela,
                        escopo,
                        instance_id,
                        user_id,
                        tipo,
                        existing.get(coluna_valor),
                        valor_convertido,
                        criado_por
                    )

                else:
                    # INSERT
                    query = f"""
                    INSERT INTO configurations
                        (nome, tela, escopo, instance_id, user_id, tipo, {coluna_valor},
                         descricao, criado_por, atualizado_por)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """

                    cursor.execute(query, (
                        nome, tela, escopo.value, instance_id, user_id,
                        tipo.value, valor_convertido, descricao, criado_por, criado_por
                    ))

                conn.commit()
                return True

            except Error as e:
                conn.rollback()
                print(f"✗ Erro ao salvar configuração: {e}")
                raise

    def get_config(
        self,
        nome: str,
        tela: str,
        escopo: ConfigScope = ConfigScope.GLOBAL,
        instance_id: Optional[str] = None,
        user_id: Optional[int] = None,
        default_value: Any = None
    ) -> Optional[Dict]:
        """Busca uma configuração"""

        query = """
        SELECT
            id, nome, tela, escopo, instance_id, user_id, tipo, descricao,
            valor_string, valor_inteiro, valor_real, valor_booleano,
            editavel, visivel, valor_padrao,
            criado_em, atualizado_em, criado_por, atualizado_por
        FROM configurations
        WHERE nome = %s
          AND tela = %s
          AND escopo = %s
          AND (instance_id = %s OR (instance_id IS NULL AND %s IS NULL))
          AND (user_id = %s OR (user_id IS NULL AND %s IS NULL))
        """

        with DatabaseManager.get_cursor() as (cursor, conn):
            cursor.execute(query, (
                nome, tela, escopo.value,
                instance_id, instance_id,
                user_id, user_id
            ))
            result = cursor.fetchone()

            if result:
                return result
            elif default_value is not None:
                return {'valor': default_value}
            else:
                return None

    def get_config_value(
        self,
        nome: str,
        tela: str,
        escopo: ConfigScope = ConfigScope.GLOBAL,
        instance_id: Optional[str] = None,
        user_id: Optional[int] = None,
        default_value: Any = None
    ) -> Any:
        """Busca apenas o valor de uma configuração"""

        config = self.get_config(nome, tela, escopo, instance_id, user_id, default_value)

        # Retornar o valor correto baseado no tipo
        tipo = config.get('tipo')

        if tipo == 'BOOLEAN':
            return config.get('valor_booleano')
        elif tipo == 'INTEGER':
            return config.get('valor_inteiro')
        elif tipo == 'FLOAT':
            return config.get('valor_real')
        elif tipo == 'STRING':
            return config.get('valor_string')
        else:  # STRING
            return default_value

    def get_configs_by_screen(
        self,
        tela: str,
        escopo: Optional[ConfigScope] = None,
        instance_id: Optional[str] = None,
        user_id: Optional[int] = None
    ) -> List[Dict]:
        """Busca todas as configurações de uma tela"""

        query = """
        SELECT
            id, nome, tela, escopo, instance_id, user_id, tipo, descricao,
            valor_string, valor_inteiro, valor_real, valor_booleano,
            editavel, visivel,
            criado_em, atualizado_em
        FROM configurations
        WHERE tela = %s
        """

        params = [tela]

        if escopo:
            query += " AND escopo = %s"
            params.append(escopo.value)

        if instance_id:
            query += " AND instance_id = %s"
            params.append(instance_id)

        if user_id:
            query += " AND user_id = %s"
            params.append(user_id)

        query += " ORDER BY nome"

        with DatabaseManager.get_cursor() as (cursor, conn):
            cursor.execute(query, tuple(params))
            return cursor.fetchall()

    def get_all_user_configs(self, user_id: int) -> List[Dict]:
        """Busca todas as configurações de um usuário"""

        query = """
        SELECT
            id, nome, tela, user_id, tipo, descricao,
            valor_string, valor_inteiro, valor_real, valor_booleano,
            editavel, visivel
        FROM configurations
        WHERE escopo = 'USER' AND user_id = %s
        ORDER BY tela, nome
        """

        with DatabaseManager.get_cursor() as (cursor, conn):
            cursor.execute(query, (user_id,))
            return cursor.fetchall()

    def delete_config(
        self,
        nome: str,
        tela: str,
        escopo: ConfigScope = ConfigScope.GLOBAL,
        instance_id: Optional[str] = None,
        user_id: Optional[int] = None
    ) -> bool:
        """Deleta uma configuração"""

        query = """
        DELETE FROM configurations
        WHERE nome = %s
          AND tela = %s
          AND escopo = %s
          AND (instance_id = %s OR (instance_id IS NULL AND %s IS NULL))
          AND (user_id = %s OR (user_id IS NULL AND %s IS NULL))
        """

        with DatabaseManager.get_cursor() as (cursor, conn):
            try:
                cursor.execute(query, (
                    nome, tela, escopo.value,
                    instance_id, instance_id,
                    user_id, user_id
                ))
                conn.commit()
                return cursor.rowcount > 0
            except Error as e:
                conn.rollback()
                print(f"✗ Erro ao deletar configuração: {e}")
                raise

    def _add_to_history(
        self,
        cursor,
        config_id: int,
        nome: str,
        tela: str,
        escopo: ConfigScope,
        instance_id: Optional[str],
        user_id: Optional[int],
        tipo: ConfigType,
        valor_antigo: Any,
        valor_novo: Any,
        alterado_por: str
    ):
        """Adiciona registro no histórico"""

        query = """
        INSERT INTO configurations_history
            (config_id, nome, tela, escopo, instance_id, user_id, tipo,
             valor_antigo, valor_novo, alterado_por)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        cursor.execute(query, (
            config_id, nome, tela, escopo.value, instance_id, user_id,
            tipo.value, str(valor_antigo), str(valor_novo), alterado_por
        ))

    def get_config_history(
        self,
        nome: str,
        tela: str,
        limit: int = 10
    ) -> List[Dict]:
        """Busca histórico de uma configuração"""

        query = """
        SELECT
            id, config_id, nome, tela, escopo, instance_id, user_id,
            tipo, valor_antigo, valor_novo, alterado_em, alterado_por
        FROM configurations_history
        WHERE nome = %s AND tela = %s
        ORDER BY alterado_em DESC
        LIMIT %s
        """

        with DatabaseManager.get_cursor() as (cursor, conn):
            cursor.execute(query, (nome, tela, limit))
            return cursor.fetchall()
