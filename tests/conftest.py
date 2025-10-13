import pytest
from src.utils.database import DatabaseManager

@pytest.fixture(scope="session")
def db_connection():
    """Fixture de conexão com banco de testes"""
    DatabaseManager.initialize_pool()
    yield
    # Cleanup se necessário

@pytest.fixture
def sample_user_data():
    """Dados de exemplo para testes"""
    return {
        "name": "João Silva",
        "email": "joao@example.com"
    }
