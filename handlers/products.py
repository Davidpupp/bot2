"""
Products Handler - Catálogo e produtos
"""

from telegram import Update
from telegram.ext import ContextTypes

from app.config import config
from app.database import db
from app.models import Product, Cart, User
from utils.keyboards import Keyboards
from utils.helpers import format_currency
from utils.logger import logger


async def products_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler de produtos via comando"""
    await show_categories(update, context)


async def show_categories(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mostra menu de categorias"""
    query = update.callback_query
    
    message = f"""
🛍️ *CATÁLOGO DE PRODUTOS*

Escolha uma categoria:

💳 *CARTÕES DE CRÉDITO*
Produtos premium de alta qualidade

📄 *DOCUMENTOS*
Comprovantes e documentos

👑 *ÁREA VIP*
Produtos exclusivos para membros
    """
    
    await query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=Keyboards.categories()
    )


async def category_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler de categoria específica"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    # Extrair categoria do callback
    if data.startswith('category_'):
        category = data.replace('category_', '')
        await show_products_by_category(update, context, category)


async def show_products_by_category(update: Update, context: ContextTypes.DEFAULT_TYPE, category: str, page: int = 1):
    """Mostra produtos de uma categoria"""
    query = update.callback_query
    
    with db.get_session() as session:
        # Buscar produtos
        products_query = session.query(Product).filter_by(
            category=category,
            is_active=True
        )
        
        # Se não for VIP, esconder produtos VIP
        user = session.query(User).filter_by(
            telegram_id=update.effective_user.id
        ).first()
        
        is_vip = user is not None and user.level.value in ['vip', 'admin', 'master']
        
        if not is_vip:
            products_query = products_query.filter_by(is_vip=False)
        
        products = products_query.all()
        
        # Preparar dados
        products_data = [
            {
                'id': p.id,
                'name': p.name,
                'category': p.category,
                'price': float(p.price),
                'is_vip': p.is_vip,
                'stock': p.stock if not p.unlimited_stock else None
            }
            for p in products
        ]
    
    # Categoria info
    category_info = config.CATEGORIES.get(category, {
        'name': category,
        'emoji': '📦'
    })
    
    message = f"""
{category_info['emoji']} *{category_info['name']}*

{category_info['description']}

*Produtos disponíveis:*
    """
    
    if not products_data:
        message += "\n\n_Nenhum produto disponível no momento._"
        keyboard = Keyboards.back_to_menu()
    else:
        keyboard = Keyboards.product_list(products_data, category, page)
    
    await query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=keyboard
    )


async def product_detail_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mostra detalhes de um produto"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if not data.startswith('product_'):
        return
    
    try:
        product_id = int(data.replace('product_', ''))
    except ValueError:
        return
    
    with db.get_session() as session:
        product = session.query(Product).get(product_id)
        
        if not product or not product.is_active:
            await query.edit_message_text(
                "❌ Produto não encontrado ou indisponível.",
                reply_markup=Keyboards.back_to_menu()
            )
            return
        
        # Verificar se está no carrinho
        user = session.query(User).filter_by(
            telegram_id=update.effective_user.id
        ).first()
        
        in_cart = False
        if user is not None:
            cart = session.query(Cart).filter_by(user_id=user.id).first()
            if cart is not None and cart.items:
                cart_items = cart.items if isinstance(cart.items, list) else []
                in_cart = any(item.get('product_id') == product_id for item in cart_items)
        
        # Formatar mensagem
        price_text = format_currency(product.price)
        compare_text = format_currency(product.compare_price) if product.compare_price else ""
        
        discount_text = ""
        if product.compare_price and float(product.compare_price) > float(product.price):
            discount = int((1 - float(product.price) / float(product.compare_price)) * 100)
            discount_text = f"~~{compare_text}~~  *{discount}% OFF*\n"
        
        stock_text = ""
        if not product.unlimited_stock:
            if product.stock > 10:
                stock_text = f"✅ Em estoque ({product.stock} unidades)\n"
            elif product.stock > 0:
                stock_text = f"⚡ Apenas {product.stock} unidades restantes!\n"
            else:
                stock_text = "❌ Fora de estoque\n"
        
        vip_text = ""
        if product.is_vip:
            vip_text = "\n💎 *PRODUTO VIP EXCLUSIVO* 💎\n"
        
        message = f"""
{vip_text}
*{product.name}*

📝 *Descrição:*
{product.description or product.short_description or 'Produto premium de alta qualidade.'}

💰 *Preço:*
{discount_text}{price_text}

{stock_text}
🔥 *Produto de alta qualidade*
⚡ *Entrega instantânea*
🔒 *Pagamento 100% seguro*
        """.strip()
    
    # Enviar ou editar mensagem
    try:
        await query.edit_message_text(
            message,
            parse_mode='Markdown',
            reply_markup=Keyboards.product_detail(
                {'id': product_id, 'category': product.category},
                in_cart
            )
        )
    except Exception as e:
        # Se falhar (mensagem muito longa), enviar nova
        await query.message.reply_text(
            message,
            parse_mode='Markdown',
            reply_markup=Keyboards.product_detail(
                {'id': product_id, 'category': product.category},
                in_cart
            )
        )


async def products_callback_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Roteador de callbacks de produtos"""
    query = update.callback_query
    data = query.data
    
    if data == "menu_products":
        await show_categories(update, context)
    
    elif data == "search_product":
        await search_product_prompt(update, context)
    
    elif data.startswith("category_"):
        await category_handler(update, context)
    
    elif data.startswith("products_"):
        # Paginação de produtos
        parts = data.split('_')
        if len(parts) >= 4:
            category = parts[1]
            page = int(parts[3])
            await show_products_by_category(update, context, category, page)
    
    elif data.startswith("product_"):
        await product_detail_handler(update, context)
    
    elif data.startswith("share_product_"):
        await share_product(update, context)


async def search_product_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Prompt de busca de produto"""
    query = update.callback_query
    
    message = """
🔍 *BUSCAR PRODUTO*

Digite o nome ou parte do nome do produto que deseja encontrar:

Exemplos:
• "gold" - encontra Info CC Gold
• "platinum" - encontra Info CC Platinum
• "comprovante" - encontra Comprovante FK

Ou envie /cancelar para voltar.
    """
    
    await query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=Keyboards.back_to_menu()
    )
    
    # Definir estado de espera
    context.user_data['awaiting'] = 'search_product'


async def handle_product_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa busca de produto"""
    search_term = update.message.text.lower()
    
    with db.get_session() as session:
        products = session.query(Product).filter(
            Product.name.ilike(f'%{search_term}%'),
            Product.is_active == True
        ).all()
    
    if not products:
        await update.message.reply_text(
            f"❌ Nenhum produto encontrado para '{search_term}'",
            reply_markup=Keyboards.back_to_menu()
        )
        return
    
    message = f"""
🔍 *RESULTADOS PARA:* `{search_term}`

Encontrados {len(products)} produto(s):
    """
    
    # Mostrar resultados
    products_data = [
        {
            'id': p.id,
            'name': p.name,
            'category': p.category,
            'price': float(p.price)
        }
        for p in products[:10]  # Limitar a 10
    ]
    
    await update.message.reply_text(
        message,
        parse_mode='Markdown',
        reply_markup=Keyboards.product_list(products_data, 'search', 1)
    )


async def share_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Compartilha produto"""
    query = update.callback_query
    await query.answer()
    
    product_id = int(query.data.replace('share_product_', ''))
    
    # Criar mensagem de compartilhamento
    share_text = f"""
🎁 Olha este produto incrível!

Confira no {config.BOT_NAME}:
👉 @{config.BOT_USERNAME}

💎 Produtos premium com entrega instantânea!
    """
    
    await query.answer(
        "Link copiado! Compartilhe com amigos.",
        show_alert=True
    )


# Handler para mensagens de busca (quando em estado de espera)
async def products_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler de mensagens para produtos"""
    if context.user_data.get('awaiting') == 'search_product':
        await handle_product_search(update, context)
        context.user_data['awaiting'] = None
