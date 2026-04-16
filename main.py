"""
TksBot - Plataforma Premium de Vendas no Telegram
==================================================

Sistema enterprise de vendas automáticas com:
- Integração SillientPay (PIX)
- Painel admin completo
- Programa de afiliados
- Carrinho de compras
- Entrega automática
- PostgreSQL + SQLAlchemy
- Deploy otimizado para Railway

Autor: Cascade AI
Versão: 2.0.0 Premium
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

# Adicionar diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent))

from telegram import Update
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes
)

# App imports
from app.config import config
from app.database import db
from app.models import seed_products, create_default_admin

# Services
from services.sillientpay import sillientpay
from services.notifications import notifications
from services.delivery import delivery

# Utils
from utils.logger import logger

# Handlers
from handlers.start import (
    start_handler, 
    start_command, 
    callback_router
)
from utils.keyboards import Keyboards
from handlers.products import products_handler, products_message_handler
from handlers.cart import cart_handler, cart_callback_router, cart_message_handler
from handlers.checkout import checkout_handler, checkout_callback_router
from handlers.orders import orders_handler
from handlers.admin import admin_handler, admin_callback_router, admin_message_handler
from handlers.support import support_handler


# ============================================
# CONFIGURAÇÃO DE LOGGING
# ============================================

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Silenciar logs muito verbosos
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('httpcore').setLevel(logging.WARNING)


# ============================================
# COMANDOS DO BOT
# ============================================

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /help"""
    message = f"""
🆘 *AJUDA - COMANDOS DISPONÍVEIS*

/start - Iniciar bot / Menu principal
/produtos - Ver catálogo
/carrinho - Meu carrinho
/pedidos - Meus pedidos
/conta - Minha conta
/suporte - Central de ajuda
/admin - Painel admin ( restrito )

💡 *DICAS:*
• Use os botões para navegar
• Seu carrinho fica salvo
• Pagamento via PIX instantâneo
• Entrega automática após pagamento

Precisa de mais ajuda? Use /suporte
    """
    
    await update.message.reply_text(
        message,
        parse_mode='Markdown',
        reply_markup=Keyboards.back_to_menu()
    )


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancela operação atual"""
    context.user_data.clear()
    
    await update.message.reply_text(
        "❌ Operação cancelada.\n\nUse /start para voltar ao menu.",
        reply_markup=Keyboards.back_to_menu()
    )


async def echo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler de mensagens não reconhecidas"""
    # Verificar se está aguardando alguma ação
    awaiting = context.user_data.get('awaiting')
    
    if awaiting == 'coupon_code':
        from handlers.cart import cart_message_handler
        await cart_message_handler(update, context)
    
    elif awaiting == 'search_product':
        from handlers.products import products_message_handler
        await products_message_handler(update, context)
    
    elif awaiting == 'broadcast_message':
        from handlers.admin import admin_message_handler
        await admin_message_handler(update, context)
    
    elif awaiting == 'new_product':
        from handlers.admin import admin_message_handler
        await admin_message_handler(update, context)
    
    elif awaiting == 'affiliate_withdraw':
        from handlers.affiliate import affiliate_message_handler
        await affiliate_message_handler(update, context)
    
    else:
        # Mensagem padrão
        await update.message.reply_text(
            "❓ Não entendi.\n\n"
            "Use /start para ver o menu ou /help para ajuda.",
            reply_markup=Keyboards.back_to_menu()
        )


# ============================================
# SETUP DO BOT
# ============================================

def setup_application() -> Application:
    """Configura aplicação do bot"""
    
    # Builder
    application = ApplicationBuilder().token(config.BOT_TOKEN).build()
    
    # Guardar bot em services
    notifications.set_bot(application.bot)
    delivery.set_bot(application.bot)
    
    # Comandos
    application.add_handler(CommandHandler('start', start_handler))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(CommandHandler('cancelar', cancel_command))
    application.add_handler(CommandHandler('cancel', cancel_command))
    
    # Comandos rápidos
    application.add_handler(CommandHandler('produtos', products_handler))
    application.add_handler(CommandHandler('carrinho', cart_handler))
    application.add_handler(CommandHandler('pedidos', orders_handler))
    application.add_handler(CommandHandler('suporte', support_handler))
    application.add_handler(CommandHandler('admin', admin_handler))
    
    # Callbacks
    application.add_handler(CallbackQueryHandler(callback_router))
    
    # Mensagens
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo_handler))
    
    # Erros
    application.add_error_handler(error_handler)
    
    return application


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler global de erros"""
    logger.error(f"Erro no update {update}: {context.error}")
    
    # Notificar usuário
    if update and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "⚠️ Ocorreu um erro. Tente novamente ou contate o suporte."
            )
        except:
            pass


# ============================================
# INICIALIZAÇÃO
# ============================================

def init_database():
    """Inicializa banco de dados"""
    try:
        # Criar tabelas
        db.create_tables()
        
        # Seed de produtos
        with db.get_session() as session:
            seed_products(session)
            
            # Criar admin master
            if config.ADMIN_TELEGRAM_ID:
                create_default_admin(session, config.ADMIN_TELEGRAM_ID)
        
        logger.info("✅ Banco de dados inicializado")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro ao inicializar banco: {e}")
        return False


async def post_init(application: Application):
    """Ações após inicialização"""
    logger.info(f"🚀 {config.BOT_NAME} iniciado com sucesso!")
    logger.info(f"Modo: {config.MODE}")
    logger.info(f"Admin: {config.ADMIN_TELEGRAM_ID}")


# ============================================
# MAIN
# ============================================

def main():
    """Função principal"""
    
    # Validar configurações
    if not config.validate():
        logger.error("❌ Configurações inválidas. Verifique .env")
        sys.exit(1)
    
    # Inicializar banco
    if not init_database():
        logger.error("❌ Falha ao conectar ao banco de dados")
        sys.exit(1)
    
    # Setup
    application = setup_application()
    
    # Post init
    application.post_init = post_init
    
    # Iniciar
    if config.MODE == 'webhook':
        # Webhook mode (Railway)
        port = int(os.environ.get('PORT', config.WEBHOOK_PORT))
        
        logger.info(f"🌐 Iniciando webhook na porta {port}")
        
        application.run_webhook(
            listen='0.0.0.0',
            port=port,
            webhook_url=config.WEBHOOK_URL,
            secret_token=config.WEBHOOK_SECRET if config.WEBHOOK_SECRET else None
        )
    else:
        # Polling mode (local/dev)
        logger.info("🔄 Iniciando polling mode")
        
        application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True
        )


if __name__ == '__main__':
    main()
