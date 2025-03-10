# config.py
import os
from dotenv import load_dotenv

load_dotenv()

# Configurações do Bot
BOT_TOKEN = "8119228125:AAErWUnh9-_8AH_C7Tt6kucD8sKChG2oPCQ"

# Configurações do Banco de Dados
DATABASE_URL = "sqlite:///finance_bot.db"  # SQLite para desenvolvimento

# Categorias padrão
DEFAULT_CATEGORIES = [
    "Alimentação", "Transporte", "Moradia", "Lazer", 
    "Saúde", "Educação", "Dívidas", "Outros"
]

# Categorias de receita padrão
DEFAULT_INCOME_CATEGORIES = [
    "Salário", "Freelance", "Investimentos", "Presente", "Outros"
]

# Configuração para NLP (opcional)
OPENAI_API_KEY = "sk-ee5b12f21e8449b7acd355ccaeed953c"  # DeepSeek key

# Configuração para lembretes
REMINDER_CHECK_INTERVAL = 3600  # Verificar lembretes a cada 1 hora (em segundos)
