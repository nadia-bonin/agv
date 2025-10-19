"""Script para popular dados iniciais"""

import sys
import os

# Adicionar o diretório raiz ao Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.auth_service import AuthService
from src.services.role_service import RoleService
from src.repositories.permission_repository import PermissionRepository
from src.repositories.user_repository import UserRepository
from src.repositories.config_repository import ConfigScope, ConfigType, ConfigManager
from loguru import logger

def seed_permissions():
    """Cria permissões básicas"""
    permission_repo = PermissionRepository()

    permissions = [
        # Users
        {'name': 'users.read', 'resource': 'users', 'action': 'read', 'description': 'Ler usuários'},
        {'name': 'users.create', 'resource': 'users', 'action': 'create', 'description': 'Criar usuários'},
        {'name': 'users.update', 'resource': 'users', 'action': 'update', 'description': 'Atualizar usuários'},
        {'name': 'users.delete', 'resource': 'users', 'action': 'delete', 'description': 'Deletar usuários'},

        # Products
        {'name': 'products.read', 'resource': 'products', 'action': 'read', 'description': 'Ler produtos'},
        {'name': 'products.create', 'resource': 'products', 'action': 'create', 'description': 'Criar produtos'},
        {'name': 'products.update', 'resource': 'products', 'action': 'update', 'description': 'Atualizar produtos'},
        {'name': 'products.delete', 'resource': 'products', 'action': 'delete', 'description': 'Deletar produtos'},

        # Roles
        {'name': 'roles.read', 'resource': 'roles', 'action': 'read', 'description': 'Ler roles'},
        {'name': 'roles.manage', 'resource': 'roles', 'action': 'manage', 'description': 'Gerenciar roles'},
    ]

    for perm in permissions:
        try:
            existing = permission_repo.find_by_name(perm['name'])
            if not existing:
                permission_repo.create(perm)
                logger.info(f"✓ Permissão criada: {perm['name']}")
            else:
                logger.info(f"○ Permissão já existe: {perm['name']}")
        except Exception as e:
            logger.error(f"✗ Erro ao criar permissão {perm['name']}: {e}")

def seed_roles():
    """Cria roles básicas"""
    role_service = RoleService()

    roles = [
        {
            'name': 'admin',
            'description': 'Administrador com acesso total',
            'permissions': [
                'users.read', 'users.create', 'users.update', 'users.delete',
                'products.read', 'products.create', 'products.update', 'products.delete',
                'roles.read', 'roles.manage'
            ]
        },
        {
            'name': 'manager',
            'description': 'Gerente com permissões elevadas',
            'permissions': [
                'users.read',
                'products.read', 'products.create', 'products.update', 'products.delete'
            ]
        },
        {
            'name': 'user',
            'description': 'Usuário comum',
            'permissions': ['users.read', 'products.read']
        }
    ]

    for role_data in roles:
        try:
            # Criar role
            role = role_service.create_role(role_data['name'], role_data['description'])
            logger.info(f"✓ Role criada: {role.name}")

            # Atribuir permissões
            for perm_name in role_data['permissions']:
                try:
                    role_service.assign_permission_to_role(role.id, perm_name)
                except Exception as e:
                    logger.warning(f"  Erro ao atribuir permissão {perm_name}: {e}")

        except Exception as e:
            logger.info(f"○ Role '{role_data['name']}' já existe")

def seed_admin_user():
    """Cria usuário administrador padrão"""
    auth_service = AuthService()
    user_repo = UserRepository()
    role_service = RoleService()

    admin_email = "admin@example.com"
    admin_password = "Admin@123"

    try:
        # Verificar se já existe
        existing = user_repo.find_by_email(admin_email)
        if existing:
            logger.info(f"○ Usuário admin já existe: {admin_email}")
            return

        # Criar admin
        result = auth_service.register(
            name="Administrador",
            email=admin_email,
            password=admin_password
        )

        # Buscar role admin
        admin_role = role_service.get_role_by_name('admin')

        # Atribuir role
        user_repo.assign_role(result['user'].id, admin_role.id)

        # Tornar superuser
        user_repo.update(result['user'].id, {'is_superuser': True})

        logger.success(f"✓ Usuário admin criado: {admin_email} / {admin_password}")

    except Exception as e:
        logger.error(f"✗ Erro ao criar admin: {e}")

def seed_configurations() :
    """Cria usuário administrador padrão"""

    initial_configs = [
        # Configurações Globais
        {
            'nome': 'app_name',
            'tela': 'GERAL',
            'descricao': 'Nome da aplicação',
            'escopo': ConfigScope.GLOBAL,
            'tipo': ConfigType.STRING,
            'valor': 'Monitor AGV',
            'criado_por': 'SYSTEM'
        },
        {
            'nome': 'max_concurrent_users',
            'tela': 'GERAL',
            'descricao': 'Número máximo de usuários simultâneos',
            'escopo': ConfigScope.GLOBAL,
            'tipo': ConfigType.INTEGER,
            'valor': 100,
            'criado_por': 'SYSTEM'
        },
        {
            'nome': 'maintenance_mode',
            'tela': 'GERAL',
            'descricao': 'Modo de manutenção ativo',
            'escopo': ConfigScope.GLOBAL,
            'tipo': ConfigType.BOOLEAN,
            'valor': False,
            'criado_por': 'SYSTEM'
        },
        # Configurações de Instância
        {
            'nome': 'server_port',
            'tela': 'SERVIDOR',
            'descricao': 'Porta do servidor',
            'escopo': ConfigScope.INSTANCE,
            'instance_id': 'server-001',
            'tipo': ConfigType.INTEGER,
            'valor': 8080,
            'criado_por': 'SYSTEM'
        },
        {
            'nome': 'enable_logging',
            'tela': 'SERVIDOR',
            'descricao': 'Habilitar logs detalhados',
            'escopo': ConfigScope.INSTANCE,
            'instance_id': 'server-001',
            'tipo': ConfigType.BOOLEAN,
            'valor': True,
            'criado_por': 'SYSTEM'
        },
        # Configurações de Usuário
        {
            'nome': 'theme',
            'tela': 'INTERFACE',
            'descricao': 'Tema da interface',
            'escopo': ConfigScope.USER,
            'user_id': 1,
            'tipo': ConfigType.STRING,
            'valor': 'dark',
            'criado_por': 'user_1'
        },
        {
            'nome': 'items_per_page',
            'tela': 'INTERFACE',
            'descricao': 'Itens por página',
            'escopo': ConfigScope.USER,
            'user_id': 1,
            'tipo': ConfigType.INTEGER,
            'valor': 25,
            'criado_por': 'user_1'
        },
        {
            'nome': 'notifications_enabled',
            'tela': 'NOTIFICACOES',
            'descricao': 'Notificações habilitadas',
            'escopo': ConfigScope.USER,
            'user_id': 1,
            'tipo': ConfigType.BOOLEAN,
            'valor': True,
            'criado_por': 'user_1'
        }
    ]

    manager = ConfigManager()

    for config in initial_configs:
        try:
            manager.set_config(
                nome=config['nome'],
                tela=config['tela'],
                valor=config['valor'],
                tipo=config['tipo'],
                escopo=config['escopo'],
                instance_id=config.get('instance_id'),
                user_id=config.get('user_id'),
                descricao=config.get('descricao'),
                criado_por=config.get('criado_por')
            )
            print(f"✓ Configuração criada: {config['nome']} ({config['escopo'].value})")
        except Exception as e:
            print(f"⚠ {config['nome']}: {e}")


def seed_all():
    """Executa todos os seeds"""
    logger.info("=== Iniciando seed de dados ===")

    seed_permissions()
    seed_roles()
    seed_admin_user()
    seed_configurations()

    logger.success("=== Seed concluído com sucesso! ===")

if __name__ == "__main__":
    seed_all()
