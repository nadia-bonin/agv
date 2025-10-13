from typing import List, Optional
from src.models.user import User
from src.repositories.user_repository import UserRepository
from src.utils.exceptions import ValidationError, DuplicateRecordError
from loguru import logger

class UserService:
    """Serviço de lógica de negócio para usuários"""
    
    def __init__(self):
        self.repository = UserRepository()
    
    def create_user(self, name: str, email: str) -> User:
        """Cria novo usuário"""
        # Criar modelo e validar
        user = User(name=name, email=email)
        
        try:
            user.validate()
        except ValueError as e:
            raise ValidationError(str(e))
        
        # Verificar duplicidade
        if self.repository.email_exists(email):
            raise DuplicateRecordError(f"Email {email} já cadastrado")
        
        # Salvar
        user_id = self.repository.create(user.to_dict())
        user.id = user_id
        
        logger.info(f"Usuário criado: {user.id}")
        return user
    
    def get_user(self, user_id: int) -> User:
        """Busca usuário por ID"""
        data = self.repository.find_by_id(user_id)
        return User.from_dict(data)
    
    def list_users(self, limit: int = 100, offset: int = 0) -> List[User]:
        """Lista usuários"""
        data_list = self.repository.find_all(limit, offset)
        return [User.from_dict(data) for data in data_list]
    
    def update_user(self, user_id: int, name: Optional[str] = None, 
                    email: Optional[str] = None) -> User:
        """Atualiza usuário"""
        update_data = {}
        
        if name:
            update_data['name'] = name
        if email:
            if self.repository.email_exists(email):
                raise DuplicateRecordError(f"Email {email} já cadastrado")
            update_data['email'] = email
        
        if update_data:
            self.repository.update(user_id, update_data)
        
        return self.get_user(user_id)
    
    def delete_user(self, user_id: int) -> bool:
        """Deleta usuário"""
        return self.repository.delete(user_id)