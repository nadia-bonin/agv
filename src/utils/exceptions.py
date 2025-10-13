class DatabaseError(Exception):
    """Erro genérico de banco de dados"""
    pass

class RecordNotFoundError(DatabaseError):
    """Registro não encontrado"""
    pass

class DuplicateRecordError(DatabaseError):
    """Registro duplicado"""
    pass

class ValidationError(Exception):
    """Erro de validação"""
    pass

# ===== Exceções de Autenticação =====

class AuthenticationError(Exception):
    """Erro de autenticação"""
    pass

class InvalidCredentialsError(AuthenticationError):
    """Credenciais inválidas"""
    pass

class TokenExpiredError(AuthenticationError):
    """Token expirado"""
    pass

class InvalidTokenError(AuthenticationError):
    """Token inválido"""
    pass

# ===== Exceções de Autorização =====

class AuthorizationError(Exception):
    """Erro de autorização"""
    pass

class PermissionDeniedError(AuthorizationError):
    """Permissão negada"""
    pass

class InsufficientPermissionsError(AuthorizationError):
    """Permissões insuficientes"""
    pass
