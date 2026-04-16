"""
TksBot - Plataforma Premium de Vendas no Telegram

Sistema enterprise de vendas automáticas com integração SillientPay,
painel admin completo e deploy otimizado para Railway.

Autor: Cascade AI
Versão: 2.0.0 Premium
"""

__version__ = "2.0.0"
__author__ = "TksBot Team"
__license__ = "Enterprise"

from app.config import Config
from app.database import Database

__all__ = ['Config', 'Database']
