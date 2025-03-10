# handlers/export.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database.db_operations import get_user, get_user_transactions
from keyboards import create_main_keyboard, create_export_keyboard
import pandas as pd
import io
from datetime import datetime
from xhtml2pdf import pisa

router = Router()

class ExportStates(StatesGroup):
    waiting_for_format = State()

@router.message(Command("export"))
@router.message(F.text == "📤 Exportar")
async def cmd_export(message: Message, state: FSMContext):
    user = get_user(message.from_user.id)
    if not user:
        await message.answer(
            "Você precisa se cadastrar primeiro. Use o comando /start para começar."
        )
        return
    
    await message.answer(
        "Em qual formato você deseja exportar seus dados?",
        reply_markup=create_export_keyboard()
    )
    await state.set_state(ExportStates.waiting_for_format)

@router.callback_query(ExportStates.waiting_for_format)
async def process_export_format(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    export_format = callback.data
    user = get_user(callback.from_user.id)
    
    # Obter todas as transações do usuário
    transactions = get_user_transactions(callback.from_user.id)
    
    if not transactions:
        await callback.message.answer(
            "Você ainda não possui transações para exportar.",
            reply_markup=create_main_keyboard()
        )
        await state.clear()
        return
    
    # Criar DataFrame
    data = []
    for t in transactions:
        category = t.category.name if t.category else "Sem categoria"
        data.append({
            'Data': t.date.strftime('%d/%m/%Y'),
            'Tipo': 'Despesa' if t.is_expense else 'Receita',
            'Categoria': category,
            'Descrição': t.description,
            'Valor': t.amount
        })
    
    df = pd.DataFrame(data)
    
    # Exportar no formato escolhido
    buffer = io.BytesIO()
    filename = f"financas_{datetime.now().strftime('%Y%m%d')}"
    
    if export_format == "csv":
        df.to_csv(buffer, index=False, encoding='utf-8')
        buffer.seek(0)
        filename += ".csv"
        
    elif export_format == "excel":
        df.to_excel(buffer, index=False, engine='xlsxwriter')
        buffer.seek(0)
        filename += ".xlsx"
        
    elif export_format == "pdf":
        # Usando pandas para gerar um HTML e depois converter para PDF
        html = df.to_html(index=False)
        
        # Adicionar estilos básicos
        styled_html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                .header {{ text-align: center; margin-bottom: 20px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Relatório Financeiro</h1>
                <p>Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
                <p>Usuário: {user.name}</p>
            </div>
            {html}
        </body>
        </html>
        """
        
        pisa.CreatePDF(styled_html, dest=buffer)
        buffer.seek(0)
        filename += ".pdf"
    
    # Enviar arquivo
    await callback.message.answer_document(
        document=(filename, buffer),
        caption="Aqui está o seu relatório financeiro.",
        reply_markup=create_main_keyboard()
    )
    await state.clear()
