"""
Sistema de logging estruturado
"""

import logging
import sys
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path

from app.config import config
from app.database import db


class Logger:
    """Logger estruturado com múltiplos handlers"""
    
    def __init__(self, name: str = "TksBot"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG if config.DEBUG else logging.INFO)
        
        # Evitar duplicação de handlers
        if self.logger.handlers:
            return
        
        # Formato padrão
        formatter = logging.Formatter(
            '%(asctime)s | %(name)s | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # File handler (rotacionado)
        log_dir = Path('logs')
        log_dir.mkdir(exist_ok=True)
        
        file_handler = logging.FileHandler(
            log_dir / f'bot_{datetime.now():%Y%m%d}.log',
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        # Error file handler
        error_handler = logging.FileHandler(
            log_dir / f'errors_{datetime.now():%Y%m%d}.log',
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        self.logger.addHandler(error_handler)
    
    def debug(self, message: str, **kwargs):
        """Log de debug"""
        self._log(logging.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log de informação"""
        self._log(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log de aviso"""
        self._log(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log de erro"""
        self._log(logging.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log crítico"""
        self._log(logging.CRITICAL, message, **kwargs)
    
    def _log(self, level: int, message: str, **kwargs):
        """Método interno de logging"""
        extra = self._format_extra(kwargs)
        full_message = f"{message} | {extra}" if extra else message
        self.logger.log(level, full_message)
        
        # Salvar no banco se for erro ou warning
        if level >= logging.WARNING:
            self._save_to_db(level, message, kwargs)
    
    def _format_extra(self, kwargs: Dict[str, Any]) -> str:
        """Formata dados extras para string"""
        if not kwargs:
            return ""
        
        parts = []
        for key, value in kwargs.items():
            if value is not None:
                parts.append(f"{key}={value}")
        
        return " | ".join(parts)
    
    def _save_to_db(self, level: int, message: str, kwargs: Dict[str, Any]):
        """Salva log no banco de dados"""
        try:
            from app.models import Log
            
            with db.get_session() as session:
                level_name = logging.getLevelName(level)
                category = kwargs.get('category', 'system')
                
                log_entry = Log(
                    level=level_name,
                    category=category,
                    message=message,
                    user_id=kwargs.get('user_id'),
                    order_id=kwargs.get('order_id'),
                    payment_id=kwargs.get('payment_id'),
                    details=kwargs
                )
                session.add(log_entry)
        except Exception as e:
            # Se falhar o log no banco, apenas log no console
            self.logger.error(f"Falha ao salvar log no banco: {e}")


# Instância global do logger
logger = Logger()


# Funções de conveniência
def log_payment_event(message: str, user_id: Optional[int] = None, 
                      order_id: Optional[int] = None, **kwargs):
    """Log específico para eventos de pagamento"""
    logger.info(message, category='payment', user_id=user_id, order_id=order_id, **kwargs)


def log_order_event(message: str, user_id: Optional[int] = None, 
                    order_id: Optional[int] = None, **kwargs):
    """Log específico para eventos de pedido"""
    logger.info(message, category='order', user_id=user_id, order_id=order_id, **kwargs)


def log_user_event(message: str, user_id: Optional[int] = None, **kwargs):
    """Log específico para eventos de usuário"""
    logger.info(message, category='user', user_id=user_id, **kwargs)


def log_admin_event(message: str, admin_id: Optional[int] = None, **kwargs):
    """Log específico para eventos administrativos"""
    logger.info(message, category='admin', user_id=admin_id, **kwargs)


def log_error(message: str, exception: Optional[Exception] = None, **kwargs):
    """Log de erro com detalhes da exceção"""
    if exception:
        message = f"{message} | Exception: {type(exception).__name__}: {str(exception)}"
    logger.error(message, category='error', **kwargs)
