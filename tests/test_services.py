import pytest
from src.services.user_service import UserService
from src.utils.exceptions import ValidationError, DuplicateRecordError

def test_create_user_success(db_connection, sample_user_data):
    """Testa criação de usuário com sucesso"""
    service = UserService()
    user = service.create_user(**sample_user_data)
    
    assert user.id is not None
    assert user.name == sample_user_data['name']
    assert user.email == sample_user_data['email']

def test_create_user_invalid_email(db_connection):
    """Testa criação com email inválido"""
    service = UserService()
    
    with pytest.raises(ValidationError):
        service.create_user(name="Test", email="invalid")
