# 🚀 TksBot - Plataforma Premium de Vendas no Telegram

Sistema enterprise de vendas automáticas com integração SillientPay, painel admin completo e deploy otimizado para Railway.

![Version](https://img.shields.io/badge/version-2.0.0-blue)
![Python](https://img.shields.io/badge/python-3.11-green)
![License](https://img.shields.io/badge/license-Enterprise-red)

---

## ✨ Funcionalidades

### 💰 Sistema de Vendas
- 🛒 Carrinho de compras persistente
- 💳 Pagamento PIX via SillientPay
- 🎁 Cupons de desconto (porcentagem/valor fixo)
- 📦 Entrega automática de produtos
- 🔄 Order bump e upsell
- 🛍️ Catálogo com categorias

### 👤 Área do Cliente
- 📦 Histórico de pedidos
- 👤 Gerenciamento de conta
- 💎 Programa de afiliados
- 🆘 Suporte integrado
- 🔔 Notificações automáticas

### ⚙️ Painel Admin
- 📊 Dashboard com estatísticas
- 🛍️ Gestão de produtos
- 📦 Controle de pedidos
- 💳 Monitoramento de pagamentos
- 👥 Gestão de usuários
- 📢 Sistema de broadcast
- 🏷️ Gestão de cupons

### 🔒 Segurança
- 🛡️ Anti-flood e rate limiting
- 🔐 Proteção contra SQL injection
- ✅ Sanitização de inputs
- 🔑 Tokens em .env
- 📝 Logs completos

---

## 📁 Estrutura do Projeto

```
TksBot/
├── app/
│   ├── __init__.py
│   ├── config.py          # Configurações centralizadas
│   ├── database.py        # Conexão PostgreSQL/SQLite
│   └── models.py          # Tabelas SQLAlchemy
├── handlers/
│   ├── __init__.py
│   ├── start.py           # Start e menu principal
│   ├── products.py        # Catálogo de produtos
│   ├── cart.py            # Carrinho de compras
│   ├── checkout.py        # Pagamentos
│   ├── orders.py          # Pedidos
│   ├── admin.py           # Painel admin
│   ├── affiliate.py       # Programa de afiliados
│   └── support.py         # Suporte ao cliente
├── services/
│   ├── __init__.py
│   ├── sillientpay.py     # Integração PIX
│   ├── notifications.py   # Notificações
│   ├── analytics.py       # Estatísticas
│   └── delivery.py        # Entrega automática
├── utils/
│   ├── __init__.py
│   ├── helpers.py         # Funções utilitárias
│   ├── keyboards.py       # Teclados inline
│   └── logger.py          # Sistema de logs
├── middlewares/
│   ├── __init__.py
│   ├── security.py        # Anti-flood, proteções
│   ├── rate_limit.py      # Rate limiting
│   └── logging.py         # Logging middleware
├── main.py                # Entry point
├── requirements.txt       # Dependências
├── Procfile               # Railway config
├── runtime.txt            # Python version
├── .env                   # Variáveis de ambiente
└── .env.example           # Template de env
```

---

## 🚀 Deploy no Railway

### 1. Criar Repositório GitHub

```bash
# Inicializar git
git init

# Adicionar todos os arquivos
git add .

# Commit inicial
git commit -m "Initial commit: TksBot Premium"

# Criar repositório no GitHub e conectar
git branch -M main
git remote add origin https://github.com/SEU_USUARIO/tksbot.git
git push -u origin main
```

### 2. Deploy no Railway

1. Acesse [Railway.app](https://railway.app)
2. Clique em "New Project"
3. Selecione "Deploy from GitHub repo"
4. Escolha o repositório `tksbot`
5. Clique em "Deploy"

### 3. Adicionar PostgreSQL

1. No projeto Railway, clique em "New"
2. Selecione "Database" → "Add PostgreSQL"
3. Railway criará automaticamente a variável `DATABASE_URL`

### 4. Configurar Variáveis de Ambiente

No Railway Dashboard → Variables, adicione:

```
BOT_TOKEN=8760632368:AAEp_n2rGPtRJatoPVksqkpl658OBSK89ow
ADMIN_TELEGRAM_ID=8649452369
SILLIENT_API_KEY=sp_live_810a34a0a85860235def74a554f3af24
SILLIENT_SECRET_KEY=sk_7eda4b706278a1b0a1fae032795a16bfb7b1e7a8847dc8ee3e32fca8d0b96942
MODE=webhook
WEBHOOK_URL=https://seu-app.up.railway.app
WEBHOOK_SECRET=tksbot_webhook_secret_2024
ENVIRONMENT=production
```

### 5. Obter URL do Webhook

1. Aguarde o deploy completar
2. Railway fornecerá uma URL (ex: `https://tksbot-production.up.railway.app`)
3. Adicione essa URL em `WEBHOOK_URL`
4. Re-deploy se necessário

---

## 🛠️ Configuração Webhook Telegram

Configure o webhook do Telegram (substitua pela sua URL):

```bash
curl -X POST \
  https://api.telegram.org/bot8760632368:AAEp_n2rGPtRJatoPVksqkpl658OBSK89ow/setWebhook \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://seu-app.up.railway.app/webhook",
    "secret_token": "tksbot_webhook_secret_2024"
  }'
```

---

## 💻 Desenvolvimento Local

### 1. Clonar e Instalar

```bash
# Clone
git clone https://github.com/SEU_USUARIO/tksbot.git
cd tksbot

# Criar ambiente virtual
python -m venv venv

# Ativar (Windows)
venv\Scripts\activate

# Ativar (Linux/Mac)
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
```

### 2. Configurar .env

Copie o template e ajuste:

```bash
cp .env.example .env
# Edite .env com suas configurações
```

### 3. Executar

```bash
python main.py
```

---

## 📊 Comandos do Bot

| Comando | Descrição |
|---------|-----------|
| `/start` | Iniciar bot / Menu principal |
| `/produtos` | Ver catálogo |
| `/carrinho` | Meu carrinho |
| `/pedidos` | Meus pedidos |
| `/conta` | Minha conta |
| `/suporte` | Central de ajuda |
| `/admin` | Painel admin (restrito) |
| `/cancelar` | Cancelar operação |
| `/help` | Ajuda |

---

## 🎨 Produtos Configurados

| Produto | Categoria | Preço |
|---------|-----------|-------|
| 💳 Info CC Gold | Cartões | R$ 150,00 |
| 💎 Info CC Platinum | Cartões | R$ 300,00 |
| 🏆 Info CC Infinite | Cartões | R$ 500,00 |
| ⭐ Info CC Basic | Cartões | R$ 80,00 |
| 🖤 Info CC Black | Cartões VIP | R$ 800,00 |
| 📄 Comprovante FK | Documentos | R$ 50,00 |
| 📋 Doc FK App | Documentos | R$ 75,00 |

---

## 🔧 Configurações Avançadas

### Webhook SillientPay

Configure no dashboard da SillientPay:

```
URL: https://seu-app.up.railway.app/webhook/sillientpay
Método: POST
Content-Type: application/json
```

### Cupons Padrão

- `BEMVINDO10` - 10% OFF (primeira compra)
- `VIP20` - 20% OFF (produtos VIP)
- `FLASH30` - 30% OFF (oferta relâmpago)

---

## 📝 Troubleshooting

### Erro: "Module not found"
```bash
pip install -r requirements.txt
```

### Erro: "Database locked" (SQLite)
Reinicie o bot. SQLite não suporta concorrência alta.

### Erro: "Webhook not found"
Verifique se a URL do webhook está correta e acessível.

### Erro: "Invalid token"
Verifique se o BOT_TOKEN está correto no .env

---

## 🔐 Segurança

- ✅ Tokens em .env (nunca commite!)
- ✅ SQL Injection protection (SQLAlchemy ORM)
- ✅ Input sanitization
- ✅ Rate limiting por usuário
- ✅ Anti-flood protection
- ✅ Webhook signature validation

---

## 📈 Roadmap

- [ ] Pagamento com Cartão de Crédito
- [ ] Sistema de Assinaturas
- [ ] API REST para integrações
- [ ] Dashboard web em Flask
- [ ] Suporte a múltiplos gateways
- [ ] Sistema de tickets
- [ ] Analytics avançado
- [ ] App mobile híbrido

---

## 🆘 Suporte

Problemas? Entre em contato:

- Telegram: [@suporte_tksbot](https://t.me/suporte_tksbot)
- Email: suporte@tksbot.com

---

## 📄 Licença

Este projeto é proprietário e confidencial.
Uso exclusivo do licenciado.

---

**Feito com 💎 pelo TksBot Team**

*Versão 2.0.0 Premium - Enterprise Edition*
