# handlers/reports.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database.db_operations import get_user, get_monthly_summary, get_category_expenses
from utils.chart_generator import generate_expense_pie_chart, generate_monthly_comparison_chart, generate_budget_progress_chart
from utils.ai_suggestions import generate_spending_insights, generate_savings_recommendations
from keyboards import create_main_keyboard, create_category_keyboard, create_report_keyboard
from datetime import datetime

router = Router()

class ReportStates(StatesGroup):
    waiting_for_month = State()
    waiting_for_category = State()

@router.message(Command("report"))
@router.message(F.text == "📊 Relatórios")
async def cmd_report(message: Message):
    user = get_user(message.from_user.id)
    if not user:
        await message.answer(
            "Você precisa se cadastrar primeiro. Use o comando /start para começar."
        )
        return
    
    await message.answer(
        "Que tipo de relatório você deseja ver?",
        reply_markup=create_report_keyboard()
    )

@router.callback_query(F.data == "monthly_summary")
async def show_monthly_summary(callback: CallbackQuery):
    await callback.answer()
    user = get_user(callback.from_user.id)
    
    # Obter resumo do mês atual
    today = datetime.now()
    summary = get_monthly_summary(callback.from_user.id, today.month, today.year)
    
    if not summary:
        await callback.message.answer(
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
    
    message_text += "\n<b>Status dos Orçamentos:</b>\n"
    for category, status in summary['budget_status'].items():
        percentage = status['percentage']
        emoji = "🟢" if percentage < 80 else "🟠" if percentage < 100 else "🔴"
        message_text += f"{emoji} {category}: {percentage:.1f}% ({user.currency} {status['spent']:.2f}/{status['budget']:.2f})\n"
    
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
    await callback.message.answer_photo(
        photo=chart_buffer,
        caption=message_text,
        reply_markup=create_main_keyboard()
    )

@router.callback_query(F.data == "category_report")
async def select_category_report(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    
    await callback.message.answer(
        "Selecione a categoria para ver o relatório:",
        reply_markup=create_category_keyboard(callback.from_user.id)
    )
    await state.set_state(ReportStates.waiting_for_category)

@router.callback_query(ReportStates.waiting_for_category)
async def show_selected_category_report(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    user = get_user(callback.from_user.id)
    category = callback.data
    
    if category == "new_category":
        await callback.message.answer(
            "Primeiro crie a categoria antes de gerar um relatório para ela.",
            reply_markup=create_main_keyboard()
        )
        await state.clear()
        return
    
    # Obter despesas da categoria no mês atual
    today = datetime.now()
    result = get_category_expenses(callback.from_user.id, category, today.month, today.year)
    
    if not result:
        await callback.message.answer(
            f"Não encontrei despesas na categoria '{category}' para este mês.",
            reply_markup=create_main_keyboard()
        )
        await state.clear()
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
    
    await callback.message.answer(message_text, reply_markup=create_main_keyboard())
    await state.clear()

@router.callback_query(F.data == "month_comparison")
async def show_month_comparison(callback: CallbackQuery):
    await callback.answer()
    user = get_user(callback.from_user.id)
    
    # Obter dados dos últimos 3 meses
    today = datetime.now()
    current_month = today.month
    current_year = today.year
    
    monthly_data = {}
    
    for i in range(3):
        month = current_month - i
        year = current_year
        if month <= 0:
            month += 12
            year -= 1
        
        month_name = datetime(year, month, 1).strftime("%b/%Y")
        summary = get_monthly_summary(callback.from_user.id, month, year)
        
        if summary:
            monthly_data[month_name] = summary
    
    if not monthly_data:
        await callback.message.answer(
            "Não encontrei transações para os últimos meses.",
            reply_markup=create_main_keyboard()
        )
        return
    
    # Criar mensagem de comparação
    message_text = f"📊 <b>Comparação dos Últimos Meses</b>\n\n"
    
    # Tabela de comparação
    message_text += "<pre>"
    message_text += f"{'Mês':<10}{'Receitas':<15}{'Despesas':<15}{'Saldo':<15}\n"
    message_text += "-" * 50 + "\n"
    
    for month_name, summary in monthly_data.items():
        income = summary['total_income']
        expense = summary['total_expense']
        balance = summary['balance']
        
        message_text += f"{month_name:<10}{user.currency} {income:<10.2f}{user.currency} {expense:<10.2f}{user.currency} {balance:<10.2f}\n"
    
    message_text += "</pre>"
    
    # Gerar gráfico de comparação
    chart_buffer = generate_monthly_comparison_chart(monthly_data, user.currency)
    
    # Enviar mensagem com gráfico
    await callback.message.answer_photo(
        photo=chart_buffer,
        caption=message_text,
        reply_markup=create_main_keyboard()
    )

@router.callback_query(F.data == "insights")
async def show_insights(callback: CallbackQuery):
    await callback.answer()
    user = get_user(callback.from_user.id)
    
    # Gerar insights
    insights = generate_spending_insights(callback.from_user.id)
    recommendations = generate_savings_recommendations(callback.from_user.id)
    
    if not insights and not recommendations:
        await callback.message.answer(
            "Ainda não temos dados suficientes para gerar insights. Continue registrando suas transações!",
            reply_markup=create_main_keyboard()
        )
        return
    
    # Criar mensagem com insights
    message_text = f"💡 <b>Insights e Recomendações Financeiras</b>\n\n"
    
    if insights:
        message_text += "<b>Análise dos seus gastos:</b>\n"
        for insight in insights:
            message_text += f"• {insight}\n"
        message_text += "\n"
    
    if recommendations:
        message_text += "<b>Recomendações para economizar:</b>\n"
        for recommendation in recommendations:
            message_text += f"• {recommendation}\n"
    
    # Obter resumo do mês atual para gerar gráfico de orçamento
    today = datetime.now()
    summary = get_monthly_summary(callback.from_user.id, today.month, today.year)
    
    if summary and summary['budget_status']:
        # Gerar gráfico de progresso do orçamento
        chart_buffer = generate_budget_progress_chart(summary['budget_status'], user.currency)
        
        # Enviar mensagem com gráfico
        await callback.message.answer_photo(
            photo=chart_buffer,
            caption=message_text,
            reply_markup=create_main_keyboard()
        )
    else:
        # Enviar apenas o texto se não houver dados para o gráfico
        await callback.message.answer(
            message_text,
            reply_markup=create_main_keyboard()
        )
