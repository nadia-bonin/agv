import re
from email.utils import parseaddr

class EmailUtils:

    # Tenta importar a lib email-validator, mas não é obrigatória
    try:
        from email_validator import validate_email, EmailNotValidError
        HAS_EMAIL_VALIDATOR = True
    except ImportError:
        HAS_EMAIL_VALIDATOR = False

    # --- 1) Regex simples ----------------------------------------------
    #EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")

    @staticmethod
    def is_valid_email_regex(email: str) -> bool:
        """Valida e-mail com regex simples (sem dependências externas)."""
        if not isinstance(email, str):
            return False
        email = email.strip()
        return bool(re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$").match(email))

    # --- 2) Usando email.utils.parseaddr -------------------------------
    @staticmethod
    def is_valid_email_parseaddr(email: str) -> bool:
        """Valida e-mail usando parseaddr (aceita 'Nome <email@dominio>')."""
        if not isinstance(email, str):
            return False
        _, addr = parseaddr(email)
        if not addr:
            return False
        return bool(re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$").match(addr))

    # --- 3) Usando biblioteca email-validator ---------------------------
    @staticmethod
    def is_valid_email_emailvalidator(email: str) -> bool:
        """Valida e normaliza o e-mail com a lib 'email-validator'."""
        if not HAS_EMAIL_VALIDATOR:
            raise RuntimeError(
                "A biblioteca 'email-validator' não está instalada. "
                "Execute: pip install email-validator"
            )
        try:
            validate_email(email, check_deliverability=False)
            return True
        except EmailNotValidError:
            return False
