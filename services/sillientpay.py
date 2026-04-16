"""
SillientPay Integration Service
Integração completa com API SillientPay para PIX
"""

import base64
import hashlib
import hmac
import json
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional, Dict, Any

import httpx
from telegram import Update

from app.config import config
from utils.logger import logger, log_payment_event


class SillientPayService:
    """Serviço de integração com SillientPay"""
    
    def __init__(self):
        self.api_key = config.SILLIENT_API_KEY
        self.secret_key = config.SILLIENT_SECRET_KEY
        self.base_url = config.SILLIENT_BASE_URL
        
        # Headers padrão
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    
    def _generate_signature(self, payload: str) -> str:
        """Gera assinatura HMAC para webhook validation"""
        return hmac.new(
            self.secret_key.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
    
    def _verify_webhook_signature(self, payload: str, signature: str) -> bool:
        """Verifica assinatura do webhook"""
        expected = self._generate_signature(payload)
        return hmac.compare_digest(expected, signature)
    
    async def create_pix_payment(
        self,
        amount: Decimal,
        description: str,
        order_id: str,
        customer: Dict[str, Any]
    ) -> Optional[Dict]:
        """
        Cria cobrança PIX
        
        Args:
            amount: Valor da cobrança
            description: Descrição do pagamento
            order_id: ID interno do pedido
            customer: Dados do cliente {name, email, cpf}
        
        Returns:
            Dict com payment_id, qr_code, copy_paste, expiration
        """
        try:
            payload = {
                'amount': float(amount),
                'description': description[:80],  # Limite da API
                'external_reference': str(order_id),
                'customer': {
                    'name': customer.get('name', 'Cliente')[:100],
                    'email': customer.get('email', '')[:100],
                    'document': customer.get('cpf', '')[:14]
                },
                'pix_expiration': config.PIX_EXPIRATION * 60,  # segundos
                'notification_url': f"{config.WEBHOOK_URL}/webhook/sillientpay"
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/payments/pix",
                    headers=self.headers,
                    json=payload
                )
                
                response.raise_for_status()
                data = response.json()
                
                log_payment_event(
                    f"PIX criado: {data.get('id')}",
                    order_id=order_id,
                    amount=float(amount)
                )
                
                return {
                    'payment_id': data.get('id'),
                    'qr_code': data.get('pix', {}).get('qr_code'),
                    'qr_code_base64': data.get('pix', {}).get('qr_code_base64'),
                    'copy_paste': data.get('pix', {}).get('copy_paste'),
                    'expiration': datetime.utcnow() + timedelta(minutes=config.PIX_EXPIRATION),
                    'status': data.get('status', 'pending'),
                    'amount': float(amount),
                    'raw_response': data
                }
                
        except httpx.HTTPStatusError as e:
            logger.error(
                f"Erro HTTP SillientPay: {e.response.status_code} - {e.response.text}",
                order_id=order_id
            )
            return None
        except Exception as e:
            logger.error(f"Erro ao criar PIX: {e}", order_id=order_id)
            return None
    
    async def check_payment_status(self, payment_id: str) -> Optional[Dict]:
        """
        Consulta status do pagamento
        
        Args:
            payment_id: ID do pagamento na SillientPay
        
        Returns:
            Dict com status e detalhes
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.base_url}/payments/{payment_id}",
                    headers=self.headers
                )
                
                response.raise_for_status()
                data = response.json()
                
                return {
                    'id': data.get('id'),
                    'status': data.get('status'),
                    'amount': data.get('amount'),
                    'paid_amount': data.get('paid_amount'),
                    'paid_at': data.get('paid_at'),
                    'raw_response': data
                }
                
        except Exception as e:
            logger.error(f"Erro ao verificar pagamento: {e}", payment_id=payment_id)
            return None
    
    async def cancel_payment(self, payment_id: str) -> bool:
        """
        Cancela um pagamento pendente
        
        Args:
            payment_id: ID do pagamento
        
        Returns:
            True se cancelado com sucesso
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.base_url}/payments/{payment_id}/cancel",
                    headers=self.headers
                )
                
                response.raise_for_status()
                
                log_payment_event(f"Pagamento cancelado: {payment_id}")
                return True
                
        except Exception as e:
            logger.error(f"Erro ao cancelar pagamento: {e}", payment_id=payment_id)
            return False
    
    async def refund_payment(self, payment_id: str, amount: Optional[Decimal] = None) -> bool:
        """
        Solicita reembolso
        
        Args:
            payment_id: ID do pagamento
            amount: Valor a reembolsar (None = total)
        
        Returns:
            True se reembolsado com sucesso
        """
        try:
            payload = {}
            if amount:
                payload['amount'] = float(amount)
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.base_url}/payments/{payment_id}/refund",
                    headers=self.headers,
                    json=payload if payload else None
                )
                
                response.raise_for_status()
                
                log_payment_event(f"Pagamento reembolsado: {payment_id}")
                return True
                
        except Exception as e:
            logger.error(f"Erro ao reembolsar: {e}", payment_id=payment_id)
            return False
    
    def parse_webhook(self, body: str, signature: str) -> Optional[Dict]:
        """
        Processa webhook da SillientPay
        
        Args:
            body: Corpo da requisição
            signature: Assinatura do webhook
        
        Returns:
            Dict com dados do webhook ou None se inválido
        """
        # Verificar assinatura
        if not self._verify_webhook_signature(body, signature):
            logger.error("Assinatura de webhook inválida")
            return None
        
        try:
            data = json.loads(body)
            
            return {
                'payment_id': data.get('data', {}).get('id'),
                'status': data.get('data', {}).get('status'),
                'external_reference': data.get('data', {}).get('external_reference'),
                'amount': data.get('data', {}).get('amount'),
                'paid_amount': data.get('data', {}).get('paid_amount'),
                'paid_at': data.get('data', {}).get('paid_at'),
                'raw': data
            }
            
        except json.JSONDecodeError:
            logger.error("JSON inválido no webhook")
            return None
    
    def format_pix_message(self, qr_code_base64: str, copy_paste: str, amount: float, expiration: datetime) -> str:
        """
        Formata mensagem de PIX para o cliente
        
        Returns:
            Texto formatado com QR code e instruções
        """
        from utils.helpers import format_currency
        
        time_left = expiration - datetime.utcnow()
        minutes_left = max(0, int(time_left.total_seconds() / 60))
        
        message = f"""
💳 *PAGAMENTO PIX*

💰 Valor: `{format_currency(amount)}`
⏰ Expira em: {minutes_left} minutos

*Escaneie o QR Code acima ☝️*
ou
*Copie o código abaixo:*

`{copy_paste[:50]}...`

⚡ O pagamento será detectado automaticamente
🔔 Você receberá confirmação aqui mesmo
"""
        return message.strip()


# Instância global
sillientpay = SillientPayService()
