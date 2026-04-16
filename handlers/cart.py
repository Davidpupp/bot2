"""
Cart Handler - Carrinho de compras
"""

from telegram import Update
from telegram.ext import ContextTypes

from app.config import config
from app.database import db
from app.models import Cart, Product, User
from utils.keyboards import Keyboards
from utils.helpers import format_currency
from utils.logger import logger


async def cart_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler do carrinho via comando"""
    await show_cart(update, context)


async def show_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mostra carrinho atual"""
    user = update.effective_user
    
    with db.get_session() as session:
        db_user = session.query(User).filter_by(telegram_id=user.id).first()
        
        if not db_user:
            message = "❌ Você precisa iniciar o bot primeiro.\nUse /start"
            keyboard = Keyboards.back_to_menu()
        else:
            cart = session.query(Cart).filter_by(user_id=db_user.id).first()
            
            if not cart or not cart.items:
                message = f"""
🛒 *CARRINHO VAZIO*

Seu carrinho está esperando por produtos incríveis!

🛍️ Explore nosso catálogo e adicione itens.
                """
                keyboard = Keyboards.cart_empty()
            else:
                # Processar itens
                cart_items = cart.items if isinstance(cart.items, list) else []
                
                items_data = []
                total = 0
                
                for item in cart_items:
                    product = session.query(Product).get(item['product_id'])
                    if product:
                        quantity = item.get('quantity', 1)
                        subtotal = float(product.price) * quantity
                        
                        items_data.append({
                            'id': product.id,
                            'name': product.name,
                            'quantity': quantity,
                            'subtotal': subtotal
                        })
                        
                        total += subtotal
                
                if not items_data:
                    message = f"""
🛒 *CARRINHO VAZIO*

Os produtos podem ter sido removidos ou esgotados.

🛍️ Explore nosso catálogo novamente.
                    """
                    keyboard = Keyboards.cart_empty()
                else:
                    # Formatar mensagem
                    items_text = "\n".join([
                        f"• {item['name']} (x{item['quantity']}) - {format_currency(item['subtotal'])}"
                        for item in items_data
                    ])
                    
                    message = f"""
🛒 *MEU CARRINHO*

{items_text}

💰 *Total:* {format_currency(total)}

Pronto para finalizar? 💳
                    """
                    keyboard = Keyboards.cart(items_data, total)
    
    # Enviar mensagem
    if update.callback_query:
        await update.callback_query.edit_message_text(
            message,
            parse_mode='Markdown',
            reply_markup=keyboard
        )
    else:
        await update.message.reply_text(
            message,
            parse_mode='Markdown',
            reply_markup=keyboard
        )


async def add_to_cart_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Adiciona produto ao carrinho"""
    query = update.callback_query
    await query.answer()
    
    product_id = int(query.data.replace('add_to_cart_', ''))
    user = update.effective_user
    
    with db.get_session() as session:
        db_user = session.query(User).filter_by(telegram_id=user.id).first()
        
        if not db_user:
            await query.edit_message_text(
                "❌ Erro: Usuário não encontrado. Use /start",
                reply_markup=Keyboards.back_to_menu()
            )
            return
        
        product = session.query(Product).get(product_id)
        
        if not product or not product.is_active:
            await query.answer("❌ Produto indisponível", show_alert=True)
            return
        
        # Verificar estoque
        if not product.has_stock:
            await query.answer("❌ Produto esgotado", show_alert=True)
            return
        
        # Buscar ou criar carrinho
        cart = session.query(Cart).filter_by(user_id=db_user.id).first()
        if not cart:
            cart = Cart(user_id=db_user.id)
            session.add(cart)
            session.flush()
        
        # Adicionar item
        cart.add_item(product_id, 1)
        
        # Contar itens
        cart_items = cart.items if isinstance(cart.items, list) else []
        items_count = sum(item.get('quantity', 1) for item in cart_items)
    
    await query.answer(
        f"✅ {product.name} adicionado!\n🛒 Carrinho: {items_count} item(s)",
        show_alert=True
    )
    
    # Atualizar view ou mostrar carrinho
    await show_cart(update, context)


async def remove_from_cart_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remove item do carrinho"""
    query = update.callback_query
    await query.answer()
    
    product_id = int(query.data.replace('cart_remove_', ''))
    user = update.effective_user
    
    with db.get_session() as session:
        db_user = session.query(User).filter_by(telegram_id=user.id).first()
        
        if not db_user:
            return
        
        cart = session.query(Cart).filter_by(user_id=db_user.id).first()
        
        if cart:
            cart.remove_item(product_id)
    
    await query.answer("✅ Item removido!")
    await show_cart(update, context)


async def clear_cart_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Limpa carrinho"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    
    with db.get_session() as session:
        db_user = session.query(User).filter_by(telegram_id=user.id).first()
        
        if db_user:
            cart = session.query(Cart).filter_by(user_id=db_user.id).first()
            if cart:
                cart.clear()
    
    await query.answer("🗑️ Carrinho limpo!")
    await show_cart(update, context)


async def apply_coupon_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Aplica cupom de desconto"""
    query = update.callback_query
    await query.answer()
    
    query.edit_message_text(
        """
🏷️ *APLICAR CUPOM*

Digite o código do cupom:

Exemplos válidos:
• BEMVINDO10
• VIP20
• FLASH30

Ou envie /cancelar para voltar.
        """,
        parse_mode='Markdown',
        reply_markup=Keyboards.back_to_menu()
    )
    
    # Definir estado
    context.user_data['awaiting'] = 'coupon_code'


async def process_coupon(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa código de cupom"""
    code = update.message.text.upper().strip()
    user = update.effective_user
    
    with db.get_session() as session:
        from app.models import Coupon
        
        coupon = session.query(Coupon).filter_by(code=code, is_active=True).first()
        
        if not coupon or not coupon.is_valid:
            await update.message.reply_text(
                f"❌ Cupom *{code}* inválido ou expirado.",
                parse_mode='Markdown',
                reply_markup=Keyboards.back_to_menu()
            )
            return
        
        # Aplicar ao carrinho
        db_user = session.query(User).filter_by(telegram_id=user.id).first()
        cart = session.query(Cart).filter_by(user_id=db_user.id).first()
        
        if cart:
            cart.coupon_code = code
        
        discount_type = "porcentagem" if coupon.discount_type.value == 'percentage' else "valor fixo"
        
        await update.message.reply_text(
            f"""
✅ *CUPOM APLICADO!*

Código: *{code}*
Desconto: {discount_type}
Valor: {coupon.discount_value}{'%' if coupon.discount_type.value == 'percentage' else 'R$'}

O desconto será aplicado no checkout!
            """,
            parse_mode='Markdown',
            reply_markup=Keyboards.back_to_menu()
        )
    
    context.user_data['awaiting'] = None


async def cart_callback_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Roteador de callbacks do carrinho"""
    query = update.callback_query
    data = query.data
    
    if data == "menu_cart":
        await show_cart(update, context)
    
    elif data == "cart_coupon":
        await apply_coupon_handler(update, context)
    
    elif data == "cart_clear":
        await clear_cart_handler(update, context)
    
    elif data == "cart_checkout":
        from handlers.checkout import start_checkout
        await start_checkout(update, context)
    
    elif data.startswith("cart_remove_"):
        await remove_from_cart_handler(update, context)
    
    elif data.startswith("add_to_cart_"):
        await add_to_cart_handler(update, context)


# Handler para mensagens de cupom
async def cart_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler de mensagens para carrinho"""
    if context.user_data.get('awaiting') == 'coupon_code':
        await process_coupon(update, context)
