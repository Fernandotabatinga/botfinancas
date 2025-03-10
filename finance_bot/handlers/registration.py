# handlers/registration.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database.db_operations import get_user, create_user
from keyboards import create_main_keyboard, create_currency_keyboard

router = Router()

class RegistrationStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_currency = State()
    waiting_for_income = State()

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    user = get_user(message.from_user.id)
    
    if user:
        await message.answer(
            f"Bem-vindo de volta, {user.name}! Estou aqui para ajudar com suas finanças.",
            reply_markup=create_main_keyboard()
        )
    else:
        await message.answer(
            "Olá! Sou seu assistente financeiro pessoal. Vamos configurar sua conta.\n\n"
            "Por favor, me diga seu nome:"
        )
        await state.set_state(RegistrationStates.waiting_for_name)

@router.message(RegistrationStates.waiting_for_name)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    
    await message.answer(
        "Obrigado! Agora, escolha a moeda que você utiliza:",
        reply_markup=create_currency_keyboard()
    )
    await state.set_state(RegistrationStates.waiting_for_currency)

@router.callback_query(RegistrationStates.waiting_for_currency)
async def process_currency(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    currency = callback.data
    await state.update_data(currency=currency)
    
    await callback.message.answer(
        f"Ótimo! Agora, por favor, me informe sua renda mensal estimada em {currency}:"
    )
    await state.set_state(RegistrationStates.waiting_for_income)

@router.message(RegistrationStates.waiting_for_income)
async def process_income(message: Message, state: FSMContext):
    try:
        income = float(message.text.replace(',', '.'))
        user_data = await state.get_data()
        
        create_user(
            message.from_user.id,
            user_data['name'],
            user_data['currency'],
            income
        )
        
        await message.answer(
            f"Cadastro concluído com sucesso, {user_data['name']}!\n\n"
            f"Sua renda mensal foi registrada como {user_data['currency']} {income:.2f}.\n\n"
            "Agora você pode registrar suas despesas e receitas, definir orçamentos e visualizar relatórios.\n\n"
            "Você pode me enviar mensagens como:\n"
            "• 'Gastei 50 no mercado hoje'\n"
            "• 'Recebi 2000 de salário'\n"
            "• 'Me mostre um resumo do mês'\n"
            "• 'Quanto gastei com alimentação?'\n"
            "• 'Lembre-me de pagar a conta de luz dia 10'",
            reply_markup=create_main_keyboard()
        )
        await state.clear()
    except ValueError:
        await message.answer(
            "Por favor, digite apenas números para sua renda mensal. Tente novamente:"
        )
