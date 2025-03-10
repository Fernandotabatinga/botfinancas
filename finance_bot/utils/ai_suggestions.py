# utils/ai_suggestions.py
from datetime import datetime, timedelta
from database.db_operations import get_monthly_summary

def generate_spending_insights(user_id):
    """Gera insights sobre os gastos do usuário."""
    # Obter dados dos últimos 3 meses
    today = datetime.now()
    current_month = today.month
    current_year = today.year
    
    # Calcular meses anteriores
    months_data = []
    for i in range(3):
        month = current_month - i
        year = current_year
        if month <= 0:
            month += 12
            year -= 1
        
        summary = get_monthly_summary(user_id, month, year)
        if summary:
            months_data.append({
                'month': month,
                'year': year,
                'summary': summary
            })
    
    if not months_data:
        return ["Ainda não temos dados suficientes para gerar insights."]
    
    insights = []
    
    # Comparar gastos entre meses
    if len(months_data) >= 2:
        current = months_data[0]['summary']
        previous = months_data[1]['summary']
        
        # Comparar gastos totais
        if current['total_expense'] > previous['total_expense'] * 1.2:  # 20% de aumento
            insights.append(f"⚠️ Seus gastos aumentaram {((current['total_expense'] / previous['total_expense']) - 1) * 100:.1f}% em relação ao mês anterior.")
        elif current['total_expense'] < previous['total_expense'] * 0.8:  # 20% de redução
            insights.append(f"✅ Parabéns! Você reduziu seus gastos em {(1 - (current['total_expense'] / previous['total_expense'])) * 100:.1f}% em relação ao mês anterior.")
        
        # Comparar por categoria
        for category, amount in current['category_expenses'].items():
            if category in previous['category_expenses']:
                prev_amount = previous['category_expenses'][category]
                if amount > prev_amount * 1.3:  # 30% de aumento
                    insights.append(f"⚠️ Seus gastos com {category} aumentaram {((amount / prev_amount) - 1) * 100:.1f}% em relação ao mês anterior.")
    
    # Analisar orçamentos
    for category, status in months_data[0]['summary']['budget_status'].items():
        if status['percentage'] > 90:
            insights.append(f"⚠️ Você já utilizou {status['percentage']:.1f}% do seu orçamento para {category}.")
        elif status['percentage'] < 30 and status['budget'] > 0:
            insights.append(f"✅ Você está controlando bem seus gastos com {category}, utilizando apenas {status['percentage']:.1f}% do orçamento.")
    
    # Analisar equilíbrio entre receitas e despesas
    current_summary = months_data[0]['summary']
    if current_summary['total_expense'] > current_summary['total_income']:
        insights.append(f"⚠️ Suas despesas ({current_summary['total_expense']:.2f}) estão maiores que suas receitas ({current_summary['total_income']:.2f}) este mês.")
    elif current_summary['total_expense'] > current_summary['total_income'] * 0.9:
        insights.append(f"⚠️ Suas despesas estão consumindo {(current_summary['total_expense'] / current_summary['total_income']) * 100:.1f}% da sua renda. Tente reduzir para ter mais folga financeira.")
    else:
        insights.append(f"✅ Você está economizando {(1 - (current_summary['total_expense'] / current_summary['total_income'])) * 100:.1f}% da sua renda este mês. Continue assim!")
    
    # Verificar lembretes e receitas futuras
    if current_summary['reminder_total'] > 0:
        insights.append(f"📅 Você tem {len(current_summary['reminders'])} contas a pagar este mês, totalizando {current_summary['reminder_total']:.2f}.")
    
    if current_summary['future_income_total'] > 0:
        insights.append(f"💰 Você tem {len(current_summary['future_incomes'])} receitas futuras previstas para este mês, totalizando {current_summary['future_income_total']:.2f}.")
    
    # Se não houver insights, adicionar mensagem genérica
    if not insights:
        insights.append("Não temos insights específicos para mostrar neste momento. Continue registrando suas transações para obter análises mais detalhadas.")
    
    return insights

def generate_savings_recommendations(user_id):
    """Gera recomendações de economia para o usuário."""
    # Obter dados do mês atual
    today = datetime.now()
    summary = get_monthly_summary(user_id, today.month, today.year)
    
    if not summary:
        return ["Ainda não temos dados suficientes para gerar recomendações."]
    
    recommendations = []
    
    # Identificar categorias com maior gasto
    sorted_categories = sorted(summary['category_expenses'].items(), key=lambda x: x[1], reverse=True)
    
    if sorted_categories:
        top_category, top_amount = sorted_categories[0]
        if top_amount > summary['total_expense'] * 0.3:  # Mais de 30% dos gastos
            recommendations.append(f"🔍 Seus maiores gastos são com {top_category} ({top_amount:.2f}). Considere reduzir um pouco nesta categoria.")
    
    # Recomendar com base no orçamento
    for category, status in summary['budget_status'].items():
        if status['percentage'] > 100:
            overspent = status['spent'] - status['budget']
            recommendations.append(f"💸 Você estourou o orçamento de {category} em {overspent:.2f}. No próximo mês, tente se manter dentro do limite.")
    
    # Recomendar economia geral
    if summary['total_expense'] > summary['total_income'] * 0.7:
        savings_target = summary['total_income'] * 0.2  # Sugerir economizar 20% da renda
        recommendations.append(f"💰 Tente economizar pelo menos {savings_target:.2f} por mês para construir uma reserva de emergência.")
    
    # Recomendar diversificação de receitas
    if len(sorted_categories) <= 3:
        recommendations.append("💼 Considere diversificar suas fontes de renda para aumentar sua estabilidade financeira.")
    
    # Recomendar investimentos
    if summary['balance'] > summary['total_income'] * 0.3:
        recommendations.append("📈 Você tem um bom saldo positivo. Considere investir parte desse valor para fazer seu dinheiro trabalhar para você.")
    
    # Se não houver recomendações, adicionar mensagem genérica
    if not recommendations:
        recommendations.append("Continue mantendo o controle das suas finanças. Não temos recomendações específicas neste momento.")
    
    return recommendations
