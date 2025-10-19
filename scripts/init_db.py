"""Script para inicializar o banco de dados"""

import sys
import os

# Adicionar o diretório raiz ao Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.database import DatabaseManager
from loguru import logger
from src.log.log import AppLogger, UserContext

logger = AppLogger.get_logger(__name__)


def create_tables():
    """Cria as tabelas do banco"""

    users_table = """
    CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        email VARCHAR(255) NOT NULL UNIQUE,
        password_hash VARCHAR(255) NOT NULL,
        is_active BOOLEAN DEFAULT TRUE,
        is_superuser BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        INDEX idx_email (email),
        INDEX idx_is_active (is_active)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """

    roles_table = """
    CREATE TABLE IF NOT EXISTS roles (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(100) NOT NULL UNIQUE,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        INDEX idx_name (name)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """

    permissions_table = """
    CREATE TABLE IF NOT EXISTS permissions (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(100) NOT NULL UNIQUE,
        resource VARCHAR(100) NOT NULL,
        action VARCHAR(50) NOT NULL,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        INDEX idx_name (name),
        INDEX idx_resource_action (resource, action)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """

    user_roles_table = """
    CREATE TABLE IF NOT EXISTS user_roles (
        user_id INT NOT NULL,
        role_id INT NOT NULL,
        assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (user_id, role_id),
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """

    role_permissions_table = """
    CREATE TABLE IF NOT EXISTS role_permissions (
        role_id INT NOT NULL,
        permission_id INT NOT NULL,
        assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (role_id, permission_id),
        FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE,
        FOREIGN KEY (permission_id) REFERENCES permissions(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """

    products_table = """
    CREATE TABLE IF NOT EXISTS products (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        description TEXT,
        price DECIMAL(10, 2) NOT NULL,
        stock INT DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """

    refresh_tokens_table = """
    CREATE TABLE IF NOT EXISTS refresh_tokens (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL,
        token VARCHAR(500) NOT NULL,
        expires_at DATETIME NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        INDEX idx_token (token),
        INDEX idx_user_id (user_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """

    layout_table = """
    CREATE TABLE IF NOT EXISTS layout (
        id INT AUTO_INCREMENT PRIMARY KEY,
        code VARCHAR(25) NOT NULL,
        description VARCHAR(250) NOT NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """

    path_table = """
    CREATE TABLE IF NOT EXISTS path (
        id INT AUTO_INCREMENT PRIMARY KEY,
        code VARCHAR(25) NOT NULL,
        description VARCHAR(250) NOT NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """

    station_table = """
    CREATE TABLE IF NOT EXISTS station (
        id INT AUTO_INCREMENT PRIMARY KEY,
        code VARCHAR(25) NOT NULL,
        description VARCHAR(250) NOT NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """

    agv_table = """
    CREATE TABLE IF NOT EXISTS agv (
        id INT AUTO_INCREMENT PRIMARY KEY,
        code VARCHAR(25) NOT NULL,
        description VARCHAR(250) NOT NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """

    config_table = """
    CREATE TABLE IF NOT EXISTS configurations (
        id INT AUTO_INCREMENT PRIMARY KEY,

        -- Identificação
        nome VARCHAR(100) NOT NULL,
        tela VARCHAR(100) NOT NULL,
        descricao TEXT,

        -- Escopo
        escopo ENUM('GLOBAL', 'INSTANCE', 'USER') NOT NULL DEFAULT 'GLOBAL',
        instance_id VARCHAR(50) NULL,
        user_id INT NULL,

        -- Tipo e Valor
        tipo ENUM('BOOLEAN', 'INTEGER', 'FLOAT', 'STRING') NOT NULL,
        valor_string TEXT NULL,
        valor_inteiro BIGINT NULL,
        valor_real DOUBLE NULL,
        valor_booleano BOOLEAN NULL,

        -- Metadados
        editavel BOOLEAN DEFAULT TRUE,
        visivel BOOLEAN DEFAULT TRUE,
        valor_padrao TEXT NULL,

        -- Auditoria
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        criado_por VARCHAR(100),
        atualizado_por VARCHAR(100),

        -- Índices
        INDEX idx_nome (nome),
        INDEX idx_tela (tela),
        INDEX idx_escopo (escopo),
        INDEX idx_instance (instance_id),
        INDEX idx_user (user_id),
        INDEX idx_nome_tela (nome, tela),

        -- Restrições
        CONSTRAINT uq_global_config UNIQUE (nome, tela, escopo, instance_id, user_id),

        -- Garantir que apenas um valor esteja preenchido
        CONSTRAINT chk_valor CHECK (
            (tipo = 'BOOLEAN' AND valor_booleano IS NOT NULL) OR
            (tipo = 'INTEGER' AND valor_inteiro IS NOT NULL) OR
            (tipo = 'FLOAT' AND valor_real IS NOT NULL) OR
            (tipo = 'STRING' AND valor_string IS NOT NULL)
        )
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """

    # Tabela de histórico
    history_table = """
    CREATE TABLE IF NOT EXISTS configurations_history (
        id INT AUTO_INCREMENT PRIMARY KEY,
        config_id INT NOT NULL,
        nome VARCHAR(100) NOT NULL,
        tela VARCHAR(100) NOT NULL,
        escopo ENUM('GLOBAL', 'INSTANCE', 'USER') NOT NULL,
        instance_id VARCHAR(50) NULL,
        user_id INT NULL,

        -- Valores antigos e novos
        tipo ENUM('BOOLEAN', 'INTEGER', 'FLOAT', 'STRING') NOT NULL,
        valor_antigo TEXT,
        valor_novo TEXT,

        -- Auditoria
        alterado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        alterado_por VARCHAR(100),

        INDEX idx_config_id (config_id),
        INDEX idx_alterado_em (alterado_em)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """

    with DatabaseManager.get_cursor(dictionary=False) as (cursor, conn):
        try:
            cursor.execute(users_table)
            logger.info("✓ Tabela 'users' criada")

            cursor.execute(roles_table)
            logger.info("✓ Tabela 'roles' criada")

            cursor.execute(permissions_table)
            logger.info("✓ Tabela 'permissions' criada")

            cursor.execute(user_roles_table)
            logger.info("✓ Tabela 'user_roles' criada")

            cursor.execute(role_permissions_table)
            logger.info("✓ Tabela 'role_permissions' criada")

            cursor.execute(products_table)
            logger.info("✓ Tabela 'products' criada")

            cursor.execute(refresh_tokens_table)
            logger.info("✓ Tabela 'refresh_tokens' criada")

            cursor.execute(layout_table)
            logger.info("✓ Tabela 'layout_table' criada")

            cursor.execute(path_table)
            logger.info("✓ Tabela 'path_table' criada")

            cursor.execute(station_table)
            logger.info("✓ Tabela 'station_table' criada")

            cursor.execute(agv_table)
            logger.info("✓ Tabela 'agv_table' criada")

            cursor.execute(config_table)
            logger.info("✓ Tabela 'config_table' criada")

            cursor.execute(history_table)
            logger.info("✓ Tabela 'history_table' criada")

            conn.commit()
            logger.info("✓ Banco de dados inicializado com sucesso!")

        except Exception as e:
            conn.rollback()
            logger.error(f"✗ Erro ao criar tabelas: {e}")
            raise

if __name__ == "__main__":
    create_tables()
