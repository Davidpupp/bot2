"""
Modelos SQLAlchemy - Tabelas do banco de dados
Toda a estrutura de dados da plataforma TksBot
"""

import uuid
import secrets
import string
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from enum import Enum as PyEnum

from sqlalchemy import (
    Column, Integer, BigInteger, String, Text, Float, Boolean, 
    DateTime, ForeignKey, JSON, Enum, Index, UniqueConstraint,
    Numeric, func
)
from sqlalchemy.orm import relationship, validates
from sqlalchemy.ext.hybrid import hybrid_property

from app.database import Base


# ============================================
# ENUMS
# ============================================

class OrderStatus(PyEnum):
    PENDING = 'pending'
    PAID = 'paid'
    PROCESSING = 'processing'
    DELIVERED = 'delivered'
    CANCELLED = 'cancelled'
    REFUNDED = 'refunded'


class PaymentStatus(PyEnum):
    PENDING = 'pending'
    PROCESSING = 'processing'
    APPROVED = 'approved'
    REJECTED = 'rejected'
    CANCELLED = 'cancelled'
    REFUNDED = 'refunded'
    EXPIRED = 'expired'


class PaymentMethod(PyEnum):
    PIX = 'pix'
    CREDIT_CARD = 'credit_card'
    BOLETO = 'boleto'


class DiscountType(PyEnum):
    PERCENTAGE = 'percentage'
    FIXED = 'fixed'


class UserLevel(PyEnum):
    CUSTOMER = 'customer'
    VIP = 'vip'
    ADMIN = 'admin'
    MASTER = 'master'


# ============================================
# MODELS
# ============================================

class User(Base):
    """Usuários do bot"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(BigInteger, unique=True, index=True, nullable=False)
    username = Column(String(100), index=True)
    first_name = Column(String(100))
    last_name = Column(String(100))
    phone = Column(String(20))
    email = Column(String(100))
    
    # Status
    is_active = Column(Boolean, default=True)
    is_banned = Column(Boolean, default=False)
    ban_reason = Column(Text)
    
    # Nível e afiliação
    level = Column(Enum(UserLevel), default=UserLevel.CUSTOMER)
    affiliate_code = Column(String(20), unique=True, index=True)
    referrer_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    
    # Estatísticas
    total_orders = Column(Integer, default=0)
    total_spent = Column(Numeric(12, 2), default=0.00)
    last_activity = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    orders = relationship("Order", back_populates="user", lazy="dynamic")
    affiliate = relationship("Affiliate", uselist=False, back_populates="user")
    referrals = relationship("User", backref="referrer", remote_side=[id])
    logs = relationship("Log", back_populates="user", lazy="dynamic")
    
    # Índices
    __table_args__ = (
        Index('idx_users_telegram_id', 'telegram_id'),
        Index('idx_users_affiliate', 'affiliate_code'),
        Index('idx_users_active', 'is_active'),
    )
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.affiliate_code is None or self.affiliate_code == '':
            self.affiliate_code = self._generate_affiliate_code()
    
    @staticmethod
    def _generate_affiliate_code() -> str:
        """Gera código de afiliado único"""
        return ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
    
    @property
    def full_name(self) -> str:
        """Retorna nome completo do usuário"""
        if self.first_name is not None and self.last_name is not None:
            return f"{self.first_name} {self.last_name}"
        return self.first_name or self.username or "Usuário"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'telegram_id': self.telegram_id,
            'username': self.username,
            'full_name': self.full_name,
            'level': self.level.value,
            'total_orders': self.total_orders,
            'total_spent': float(self.total_spent),
            'is_active': self.is_active,
            'is_banned': self.is_banned,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Product(Base):
    """Produtos disponíveis para venda"""
    __tablename__ = 'products'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    slug = Column(String(200), unique=True, index=True)
    category = Column(String(50), index=True, nullable=False)
    description = Column(Text)
    short_description = Column(String(500))
    
    # Preços
    price = Column(Numeric(10, 2), nullable=False)
    compare_price = Column(Numeric(10, 2))  # Preço "de"
    cost_price = Column(Numeric(10, 2))  # Preço de custo
    
    # Estoque
    stock = Column(Integer, default=0)
    unlimited_stock = Column(Boolean, default=False)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)
    is_hidden = Column(Boolean, default=False)  # Produto VIP/Secreto
    is_vip = Column(Boolean, default=False)
    
    # Mídia
    image_url = Column(String(500))
    file_url = Column(String(500))  # Arquivo para entrega
    
    # Vendas
    orderbump_product_id = Column(Integer, ForeignKey('products.id'), nullable=True)
    upsell_product_id = Column(Integer, ForeignKey('products.id'), nullable=True)
    
    # Estatísticas
    view_count = Column(Integer, default=0)
    sales_count = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    order_items = relationship("OrderItem", back_populates="product")
    
    # Índices
    __table_args__ = (
        Index('idx_products_category', 'category'),
        Index('idx_products_active', 'is_active'),
        Index('idx_products_featured', 'is_featured'),
        Index('idx_products_price', 'price'),
    )
    
    @hybrid_property
    def has_stock(self) -> bool:
        """Verifica se há estoque disponível"""
        return self.unlimited_stock is True or self.stock > 0
    
    @property
    def display_price(self) -> str:
        """Retorna preço formatado"""
        return f"R$ {float(self.price):,.2f}".replace(',', '.')
    
    def decrease_stock(self, quantity: int = 1):
        """Diminui estoque após venda"""
        if self.unlimited_stock is False and self.stock >= quantity:
            self.stock -= quantity
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'slug': self.slug,
            'category': self.category,
            'description': self.description,
            'short_description': self.short_description,
            'price': float(self.price),
            'compare_price': float(self.compare_price) if self.compare_price else None,
            'stock': self.stock if not self.unlimited_stock else None,
            'is_active': self.is_active,
            'is_featured': self.is_featured,
            'is_vip': self.is_vip,
            'image_url': self.image_url,
            'sales_count': self.sales_count
        }


class Order(Base):
    """Pedidos de compra"""
    __tablename__ = 'orders'
    
    id = Column(Integer, primary_key=True, index=True)
    order_number = Column(String(20), unique=True, index=True)
    
    # Usuário
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Afiliado
    affiliate_id = Column(Integer, ForeignKey('affiliates.id'), nullable=True)
    affiliate_commission = Column(Numeric(10, 2), default=0.00)
    
    # Valores
    subtotal = Column(Numeric(12, 2), default=0.00)
    discount = Column(Numeric(12, 2), default=0.00)
    discount_code = Column(String(50))
    shipping = Column(Numeric(10, 2), default=0.00)
    total = Column(Numeric(12, 2), default=0.00)
    
    # Status
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    paid_at = Column(DateTime)
    delivered_at = Column(DateTime)
    
    # Observações
    notes = Column(Text)
    customer_notes = Column(Text)
    
    # Relacionamentos
    user = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", lazy="dynamic")
    payments = relationship("Payment", back_populates="order", lazy="dynamic")
    
    # Índices
    __table_args__ = (
        Index('idx_orders_user', 'user_id'),
        Index('idx_orders_status', 'status'),
        Index('idx_orders_created', 'created_at'),
        Index('idx_orders_number', 'order_number'),
    )
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.order_number is None or self.order_number == '':
            self.order_number = self._generate_order_number()
    
    @staticmethod
    def _generate_order_number() -> str:
        """Gera número de pedido único"""
        timestamp = datetime.now().strftime('%Y%m%d')
        random_suffix = ''.join(secrets.choice(string.digits) for _ in range(4))
        return f"TKS{timestamp}{random_suffix}"
    
    @property
    def item_count(self) -> int:
        """Retorna quantidade total de itens"""
        return sum(item.quantity for item in self.items)
    
    @property
    def formatted_total(self) -> str:
        """Retorna total formatado"""
        return f"R$ {float(self.total):,.2f}".replace(',', '.')
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'order_number': self.order_number,
            'user_id': self.user_id,
            'status': self.status.value,
            'subtotal': float(self.subtotal),
            'discount': float(self.discount),
            'total': float(self.total),
            'item_count': self.item_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'paid_at': self.paid_at.isoformat() if self.paid_at else None
        }


class OrderItem(Base):
    """Itens de pedido"""
    __tablename__ = 'order_items'
    
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('orders.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    
    # Dados snapshot (não mudam mesmo se produto mudar)
    product_name = Column(String(200), nullable=False)
    product_price = Column(Numeric(10, 2), nullable=False)
    
    quantity = Column(Integer, default=1)
    
    # Relacionamentos
    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")
    
    @property
    def subtotal(self) -> float:
        """Calcula subtotal do item"""
        return float(self.product_price) * self.quantity


class Payment(Base):
    """Pagamentos"""
    __tablename__ = 'payments'
    
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('orders.id'), nullable=False)
    
    # Identificadores externos
    external_id = Column(String(100), index=True)  # ID no gateway
    external_reference = Column(String(100))
    
    # Método e status
    method = Column(Enum(PaymentMethod), default=PaymentMethod.PIX)
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    
    # Valores
    amount = Column(Numeric(12, 2), nullable=False)
    paid_amount = Column(Numeric(12, 2), default=0.00)
    
    # PIX específico
    pix_qr_code = Column(Text)  # Base64 ou URL
    pix_copy_paste = Column(Text)  # Código copia e cola
    pix_expiration = Column(DateTime)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    paid_at = Column(DateTime)
    
    # Resposta bruta do gateway
    gateway_response = Column(JSON)
    
    # Relacionamentos
    order = relationship("Order", back_populates="payments")
    
    # Índices
    __table_args__ = (
        Index('idx_payments_order', 'order_id'),
        Index('idx_payments_external', 'external_id'),
        Index('idx_payments_status', 'status'),
    )
    
    @property
    def is_pending(self) -> bool:
        return self.status == PaymentStatus.PENDING
    
    @property
    def is_approved(self) -> bool:
        return self.status == PaymentStatus.APPROVED
    
    @property
    def is_expired(self) -> bool:
        if self.pix_expiration is not None:
            return datetime.utcnow() > self.pix_expiration
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'order_id': self.order_id,
            'external_id': self.external_id,
            'method': self.method.value,
            'status': self.status.value,
            'amount': float(self.amount),
            'pix_copy_paste': self.pix_copy_paste if self.method == PaymentMethod.PIX else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'expires_at': self.pix_expiration.isoformat() if self.pix_expiration else None
        }


class Coupon(Base):
    """Cupons de desconto"""
    __tablename__ = 'coupons'
    
    id = Column(Integer, primary_key=True)
    code = Column(String(50), unique=True, index=True, nullable=False)
    
    # Tipo e valor
    discount_type = Column(Enum(DiscountType), nullable=False)
    discount_value = Column(Numeric(10, 2), nullable=False)  # % ou valor fixo
    
    # Limites
    max_uses = Column(Integer)
    used_count = Column(Integer, default=0)
    min_purchase = Column(Numeric(10, 2), default=0.00)
    
    # Restrições
    valid_from = Column(DateTime, default=datetime.utcnow)
    valid_until = Column(DateTime)
    applicable_products = Column(JSON)  # Lista de IDs ou None para todos
    applicable_categories = Column(JSON)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Índices
    __table_args__ = (
        Index('idx_coupons_code', 'code'),
        Index('idx_coupons_active', 'is_active'),
    )
    
    @property
    def is_valid(self) -> bool:
        """Verifica se cupom está válido"""
        if self.is_active is False:
            return False
        
        now = datetime.utcnow()
        if self.valid_from is not None and now < self.valid_from:
            return False
        if self.valid_until is not None and now > self.valid_until:
            return False
        if self.max_uses is not None and self.used_count >= self.max_uses:
            return False
        
        return True
    
    def calculate_discount(self, subtotal: float) -> float:
        """Calcula valor do desconto"""
        if subtotal < float(self.min_purchase):
            return 0.0
        
        if self.discount_type == DiscountType.PERCENTAGE:
            return subtotal * (float(self.discount_value) / 100)
        else:
            return min(float(self.discount_value), subtotal)
    
    def use(self):
        """Registra uso do cupom"""
        self.used_count += 1


class Affiliate(Base):
    """Programa de afiliados"""
    __tablename__ = 'affiliates'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), unique=True, nullable=False)
    
    # Código único
    code = Column(String(20), unique=True, index=True, nullable=False)
    
    # Financeiro
    balance = Column(Numeric(12, 2), default=0.00)
    total_earned = Column(Numeric(12, 2), default=0.00)
    total_paid = Column(Numeric(12, 2), default=0.00)
    
    # Estatísticas
    total_referrals = Column(Integer, default=0)
    total_orders = Column(Integer, default=0)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Dados bancários para saque
    pix_key = Column(String(100))
    bank_account = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    user = relationship("User", back_populates="affiliate")
    withdrawals = relationship("AffiliateWithdrawal", back_populates="affiliate", lazy="dynamic")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.code is None or self.code == '':
            self.code = self._generate_code()
    
    @staticmethod
    def _generate_code() -> str:
        """Gera código de afiliado"""
        return ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
    
    def add_commission(self, amount: float):
        """Adiciona comissão ao saldo"""
        self.balance += amount
        self.total_earned += amount
    
    def request_withdrawal(self, amount: float):
        """Solicita saque"""
        if amount > float(self.balance):
            raise ValueError("Saldo insuficiente")
        
        self.balance -= amount
        return True


class AffiliateWithdrawal(Base):
    """Saques de afiliados"""
    __tablename__ = 'affiliate_withdrawals'
    
    id = Column(Integer, primary_key=True)
    affiliate_id = Column(Integer, ForeignKey('affiliates.id'), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    status = Column(String(20), default='pending')  # pending, approved, rejected, paid
    
    # Dados do pagamento
    pix_key = Column(String(100))
    payment_proof = Column(String(500))
    
    # Timestamps
    requested_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime)
    notes = Column(Text)
    
    # Relacionamentos
    affiliate = relationship("Affiliate", back_populates="withdrawals")


class Cart(Base):
    """Carrinho de compras (sessão)"""
    __tablename__ = 'carts'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), unique=True, nullable=False)
    
    # Itens em JSON
    items = Column(JSON, default=list)  # [{product_id, quantity, added_at}]
    
    # Cupom aplicado
    coupon_code = Column(String(50))
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = Column(DateTime)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.expires_at is None:
            self.expires_at = datetime.utcnow() + timedelta(minutes=30)
    
    def add_item(self, product_id: int, quantity: int = 1):
        """Adiciona item ao carrinho"""
        items = self.items or []
        
        # Verifica se já existe
        for item in items:
            if item.get('product_id') == product_id:
                item['quantity'] += quantity
                break
        else:
            items.append({
                'product_id': product_id,
                'quantity': quantity,
                'added_at': datetime.utcnow().isoformat()
            })
        
        self.items = items
        self.updated_at = datetime.utcnow()
    
    def remove_item(self, product_id: int):
        """Remove item do carrinho"""
        items = self.items or []
        self.items = [item for item in items if item.get('product_id') != product_id]
        self.updated_at = datetime.utcnow()
    
    def clear(self):
        """Limpa carrinho"""
        self.items = []
        self.coupon_code = None
        self.updated_at = datetime.utcnow()


class Log(Base):
    """Logs do sistema"""
    __tablename__ = 'logs'
    
    id = Column(Integer, primary_key=True)
    
    # Categorização
    level = Column(String(20), default='INFO')  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    category = Column(String(50), index=True)  # payment, order, user, system, error
    
    # Conteúdo
    message = Column(Text, nullable=False)
    details = Column(JSON)
    
    # Referências
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    order_id = Column(Integer, ForeignKey('orders.id'), nullable=True)
    payment_id = Column(Integer, ForeignKey('payments.id'), nullable=True)
    
    # Origem
    source_ip = Column(String(50))
    user_agent = Column(String(500))
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    user = relationship("User", back_populates="logs")
    
    # Índices
    __table_args__ = (
        Index('idx_logs_category', 'category'),
        Index('idx_logs_level', 'level'),
        Index('idx_logs_created', 'created_at'),
        Index('idx_logs_user', 'user_id'),
    )


class Admin(Base):
    """Administradores do sistema"""
    __tablename__ = 'admins'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), unique=True, nullable=False)
    telegram_id = Column(BigInteger, unique=True, nullable=False)
    
    # Nível de acesso
    level = Column(String(20), default='admin')  # admin, super, master
    
    # Permissões específicas
    can_manage_products = Column(Boolean, default=True)
    can_manage_orders = Column(Boolean, default=True)
    can_manage_users = Column(Boolean, default=True)
    can_manage_finance = Column(Boolean, default=False)
    can_broadcast = Column(Boolean, default=False)
    can_manage_admins = Column(Boolean, default=False)
    
    # Status
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Índices
    __table_args__ = (
        Index('idx_admins_telegram', 'telegram_id'),
        Index('idx_admins_level', 'level'),
    )


class Setting(Base):
    """Configurações dinâmicas do sistema"""
    __tablename__ = 'settings'
    
    id = Column(Integer, primary_key=True)
    key = Column(String(100), unique=True, index=True, nullable=False)
    value = Column(Text)
    type = Column(String(20), default='string')  # string, int, float, bool, json
    
    description = Column(String(500))
    is_editable = Column(Boolean, default=True)
    
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(Integer, ForeignKey('admins.id'))
    
    def get_value(self):
        """Retorna valor convertido conforme tipo"""
        if self.type == 'int':
            return int(self.value) if self.value else 0
        elif self.type == 'float':
            return float(self.value) if self.value else 0.0
        elif self.type == 'bool':
            return self.value.lower() == 'true' if self.value else False
        elif self.type == 'json':
            import json
            return json.loads(self.value) if self.value else {}
        return self.value


# ============================================
# FUNÇÕES UTILITÁRIAS
# ============================================

def create_default_admin(session, telegram_id: int):
    """Cria administrador master padrão"""
    # Verifica se já existe
    existing = session.query(Admin).filter_by(telegram_id=telegram_id).first()
    if existing:
        return existing
    
    # Cria usuário se não existir
    user = session.query(User).filter_by(telegram_id=telegram_id).first()
    if not user:
        user = User(
            telegram_id=telegram_id,
            username='admin',
            first_name='Administrador',
            level=UserLevel.MASTER
        )
        session.add(user)
        session.flush()
    
    # Cria admin
    admin = Admin(
        user_id=user.id,
        telegram_id=telegram_id,
        level='master',
        can_manage_finance=True,
        can_broadcast=True,
        can_manage_admins=True
    )
    session.add(admin)
    session.commit()
    
    return admin


def seed_products(session):
    """Cria produtos iniciais"""
    products_data = [
        {
            'name': '💳 Info CC Gold',
            'slug': 'info-cc-gold',
            'category': 'credit_cards',
            'description': 'Informações de cartão Gold - Limite médio-alto, aceito em estabelecimentos premium',
            'short_description': 'Cartão Gold premium com limite elevado',
            'price': 150.00,
            'compare_price': 200.00,
            'stock': 100,
            'is_active': True,
            'is_featured': True
        },
        {
            'name': '💎 Info CC Platinum',
            'slug': 'info-cc-platinum',
            'category': 'credit_cards',
            'description': 'Informações de cartão Platinum - Exclusivo, benefícios premium, limite alto',
            'short_description': 'Cartão Platinum exclusivo',
            'price': 300.00,
            'compare_price': 400.00,
            'stock': 50,
            'is_active': True,
            'is_featured': True
        },
        {
            'name': '🏆 Info CC Infinite',
            'slug': 'info-cc-infinite',
            'category': 'credit_cards',
            'description': 'Informações de cartão Infinite - Top de linha, sem limites, acesso VIP mundial',
            'short_description': 'Cartão Infinite sem limites',
            'price': 500.00,
            'compare_price': 700.00,
            'stock': 25,
            'is_active': True,
            'is_featured': True
        },
        {
            'name': '⭐ Info CC Basic',
            'slug': 'info-cc-basic',
            'category': 'credit_cards',
            'description': 'Informações de cartão Basic - Acesso econômico, ideal para iniciantes',
            'short_description': 'Cartão Basic acessível',
            'price': 80.00,
            'compare_price': 120.00,
            'stock': 200,
            'is_active': True
        },
        {
            'name': '🖤 Info CC Black',
            'slug': 'info-cc-black',
            'category': 'credit_cards',
            'description': 'Informações de cartão Black - Ultra premium, concierge mundial, sem limites reais',
            'short_description': 'Cartão Black ultra premium',
            'price': 800.00,
            'compare_price': 1200.00,
            'stock': 10,
            'is_active': True,
            'is_vip': True
        },
        {
            'name': '📄 Comprovante FK',
            'slug': 'comprovante-fk',
            'category': 'documents',
            'description': 'Comprovante FK profissional - Documento verificado e atualizado',
            'short_description': 'Comprovante FK verificado',
            'price': 50.00,
            'stock': 500,
            'unlimited_stock': True,
            'is_active': True
        },
        {
            'name': '📋 Doc FK App',
            'slug': 'doc-fk-app',
            'category': 'documents',
            'description': 'Documento FK App - Versão digital completa para aplicativos',
            'short_description': 'Doc FK App digital',
            'price': 75.00,
            'stock': 300,
            'unlimited_stock': True,
            'is_active': True
        }
    ]
    
    created_count = 0
    for data in products_data:
        existing = session.query(Product).filter_by(slug=data['slug']).first()
        if not existing:
            product = Product(**data)
            session.add(product)
            created_count += 1
    
    if created_count > 0:
        session.commit()
        logger.info(f"✅ {created_count} produtos criados")
    else:
        logger.info("ℹ️ Produtos já existem")


# Logger para models
logger = logging.getLogger(__name__)
