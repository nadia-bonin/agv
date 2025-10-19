from config.settings import settings

class UserManager:
    """Gerenciador de usuário"""

    @staticmethod
    def validate_name(password: str) -> tuple[bool, str]:
        """
        Valida nome

        Returns:
            (is_valid, message)
        """
        if len(password) < settings.NAME_MIN_LENGTH:
            return False, f"Nome deve ter pelo menos {settings.NAME_MIN_LENGTH} caracteres"

        return True, "Nome inválido"
