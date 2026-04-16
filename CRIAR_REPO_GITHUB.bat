@echo off
chcp 65001 >nul
title Criar Repositorio TksBot no GitHub
echo.
echo ============================================
echo   🚀 TksBot - Criar Repositorio GitHub
echo ============================================
echo.
echo Este script vai enviar seu codigo para o GitHub!
echo.

set /p GITHUB_USER="Digite seu nome de usuario GitHub: "

if "%GITHUB_USER%"=="" (
    echo.
    echo ❌ ERRO: Usuario nao pode ser vazio!
    pause
    exit /b 1
)

echo.
echo 🔗 Configurando remote para: github.com/%GITHUB_USER%/tksbot
echo.

cd /d "c:\Users\davip\Nova pasta\bot2"

REM Remove remote antigo se existir
git remote remove origin 2>nul

REM Adiciona novo remote
git remote add origin https://github.com/%GITHUB_USER%/tksbot.git

echo 🚀 Enviando codigo para GitHub...
echo.

git branch -M main
git push -u origin main

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ============================================
    echo   ❌ ERRO AO ENVIAR!
    echo ============================================
    echo.
    echo Provaveis causas:
    echo.
    echo 1. ⬜ Repositorio 'tksbot' NAO existe no GitHub
    echo    SOLUCAO: Crie em https://github.com/new
    echo.
    echo 2. ⬜ Nao esta logado no Git no computador
    echo    SOLUCAO: Execute: git config --global credential.helper manager
    echo.
    echo 3. ⬜ Problema de autenticacao
    echo    SOLUCAO: Configure token GitHub ou login
    echo.
    pause
    exit /b 1
)

echo.
echo ============================================
echo   ✅ SUCESSO! Codigo enviado!
echo ============================================
echo.
echo 📍 Repositorio: https://github.com/%GITHUB_USER%/tksbot
echo.
echo 🎯 PROXIMOS PASSOS:
echo.
echo 1. Acesse o link acima para verificar
echo 2. No Railway.app, conecte este repositorio
    echo 3. Adicione PostgreSQL no Railway
echo 4. Configure as variaveis de ambiente
echo 5. Deploy automatico a cada commit!
echo.
echo 🔗 Link Railway: https://railway.app
echo.
pause
start https://github.com/%GITHUB_USER%/tksbot
