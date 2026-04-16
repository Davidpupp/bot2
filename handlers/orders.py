"""
Orders Handler - Pedidos e entregas
"""

from telegram import Update
from telegram.ext import ContextTypes

from app.config import config
from app.database import db
from app.models import Order, OrderStatus, Payment, User
from utils.keyboards import Keyboards
from utils.helpers import format_currency, format_datetime


async def orders_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler de pedidos via comando"""
    await show_orders(update, context)


async def show_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mostra lista de pedidos do usuário"""
    user = update.effective_user
    
    with db.get_session() as session:
        db_user = session.query(User).filter_by(telegram_id=user.id).first()
        
        if not db_user:
            message = "❌ Você precisa iniciar o bot primeiro.\nUse /start"
            if update.callback_query:
                await update.callback_query.edit_message_text(message)
            else:
                await update.message.reply_text(message)
            return
        
        orders = session.query(Order).filter_by(user_id=db_user.id).order_by(
            Order.created_at.desc()
        ).all()
    
    if not orders:
        message = f"""
📦 *MEUS PEDIDOS*

Você ainda não fez nenhum pedido.

🛍️ Que tal explorar nossos produtos?
        """
        keyboard = Keyboards.back_to_menu()
    else:
        # Preparar dados
        orders_data = [
            {
                'id': o.id,
                'order_number': o.order_number,
                'status': o.status.value,
                'total': float(o.total)
            }
            for o in orders
        ]
        
        message = f"""
📦 *MEUS PEDIDOS*

Total de pedidos: {len(orders)}
        """
        
        keyboard = Keyboards.orders_list(orders_data)
    
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


async def order_detail_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mostra detalhes de um pedido"""
    query = update.callback_query
    await query.answer()
    
    order_id = int(query.data.replace('order_', ''))
    
    with db.get_session() as session:
        order = session.query(Order).get(order_id)
        
        if not order:
            await query.edit_message_text(
                "❌ Pedido não encontrado.",
                reply_markup=Keyboards.back_to_menu()
            )
            return
        
        # Status emoji
        status_emoji = {
            'pending': '⏳',
            'paid': '✅',
            'processing': '🔄',
            'delivered': '📦',
            'cancelled': '❌',
            'refunded': '↩️'
        }.get(order.status.value, '❓')
        
        # Itens
        items_text = "\n".join([
            f"• {item.product_name} x{item.quantity} - {format_currency(item.subtotal)}"
            for item in order.items
        ])
        
        # Pagamento
        payment = session.query(Payment).filter_by(order_id=order.id).first()
        payment_text = ""
        if payment:
            payment_method = {
                'pix': '💠 PIX',
                'credit_card': '💳 Cartão',
                'boleto': '📄 Boleto'
            }.get(payment.method.value, payment.method.value)
            
            payment_text = f"\n💳 Pagamento: {payment_method}"
            if payment.paid_at:
                payment_text += f"\n✅ Pago em: {format_datetime(payment.paid_at)}"
        
        # Mensagem
        message = f"""
📦 *PEDIDO #{order.order_number}*

{status_emoji} Status: {config.ORDER_STATUS.get(order.status.value, order.status.value)}

📝 *ITENS:*
{items_text}

💰 Subtotal: {format_currency(order.subtotal)}
        """
        
        if float(order.discount) > 0:
            message += f"\n🏷️ Desconto: -{format_currency(order.discount)}"
        
        message += f"""
💰 *Total: {format_currency(order.total)}*
{payment_text}

📅 Criado: {format_datetime(order.created_at)}
        """
        
        if order.delivered_at:
            message += f"\n📦 Entregue: {format_datetime(order.delivered_at)}"
    
    await query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=Keyboards.order_detail({
            'id': order.id,
            'status': order.status.value
        })
    )


async def order_pay_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para pagar pedido pendente"""
    query = update.callback_query
    await query.answer()
    
    order_id = int(query.data.replace('order_pay_', ''))
    
    # Redirecionar para checkout
    from handlers.checkout import process_pix_payment
    await process_pix_payment(update, context, order_id)


async def delivery_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mostra entrega do pedido"""
    query = update.callback_query
    await query.answer()
    
    order_id = int(query.data.replace('delivery_', ''))
    
    with db.get_session() as session:
        order = session.query(Order).get(order_id)
        
        if not order:
            await query.edit_message_text(
                "❌ Pedido não encontrado.",
                reply_markup=Keyboards.back_to_menu()
            )
            return
        
        if order.status != OrderStatus.DELIVERED:
            await query.edit_message_text(
                f"""
⏳ *AGUARDANDO ENTREGA*

Seu pedido está sendo processado.

Status atual: {config.ORDER_STATUS.get(order.status.value)}

Você será notificado quando estiver pronto!
                """,
                parse_mode='Markdown',
                reply_markup=Keyboards.back_to_menu()
            )
            return
        
        # Mostrar itens entregues
        items_text = "\n\n".join([
            f"✅ *{item.product_name}*\n\nProduto entregue com sucesso!"
            for item in order.items
        ])
        
        message = f"""
📦 *ENTREGA - PEDIDO #{order.order_number}*

{items_text}

🎉 Agradecemos a preferência!
        """
    
    await query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=Keyboards.back_to_menu()
    )


async def receipt_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Envia recibo do pedido"""
    query = update.callback_query
    await query.answer()
    
    order_id = int(query.data.replace('receipt_', ''))
    
    with db.get_session() as session:
        order = session.query(Order).get(order_id)
        payment = session.query(Payment).filter_by(order_id=order_id).first()
        
        if not order:
            await query.answer("❌ Pedido não encontrado", show_alert=True)
            return
        
        # Recibo simplificado
        receipt = f"""
📄 *RECIBO DE COMPRA*

{config.BOT_NAME}
CNPJ: 00.000.000/0001-00

--------------------------------
PEDIDO: #{order.order_number}
DATA: {format_datetime(order.created_at)}
--------------------------------

ITENS:
        """
        
        for item in order.items:
            receipt += f"\n{item.product_name}"
            receipt += f"\n{item.quantity}x R$ {float(item.product_price):.2f}"
            receipt += f"\nSubtotal: R$ {float(item.subtotal):.2f}\n"
        
        receipt += f"""
--------------------------------
SUBTOTAL: R$ {float(order.subtotal):.2f}
        """
        
        if float(order.discount) > 0:
            receipt += f"\nDESCONTO: -R$ {float(order.discount):.2f}"
        
        receipt += f"""
--------------------------------
TOTAL: R$ {float(order.total):.2f}
--------------------------------

PAGAMENTO: {payment.method.value.upper() if payment else 'N/A'}
STATUS: {order.status.value.upper()}

Obrigado pela preferência!
"""
    
    await query.message.reply_text(
        receipt,
        parse_mode='Markdown'
    )


async def orders_callback_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Roteador de callbacks de pedidos"""
    query = update.callback_query
    data = query.data
    
    if data == "menu_orders":
        await show_orders(update, context)
    
    elif data.startswith("order_"):
        if data.startswith("order_pay_"):
            await order_pay_handler(update, context)
        else:
            await order_detail_handler(update, context)
    
    elif data.startswith("delivery_"):
        await delivery_handler(update, context)
    
    elif data.startswith("receipt_"):
        await receipt_handler(update, context)
    
    elif data.startswith("support_order_"):
        order_id = int(data.replace('support_order_', ''))
        await query.answer(f"Contate @suporte com o Pedido #{order_id}", show_alert=True)
    
    elif data.startswith("orders_page_"):
        page = int(data.replace('orders_page_', ''))
        # Implementar paginação se necessário
        await show_orders(update, context)
