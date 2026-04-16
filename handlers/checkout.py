"""
Checkout Handler - Finalização de compra e pagamentos
"""

import base64
from io import BytesIO
from datetime import datetime
from decimal import Decimal

from telegram import Update, InputFile
from telegram.ext import ContextTypes

from app.config import config
from app.database import db
from app.models import (
    Order, OrderItem, Payment, PaymentStatus, PaymentMethod,
    Cart, Product, User, OrderStatus, Coupon, DiscountType
)
from services.sillientpay import sillientpay
from services.notifications import notifications
from services.delivery import delivery
from utils.keyboards import Keyboards
from utils.helpers import format_currency, calculate_discount
from utils.logger import logger, log_order_event, log_payment_event


async def checkout_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler de checkout via comando"""
    await start_checkout(update, context)


async def start_checkout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Inicia processo de checkout"""
    user = update.effective_user
    
    with db.get_session() as session:
        db_user = session.query(User).filter_by(telegram_id=user.id).first()
        
        if db_user is None:
            message = "❌ Você precisa iniciar o bot primeiro.\nUse /start"
            if update.callback_query:
                await update.callback_query.edit_message_text(message)
            else:
                await update.message.reply_text(message)
            return
        
        cart = session.query(Cart).filter_by(user_id=db_user.id).first()
        
        if cart is None or not cart.items:
            message = f"""
🛒 *CARRINHO VAZIO*

Adicione produtos antes de finalizar a compra.
            """
            if update.callback_query:
                await update.callback_query.edit_message_text(
                    message,
                    parse_mode='Markdown',
                    reply_markup=Keyboards.cart_empty()
                )
            return
        
        # Calcular totais
        cart_items = cart.items if isinstance(cart.items, list) else []
        
        if not cart_items:
            message = "❌ Erro ao processar carrinho."
            if update.callback_query:
                await update.callback_query.edit_message_text(message)
            return
        
        # Validar produtos
        valid_items = []
        subtotal = Decimal('0')
        
        for item in cart_items:
            product = session.query(Product).get(item['product_id'])
            if product and product.is_active and product.has_stock:
                quantity = item.get('quantity', 1)
                item_subtotal = Decimal(str(product.price)) * quantity
                
                valid_items.append({
                    'product': product,
                    'quantity': quantity,
                    'subtotal': item_subtotal
                })
                
                subtotal += item_subtotal
        
        if not valid_items:
            message = "❌ Os produtos do seu carrinho não estão mais disponíveis."
            if update.callback_query:
                await update.callback_query.edit_message_text(
                    message,
                    reply_markup=Keyboards.back_to_menu()
                )
            return
        
        # Aplicar cupom se houver
        discount = Decimal('0')
        if cart.coupon_code:
            coupon = session.query(Coupon).filter_by(code=cart.coupon_code).first()
            if coupon is not None and coupon.is_valid:
                discount = Decimal(str(coupon.calculate_discount(float(subtotal))))
        
        total = subtotal - discount
        
        # Criar pedido
        order = Order(
            user_id=db_user.id,
            subtotal=subtotal,
            discount=discount,
            discount_code=cart.coupon_code,
            total=total,
            status=OrderStatus.PENDING
        )
        
        session.add(order)
        session.flush()
        
        # Criar itens do pedido
        for item in valid_items:
            order_item = OrderItem(
                order_id=order.id,
                product_id=item['product'].id,
                product_name=item['product'].name,
                product_price=item['product'].price,
                quantity=item['quantity']
            )
            session.add(order_item)
        
        # Guardar order_id no context
        context.user_data['current_order_id'] = order.id
    
    # Mensagem de checkout
    discount_text = ""
    if discount > 0:
        discount_text = f"🏷️ Desconto: -{format_currency(discount)}\n"
    
    items_text = "\n".join([
        f"• {item['product'].name} x{item['quantity']} = {format_currency(item['subtotal'])}"
        for item in valid_items
    ])
    
    message = f"""
💳 *CHECKOUT*

Pedido: `#{order.order_number}`

{items_text}

Subtotal: {format_currency(subtotal)}
{discount_text}💰 *Total: {format_currency(total)}*

Escolha a forma de pagamento:
    """
    
    keyboard = Keyboards.checkout(order.id, bool(discount > 0))
    
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


async def checkout_callback_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Roteador de callbacks de checkout"""
    query = update.callback_query
    data = query.data
    
    if data.startswith("checkout_pix_"):
        order_id = int(data.replace('checkout_pix_', ''))
        await process_pix_payment(update, context, order_id)
    
    elif data.startswith("checkout_coupon_"):
        from handlers.cart import apply_coupon_handler
        await apply_coupon_handler(update, context)
    
    elif data.startswith("cancel_order_"):
        order_id = int(data.replace('cancel_order_', ''))
        await cancel_order(update, context, order_id)
    
    elif data.startswith("buy_now_"):
        product_id = int(data.replace('buy_now_', ''))
        await buy_now(update, context, product_id)
    
    elif data.startswith("pix_"):
        await pix_callback_router(update, context)


async def process_pix_payment(update: Update, context: ContextTypes.DEFAULT_TYPE, order_id: int):
    """Processa pagamento PIX"""
    query = update.callback_query
    await query.answer("⏳ Gerando cobrança PIX...")
    
    with db.get_session() as session:
        order = session.query(Order).get(order_id)
        
        if not order or order.status != OrderStatus.PENDING:
            await query.edit_message_text(
                "❌ Pedido não encontrado ou já processado.",
                reply_markup=Keyboards.back_to_menu()
            )
            return
        
        user = order.user
        
        # Verificar se já existe pagamento
        existing_payment = session.query(Payment).filter_by(
            order_id=order_id,
            status=PaymentStatus.PENDING
        ).first()
        
        if existing_payment:
            # Mostrar pagamento existente
            await show_pix_payment(update, context, existing_payment)
            return
        
        # Criar pagamento na SillientPay
        customer = {
            'name': user.full_name,
            'email': user.email or f"cliente{user.telegram_id}@email.com",
            'cpf': '00000000000'  # Placeholder - idealmente coletar do usuário
        }
        
        pix_data = await sillientpay.create_pix_payment(
            amount=order.total,
            description=f"Pedido #{order.order_number} - {config.BOT_NAME}",
            order_id=str(order.id),
            customer=customer
        )
        
        if not pix_data:
            await query.edit_message_text(
                "❌ Erro ao gerar PIX. Tente novamente.",
                reply_markup=Keyboards.back_to_menu()
            )
            return
        
        # Salvar pagamento no banco
        payment = Payment(
            order_id=order_id,
            external_id=pix_data['payment_id'],
            method=PaymentMethod.PIX,
            status=PaymentStatus.PENDING,
            amount=order.total,
            pix_qr_code=pix_data.get('qr_code_base64') or pix_data.get('qr_code'),
            pix_copy_paste=pix_data['copy_paste'],
            pix_expiration=pix_data['expiration'],
            gateway_response=pix_data['raw_response']
        )
        
        session.add(payment)
        session.commit()
    
    log_payment_event(f"PIX criado: {payment.external_id}", order_id=order_id)
    
    # Mostrar pagamento
    await show_pix_payment(update, context, payment)


async def show_pix_payment(update: Update, context: ContextTypes.DEFAULT_TYPE, payment):
    """Mostra QR code e código PIX"""
    query = update.callback_query
    
    time_left = payment.pix_expiration - datetime.utcnow()
    minutes_left = max(0, int(time_left.total_seconds() / 60))
    
    message = f"""
💳 *PAGAMENTO PIX*

💰 Valor: `{format_currency(payment.amount)}`
⏰ Expira em: {minutes_left} minutos

*CÓDIGO COPIA E COLA:*

`{payment.pix_copy_paste[:60]}...`

⚡ O pagamento será detectado automaticamente
🔔 Você receberá confirmação aqui mesmo
    """
    
    keyboard = Keyboards.payment_pix(payment.id, payment.pix_copy_paste)
    
    # Enviar QR code se disponível
    if payment.pix_qr_code is not None and payment.pix_qr_code != '':
        try:
            # Se é base64, decodificar
            if ',' in payment.pix_qr_code:
                qr_data = payment.pix_qr_code.split(',')[1]
                qr_bytes = base64.b64decode(qr_data)
                
                await query.message.delete()
                
                await query.message.reply_photo(
                    photo=InputFile(BytesIO(qr_bytes), filename='pix_qr.png'),
                    caption=message,
                    parse_mode='Markdown',
                    reply_markup=keyboard
                )
                return
        except Exception as e:
            logger.error(f"Erro ao enviar QR: {e}")
    
    # Fallback para mensagem texto
    await query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=keyboard
    )


async def pix_callback_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Roteia callbacks de PIX"""
    query = update.callback_query
    data = query.data
    
    if data.startswith("pix_check_"):
        payment_id = int(data.replace('pix_check_', ''))
        await check_pix_status(update, context, payment_id)
    
    elif data.startswith("pix_copy_"):
        payment_id = int(data.replace('pix_copy_', ''))
        await copy_pix_code(update, context, payment_id)
    
    elif data.startswith("pix_regenerate_"):
        payment_id = int(data.replace('pix_regenerate_', ''))
        await regenerate_pix(update, context, payment_id)
    
    elif data.startswith("pix_cancel_"):
        payment_id = int(data.replace('pix_cancel_', ''))
        await cancel_pix_payment(update, context, payment_id)


async def check_pix_status(update: Update, context: ContextTypes.DEFAULT_TYPE, payment_id: int):
    """Verifica status do PIX"""
    query = update.callback_query
    await query.answer("⏳ Verificando pagamento...")
    
    with db.get_session() as session:
        payment = session.query(Payment).get(payment_id)
        
        if not payment:
            await query.answer("❌ Pagamento não encontrado", show_alert=True)
            return
        
        # Verificar na API
        status_data = await sillientpay.check_payment_status(payment.external_id)
        
        if status_data:
            # Atualizar status
            old_status = payment.status
            
            if status_data['status'] == 'approved':
                payment.status = PaymentStatus.APPROVED
                payment.paid_amount = Decimal(str(status_data.get('paid_amount', payment.amount)))
                payment.paid_at = datetime.utcnow()
                
                # Atualizar pedido
                order = payment.order
                order.status = OrderStatus.PAID
                order.paid_at = datetime.utcnow()
                
                # Atualizar estatísticas do usuário
                user = order.user
                user.total_orders += 1
                user.total_spent += order.total
                
                # Diminuir estoque
                for item in order.items:
                    item.product.decrease_stock(item.quantity)
                
                session.commit()
                
                # Notificar
                await notifications.payment_approved(payment_id)
                
                # Entregar produto
                await delivery.deliver_order(order.id)
                
                # Mostrar sucesso
                await query.edit_message_text(
                    f"""
✅ *PAGAMENTO CONFIRMADO!*

Pedido: `#{order.order_number}`
Valor: {format_currency(payment.paid_amount or payment.amount)}

🎉 Seu pagamento foi aprovado!

Entregue em breve. 📦
                    """,
                    parse_mode='Markdown',
                    reply_markup=Keyboards.payment_success(order.id)
                )
                return
            
            elif status_data['status'] == 'expired':
                payment.status = PaymentStatus.EXPIRED
                session.commit()
                
                await query.answer("⏰ PIX expirado. Gere um novo.", show_alert=True)
                return
        
        # Ainda pendente
        await query.answer(
            "⏳ Pagamento ainda pendente.\nAguarde alguns instantes.",
            show_alert=True
        )


async def copy_pix_code(update: Update, context: ContextTypes.DEFAULT_TYPE, payment_id: int):
    """Copia código PIX"""
    query = update.callback_query
    
    with db.get_session() as session:
        payment = session.query(Payment).get(payment_id)
        
        if payment is not None and payment.pix_copy_paste:
            # Enviar código em mensagem separada para facilitar cópia
            await query.message.reply_text(
                f"`{payment.pix_copy_paste}`",
                parse_mode='Markdown'
            )
            await query.answer("📋 Código enviado acima!")


async def regenerate_pix(update: Update, context: ContextTypes.DEFAULT_TYPE, payment_id: int):
    """Regenera PIX expirado"""
    query = update.callback_query
    await query.answer("🔄 Gerando novo PIX...")
    
    with db.get_session() as session:
        payment = session.query(Payment).get(payment_id)
        
        if not payment:
            return
        
        order = payment.order
        
        # Cancelar pagamento antigo
        await sillientpay.cancel_payment(payment.external_id)
        payment.status = PaymentStatus.CANCELLED
        
        session.commit()
        
        # Criar novo
        await process_pix_payment(update, context, order.id)


async def cancel_pix_payment(update: Update, context: ContextTypes.DEFAULT_TYPE, payment_id: int):
    """Cancela pagamento PIX"""
    query = update.callback_query
    await query.answer()
    
    with db.get_session() as session:
        payment = session.query(Payment).get(payment_id)
        
        if payment is not None:
            await sillientpay.cancel_payment(payment.external_id)
            payment.status = PaymentStatus.CANCELLED
            
            order = payment.order
            order.status = OrderStatus.CANCELLED
            
            session.commit()
    
    await query.edit_message_text(
        "❌ Pagamento cancelado.",
        reply_markup=Keyboards.back_to_menu()
    )


async def cancel_order(update: Update, context: ContextTypes.DEFAULT_TYPE, order_id: int):
    """Cancela pedido"""
    query = update.callback_query
    await query.answer()
    
    with db.get_session() as session:
        order = session.query(Order).get(order_id)
        
        if order is not None and order.status == OrderStatus.PENDING:
            order.status = OrderStatus.CANCELLED
            session.commit()
            
            await notifications.order_cancelled(order_id, "Cancelado pelo cliente")
    
    await query.edit_message_text(
        "❌ Pedido cancelado.",
        reply_markup=Keyboards.back_to_menu()
    )


async def buy_now(update: Update, context: ContextTypes.DEFAULT_TYPE, product_id: int):
    """Compra direta de produto (buy now)"""
    query = update.callback_query
    await query.answer("🛒 Adicionando ao carrinho...")
    
    user = update.effective_user
    
    with db.get_session() as session:
        db_user = session.query(User).filter_by(telegram_id=user.id).first()
        
        if db_user is None:
            return
        
        # Limpar carrinho atual
        cart = session.query(Cart).filter_by(user_id=db_user.id).first()
        if cart:
            cart.clear()
            cart.add_item(product_id, 1)
        else:
            cart = Cart(user_id=db_user.id, items=[{
                'product_id': product_id,
                'quantity': 1,
                'added_at': datetime.utcnow().isoformat()
            }])
            session.add(cart)
        
        session.commit()
    
    # Ir direto para checkout
    await start_checkout(update, context)


# Webhook handler
async def handle_sillientpay_webhook(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa webhook da SillientPay"""
    # Esta função seria chamada via endpoint web
    # Implementação simplificada
    pass
