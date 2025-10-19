from typing import Dict, Tuple
from src.models.user import User
from src.repositories.user_repository import UserRepository
from src.utils.password import PasswordManager
from src.utils.user import UserManager
from src.utils.token import TokenManager
from src.utils.emailutils import EmailUtils
from config.settings import settings

from src.utils.exceptions import (
    InvalidCredentialsError,
    ValidationError,
    DuplicateRecordError,
    RecordNotFoundError
)
from loguru import logger

class AuthService:
    """Serviço de autenticação"""

    def __init__(self):
        self.user_repo = UserRepository()
        self.password_manager = PasswordManager()
        self.token_manager = TokenManager()
        self.user_manager = UserManager()
        self.email_utils = EmailUtils()

    def register(self, name: str, email: str, password: str) -> Dict:
        """
        Registra novo usuário

        Returns:
            Dict com user e tokens
        """

        # Validar nome
        is_valid, message = self.user_manager.validate_name(name)
        if not is_valid:
            raise ValidationError(f"Nome deve ter pelo menos {settings.NAME_MIN_LENGTH} caracteres")

        # Validar senha
        is_valid, message = self.password_manager.validate_password_strength(password)
        if not is_valid:
            raise ValidationError(message)

        # Validar email
        if not self.email_utils.is_valid_email_regex(email):
            raise ValidationError("Email inválido")

        # Verificar email duplicado
        if self.user_repo.email_exists(email):
            raise DuplicateRecordError("Email já cadastrado")

        # Criar usuário
        password_hash = self.password_manager.hash_password(password)
        user_data = {
            'name': name,
            'email': email,
            'password_hash': password_hash,
            'is_active': True,
            'is_superuser': False
        }

        user_id = self.user_repo.create(user_data)

        # Buscar usuário completo com roles
        user_data = self.user_repo.find_by_id(user_id)
        roles = self.user_repo.get_user_roles(user_id)

        # Gerar tokens
        access_token = self.token_manager.create_access_token(
            user_id, email, roles
        )
        refresh_token = self.token_manager.create_refresh_token(user_id)

        logger.info(f"Usuário registrado: {email}")

        return {
            'user': User.from_dict({**user_data, 'roles': roles}),
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'bearer'
        }

    def login(self, email: str, password: str) -> Dict:
        """
        Autentica usuário

        Returns:
            Dict com user e tokens
        """
        # Buscar usuário
        user_data = self.user_repo.find_by_email(email)

        if not user_data:
            raise InvalidCredentialsError("Email ou senha inválidos")

        # Verificar senha
        if not self.password_manager.verify_password(password, user_data['password_hash']):
            raise InvalidCredentialsError("Email ou senha inválidos")

        # Verificar se está ativo
        if not user_data.get('is_active', True):
            raise InvalidCredentialsError("Usuário inativo")

        # Buscar roles
        roles = self.user_repo.get_user_roles(user_data['id'])

        # Gerar tokens
        access_token = self.token_manager.create_access_token(
            user_data['id'], email, roles
        )
        refresh_token = self.token_manager.create_refresh_token(user_data['id'])

        logger.info(f"Login realizado: {email}")

        return {
            'user': User.from_dict({**user_data, 'roles': roles}),
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'bearer'
        }

    def refresh_access_token(self, refresh_token: str) -> Dict:
        """
        Renova access token usando refresh token

        Returns:
            Dict com novo access_token
        """
        payload = self.token_manager.verify_token(refresh_token, 'refresh')

        if not payload:
            raise InvalidCredentialsError("Refresh token inválido ou expirado")

        user_id = int(payload['sub'])

        # Buscar usuário
        user_data = self.user_repo.find_by_id(user_id)
        roles = self.user_repo.get_user_roles(user_id)

        # Gerar novo access token
        access_token = self.token_manager.create_access_token(
            user_id, user_data['email'], roles
        )

        return {
            'access_token': access_token,
            'token_type': 'bearer'
        }

    def change_password(self, user_id: int, old_password: str, new_password: str) -> bool:
        """Altera senha do usuário"""
        # Buscar usuário
        user_data = self.user_repo.find_by_id(user_id)

        # Verificar senha antiga
        if not self.password_manager.verify_password(old_password, user_data['password_hash']):
            raise InvalidCredentialsError("Senha atual incorreta")

        # Validar nova senha
        is_valid, message = self.password_manager.validate_password_strength(new_password)
        if not is_valid:
            raise ValidationError(message)

        # Atualizar senha
        new_hash = self.password_manager.hash_password(new_password)
        self.user_repo.update(user_id, {'password_hash': new_hash})

        logger.info(f"Senha alterada para usuário ID: {user_id}")
        return True

    def verify_token(self, token: str) -> Dict:
        """Verifica e retorna dados do token"""
        payload = self.token_manager.verify_token(token, 'access')

        if not payload:
            raise InvalidCredentialsError("Token inválido ou expirado")

        return payload
