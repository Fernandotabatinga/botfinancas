# handlers/reminders.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database.db_operations import get_user, add_reminder, get_pending_reminders, mark_reminder_as_paid
from keyboards import create_main_keyboard, create_reminder_keyboard, create_yes_no_keyboard
from datetime import datetime
from utils.helpers import parse_date_from_text, extract_amount_from_text
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

router = Router()

class ReminderStates(StatesGroup):
    waiting_for_description = State()
    waiting_for_amount = State()
    waiting_for_date = State()
    waiting_for_recurring = State()
    waiting_for_recurrence_type = State()
    waiting_for_recurrence_day = State()
    waiting_for_reminder_action = State()

@router.message(Command("reminders"))
@router.message(F.text == "🔔 Lembretes")
async def cmd_reminders(message: Message):
    user = get_user(message.from_user.id)
    if not user:
        await message.answer(
            "Você precisa se cadastrar primeiro. Use o comando /start para começar."
        )
        return
    
    reminders = get_pending_reminders(message.from_user.id)
    
    if not reminders:
        await message.answer(
            "Você não tem lembretes pendentes. Use o comando /add_reminder para adicionar um novo lembrete.",
            reply_markup=create_main_keyboard()
        )
        return
    
    await message.answer(
        "Seus lembretes pendentes:",
        reply_markup=create_reminder_keyboard(reminders)
    )

@router.message(Command("add_reminder"))
async def cmd_add_reminder(message: Message, state: FSMContext):
    user = get_user(message.from_user.id)
    if not user:
        await message.answer(
            "Você precisa se cadastrar primeiro. Use o comando /start para começar."
        )
        return
    
    await message.answer(
        "Vamos criar um lembrete de pagamento. Por favor, me diga qual é a conta a pagar:"
    )
    await state.set_state(ReminderStates.waiting_for_description)

@router.message(ReminderStates.waiting_for_description)
async def process_reminder_description(message: Message, state: FSMContext):
    description = message.text
    await state.update_data(description=description)
    
    await message.answer(
        "Qual é o valor a ser pago?"
    )
    await state.set_state(ReminderStates.waiting_for_amount)

@router.message(ReminderStates.waiting_for_amount)
async def process_reminder_amount(message: Message, state: FSMContext):
    try:
        amount = float(message.text.replace(',', '.'))
        await state.update_data(amount=amount)
        
        await message.answer(
            "Qual é a data de vencimento? (formato DD/MM/AAAA ou 'dia 10')"
        )
        await state.set_state(ReminderStates.waiting_for_date)
    except ValueError:
        await message.answer(
            "Por favor, digite apenas números para o valor. Tente novamente:"
        )

@router.message(ReminderStates.waiting_for_date)
async def process_reminder_date(message: Message, state: FSMContext):
    date = parse_date_from_text(message.text)
    
    if not date:
        await message.answer(
            "Formato de data inválido. Por favor, use o formato DD/MM/AAAA ou 'dia X':"
        )
        return
    
    await state.update_data(date=date)
    
    await message.answer(
        "Este é um lembrete recorrente? (ex: conta mensal)",
        reply_markup=create_yes_no_keyboard()
    )
    await state.set_state(ReminderStates.waiting_for_recurring)

@router.callback_query(ReminderStates.waiting_for_recurring)
async def process_reminder_recurring(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    is_recurring = callback.data == "yes"
    await state.update_data(is_recurring=is_recurring)
    
    if is_recurring:
        await callback.message.answer(
            "Qual é a recorrência? (mensal, semanal, etc.)"
        )
        await state.set_state(ReminderStates.waiting_for_recurrence_type)
    else:
        # Finalizar criação do lembrete não recorrente
        await finish_reminder_creation(callback.message, state)

@router.message(ReminderStates.waiting_for_recurrence_type)
async def process_recurrence_type(message: Message, state: FSMContext):
    recurrence_type = message.text.lower()
    valid_types = ["mensal", "semanal", "quinzenal", "bimestral", "trimestral", "semestral", "anual"]
    
    if recurrence_type not in valid_types:
        await message.answer(
            f"Tipo de recorrência inválido. Por favor, escolha entre: {', '.join(valid_types)}"
        )
        return
    
    await state.update_data(recurrence_type=recurrence_type)
    
    if recurrence_type == "mensal":
        await message.answer(
            "Em qual dia do mês o pagamento deve ser feito? (1-31)"
        )
        await state.set_state(ReminderStates.waiting_for_recurrence_day)
    else:
        # Para outros tipos de recorrência, podemos usar a data informada
        await finish_reminder_creation(message, state)

@router.message(ReminderStates.waiting_for_recurrence_day)
async def process_recurrence_day(message: Message, state: FSMContext):
    try:
        day = int(message.text)
        if day < 1 or day > 31:
            raise ValueError("Dia inválido")
        
        await state.update_data(recurrence_day=day)
        await finish_reminder_creation(message, state)
    except ValueError:
        await message.answer(
            "Por favor, digite um número válido entre 1 e 31."
        )

async def finish_reminder_creation(message: Message, state: FSMContext):
    user = get_user(message.from_user.id)
    data = await state.get_data()
    
    reminder = add_reminder(
        message.from_user.id,
        data['description'],
        data['amount'],
        data['date'],
        is_recurring=data.get('is_recurring', False),
        recurrence_type=data.get('recurrence_type'),
        recurrence_day=data.get('recurrence_day')
    )
    
    recurrence_info = ""
    if data.get('is_recurring'):
        recurrence_info = f"\nRecorrência: {data.get('recurrence_type', 'Não definida')}"
        if data.get('recurrence_day'):
            recurrence_info += f"\nDia do mês: {data.get('recurrence_day')}"
    
    await message.answer(
        f"✅ Lembrete criado com sucesso!\n\n"
        f"Descrição: {data['description']}\n"
        f"Valor: {user.currency} {data['amount']:.2f}\n"
        f"Data de vencimento: {data['date'].strftime('%d/%m/%Y')}{recurrence_info}",
        reply_markup=create_main_keyboard()
    )
    await state.clear()

@router.callback_query(F.data.startswith("reminder_"))
async def process_reminder_selection(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    reminder_id = int(callback.data.split("_")[1])
    
    await state.update_data(reminder_id=reminder_id)
    
    await callback.message.answer(
        "O que você deseja fazer com este lembrete?",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="✅ Marcar como pago", callback_data="mark_paid")],
                [InlineKeyboardButton(text="🗑️ Excluir", callback_data="delete_reminder")],
                [InlineKeyboardButton(text="🔙 Voltar", callback_data="back_to_reminders")]
            ]
        )
    )
    await state.set_state(ReminderStates.waiting_for_reminder_action)

@router.callback_query(ReminderStates.waiting_for_reminder_action, F.data == "mark_paid")
async def mark_reminder_paid(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    data = await state.get_data()
    reminder_id = data.get('reminder_id')
    
    if reminder_id:
        reminder = mark_reminder_as_paid(reminder_id, callback.from_user.id)
        if reminder:
            await callback.message.answer(
                f"✅ Lembrete '{reminder.description}' marcado como pago!",
                reply_markup=create_main_keyboard()
            )
        else:
            await callback.message.answer(
                "Não foi possível encontrar o lembrete.",
                reply_markup=create_main_keyboard()
            )
    
    await state.clear()

@router.callback_query(ReminderStates.waiting_for_reminder_action, F.data == "delete_reminder")
async def delete_reminder(callback: CallbackQuery, state: FSMContext):
    # Implementar a lógica para excluir o lembrete
    await callback.answer("Funcionalidade em desenvolvimento")
    await state.clear()

@router.callback_query(ReminderStates.waiting_for_reminder_action, F.data == "back_to_reminders")
async def back_to_reminders(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await cmd_reminders(callback.message)
    await state.clear()

