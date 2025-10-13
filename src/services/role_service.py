from typing import List, Dict
from src.models.role import Role
from src.repositories.role_repository import RoleRepository
from src.repositories.permission_repository import PermissionRepository
from src.utils.exceptions import ValidationError, DuplicateRecordError, RecordNotFoundError
from loguru import logger

class RoleService:
    """Serviço de gerenciamento de roles"""
    
    def __init__(self):
        self.role_repo = RoleRepository()
        self.permission_repo = PermissionRepository()
    
    def create_role(self, name: str, description: str = None) -> Role:
        """Cria nova role"""
        # Verificar duplicidade
        existing = self.role_repo.find_by_name(name)
        if existing:
            raise DuplicateRecordError(f"Role '{name}' já existe")
        
        role_data = {
            'name': name,
            'description': description
        }
        
        role_id = self.role_repo.create(role_data)
        logger.info(f"Role criada: {name}")
        
        role_data['id'] = role_id
        return Role.from_dict(role_data)
    
    def get_role(self, role_id: int) -> Role:
        """Busca role por ID"""
        data = self.role_repo.find_by_id(role_id)
        permissions = self.role_repo.get_role_permissions(role_id)
        
        return Role.from_dict({**data, 'permissions': permissions})
    
    def get_role_by_name(self, name: str) -> Role:
        """Busca role por nome"""
        data = self.role_repo.find_by_name(name)
        if not data:
            raise RecordNotFoundError(f"Role '{name}' não encontrada")
        
        permissions = self.role_repo.get_role_permissions(data['id'])
        return Role.from_dict({**data, 'permissions': permissions})
    
    def list_roles(self) -> List[Role]:
        """Lista todas as roles"""
        roles_data = self.role_repo.find_all(limit=1000)
        roles = []
        
        for data in roles_data:
            permissions = self.role_repo.get_role_permissions(data['id'])
            roles.append(Role.from_dict({**data, 'permissions': permissions}))
        
        return roles
    
    def assign_permission_to_role(self, role_id: int, permission_name: str) -> bool:
        """Atribui permissão à role"""
        # Verificar se role existe
        self.role_repo.find_by_id(role_id)
        
        # Buscar permissão
        permission = self.permission_repo.find_by_name(permission_name)
        if not permission:
            raise RecordNotFoundError(f"Permissão '{permission_name}' não encontrada")
        
        self.role_repo.assign_permission(role_id, permission['id'])
        logger.info(f"Permissão '{permission_name}' atribuída à role ID {role_id}")
        
        return True
    
    def create_default_roles(self):
        """Cria roles padrão do sistema"""
        default_roles = [
            {
                'name': 'admin',
                'description': 'Administrador com acesso total',
                'permissions': ['*']
            },
            {
                'name': 'user',
                'description': 'Usuário comum',
                'permissions': ['users.read', 'products.read']
            },
            {
                'name': 'manager',
                'description': 'Gerente com permissões elevadas',
                'permissions': ['users.read', 'users.create', 'products.*']
            }
        ]
        
        for role_data in default_roles:
            try:
                role = self.create_role(role_data['name'], role_data['description'])
                logger.info(f"Role padrão criada: {role.name}")
            except DuplicateRecordError:
                logger.info(f"Role '{role_data['name']}' já existe")