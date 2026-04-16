"""
Configuração centralizada do TksBot
Todas as variáveis de ambiente e constantes do sistema
"""

import os
import logging
from typing import Optional, List
from dataclasses import dataclass
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Configuração de logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


@dataclass
class Config:
    """Configurações centralizadas do bot"""
    
    # ============================================
    # BOT TELEGRAM
    # ============================================
    BOT_TOKEN: str = os.getenv('BOT_TOKEN', '')
    BOT_NAME: str = os.getenv('BOT_NAME', 'TksBot')
    BOT_USERNAME: str = os.getenv('BOT_USERNAME', 'tksbot')
    
    # ============================================
    # ADMINISTRAÇÃO
    # ============================================
    ADMIN_TELEGRAM_ID: int = int(os.getenv('ADMIN_TELEGRAM_ID', '0'))
    
    @property
    def ADMIN_IDS(self) -> List[int]:
        """Retorna lista de IDs de administradores"""
        admin_ids = os.getenv('ADMIN_IDS', '')
        if admin_ids:
            return [int(x.strip()) for x in admin_ids.split(',') if x.strip()]
        return [self.ADMIN_TELEGRAM_ID] if self.ADMIN_TELEGRAM_ID else []
    
    # ============================================
    # SILLIENTPAY (PIX)
    # ============================================
    SILLIENT_API_KEY: str = os.getenv('SILLIENT_API_KEY', '')
    SILLIENT_SECRET_KEY: str = os.getenv('SILLIENT_SECRET_KEY', '')
    SILLIENT_BASE_URL: str = os.getenv('SILLIENT_BASE_URL', 'https://api.sillientpay.com/v1')
    
    # ============================================
    # BANCO DE DADOS
    # ============================================
    DATABASE_URL: str = os.getenv('DATABASE_URL', 'sqlite:///bot_database.db')
    
    @property
    def IS_POSTGRESQL(self) -> bool:
        """Verifica se está usando PostgreSQL"""
        return 'postgresql' in self.DATABASE_URL.lower()
    
    # ============================================
    # REDIS (CACHE)
    # ============================================
    REDIS_URL: str = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    
    # ============================================
    # WEBHOOK
    # ============================================
    WEBHOOK_URL: str = os.getenv('WEBHOOK_URL', '')
    WEBHOOK_SECRET: str = os.getenv('WEBHOOK_SECRET', '')
    WEBHOOK_PATH: str = os.getenv('WEBHOOK_PATH', '/webhook')
    WEBHOOK_PORT: int = int(os.getenv('WEBHOOK_PORT', '8000'))
    
    # ============================================
    # MODO DE OPERAÇÃO
    # ============================================
    MODE: str = os.getenv('MODE', 'polling')  # 'polling' ou 'webhook'
    DEBUG: bool = os.getenv('DEBUG', 'false').lower() == 'true'
    ENVIRONMENT: str = os.getenv('ENVIRONMENT', 'development')
    
    @property
    def IS_PRODUCTION(self) -> bool:
        """Verifica se está em produção"""
        return self.ENVIRONMENT == 'production'
    
    # ============================================
    # SEGURANÇA
    # ============================================
    RATE_LIMIT_MESSAGES: int = int(os.getenv('RATE_LIMIT_MESSAGES', '20'))
    RATE_LIMIT_WINDOW: int = int(os.getenv('RATE_LIMIT_WINDOW', '60'))
    FLOOD_THRESHOLD: int = int(os.getenv('FLOOD_THRESHOLD', '5'))
    
    # ============================================
    # TEMPOS DE EXPIRAÇÃO (minutos)
    # ============================================
    CART_TIMEOUT: int = int(os.getenv('CART_TIMEOUT', '30'))
    PAYMENT_TIMEOUT: int = int(os.getenv('PAYMENT_TIMEOUT', '30'))
    PIX_EXPIRATION: int = int(os.getenv('PIX_EXPIRATION', '30'))
    
    # ============================================
    # NOTIFICAÇÕES
    # ============================================
    NOTIFICATION_CHANNEL_ID: Optional[str] = os.getenv('NOTIFICATION_CHANNEL_ID')
    ERROR_LOG_CHANNEL_ID: Optional[str] = os.getenv('ERROR_LOG_CHANNEL_ID')
    
    # ============================================
    # AFILIADOS
    # ============================================
    AFFILIATE_COMMISSION_PERCENT: float = float(os.getenv('AFFILIATE_COMMISSION_PERCENT', '10'))
    MIN_AFFILIATE_PAYOUT: float = float(os.getenv('MIN_AFFILIATE_PAYOUT', '50'))
    
    # ============================================
    # BACKUP
    # ============================================
    BACKUP_INTERVAL_HOURS: int = int(os.getenv('BACKUP_INTERVAL_HOURS', '24'))
    BACKUP_RETENTION_DAYS: int = int(os.getenv('BACKUP_RETENTION_DAYS', '7'))
    
    # ============================================
    # URLS
    # ============================================
    SUPPORT_URL: str = os.getenv('SUPPORT_URL', 'https://t.me/suporte_tksbot')
    CHANNEL_URL: str = os.getenv('CHANNEL_URL', 'https://t.me/tksbot_canal')
    
    # ============================================
    # FUNCIONALIDADES
    # ============================================
    ENABLE_ORDER_BUMP: bool = os.getenv('ENABLE_ORDER_BUMP', 'true').lower() == 'true'
    ENABLE_UPSELL: bool = os.getenv('ENABLE_UPSELL', 'true').lower() == 'true'
    ENABLE_ABANDONED_CART: bool = os.getenv('ENABLE_ABANDONED_CART', 'true').lower() == 'true'
    ENABLE_REMARKETING: bool = os.getenv('ENABLE_REMARKETING', 'true').lower() == 'true'
    
    # ============================================
    # CONSTANTES DE UI
    # ============================================
    EMOJIS = {
        'cart': '🛒',
        'money': '💰',
        'card': '💳',
        'diamond': '💎',
        'trophy': '🏆',
        'fire': '🔥',
        'star': '⭐',
        'crown': '👑',
        'lock': '🔒',
        'shield': '🛡️',
        'gift': '🎁',
        'rocket': '🚀',
        'lightning': '⚡',
        'check': '✅',
        'warning': '⚠️',
        'error': '❌',
        'info': 'ℹ️',
        'user': '👤',
        'support': '🆘',
        'package': '📦',
        'shopping': '🛍️',
        'discount': '🏷️',
        'chart': '📈',
        'document': '📄',
        'file': '📋',
        'time': '⏰',
        'success': '🎉',
        'vip': '🥇',
        'gold': '🥇',
        'silver': '🥈',
        'bronze': '🥉',
        'black': '🖤',
        'platinum': '💎',
        'infinite': '♾️',
        'basic': '📱',
    }
    
    # Categorias de produtos
    CATEGORIES = {
        'credit_cards': {
            'name': '💳 Cartões de Crédito',
            'emoji': '💳',
            'description': 'Informações de cartões premium'
        },
        'documents': {
            'name': '📄 Documentos',
            'emoji': '📄',
            'description': 'Documentos e comprovantes'
        },
        'vip': {
            'name': '👑 VIP',
            'emoji': '👑',
            'description': 'Produtos exclusivos VIP'
        }
    }
    
    # Status de pedidos
    ORDER_STATUS = {
        'pending': '⏳ Pendente',
        'paid': '✅ Pago',
        'processing': '🔄 Processando',
        'delivered': '📦 Entregue',
        'cancelled': '❌ Cancelado',
        'refunded': '↩️ Reembolsado'
    }
    
    # Status de pagamentos
    PAYMENT_STATUS = {
        'pending': '⏳ Aguardando Pagamento',
        'processing': '🔄 Processando',
        'approved': '✅ Aprovado',
        'rejected': '❌ Rejeitado',
        'cancelled': '🚫 Cancelado',
        'refunded': '↩️ Reembolsado',
        'expired': '⏰ Expirado'
    }
    
    # Métodos de pagamento
    PAYMENT_METHODS = {
        'pix': '💠 PIX',
        'credit_card': '💳 Cartão',
        'boleto': '📄 Boleto'
    }
    
    # ============================================
    # VALIDAÇÃO
    # ============================================
    def validate(self) -> bool:
        """Valida configurações obrigatórias"""
        required = [
            self.BOT_TOKEN,
            self.SILLIENT_API_KEY,
            self.SILLIENT_SECRET_KEY,
        ]
        
        if self.MODE == 'webhook':
            required.append(self.WEBHOOK_URL)
        
        missing = [i for i, val in enumerate(required) if not val]
        if missing:
            logger.error(f"Configurações obrigatórias ausentes: {missing}")
            return False
        
        logger.info("✅ Configurações validadas com sucesso")
        return True


# Instância global de configurações
config = Config()
