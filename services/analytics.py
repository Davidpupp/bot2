"""
Analytics Service
Estatísticas e relatórios
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Any, Optional

from sqlalchemy import func

from app.database import db
from app.models import User, Order, Payment, Product, OrderStatus, PaymentStatus


class AnalyticsService:
    """Serviço de análise e estatísticas"""
    
    def __init__(self):
        pass
    
    # ============================================
    # ESTATÍSTICAS GERAIS
    # ============================================
    
    def get_dashboard_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas para dashboard"""
        with db.get_session() as session:
            today = datetime.utcnow().date()
            month_start = today.replace(day=1)
            
            # Total usuários
            total_users = session.query(func.count(User.id)).scalar() or 0
            new_users_today = session.query(func.count(User.id)).filter(
                func.date(User.created_at) == today
            ).scalar() or 0
            
            # Total vendas
            total_orders = session.query(func.count(Order.id)).scalar() or 0
            orders_today = session.query(func.count(Order.id)).filter(
                func.date(Order.created_at) == today
            ).scalar() or 0
            
            # Receita
            revenue_today = session.query(func.sum(Order.total)).filter(
                func.date(Order.created_at) == today,
                Order.status == OrderStatus.PAID
            ).scalar() or 0
            
            revenue_month = session.query(func.sum(Order.total)).filter(
                Order.created_at >= month_start,
                Order.status == OrderStatus.PAID
            ).scalar() or 0
            
            total_revenue = session.query(func.sum(Order.total)).filter(
                Order.status == OrderStatus.PAID
            ).scalar() or 0
            
            # Ticket médio
            paid_orders = session.query(func.count(Order.id)).filter(
                Order.status == OrderStatus.PAID
            ).scalar() or 0
            
            avg_ticket = float(total_revenue) / paid_orders if paid_orders > 0 else 0
            
            # Conversão
            pending_orders = session.query(func.count(Order.id)).filter(
                Order.status == OrderStatus.PENDING
            ).scalar() or 0
            
            conversion_rate = 0
            if total_orders > 0:
                conversion_rate = (paid_orders / total_orders) * 100
            
            # Produto campeão
            top_product = session.query(
                Product.id,
                Product.name,
                func.sum(OrderItem.quantity).label('total_sales')
            ).join(OrderItem).group_by(Product.id).order_by(
                func.sum(OrderItem.quantity).desc()
            ).first()
            
            return {
                'total_users': total_users,
                'new_users_today': new_users_today,
                'total_orders': total_orders,
                'orders_today': orders_today,
                'revenue_today': float(revenue_today),
                'revenue_month': float(revenue_month),
                'total_revenue': float(total_revenue),
                'avg_ticket': avg_ticket,
                'conversion_rate': conversion_rate,
                'paid_orders': paid_orders,
                'pending_orders': pending_orders,
                'top_product': {
                    'id': top_product[0],
                    'name': top_product[1],
                    'sales': top_product[2]
                } if top_product else None
            }
    
    def get_sales_by_period(self, days: int = 30) -> List[Dict]:
        """Vendas por período (últimos N dias)"""
        with db.get_session() as session:
            from_date = datetime.utcnow() - timedelta(days=days)
            
            results = session.query(
                func.date(Order.created_at).label('date'),
                func.count(Order.id).label('orders'),
                func.sum(Order.total).label('revenue')
            ).filter(
                Order.created_at >= from_date,
                Order.status == OrderStatus.PAID
            ).group_by(
                func.date(Order.created_at)
            ).order_by(
                func.date(Order.created_at)
            ).all()
            
            return [
                {
                    'date': r.date.isoformat(),
                    'orders': r.orders,
                    'revenue': float(r.revenue or 0)
                }
                for r in results
            ]
    
    def get_top_products(self, limit: int = 10) -> List[Dict]:
        """Produtos mais vendidos"""
        from app.models import OrderItem
        
        with db.get_session() as session:
            results = session.query(
                Product.id,
                Product.name,
                Product.category,
                func.sum(OrderItem.quantity).label('quantity_sold'),
                func.sum(OrderItem.product_price * OrderItem.quantity).label('revenue')
            ).join(OrderItem).join(Order).filter(
                Order.status == OrderStatus.PAID
            ).group_by(Product.id).order_by(
                func.sum(OrderItem.quantity).desc()
            ).limit(limit).all()
            
            return [
                {
                    'id': r.id,
                    'name': r.name,
                    'category': r.category,
                    'quantity_sold': r.quantity_sold,
                    'revenue': float(r.revenue or 0)
                }
                for r in results
            ]
    
    def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """Estatísticas de usuário específico"""
        with db.get_session() as session:
            user = session.query(User).get(user_id)
            if not user:
                return {}
            
            total_orders = session.query(func.count(Order.id)).filter(
                Order.user_id == user_id
            ).scalar() or 0
            
            total_spent = session.query(func.sum(Order.total)).filter(
                Order.user_id == user_id,
                Order.status == OrderStatus.PAID
            ).scalar() or 0
            
            last_order = session.query(Order).filter(
                Order.user_id == user_id
            ).order_by(Order.created_at.desc()).first()
            
            return {
                'user_id': user_id,
                'total_orders': total_orders,
                'total_spent': float(total_spent),
                'last_order_date': last_order.created_at if last_order else None,
                'customer_since': user.created_at
            }
    
    def get_affiliate_stats(self, affiliate_id: int) -> Dict[str, Any]:
        """Estatísticas de afiliado"""
        from app.models import Affiliate, AffiliateWithdrawal
        
        with db.get_session() as session:
            affiliate = session.query(Affiliate).get(affiliate_id)
            if not affiliate:
                return {}
            
            # Total de saques
            total_withdrawals = session.query(func.sum(AffiliateWithdrawal.amount)).filter(
                AffiliateWithdrawal.affiliate_id == affiliate_id,
                AffiliateWithdrawal.status == 'paid'
            ).scalar() or 0
            
            # Saques pendentes
            pending_withdrawals = session.query(func.sum(AffiliateWithdrawal.amount)).filter(
                AffiliateWithdrawal.affiliate_id == affiliate_id,
                AffiliateWithdrawal.status == 'pending'
            ).scalar() or 0
            
            return {
                'total_earned': float(affiliate.total_earned),
                'total_paid': float(total_withdrawals),
                'pending_payout': float(pending_withdrawals),
                'current_balance': float(affiliate.balance),
                'total_referrals': affiliate.total_referrals,
                'total_orders': affiliate.total_orders
            }
    
    def get_abandoned_carts(self, hours: int = 24) -> List[Dict]:
        """Carrinhos abandonados"""
        from app.models import Cart
        
        with db.get_session() as session:
            cutoff = datetime.utcnow() - timedelta(hours=hours)
            
            results = session.query(Cart, User).join(User).filter(
                Cart.updated_at < cutoff,
                Cart.items != None,
                Cart.items != '[]'
            ).all()
            
            abandoned = []
            for cart, user in results:
                items = cart.items or []
                abandoned.append({
                    'user_id': user.telegram_id,
                    'username': user.username,
                    'items_count': len(items),
                    'last_update': cart.updated_at
                })
            
            return abandoned


# Instância global
analytics = AnalyticsService()
