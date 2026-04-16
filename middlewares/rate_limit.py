"""
Rate Limit Middleware
"""

import time
from collections import defaultdict
from typing import Dict, List
from telegram import Update
from telegram.ext import ContextTypes


class RateLimitMiddleware:
    """Controla rate limit por usuário e tipo de ação"""
    
    def __init__(self):
        # {user_id: {action: [timestamps]}}
        self.requests: Dict[int, Dict[str, List[float]]] = defaultdict(
            lambda: defaultdict(list)
        )
        
        # Configurações por ação
        self.limits = {
            'default': {'max': 20, 'window': 60},
            'payment': {'max': 5, 'window': 300},  # 5 pagamentos a cada 5 min
            'order': {'max': 10, 'window': 60},
            'message': {'max': 30, 'window': 60},
            'callback': {'max': 50, 'window': 60},
        }
    
    def is_allowed(self, user_id: int, action: str = 'default') -> bool:
        """Verifica se ação é permitida dentro do rate limit"""
        now = time.time()
        limit_config = self.limits.get(action, self.limits['default'])
        
        max_requests = limit_config['max']
        window = limit_config['window']
        
        # Limpar entradas antigas
        requests = self.requests[user_id][action]
        self.requests[user_id][action] = [
            t for t in requests if now - t < window
        ]
        
        # Verificar limite
        if len(self.requests[user_id][action]) >= max_requests:
            return False
        
        # Registrar requisição
        self.requests[user_id][action].append(now)
        return True
    
    def get_remaining(self, user_id: int, action: str = 'default') -> int:
        """Retorna quantas requisições restam"""
        limit_config = self.limits.get(action, self.limits['default'])
        used = len(self.requests[user_id][action])
        return max(0, limit_config['max'] - used)
    
    def get_reset_time(self, user_id: int, action: str = 'default') -> float:
        """Retorna quando o rate limit reseta"""
        requests = self.requests[user_id][action]
        if not requests:
            return 0
        
        limit_config = self.limits.get(action, self.limits['default'])
        oldest = min(requests)
        return oldest + limit_config['window']


# Instância global
rate_limiter = RateLimitMiddleware()
