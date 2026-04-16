"""
Start Handler - Tela inicial e menu principal
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from sqlalchemy import func

from app.config import config
from app.database import db
from app.models import User, UserLevel, Cart, Affiliate
from utils.keyboards import Keyboards
from utils.logger import logger


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler do comando /start
    Tela inicial premium com experiência impactante
    """
    user = update.effective_user
    
    # Registrar ou atualizar usuário
    with db.get_session() as session:
        db_user = session.query(User).filter_by(telegram_id=user.id).first()
        
        is_new = False
        if not db_user:
            # Novo usuário
            db_user = User(
                telegram_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name
            )
            session.add(db_user)
            session.flush()
            
            # Criar carrinho
            cart = Cart(user_id=db_user.id)
            session.add(cart)
            
            is_new = True
            logger.info(f"Novo usuário registrado: {user.id} ({user.username})")
        else:
            # Atualizar dados
            db_user.username = user.username
            db_user.first_name = user.first_name
            db_user.last_name = user.last_name
            db_user.last_activity = func.now()
        
        user_id = db_user.id
        user_level = db_user.level
    
    # Mensagem de boas-vindas PREMIUM
    if is_new:
        welcome_text = f"""
🚀 *BEM-VINDO À {config.BOT_NAME}* 🚀

Olá *{user.first_name}*! 

Você acabou de entrar na *PLATAFORMA PREMIUM* de produtos digitais mais avançada do Telegram!

💎 *O QUE VOCÊ ENCONTRA AQUI:*
✅ Produtos de alta qualidade
✅ Entrega instantânea 24/7
✅ Pagamento 100% seguro via PIX
✅ Suporte especializado
✅ Ofertas exclusivas VIP

⚡ *PRIMEIRO PASSO:*
Explore nosso catálogo e descubra produtos incríveis!
        """
    else:
        # Usuário existente
        greeting = "Bom dia" if 5 <= func.extract('hour', func.now()) < 12 else \
                   "Boa tarde" if 12 <= func.extract('hour', func.now()) < 18 else \
                   "Boa noite"
        
        welcome_text = f"""
{config.EMOJIS['rocket']} *{greeting}, {user.first_name}!*

Bem-vindo de volta à *{config.BOT_NAME}* 💎

🎯 *ACESSO RÁPIDO:*
        """
    
    # Verificar se é admin
    is_admin = user.id == config.ADMIN_TELEGRAM_ID or user.id in config.ADMIN_IDS
    
    # Enviar mensagem com keyboard
    keyboard = Keyboards.start(user.first_name)
    
    # Adicionar botão admin se aplicável
    if is_admin:
        # Criar nova keyboard com botão admin
        keyboard = InlineKeyboardMarkup([
            *keyboard.inline_keyboard,
            [InlineKeyboardButton("⚙️ PAINEL ADMIN", callback_data="admin_panel")]
        ])
    
    await update.message.reply_text(
        welcome_text,
        parse_mode='Markdown',
        reply_markup=keyboard
    )
    
    # Mensagem adicional para novos usuários
    if is_new:
        await update.message.reply_text(
            f"""
🎁 *PROMOÇÃO DE BOAS-VINDAS!*

Use o código *BEMVINDO10* e ganhe *10% OFF* na primeira compra!

⏳ Válido por 24 horas
            """,
            parse_mode='Markdown'
        )


async def main_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para retorno ao menu principal"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    
    message = f"""
🎯 *MENU PRINCIPAL*

Olá *{user.first_name}*!

Escolha uma opção abaixo:
    """
    
    await query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=Keyboards.main_menu()
    )


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler principal de callbacks
    Roteia para handlers específicos
    """
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    # Roteamento de callbacks
    if data == "main_menu":
        await main_menu_handler(update, context)
    
    elif data == "start":
        await start_callback(update, context)
    
    elif data.startswith("menu_"):
        await menu_router(update, context, data)
    
    elif data.startswith("admin_"):
        from handlers.admin import admin_callback_router
        await admin_callback_router(update, context)
    
    elif data.startswith("category_") or data.startswith("product_"):
        from handlers.products import products_callback_router
        await products_callback_router(update, context)
    
    elif data.startswith("cart_") or data.startswith("add_to_cart_"):
        from handlers.cart import cart_callback_router
        await cart_callback_router(update, context)
    
    elif data.startswith("checkout_") or data.startswith("pix_") or data.startswith("buy_now_"):
        from handlers.checkout import checkout_callback_router
        await checkout_callback_router(update, context)
    
    elif data.startswith("order_") or data.startswith("delivery_"):
        from handlers.orders import orders_callback_router
        await orders_callback_router(update, context)
    
    elif data.startswith("affiliate_"):
        from handlers.affiliate import affiliate_callback_router
        await affiliate_callback_router(update, context)
    
    elif data == "close_message":
        await query.delete_message()
    
    elif data == "noop":
        # Não faz nada (botão decorativo)
        pass


async def start_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Callback do botão voltar ao início"""
    query = update.callback_query
    user = update.effective_user
    
    message = f"""
🚀 *{config.BOT_NAME}* 🚀

💎 *A MELHOR PLATAFORMA DE PRODUTOS DIGITAIS*

Escolha uma opção:
    """
    
    keyboard = Keyboards.start(user.first_name)
    
    # Verificar se é admin
    if user.id == config.ADMIN_TELEGRAM_ID:
        keyboard = InlineKeyboardMarkup([
            *keyboard.inline_keyboard,
            [InlineKeyboardButton("⚙️ PAINEL ADMIN", callback_data="admin_panel")]
        ])
    
    await query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=keyboard
    )


async def menu_router(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    """Roteia callbacks de menu"""
    query = update.callback_query
    
    if data == "menu_products":
        from handlers.products import show_categories
        await show_categories(update, context)
    
    elif data == "menu_shop":
        from handlers.products import show_categories
        await show_categories(update, context)
    
    elif data == "menu_cart":
        from handlers.cart import show_cart
        await show_cart(update, context)
    
    elif data == "menu_orders":
        from handlers.orders import show_orders
        await show_orders(update, context)
    
    elif data == "menu_promos":
        await show_promos(update, context)
    
    elif data == "menu_account":
        await show_account(update, context)
    
    elif data == "menu_support":
        from handlers.support import show_support
        await show_support(update, context)
    
    elif data == "menu_vip":
        await show_vip_area(update, context)


async def show_promos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mostra promoções ativas"""
    query = update.callback_query
    
    message = f"""
🎁 *PROMOÇÕES ATIVAS*

🔥 *BLACK FRIDAY TODO DIA!*

🏷️ Código: *BEMVINDO10*
Desconto: 10% OFF
Válido: Primeira compra

🏷️ Código: *VIP20*
Desconto: 20% OFF
Válido: Produtos VIP

🏷️ Código: *FLASH30*
Desconto: 30% OFF
Válido: Próximas 2h

⚡ *OFERTAS RELÂMPAGO:*
💳 Info CC Gold - De R$ 200,00 por R$ 150,00
💎 Info CC Platinum - De R$ 400,00 por R$ 300,00
🏆 Info CC Infinite - De R$ 700,00 por R$ 500,00
    """
    
    await query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=Keyboards.back_to_menu()
    )


async def show_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mostra dados da conta do usuário"""
    query = update.callback_query
    user = update.effective_user
    
    with db.get_session() as session:
        db_user = session.query(User).filter_by(telegram_id=user.id).first()
        
        if not db_user:
            await query.edit_message_text(
                "❌ Erro ao carregar dados. Use /start",
                reply_markup=Keyboards.back_to_menu()
            )
            return
        
        affiliate = session.query(Affiliate).filter_by(user_id=db_user.id).first()
        is_affiliate = affiliate is not None
        
        message = f"""
👤 *MINHA CONTA*

📝 *DADOS PESSOAIS*
Nome: {db_user.full_name}
Username: @{db_user.username or 'N/A'}
ID: `{db_user.telegram_id}`
Nível: {db_user.level.value.upper()}

📊 *RESUMO*
Total de pedidos: {db_user.total_orders}
Total gasto: R$ {float(db_user.total_spent):.2f}
Cadastro: {db_user.created_at.strftime('%d/%m/%Y')}
        """
        
        if is_affiliate:
            message += f"""

🤝 *PROGRAMA DE AFILIADOS*
Saldo: R$ {float(affiliate.balance):.2f}
Total ganho: R$ {float(affiliate.total_earned):.2f}
Indicados: {affiliate.total_referrals}
            """
    
    await query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=Keyboards.account(is_affiliate)
    )


async def show_vip_area(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mostra área VIP"""
    query = update.callback_query
    user = update.effective_user
    
    with db.get_session() as session:
        db_user = session.query(User).filter_by(telegram_id=user.id).first()
        
        # Verificar se é VIP
        is_vip = db_user is not None and db_user.level in [UserLevel.VIP, UserLevel.ADMIN, UserLevel.MASTER]
    
    if is_vip:
        message = f"""
👑 *ÁREA VIP EXCLUSIVA*

🎉 Bem-vindo, VIP!

💎 *BENEFÍCIOS ATIVOS:*
✅ Acesso a produtos exclusivos
✅ 20% OFF em todas as compras
✅ Prioridade no suporte
✅ Produtos antes de todo mundo
✅ Brindes mensais

🔥 *PRODUTOS VIP DISPONÍVEIS:*
• Info CC Black - R$ 800,00
• Pacote Premium - R$ 1.500,00

💎 Você é especial para nós!
        """
    else:
        message = f"""
👑 *ÁREA VIP*

🔒 *ACESSO RESTRITO*

Para acessar esta área, você precisa:

✅ Realizar 5 compras
OU
✅ Comprar o pacote VIP (R$ 500,00)

🎁 *BENEFÍCIOS VIP:*
• 20% OFF em todas as compras
• Produtos exclusivos
• Atendimento prioritário
• Acesso antecipado a novidades

Quer virar VIP? Fale com @suporte
        """
    
    await query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=Keyboards.back_to_menu()
    )


# Handlers para registro
start_command = CommandHandler('start', start_handler)
main_menu_callback = CallbackQueryHandler(main_menu_handler, pattern='^main_menu$')
callback_router = CallbackQueryHandler(callback_handler)
