# 🚀 Setup GitHub Repository - TksBot

## Opção 1: Usando GitHub CLI (Recomendado)

### 1. Instale o GitHub CLI
Baixe em: https://cli.github.com/

### 2. Autentique
```bash
gh auth login
```

### 3. Crie o repositório e faça push
```bash
# Navegue até a pasta do projeto
cd "c:\Users\davip\Nova pasta\bot2"

# Crie repositório privado
ght repo create tksbot --private --source=. --push

# Ou público
ght repo create tksbot --public --source=. --push
```

---

## Opção 2: Usando GitHub Web + Git

### 1. Crie o repositório no GitHub
1. Acesse: https://github.com/new
2. Repository name: `tksbot`
3. Description: `TksBot - Plataforma Premium de Vendas no Telegram`
4. Escolha: Private ou Public
5. NÃO marque "Add a README" (já temos)
6. Clique em **Create repository**

### 2. Faça o push do código
```bash
# Navegue até a pasta
cd "c:\Users\davip\Nova pasta\bot2"

# Adicione o remote (substitua SEU_USUARIO)
git remote add origin https://github.com/SEU_USUARIO/tksbot.git

# Faça o push
git branch -M main
git push -u origin main
```

---

## Opção 3: Script Automatizado (Windows)

Salve como `push_to_github.bat` e execute:

```batch
@echo off
set /p GITHUB_USER="Digite seu usuario GitHub: "
cd /d "c:\Users\davip\Nova pasta\bot2"
git remote add origin https://github.com/%GITHUB_USER%/tksbot.git
git branch -M main
git push -u origin main
echo.
echo ✅ Codigo enviado para GitHub!
pause
```

---

## 🔗 Integração com Railway

Após criar o repositório:

1. Acesse https://railway.app
2. New Project → Deploy from GitHub repo
3. Escolha `tksbot`
4. Railway fará deploy automático a cada push!

---

## ⚙️ Configurações importantes

### .gitignore já configurado para ignorar:
- Arquivos de ambiente (.env)
- Banco de dados local (*.db)
- Logs (*.log)
- Cache Python (__pycache__)
- Virtual environments (venv/)

### Arquivos que serão enviados:
✅ Todo código fonte
✅ README.md
✅ requirements.txt
✅ Procfile
✅ .env.example (template seguro)
❌ .env (seu arquivo com senhas - NÃO será enviado)

---

## 🔐 Segurança

⚠️ **IMPORTANTE:** O arquivo `.env` com suas credenciais NÃO será enviado ao GitHub (está no .gitignore).

No Railway, você vai configurar as variáveis manualmente no dashboard.

---

## ✅ Verificação após push

Execute:
```bash
git status
```

Deve mostrar: "nothing to commit, working tree clean"

Acesse `https://github.com/SEU_USUARIO/tksbot` para confirmar!
