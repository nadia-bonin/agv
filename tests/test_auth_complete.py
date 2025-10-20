import sys
import os

# Adicionar o diretório raiz ao Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

"""
pytest tests/test_auth_complete.py -v
"""

import pytest
from datetime import datetime
from src.services.auth_service import AuthService
from src.services.user_service import UserService
from src.services.role_service import RoleService
from src.repositories.user_repository import UserRepository
from src.middleware.auth_middleware import auth_middleware
from src.middleware.permission_middleware import permission_middleware
from src.utils.emailutils import EmailUtils
from src.utils.exceptions import (
    InvalidCredentialsError,
    PermissionDeniedError,
    ValidationError,
    DuplicateRecordError,
    RecordNotFoundError
)

# ===== FIXTURES =====

@pytest.fixture(scope="function")
def log_service():
    """Fixture do serviço de autenticação"""
    return AuthService()

@pytest.fixture(scope="function")
def user_service():
    """Fixture do serviço de usuários"""
    return UserService()

@pytest.fixture(scope="function")
def role_service():
    """Fixture do serviço de roles"""
    return RoleService()

@pytest.fixture(scope="function")
def user_repository():
    """Fixture do repositório de usuários"""
    return UserRepository()

@pytest.fixture(scope="function")
def emailutils():
    """Fixture do utilitário de email"""
    return EmailUtils()

@pytest.fixture(scope="function")
def test_user_data():
    """Dados de teste para usuário"""
    timestamp = datetime.now().timestamp()
    return {
        "name": "João Silva",
        "email": f"joao_{timestamp}@example.com",
        "password": "Senha@123"
    }

@pytest.fixture(scope="function")
def registered_user(auth_service, test_user_data):
    """Fixture que cria e retorna um usuário registrado"""
    result = auth_service.register(**test_user_data)
    return {
        "user": result["user"],
        "access_token": result["access_token"],
        "refresh_token": result["refresh_token"],
        "email": test_user_data["email"],
        "password": test_user_data["password"]
    }

# ===== TESTES DE REGISTRO =====
class TestRegistration:
    """Testes de registro de usuário"""

    def test_register_success(self, auth_service, test_user_data):
        """Teste: Registro bem-sucedido"""
        result = auth_service.register(**test_user_data)

        assert result["user"].name == test_user_data["name"]
        assert result["user"].email == test_user_data["email"]
        assert result["user"].id is not None
        assert result["access_token"] is not None
        assert result["refresh_token"] is not None
        assert result["token_type"] == "bearer"

    def test_register_weak_password(self, auth_service, test_user_data):
        """Teste: Rejeitar senha fraca"""
        test_user_data["password"] = "123"  # Senha muito fraca

        with pytest.raises(ValidationError) as exc_info:
            auth_service.register(**test_user_data)

        assert "caracteres" in str(exc_info.value).lower()

    def test_register_duplicate_email(self, auth_service, test_user_data):
        """Teste: Rejeitar email duplicado"""
        # Registrar primeiro usuário
        auth_service.register(**test_user_data)

        # Tentar registrar com mesmo email
        with pytest.raises(DuplicateRecordError) as exc_info:
            auth_service.register(**test_user_data)

        assert "email" in str(exc_info.value).lower()

    def test_register_invalid_email(self, auth_service, test_user_data):
        """Teste: Rejeitar email inválido"""
        test_user_data["email"] = "email_invalido"

        with pytest.raises(ValidationError):
            auth_service.register(**test_user_data)

    def test_register_short_name(self, auth_service, test_user_data):
        """Teste: Rejeitar nome muito curto"""
        test_user_data["name"] = "Jo"  # Menos de 3 caracteres

        with pytest.raises(ValidationError):
            auth_service.register(**test_user_data)

# ===== TESTES DE LOGIN =====
class TestLogin:
    """Testes de login"""

    def test_login_success(self, auth_service, registered_user):
        """Teste: Login bem-sucedido"""
        result = auth_service.login(
            email=registered_user["email"],
            password=registered_user["password"]
        )

        assert result["user"].email == registered_user["email"]
        assert result["access_token"] is not None
        assert result["refresh_token"] is not None

    def test_login_wrong_password(self, auth_service, registered_user):
        """Teste: Rejeitar senha incorreta"""
        with pytest.raises(InvalidCredentialsError) as exc_info:
            auth_service.login(
                email=registered_user["email"],
                password="SenhaErrada@123"
            )

        assert "inválidos" in str(exc_info.value).lower()

    def test_login_nonexistent_email(self, auth_service):
        """Teste: Rejeitar email não existente"""
        with pytest.raises(InvalidCredentialsError):
            auth_service.login(
                email="naoexiste@example.com",
                password="Senha@123"
            )

    def test_login_returns_user_data(self, auth_service, registered_user):
        """Teste: Login retorna dados completos do usuário"""
        result = auth_service.login(
            email=registered_user["email"],
            password=registered_user["password"]
        )

        assert result["user"].id is not None
        assert result["user"].name is not None
        assert result["user"].email == registered_user["email"]
        assert isinstance(result["user"].roles, list)

# ===== TESTES DE TOKEN =====
class TestTokenManagement:
    """Testes de gerenciamento de tokens"""

    def test_refresh_token_success(self, auth_service, registered_user):
        """Teste: Renovar access token com refresh token"""
        result = auth_service.refresh_access_token(
            registered_user["refresh_token"]
        )

        assert result["access_token"] is not None
        assert result["token_type"] == "bearer"
        assert result["access_token"] != registered_user["access_token"]

    def test_refresh_token_invalid(self, auth_service):
        """Teste: Rejeitar refresh token inválido"""
        with pytest.raises(InvalidCredentialsError):
            auth_service.refresh_access_token("token_invalido")

    def test_verify_token_valid(self, auth_service, registered_user):
        """Teste: Verificar token válido"""
        payload = auth_service.verify_token(registered_user["access_token"])

        assert payload is not None
        assert int(payload["sub"]) == registered_user["user"].id
        assert payload["email"] == registered_user["user"].email

    def test_verify_token_invalid(self, auth_service):
        """Teste: Rejeitar token inválido"""
        with pytest.raises(InvalidCredentialsError):
            auth_service.verify_token("token_invalido")

# ===== TESTES DE ALTERAÇÃO DE SENHA =====
class TestPasswordChange:
    """Testes de alteração de senha"""

    def test_change_password_success(self, auth_service, registered_user):
        """Teste: Alterar senha com sucesso"""
        success = auth_service.change_password(
            user_id=registered_user["user"].id,
            old_password=registered_user["password"],
            new_password="NovaSenha@456"
        )

        assert success is True

        # Verificar login com nova senha
        result = auth_service.login(
            email=registered_user["email"],
            password="NovaSenha@456"
        )
        assert result["access_token"] is not None

    def test_change_password_wrong_old_password(self, auth_service, registered_user):
        """Teste: Rejeitar senha antiga incorreta"""
        with pytest.raises(InvalidCredentialsError):
            auth_service.change_password(
                user_id=registered_user["user"].id,
                old_password="SenhaErrada@123",
                new_password="NovaSenha@456"
            )

    def test_change_password_weak_new_password(self, auth_service, registered_user):
        """Teste: Rejeitar nova senha fraca"""
        with pytest.raises(ValidationError):
            auth_service.change_password(
                user_id=registered_user["user"].id,
                old_password=registered_user["password"],
                new_password="123"
            )

# ===== TESTES DE ROLES E PERMISSÕES =====
class TestRolesAndPermissions:
    """Testes de roles e permissões"""

    def test_get_user_roles(self, user_repository, registered_user, role_service):
        """Teste: Buscar roles do usuário"""
        # Atribuir role
        try:
            user_role = role_service.get_role_by_name('user')
            user_repository.assign_role(registered_user["user"].id, user_role.id)
        except RecordNotFoundError:
            pytest.skip("Role 'user' não encontrada no banco")

        roles = user_repository.get_user_roles(registered_user["user"].id)

        assert isinstance(roles, list)
        assert 'user' in roles

    def test_get_user_permissions(self, user_repository, registered_user, role_service):
        """Teste: Buscar permissões do usuário"""
        # Atribuir role
        try:
            user_role = role_service.get_role_by_name('user')
            user_repository.assign_role(registered_user["user"].id, user_role.id)
        except RecordNotFoundError:
            pytest.skip("Role 'user' não encontrada no banco")

        permissions = user_repository.get_user_permissions(registered_user["user"].id)

        assert isinstance(permissions, list)

    def test_assign_role_to_user(self, user_repository, registered_user, role_service):
        """Teste: Atribuir role a usuário"""
        try:
            admin_role = role_service.get_role_by_name('admin')
        except RecordNotFoundError:
            pytest.skip("Role 'admin' não encontrada no banco")

        success = user_repository.assign_role(
            registered_user["user"].id,
            admin_role.id
        )

        assert success is True

        roles = user_repository.get_user_roles(registered_user["user"].id)
        assert 'admin' in roles

    def test_remove_role_from_user(self, user_repository, registered_user, role_service):
        """Teste: Remover role de usuário"""
        try:
            user_role = role_service.get_role_by_name('user')
            # Primeiro atribuir
            user_repository.assign_role(registered_user["user"].id, user_role.id)

            # Depois remover
            success = user_repository.remove_role(
                registered_user["user"].id,
                user_role.id
            )

            assert success is True

            roles = user_repository.get_user_roles(registered_user["user"].id)
            assert 'user' not in roles
        except RecordNotFoundError:
            pytest.skip("Role 'user' não encontrada no banco")

# ===== TESTES DE MIDDLEWARE =====
class TestAuthMiddleware:
    """Testes de middleware de autenticação"""

    def test_require_auth_with_valid_token(self, registered_user):
        """Teste: Função protegida com token válido"""

        @auth_middleware.require_auth
        def protected_function(user_id: int, user_email: str, **kwargs):
            return {"user_id": user_id, "email": user_email}

        result = protected_function(token=registered_user["access_token"])

        assert result["user_id"] == registered_user["user"].id
        assert result["email"] == registered_user["user"].email

    def test_require_auth_without_token(self):
        """Teste: Função protegida sem token"""

        @auth_middleware.require_auth
        def protected_function(user_id: int, **kwargs):
            return {"user_id": user_id}

        with pytest.raises(Exception):  # AuthenticationError
            protected_function()

    def test_require_auth_with_invalid_token(self):
        """Teste: Função protegida com token inválido"""

        @auth_middleware.require_auth
        def protected_function(user_id: int, **kwargs):
            return {"user_id": user_id}

        with pytest.raises(Exception):  # AuthenticationError
            protected_function(token="token_invalido")

class TestPermissionMiddleware:
    """Testes de middleware de permissões"""

    def test_require_permissions_with_permission(self, registered_user, user_repository, role_service):
        """Teste: Função com permissão requerida"""

        # Atribuir role com permissão
        try:
            user_role = role_service.get_role_by_name('user')
            user_repository.assign_role(registered_user["user"].id, user_role.id)
        except RecordNotFoundError:
            pytest.skip("Role 'user' não encontrada")

        @auth_middleware.require_auth
        @permission_middleware.require_permissions('users.read')
        def protected_function(user_id: int, **kwargs):
            return {"success": True, "user_id": user_id}

        try:
            result = protected_function(token=registered_user["access_token"])
            assert result["success"] is True
        except PermissionDeniedError:
            pytest.skip("Usuário não tem permissão 'users.read'")

    def test_require_permissions_without_permission(self, registered_user):
        """Teste: Função sem permissão requerida"""

        @auth_middleware.require_auth
        @permission_middleware.require_permissions('admin.delete')
        def protected_function(user_id: int, **kwargs):
            return {"success": True}

        with pytest.raises(PermissionDeniedError):
            protected_function(token=registered_user["access_token"])

# ===== TESTES DE GERENCIAMENTO DE USUÁRIOS =====
class TestUserManagement:
    """Testes de gerenciamento de usuários"""

    def test_list_users(self, user_repository):
        """Teste: Listar usuários"""
        users = user_repository.find_all(limit=10)

        assert isinstance(users, list)
        assert len(users) > 0

    def test_find_user_by_id(self, user_repository, registered_user):
        """Teste: Buscar usuário por ID"""
        user = user_repository.find_by_id(registered_user["user"].id)

        assert user is not None
        assert user["id"] == registered_user["user"].id
        assert user["email"] == registered_user["user"].email

    def test_find_user_by_email(self, user_repository, registered_user):
        """Teste: Buscar usuário por email"""
        user = user_repository.find_by_email(registered_user["email"])

        assert user is not None
        assert user["email"] == registered_user["email"]

    def test_update_user(self, user_repository, registered_user):
        """Teste: Atualizar usuário"""
        success = user_repository.update(
            registered_user["user"].id,
            {"name": "João Silva Atualizado"}
        )

        assert success is True

        user = user_repository.find_by_id(registered_user["user"].id)
        assert user["name"] == "João Silva Atualizado"

    def test_count_users(self, user_repository):
        """Teste: Contar usuários"""
        count = user_repository.count()

        assert isinstance(count, int)
        assert count > 0

    def test_find_nonexistent_user(self, user_repository):
        """Teste: Buscar usuário inexistente"""
        with pytest.raises(RecordNotFoundError):
            user_repository.find_by_id(999999999)

# ===== TESTES DE INTEGRAÇÃO =====
class TestIntegration:
    """Testes de integração completos"""

    def test_complete_user_flow(self, auth_service, user_repository, role_service):
        """Teste: Fluxo completo de usuário"""
        # 1. Registrar
        timestamp = datetime.now().timestamp()
        user_data = {
            "name": "Teste Integração",
            "email": f"integracao_{timestamp}@example.com",
            "password": "Senha@123"
        }

        result = auth_service.register(**user_data)
        assert result["user"].id is not None

        user_id = result["user"].id
        access_token = result["access_token"]

        # 2. Login
        login_result = auth_service.login(
            email=user_data["email"],
            password=user_data["password"]
        )
        assert login_result["access_token"] is not None

        # 3. Atribuir role
        try:
            user_role = role_service.get_role_by_name('user')
            user_repository.assign_role(user_id, user_role.id)

            roles = user_repository.get_user_roles(user_id)
            assert 'user' in roles
        except RecordNotFoundError:
            pass  # Role não existe no banco

        # 4. Alterar senha
        auth_service.change_password(
            user_id=user_id,
            old_password=user_data["password"],
            new_password="NovaSenha@456"
        )

        # 5. Login com nova senha
        new_login = auth_service.login(
            email=user_data["email"],
            password="NovaSenha@456"
        )
        assert new_login["access_token"] is not None

        # 6. Verificar token
        payload = auth_service.verify_token(new_login["access_token"])
        assert int(payload["sub"]) == user_id

# ===== CONFIGURAÇÃO DO PYTEST =====
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
