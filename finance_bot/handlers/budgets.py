# handlers/budgets.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database.db_operations import get_user, set_budget
from keyboards import create_main_keyboard, create_category_keyboard
from datetime import datetime

router = Router()

class BudgetStates(StatesGroup):
    waiting_for_category = State()
    waiting_for_amount = State()

@router.message(Command("budget"))
@router.message(F.text == "💰 Orçamentos")
async def cmd_budget(message: Message, state: FSMContext):
    user = get_user(message.from_user.id)
    if not user:
        await message.answer(
            "Você precisa se cadastrar primeiro. Use o comando /start para começar."
        )
        return
    
    await message.answer(
        "Selecione a categoria para definir um orçamento:",
        reply_markup=create_category_keyboard(message.from_user.id)
    )
    await state.set_state(BudgetStates.waiting_for_category)

@router.callback_query(BudgetStates.waiting_for_category)
async def process_budget_category(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    category = callback.data
    
    if category == "new_category":
        await callback.message.answer(
            "Digite o nome da nova categoria:"
        )
        return
    
    await state.update_data(category=category)
    
    user = get_user(callback.from_user.id)
    
    await callback.message.answer(
        f"Digite o valor do orçamento mensal para '{category}' em {user.currency}:"
    )
    await state.set_state(BudgetStates.waiting_for_amount)

@router.message(BudgetStates.waiting_for_amount)
async def process_budget_amount(message: Message, state: FSMContext):
    try:
        amount = float(message.text.replace(',', '.'))
        user_data = await state.get_data()
        category = user_data['category']
        
        # Definir orçamento para o mês atual
        today = datetime.now()
        budget = set_budget(
            message.from_user.id,
            category,
            amount,
            today.month,
            today.year
        )
        
        user = get_user(message.from_user.id)
        
        await message.answer(
            f"✅ Orçamento definido com sucesso!\n\n"
            f"Categoria: {category}\n"
            f"Valor: {user.currency} {amount:.2f}\n"
            f"Mês: {today.strftime('%B/%Y')}",
            reply_markup=create_main_keyboard()
        )
        await state.clear()
    except ValueError:
        await message.answer(
            "Por favor, digite apenas números para o valor do orçamento. Tente novamente:"
        )
