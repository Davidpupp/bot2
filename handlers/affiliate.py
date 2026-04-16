"""
Affiliate Handler - Programa de afiliados
"""

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from app.config import config
from app.database import db
from app.models import User, Affiliate
from services.analytics import analytics
from services.notifications import notifications
from utils.keyboards import Keyboards
from utils.helpers import format_currency


async def affiliate_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler de afiliado via comando"""
    await show_affiliate_dashboard(update, context)


async def show_affiliate_dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mostra dashboard de afiliado"""
    user = update.effective_user
    
    with db.get_session() as session:
        db_user = session.query(User).filter_by(telegram_id=user.id).first()
        
        if db_user is None:
            message = "❌ Você precisa iniciar o bot primeiro.\nUse /start"
            if update.callback_query:
                await update.callback_query.edit_message_text(message)
            else:
                await update.message.reply_text(message)
            return
        
        # Verificar se é afiliado
        affiliate = session.query(Affiliate).filter_by(user_id=db_user.id).first()
        
        if affiliate is None:
            # Mostrar opção de virar afiliado
            message = f"""
🤝 *PROGRAMA DE AFILIADOS*

Ganhe *{config.AFFILIATE_COMMISSION_PERCENT}%* em cada venda!

💰 *COMO FUNCIONA:*
1. Receba seu link exclusivo
2. Compartilhe com amigos
3. Ganhe comissão automática
4. Saque quando quiser

📊 *BENEFÍCIOS:*
• Comissão de {config.AFFILIATE_COMMISSION_PERCENT}%
• Pagamento via PIX
• Saque mínimo: {format_currency(config.MIN_AFFILIATE_PAYOUT)}
• Painel de estatísticas
• Materiais de divulgação

Quer começar a ganhar?
            """
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🚀 Virar Afiliado", callback_data="affiliate_join")],
                [InlineKeyboardButton("🔙 Voltar", callback_data="menu_account")]
            ])
        else:
            # Mostrar dashboard
            stats = analytics.get_affiliate_stats(affiliate.id)
            
            message = f"""
🤝 *PAINEL DE AFILIADO*

💰 *SALDO ATUAL*
{format_currency(affiliate.balance)}

📊 *ESTATÍSTICAS*
Total ganho: {format_currency(affiliate.total_earned)}
Indicados: {affiliate.total_referrals}
Vendas: {affiliate.total_orders}

🔗 *SEU CÓDIGO*
`{affiliate.code}`

Compartilhe seu link:
`https://t.me/{config.BOT_USERNAME}?start=ref_{affiliate.code}`
            """
            
            keyboard = Keyboards.affiliate_dashboard(float(affiliate.balance))
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            message,
            parse_mode='Markdown',
            reply_markup=keyboard
        )
    else:
        await update.message.reply_text(
            message,
            parse_mode='Markdown',
            reply_markup=keyboard
        )


async def affiliate_join_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Registra novo afiliado"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    
    with db.get_session() as session:
        db_user = session.query(User).filter_by(telegram_id=user.id).first()
        
        if db_user is None:
            await query.edit_message_text(
                "❌ Erro: Usuário não encontrado.",
                reply_markup=Keyboards.back_to_menu()
            )
            return
        
        # Verificar se já é afiliado
        existing = session.query(Affiliate).filter_by(user_id=db_user.id).first()
        if existing is not None:
            await query.answer("Você já é afiliado!", show_alert=True)
            await show_affiliate_dashboard(update, context)
            return
        
        # Criar afiliado
        affiliate = Affiliate(user_id=db_user.id)
        session.add(affiliate)
        session.commit()
    
    await query.answer("🎉 Bem-vindo ao programa de afiliados!")
    
    # Notificar admin
    await notifications.notify_admin(
        f"🤝 Novo afiliado registrado:\n"
        f"Nome: {user.full_name}\n"
        f"ID: {user.id}"
    )
    
    await show_affiliate_dashboard(update, context)


async def affiliate_link_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mostra link de afiliado"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    
    with db.get_session() as session:
        db_user = session.query(User).filter_by(telegram_id=user.id).first()
        affiliate = session.query(Affiliate).filter_by(user_id=db_user.id).first()
        
        if affiliate is None:
            return
        
        ref_link = f"https://t.me/{config.BOT_USERNAME}?start=ref_{affiliate.code}"
        
        message = f"""
🔗 *SEU LINK DE AFILIADO*

`{ref_link}`

📱 *Como usar:*
1. Copie o link acima
2. Compartilhe nas redes sociais
3. Quando alguém clicar e comprar, você ganha!

💡 *DICAS:*
• Compartilhe em grupos
• Poste no Facebook/Instagram
• Envie para amigos interessados
• Crie conteúdo sobre os produtos

Boa sorte! 🚀
        """
    
    await query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=Keyboards.affiliate_dashboard(0)  # Botão voltar
    )


async def affiliate_stats_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mostra estatísticas detalhadas"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    
    with db.get_session() as session:
        db_user = session.query(User).filter_by(telegram_id=user.id).first()
        affiliate = session.query(Affiliate).filter_by(user_id=db_user.id).first()
        
        if affiliate is None:
            return
        
        stats = analytics.get_affiliate_stats(affiliate.id)
        
        message = f"""
📊 *ESTATÍSTICAS DETALHADAS*

💰 FINANCEIRO
Saldo atual: {format_currency(stats['current_balance'])}
Total ganho: {format_currency(stats['total_earned'])}
Total pago: {format_currency(stats['total_paid'])}
Pendente: {format_currency(stats['pending_payout'])}

📈 PERFORMANCE
Indicados: {stats['total_referrals']}
Vendas: {stats['total_orders']}
Conversão: {(stats['total_orders'] / stats['total_referrals'] * 100) if stats['total_referrals'] > 0 else 0:.1f}%

💵 TAXA DE COMISSÃO
{config.AFFILIATE_COMMISSION_PERCENT}% por venda
        """
    
    await query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=Keyboards.affiliate_dashboard(float(affiliate.balance))
    )


async def affiliate_withdraw_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Solicita saque"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    
    with db.get_session() as session:
        db_user = session.query(User).filter_by(telegram_id=user.id).first()
        affiliate = session.query(Affiliate).filter_by(user_id=db_user.id).first()
        
        if affiliate is None:
            return
        
        balance = float(affiliate.balance)
        min_payout = config.MIN_AFFILIATE_PAYOUT
        
        if balance < min_payout:
            await query.answer(
                f"Saldo mínimo para saque: {format_currency(min_payout)}",
                show_alert=True
            )
            return
        
        # Formulário de saque
        message = f"""
💰 *SOLICITAR SAQUE*

Saldo disponível: {format_currency(balance)}

Digite o valor do saque:
Mínimo: {format_currency(min_payout)}
Máximo: {format_currency(balance)}

Formato: 50.00

/cancelar - voltar
        """
    
    await query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=Keyboards.affiliate_dashboard(balance)
    )
    
    context.user_data['awaiting'] = 'affiliate_withdraw'
    context.user_data['affiliate_balance'] = balance


async def affiliate_callback_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Roteador de callbacks de afiliado"""
    query = update.callback_query
    data = query.data
    
    if data == "affiliate_dashboard":
        await show_affiliate_dashboard(update, context)
    
    elif data == "affiliate_join":
        await affiliate_join_handler(update, context)
    
    elif data == "affiliate_link":
        await affiliate_link_handler(update, context)
    
    elif data == "affiliate_stats":
        await affiliate_stats_handler(update, context)
    
    elif data == "affiliate_withdraw":
        await affiliate_withdraw_handler(update, context)
    
    elif data == "affiliate_ranking":
        await query.edit_message_text(
            "🏆 Ranking - Em breve!",
            reply_markup=Keyboards.affiliate_dashboard(0)
        )
    
    elif data == "affiliate_material":
        await query.edit_message_text(
            "📚 Material de divulgação:\n\n"
            "• Banner 1: [link]\n"
            "• Banner 2: [link]\n"
            "• Texto promocional: [link]",
            reply_markup=Keyboards.affiliate_dashboard(0)
        )


# Handler de mensagens para saque
async def affiliate_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa mensagens de afiliado"""
    if context.user_data.get('awaiting') == 'affiliate_withdraw':
        try:
            amount = float(update.message.text.replace(',', '.'))
            max_balance = context.user_data.get('affiliate_balance', 0)
            
            if amount < config.MIN_AFFILIATE_PAYOUT:
                await update.message.reply_text(
                    f"❌ Mínimo para saque: {format_currency(config.MIN_AFFILIATE_PAYOUT)}"
                )
                return
            
            if amount > max_balance:
                await update.message.reply_text("❌ Valor maior que seu saldo!")
                return
            
            # Processar saque
            await update.message.reply_text(
                f"""
✅ *SAQUE SOLICITADO*

Valor: {format_currency(amount)}
Status: Em análise

Você receberá o PIX em até 48h úteis.
                """,
                parse_mode='Markdown'
            )
            
            context.user_data['awaiting'] = None
            
        except ValueError:
            await update.message.reply_text("❌ Valor inválido. Use formato: 50.00")
