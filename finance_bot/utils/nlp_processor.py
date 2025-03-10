# utils/nlp_processor.py
import re
from datetime import datetime, timedelta
import config

def extract_transaction_info(text):
    """
    Extrai informações de transação do texto do usuário.
    Exemplo: "Gastei 50 no mercado hoje" -> (50, "mercado", hoje, True)
    """
    # Versão simples com regex
    is_expense = True
    if re.search(r'receb|ganhe|ganhei|salário|salario|recebi', text.lower()):
        is_expense = False
    
    # Extrair valor
    amount_match = re.search(r'(\d+[.,]?\d*)', text)
    amount = float(amount_match.group(1).replace(',', '.')) if amount_match else 0
    
    # Extrair data
    date = datetime.now().date()
    if 'ontem' in text.lower():
        date = date - timedelta(days=1)
    elif 'anteontem' in text.lower():
        date = date - timedelta(days=2)
    
    # Tentar identificar categoria
    category = "Outros"
    description = text
    
    # Palavras-chave para categorias
    category_keywords = {
        "Alimentação": ["mercado", "supermercado", "comida", "restaurante", "lanche", "café", "almoço", "jantar"],
        "Transporte": ["uber", "99", "táxi", "ônibus", "metrô", "gasolina", "combustível", "estacionamento", "passagem"],
        "Moradia": ["aluguel", "condomínio", "luz", "água", "gás", "internet", "iptu"],
        "Lazer": ["cinema", "teatro", "show", "viagem", "passeio", "festa", "bar"],
        "Saúde": ["médico", "consulta", "remédio", "farmácia", "exame", "plano de saúde"],
        "Educação": ["curso", "faculdade", "escola", "livro", "material"],
        "Dívidas": ["empréstimo", "financiamento", "cartão", "parcela", "prestação"]
    }
    
    text_lower = text.lower()
    for cat, keywords in category_keywords.items():
        for keyword in keywords:
            if keyword in text_lower:
                category = cat
                break
        if category != "Outros":
            break
    
    return amount, category, description, date, is_expense

def detect_intent(text):
    """
    Detecta a intenção do usuário a partir do texto.
    Retorna: (intenção, parâmetros)
    """
    text_lower = text.lower()
    
    # Dicionário de palavras-chave para cada intenção
    intent_keywords = {
        "monthly_report": ["relatório", "resumo", "balanço", "mês", "mensal", "gastei este mês", "gastos do mês"],
        "category_report": ["quanto gastei com", "gastos em", "despesas com", "categoria"],
        "budget_set": ["definir orçamento", "estabelecer limite", "orçamento para", "limite de gasto"],
        "add_reminder": ["lembrar", "lembrete", "não esquecer", "avise", "conta para pagar", "vencimento"],
        "future_income": ["vou receber", "receita futura", "entrada de dinheiro", "pagamento", "receberei"],
        "add_expense": ["gastei", "comprei", "paguei", "despesa", "gasto"],
        "add_income": ["recebi", "ganhei", "salário", "receita", "entrada"]
    }
    
    # Verificar qual intenção corresponde melhor ao texto
    for intent, keywords in intent_keywords.items():
        for keyword in keywords:
            if keyword in text_lower:
                # Extrair parâmetros relevantes
                params = {}
                
                # Para relatórios de categoria, extrair a categoria
                if intent == "category_report" and "com" in text_lower:
                    category_match = re.search(r"com\s+(\w+)", text_lower)
                    if category_match:
                        params["category"] = category_match.group(1)
                
                # Para orçamentos, extrair categoria e valor
                if intent == "budget_set":
                    category_match = re.search(r"para\s+(\w+)", text_lower)
                    if category_match:
                        params["category"] = category_match.group(1)
                    
                    amount_match = re.search(r"(\d+[.,]?\d*)", text_lower)
                    if amount_match:
                        params["amount"] = float(amount_match.group(1).replace(',', '.'))
                
                # Para lembretes, extrair descrição e data
                if intent == "add_reminder":
                    # Extrair descrição (tudo após "lembrar" ou similar)
                    for keyword in ["lembrar", "lembrete", "avise"]:
                        if keyword in text_lower:
                            desc_match = re.search(f"{keyword}\s+(.*?)(?:\s+em|\s+dia|\s+para|\s+no dia|$)", text_lower)
                            if desc_match:
                                params["description"] = desc_match.group(1).strip()
                    
                    # Extrair data
                    date_match = re.search(r"(?:em|dia|para|no dia)\s+(\d{1,2})[/\-](\d{1,2})(?:[/\-](\d{2,4}))?", text_lower)
                    if date_match:
                        day = int(date_match.group(1))
                        month = int(date_match.group(2))
                        year = int(date_match.group(3)) if date_match.group(3) else datetime.now().year
                        if year < 100:
                            year += 2000
                        params["date"] = datetime(year, month, day).date()
                
                # Para receitas futuras, extrair valor e data
                if intent == "future_income":
                    amount_match = re.search(r"(\d+[.,]?\d*)", text_lower)
                    if amount_match:
                        params["amount"] = float(amount_match.group(1).replace(',', '.'))
                    
                    # Extrair data
                    date_match = re.search(r"(?:em|dia|no dia)\s+(\d{1,2})[/\-](\d{1,2})(?:[/\-](\d{2,4}))?", text_lower)
                    if date_match:
                        day = int(date_match.group(1))
                        month = int(date_match.group(2))
                        year = int(date_match.group(3)) if date_match.group(3) else datetime.now().year
                        if year < 100:
                            year += 2000
                        params["date"] = datetime(year, month, day).date()
                    
                    # Extrair descrição
                    desc_match = re.search(r"receber\s+(.*?)(?:\s+em|\s+dia|\s+no dia|$)", text_lower)
                    if desc_match:
                        params["description"] = desc_match.group(1).strip()
                
                return intent, params
    
    # Se nenhuma intenção for detectada
    return "unknown", {}
