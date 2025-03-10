# database/models.py
from sqlalchemy import create_engine, Column, Integer, String, Float, Date, ForeignKey, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
import config

Base = declarative_base()
engine = create_engine(config.DATABASE_URL)
Session = sessionmaker(bind=engine)

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(String, unique=True)
    name = Column(String)
    currency = Column(String, default="R$")
    monthly_income = Column(Float, default=0.0)
    created_at = Column(Date, default=datetime.now().date())
    
    transactions = relationship("Transaction", back_populates="user")
    budgets = relationship("Budget", back_populates="user")
    categories = relationship("Category", back_populates="user")
    reminders = relationship("Reminder", back_populates="user")
    future_incomes = relationship("FutureIncome", back_populates="user")

class Category(Base):
    __tablename__ = 'categories'
    
    id = Column(Integer, primary_key=True)
    name = Column(String)
    user_id = Column(Integer, ForeignKey('users.id'))
    is_default = Column(Boolean, default=False)
    is_income = Column(Boolean, default=False)  # True para categorias de receita
    
    user = relationship("User", back_populates="categories")
    transactions = relationship("Transaction", back_populates="category")
    budgets = relationship("Budget", back_populates="category")

class Transaction(Base):
    __tablename__ = 'transactions'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    category_id = Column(Integer, ForeignKey('categories.id'))
    amount = Column(Float)
    description = Column(String)
    date = Column(Date, default=datetime.now().date())
    is_expense = Column(Boolean, default=True)
    is_future = Column(Boolean, default=False)  # True para transações futuras
    
    user = relationship("User", back_populates="transactions")
    category = relationship("Category", back_populates="transactions")

class Budget(Base):
    __tablename__ = 'budgets'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    category_id = Column(Integer, ForeignKey('categories.id'))
    amount = Column(Float)
    month = Column(Integer)
    year = Column(Integer)
    
    user = relationship("User", back_populates="budgets")
    category = relationship("Category", back_populates="budgets")

class Reminder(Base):
    __tablename__ = 'reminders'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    description = Column(String)
    amount = Column(Float)
    due_date = Column(Date)
    is_paid = Column(Boolean, default=False)
    is_recurring = Column(Boolean, default=False)
    recurrence_type = Column(String)  # 'monthly', 'weekly', etc.
    recurrence_day = Column(Integer)  # Dia do mês ou dia da semana
    last_notification = Column(DateTime, nullable=True)
    
    user = relationship("User", back_populates="reminders")

class FutureIncome(Base):
    __tablename__ = 'future_incomes'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    amount = Column(Float)
    description = Column(String)
    expected_date = Column(Date)
    is_received = Column(Boolean, default=False)
    category_id = Column(Integer, ForeignKey('categories.id'), nullable=True)
    
    user = relationship("User", back_populates="future_incomes")
    category = relationship("Category", foreign_keys=[category_id])

# Criar tabelas
Base.metadata.create_all(engine)
