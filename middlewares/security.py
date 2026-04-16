"""
Middleware de Segurança
Anti-flood, anti-spam, sanitização
"""

import time
from typing import Callable, Any
from telegram import Update
from telegram.ext import ContextTypes

from app.config import config
from app.database import db
from utils.logger import logger


class SecurityMiddleware:
    """Middleware de segurança e proteção"""
    
    def __init__(self):
        self.user_activity = {}  # {user_id: [timestamps]}
        self.banned_users = set()
        self._load_banned_users()
    
    def _load_banned_users(self):
        """Carrega usuários banidos do banco"""
        try:
            from app.models import User
            with db.get_session() as session:
                banned = session.query(User.telegram_id).filter_by(is_banned=True).all()
                self.banned_users = {user[0] for user in banned}
        except Exception as e:
            logger.error(f"Erro ao carregar usuários banidos: {e}")
    
    async def check_banned(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        """Verifica se usuário está banido"""
        user_id = update.effective_user.id
        
        if user_id in self.banned_users:
            await update.message.reply_text(
                "🚫 *Acesso Negado*\n\n"
                "Sua conta foi suspensa.\n"
                "Entre em contato com o suporte.",
                parse_mode='Markdown'
            )
            return False
        return True
    
    async def check_flood(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        """Verifica proteção anti-flood"""
        user_id = update.effective_user.id
        now = time.time()
        
        if user_id not in self.user_activity:
            self.user_activity[user_id] = []
        
        # Limpar entradas antigas (mais de 60 segundos)
        window = self.user_activity[user_id]
        self.user_activity[user_id] = [t for t in window if now - t < config.RATE_LIMIT_WINDOW]
        
        # Adicionar nova atividade
        self.user_activity[user_id].append(now)
        
        # Verificar limite
        if len(self.user_activity[user_id]) > config.RATE_LIMIT_MESSAGES:
            await update.message.reply_text(
                "⚠️ *Muitas mensagens rápidas!*\n\n"
                "Por favor, aguarde um momento antes de enviar mais mensagens.",
                parse_mode='Markdown'
            )
            return False
        
        # Verificar flood extremo (muitas mensagens em pouco tempo)
        if len(self.user_activity[user_id]) > config.FLOOD_THRESHOLD:
            recent = [t for t in self.user_activity[user_id] if now - t < 10]  # Últimos 10 segundos
            if len(recent) > config.FLOOD_THRESHOLD:
                await update.message.reply_text(
                    "⏳ *Calma aí!*\n\n"
                    "Você está enviando mensagens muito rápido. "
                    "Aguarde alguns segundos.",
                    parse_mode='Markdown'
                )
                return False
        
        return True
    
    async def sanitize_input(self, text: str) -> str:
        """Sanitiza input do usuário"""
        if not text:
            return ""
        
        # Remover caracteres de controle (exceto nova linha)
        text = ''.join(char for char in text if ord(char) >= 32 or char == '\n')
        
        # Limitar tamanho
        if len(text) > 1000:
            text = text[:1000]
        
        return text.strip()
    
    async def pre_process(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        """Processamento pré-handler"""
        if not update.effective_user:
            return False
        
        # Verificar ban
        if not await self.check_banned(update, context):
            return False
        
        # Verificar flood
        if update.message and not await self.check_flood(update, context):
            return False
        
        # Sanitizar mensagem
        if update.message and update.message.text:
            update.message.text = await self.sanitize_input(update.message.text)
        
        return True
    
    async def ban_user(self, telegram_id: int, reason: str = ""):
        """Bane um usuário"""
        try:
            from app.models import User
            
            with db.get_session() as session:
                user = session.query(User).filter_by(telegram_id=telegram_id).first()
                if user:
                    user.is_banned = True
                    user.ban_reason = reason
                
                self.banned_users.add(telegram_id)
                
                logger.warning(f"Usuário banido: {telegram_id}. Motivo: {reason}")
        except Exception as e:
            logger.error(f"Erro ao banir usuário: {e}")
    
    async def unban_user(self, telegram_id: int):
        """Desbane um usuário"""
        try:
            from app.models import User
            
            with db.get_session() as session:
                user = session.query(User).filter_by(telegram_id=telegram_id).first()
                if user:
                    user.is_banned = False
                    user.ban_reason = None
                
                self.banned_users.discard(telegram_id)
                
                logger.info(f"Usuário desbanido: {telegram_id}")
        except Exception as e:
            logger.error(f"Erro ao desbanir usuário: {e}")


# Instância global
security = SecurityMiddleware()
