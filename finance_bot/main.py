# main.py
import asyncio
import logging

# Configurar logging com nível DEBUG para ver mensagens detalhadas
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from config import BOT_TOKEN
from handlers import registration, expenses, income, reports, budgets, reminders, future_income, export, general
from database.models import Base, engine
from scheduler import start_scheduler

async def main():
    logger.info("Iniciando o bot...")
    
    # Criar tabelas no banco de dados
    logger.debug("Criando tabelas no banco de dados...")
    Base.metadata.create_all(engine)
    
    # Inicializar o bot e o dispatcher
    logger.debug("Inicializando bot e dispatcher...")
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    
    # Remover webhook antes de iniciar o polling
    logger.debug("Removendo webhook...")
    await bot.delete_webhook(drop_pending_updates=True)
    
    # Registrar handlers
    logger.debug("Registrando handlers...")
    dp.include_router(registration.router)
    dp.include_router(expenses.router)
    dp.include_router(income.router)
    dp.include_router(reports.router)
    dp.include_router(budgets.router)
    dp.include_router(reminders.router)
    dp.include_router(future_income.router)
    dp.include_router(export.router)
    dp.include_router(general.router)  # Deve ser o último para capturar mensagens não tratadas
    
    # Iniciar o agendador de tarefas
    logger.debug("Iniciando agendador de tarefas...")
    asyncio.create_task(start_scheduler(bot))
    
    # Iniciar polling
    logger.info("Bot iniciado! Aguardando mensagens...")
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Erro ao iniciar o polling: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Erro fatal: {e}")
