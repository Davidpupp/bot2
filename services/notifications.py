"""
Notification Service
Envio de notificações para usuários e admins
"""

from typing import Optional, List
from telegram import Bot

from app.config import config
from app.database import db
from app.models import User, Order, Payment
from utils.logger import logger
from utils.helpers import format_currency, format_datetime


class NotificationService:
    """Serviço de notificações"""
    
    def __init__(self):
        self.bot: Optional[Bot] = None
    
    def set_bot(self, bot: Bot):
        """Define instância do bot"""
        self.bot = bot
    
    async def notify_user(self, telegram_id: int, message: str, parse_mode: str = 'Markdown'):
        """Envia notificação para usuário"""
        if not self.bot:
            return
        
        try:
            await self.bot.send_message(
                chat_id=telegram_id,
                text=message,
                parse_mode=parse_mode
            )
        except Exception as e:
            logger.error(f"Erro ao notificar usuário {telegram_id}: {e}")
    
    async def notify_admin(self, message: str, parse_mode: str = 'Markdown'):
        """Envia notificação para admin master"""
        if not self.bot or not config.ADMIN_TELEGRAM_ID:
            return
        
        try:
            await self.bot.send_message(
                chat_id=config.ADMIN_TELEGRAM_ID,
                text=f"🔔 *NOTIFICAÇÃO ADMIN*\n\n{message}",
                parse_mode=parse_mode
            )
        except Exception as e:
            logger.error(f"Erro ao notificar admin: {e}")
    
    async def notify_channel(self, channel_id: str, message: str, parse_mode: str = 'Markdown'):
        """Envia notificação para canal"""
        if not self.bot or not channel_id:
            return
        
        try:
            await self.bot.send_message(
                chat_id=channel_id,
                text=message,
                parse_mode=parse_mode
            )
        except Exception as e:
            logger.error(f"Erro ao notificar canal: {e}")
    
    # ============================================
    # NOTIFICAÇÕES ESPECÍFICAS
    # ============================================
    
    async def order_created(self, order_id: int):
        """Notifica criação de pedido"""
        with db.get_session() as session:
            order = session.query(Order).get(order_id)
            if not order:
                return
            
            user = order.user
            
            message = f"""
🛒 *PEDIDO CRIADO*

Número: `#{order.order_number}`
Valor: {format_currency(order.total)}
Status: ⏳ Aguardando pagamento

Para pagar, acesse seus pedidos ou clique em *Pagar Agora*.
"""
            
            await self.notify_user(user.telegram_id, message)
    
    async def payment_pending(self, payment_id: int):
        """Notifica PIX gerado"""
        with db.get_session() as session:
            payment = session.query(Payment).get(payment_id)
            if not payment:
                return
            
            user = payment.order.user
            
            message = f"""
💳 *PIX GERADO*

Pedido: `#{payment.order.order_number}`
Valor: {format_currency(payment.amount)}

O QR Code foi enviado acima. 
Escaneie ou use o código copia e cola para pagar.

⏰ Válido por {config.PIX_EXPIRATION} minutos
"""
            
            await self.notify_user(user.telegram_id, message)
    
    async def payment_approved(self, payment_id: int):
        """Notifica pagamento aprovado"""
        with db.get_session() as session:
            payment = session.query(Payment).get(payment_id)
            if not payment:
                return
            
            order = payment.order
            user = order.user
            
            message = f"""
✅ *PAGAMENTO APROVADO*

Pedido: `#{order.order_number}`
Valor: {format_currency(payment.paid_amount or payment.amount)}

🎉 Seu pagamento foi confirmado!

Em breve você receberá seu produto.
Acompanhe em 📦 Meus Pedidos
"""
            
            await self.notify_user(user.telegram_id, message)
            
            # Notificar admin
            await self.notify_admin(
                f"💰 *VENDA REALIZADA*\n\n"
                f"Cliente: {user.full_name}\n"
                f"Pedido: #{order.order_number}\n"
                f"Valor: {format_currency(payment.amount)}"
            )
    
    async def order_delivered(self, order_id: int):
        """Notifica entrega do pedido"""
        with db.get_session() as session:
            order = session.query(Order).get(order_id)
            if not order:
                return
            
            user = order.user
            
            message = f"""
📦 *PEDIDO ENTREGUE*

Pedido: `#{order.order_number}`
Entregue em: {format_datetime(order.delivered_at)}

✅ Seu produto foi entregue!
Confira acima ⬆️

Agradecemos a preferência! 🎉
"""
            
            await self.notify_user(user.telegram_id, message)
    
    async def order_cancelled(self, order_id: int, reason: str = ""):
        """Notifica cancelamento"""
        with db.get_session() as session:
            order = session.query(Order).get(order_id)
            if not order:
                return
            
            user = order.user
            
            message = f"""
❌ *PEDIDO CANCELADO*

Pedido: `#{order.order_number}`
Motivo: {reason or 'Cancelado a pedido do cliente'}

Se precisar de ajuda, contate o suporte.
"""
            
            await self.notify_user(user.telegram_id, message)
    
    async def cart_abandoned(self, user_id: int, cart_items: int):
        """Notifica carrinho abandonado"""
        with db.get_session() as session:
            user = session.query(User).get(user_id)
            if not user:
                return
            
            message = f"""
🛒 *CARRINHO AGUARDANDO*

Você tem {cart_items} item(s) no carrinho esperando!

Volte e finalize sua compra:
💎 Produtos exclusivos
🔒 Pagamento seguro
⚡ Entrega instantânea

Clique em /carrinho para continuar
"""
            
            await self.notify_user(user.telegram_id, message)
    
    async def affiliate_sale(self, affiliate_id: int, order_id: int, commission: float):
        """Notifica venda de afiliado"""
        with db.get_session() as session:
            affiliate = session.query(Affiliate).get(affiliate_id)
            if not affiliate:
                return
            
            order = session.query(Order).get(order_id)
            
            message = f"""
🎉 *NOVA COMISSÃO*

Venda realizada pela sua indicação!
💰 Comissão: {format_currency(commission)}

Total acumulado: {format_currency(affiliate.balance)}

Continue divulgando seu link! 🚀
"""
            
            await self.notify_user(affiliate.user.telegram_id, message)


# Instância global
notifications = NotificationService()
