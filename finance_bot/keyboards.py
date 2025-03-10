# keyboards.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from database.db_operations import get_user_categories
import config

def create_main_keyboard():
    """Cria o teclado principal do bot"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💸 Adicionar Despesa"), KeyboardButton(text="💰 Adicionar Receita")],
            [KeyboardButton(text="📊 Relatórios"), KeyboardButton(text="💰 Orçamentos")],
            [KeyboardButton(text="🔔 Lembretes"), KeyboardButton(text="📆 Receitas Futuras")],
            [KeyboardButton(text="📤 Exportar"), KeyboardButton(text="⚙️ Configurações")]
        ],
        resize_keyboard=True
    )
    return keyboard

def create_currency_keyboard():
    """Cria o teclado para seleção de moeda"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="R$ (Real)", callback_data="R$"),
                InlineKeyboardButton(text="$ (Dólar)", callback_data="$")
            ],
            [
                InlineKeyboardButton(text="€ (Euro)", callback_data="€"),
                InlineKeyboardButton(text="£ (Libra)", callback_data="£")
            ]
        ]
    )
    return keyboard

def create_add_keyboard():
    """Cria o teclado para adicionar transações"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="💸 Despesa", callback_data="add_expense"),
                InlineKeyboardButton(text="💰 Receita", callback_data="add_income")
            ]
        ]
    )
    return keyboard

def create_category_keyboard(user_id):
    """Cria o teclado com as categorias do usuário"""
    categories = get_user_categories(user_id, income=False) or config.DEFAULT_CATEGORIES
    
    # Organizar em linhas de 2 botões
    buttons = []
    row = []
    
    for category in categories:
        if len(row) < 2:
            row.append(InlineKeyboardButton(text=category, callback_data=category))
        else:
            buttons.append(row)
            row = [InlineKeyboardButton(text=category, callback_data=category)]
    
    if row:  # Adicionar a última linha se não estiver vazia
        buttons.append(row)
    
    # Adicionar botão para criar nova categoria
    buttons.append([InlineKeyboardButton(text="➕ Nova Categoria", callback_data="new_category")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def create_income_category_keyboard(user_id):
    """Cria o teclado com categorias de receita"""
    income_categories = get_user_categories(user_id, income=True) or config.DEFAULT_INCOME_CATEGORIES
    
    # Organizar em linhas de 2 botões
    buttons = []
    row = []
    
    for category in income_categories:
        if len(row) < 2:
            row.append(InlineKeyboardButton(text=category, callback_data=category))
        else:
            buttons.append(row)
            row = [InlineKeyboardButton(text=category, callback_data=category)]
    
    if row:  # Adicionar a última linha se não estiver vazia
        buttons.append(row)
    
    # Adicionar botão para criar nova categoria
    buttons.append([InlineKeyboardButton(text="➕ Nova Categoria", callback_data="new_income_category")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def create_report_keyboard():
    """Cria o teclado para seleção de relatórios"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📊 Resumo Mensal", callback_data="monthly_summary")
            ],
            [
                InlineKeyboardButton(text="📈 Relatório por Categoria", callback_data="category_report")
            ],
            [
                InlineKeyboardButton(text="📅 Comparação entre Meses", callback_data="month_comparison")
            ],
            [
                InlineKeyboardButton(text="💡 Insights e Sugestões", callback_data="insights")
            ]
        ]
    )
    return keyboard

def create_export_keyboard():
    """Cria o teclado para seleção de formato de exportação"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📄 CSV", callback_data="csv"),
                InlineKeyboardButton(text="📊 Excel", callback_data="excel")
            ],
            [
                InlineKeyboardButton(text="📑 PDF", callback_data="pdf")
            ]
        ]
    )
    return keyboard

def create_settings_keyboard():
    """Cria o teclado para configurações"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="👤 Editar Perfil", callback_data="edit_profile")
            ],
            [
                InlineKeyboardButton(text="🏷️ Gerenciar Categorias", callback_data="manage_categories")
            ],
            [
                InlineKeyboardButton(text="🔔 Configurar Lembretes", callback_data="configure_reminders")
            ]
        ]
    )
    return keyboard

def create_yes_no_keyboard():
    """Cria um teclado simples de sim/não"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Sim", callback_data="yes"),
                InlineKeyboardButton(text="❌ Não", callback_data="no")
            ]
        ]
    )
    return keyboard

def create_reminder_keyboard(reminders):
    """Cria um teclado com os lembretes pendentes"""
    buttons = []
    
    for reminder in reminders:
        due_date = reminder.due_date.strftime("%d/%m")
        button_text = f"{reminder.description} - {due_date} - {reminder.amount:.2f}"
        buttons.append([InlineKeyboardButton(text=button_text, callback_data=f"reminder_{reminder.id}")])
    
    buttons.append([InlineKeyboardButton(text="➕ Novo Lembrete", callback_data="new_reminder")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def create_future_income_keyboard(future_incomes):
    """Cria um teclado com as receitas futuras"""
    buttons = []
    
    for income in future_incomes:
        expected_date = income.expected_date.strftime("%d/%m")
        button_text = f"{income.description} - {expected_date} - {income.amount:.2f}"
        buttons.append([InlineKeyboardButton(text=button_text, callback_data=f"future_income_{income.id}")])
    
    buttons.append([InlineKeyboardButton(text="➕ Nova Receita Futura", callback_data="new_future_income")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)
