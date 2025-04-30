import os
import json
import pandas as pd
import logging
import warnings
import shutil
import gc
from flask import Blueprint, request, jsonify, session as flask_session
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from config.config import Config
from models.models import Upload  # Caso você tenha esse model

# Suprime o aviso do openpyxl sobre Data Validation
warnings.filterwarnings("ignore", message="Data Validation extension is not supported and will be removed",
                        category=UserWarning)

# Configuração do logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


engine = create_engine(Config.DATABASE_URL)
Session = sessionmaker(bind=engine)
db_session = Session()

UPLOAD_FOLDER = "uploads"
BACKUP_FOLDER = "backup_uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(BACKUP_FOLDER, exist_ok=True)


def is_file_in_use(file_path):
    """
    Verifica se o arquivo está em uso antes de tentar removê-lo.
    """
    try:
        with open(file_path, 'r+'):
            return False  # O arquivo pode ser editado (não está bloqueado)
    except IOError:
        return True  # O arquivo está em uso


def insert_row(table_name, username, file_name, row_dict, editavel, unique_cols=None):
    """
    Insere uma linha na tabela, salvando row_data como JSON, evitando duplicatas.
    Se unique_cols for fornecido, verifica se já existe uma linha com os mesmos valores
    para as colunas definidas em unique_cols.
    """
    if unique_cols is None:
        unique_cols = []  # Se não houver colunas únicas definidas, insere sempre

    # Converte row_dict para JSON
    row_data_json = json.dumps(row_dict, ensure_ascii=False)

    # Verifica se a linha já existe com base nas colunas únicas
    if unique_cols:
        # Constrói cláusula WHERE dinamicamente: "col1 = :col1 AND col2 = :col2 ..."
        where_conditions = []
        params = {}
        for col in unique_cols:
            where_conditions.append(f"{col} = :{col}")
            # Usa valor do row_dict; se não existir, usa string vazia
            params[col] = row_dict.get(col, "")
        where_clause = " AND ".join(where_conditions)
        check_sql = text(f"SELECT COUNT(*) as cnt FROM `{table_name}` WHERE {where_clause}")
        with engine.begin() as conn:
            result = conn.execute(check_sql, params).fetchone()
            if result and result["cnt"] > 0:
                logger.debug(f"[DEBUG] Linha duplicada detectada em {table_name} para {row_dict}")
                return  # Já existe, não insere novamente

    # Insere a nova linha
    insert_sql = text(f"""
        INSERT INTO `{table_name}` (username, file_name, row_data, editavel)
        VALUES (:username, :file_name, :row_data, :editavel)
    """)
    with engine.begin() as conn:
        conn.execute(
            insert_sql,
            {
                "username": username,
                "file_name": file_name,
                "row_data": row_data_json,
                "editavel": editavel
            }
        )

def process_excel(file_path, username):
    """
    Processa o arquivo Excel, fechando-o corretamente após a leitura.
    Para a aba "amostra", ignora a linha se:
      - O campo "Ocorrência" estiver vazio
      E
      - O campo "Código da Amostr" estiver vazio ou indicar que não há dados (por exemplo, conter "OT")
    """
    try:
        with pd.ExcelFile(file_path) as xls:
            sheet_names = xls.sheet_names  # Lê os nomes das abas
            logger.debug(f"[DEBUG] Abas encontradas no arquivo: {sheet_names}")
            user_type = flask_session.get("user_type", "regular")

            for sheet_name in sheet_names:
                if sheet_name == "Domínios (NÃO MEXER)":
                    logger.debug(f"[DEBUG] Ignorando a aba: {sheet_name}")
                    continue

                # Cria o nome da tabela a partir do nome da aba
                raw_table_name = sheet_name.lower().replace(" ", "_").replace("(", "").replace(")", "")
                table_name = raw_table_name  # Nome seguro para SQL

                # Deleta registros existentes para este arquivo na tabela
                with engine.begin() as conn:
                    delete_sql = text(f"DELETE FROM `{table_name}` WHERE file_name = :file_name")
                    conn.execute(delete_sql, {"file_name": os.path.basename(file_path)})

                try:
                    df = xls.parse(sheet_name, dtype=str).fillna("")
                except Exception as e:
                    logger.exception(f"Erro ao processar a aba {sheet_name}")
                    continue

                logger.debug(f"[DEBUG] Aba '{sheet_name}' -> Tabela '{table_name}', total de linhas: {len(df)}")

                for i, row_series in df.iterrows():
                    row_dict = row_series.to_dict()
                    logger.debug(f"[DEBUG] Processando linha {i} da aba '{sheet_name}': {row_dict}")

                    # Checagem especial para a aba "amostra"
                    if table_name == "amostra":
                        ocorrencia = row_dict.get("Ocorrência", "").strip()
                        codigo_amostra = row_dict.get("Código da Amostr", "").strip()
                        # Se não houver valor em "Ocorrência"
                        # E se "Código da Amostr" estiver vazio ou indicar "OT" (caso-insensitivo)
                        if not ocorrencia and (not codigo_amostra or codigo_amostra.upper().startswith("OT")):
                            logger.debug(f"[DEBUG] Linha {i} ignorada. Ocorrência: '{ocorrencia}', Código da Amostr: '{codigo_amostra}'")
                            continue

                    # Define as colunas únicas para evitar duplicatas (se aplicável)
                    unique_cols = []
                    if "amostra" in row_dict:
                        unique_cols.append("amostra")
                    if "data" in row_dict:
                        unique_cols.append("data")

                    try:
                        insert_row(
                            table_name=table_name,
                            username=username,
                            file_name=os.path.basename(file_path),
                            row_dict=row_dict,
                            editavel="admin" if user_type == "admin" else "regular",
                            unique_cols=unique_cols
                        )
                    except Exception as e:
                        logger.exception(f"Erro ao inserir linha {i} da aba {sheet_name}")
    except Exception as e:
        logger.exception("Erro ao ler o arquivo Excel")
        raise

    gc.collect()

    # Registra o upload no banco (sem inserir coluna 'upload_date')
    try:
        timestamp_id = datetime.now().strftime("%Y%m%d%H%M%S")
        insert_upload_sql = text("""
            INSERT INTO uploads (id, username, file_name)
            VALUES (:id, :username, :file_name)
        """)
        db_session.execute(insert_upload_sql, {
            "id": int(timestamp_id),
            "username": username,
            "file_name": os.path.basename(file_path)
        })
        db_session.commit()
    except Exception as e:
        logger.exception("Erro ao registrar o upload")
        raise

@excel_bp.route('/upload-excel', methods=['POST'])
def upload_excel():
    """
    Rota de upload do Excel:
      - Recebe o arquivo via form-data na chave 'file'
      - Se 'replace' for "true", substitui o arquivo existente no disco.
      - Antes de processar, verifica se o nome do arquivo já existe no banco (tabela uploads);
        se existir, deleta todos os registros associados a esse arquivo.
      - Processa as abas do Excel e insere os dados nas tabelas correspondentes, evitando duplicatas.
    """
    if 'file' not in request.files:
        return jsonify({"message": "Nenhum arquivo enviado."}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"message": "Nome do arquivo inválido."}), 400

    file_name = os.path.basename(file.filename)
    file_path = os.path.join(UPLOAD_FOLDER, file_name)

    # Verifica se o arquivo já existe no disco
    if os.path.exists(file_path):
        replace_flag = request.form.get("replace", "").lower()
        if replace_flag == "true":
            if is_file_in_use(file_path):
                return jsonify({"message": "O arquivo está em uso. Feche-o antes de substituir."}), 409
            try:
                backup_path = os.path.join(BACKUP_FOLDER, file_name)
                shutil.move(file_path, backup_path)
                logger.info(f"Arquivo antigo movido para backup: {backup_path}")
            except Exception as move_error:
                logger.exception("Erro ao mover o arquivo para backup antes de substituir")
                return jsonify({"message": f"Erro ao substituir arquivo: {move_error}"}), 500
        else:
            return jsonify({"message": f"O arquivo '{file_name}' já existe. Deseja substituir?"}), 409

    try:
        # Salva o arquivo no diretório
        file.save(file_path)
        username = flask_session.get("username")
        if not username:
            return jsonify({"message": "Usuário não autenticado."}), 401

        # Verifica na tabela 'uploads' se já existe o arquivo
        from models.models import Upload  # Certifique-se de que o model Upload está importado
        existing_uploads = db_session.query(Upload).filter(Upload.file_name == file_name).all()
        if existing_uploads:
            for up in existing_uploads:
                db_session.delete(up)
            db_session.commit()
            logger.info(f"Registros de upload com o arquivo '{file_name}' foram removidos do banco.")

        # Processa o Excel (a função process_excel já deleta registros em cada tabela para esse arquivo)
        process_excel(file_path, username)

        # Registra o novo upload na tabela 'uploads'
        timestamp_id = datetime.now().strftime("%Y%m%d%H%M%S")
        new_upload = Upload(
            id=int(timestamp_id),
            username=username,
            file_name=file_name
        )
        db_session.add(new_upload)
        db_session.commit()

        return jsonify({"message": "Arquivo processado com sucesso!"}), 200

    except Exception as e:
        logger.exception("Erro ao processar o arquivo")
        return jsonify({"message": f"Erro ao processar arquivo: {e}"}), 500

