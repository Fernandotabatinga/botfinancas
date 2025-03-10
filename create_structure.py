import os

# Definindo a estrutura do projeto
dirs = [
    "finance_bot",
    "finance_bot/database",
    "finance_bot/handlers",
    "finance_bot/utils"
]

files = [
    "finance_bot/main.py",
    "finance_bot/config.py",
    "finance_bot/requirements.txt",
    "finance_bot/database/__init__.py",
    "finance_bot/database/models.py",
    "finance_bot/database/db_operations.py",
    "finance_bot/handlers/__init__.py",
    "finance_bot/handlers/registration.py",
    "finance_bot/handlers/expenses.py",
    "finance_bot/handlers/income.py",
    "finance_bot/handlers/reports.py",
    "finance_bot/handlers/budgets.py",
    "finance_bot/handlers/export.py",
    "finance_bot/utils/__init__.py",
    "finance_bot/utils/nlp_processor.py",
    "finance_bot/utils/chart_generator.py",
    "finance_bot/utils/helpers.py"
]

# Criar diretórios
for dir_path in dirs:
    os.makedirs(dir_path, exist_ok=True)
    print(f"Diretório criado: {dir_path}")

# Criar arquivos vazios
for file_path in files:
    with open(file_path, 'w') as f:
        pass
    print(f"Arquivo criado: {file_path}")

print("Estrutura do projeto criada com sucesso!")

