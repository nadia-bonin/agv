import sys
import os

# Adicionar o diretório raiz ao Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

"""
pytest tests/test_logging_system.py -v --cov=logging_system
"""

import pytest
import logging
import json
import os
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
import threading
import time

# Importar classes do sistema
import sys
sys.path.insert(0, '..')

from src.log.log import (
    UserContext,
    UserContextFilter,
    DetailedFormatter,
    JSONFormatter,
    ColoredFormatter,
    AppLogger,
    log_function_call,
    log_execution_time,
    LoggedOperation
)

# =====================================================
# FIXTURES
# =====================================================

@pytest.fixture(scope="function")
def temp_log_dir():
    """Diretório temporário para logs"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)

@pytest.fixture(scope="function")
def clean_logger():
    """Limpa configuração de loggers entre testes"""
    # Limpar handlers do root logger
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        handler.close()
        root_logger.removeHandler(handler)

    # Resetar nível
    root_logger.setLevel(logging.WARNING)

    # Resetar flag de configuração
    AppLogger._configured = False

    yield

    # Cleanup final
    for handler in root_logger.handlers[:]:
        handler.close()
        root_logger.removeHandler(handler)

@pytest.fixture(scope="function")
def clear_user_context():
    """Limpa contexto de usuário entre testes"""
    UserContext.clear_user()
    yield
    UserContext.clear_user()

@pytest.fixture
def sample_user():
    """Dados de exemplo de usuário"""
    return {
        'username': 'test_user',
        'user_id': 123,
        'role': 'admin',
        'department': 'TI',
        'session_id': 'test-session-123'
    }

# =====================================================
# TESTES DE CONTEXTO DE USUÁRIO
# =====================================================

class TestUserContext:
    """Testes do contexto de usuário"""

    def test_set_user_basic(self, clear_user_context, sample_user):
        """Teste: Definir usuário básico"""
        UserContext.set_user(
            username=sample_user['username'],
            user_id=sample_user['user_id']
        )

        assert UserContext.get_user() == sample_user['username']
        assert UserContext.get_user_id() == sample_user['user_id']

    def test_set_user_with_extra_info(self, clear_user_context, sample_user):
        """Teste: Definir usuário com informações extras"""
        UserContext.set_user(**sample_user)

        assert UserContext.get_user() == sample_user['username']
        assert UserContext.get_user_id() == sample_user['user_id']

        extra_info = UserContext.get_extra_info()
        assert extra_info['role'] == sample_user['role']
        assert extra_info['department'] == sample_user['department']
        assert extra_info['session_id'] == sample_user['session_id']

    def test_get_user_without_context(self, clear_user_context):
        """Teste: Obter usuário sem contexto retorna SYSTEM"""
        assert UserContext.get_user() == 'SYSTEM'
        assert UserContext.get_user_id() is None
        assert UserContext.get_extra_info() == {}

    def test_clear_user(self, clear_user_context, sample_user):
        """Teste: Limpar contexto de usuário"""
        UserContext.set_user(**sample_user)
        assert UserContext.get_user() == sample_user['username']

        UserContext.clear_user()
        assert UserContext.get_user() == 'SYSTEM'
        assert UserContext.get_user_id() is None

    def test_user_context_thread_local(self, clear_user_context):
        """Teste: Contexto de usuário é thread-local"""
        results = {}

        def thread_func(thread_id, username):
            UserContext.set_user(username=username, user_id=thread_id)
            time.sleep(0.1)  # Simular trabalho
            results[thread_id] = UserContext.get_user()

        threads = []
        for i in range(3):
            thread = threading.Thread(
                target=thread_func,
                args=(i, f'user_{i}')
            )
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Cada thread deve ter seu próprio contexto
        assert results[0] == 'user_0'
        assert results[1] == 'user_1'
        assert results[2] == 'user_2'

# =====================================================
# TESTES DE FILTROS
# =====================================================

class TestUserContextFilter:
    """Testes do filtro de contexto"""

    def test_filter_adds_user_info(self, clear_user_context, sample_user):
        """Teste: Filtro adiciona informações do usuário"""
        UserContext.set_user(**sample_user)

        # Criar log record
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='test.py',
            lineno=1,
            msg='Test message',
            args=(),
            exc_info=None
        )

        # Aplicar filtro
        filter = UserContextFilter()
        filter.filter(record)

        # Verificar campos adicionados
        assert record.username == sample_user['username']
        assert record.user_id == sample_user['user_id']
        assert record.user_role == sample_user['role']
        assert record.user_department == sample_user['department']
        assert record.session_id == sample_user['session_id']

    def test_filter_without_user_context(self, clear_user_context):
        """Teste: Filtro sem contexto usa valores padrão"""
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='test.py',
            lineno=1,
            msg='Test message',
            args=(),
            exc_info=None
        )

        filter = UserContextFilter()
        filter.filter(record)

        assert record.username == 'SYSTEM'
        assert record.user_id == 'N/A'
        assert record.user_role == 'N/A'

# =====================================================
# TESTES DE FORMATTERS
# =====================================================

class TestDetailedFormatter:
    """Testes do formatter detalhado"""

    def test_format_includes_all_fields(self, clear_user_context, sample_user):
        """Teste: Formato inclui todos os campos"""
        UserContext.set_user(**sample_user)

        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='test.py',
            lineno=42,
            msg='Test message',
            args=(),
            exc_info=None,
            func='test_function'
        )

        # Aplicar filtro primeiro
        filter = UserContextFilter()
        filter.filter(record)

        # Formatar
        formatter = DetailedFormatter()
        formatted = formatter.format(record)

        # Verificar conteúdo
        assert sample_user['username'] in formatted
        assert str(sample_user['user_id']) in formatted
        assert 'test' in formatted
        assert 'test_function' in formatted
        assert '42' in formatted
        assert 'Test message' in formatted

class TestJSONFormatter:
    """Testes do formatter JSON"""

    def test_json_format_valid(self, clear_user_context, sample_user):
        """Teste: Formato JSON válido"""
        UserContext.set_user(**sample_user)

        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='/path/to/test.py',
            lineno=42,
            msg='Test message',
            args=(),
            exc_info=None,
            func='test_function'
        )

        filter = UserContextFilter()
        filter.filter(record)

        formatter = JSONFormatter()
        formatted = formatter.format(record)

        # Verificar que é JSON válido
        log_data = json.loads(formatted)

        assert log_data['level'] == 'INFO'
        assert log_data['user']['username'] == sample_user['username']
        assert log_data['user']['user_id'] == sample_user['user_id']
        assert log_data['code']['module'] == 'test'
        assert log_data['code']['function'] == 'test_function'
        assert log_data['code']['line'] == 42
        assert log_data['message'] == 'Test message'

    def test_json_format_with_exception(self, clear_user_context):
        """Teste: JSON com informação de exceção"""
        try:
            raise ValueError("Test error")
        except ValueError:
            exc_info = sys.exc_info()

        record = logging.LogRecord(
            name='test',
            level=logging.ERROR,
            pathname='test.py',
            lineno=1,
            msg='Error occurred',
            args=(),
            exc_info=exc_info,
            func='test_func'
        )

        filter = UserContextFilter()
        filter.filter(record)

        formatter = JSONFormatter()
        formatted = formatter.format(record)

        log_data = json.loads(formatted)

        assert 'exception' in log_data
        assert 'ValueError' in log_data['exception']
        assert 'Test error' in log_data['exception']

class TestColoredFormatter:
    """Testes do formatter com cores"""

    def test_colored_format_has_ansi_codes(self, clear_user_context):
        """Teste: Formato colorido contém códigos ANSI"""
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='test.py',
            lineno=1,
            msg='Test message',
            args=(),
            exc_info=None,
            func='test_func'
        )

        filter = UserContextFilter()
        filter.filter(record)

        formatter = ColoredFormatter()
        formatted = formatter.format(record)

        # Verificar presença de códigos ANSI (cores)
        assert '\033[' in formatted  # Código ANSI presente

    def test_colored_format_different_levels(self, clear_user_context):
        """Teste: Diferentes níveis têm cores diferentes"""
        levels = [
            logging.DEBUG,
            logging.INFO,
            logging.WARNING,
            logging.ERROR,
            logging.CRITICAL
        ]

        formatter = ColoredFormatter()
        filter = UserContextFilter()
        formatted_messages = []

        for level in levels:
            record = logging.LogRecord(
                name='test',
                level=level,
                pathname='test.py',
                lineno=1,
                msg='Test',
                args=(),
                exc_info=None,
                func='test'
            )
            filter.filter(record)
            formatted_messages.append(formatter.format(record))

        # Cada nível deve ter formatação diferente
        assert len(set(formatted_messages)) == len(levels)

# =====================================================
# TESTES DE CONFIGURAÇÃO DO LOGGER
# =====================================================

class TestAppLogger:
    """Testes de configuração do AppLogger"""

    def test_setup_logging_creates_files(self, temp_log_dir, clean_logger):
        """Teste: Setup cria arquivos de log"""
        AppLogger.setup_logging(
            log_dir=temp_log_dir,
            app_name='test_app',
            level=logging.INFO,
            console_output=False,
            file_output=True,
            json_output=True
        )

        # Verificar que arquivos foram criados após primeiro log
        logger = AppLogger.get_logger(__name__)
        logger.info("Test message")

        log_files = list(Path(temp_log_dir).glob('*.log'))
        json_files = list(Path(temp_log_dir).glob('*.json'))

        assert len(log_files) >= 1  # Pelo menos um arquivo .log
        assert len(json_files) >= 1  # Pelo menos um arquivo .json

    def test_setup_logging_only_once(self, temp_log_dir, clean_logger):
        """Teste: Setup só configura uma vez"""
        AppLogger.setup_logging(log_dir=temp_log_dir)
        first_setup = AppLogger._configured

        AppLogger.setup_logging(log_dir=temp_log_dir)
        second_setup = AppLogger._configured

        assert first_setup is True
        assert second_setup is True

    def test_get_logger_returns_configured_logger(self, temp_log_dir, clean_logger):
        """Teste: get_logger retorna logger configurado"""
        AppLogger.setup_logging(log_dir=temp_log_dir)

        logger = AppLogger.get_logger('test')

        assert logger is not None
        assert isinstance(logger, logging.Logger)
        assert logger.name == 'test'

    def test_logging_levels(self, temp_log_dir, clean_logger):
        """Teste: Diferentes níveis de log funcionam"""
        AppLogger.setup_logging(
            log_dir=temp_log_dir,
            level=logging.DEBUG
        )

        logger = AppLogger.get_logger(__name__)

        # Não deve lançar exceção
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")
        logger.critical("Critical message")

# =====================================================
# TESTES DE DECORATORS
# =====================================================

class TestDecorators:
    """Testes dos decorators de logging"""

    def test_log_function_call_decorator(self, temp_log_dir, clean_logger, clear_user_context, sample_user):
        """Teste: Decorator loga entrada e saída de função"""
        AppLogger.setup_logging(
            log_dir=temp_log_dir,
            level=logging.DEBUG,
            console_output=False,
            file_output=True,
            json_output=False
            )
        UserContext.set_user(**sample_user)

        @log_function_call(level=logging.INFO)
        def test_function(x, y):
            return x + y

        result = test_function(10, 20)

        assert result == 30

        # Verificar que logs foram criados
        log_file = list(Path(temp_log_dir).glob('*.log'))[0]
        log_content = log_file.read_text(encoding='utf-8')

        assert 'test_function' in log_content
        assert 'Iniciando' in log_content
        assert 'Concluído' in log_content

    def test_log_function_call_with_exception(self, temp_log_dir, clean_logger, clear_user_context):
        """Teste: Decorator loga exceção"""
        AppLogger.setup_logging(log_dir=temp_log_dir, level=logging.DEBUG)

        @log_function_call()
        def failing_function():
            raise ValueError("Test error")

        with pytest.raises(ValueError):
            failing_function()

        # Verificar que erro foi logado
        log_file = list(Path(temp_log_dir).glob('*.log'))[0]
        log_content = log_file.read_text(encoding='utf-8')

        assert 'Erro em failing_function' in log_content
        assert 'ValueError' in log_content

    def test_log_execution_time_decorator(self, temp_log_dir, clean_logger):
        """Teste: Decorator loga tempo de execução"""
        AppLogger.setup_logging(
            log_dir=temp_log_dir,
            level=logging.INFO,
            console_output=False,
            file_output=True,
            json_output=False
            )

        @log_execution_time
        def slow_function():
            time.sleep(0.1)
            return "done"

        result = slow_function()

        assert result == "done"

        # Verificar que tempo foi logado
        log_file = list(Path(temp_log_dir).glob('*.log'))[0]
        log_content = log_file.read_text(encoding='utf-8')

        assert 'slow_function executado em' in log_content
        assert 's' in log_content  # Segundos

    def test_combined_decorators(self, temp_log_dir, clean_logger):
        """Teste: Múltiplos decorators combinados"""
        AppLogger.setup_logging(
            log_dir=temp_log_dir,
            level=logging.INFO,
            console_output=False,
            file_output=True,
            json_output=False
            )

        @log_function_call()
        @log_execution_time
        def combined_function(x):
            return x * 2

        result = combined_function(5)

        assert result == 10

        log_file = list(Path(temp_log_dir).glob('*.log'))[0]
        log_content = log_file.read_text(encoding='utf-8')

        assert 'Iniciando combined_function' in log_content
        assert 'executado em' in log_content
        assert 'Concluído combined_function' in log_content

# =====================================================
# TESTES DE CONTEXT MANAGER
# =====================================================

class TestLoggedOperation:
    """Testes do context manager LoggedOperation"""

    def test_logged_operation_success(self, temp_log_dir, clean_logger):
        """Teste: LoggedOperation loga operação bem-sucedida"""
        AppLogger.setup_logging(
            log_dir=temp_log_dir,
            level=logging.INFO,
            console_output=False,
            file_output=True,
            json_output=False
            )
        logger = AppLogger.get_logger(__name__)

        with LoggedOperation("Test Operation", logger):
            time.sleep(0.1)
            # Operação bem-sucedida
            pass

        log_file = list(Path(temp_log_dir).glob('*.log'))[0]
        log_content = log_file.read_text(encoding='utf-8')

        assert 'Iniciando operação: Test Operation' in log_content
        assert 'Operação concluída: Test Operation' in log_content

    def test_logged_operation_failure(self, temp_log_dir, clean_logger):
        """Teste: LoggedOperation loga operação falha"""
        AppLogger.setup_logging(
            log_dir=temp_log_dir,
            level=logging.INFO,
            console_output=False,
            file_output=True,
            json_output=False
        )
        logger = AppLogger.get_logger(__name__)

        with pytest.raises(ValueError):
            with LoggedOperation("Failing Operation", logger):
                raise ValueError("Test error")

        log_file = list(Path(temp_log_dir).glob('*.log'))[0]
        log_content = log_file.read_text(encoding='utf-8')

        assert 'Iniciando operação: Failing Operation' in log_content
        assert 'Operação falhou: Failing Operation' in log_content
        assert 'ValueError' in log_content

    def test_logged_operation_with_default_logger(self, temp_log_dir, clean_logger):
        """Teste: LoggedOperation com logger padrão"""
        AppLogger.setup_logging(
            log_dir=temp_log_dir,
            level=logging.INFO,
            console_output=False,
            file_output=True,
            json_output=False
            )

        with LoggedOperation("Default Logger Operation"):
            pass

        log_file = list(Path(temp_log_dir).glob('*.log'))[0]
        log_content = log_file.read_text(encoding='utf-8')

        assert 'Default Logger Operation' in log_content

# =====================================================
# TESTES DE INTEGRAÇÃO
# =====================================================

class TestIntegration:
    """Testes de integração completos"""

    def test_complete_logging_workflow(self, temp_log_dir, clean_logger, clear_user_context, sample_user):
        """Teste: Fluxo completo de logging"""
        # 1. Setup
        AppLogger.setup_logging(
            log_dir=temp_log_dir,
            app_name='integration_test',
            level=logging.DEBUG,
            console_output=False,
            file_output=True,
            json_output=True
        )

        # 2. Definir usuário
        UserContext.set_user(**sample_user)

        # 3. Obter logger
        logger = AppLogger.get_logger('integration_module')

        # 4. Logs simples
        logger.debug("Debug message")
        logger.info("User logged in")
        logger.warning("Warning message")

        # 5. Função com decorator
        @log_function_call()
        @log_execution_time
        def process_data(data_id):
            logger.info(f"Processing data {data_id}")
            return f"Processed {data_id}"

        result = process_data(123)
        assert result == "Processed 123"

        # 6. Context manager
        with LoggedOperation("Data Import", logger):
            logger.info("Importing 100 records")
            time.sleep(0.05)

        # 7. Log com exceção
        try:
            raise RuntimeError("Simulated error")
        except RuntimeError:
            logger.error("Error occurred", exc_info=True)

        # 8. Trocar usuário
        UserContext.set_user(username='another_user', user_id=456)
        logger.info("Different user action")

        # 9. Verificar arquivos criados
        log_files = list(Path(temp_log_dir).glob('*.log'))
        json_files = list(Path(temp_log_dir).glob('*.json'))

        assert len(log_files) >= 1
        assert len(json_files) >= 1

        # 10. Verificar conteúdo
        log_file = [f for f in log_files if 'integration_test' in f.name][0]
        log_content = log_file.read_text(encoding='utf-8')

        # Verificar presença de elementos chave
        assert sample_user['username'] in log_content
        assert 'User logged in' in log_content
        assert 'process_data' in log_content
        assert 'Data Import' in log_content
        assert 'RuntimeError' in log_content
        assert 'another_user' in log_content

        # 11. Verificar JSON
        json_file = [f for f in json_files if 'integration_test' in f.name][0]
        json_content = json_file.read_text(encoding='utf-8')

        # Cada linha deve ser um JSON válido
        for line in json_content.strip().split('\n'):
            if line:
                log_entry = json.loads(line)
                assert 'timestamp' in log_entry
                assert 'level' in log_entry
                assert 'user' in log_entry
                assert 'message' in log_entry

    def test_concurrent_logging(self, temp_log_dir, clean_logger):
        """Teste: Logging concorrente em múltiplas threads"""
        AppLogger.setup_logging(
            log_dir=temp_log_dir,
            app_name='concurrent_test',
            level=logging.INFO,
            console_output=False,
            file_output=True,
            json_output=False
        )

        def thread_worker(thread_id):
            UserContext.set_user(username=f'user_{thread_id}', user_id=thread_id)
            logger = AppLogger.get_logger(f'thread_{thread_id}')

            for i in range(5):
                logger.info(f"Thread {thread_id} - Message {i}")
                time.sleep(0.01)

        threads = []
        for i in range(3):
            thread = threading.Thread(target=thread_worker, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Verificar que logs foram criados
        log_files = list(Path(temp_log_dir).glob('*.log'))
        assert len(log_files) >= 1

        log_file = [f for f in log_files if 'concurrent_test' in f.name][0]
        log_content = log_file.read_text(encoding='utf-8')

        # Verificar que logs de todas as threads estão presentes
        assert 'user_0' in log_content
        assert 'user_1' in log_content
        assert 'user_2' in log_content

# =====================================================
# EXECUTAR TESTES
# =====================================================

if __name__ == "__main__":
    pytest.main([
        __file__,
        "-v",
        # "--tb=short",
        # "--cov=logging_system",
        # "--cov-report=html",
        # "--cov-report=term-missing"
    ])