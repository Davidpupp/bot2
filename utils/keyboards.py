"""
Keyboards Inline - Todas as telas de botões do bot
Design premium com emojis estratégicos
"""

from typing import List, Optional, Dict, Any
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from app.config import config


class Keyboards:
    """Classe centralizada de keyboards"""
    
    # ============================================
    # MÉTODOS AUXILIARES
    # ============================================
    
    @staticmethod
    def _chunk_buttons(buttons: List[InlineKeyboardButton], chunk_size: int = 2) -> List[List[InlineKeyboardButton]]:
        """Divide botões em linhas"""
        return [buttons[i:i + chunk_size] for i in range(0, len(buttons), chunk_size)]
    
    @staticmethod
    def _nav_buttons(current_page: int, total_pages: int, prefix: str) -> List[InlineKeyboardButton]:
        """Botões de navegação de paginação"""
        buttons = []
        
        if current_page > 1:
            buttons.append(InlineKeyboardButton(
                "◀️ Anterior", 
                callback_data=f"{prefix}_page_{current_page - 1}"
            ))
        
        buttons.append(InlineKeyboardButton(
            f"📄 {current_page}/{total_pages}",
            callback_data="noop"
        ))
        
        if current_page < total_pages:
            buttons.append(InlineKeyboardButton(
                "Próxima ▶️",
                callback_data=f"{prefix}_page_{current_page + 1}"
            ))
        
        return buttons
    
    # ============================================
    # TELA INICIAL
    # ============================================
    
    @classmethod
    def start(cls, user_name: str = "") -> InlineKeyboardMarkup:
        """Tela inicial premium"""
        greeting = f"Olá {user_name}! " if user_name else ""
        
        buttons = [
            [
                InlineKeyboardButton("🛍️ Ver Produtos", callback_data="menu_products"),
                InlineKeyboardButton("💳 Comprar Agora", callback_data="menu_shop")
            ],
            [
                InlineKeyboardButton("📦 Meus Pedidos", callback_data="menu_orders"),
                InlineKeyboardButton("🎁 Promoções", callback_data="menu_promos")
            ],
            [
                InlineKeyboardButton("👤 Minha Conta", callback_data="menu_account"),
                InlineKeyboardButton("🆘 Suporte", callback_data="menu_support")
            ],
            [
                InlineKeyboardButton("💎 Área VIP", callback_data="menu_vip")
            ]
        ]
        
        return InlineKeyboardMarkup(buttons)
    
    @classmethod
    def main_menu(cls) -> InlineKeyboardMarkup:
        """Menu principal"""
        buttons = [
            [
                InlineKeyboardButton("🛍️ Produtos", callback_data="menu_products"),
                InlineKeyboardButton("🛒 Carrinho", callback_data="menu_cart")
            ],
            [
                InlineKeyboardButton("📦 Pedidos", callback_data="menu_orders"),
                InlineKeyboardButton("💎 VIP", callback_data="menu_vip")
            ],
            [
                InlineKeyboardButton("👤 Conta", callback_data="menu_account"),
                InlineKeyboardButton("🆘 Suporte", callback_data="menu_support")
            ],
            [
                InlineKeyboardButton("🔙 Voltar ao Início", callback_data="start")
            ]
        ]
        
        return InlineKeyboardMarkup(buttons)
    
    # ============================================
    # PRODUTOS E CATÁLOGO
    # ============================================
    
    @classmethod
    def categories(cls) -> InlineKeyboardMarkup:
        """Menu de categorias"""
        buttons = [
            [
                InlineKeyboardButton("💳 Cartões de Crédito", callback_data="category_credit_cards"),
            ],
            [
                InlineKeyboardButton("📄 Documentos", callback_data="category_documents"),
            ],
            [
                InlineKeyboardButton("👑 Área VIP", callback_data="category_vip"),
            ],
            [
                InlineKeyboardButton("🔍 Buscar Produto", callback_data="search_product"),
            ],
            [
                InlineKeyboardButton("🔙 Menu Principal", callback_data="main_menu")
            ]
        ]
        
        return InlineKeyboardMarkup(buttons)
    
    @classmethod
    def product_list(cls, products: List[Dict], category: str, page: int = 1, page_size: int = 5) -> InlineKeyboardMarkup:
        """Lista de produtos com paginação"""
        buttons = []
        
        # Calcular paginação
        total = len(products)
        total_pages = (total + page_size - 1) // page_size
        start = (page - 1) * page_size
        end = start + page_size
        page_products = products[start:end]
        
        # Botões de produtos
        for product in page_products:
            emoji = "💎" if product.get('is_vip') else "💳" if category == 'credit_cards' else "📄"
            price = f"R$ {product['price']:.2f}".replace('.', ',')
            
            buttons.append([
                InlineKeyboardButton(
                    f"{emoji} {product['name']} - {price}",
                    callback_data=f"product_{product['id']}"
                )
            ])
        
        # Paginação
        if total_pages > 1:
            buttons.append(cls._nav_buttons(page, total_pages, f"products_{category}"))
        
        # Voltar
        buttons.append([
            InlineKeyboardButton("🔙 Categorias", callback_data="menu_products")
        ])
        
        return InlineKeyboardMarkup(buttons)
    
    @classmethod
    def product_detail(cls, product: Dict, in_cart: bool = False) -> InlineKeyboardMarkup:
        """Detalhes do produto"""
        buttons = []
        
        # Ações principais
        action_buttons = []
        if in_cart:
            action_buttons.append(InlineKeyboardButton("✅ No Carrinho", callback_data="noop"))
        else:
            action_buttons.append(InlineKeyboardButton("🛒 Adicionar", callback_data=f"add_to_cart_{product['id']}"))
        
        action_buttons.append(InlineKeyboardButton("💳 Comprar", callback_data=f"buy_now_{product['id']}"))
        buttons.append(action_buttons)
        
        # Compartilhar
        buttons.append([
            InlineKeyboardButton("📤 Compartilhar", callback_data=f"share_product_{product['id']}"),
        ])
        
        # Navegação
        buttons.append([
            InlineKeyboardButton("🔙 Produtos", callback_data=f"category_{product['category']}"),
            InlineKeyboardButton("🛍️ Catálogo", callback_data="menu_products")
        ])
        
        return InlineKeyboardMarkup(buttons)
    
    # ============================================
    # CARRINHO
    # ============================================
    
    @classmethod
    def cart(cls, items: List[Dict], total: float) -> InlineKeyboardMarkup:
        """Tela do carrinho"""
        buttons = []
        
        # Itens com botões de remover
        for item in items:
            buttons.append([
                InlineKeyboardButton(
                    f"❌ {item['name'][:20]}",
                    callback_data=f"cart_remove_{item['id']}"
                ),
                InlineKeyboardButton(
                    f"{item['quantity']}x R$ {item['subtotal']:.2f}".replace('.', ','),
                    callback_data="noop"
                )
            ])
        
        # Separador e total
        buttons.append([
            InlineKeyboardButton(f"💰 Total: R$ {total:.2f}".replace('.', ','), callback_data="noop")
        ])
        
        # Ações
        buttons.append([
            InlineKeyboardButton("🏷️ Aplicar Cupom", callback_data="cart_coupon"),
            InlineKeyboardButton("🗑️ Limpar", callback_data="cart_clear")
        ])
        
        buttons.append([
            InlineKeyboardButton("💳 Finalizar Compra", callback_data="cart_checkout"),
        ])
        
        buttons.append([
            InlineKeyboardButton("🛍️ Continuar Comprando", callback_data="menu_products")
        ])
        
        return InlineKeyboardMarkup(buttons)
    
    @classmethod
    def cart_empty(cls) -> InlineKeyboardMarkup:
        """Carrinho vazio"""
        buttons = [
            [
                InlineKeyboardButton("🛍️ Ver Produtos", callback_data="menu_products")
            ],
            [
                InlineKeyboardButton("🔙 Menu Principal", callback_data="main_menu")
            ]
        ]
        
        return InlineKeyboardMarkup(buttons)
    
    # ============================================
    # CHECKOUT E PAGAMENTO
    # ============================================
    
    @classmethod
    def checkout(cls, order_id: int, has_coupon: bool = False) -> InlineKeyboardMarkup:
        """Tela de checkout"""
        buttons = []
        
        if not has_coupon:
            buttons.append([
                InlineKeyboardButton("🏷️ Tenho Cupom", callback_data=f"checkout_coupon_{order_id}")
            ])
        
        buttons.append([
            InlineKeyboardButton("💠 Pagar com PIX", callback_data=f"checkout_pix_{order_id}")
        ])
        
        buttons.append([
            InlineKeyboardButton("🛒 Voltar ao Carrinho", callback_data="menu_cart"),
            InlineKeyboardButton("❌ Cancelar", callback_data=f"cancel_order_{order_id}")
        ])
        
        return InlineKeyboardMarkup(buttons)
    
    @classmethod
    def payment_pix(cls, payment_id: int, copy_code: str) -> InlineKeyboardMarkup:
        """Tela de pagamento PIX"""
        buttons = [
            [
                InlineKeyboardButton("📋 Copiar Código", callback_data=f"pix_copy_{payment_id}")
            ],
            [
                InlineKeyboardButton("🔄 Verificar Pagamento", callback_data=f"pix_check_{payment_id}")
            ],
            [
                InlineKeyboardButton("🔄 Gerar Novo QR", callback_data=f"pix_regenerate_{payment_id}")
            ],
            [
                InlineKeyboardButton("❌ Cancelar", callback_data=f"pix_cancel_{payment_id}")
            ]
        ]
        
        return InlineKeyboardMarkup(buttons)
    
    @classmethod
    def payment_success(cls, order_id: int, has_delivery: bool = True) -> InlineKeyboardMarkup:
        """Pagamento aprovado"""
        buttons = []
        
        if has_delivery:
            buttons.append([
                InlineKeyboardButton("📦 Ver Entrega", callback_data=f"delivery_{order_id}")
            ])
        
        buttons.append([
            InlineKeyboardButton("🛍️ Continuar Comprando", callback_data="menu_products"),
            InlineKeyboardButton("📦 Meus Pedidos", callback_data="menu_orders")
        ])
        
        return InlineKeyboardMarkup(buttons)
    
    # ============================================
    # PEDIDOS
    # ============================================
    
    @classmethod
    def orders_list(cls, orders: List[Dict], page: int = 1) -> InlineKeyboardMarkup:
        """Lista de pedidos"""
        buttons = []
        page_size = 5
        
        total = len(orders)
        total_pages = (total + page_size - 1) // page_size
        start = (page - 1) * page_size
        end = start + page_size
        page_orders = orders[start:end]
        
        for order in page_orders:
            status_emoji = {
                'pending': '⏳',
                'paid': '✅',
                'processing': '🔄',
                'delivered': '📦',
                'cancelled': '❌'
            }.get(order['status'], '❓')
            
            buttons.append([
                InlineKeyboardButton(
                    f"{status_emoji} #{order['order_number']} - {order['total']}",
                    callback_data=f"order_{order['id']}"
                )
            ])
        
        if total_pages > 1:
            buttons.append(cls._nav_buttons(page, total_pages, "orders"))
        
        buttons.append([
            InlineKeyboardButton("🔙 Menu Principal", callback_data="main_menu")
        ])
        
        return InlineKeyboardMarkup(buttons)
    
    @classmethod
    def order_detail(cls, order: Dict) -> InlineKeyboardMarkup:
        """Detalhes do pedido"""
        buttons = []
        
        if order['status'] == 'pending':
            buttons.append([
                InlineKeyboardButton("💳 Pagar Agora", callback_data=f"order_pay_{order['id']}")
            ])
        
        if order['status'] == 'paid':
            buttons.append([
                InlineKeyboardButton("📦 Ver Entrega", callback_data=f"delivery_{order['id']}")
            ])
        
        buttons.append([
            InlineKeyboardButton("📄 Recibo", callback_data=f"receipt_{order['id']}"),
            InlineKeyboardButton("🆘 Suporte", callback_data=f"support_order_{order['id']}")
        ])
        
        buttons.append([
            InlineKeyboardButton("🔙 Meus Pedidos", callback_data="menu_orders"),
            InlineKeyboardButton("🛍️ Comprar Mais", callback_data="menu_products")
        ])
        
        return InlineKeyboardMarkup(buttons)
    
    # ============================================
    # CONTA DO USUÁRIO
    # ============================================
    
    @classmethod
    def account(cls, is_affiliate: bool = False) -> InlineKeyboardMarkup:
        """Menu da conta"""
        buttons = [
            [
                InlineKeyboardButton("👤 Editar Perfil", callback_data="account_edit"),
                InlineKeyboardButton("📦 Histórico", callback_data="menu_orders")
            ],
            [
                InlineKeyboardButton("💳 Pagamentos", callback_data="account_payments"),
                InlineKeyboardButton("🏷️ Cupons", callback_data="account_coupons")
            ]
        ]
        
        if is_affiliate:
            buttons.append([
                InlineKeyboardButton("🤝 Programa de Afiliados", callback_data="affiliate_dashboard")
            ])
        else:
            buttons.append([
                InlineKeyboardButton("🤝 Virar Afiliado", callback_data="affiliate_join")
            ])
        
        buttons.append([
            InlineKeyboardButton("🔙 Menu Principal", callback_data="main_menu")
        ])
        
        return InlineKeyboardMarkup(buttons)
    
    # ============================================
    # AFILIADOS
    # ============================================
    
    @classmethod
    def affiliate_dashboard(cls, balance: float) -> InlineKeyboardMarkup:
        """Dashboard de afiliado"""
        buttons = [
            [
                InlineKeyboardButton("🔗 Meu Link", callback_data="affiliate_link"),
                InlineKeyboardButton("📊 Estatísticas", callback_data="affiliate_stats")
            ],
            [
                InlineKeyboardButton(f"💰 Saque (R$ {balance:.2f})".replace('.', ','), 
                                   callback_data="affiliate_withdraw")
            ],
            [
                InlineKeyboardButton("🏆 Ranking", callback_data="affiliate_ranking"),
                InlineKeyboardButton("📚 Material", callback_data="affiliate_material")
            ],
            [
                InlineKeyboardButton("🔙 Minha Conta", callback_data="menu_account")
            ]
        ]
        
        return InlineKeyboardMarkup(buttons)
    
    # ============================================
    # SUPORTE
    # ============================================
    
    @classmethod
    def support(cls) -> InlineKeyboardMarkup:
        """Menu de suporte"""
        buttons = [
            [
                InlineKeyboardButton("❓ FAQ - Perguntas", callback_data="support_faq")
            ],
            [
                InlineKeyboardButton("📞 Falar com Atendente", callback_data="support_chat")
            ],
            [
                InlineKeyboardButton("📄 Política de Reembolso", callback_data="support_refund")
            ],
            [
                InlineKeyboardButton("🔙 Menu Principal", callback_data="main_menu")
            ]
        ]
        
        return InlineKeyboardMarkup(buttons)
    
    # ============================================
    # ADMIN PANEL
    # ============================================
    
    @classmethod
    def admin_dashboard(cls) -> InlineKeyboardMarkup:
        """Dashboard do admin"""
        buttons = [
            [
                InlineKeyboardButton("📊 Estatísticas", callback_data="admin_stats"),
                InlineKeyboardButton("👥 Usuários", callback_data="admin_users")
            ],
            [
                InlineKeyboardButton("📦 Pedidos", callback_data="admin_orders"),
                InlineKeyboardButton("💳 Pagamentos", callback_data="admin_payments")
            ],
            [
                InlineKeyboardButton("🛍️ Produtos", callback_data="admin_products"),
                InlineKeyboardButton("🏷️ Cupons", callback_data="admin_coupons")
            ],
            [
                InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast"),
                InlineKeyboardButton("⚙️ Configurações", callback_data="admin_settings")
            ],
            [
                InlineKeyboardButton("🔙 Menu Principal", callback_data="main_menu")
            ]
        ]
        
        return InlineKeyboardMarkup(buttons)
    
    @classmethod
    def admin_products(cls) -> InlineKeyboardMarkup:
        """Gestão de produtos"""
        buttons = [
            [
                InlineKeyboardButton("➕ Novo Produto", callback_data="admin_product_new")
            ],
            [
                InlineKeyboardButton("✏️ Editar Produto", callback_data="admin_product_edit")
            ],
            [
                InlineKeyboardButton("📦 Gerenciar Estoque", callback_data="admin_stock")
            ],
            [
                InlineKeyboardButton("🔙 Painel Admin", callback_data="admin_panel")
            ]
        ]
        
        return InlineKeyboardMarkup(buttons)
    
    @classmethod
    def admin_orders(cls) -> InlineKeyboardMarkup:
        """Gestão de pedidos"""
        buttons = [
            [
                InlineKeyboardButton("⏳ Pendentes", callback_data="admin_orders_pending"),
                InlineKeyboardButton("✅ Pagos", callback_data="admin_orders_paid")
            ],
            [
                InlineKeyboardButton("🔄 Processando", callback_data="admin_orders_processing"),
                InlineKeyboardButton("📦 Entregues", callback_data="admin_orders_delivered")
            ],
            [
                InlineKeyboardButton("🔙 Painel Admin", callback_data="admin_panel")
            ]
        ]
        
        return InlineKeyboardMarkup(buttons)
    
    @classmethod
    def admin_order_actions(cls, order_id: int, status: str) -> InlineKeyboardMarkup:
        """Ações em pedido específico"""
        buttons = []
        
        if status == 'pending':
            buttons.append([
                InlineKeyboardButton("✅ Confirmar Pagamento", callback_data=f"admin_confirm_{order_id}")
            ])
        
        if status in ['pending', 'paid']:
            buttons.append([
                InlineKeyboardButton("📦 Marcar Entregue", callback_data=f"admin_deliver_{order_id}")
            ])
        
        buttons.append([
            InlineKeyboardButton("↩️ Reembolsar", callback_data=f"admin_refund_{order_id}")
        ])
        
        buttons.append([
            InlineKeyboardButton("❌ Cancelar Pedido", callback_data=f"admin_cancel_{order_id}")
        ])
        
        buttons.append([
            InlineKeyboardButton("🔙 Pedidos", callback_data="admin_orders")
        ])
        
        return InlineKeyboardMarkup(buttons)
    
    # ============================================
    # BOTÕES GLOBAIS
    # ============================================
    
    @classmethod
    def back_to_menu(cls) -> InlineKeyboardMarkup:
        """Botão simples de voltar"""
        return InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 Menu Principal", callback_data="main_menu")
        ]])
    
    @classmethod
    def confirm_cancel(cls, action_confirm: str, action_cancel: str) -> InlineKeyboardMarkup:
        """Botões de confirmação/cancelamento"""
        return InlineKeyboardMarkup([[
            InlineKeyboardButton("✅ Confirmar", callback_data=action_confirm),
            InlineKeyboardButton("❌ Cancelar", callback_data=action_cancel)
        ]])
    
    @classmethod
    def close(cls) -> InlineKeyboardMarkup:
        """Botão de fechar"""
        return InlineKeyboardMarkup([[
            InlineKeyboardButton("❌ Fechar", callback_data="close_message")
        ]])
