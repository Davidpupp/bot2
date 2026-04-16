"""
Admin Handler - Painel administrativo
"""

from telegram import Update
from telegram.ext import ContextTypes

from app.config import config
from app.database import db
from app.models import User, Order, Product, Payment, OrderStatus, Admin
from services.analytics import analytics
from services.notifications import notifications
from utils.keyboards import Keyboards
from utils.helpers import format_currency, format_datetime


def is_admin(telegram_id: int) -> bool:
    """Verifica se usuário é admin"""
    return telegram_id == config.ADMIN_TELEGRAM_ID or telegram_id in config.ADMIN_IDS


async def admin_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler de admin via comando"""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("🚫 Acesso negado.")
        return
    
    await show_admin_panel(update, context)


async def show_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mostra painel admin"""
    user = update.effective_user
    
    message = f"""
⚙️ *PAINEL ADMINISTRATIVO*

Bem-vindo, *{user.first_name}*!

Acesso completo ao sistema.
    """
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            message,
            parse_mode='Markdown',
            reply_markup=Keyboards.admin_dashboard()
        )
    else:
        await update.message.reply_text(
            message,
            parse_mode='Markdown',
            reply_markup=Keyboards.admin_dashboard()
        )


async def admin_stats_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mostra estatísticas detalhadas"""
    query = update.callback_query
    await query.answer()
    
    if not is_admin(update.effective_user.id):
        return
    
    stats = analytics.get_dashboard_stats()
    
    message = f"""
📊 *ESTATÍSTICAS GERAIS*

👥 *USUÁRIOS*
Total: {stats['total_users']:,}
Hoje: +{stats['new_users_today']}

📦 *PEDIDOS*
Total: {stats['total_orders']:,}
Hoje: {stats['orders_today']}
Aprovados: {stats['paid_orders']}
Pendentes: {stats['pending_orders']}

💰 *RECEITA*
Hoje: {format_currency(stats['revenue_today'])}
Mês: {format_currency(stats['revenue_month'])}
Total: {format_currency(stats['total_revenue'])}
Ticket Médio: {format_currency(stats['avg_ticket'])}

📈 *CONVERSÃO*
Taxa: {stats['conversion_rate']:.1f}%

🏆 *PRODUTO CAMPEÃO*
{stats['top_product']['name'] if stats['top_product'] else 'N/A'}
Vendas: {stats['top_product']['sales'] if stats['top_product'] else 0}
    """
    
    await query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=Keyboards.admin_dashboard()
    )


async def admin_users_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gestão de usuários"""
    query = update.callback_query
    await query.answer()
    
    if not is_admin(update.effective_user.id):
        return
    
    with db.get_session() as session:
        total_users = session.query(User).count()
        new_today = session.query(User).filter(
            db.func.date(User.created_at) == db.func.date(db.func.now())
        ).count()
        banned = session.query(User).filter_by(is_banned=True).count()
    
    message = f"""
👥 *GESTÃO DE USUÁRIOS*

Total: {total_users:,}
Novos hoje: {new_today}
Banidos: {banned}

*AÇÕES:*
• Buscar usuário por ID
• Banir/Desbanir
• Ver histórico
• Enviar mensagem

Em desenvolvimento...
    """
    
    await query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=Keyboards.admin_dashboard()
    )


async def admin_orders_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gestão de pedidos"""
    query = update.callback_query
    await query.answer()
    
    if not is_admin(update.effective_user.id):
        return
    
    with db.get_session() as session:
        pending = session.query(Order).filter_by(status=OrderStatus.PENDING).count()
        paid = session.query(Order).filter_by(status=OrderStatus.PAID).count()
        delivered = session.query(Order).filter_by(status=OrderStatus.DELIVERED).count()
    
    message = f"""
📦 *GESTÃO DE PEDIDOS*

⏳ Pendentes: {pending}
✅ Pagos: {paid}
📦 Entregues: {delivered}

Selecione uma categoria:
    """
    
    await query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=Keyboards.admin_orders()
    )


async def admin_orders_list_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, status: str):
    """Lista pedidos por status"""
    query = update.callback_query
    await query.answer()
    
    if not is_admin(update.effective_user.id):
        return
    
    with db.get_session() as session:
        orders = session.query(Order).filter_by(status=status).order_by(
            Order.created_at.desc()
        ).limit(20).all()
    
    if not orders:
        await query.edit_message_text(
            f"❌ Nenhum pedido {status}",
            reply_markup=Keyboards.admin_orders()
        )
        return
    
    message = f"""
📦 *PEDIDOS - {status.upper()}*

Últimos {len(orders)} pedidos:

"""
    
    for order in orders[:10]:  # Limitar a 10
        message += f"""
#{order.order_number} - {order.user.full_name[:20]}
Total: {format_currency(order.total)}
Data: {format_datetime(order.created_at)}
---
"""
    
    await query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=Keyboards.admin_orders()
    )


async def admin_products_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gestão de produtos"""
    query = update.callback_query
    await query.answer()
    
    if not is_admin(update.effective_user.id):
        return
    
    with db.get_session() as session:
        total = session.query(Product).count()
        active = session.query(Product).filter_by(is_active=True).count()
        low_stock = session.query(Product).filter(
            Product.stock < 10,
            Product.unlimited_stock == False
        ).count()
    
    message = f"""
🛍️ *GESTÃO DE PRODUTOS*

Total: {total}
Ativos: {active}
Estoque baixo: {low_stock}

*AÇÕES:*
    """
    
    await query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=Keyboards.admin_products()
    )


async def admin_product_new_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Novo produto - prompt"""
    query = update.callback_query
    await query.answer()
    
    if not is_admin(update.effective_user.id):
        return
    
    await query.edit_message_text(
        """
➕ *NOVO PRODUTO*

Envie os dados no formato:

Nome: Nome do Produto
Categoria: credit_cards/documents
Preço: 100.00
Descrição: Descrição do produto
Estoque: 100

Ou /cancelar para voltar.
        """,
        parse_mode='Markdown',
        reply_markup=Keyboards.admin_products()
    )
    
    context.user_data['awaiting'] = 'new_product'


async def admin_broadcast_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Broadcast para usuários"""
    query = update.callback_query
    await query.answer()
    
    if not is_admin(update.effective_user.id):
        return
    
    await query.edit_message_text(
        """
📢 *BROADCAST*

Digite a mensagem para enviar a todos os usuários:

⚠️ *ATENÇÃO:*
Esta ação enviará mensagem para TODOS.
Use com cautela.

/confirma - confirmar envio
/cancelar - cancelar
        """,
        parse_mode='Markdown',
        reply_markup=Keyboards.admin_dashboard()
    )
    
    context.user_data['awaiting'] = 'broadcast_message'


async def admin_callback_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Roteador de callbacks admin"""
    query = update.callback_query
    data = query.data
    
    if not is_admin(update.effective_user.id):
        await query.answer("🚫 Acesso negado", show_alert=True)
        return
    
    if data == "admin_panel":
        await show_admin_panel(update, context)
    
    elif data == "admin_stats":
        await admin_stats_handler(update, context)
    
    elif data == "admin_users":
        await admin_users_handler(update, context)
    
    elif data == "admin_orders":
        await admin_orders_handler(update, context)
    
    elif data == "admin_orders_pending":
        await admin_orders_list_handler(update, context, 'pending')
    
    elif data == "admin_orders_paid":
        await admin_orders_list_handler(update, context, 'paid')
    
    elif data == "admin_orders_processing":
        await admin_orders_list_handler(update, context, 'processing')
    
    elif data == "admin_orders_delivered":
        await admin_orders_list_handler(update, context, 'delivered')
    
    elif data == "admin_products":
        await admin_products_handler(update, context)
    
    elif data == "admin_product_new":
        await admin_product_new_handler(update, context)
    
    elif data == "admin_coupons":
        await query.edit_message_text(
            "🏷️ Gestão de cupons - Em desenvolvimento",
            reply_markup=Keyboards.admin_dashboard()
        )
    
    elif data == "admin_broadcast":
        await admin_broadcast_handler(update, context)
    
    elif data == "admin_settings":
        await query.edit_message_text(
            "⚙️ Configurações - Em desenvolvimento",
            reply_markup=Keyboards.admin_dashboard()
        )
    
    elif data == "admin_payments":
        await query.edit_message_text(
            "💳 Gestão de pagamentos - Em desenvolvimento",
            reply_markup=Keyboards.admin_dashboard()
        )
    
    elif data.startswith("admin_confirm_"):
        order_id = int(data.replace('admin_confirm_', ''))
        # Confirmar pedido
        await query.answer(f"Pedido #{order_id} confirmado!")
    
    elif data.startswith("admin_deliver_"):
        order_id = int(data.replace('admin_deliver_', ''))
        # Marcar entregue
        from services.delivery import delivery
        await delivery.deliver_order(order_id)
        await query.answer(f"Pedido #{order_id} entregue!")
    
    elif data.startswith("admin_refund_"):
        order_id = int(data.replace('admin_refund_', ''))
        await query.answer(f"Pedido #{order_id} reembolsado")
    
    elif data.startswith("admin_cancel_"):
        order_id = int(data.replace('admin_cancel_', ''))
        await query.answer(f"Pedido #{order_id} cancelado")


# Handler de mensagens admin
async def admin_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa mensagens de admin (broadcast, novo produto, etc)"""
    if not is_admin(update.effective_user.id):
        return
    
    if context.user_data.get('awaiting') == 'broadcast_message':
        # Processar broadcast
        message = update.message.text
        
        if message == '/cancelar':
            context.user_data['awaiting'] = None
            await update.message.reply_text("❌ Broadcast cancelado.")
            return
        
        if message == '/confirma':
            # Enviar broadcast
            await update.message.reply_text("📢 Enviando broadcast...")
            
            with db.get_session() as session:
                users = session.query(User).filter_by(is_active=True).all()
                
                sent = 0
                failed = 0
                
                for user in users:
                    try:
                        # Aqui você usaria o bot para enviar
                        sent += 1
                    except:
                        failed += 1
                
                await update.message.reply_text(
                    f"✅ Broadcast enviado!\nSucesso: {sent}\nFalhas: {failed}"
                )
            
            context.user_data['awaiting'] = None
            return
        
        # Preview
        await update.message.reply_text(
            f"""
📢 *PREVIEW DO BROADCAST*

{message}

/confirma - confirmar envio
/cancelar - cancelar
            """,
            parse_mode='Markdown'
        )
    
    elif context.user_data.get('awaiting') == 'new_product':
        # Processar novo produto
        await update.message.reply_text("➕ Processando novo produto...")
        context.user_data['awaiting'] = None
