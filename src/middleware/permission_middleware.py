from functools import wraps
from typing import Callable, List
from src.repositories.user_repository import UserRepository
from src.utils.exceptions import PermissionDeniedError

class PermissionMiddleware:
    """Middleware para verificar permissões"""
    
    def __init__(self):
        self.user_repo = UserRepository()
    
    def require_permissions(self, *required_permissions: str):
        """
        Decorator para exigir permissões específicas
        
        Usage:
            @permission_middleware.require_permissions('users.create', 'users.edit')
            def create_user(user_id: int, **kwargs):
                ...
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                user_id = kwargs.get('user_id')
                
                if not user_id:
                    raise PermissionDeniedError("Usuário não autenticado")
                
                # Buscar permissões do usuário
                user_permissions = self.user_repo.get_user_permissions(user_id)
                
                # Verificar se tem todas as permissões necessárias
                missing_permissions = set(required_permissions) - set(user_permissions)
                
                if missing_permissions:
                    raise PermissionDeniedError(
                        f"Permissões necessárias: {', '.join(missing_permissions)}"
                    )
                
                return func(*args, **kwargs)
            
            return wrapper
        return decorator
    
    def require_roles(self, *required_roles: str):
        """
        Decorator para exigir roles específicas
        
        Usage:
            @permission_middleware.require_roles('admin', 'manager')
            def admin_function(user_id: int, **kwargs):
                ...
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                user_id = kwargs.get('user_id')
                user_roles = kwargs.get('user_roles', [])
                
                if not user_id:
                    raise PermissionDeniedError("Usuário não autenticado")
                
                # Verificar se tem pelo menos uma das roles necessárias
                if not any(role in user_roles for role in required_roles):
                    raise PermissionDeniedError(
                        f"Roles necessárias: {', '.join(required_roles)}"
                    )
                
                return func(*args, **kwargs)
            
            return wrapper
        return decorator
    
    def require_superuser(self, func: Callable) -> Callable:
        """
        Decorator para exigir superusuário
        
        Usage:
            @permission_middleware.require_superuser
            def admin_only_function(user_id: int, **kwargs):
                ...
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            user_id = kwargs.get('user_id')
            
            if not user_id:
                raise PermissionDeniedError("Usuário não autenticado")
            
            # Buscar usuário
            user_data = self.user_repo.find_by_id(user_id)
            
            if not user_data.get('is_superuser', False):
                raise PermissionDeniedError("Acesso restrito a superusuários")
            
            return func(*args, **kwargs)
        
        return wrapper

# Instância global
permission_middleware = PermissionMiddleware()
