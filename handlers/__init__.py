"""
Handlers do TksBot
"""

from handlers.start import start_handler, main_menu_handler, callback_handler
from handlers.products import products_handler, category_handler, product_detail_handler
from handlers.cart import cart_handler, add_to_cart_handler, clear_cart_handler
from handlers.checkout import checkout_handler, checkout_callback_router
from handlers.orders import orders_handler, order_detail_handler
from handlers.admin import admin_handler, admin_stats_handler
from handlers.support import support_handler

__all__ = [
    'start_handler',
    'main_menu_handler',
    'callback_handler',
    'products_handler',
    'category_handler',
    'product_detail_handler',
    'cart_handler',
    'add_to_cart_handler',
    'clear_cart_handler',
    'checkout_handler',
    'checkout_callback_router',
    'orders_handler',
    'order_detail_handler',
    'admin_handler',
    'admin_stats_handler',
    'support_handler'
]
