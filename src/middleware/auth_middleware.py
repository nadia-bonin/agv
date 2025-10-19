from functools import wraps
from typing import Callable
from src.services.auth_service import AuthService
from src.utils.exceptions import InvalidCredentialsError, AuthenticationError
from src.utils.emailutils import EmailUtils

class AuthMiddleware:
    """Middleware para verificar autenticação"""

    def __init__(self):
        self.auth_service = AuthService()

    def require_auth(self, func: Callable) -> Callable:
        """
        Decorator para exigir autenticação

        Usage:
            @auth_middleware.require_auth
            def protected_function(user_id: int, **kwargs):
                ...
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Buscar token do contexto (implementação depende do framework)
            token = kwargs.get('token') or kwargs.get('access_token')

            if not token:
                raise AuthenticationError("Token não fornecido")

            try:
                # Verificar token
                payload = self.auth_service.verify_token(token)

                # Adicionar dados do usuário aos kwargs
                kwargs['user_id'] = int(payload['sub'])
                kwargs['user_email'] = payload['email']
                kwargs['user_roles'] = payload.get('roles', [])

                return func(*args, **kwargs)

            except InvalidCredentialsError:
                raise AuthenticationError("Token inválido ou expirado")

        return wrapper

# Instância global
auth_middleware = AuthMiddleware()
