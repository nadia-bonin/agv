import jwt
from datetime import datetime, timedelta
from typing import Dict, Optional
from config.settings import settings
from loguru import logger

class TokenManager:
    """Gerenciador de JWT tokens"""
    
    @staticmethod
    def create_access_token(user_id: int, email: str, roles: list = None) -> str:
        """
        Cria token de acesso JWT
        
        Args:
            user_id: ID do usuário
            email: Email do usuário
            roles: Lista de roles do usuário
            
        Returns:
            Token JWT
        """
        expire = datetime.utcnow() + timedelta(
            minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        )
        
        payload = {
            'sub': str(user_id),
            'email': email,
            'roles': roles or [],
            'type': 'access',
            'exp': expire,
            'iat': datetime.utcnow()
        }
        
        return jwt.encode(
            payload,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM
        )
    
    @staticmethod
    def create_refresh_token(user_id: int) -> str:
        """
        Cria token de refresh JWT
        
        Args:
            user_id: ID do usuário
            
        Returns:
            Refresh token JWT
        """
        expire = datetime.utcnow() + timedelta(
            days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
        )
        
        payload = {
            'sub': str(user_id),
            'type': 'refresh',
            'exp': expire,
            'iat': datetime.utcnow()
        }
        
        return jwt.encode(
            payload,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM
        )
    
    @staticmethod
    def decode_token(token: str) -> Optional[Dict]:
        """
        Decodifica e valida token JWT
        
        Args:
            token: Token JWT
            
        Returns:
            Payload do token ou None se inválido
        """
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token expirado")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Token inválido: {e}")
            return None
    
    @staticmethod
    def verify_token(token: str, token_type: str = 'access') -> Optional[Dict]:
        """
        Verifica token e seu tipo
        
        Args:
            token: Token JWT
            token_type: Tipo esperado ('access' ou 'refresh')
            
        Returns:
            Payload se válido, None caso contrário
        """
        payload = TokenManager.decode_token(token)
        
        if payload and payload.get('type') == token_type:
            return payload
        
        return None