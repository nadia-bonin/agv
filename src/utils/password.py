import bcrypt
from config.settings import settings
from loguru import logger

class PasswordManager:
    """Gerenciador de senhas com bcrypt"""

    @staticmethod
    def hash_password(password: str) -> str:
        """
        Gera hash da senha usando bcrypt

        Args:
            password: Senha em texto plano

        Returns:
            Hash da senha
        """
        salt = bcrypt.gensalt(rounds=settings.BCRYPT_ROUNDS)
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Verifica se a senha corresponde ao hash

        Args:
            plain_password: Senha em texto plano
            hashed_password: Hash armazenado

        Returns:
            True se a senha estiver correta
        """
        try:
            return bcrypt.checkpw(
                plain_password.encode('utf-8'),
                hashed_password.encode('utf-8')
            )
        except Exception as e:
            logger.error(f"Erro ao verificar senha: {e}")
            return False

    @staticmethod
    def validate_password_strength(password: str) -> tuple[bool, str]:
        """
        Valida força da senha

        Returns:
            (is_valid, message)
        """
        if len(password) < settings.PASSWORD_MIN_LENGTH:
            return False, f"Senha deve ter pelo menos {settings.PASSWORD_MIN_LENGTH} caracteres"

        if not any(c.isupper() for c in password):
            return False, "Senha deve conter pelo menos uma letra maiúscula"

        if not any(c.islower() for c in password):
            return False, "Senha deve conter pelo menos uma letra minúscula"

        if not any(c.isdigit() for c in password):
            return False, "Senha deve conter pelo menos um número"

        if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password):
            return False, "Senha deve conter pelo menos um caractere especial"

        return True, "Senha válida"
