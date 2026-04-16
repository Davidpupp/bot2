"""
Funções utilitárias auxiliares
"""

import re
import secrets
import string
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional, Union


def format_currency(value: Union[float, Decimal, int]) -> str:
    """Formata valor como moeda brasileira"""
    try:
        amount = float(value)
        return f"R$ {amount:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    except (ValueError, TypeError):
        return "R$ 0,00"


def format_datetime(dt: Optional[datetime], format: str = '%d/%m/%Y %H:%M') -> str:
    """Formata datetime para string"""
    if not dt:
        return "N/A"
    return dt.strftime(format)


def format_date(dt: Optional[datetime]) -> str:
    """Formata apenas a data"""
    return format_datetime(dt, '%d/%m/%Y')


def format_time(dt: Optional[datetime]) -> str:
    """Formata apenas a hora"""
    return format_datetime(dt, '%H:%M')


def truncate_text(text: str, max_length: int = 100, suffix: str = '...') -> str:
    """Trunca texto para tamanho máximo"""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)].rstrip() + suffix


def generate_random_code(length: int = 8, uppercase: bool = True, digits: bool = True) -> str:
    """Gera código aleatório"""
    chars = ''
    if uppercase:
        chars += string.ascii_uppercase
    if digits:
        chars += string.digits
    if not chars:
        chars = string.ascii_uppercase + string.digits
    
    return ''.join(secrets.choice(chars) for _ in range(length))


def generate_order_number() -> str:
    """Gera número de pedido único"""
    timestamp = datetime.now().strftime('%Y%m%d')
    random_suffix = generate_random_code(4)
    return f"TKS{timestamp}{random_suffix}"


def escape_markdown(text: str) -> str:
    """Escapa caracteres especiais do Markdown V2 do Telegram"""
    if not text:
        return ""
    
    # Caracteres que precisam ser escapados no Markdown V2
    escape_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    
    for char in escape_chars:
        text = text.replace(char, f'\\{char}')
    
    return text


def remove_html_tags(text: str) -> str:
    """Remove tags HTML do texto"""
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)


def validate_email(email: str) -> bool:
    """Valida formato de email"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_phone(phone: str) -> bool:
    """Valida formato de telefone brasileiro"""
    # Remove caracteres não numéricos
    digits = re.sub(r'\D', '', phone)
    # Deve ter 10 ou 11 dígitos
    return len(digits) in [10, 11]


def sanitize_input(text: str, max_length: int = 1000) -> str:
    """Sanitiza input do usuário"""
    if not text:
        return ""
    
    # Remove caracteres de controle
    text = ''.join(char for char in text if ord(char) >= 32 or char == '\n')
    
    # Remove tags HTML
    text = remove_html_tags(text)
    
    # Limita tamanho
    text = truncate_text(text, max_length, '')
    
    return text.strip()


def calculate_percentage(value: float, percentage: float) -> float:
    """Calcula porcentagem de um valor"""
    return value * (percentage / 100)


def calculate_discount(subtotal: float, discount_type: str, discount_value: float) -> float:
    """Calcula valor do desconto"""
    if discount_type == 'percentage':
        return calculate_percentage(subtotal, discount_value)
    else:  # fixed
        return min(discount_value, subtotal)


def format_bytes(size_bytes: int) -> str:
    """Formata bytes para unidades legíveis"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def time_ago(dt: datetime) -> str:
    """Retorna tempo relativo (ex: '2 horas atrás')"""
    now = datetime.utcnow()
    diff = now - dt
    
    seconds = diff.total_seconds()
    
    if seconds < 60:
        return "agora"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f"{minutes} min{'s' if minutes > 1 else ''} atrás"
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f"{hours} h{'s' if hours > 1 else ''} atrás"
    elif seconds < 604800:
        days = int(seconds / 86400)
        return f"{days} dia{'s' if days > 1 else ''} atrás"
    else:
        return format_date(dt)


def get_greeting() -> str:
    """Retorna saudação baseada na hora do dia"""
    hour = datetime.now().hour
    
    if 5 <= hour < 12:
        return "Bom dia"
    elif 12 <= hour < 18:
        return "Boa tarde"
    else:
        return "Boa noite"


def parse_telegram_link(text: str) -> Optional[str]:
    """Extrai username de link do Telegram"""
    patterns = [
        r't\.me/(\w+)',
        r'telegram\.me/(\w+)',
        r'@(\w+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1)
    
    return None


def mask_sensitive_data(data: str, visible_chars: int = 4) -> str:
    """Mascara dados sensíveis (ex: cartão, CPF)"""
    if len(data) <= visible_chars * 2:
        return '*' * len(data)
    
    return data[:visible_chars] + '*' * (len(data) - visible_chars * 2) + data[-visible_chars:]


def chunk_list(lst: list, chunk_size: int) -> list:
    """Divide lista em chunks de tamanho específico"""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def is_valid_pix_key(key: str) -> bool:
    """Valida se é uma chave PIX válida (CPF, CNPJ, email, celular ou aleatória)"""
    if not key:
        return False
    
    key = key.strip()
    
    # CPF (11 dígitos)
    if re.match(r'^\d{11}$', key):
        return True
    
    # CNPJ (14 dígitos)
    if re.match(r'^\d{14}$', key):
        return True
    
    # Celular (+55 ou 55 + 11 dígitos)
    if re.match(r'^(\+?55)?\d{11}$', key):
        return True
    
    # Email
    if validate_email(key):
        return True
    
    # Chave aleatória (UUID) - 36 caracteres com hífens
    if re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', key, re.I):
        return True
    
    return False


def parse_price(text: str) -> Optional[float]:
    """Extrai valor numérico de texto de preço"""
    # Remove R$, espaços e troca vírgula por ponto
    cleaned = text.replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')
    
    try:
        return float(cleaned)
    except ValueError:
        return None


class PaginationHelper:
    """Helper para paginação de resultados"""
    
    def __init__(self, items: list, page_size: int = 5):
        self.items = items
        self.page_size = page_size
        self.total_pages = (len(items) + page_size - 1) // page_size
    
    def get_page(self, page: int) -> list:
        """Retorna itens da página especificada"""
        if page < 1:
            page = 1
        if page > self.total_pages:
            page = self.total_pages
        
        start = (page - 1) * self.page_size
        end = start + self.page_size
        return self.items[start:end]
    
    def has_next(self, page: int) -> bool:
        """Verifica se há próxima página"""
        return page < self.total_pages
    
    def has_prev(self, page: int) -> bool:
        """Verifica se há página anterior"""
        return page > 1
