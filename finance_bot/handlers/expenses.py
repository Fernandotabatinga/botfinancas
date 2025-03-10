# handlers/expenses.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database.db_operations import get_user, add_transaction
from utils.nlp_processor import extract_transaction_info
from keyboards import create_main_keyboard, create_category_keyboard, create_add_keyboard
from datetime import datetime

router = Router()

class ExpenseStates(StatesGroup):
    waiting_for_expense = State()
    waiting_for_category = State()
    waiting_for_description = State()
    waiting_for_date = State()

@router.message(F.text.startswith("Gastei"))
@router.message(F.text.startswith("gastei"))
async def process_expense_text(message: Message):
    user = get_user(message.from_user.id)
    if not user:
        await message.answer(
            "Você precisa se cadastrar primeiro. Use o comando /start para começar."
        )
        return
    
    amount, category, description, date, is_expense = extract_transaction_info(message.text)
    
    if amount > 0:
        transaction = add_transaction(
            message.from_user.id,
            amount,
            description,
            category,
            date,
            is_expense=True
        )
        
        await message.answer(
            f"✅ Despesa registrada com sucesso!\n\n"
            f"Valor: {user.currency} {amount:.2f}\n"
            f"Categoria: {category}\n"
            f"Descrição: {description}\n"
            f"Data: {date.strftime('%d/%m/%Y')}"
        )
    else:
        await message.answer(
            "Não consegui identificar o valor da despesa. Por favor, tente novamente ou use o comando /add para adicionar manualmente."
        )

@router.message(Command("add"))
@router.message(F.text == "💸 Adicionar Despesa")
async def cmd_add(message: Message, state: FSMContext):
    user = get_user(message.from_user.id)
    if not user:
        await message.answer(
            "Você precisa se cadastrar primeiro. Use o comando /start para começar."
        )
        return
    
    await message.answer(
        f"Digite o valor da despesa em {user.currency}:"
    )
    await state.set_state(ExpenseStates.waiting_for_expense)

@router.message(ExpenseStates.waiting_for_expense)
async def process_expense_amount(message: Message, state: FSMContext):
    try:
        amount = float(message.text.replace(',', '.'))
        await state.update_data(amount=amount)
        
        await message.answer(
            "Selecione a categoria:",
            reply_markup=create_category_keyboard(message.from_user.id)
        )
        await state.set_state(ExpenseStates.waiting_for_category)
    except ValueError:
        await message.answer(
            "Por favor, digite apenas números para o valor. Tente novamente:"
        )

@router.callback_query(ExpenseStates.waiting_for_category)
async def process_expense_category(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    category = callback.data
    
    if category == "new_category":
        await callback.message.answer(
            "Digite o nome da nova categoria:"
        )
        return
    
    await state.update_data(category=category)
    
    await callback.message.answer(
        "Digite uma descrição para essa despesa:"
    )
    await state.set_state(ExpenseStates.waiting_for_description)

@router.message(ExpenseStates.waiting_for_description)
async def process_expense_description(message: Message, state: FSMContext):
    description = message.text
    await state.update_data(description=description)
    
    await message.answer(
        "Digite a data da despesa (formato DD/MM/AAAA) ou envie 'hoje' para usar a data atual:"
    )
    await state.set_state(ExpenseStates.waiting_for_date)

@router.message(ExpenseStates.waiting_for_date)
async def process_expense_date(message: Message, state: FSMContext):
    user = get_user(message.from_user.id)
    data = await state.get_data()
    
    if message.text.lower() == "hoje":
        date = datetime.now().date()
    else:
        try:
            date = datetime.strptime(message.text, "%d/%m/%Y").date()
        except ValueError:
            await message.answer(
                "Formato de data inválido. Por favor, use o formato DD/MM/AAAA ou digite 'hoje':"
            )
            return
    
    transaction = add_transaction(
        message.from_user.id,
        data['amount'],
        data['description'],
        data['category'],
        date,
        is_expense=True
    )
    
    await message.answer(
        f"✅ Despesa registrada com sucesso!\n\n"
        f"Valor: {user.currency} {data['amount']:.2f}\n"
        f"Categoria: {data['category']}\n"
        f"Descrição: {data['description']}\n"
        f"Data: {date.strftime('%d/%m/%Y')}",
        reply_markup=create_main_keyboard()
    )
    await state.clear()
