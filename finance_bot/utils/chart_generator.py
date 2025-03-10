# utils/chart_generator.py
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Para usar sem interface gráfica
import io
import numpy as np
from datetime import datetime

def generate_expense_pie_chart(category_expenses, currency="R$"):
    """Gera um gráfico de pizza com as despesas por categoria"""
    # Filtrar categorias com valores
    categories = []
    values = []
    
    for category, amount in category_expenses.items():
        if amount > 0:
            categories.append(category)
            values.append(amount)
    
    # Criar figura
    plt.figure(figsize=(10, 6))
    plt.pie(values, labels=categories, autopct='%1.1f%%', startangle=90, 
            shadow=True, explode=[0.05] * len(categories), 
            colors=plt.cm.tab20.colors[:len(categories)])
    
    # Adicionar título
    current_month = datetime.now().strftime('%B %Y')
    plt.title(f'Despesas por Categoria - {current_month}', fontsize=16)
    
    # Adicionar legenda
    plt.legend(categories, loc="best")
    
    # Ajustar layout
    plt.tight_layout()
    
    # Salvar em buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=100)
    buf.seek(0)
    plt.close()
    
    return buf

def generate_monthly_comparison_chart(monthly_data, currency="R$"):
    """Gera um gráfico de barras comparando despesas e receitas por mês"""
    months = list(monthly_data.keys())
    expenses = [data['total_expense'] for data in monthly_data.values()]
    incomes = [data['total_income'] for data in monthly_data.values()]
    
    x = np.arange(len(months))  # Posições das barras
    width = 0.35  # Largura das barras
    
    fig, ax = plt.subplots(figsize=(12, 6))
    rects1 = ax.bar(x - width/2, expenses, width, label='Despesas', color='#ff6b6b')
    rects2 = ax.bar(x + width/2, incomes, width, label='Receitas', color='#51cf66')
    
    # Adicionar rótulos e título
    ax.set_xlabel('Mês')
    ax.set_ylabel(f'Valor ({currency})')
    ax.set_title('Comparação de Despesas e Receitas por Mês')
    ax.set_xticks(x)
    ax.set_xticklabels(months)
    ax.legend()
    
    # Adicionar valores nas barras
    def autolabel(rects):
        for rect in rects:
            height = rect.get_height()
            ax.annotate(f'{currency} {height:.2f}',
                        xy=(rect.get_x() + rect.get_width() / 2, height),
                        xytext=(0, 3),  # 3 pontos de deslocamento vertical
                        textcoords="offset points",
                        ha='center', va='bottom', rotation=90, fontsize=8)
    
    autolabel(rects1)
    autolabel(rects2)
    
    fig.tight_layout()
    
    # Salvar em buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=100)
    buf.seek(0)
    plt.close()
    
    return buf

def generate_budget_progress_chart(budget_status, currency="R$"):
    """Gera um gráfico de barras horizontais mostrando o progresso do orçamento"""
    categories = list(budget_status.keys())
    spent = [status['spent'] for status in budget_status.values()]
    budgets = [status['budget'] for status in budget_status.values()]
    percentages = [status['percentage'] for status in budget_status.values()]
    
    # Ordenar por percentagem (do maior para o menor)
    sorted_indices = np.argsort(percentages)[::-1]
    categories = [categories[i] for i in sorted_indices]
    spent = [spent[i] for i in sorted_indices]
    budgets = [budgets[i] for i in sorted_indices]
    percentages = [percentages[i] for i in sorted_indices]
    
    # Criar figura
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Criar barras horizontais
    y_pos = np.arange(len(categories))
    ax.barh(y_pos, budgets, height=0.5, color='lightgray', label='Orçamento')
    
    # Colorir barras de gasto de acordo com a porcentagem
    colors = []
    for p in percentages:
        if p < 70:
            colors.append('#51cf66')  # Verde
        elif p < 90:
            colors.append('#fcc419')  # Amarelo
        else:
            colors.append('#ff6b6b')  # Vermelho
    
    ax.barh(y_pos, spent, height=0.5, color=colors, label='Gasto')
    
    # Adicionar rótulos
    ax.set_yticks(y_pos)
    ax.set_yticklabels(categories)
    ax.invert_yaxis()  # Inverter eixo y para ter o maior no topo
    ax.set_xlabel(f'Valor ({currency})')
    ax.set_title('Progresso do Orçamento por Categoria')
    
    # Adicionar percentagens nas barras
    for i, (s, b, p) in enumerate(zip(spent, budgets, percentages)):
        ax.text(s + 0.1, i, f'{p:.1f}%', va='center')
        ax.text(b - 0.5, i, f'{currency} {b:.2f}', va='center', ha='right', color='black')
    
    fig.tight_layout()
    
    # Salvar em buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=100)
    buf.seek(0)
    plt.close()
    
    return buf
