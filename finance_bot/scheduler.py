# scheduler.py
import asyncio
import logging
from datetime import datetime, timedelta
from database.db_operations import get_pending_reminders
from database.models import User, Session as DBSession

async def check_reminders(bot):
    """Verifica lembretes pendentes e envia notificações"""
    logging.info("Verificando lembretes pendentes...")
    
    # Obter lembretes que vencem nos próximos 3 dias
    reminders = get_pending_reminders(days_ahead=3)
    
    # Agrupar lembretes por usuário
    user_reminders = {}
    for reminder in reminders:
        if reminder.user_id not in user_reminders:
            user_reminders[reminder.user_id] = []
        user_reminders[reminder.user_id].append(reminder)
    
    # Enviar notificações para cada usuário
    with DBSession() as session:
        for user_id, reminders in user_reminders.items():
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                continue
            
            # Filtrar lembretes que não foram notificados recentemente
            now = datetime.now()
            reminders_to_notify = []
            
            for reminder in reminders:
                # Se o lembrete nunca foi notificado ou foi notificado há mais de 24 horas
                if (reminder.last_notification is None or 
                    (now - reminder.last_notification) > timedelta(hours=24)):
                    
                    # Se o vencimento é hoje ou amanhã, notificar
                    days_until_due = (reminder.due_date - now.date()).days
                    if days_until_due <= 1:
                        reminders_to_notify.append(reminder)
                        
                        # Atualizar data da última notificação
                        reminder.last_notification = now
            
            if reminders_to_notify:
                # Criar mensagem de notificação
                message = "🔔 <b>Lembrete de contas a pagar:</b>\n\n"
                
                for reminder in reminders_to_notify:
                    days = (reminder.due_date - now.date()).days
                    if days == 0:
                        due_text = "HOJE"
                    elif days == 1:
                        due_text = "AMANHÃ"
                    else:
                        due_text = f"em {days} dias"
                    
                    message += f"• {reminder.description}: {user.currency} {reminder.amount:.2f} - Vence {due_text}\n"
                
                # Enviar mensagem para o usuário
                try:
                    await bot.send_message(chat_id=user.telegram_id, text=message)
                    logging.info(f"Notificação enviada para o usuário {user.telegram_id}")
                except Exception as e:
                    logging.error(f"Erro ao enviar notificação: {e}")
        
        # Commit das alterações (atualização de last_notification)
        session.commit()

async def start_scheduler(bot):
    """Inicia o agendador de tarefas"""
    while True:
        try:
            await check_reminders(bot)
        except Exception as e:
            logging.error(f"Erro no agendador: {e}")
        
        # Verificar novamente em 1 hora
        await asyncio.sleep(3600)  # 3600 segundos = 1 hora
