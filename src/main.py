import sys
import os

# Adicionar o diretório raiz ao Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

"""
main.py - Função principal para testar todos os recursos do projeto
"""

import logging

from datetime import datetime
from loguru import logger
from log.log import AppLogger, UserContext, log_function_call, log_execution_time
from repositories.config_repository import ConfigManager, is_connected 

# Configurar logger
#logger.remove()
#logger = AppLogger.get_logger(__name__)
# logger.add(
#     sys.stdout,
#     format="<level>{time:YYYY-MM-DD HH:mm:ss}</level> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
#     level="INFO"
# )

from src.services.auth_service import AuthService
from src.services.user_service import UserService
from src.services.role_service import RoleService
from src.repositories.permission_repository import PermissionRepository
from src.repositories.user_repository import UserRepository
from src.utils.exceptions import (
    InvalidCredentialsError,
    PermissionDeniedError,
    ValidationError,
    DuplicateRecordError,
    RecordNotFoundError
)
from src.middleware.auth_middleware import auth_middleware
from src.middleware.permission_middleware import permission_middleware

# ===== CORES PARA OUTPUT =====
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_section(title: str):
    """Imprime uma seção"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'':^70}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{title:^70}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'':^70}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}\n")

def print_success(message: str):
    """Imprime mensagem de sucesso"""
    print(f"{Colors.OKGREEN}✓ {message}{Colors.ENDC}")

def print_error(message: str):
    """Imprime mensagem de erro"""
    print(f"{Colors.FAIL}✗ {message}{Colors.ENDC}")

def print_info(message: str):
    """Imprime mensagem informativa"""
    print(f"{Colors.OKCYAN}ℹ {message}{Colors.ENDC}")

def print_warning(message: str):
    """Imprime aviso"""
    print(f"{Colors.WARNING}⚠ {message}{Colors.ENDC}")

# ===== FUNÇÃO MAIN =====
def main():
    """Função principal - executa todos os testes"""

    processar_pedido(10)


@log_function_call(level=logging.INFO)
@log_execution_time
def processar_pedido(pedido_id: int, prioridade: str = 'normal'):
    """Processa um pedido"""
    import time
    logger.info(f"Processando pedido {pedido_id} com prioridade {prioridade}")
    time.sleep(0.5)  # Simular processamento
    return f"Pedido {pedido_id} processado"


def initialize_log():
    """Inicializa log"""

    # 1. Configurar logging
    AppLogger.setup_logging(
        log_dir='logs',
        app_name='meu_app',
        level=logging.DEBUG,
        console_output=True,
        file_output=True,
        json_output=True
    )

    # 2. Definir usuário atual
    UserContext.set_user(
        username='joao.silva',
        user_id=123,
        role='admin',
        department='TI',
        session_id='abc-123-xyz'
    )

    # 3. Obter logger
    logger = AppLogger.get_logger(__name__)

    logger.info("╔══════════════════════════════════════════════════════════════════════╗")
    logger.info("║                SISTEMA DE GERENCIAMENTO DE ROTAS DE AGV              ║")
    logger.info("║                                                                      ║")
    logger.info(f"║  Iniciado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S'):^55}║")
    logger.info("╚══════════════════════════════════════════════════════════════════════╝")

def test_configuration():
    """Exemplo de uso do sistema de configurações"""

    ConfigDatabase.seed_initial_data()

    # Usar o gerenciador
    manager = ConfigManager()

    # Exemplo 1: Configuração Global
    print("\n1. Configuração Global:")
    valor = manager.get_config_value('app_name', 'GERAL', ConfigScope.GLOBAL)
    print(f"   Nome da aplicação: {valor}")

    # Exemplo 2: Configuração de Instância
    print("\n2. Configuração de Instância:")
    valor = manager.get_config_value(
        'server_port',
        'SERVIDOR',
        ConfigScope.INSTANCE,
        instance_id='server-001'
    )
    print(f"   Porta do servidor-001: {valor}")

    # Exemplo 3: Configuração de Usuário
    print("\n3. Configuração de Usuário:")
    valor = manager.get_config_value(
        'theme',
        'INTERFACE',
        ConfigScope.USER,
        user_id=1
    )
    print(f"   Tema do usuário 1: {valor}")

    # Exemplo 4: Atualizar configuração
    print("\n4. Atualizar Configuração:")
    manager.set_config(
        nome='theme',
        tela='INTERFACE',
        valor='light',
        tipo=ConfigType.STRING,
        escopo=ConfigScope.USER,
        user_id=1,
        criado_por='user_1'
    )
    print("   Tema alterado para 'light'")

    # Exemplo 5: Buscar por tela
    print("\n5. Todas as configurações da tela INTERFACE:")
    configs = manager.get_configs_by_screen('INTERFACE')
    for config in configs:
        tipo = config['tipo']
        if tipo == 'BOOLEAN':
            valor = config['valor_booleano']
        elif tipo == 'INTEGER':
            valor = config['valor_inteiro']
        elif tipo == 'FLOAT':
            valor = config['valor_real']
        else:
            valor = config['valor_string']

        print(f"   - {config['nome']}: {valor} ({config['escopo']})")

    # Exemplo 6: Histórico
    print("\n6. Histórico da configuração 'theme':")
    history = manager.get_config_history('theme', 'INTERFACE', limit=5)
    for record in history:
        print(f"   {record['alterado_em']}: {record['valor_antigo']} → {record['valor_novo']} "
              f"(por {record['alterado_por']})")

    print("\n" + "=" * 60)
    print("✓ SISTEMA DE CONFIGURAÇÕES FUNCIONANDO")
    print("=" * 60)

if __name__ == "__main__":
    try:
        initialize_log()
        test_configuration()
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}Testes interrompidos pelo usuário{Colors.ENDC}\n")
    except Exception as e:
        print(f"\n{Colors.FAIL}Erro fatal: {e}{Colors.ENDC}\n")
        import traceback
        traceback.print_exc()
