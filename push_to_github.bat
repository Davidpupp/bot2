@echo off
chcp 65001 >nul
echo ============================================
echo  🚀 TksBot - Push para GitHub
echo ============================================
echo.

set /p GITHUB_USER="Digite seu usuario GitHub: "
echo.

if "%GITHUB_USER%"=="" (
    echo ❌ Usuario nao pode ser vazio!
    pause
    exit /b 1
)

cd /d "c:\Users\davip\Nova pasta\bot2"

echo 🔍 Verificando repositorio...
git status >nul 2>&1
if errorlevel 1 (
    echo ❌ Git nao inicializado. Inicializando...
    git init
)

echo.
echo 📦 Adicionando arquivos...
git add .

echo.
echo 💾 Criando commit...
git commit -m "feat: TksBot Premium v2.0.0 - Ready for production" 2>nul || echo ✅ Commit ja existe

echo.
echo 🔗 Configurando remote...
git remote remove origin 2>nul
git remote add origin https://github.com/%GITHUB_USER%/tksbot.git

echo.
echo 🚀 Enviando para GitHub...
git branch -M main
git push -u origin main

if errorlevel 1 (
    echo.
    echo ❌ ERRO: Push falou!
    echo.
    echo Possiveis causas:
    echo 1. Repositorio 'tksbot' nao existe no GitHub
    echo 2. Credenciais git nao configuradas
    echo 3. Problema de autenticacao
    echo.
    echo Solucao:
    echo 1. Crie o repositorio em: https://github.com/new
    echo 2. Execute: git config --global user.email "seu@email.com"
    echo 3. Execute: git config --global user.name "Seu Nome"
    pause
    exit /b 1
)

echo.
echo ============================================
echo  ✅ SUCESSO!
echo ============================================
echo.
echo Repositorio: https://github.com/%GITHUB_USER%/tksbot
echo.
echo Proximos passos:
echo 1. Acesse o link acima para verificar
echo 2. Integre com Railway: https://railway.app
echo 3. Configure as variaveis de ambiente
echo.
pause
