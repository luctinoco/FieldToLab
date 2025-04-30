import os
from datetime import datetime
import barcode
from barcode.writer import ImageWriter
import unicodedata
import logging

# Configuração do Logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Diretório para salvar os códigos de barras
BARCODE_DIRECTORY = os.path.join(os.getcwd(), 'barcodes')
os.makedirs(BARCODE_DIRECTORY, exist_ok=True)

def normalize_text(text):
    """
    Remove acentos e normaliza um texto para evitar caracteres inválidos.
    """
    return ''.join(
        c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn'
    ).strip()

def generate_sample_code(code_type, state_abbreviation, municipality, date, sequential):
    """
    Gera um código de amostra no formato esperado usando a sigla do estado.
    Formato: TYPE-STATE-MUNI-SEQ-DATE
    """
    # Valida a sigla do estado
    if not state_abbreviation or len(state_abbreviation) != 2 or not state_abbreviation.isalpha():
        raise ValueError(f"Sigla do estado inválida: {state_abbreviation}")

    state_abbreviation = state_abbreviation.upper()
    municipality_abbreviation = normalize_text(municipality)[:4].upper()
    try:
        date_compact = date.strftime('%d%m%y')  # Valida e formata a data
    except Exception as e:
        raise ValueError(f"Erro ao formatar a data: {e}")

    # Formata o código
    return f"{code_type}-{state_abbreviation}-{municipality_abbreviation}-{sequential:04}-{date_compact}"

def generate_barcode(code):
    """
    Gera uma imagem de código de barras no formato Code 128.
    """
    try:
        # Certifica-se de que o diretório de saída existe
        if not os.path.exists(BARCODE_DIRECTORY):
            os.makedirs(BARCODE_DIRECTORY)

        # Cria o código de barras
        barcode_format = barcode.get('code128', code.replace("-", ""), writer=ImageWriter())

        # Remove a extensão .png do nome do arquivo
        filename = os.path.join(BARCODE_DIRECTORY, f"{code.replace('-', '_')}")
        barcode_path = barcode_format.save(filename)

        # Retorna o caminho completo da imagem gerada
        logging.info(f"Código de barras gerado: {barcode_path}")
        return barcode_path
    except Exception as e:
        logging.error(f"Erro ao gerar código de barras '{code}': {e}")
        return None

def generate_multiple_barcodes(code_type, state_abbreviation, municipality, date, sequential_start, sequential_end):
    """
    Gera múltiplos códigos de barras com base em um intervalo sequencial.
    """
    barcode_paths = []
    for sequential in range(sequential_start, sequential_end + 1):
        try:
            # Gera o código de amostra
            sample_code = generate_sample_code(code_type, state_abbreviation, municipality, date, sequential)

            # Gera o código de barras e salva no diretório
            barcode_path = generate_barcode(sample_code)
            if barcode_path:
                barcode_paths.append(barcode_path)
            else:
                logging.warning(f"Erro ao gerar código para o sequencial: {sequential}")
        except ValueError as e:
            logging.error(f"Erro ao gerar código: {e}")
    return barcode_paths

# Exemplo de uso
if __name__ == "__main__":
    code_type = "PE"
    state_abbreviation = "SP"  # Sigla do estado
    municipality = "Campinas"
    date_input = "2024-12-06"

    try:
        # Conversão da data
        date = datetime.strptime(date_input, "%Y-%m-%d")
    except ValueError as e:
        logging.error(f"Erro na data fornecida '{date_input}': {e}")
        exit(1)

    sequential_start = 1
    sequential_end = 5

    barcode_paths = generate_multiple_barcodes(code_type, state_abbreviation, municipality, date, sequential_start, sequential_end)

    if barcode_paths:
        logging.info("Códigos de barras gerados com sucesso:")
        for path in barcode_paths:
            logging.info(path)
    else:
        logging.warning("Nenhum código foi gerado.")
