"""
Logging Middleware
"""

import time
from telegram import Update
from telegram.ext import ContextTypes

from utils.logger import logger


class LoggingMiddleware:
    """Middleware para logging de todas as interações"""
    
    def __init__(self):
        self.processing_times = {}
    
    async def log_update(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Log de atualização recebida"""
        user = update.effective_user
        
        if not user:
            return
        
        # Identificar tipo de update
        update_type = "unknown"
        content = ""
        
        if update.message:
            update_type = "message"
            content = update.message.text[:50] if update.message.text else "(no text)"
        elif update.callback_query:
            update_type = "callback"
            content = update.callback_query.data[:50]
        elif update.inline_query:
            update_type = "inline_query"
            content = update.inline_query.query[:50]
        
        logger.debug(
            f"Update recebido: {update_type}",
            user_id=user.id,
            username=user.username,
            content=content
        )
    
    def start_timer(self, update_id: int):
        """Inicia timer para medir tempo de processamento"""
        self.processing_times[update_id] = time.time()
    
    def end_timer(self, update_id: int) -> float:
        """Finaliza timer e retorna tempo de processamento"""
        start_time = self.processing_times.pop(update_id, None)
        if start_time:
            return time.time() - start_time
        return 0


# Instância global
logging_middleware = LoggingMiddleware()
