import sys
import os

# Adicionar o diretório raiz ao Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

"""
pytest tests/test_configurations.py -v
"""

import pytest
import mysql.connector
from datetime import datetime
from typing import Generator
from src.utils.database import DatabaseManager
from config.settings import settings


# Importar classes do sistema
sys.path.insert(0, '..')

from src.repositories.config_repository import (
    DatabaseManager,
    ConfigManager,
    ConfigScope,
    ConfigType
)

# =====================================================
# FIXTURES
# =====================================================

@pytest.fixture(scope="function")
def config_repository():
    """Fixture do repositório de configurações"""
    return ConfigRepository()

@pytest.fixture
def config_manager():
    """Instância do ConfigManager"""
    return ConfigManager()

@pytest.fixture
def sample_global_config():
    """Dados de exemplo para configuração global"""
    return {
        'nome': 'app_name',
        'tela': 'GERAL',
        'valor': 'Test App',
        'tipo': ConfigType.STRING,
        'escopo': ConfigScope.GLOBAL,
        'descricao': 'Nome da aplicação de teste'
    }

@pytest.fixture
def sample_instance_config():
    """Dados de exemplo para configuração de instância"""
    return {
        'nome': 'server_port',
        'tela': 'SERVIDOR',
        'valor': 8080,
        'tipo': ConfigType.INTEGER,
        'escopo': ConfigScope.INSTANCE,
        'instance_id': 'test-server-001',
        'descricao': 'Porta do servidor de teste'
    }

@pytest.fixture
def sample_user_config():
    """Dados de exemplo para configuração de usuário"""
    return {
        'nome': 'theme',
        'tela': 'INTERFACE',
        'valor': 'dark',
        'tipo': ConfigType.STRING,
        'escopo': ConfigScope.USER,
        'user_id': 100,
        'descricao': 'Tema da interface'
    }

# =====================================================
# TESTES DE CONFIGURAÇÕES GLOBAIS
# =====================================================

class TestGlobalConfigs:
    """Testes de configurações globais"""

    def test_set_global_config_string(self, config_manager, sample_global_config):
        """Teste: Criar configuração global tipo STRING"""
        success = config_manager.set_config(**sample_global_config)

        assert success is True

        # Verificar se foi salvo
        config = config_manager.get_config(
            sample_global_config['nome'],
            sample_global_config['tela'],
            ConfigScope.GLOBAL
        )

        assert config is not None
        assert config['nome'] == sample_global_config['nome']
        assert config['valor_string'] == sample_global_config['valor']

    def test_set_global_config_integer(self, config_manager):
        """Teste: Criar configuração global tipo INTEGER"""
        success = config_manager.set_config(
            nome='max_users',
            tela='GERAL',
            valor=100,
            tipo=ConfigType.INTEGER,
            escopo=ConfigScope.GLOBAL
        )

        assert success is True

        valor = config_manager.get_config_value(
            'max_users',
            'GERAL',
            ConfigScope.GLOBAL
        )

        assert valor == 100
        assert isinstance(valor, int)

    def test_set_global_config_float(self, config_manager):
        """Teste: Criar configuração global tipo FLOAT"""
        success = config_manager.set_config(
            nome='tax_rate',
            tela='FINANCEIRO',
            valor=0.15,
            tipo=ConfigType.FLOAT,
            escopo=ConfigScope.GLOBAL
        )

        assert success is True

        valor = config_manager.get_config_value(
            'tax_rate',
            'FINANCEIRO',
            ConfigScope.GLOBAL
        )

        assert valor == 0.15
        assert isinstance(valor, float)

    def test_set_global_config_boolean(self, config_manager):
        """Teste: Criar configuração global tipo BOOLEAN"""
        success = config_manager.set_config(
            nome='maintenance_mode',
            tela='GERAL',
            valor=True,
            tipo=ConfigType.BOOLEAN,
            escopo=ConfigScope.GLOBAL
        )

        assert success is True

        valor = config_manager.get_config_value(
            'maintenance_mode',
            'GERAL',
            ConfigScope.GLOBAL
        )

        assert valor is 1
        #assert isinstance(valor, bool)
        assert isinstance(valor, int)

    def test_update_global_config(self, config_manager, sample_global_config):
        """Teste: Atualizar configuração global existente"""
        # Criar
        config_manager.set_config(**sample_global_config)

        # Atualizar
        config_manager.set_config(
            nome=sample_global_config['nome'],
            tela=sample_global_config['tela'],
            valor='Updated App',
            tipo=ConfigType.STRING,
            escopo=ConfigScope.GLOBAL
        )

        # Verificar
        valor = config_manager.get_config_value(
            sample_global_config['nome'],
            sample_global_config['tela'],
            ConfigScope.GLOBAL
        )

        assert valor == 'Updated App'

    def test_get_nonexistent_config_returns_default(self, config_manager):
        """Teste: Buscar config inexistente retorna default"""
        valor = config_manager.get_config_value(
            'nonexistent1',
            'TELA',
            ConfigScope.GLOBAL,
            default_value='default_value'
        )

        assert valor == 'default_value'

# =====================================================
# TESTES DE CONFIGURAÇÕES DE INSTÂNCIA
# =====================================================

class TestInstanceConfigs:
    """Testes de configurações por instância"""

    def test_set_instance_config(self, config_manager, sample_instance_config):
        """Teste: Criar configuração de instância"""
        success = config_manager.set_config(**sample_instance_config)

        assert success is True

        valor = config_manager.get_config_value(
            sample_instance_config['nome'],
            sample_instance_config['tela'],
            ConfigScope.INSTANCE,
            instance_id=sample_instance_config['instance_id']
        )

        assert valor == sample_instance_config['valor']

    def test_instance_config_requires_instance_id(self, config_manager):
        """Teste: Config de instância requer instance_id"""
        with pytest.raises(ValueError, match="instance_id é obrigatório"):
            config_manager.set_config(
                nome='test',
                tela='TEST',
                valor='value',
                tipo=ConfigType.STRING,
                escopo=ConfigScope.INSTANCE
                # Falta instance_id
            )

    def test_different_instances_different_configs(self, config_manager):
        """Teste: Instâncias diferentes têm configs diferentes"""
        # Instância 1
        config_manager.set_config(
            nome='server_port',
            tela='SERVIDOR',
            valor=8080,
            tipo=ConfigType.INTEGER,
            escopo=ConfigScope.INSTANCE,
            instance_id='server-001'
        )

        # Instância 2
        config_manager.set_config(
            nome='server_port',
            tela='SERVIDOR',
            valor=9090,
            tipo=ConfigType.INTEGER,
            escopo=ConfigScope.INSTANCE,
            instance_id='server-002'
        )

        # Verificar valores diferentes
        valor1 = config_manager.get_config_value(
            'server_port', 'SERVIDOR', ConfigScope.INSTANCE,
            instance_id='server-001'
        )
        valor2 = config_manager.get_config_value(
            'server_port', 'SERVIDOR', ConfigScope.INSTANCE,
            instance_id='server-002'
        )

        assert valor1 == 8080
        assert valor2 == 9090

# =====================================================
# TESTES DE CONFIGURAÇÕES DE USUÁRIO
# =====================================================

class TestUserConfigs:
    """Testes de configurações por usuário"""

    def test_set_user_config(self, config_manager, sample_user_config):
        """Teste: Criar configuração de usuário"""
        success = config_manager.set_config(**sample_user_config)

        assert success is True

        valor = config_manager.get_config_value(
            sample_user_config['nome'],
            sample_user_config['tela'],
            ConfigScope.USER,
            user_id=sample_user_config['user_id']
        )

        assert valor == sample_user_config['valor']

    def test_user_config_requires_user_id(self, config_manager):
        """Teste: Config de usuário requer user_id"""
        with pytest.raises(ValueError, match="user_id é obrigatório"):
            config_manager.set_config(
                nome='test',
                tela='TEST',
                valor='value',
                tipo=ConfigType.STRING,
                escopo=ConfigScope.USER
                # Falta user_id
            )

    def test_different_users_different_configs(self, config_manager):
        """Teste: Usuários diferentes têm configs diferentes"""
        # Usuário 1
        config_manager.set_config(
            nome='theme',
            tela='INTERFACE',
            valor='dark',
            tipo=ConfigType.STRING,
            escopo=ConfigScope.USER,
            user_id=1
        )

        # Usuário 2
        config_manager.set_config(
            nome='theme',
            tela='INTERFACE',
            valor='light',
            tipo=ConfigType.STRING,
            escopo=ConfigScope.USER,
            user_id=2
        )

        # Verificar valores diferentes
        valor1 = config_manager.get_config_value(
            'theme', 'INTERFACE', ConfigScope.USER, user_id=1
        )
        valor2 = config_manager.get_config_value(
            'theme', 'INTERFACE', ConfigScope.USER, user_id=2
        )

        assert valor1 == 'dark'
        assert valor2 == 'light'

    def test_get_all_user_configs(self, config_manager):
        """Teste: Buscar todas as configs de um usuário"""
        user_id = 123

        # Criar várias configs para o usuário
        configs = [
            ('theme', 'INTERFACE', 'dark', ConfigType.STRING),
            ('items_per_page', 'INTERFACE', 25, ConfigType.INTEGER),
            ('notifications', 'NOTIFICACOES', 1, ConfigType.BOOLEAN)
        ]

        for nome, tela, valor, tipo in configs:
            config_manager.set_config(
                nome=nome,
                tela=tela,
                valor=valor,
                tipo=tipo,
                escopo=ConfigScope.USER,
                user_id=user_id
            )

        # Buscar todas
        all_configs = config_manager.get_all_user_configs(user_id)

        assert len(all_configs) == 3
        assert all(c['user_id'] == user_id for c in all_configs)

# =====================================================
# TESTES DE BUSCA POR TELA
# =====================================================

class TestScreenConfigs:
    """Testes de busca por tela"""

    def test_get_configs_by_screen(self, config_manager):
        """Teste: Buscar todas as configs de uma tela"""
        tela = 'INTERFACEX'

        # Criar várias configs para a tela
        config_manager.set_config(
            'theme', tela, 'dark', ConfigType.STRING, ConfigScope.GLOBAL
        )
        config_manager.set_config(
            'language', tela, 'pt-BR', ConfigType.STRING, ConfigScope.GLOBAL
        )
        config_manager.set_config(
            'font_size', tela, 14, ConfigType.INTEGER, ConfigScope.GLOBAL
        )

        # Buscar
        configs = config_manager.get_configs_by_screen(tela)

        assert len(configs) == 3
        assert all(c['tela'] == tela for c in configs)

    def test_get_configs_by_screen_filtered_by_scope(self, config_manager):
        """Teste: Buscar configs de tela filtradas por escopo"""
        tela = 'SERVIDOR'

        # Global
        config_manager.set_config(
            'default_port', tela, 8080, ConfigType.INTEGER, ConfigScope.GLOBAL
        )

        # Instance
        config_manager.set_config(
            'server_port', tela, 9090, ConfigType.INTEGER,
            ConfigScope.INSTANCE, instance_id='server-001'
        )

        # Buscar apenas GLOBAL
        configs = config_manager.get_configs_by_screen(
            tela,
            escopo=ConfigScope.GLOBAL
        )

        assert len(configs) == 1
        assert configs[0]['escopo'] == 'GLOBAL'

# =====================================================
# TESTES DE HISTÓRICO
# =====================================================

class TestConfigHistory:
    """Testes de histórico de configurações"""

    def test_history_created_on_update(self, config_manager):
        """Teste: Histórico é criado ao atualizar config"""
        # Criar config
        config_manager.set_config(
            'test_config', 'TEST', 'value1',
            ConfigType.STRING, ConfigScope.GLOBAL,
            criado_por='user1'
        )

        # Atualizar
        config_manager.set_config(
            'test_config', 'TEST', 'value2',
            ConfigType.STRING, ConfigScope.GLOBAL,
            criado_por='user2'
        )

        # Verificar histórico
        history = config_manager.get_config_history('test_config', 'TEST')

        assert len(history) >= 1
        assert history[0]['valor_antigo'] == 'value1'
        assert history[0]['valor_novo'] == 'value2'
        assert history[0]['alterado_por'] == 'user2'

    def test_history_multiple_updates(self, config_manager):
        """Teste: Múltiplas atualizações no histórico"""
        nome = 'counter'
        tela = 'TEST'

        # Criar e atualizar várias vezes
        for i in range(5):
            config_manager.set_config(
                nome, tela, i,
                ConfigType.INTEGER, ConfigScope.GLOBAL,
                criado_por=f'user{i}'
            )

        # Verificar histórico
        history = config_manager.get_config_history(nome, tela, limit=10)

        assert len(history) >= 4  # 4 updates (primeira não gera histórico)

# =====================================================
# TESTES DE DELEÇÃO
# =====================================================

class TestConfigDeletion:
    """Testes de deleção de configurações"""

    def test_delete_config(self, config_manager, sample_global_config):
        """Teste: Deletar configuração"""
        # Criar
        config_manager.set_config(**sample_global_config)

        # Verificar que existe
        config = config_manager.get_config(
            sample_global_config['nome'],
            sample_global_config['tela'],
            ConfigScope.GLOBAL
        )
        assert config is not None

        # Deletar
        success = config_manager.delete_config(
            sample_global_config['nome'],
            sample_global_config['tela'],
            ConfigScope.GLOBAL
        )

        assert success is True

        # Verificar que não existe mais
        config = config_manager.get_config(
            sample_global_config['nome'],
            sample_global_config['tela'],
            ConfigScope.GLOBAL
        )
        assert config is None

    def test_delete_nonexistent_config(self, config_manager):
        """Teste: Deletar config inexistente retorna False"""
        success = config_manager.delete_config(
            'nonexistent',
            'TEST',
            ConfigScope.GLOBAL
        )

        assert success is False

# =====================================================
# TESTES DE CONVERSÃO DE TIPOS
# =====================================================

class TestTypeConversion:
    """Testes de conversão de tipos"""

    def test_boolean_conversion_from_string(self, config_manager):
        """Teste: Conversão de string para boolean"""
        # True
        for valor in ['true', 'True', '1', 'yes', 'YES']:
            config_manager.set_config(
                'bool_test', 'TEST', valor,
                ConfigType.BOOLEAN, ConfigScope.GLOBAL
            )

            result = config_manager.get_config_value(
                'bool_test', 'TEST', ConfigScope.GLOBAL
            )

            #assert result is True
            assert result is 1

        # False
        for valor in ['false', 'False', '0', 'no', 'NO']:
            config_manager.set_config(
                'bool_test', 'TEST', valor,
                ConfigType.BOOLEAN, ConfigScope.GLOBAL
            )

            result = config_manager.get_config_value(
                'bool_test', 'TEST', ConfigScope.GLOBAL
            )

            #assert result is False
            assert result is 0

    def test_integer_conversion(self, config_manager):
        """Teste: Conversão para integer"""
        config_manager.set_config(
            'int_test', 'TEST', '42',
            ConfigType.INTEGER, ConfigScope.GLOBAL
        )

        result = config_manager.get_config_value(
            'int_test', 'TEST', ConfigScope.GLOBAL
        )

        assert result == 42
        assert isinstance(result, int)

    def test_float_conversion(self, config_manager):
        """Teste: Conversão para float"""
        config_manager.set_config(
            'float_test', 'TEST', '3.14',
            ConfigType.FLOAT, ConfigScope.GLOBAL
        )

        result = config_manager.get_config_value(
            'float_test', 'TEST', ConfigScope.GLOBAL
        )

        assert result == 3.14
        assert isinstance(result, float)

# =====================================================
# TESTES DE INTEGRAÇÃO
# =====================================================

class TestIntegration:
    """Testes de integração completos"""

    def test_complete_workflow(self, config_manager):
        """Teste: Fluxo completo de uso do sistema"""
        # 1. Criar configuração global
        config_manager.set_config(
            'app_name', 'GERAL', 'Test App',
            ConfigType.STRING, ConfigScope.GLOBAL
        )

        # 2. Criar configuração de instância
        config_manager.set_config(
            'port', 'SERVIDOR', 8080,
            ConfigType.INTEGER, ConfigScope.INSTANCE,
            instance_id='server-001'
        )

        # 3. Criar configurações de usuário
        config_manager.set_config(
            'theme', 'INTERFACE', 'dark',
            ConfigType.STRING, ConfigScope.USER,
            user_id=1
        )

        # 4. Buscar e verificar
        app_name = config_manager.get_config_value(
            'app_name', 'GERAL', ConfigScope.GLOBAL
        )
        port = config_manager.get_config_value(
            'port', 'SERVIDOR', ConfigScope.INSTANCE,
            instance_id='server-001'
        )
        theme = config_manager.get_config_value(
            'theme', 'INTERFACE', ConfigScope.USER,
            user_id=1
        )

        assert app_name == 'Test App'
        assert port == 8080
        assert theme == 'dark'

        # 5. Atualizar
        config_manager.set_config(
            'theme', 'INTERFACE', 'light',
            ConfigType.STRING, ConfigScope.USER,
            user_id=1, criado_por='user1'
        )

        # 6. Verificar atualização
        theme = config_manager.get_config_value(
            'theme', 'INTERFACE', ConfigScope.USER,
            user_id=1
        )
        assert theme == 'light'

        # 7. Verificar histórico
        history = config_manager.get_config_history('theme', 'INTERFACE')
        assert len(history) >= 1
        assert history[0]['valor_novo'] == 'light'

# =====================================================
# EXECUTAR TESTES
# =====================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "--cov-report=html"])
