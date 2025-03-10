# utils/helpers.py
from datetime import datetime, timedelta
import re

def format_currency(amount, currency):
    """Formata um número como string de moeda."""
    return f"{currency} {amount:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")

def validate_date(date_str):
    """Valida e analisa uma string de data no formato DD/MM/AAAA."""
    try:
        return datetime.strptime(date_str, "%d/%m/%Y").date()
    except ValueError:
        return None

def calculate_percentage(part, whole):
    """Calcula a porcentagem de uma parte em relação ao todo."""
    if whole == 0:
        return 0
    return (part / whole) * 100

def get_month_name(month_number, lang='pt'):
    """Retorna o nome do mês."""
    if lang == 'pt':
        months = {
            1: "Janeiro",
            2: "Fevereiro",
            3: "Março",
            4: "Abril",
            5: "Maio",
            6: "Junho",
            7: "Julho",
            8: "Agosto",
            9: "Setembro",
            10: "Outubro",
            11: "Novembro",
            12: "Dezembro"
        }
    else:  # English default
        months = {
            1: "January",
            2: "February",
            3: "March",
            4: "April",
            5: "May",
            6: "June",
            7: "July",
            8: "August",
            9: "September",
            10: "October",
            11: "November",
            12: "December"
        }
    return months.get(month_number, "")

def format_date(date):
    """Formata uma data para exibição."""
    return date.strftime("%d/%m/%Y")

def parse_date_from_text(text):
    """Extrai uma data de um texto."""
    # Padrões comuns de data
    patterns = [
        r'(\d{1,2})[/\-](\d{1,2})[/\-](\d{2,4})',  # DD/MM/YYYY ou DD-MM-YYYY
        r'(\d{1,2})\s+de\s+(\w+)(?:\s+de\s+(\d{2,4}))?'  # DD de Mês [de YYYY]
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text.lower())
        if match:
            if len(match.groups()) == 3:
                day, month, year = match.groups()
                
                # Converter mês textual para número
                if not month.isdigit():
                    month_names = {
                        'janeiro': 1, 'fevereiro': 2, 'março': 3, 'abril': 4,
                        'maio': 5, 'junho': 6, 'julho': 7, 'agosto': 8,
                        'setembro': 9, 'outubro': 10, 'novembro': 11, 'dezembro': 12
                    }
                    month = month_names.get(month.lower(), 1)
                
                # Converter para inteiros
                day = int(day)
                month = int(month)
                year = int(year) if year else datetime.now().year
                
                # Ajustar ano de 2 dígitos
                if year < 100:
                    year += 2000
                
                try:
                    return datetime(year, month, day).date()
                except ValueError:
                    continue
    
    # Palavras-chave para datas relativas
    today = datetime.now().date()
    if 'hoje' in text.lower():
        return today
    elif 'amanhã' in text.lower() or 'amanha' in text.lower():
        return today + timedelta(days=1)
    elif 'ontem' in text.lower():
        return today - timedelta(days=1)
    
    # Se não encontrou nenhuma data, retorna None
    return None

def extract_amount_from_text(text):
    """Extrai um valor monetário de um texto."""
    # Procurar por padrões como "R$ 100,50" ou "100.50"
    amount_match = re.search(r'(?:R\$\s*)?(\d+(?:[.,]\d+)?)', text)
    if amount_match:
        amount_str = amount_match.group(1).replace(',', '.')
        try:
            return float(amount_str)
        except ValueError:
            return None
    return None
