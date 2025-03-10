# handlers/future_income.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database.db_operations import get_user, add_future_income
from keyboards import create_main_keyboard, create_income_category_keyboard
from datetime import datetime
from utils.helpers import parse_date_from_text
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

router = Router()

class FutureIncomeStates(StatesGroup):
    waiting_for_amount = State()
    waiting_for_description = State()
    waiting_for_date = State()
    waiting_for_category = State()

@router.message(Command("future_income"))
@router.message(F.text == "📆 Receitas Futuras")
async def cmd_future_income(message: Message):
    user = get_user(message.from_user.id)
    if not user:
        await message.answer(
            "Você precisa se cadastrar primeiro. Use o comando /start para começar."
        )
        return
    
    # Aqui você pode implementar a lógica para mostrar as receitas futuras
    # Por enquanto, vamos apenas oferecer a opção de adicionar uma nova
    await message.answer(
        "Aqui você pode gerenciar suas receitas futuras. O que deseja fazer?",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="➕ Adicionar Nova Receita", callback_data="add_future_income")]
            ]
        )
    )

@router.callback_query(F.data == "add_future_income")
@router.message(Command("add_future_income"))
async def cmd_add_future_income(message: Message, state: FSMContext):
    user = get_user(message.from_user.id)
    if not user:
        await message.answer(
            "Você precisa se cadastrar primeiro. Use o comando /start para começar."
        )
        return
    
    if isinstance(message, CallbackQuery):
        message = message.message
        await message.answer(
            f"Vamos registrar uma receita futura. Por favor, me diga o valor que você irá receber em {user.currency}:"
        )
    else:
        await message.answer(
            f"Vamos registrar uma receita futura. Por favor, me diga o valor que você irá receber em {user.currency}:"
        )
    
    await state.set_state(FutureIncomeStates.waiting_for_amount)

@router.message(FutureIncomeStates.waiting_for_amount)
async def process_future_income_amount(message: Message, state: FSMContext):
    try:
        amount = float(message.text.replace(',', '.'))
        await state.update_data(amount=amount)
        
        await message.answer(
            "Digite uma descrição para essa receita futura:"
        )
        await state.set_state(FutureIncomeStates.waiting_for_description)
    except ValueError:
        await message.answer(
            "Por favor, digite apenas números para o valor. Tente novamente:"
        )

@router.message(FutureIncomeStates.waiting_for_description)
async def process_future_income_description(message: Message, state: FSMContext):
    description = message.text
    await state.update_data(description=description)
    
    await message.answer(
        "Quando você espera receber este valor? (formato DD/MM/AAAA ou 'dia 10')"
    )
    await state.set_state(FutureIncomeStates.waiting_for_date)

@router.message(FutureIncomeStates.waiting_for_date)
async def process_future_income_date(message: Message, state: FSMContext):
    date = parse_date_from_text(message.text)
    
    if not date:
        await message.answer(
            "Formato de data inválido. Por favor, use o formato DD/MM/AAAA ou 'dia X':"
        )
        return
    
    await state.update_data(date=date)
    
    await message.answer(
        "Selecione a categoria desta receita:",
        reply_markup=create_income_category_keyboard(message.from_user.id)
    )
    await state.set_state(FutureIncomeStates.waiting_for_category)

@router.callback_query(FutureIncomeStates.waiting_for_category)
async def process_future_income_category(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    category = callback.data
    
    if category == "new_income_category":
        await callback.message.answer(
            "Digite o nome da nova categoria de receita:"
        )
        return
    
    await state.update_data(category=category)
    await finish_future_income_creation(callback.message, state)

async def finish_future_income_creation(message: Message, state: FSMContext):
    user = get_user(message.from_user.id)
    data = await state.get_data()
    
    future_income = add_future_income(
        message.from_user.id,
        data['amount'],
        data['description'],
        data['date']
    )
    
    await message.answer(
        f"✅ Receita futura registrada com sucesso!\n\n"
        f"Valor: {user.currency} {data['amount']:.2f}\n"
        f"Descrição: {data['description']}\n"
        f"Data esperada: {data['date'].strftime('%d/%m/%Y')}\n"
        f"Categoria: {data.get('category', 'Não categorizada')}",
        reply_markup=create_main_keyboard()
    )
    await state.clear()
