"""
Delivery Service
Sistema de entrega automática de produtos
"""

import os
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from telegram import Bot, InputFile, Update

from app.database import db
from app.models import Order, OrderStatus, User, Product
from utils.logger import logger


class DeliveryService:
    """Serviço de entrega automática de produtos"""
    
    def __init__(self):
        self.delivery_dir = Path('media/deliveries')
        self.delivery_dir.mkdir(parents=True, exist_ok=True)
    
    def set_bot(self, bot: Bot):
        """Define instância do bot"""
        self.bot = bot
    
    async def deliver_order(self, order_id: int) -> bool:
        """
        Realiza entrega automática do pedido
        
        Args:
            order_id: ID do pedido
        
        Returns:
            True se entregue com sucesso
        """
        with db.get_session() as session:
            order = session.query(Order).get(order_id)
            if not order:
                logger.error(f"Pedido não encontrado: {order_id}")
                return False
            
            user = order.user
            items = order.items.all()
            
            try:
                # Preparar mensagem de entrega
                delivery_message = self._prepare_delivery_message(order, items)
                
                # Enviar mensagem de entrega
                await self.bot.send_message(
                    chat_id=user.telegram_id,
                    text=delivery_message,
                    parse_mode='Markdown'
                )
                
                # Enviar arquivos/produtos
                for item in items:
                    await self._deliver_product(user.telegram_id, item.product)
                
                # Atualizar status
                order.status = OrderStatus.DELIVERED
                order.delivered_at = datetime.utcnow()
                
                # Notificar
                from services.notifications import notifications
                await notifications.order_delivered(order_id)
                
                logger.info(f"Pedido {order_id} entregue com sucesso")
                return True
                
            except Exception as e:
                logger.error(f"Erro ao entregar pedido {order_id}: {e}")
                return False
    
    def _prepare_delivery_message(self, order: Order, items: List[Any]) -> str:
        """Prepara mensagem de entrega"""
        from utils.helpers import format_currency, format_datetime
        
        products_text = "\n".join([
            f"✅ {item.product_name}" for item in items
        ])
        
        message = f"""
📦 *ENTREGA REALIZADA*

Pedido: `#{order.order_number}`

*Produtos entregues:*
{products_text}

💰 Valor pago: {format_currency(order.total)}
📅 Entrega: {format_datetime(datetime.utcnow())}

⚠️ *ATENÇÃO:*
Os produtos são para uso pessoal.
Não compartilhe seus dados.

Dúvidas? Use /suporte
"""
        return message.strip()
    
    async def _deliver_product(self, telegram_id: int, product: Product):
        """Entrega um produto específico"""
        
        # Entrega de CC Info (texto)
        if product.category == 'credit_cards':
            await self._deliver_credit_card(telegram_id, product)
        
        # Entrega de Documentos (arquivo)
        elif product.category == 'documents':
            await self._deliver_document(telegram_id, product)
        
        # Entrega genérica
        else:
            await self._deliver_generic(telegram_id, product)
    
    async def _deliver_credit_card(self, telegram_id: int, product: Product):
        """Entrega informações de cartão"""
        # Simulação - em produção viria de um sistema de estoque seguro
        delivery_info = self._generate_cc_info(product.name)
        
        message = f"""
💳 *{product.name}*

{delivery_info}

🔒 Guarde em local seguro
⚠️ Use com responsabilidade
"""
        await self.bot.send_message(
            chat_id=telegram_id,
            text=message,
            parse_mode='Markdown'
        )
    
    def _generate_cc_info(self, product_name: str) -> str:
        """Gera informações de cartão (SIMULAÇÃO - substituir por sistema real)"""
        import random
        
        # Números de cartão de teste (não reais)
        bins = {
            'Gold': ['4000', '5100', '3700'],
            'Platinum': ['4242', '5555', '3782'],
            'Infinite': ['6011', '4012', '3528'],
            'Basic': ['4111', '5105', '3400'],
            'Black': ['3787', '5550', '4000']
        }
        
        # Identificar tier do cartão
        tier = 'Basic'
        for key in bins.keys():
            if key in product_name:
                tier = key
                break
        
        bin_prefix = random.choice(bins.get(tier, bins['Basic']))
        
        # Gerar número fake para demonstração
        card_number = f"{bin_prefix} **** **** {random.randint(1000, 9999)}"
        
        return f"""
🏦 Banco: Itaú/Bradesco/Santander
💳 Número: `{card_number}`
📅 Validade: {random.randint(1, 12):02d}/{random.randint(24, 28)}
🔐 CVV: ***
👤 Titular: CLIENTE VIP

⚡ *Este é um exemplo de entrega*
Em produção, conecte ao seu fornecedor real.
"""
    
    async def _deliver_document(self, telegram_id: int, product: Product):
        """Entrega documento/arquivo"""
        if product.file_url:
            # Se tem URL de arquivo, enviar
            try:
                await self.bot.send_document(
                    chat_id=telegram_id,
                    document=product.file_url,
                    caption=f"📄 {product.name}"
                )
            except Exception as e:
                logger.error(f"Erro ao enviar documento: {e}")
                await self.bot.send_message(
                    chat_id=telegram_id,
                    text=f"📄 *{product.name}*\n\nArquivo disponível no painel."
                )
        else:
            # Documento como texto
            message = f"""
📄 *{product.name}*

Documento gerado com sucesso!

✅ Verificado
✅ Atualizado
✅ Pronto para uso

Consulte nosso suporte para mais detalhes.
"""
            await self.bot.send_message(
                chat_id=telegram_id,
                text=message,
                parse_mode='Markdown'
            )
    
    async def _deliver_generic(self, telegram_id: int, product: Product):
        """Entrega genérica para outros tipos"""
        message = f"""
🎁 *{product.name}*

Produto entregue com sucesso!

Acesse /pedidos para visualizar todas suas entregas.
"""
        await self.bot.send_message(
            chat_id=telegram_id,
            text=message,
            parse_mode='Markdown'
        )
    
    async def process_abandoned_carts(self):
        """Processa carrinhos abandonados"""
        from services.analytics import analytics
        from services.notifications import notifications
        
        abandoned = analytics.get_abandoned_carts(hours=2)
        
        for cart_info in abandoned:
            try:
                await notifications.cart_abandoned(
                    cart_info['user_id'],
                    cart_info['items_count']
                )
                logger.info(f"Notificação enviada para carrinho abandonado: {cart_info['user_id']}")
            except Exception as e:
                logger.error(f"Erro ao notificar carrinho abandonado: {e}")


# Instância global
delivery = DeliveryService()
