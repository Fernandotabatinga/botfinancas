# handlers/general.py
from aiogram import Router, F
from aiogram.types import Message
from datetime import datetime
from database.db_operations import get_user, get_monthly_summary, get_category_expenses
from utils.nlp_processor import detect_intent
from utils.chart_generator import generate_expense_pie_chart
from utils.ai_suggestions import generate_spending_insights, generate_savings_recommendations
from keyboards import create_main_keyboard, create_category_keyboard

router = Router()

# Configurar este router para ter a menor prioridade
router.message.filter(F.text)

@router.message()
async def process_any_message(message: Message):
    """Processa qualquer mensagem e tenta entender a intenção do usuário"""
    user = get_user(message.from_user.id)
    if not user:
        await message.answer(
            "Você precisa se cadastrar primeiro. Use o comando /start para começar."
        )
        return
    
    # Detectar intenção do usuário
    intent, params = detect_intent(message.text)
    
    # Responder de acordo com a intenção
    if intent == "monthly_report":
        # Chamar a função que gera o relatório mensal
        await show_monthly_summary_from_text(message)
    
    elif intent == "category_report":
        # Chamar a função que gera o relatório por categoria
        category = params.get("category", "")
        await show_category_expenses_from_text(message, category)
    
    elif intent == "budget_set":
        # Iniciar fluxo para definir orçamento
        await start_budget_flow(message, params)
    
    elif intent == "add_reminder":
        # Iniciar fluxo para adicionar lembrete
        await start_reminder_flow(message, params)
    
    elif intent == "future_income":
        # Iniciar fluxo para registrar receita futura
        await start_future_income_flow(message, params)
    
    elif intent == "add_expense" or intent == "add_income":
        # Já tratado por outros handlers
        pass
    
    else:
        # Se não entender a intenção, pedir esclarecimento
        await message.answer(
            "Desculpe, não entendi o que você deseja. Você pode tentar novamente ou usar os botões abaixo:",
            reply_markup=create_main_keyboard()
        )

async def show_monthly_summary_from_text(message: Message):
    """Gera e envia um relatório mensal a partir de um pedido em texto"""
    user = get_user(message.from_user.id)
    
    # Obter resumo do mês atual
    today = datetime.now()
    summary = get_monthly_summary(message.from_user.id, today.month, today.year)
    
    if not summary:
        await message.answer(
            "Não encontrei transações para este mês.",
            reply_markup=create_main_keyboard()
        )
        return
    
    # Criar mensagem de resumo
    month_name = today.strftime("%B")
    message_text = f"📊 <b>Resumo Financeiro - {month_name}/{today.year}</b>\n\n"
    message_text += f"💰 <b>Receitas:</b> {user.currency} {summary['total_income']:.2f}\n"
    message_text += f"💸 <b>Despesas:</b> {user.currency} {summary['total_expense']:.2f}\n"
    message_text += f"🧮 <b>Saldo:</b> {user.currency} {summary['balance']:.2f}\n\n"
    
    message_text += "<b>Despesas por Categoria:</b>\n"
    for category, amount in summary['category_expenses'].items():
        message_text += f"• {category}: {user.currency} {amount:.2f}\n"
    
    # Adicionar informações sobre receitas futuras
    if summary['future_income_total'] > 0:
        message_text += f"\n<b>Receitas Futuras:</b> {user.currency} {summary['future_income_total']:.2f}\n"
        for income in summary['future_incomes']:
            date_str = income['date'].strftime("%d/%m")
            message_text += f"• {date_str}: {income['description']} - {user.currency} {income['amount']:.2f}\n"
    
    # Adicionar informações sobre lembretes
    if summary['reminder_total'] > 0:
        message_text += f"\n<b>Contas a Pagar:</b> {user.currency} {summary['reminder_total']:.2f}\n"
        for reminder in summary['reminders']:
            date_str = reminder['due_date'].strftime("%d/%m")
            message_text += f"• {date_str}: {reminder['description']} - {user.currency} {reminder['amount']:.2f}\n"
    
    # Gerar gráfico de pizza
    chart_buffer = generate_expense_pie_chart(summary['category_expenses'], user.currency)
    
    # Enviar mensagem com gráfico
    await message.answer_photo(
        photo=chart_buffer,
        caption=message_text,
        reply_markup=create_main_keyboard()
    )
    
    # Enviar insights e recomendações
    insights = generate_spending_insights(message.from_user.id)
    if insights:
        insights_text = "💡 <b>Insights sobre seus gastos:</b>\n\n"
        for insight in insights:
            insights_text += f"• {insight}\n"
        
        await message.answer(insights_text)
    
    recommendations = generate_savings_recommendations(message.from_user.id)
    if recommendations:
        recommendations_text = "💰 <b>Recomendações para economizar:</b>\n\n"
        for recommendation in recommendations:
            recommendations_text += f"• {recommendation}\n"
        
        await message.answer(recommendations_text)

async def show_category_expenses_from_text(message: Message, category_name):
    """Gera e envia um relatório de categoria a partir de um pedido em texto"""
    user = get_user(message.from_user.id)
    
    # Obter despesas da categoria no mês atual
    today = datetime.now()
    result = get_category_expenses(message.from_user.id, category_name, today.month, today.year)
    
    if not result:
        await message.answer(
            f"Não encontrei despesas na categoria '{category_name}' para este mês.",
            reply_markup=create_main_keyboard()
        )
        return
    
    # Criar mensagem de resumo
    month_name = today.strftime("%B")
    message_text = f"📊 <b>Despesas com {result['category']} - {month_name}/{today.year}</b>\n\n"
    message_text += f"💸 <b>Total:</b> {user.currency} {result['total']:.2f}\n"
    
    if result['budget'] > 0:
        message_text += f"📌 <b>Orçamento:</b> {user.currency} {result['budget']:.2f}\n"
        message_text += f"🧮 <b>Restante:</b> {user.currency} {result['remaining']:.2f}\n"
        message_text += f"📏 <b>Utilizado:</b> {result['percentage']:.1f}%\n\n"
    
    message_text += "<b>Transações:</b>\n"
    for transaction in result['transactions']:
        date_str = transaction.date.strftime("%d/%m")
        message_text += f"• {date_str}: {transaction.description} - {user.currency} {transaction.amount:.2f}\n"
    
    await message.answer(message_text, reply_markup=create_main_keyboard())

async def start_budget_flow(message: Message, params=None):
    """Inicia o fluxo para definir um orçamento"""
    from handlers.budgets import cmd_budget
    await cmd_budget(message)

async def start_reminder_flow(message: Message, params=None):
    """Inicia o fluxo para adicionar um lembrete"""
    from handlers.reminders import cmd_add_reminder
    await cmd_add_reminder(message)

async def start_future_income_flow(message: Message, params=None):
    """Inicia o fluxo para registrar uma receita futura"""
    from handlers.future_income import cmd_add_future_income
    await cmd_add_future_income(message)
