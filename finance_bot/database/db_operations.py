# database/db_operations.py
from sqlalchemy.orm import Session
from .models import User, Category, Transaction, Budget, Reminder, FutureIncome, Session as DBSession
from datetime import datetime, timedelta
import config

def get_user(telegram_id):
    with DBSession() as session:
        return session.query(User).filter(User.telegram_id == str(telegram_id)).first()

def create_user(telegram_id, name, currency, monthly_income):
    with DBSession() as session:
        user = User(
            telegram_id=str(telegram_id),
            name=name,
            currency=currency,
            monthly_income=monthly_income
        )
        session.add(user)
        session.commit()
        
        # Criar categorias padrão para o usuário
        for category_name in config.DEFAULT_CATEGORIES:
            category = Category(
                name=category_name,
                user_id=user.id,
                is_default=True,
                is_income=False
            )
            session.add(category)
        
        # Criar categorias de receita padrão
        for category_name in config.DEFAULT_INCOME_CATEGORIES:
            category = Category(
                name=category_name,
                user_id=user.id,
                is_default=True,
                is_income=True
            )
            session.add(category)
        
        session.commit()
        return user

def get_user_categories(user_id, income=False):
    with DBSession() as session:
        user = session.query(User).filter(User.telegram_id == str(user_id)).first()
        
        if not user:
            return []
        
        categories = session.query(Category).filter(
            Category.user_id == user.id,
            Category.is_income == income
        ).all()
        
        return [category.name for category in categories]

def add_transaction(user_id, amount, description, category_name, date=None, is_expense=True, is_future=False):
    with DBSession() as session:
        user = session.query(User).filter(User.telegram_id == str(user_id)).first()
        
        if not user:
            return None
        
        # Encontrar ou criar categoria
        category = session.query(Category).filter(
            Category.user_id == user.id,
            Category.name == category_name,
            Category.is_income == (not is_expense)
        ).first()
        
        if not category:
            category = Category(
                name=category_name,
                user_id=user.id,
                is_income=(not is_expense)
            )
            session.add(category)
            session.commit()
        
        # Criar transação
        transaction = Transaction(
            user_id=user.id,
            category_id=category.id,
            amount=abs(amount),
            description=description,
            date=date or datetime.now().date(),
            is_expense=is_expense,
            is_future=is_future
        )
        
        session.add(transaction)
        session.commit()
        return transaction

def set_budget(user_id, category_name, amount, month=None, year=None):
    with DBSession() as session:
        user = session.query(User).filter(User.telegram_id == str(user_id)).first()
        
        if not user:
            return None
        
        # Encontrar categoria
        category = session.query(Category).filter(
            Category.user_id == user.id,
            Category.name == category_name
        ).first()
        
        if not category:
            return None
        
        # Definir mês e ano atuais se não fornecidos
        today = datetime.now()
        month = month or today.month
        year = year or today.year
        
        # Verificar se já existe um orçamento para esta categoria/mês/ano
        budget = session.query(Budget).filter(
            Budget.user_id == user.id,
            Budget.category_id == category.id,
            Budget.month == month,
            Budget.year == year
        ).first()
        
        if budget:
            budget.amount = amount
        else:
            budget = Budget(
                user_id=user.id,
                category_id=category.id,
                amount=amount,
                month=month,
                year=year
            )
            session.add(budget)
        
        session.commit()
        return budget

def get_monthly_summary(user_id, month=None, year=None):
    with DBSession() as session:
        user = session.query(User).filter(User.telegram_id == str(user_id)).first()
        
        if not user:
            return None
        
        # Definir mês e ano atuais se não fornecidos
        today = datetime.now()
        month = month or today.month
        year = year or today.year
        
        # Obter todas as transações do mês
        start_date = datetime(year, month, 1).date()
        if month == 12:
            end_date = datetime(year + 1, 1, 1).date()
        else:
            end_date = datetime(year, month + 1, 1).date()
        
        transactions = session.query(Transaction).filter(
            Transaction.user_id == user.id,
            Transaction.date >= start_date,
            Transaction.date < end_date,
            Transaction.is_future == False
        ).all()
        
        # Calcular totais
        total_income = sum(t.amount for t in transactions if not t.is_expense)
        total_expense = sum(t.amount for t in transactions if t.is_expense)
        
        # Agrupar por categoria
        category_expenses = {}
        for t in transactions:
            if t.is_expense:
                category = session.query(Category).get(t.category_id)
                if category.name not in category_expenses:
                    category_expenses[category.name] = 0
                category_expenses[category.name] += t.amount
        
        # Verificar orçamentos
        budgets = session.query(Budget).filter(
            Budget.user_id == user.id,
            Budget.month == month,
            Budget.year == year
        ).all()
        
        budget_status = {}
        for budget in budgets:
            category = session.query(Category).get(budget.category_id)
            spent = category_expenses.get(category.name, 0)
            budget_status[category.name] = {
                'budget': budget.amount,
                'spent': spent,
                'remaining': budget.amount - spent,
                'percentage': (spent / budget.amount * 100) if budget.amount > 0 else 0
            }
        
        # Obter receitas futuras
        future_incomes = session.query(FutureIncome).filter(
            FutureIncome.user_id == user.id,
            FutureIncome.expected_date >= start_date,
            FutureIncome.expected_date < end_date,
            FutureIncome.is_received == False
        ).all()
        
        future_income_total = sum(fi.amount for fi in future_incomes)
        future_income_list = [
            {
                'description': fi.description,
                'amount': fi.amount,
                'date': fi.expected_date
            }
            for fi in future_incomes
        ]
        
        # Obter lembretes pendentes
        reminders = session.query(Reminder).filter(
            Reminder.user_id == user.id,
            Reminder.due_date >= start_date,
            Reminder.due_date < end_date,
            Reminder.is_paid == False
        ).all()
        
        reminder_total = sum(r.amount for r in reminders)
        reminder_list = [
            {
                'description': r.description,
                'amount': r.amount,
                'due_date': r.due_date
            }
            for r in reminders
        ]
        
        return {
            'total_income': total_income,
            'total_expense': total_expense,
            'balance': total_income - total_expense,
            'category_expenses': category_expenses,
            'budget_status': budget_status,
            'future_income_total': future_income_total,
            'future_incomes': future_income_list,
            'reminder_total': reminder_total,
            'reminders': reminder_list
        }

def get_category_expenses(user_id, category_name, month=None, year=None):
    with DBSession() as session:
        user = session.query(User).filter(User.telegram_id == str(user_id)).first()
        
        if not user:
            return None
        
        # Definir mês e ano atuais se não fornecidos
        today = datetime.now()
        month = month or today.month
        year = year or today.year
        
        # Encontrar categoria
        category = session.query(Category).filter(
            Category.user_id == user.id,
            Category.name.ilike(f"%{category_name}%")  # Busca parcial para melhor UX
        ).first()
        
        if not category:
            return None
        
        # Obter todas as transações da categoria no mês
        start_date = datetime(year, month, 1).date()
        if month == 12:
            end_date = datetime(year + 1, 1, 1).date()
        else:
            end_date = datetime(year, month + 1, 1).date()
        
        transactions = session.query(Transaction).filter(
            Transaction.user_id == user.id,
            Transaction.category_id == category.id,
            Transaction.date >= start_date,
            Transaction.date < end_date,
            Transaction.is_expense == True,
            Transaction.is_future == False
        ).all()
        
        total = sum(t.amount for t in transactions)
        
        # Verificar orçamento
        budget = session.query(Budget).filter(
            Budget.user_id == user.id,
            Budget.category_id == category.id,
            Budget.month == month,
            Budget.year == year
        ).first()
        
        budget_amount = budget.amount if budget else 0
        
        return {
            'category': category.name,
            'total': total,
            'transactions': transactions,
            'budget': budget_amount,
            'remaining': budget_amount - total if budget_amount > 0 else 0,
            'percentage': (total / budget_amount * 100) if budget_amount > 0 else 0
        }

def add_reminder(user_id, description, amount, due_date, is_recurring=False, recurrence_type=None, recurrence_day=None):
    with DBSession() as session:
        user = session.query(User).filter(User.telegram_id == str(user_id)).first()
        
        if not user:
            return None
        
        reminder = Reminder(
            user_id=user.id,
            description=description,
            amount=amount,
            due_date=due_date,
            is_recurring=is_recurring,
            recurrence_type=recurrence_type,
            recurrence_day=recurrence_day
        )
        
        session.add(reminder)
        session.commit()
        return reminder

def get_pending_reminders(user_id=None, days_ahead=7):
    with DBSession() as session:
        query = session.query(Reminder).filter(
            Reminder.is_paid == False,
            Reminder.due_date <= (datetime.now().date() + timedelta(days=days_ahead))
        )
        
        if user_id:
            user = session.query(User).filter(User.telegram_id == str(user_id)).first()
            if not user:
                return []
            query = query.filter(Reminder.user_id == user.id)
        
        reminders = query.all()
        return reminders

def mark_reminder_as_paid(reminder_id, user_id):
    with DBSession() as session:
        user = session.query(User).filter(User.telegram_id == str(user_id)).first()
        
        if not user:
            return None
        
        reminder = session.query(Reminder).filter(
            Reminder.id == reminder_id,
            Reminder.user_id == user.id
        ).first()
        
        if not reminder:
            return None
        
        reminder.is_paid = True
        session.commit()
        return reminder

def add_future_income(user_id, amount, description, expected_date):
    with DBSession() as session:
        user = session.query(User).filter(User.telegram_id == str(user_id)).first()
        
        if not user:
            return None
        
        future_income = FutureIncome(
            user_id=user.id,
            amount=amount,
            description=description,
            expected_date=expected_date,
            is_received=False
        )
        
        session.add(future_income)
        session.commit()
        return future_income

def get_user_transactions(user_id):
    with DBSession() as session:
        user = session.query(User).filter(User.telegram_id == str(user_id)).first()
        
        if not user:
            return []
        
        transactions = session.query(Transaction).filter(
            Transaction.user_id == user.id
        ).all()
        
        return transactions

def import_bank_transactions(user_id, transactions):
    with DBSession() as session:
        user = session.query(User).filter(User.telegram_id == str(user_id)).first()
        
        if not user:
            return None
        
        imported_transactions = []
        for transaction in transactions:
            category = session.query(Category).filter(
                Category.user_id == user.id,
                Category.name.ilike(f"%{transaction['category']}%")
            ).first()
            
            if not category:
                category = Category(
                    name=transaction['category'],
                    user_id=user.id,
                    is_income=transaction['is_income']
                )
                session.add(category)
                session.commit()
            
            new_transaction = Transaction(
                user_id=user.id,
                category_id=category.id,
                amount=transaction['amount'],
                description=transaction['description'],
                date=transaction['date'],
                is_expense=not transaction['is_income']
            )
            session.add(new_transaction)
            imported_transactions.append(new_transaction)
        
        session.commit()
        return imported_transactions

def analyze_spending_patterns(user_id):
    with DBSession() as session:
        user = session.query(User).filter(User.telegram_id == str(user_id)).first()
        
        if not user:
            return None
        
        # Fetch transactions
        transactions = session.query(Transaction).filter(
            Transaction.user_id == user.id,
            Transaction.is_expense == True
        ).all()
        
        # Analyze spending by category
        category_totals = {}
        for transaction in transactions:
            category = session.query(Category).get(transaction.category_id)
            if category.name not in category_totals:
                category_totals[category.name] = 0
            category_totals[category.name] += transaction.amount
        
        # Generate suggestions
        suggestions = []
        for category, total in category_totals.items():
            if total > (user.monthly_income * 0.3):  # Example threshold: 30% of income
                suggestions.append(f"Você gastou muito com {category}. Considere reduzir seus gastos nessa categoria.")
        
        return suggestions
