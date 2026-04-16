"""
Support Handler - Suporte ao cliente
"""

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from app.config import config
from utils.keyboards import Keyboards


async def support_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler de suporte via comando"""
    await show_support(update, context)


async def show_support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mostra menu de suporte"""
    message = f"""
🆘 *CENTRAL DE AJUDA*

Como podemos ajudar você?

❓ *PERGUNTAS FREQUENTES*
Veja as respostas mais comuns

📞 *FALAR COM ATENDENTE*
Suporte humano especializado

📄 *POLÍTICAS*
Reembolso, privacidade, termos

⚡ *RESPOSTA RÁPIDA*
Atendimento em até 24h
    """
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            message,
            parse_mode='Markdown',
            reply_markup=Keyboards.support()
        )
    else:
        await update.message.reply_text(
            message,
            parse_mode='Markdown',
            reply_markup=Keyboards.support()
        )


async def support_faq_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mostra FAQ"""
    query = update.callback_query
    await query.answer()
    
    message = f"""
❓ *PERGUNTAS FREQUENTES*

*1. Como funciona a entrega?*
Após confirmação do pagamento, o produto é entregue automaticamente no chat.

*2. Quanto tempo leva?*
PIX: Aprovação em segundos, entrega imediata.

*3. É seguro?*
Sim! Usamos criptografia e não armazenamos dados sensíveis.

*4. Posso reembolsar?*
Reembolsos em até 7 dias se o produto não for entregue.

*5. Como usar os produtos?*
Cada produto inclui instruções detalhadas na entrega.

*6. O que são produtos VIP?*
Produtos exclusivos para membros VIP com descontos especiais.

*7. Como virar VIP?*
Realize 5 compras ou adquira o pacote VIP diretamente.

*8. Tenho garantia?*
Sim! Garantia de entrega ou dinheiro de volta.

Tem mais dúvidas? Fale com um atendente! 👇
    """
    
    await query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=Keyboards.support()
    )


async def support_chat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Abre chat com atendente"""
    query = update.callback_query
    await query.answer()
    
    message = f"""
📞 *FALAR COM ATENDENTE*

Nossa equipe está pronta para ajudar!

🔗 *LINK DIRETO:*
{config.SUPPORT_URL}

⏰ *HORÁRIO DE ATENDIMENTO*
Segunda a Sexta: 9h às 18h
Sábado: 9h às 14h

⚡ *RESPOSTA RÁPIDA*
Geralmente respondemos em menos de 2h!

📧 *EMAIL*
suporte@{config.BOT_USERNAME}.com

Descreva sua dúvida com:
• Seu ID do Telegram
• Número do pedido (se houver)
• Descrição detalhada
    """
    
    await query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=Keyboards.support()
    )


async def support_refund_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mostra política de reembolso"""
    query = update.callback_query
    await query.answer()
    
    message = f"""
📄 *POLÍTICA DE REEMBOLSO*

*REEMBOLSO TOTAL*
✅ Produto não entregue
✅ Produto com defeito
✅ Erro no sistema
✅ Dentro de 7 dias

*SEM REEMBOLSO*
❌ Produto já entregue e usado
❌ Após 7 dias da compra
❌ Desistência após entrega
❌ Uso indevido do produto

*COMO SOLICITAR*
1. Contate o suporte
2. Informe o número do pedido
3. Explique o motivo
4. Aguarde análise (até 48h)

*PRAZO*
Aprovado: reembolso em 3-5 dias úteis

Qualquer dúvida, fale conosco! 👇
    """
    
    await query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=Keyboards.support()
    )


async def support_callback_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Roteador de callbacks de suporte"""
    query = update.callback_query
    data = query.data
    
    if data == "menu_support":
        await show_support(update, context)
    
    elif data == "support_faq":
        await support_faq_handler(update, context)
    
    elif data == "support_chat":
        await support_chat_handler(update, context)
    
    elif data == "support_refund":
        await support_refund_handler(update, context)
