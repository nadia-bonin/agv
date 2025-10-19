import sys
import os

# Adicionar o diretório raiz ao Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

"""
Registra: usuário, timestamp, módulo, função, nível, mensagem
"""
import logging
import functools
import os
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import threading

# =====================================================
# 1. CONFIGURAÇÃO DO CONTEXTO DE USUÁRIO
# =====================================================

class UserContext:
    """Gerencia o contexto do usuário atual usando thread-local storage"""

    _context = threading.local()

    @classmethod
    def set_user(cls, username: str, user_id: Optional[int] = None, **extra_info):
        """Define o usuário atual no contexto"""
        cls._context.username = username
        cls._context.user_id = user_id
        cls._context.extra_info = extra_info

    @classmethod
    def get_user(cls) -> str:
        """Retorna o nome do usuário atual"""
        return getattr(cls._context, 'username', 'SYSTEM')

    @classmethod
    def get_user_id(cls) -> Optional[int]:
        """Retorna o ID do usuário atual"""
        return getattr(cls._context, 'user_id', None)

    @classmethod
    def get_extra_info(cls) -> Dict[str, Any]:
        """Retorna informações extras do usuário"""
        return getattr(cls._context, 'extra_info', {})

    @classmethod
    def clear_user(cls):
        """Limpa o contexto do usuário"""
        if hasattr(cls._context, 'username'):
            delattr(cls._context, 'username')
        if hasattr(cls._context, 'user_id'):
            delattr(cls._context, 'user_id')
        if hasattr(cls._context, 'extra_info'):
            delattr(cls._context, 'extra_info')

# =====================================================
# 2. FILTRO CUSTOMIZADO PARA ADICIONAR INFORMAÇÕES
# =====================================================

class UserContextFilter(logging.Filter):
    """Filtro que adiciona informações de contexto aos logs"""

    def filter(self, record):
        # Adicionar informações do usuário
        record.username = UserContext.get_user()
        record.user_id = UserContext.get_user_id() or 'N/A'

        # Adicionar informações extras
        extra_info = UserContext.get_extra_info()
        record.user_role = extra_info.get('role', 'N/A')
        record.user_department = extra_info.get('department', 'N/A')
        record.session_id = extra_info.get('session_id', 'N/A')

        # Adicionar informações de módulo e função
        # Já vem automaticamente em record.module e record.funcName

        return True

# =====================================================
# 3. FORMATTERS CUSTOMIZADOS
# =====================================================

class DetailedFormatter(logging.Formatter):
    """Formatter detalhado com todas as informações"""

    def __init__(self):
        super().__init__(
            fmt='%(asctime)s | %(levelname)-8s | User: %(username)s (ID: %(user_id)s) | '
                'Module: %(module)s | Function: %(funcName)s | Line: %(lineno)d | '
                '%(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

class JSONFormatter(logging.Formatter):
    """Formatter que gera logs em formato JSON"""

    def format(self, record):
        log_data = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'user': {
                'username': getattr(record, 'username', 'SYSTEM'),
                'user_id': getattr(record, 'user_id', None),
                'role': getattr(record, 'user_role', None),
                'department': getattr(record, 'user_department', None),
                'session_id': getattr(record, 'session_id', None)
            },
            'code': {
                'module': record.module,
                'function': record.funcName,
                'line': record.lineno,
                'pathname': record.pathname
            },
            'message': record.getMessage(),
            'thread': record.thread,
            'thread_name': record.threadName
        }

        # Adicionar exceção se houver
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)

        return json.dumps(log_data, ensure_ascii=False)

class ColoredFormatter(logging.Formatter):
    """Formatter com cores para console"""

    # Cores ANSI
    COLORS = {
        'DEBUG': '\033[36m',      # Ciano
        'INFO': '\033[32m',       # Verde
        'WARNING': '\033[33m',    # Amarelo
        'ERROR': '\033[31m',      # Vermelho
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }

    def __init__(self, fmt=None, datefmt='%Y-%m-%d %H:%M:%S'):
        super().__init__(fmt=fmt, datefmt=datefmt)

    def format(self, record):
        # Formatar timestamp primeiro
        record.asctime = self.formatTime(record, self.datefmt)

        # Salvar levelname original
        original_levelname = record.levelname

        # Adicionar cor ao nível
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.COLORS['RESET']}"

        # Adicionar cor ao nível
        if original_levelname in self.COLORS:
            colored_levelname = f"{self.COLORS[original_levelname]}{original_levelname}{self.COLORS['RESET']}"
        else:
            colored_levelname = original_levelname

        # Formato
        formatted = (
            f"{record.asctime} | {record.levelname:8s} | "
            f"👤 {getattr(record, 'username', 'SYSTEM'):12s} | "
            f"📦 {record.module:15s} | 🔧 {record.funcName:20s} | "
            f"{record.getMessage()}"
        )

        # Restaurar levelname original para não afetar outros handlers
        record.levelname = original_levelname

        return formatted

# =====================================================
# 4. CONFIGURAÇÃO DO LOGGER
# =====================================================

class AppLogger:
    """Classe para configurar e gerenciar loggers da aplicação"""

    _configured = False

    # @property
    # def logger(self) -> AppLogger:
    #     return self

    @classmethod
    def setup_logging(
        cls,
        log_dir: str = 'logs',
        app_name: str = 'app',
        level: int = logging.INFO,
        console_output: bool = True,
        file_output: bool = False,
        json_output: bool = False
    ):
        """Configura o sistema de logging"""

        if cls._configured:
            return

        # Criar diretório de logs
        log_path = Path(log_dir)
        log_path.mkdir(exist_ok=True)

        # Obter logger raiz
        root_logger = logging.getLogger()
        root_logger.setLevel(level)

        # Limpar handlers existentes
        root_logger.handlers.clear()

        # Adicionar filtro de contexto
        user_filter = UserContextFilter()

        # 1. Handler para Console (com cores)
        if console_output:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(level)
            console_handler.setFormatter(ColoredFormatter())
            console_handler.addFilter(user_filter)
            root_logger.addHandler(console_handler)

        # 2. Handler para Arquivo texto (detalhado)
        if file_output:
            today = datetime.now().strftime('%Y-%m-%d')
            file_handler = logging.FileHandler(
                log_path / f'{app_name}_{today}.log',
                encoding='utf-8'
            )
            file_handler.setLevel(level)
            file_handler.setFormatter(DetailedFormatter())
            file_handler.addFilter(user_filter)
            root_logger.addHandler(file_handler)

        # 3. Handler para JSON (análise e integração)
        if json_output:
            today = datetime.now().strftime('%Y-%m-%d')
            json_handler = logging.FileHandler(
                log_path / f'{app_name}_{today}.json',
                encoding='utf-8'
            )
            json_handler.setLevel(level)
            json_handler.setFormatter(JSONFormatter())
            json_handler.addFilter(user_filter)
            root_logger.addHandler(json_handler)

        # 4. Handler para Erros (arquivo separado)
        error_handler = logging.FileHandler(
            log_path / f'{app_name}_errors.log',
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(DetailedFormatter())
        error_handler.addFilter(user_filter)
        root_logger.addHandler(error_handler)

        cls._configured = True

        logging.info("Sistema de logging configurado com sucesso")

    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """Retorna um logger configurado"""
        if not cls._configured:
            cls.setup_logging()
        return logging.getLogger(name)

# =====================================================
# 5. DECORATORS PARA LOG AUTOMÁTICO
# =====================================================

def log_function_call(level: int = logging.INFO):
    """Decorator que loga automaticamente entrada e saída de funções"""

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = logging.getLogger(func.__module__)

            # Log de entrada
            args_repr = [repr(a) for a in args[:3]]  # Primeiros 3 args
            kwargs_repr = [f"{k}={v!r}" for k, v in list(kwargs.items())[:3]]
            signature = ", ".join(args_repr + kwargs_repr)

            logger.log(level, f"→ Iniciando {func.__name__}({signature})")

            try:
                # Executar função
                result = func(*args, **kwargs)

                # Log de saída bem-sucedida
                logger.log(level, f"✓ Concluído {func.__name__} → {type(result).__name__}")

                return result

            except Exception as e:
                # Log de erro
                logger.error(f"✗ Erro em {func.__name__}: {type(e).__name__}: {e}", exc_info=True)
                raise

        return wrapper
    return decorator

def log_execution_time(func):
    """Decorator que loga o tempo de execução"""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        import time
        logger = logging.getLogger(func.__module__)

        start_time = time.time()

        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time

            logger.info(f"⏱️ {func.__name__} executado em {execution_time:.4f}s")

            return result

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"⏱️ {func.__name__} falhou após {execution_time:.4f}s")
            raise

    return wrapper

# =====================================================
# 6. CONTEXT MANAGER PARA OPERAÇÕES
# =====================================================

class LoggedOperation:
    """Context manager para logar operações complexas"""

    def __init__(self, operation_name: str, logger: Optional[logging.Logger] = None):
        self.operation_name = operation_name
        self.logger = logger or logging.getLogger(__name__)
        self.start_time = None

    def __enter__(self):
        self.start_time = datetime.now()
        self.logger.info(f"╔═ Iniciando operação: {self.operation_name}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = (datetime.now() - self.start_time).total_seconds()

        if exc_type is None:
            self.logger.info(f"╚═ Operação concluída: {self.operation_name} ({duration:.2f}s)")
        else:
            self.logger.error(
                f"╚═ Operação falhou: {self.operation_name} ({duration:.2f}s) - "
                f"{exc_type.__name__}: {exc_val}"
            )

        # Não suprimir exceção
        return False



# =====================================================
# 7. EXEMPLO DE USO
# =====================================================

def initialize():
    """Exemplo de uso do sistema de logging"""

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

    # 4. Logs simples
    logger.debug("Mensagem de debug")
    logger.info("Sistema iniciado com sucesso")
    logger.warning("Atenção: recursos limitados")

    # 5. Usar decorators
    @log_function_call(level=logging.INFO)
    @log_execution_time
    def processar_pedido(pedido_id: int, prioridade: str = 'normal'):
        """Processa um pedido"""
        import time
        logger.info(f"Processando pedido {pedido_id} com prioridade {prioridade}")
        time.sleep(0.5)  # Simular processamento
        return f"Pedido {pedido_id} processado"

    resultado = processar_pedido(12345, prioridade='alta')
    logger.info(f"Resultado: {resultado}")

    # 6. Usar context manager
    with LoggedOperation("Importação de dados", logger):
        logger.info("Conectando ao banco de dados...")
        logger.info("Importando 1000 registros...")
        logger.info("Validando dados...")

    # 7. Log de erro com exceção
    try:
        resultado = 10 / 0
    except ZeroDivisionError as e:
        logger.error("Erro ao calcular resultado", exc_info=True)

    # 8. Trocar de usuário
    UserContext.set_user(
        username='maria.santos',
        user_id=456,
        role='user',
        department='Vendas'
    )

    logger.info("Usuário trocado - nova ação registrada")

    # 9. Log estruturado
    logger.info(
        "Venda realizada",
        extra={
            'venda_id': 789,
            'valor': 1500.00,
            'cliente': 'Cliente XYZ'
        }
    )

    # 10. Limpar contexto
    UserContext.clear_user()
    logger.info("Usuário desconectado")

if __name__ == "__main__":
    initialize()
