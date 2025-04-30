import re
import json
import unicodedata
import traceback
from flask import Blueprint, jsonify, request, session as flask_session
from sqlalchemy import text
from route.database import db_session  # Ajuste conforme seu projeto


def sanitize_table_name(table_name: str) -> str:
    """
    Remove caracteres inválidos do nome da tabela, permitindo letras (inclusive acentuadas),
    números e underscore.
    """
    table_name = unicodedata.normalize("NFKC", table_name)
    return re.sub(r"[^\wÀ-ÿ]", "", table_name)

@database_bp.route("/api/<table_name>/get-database", methods=["GET"])
def get_database(table_name):
    safe_table_name = sanitize_table_name(table_name)
    try:
        filter_username = request.args.get("username", "").strip()
        filter_filename = request.args.get("file_name", "").strip()

        # Verifica quais colunas existem na tabela
        check_columns = text(f"SHOW COLUMNS FROM `{safe_table_name}`")
        result = db_session.execute(check_columns).fetchall()
        existing_columns = {row[0] for row in result}

        # Monta lista de colunas para SELECT
        select_columns = []
        if "id" in existing_columns:
            select_columns.append("id")
        elif "id_da_amostra" in existing_columns:
            select_columns.append("id_da_amostra as id")

        for col in ["row_data", "editavel", "created_at", "file_name", "username"]:
            if col in existing_columns:
                select_columns.append(col)

        if not select_columns:
            return jsonify({"message": f"Nenhuma coluna válida encontrada em '{safe_table_name}'"}), 400

        base_sql = f"SELECT {', '.join(select_columns)} FROM `{safe_table_name}`"
        conditions = []
        params = {}

        # Filtro por username
        if filter_username and ("username" in existing_columns):
            conditions.append("username LIKE :filter_user")
            params["filter_user"] = f"%{filter_username}%"

        # Filtro por file_name
        if filter_filename and ("file_name" in existing_columns):
            conditions.append("file_name LIKE :filter_file")
            params["filter_file"] = f"%{filter_filename}%"

        # Concatena as condições
        if conditions:
            base_sql += " WHERE " + " AND ".join(conditions)

        query = text(base_sql)
        rows = db_session.execute(query, params).mappings().all()

        data = []
        for row in rows:
            try:
                row_data_value = row.get("row_data", "{}")
                try:
                    row_data_dict = json.loads(row_data_value) if row_data_value else {}
                except Exception:
                    # Se não for JSON válido
                    row_data_dict = {"raw_data": row_data_value}

                row_dict = {
                    "id": row.get("id", "N/A"),
                    "username": row.get("username", "Desconhecido"),
                    "file_name": row.get("file_name", "N/A"),
                    "created_at": row.get("created_at", "N/A"),
                    "row_data": row_data_dict,
                    "editavel": row.get("editavel", None)
                }
                data.append(row_dict)
            except Exception as inner_e:
                continue

        return jsonify(data), 200

    except Exception as e:
        return jsonify({"message": f"Erro ao carregar dados de '{safe_table_name}': {e}"}), 500


@database_bp.route("/api/<table_name>/update-database", methods=["POST"])
def update_database(table_name):
    """
    Lida com row_data como array de objetos:
      1) Remove quaisquer objetos vazios ({}) ou objetos com chaves em branco.
      2) Remove do array antigo qualquer objeto cujo 'ID da Amostra'
         seja igual ao 'ID da Amostra' de cada objeto do novo array.
      3) Adiciona os itens novos no final.
      4) Remove novamente quaisquer objetos vazios resultantes.
    """
    safe_table_name = sanitize_table_name(table_name)
    try:
        data = request.get_json()
        record_id = data.get("id")
        new_items = data.get("new_row_data", [])

        # 1) Ler registro do banco
        select_sql = text(f"""
            SELECT username, row_data
            FROM `{safe_table_name}`
            WHERE id = :id
        """)
        result = db_session.execute(select_sql, {"id": record_id}).fetchone()
        if not result:
            return jsonify({"message": f"Registro {record_id} não encontrado em '{safe_table_name}'."}), 404

        record_owner = result[0]
        existing_row_data_str = result[1]

        # 2) Verificar permissão
        logged_in_user = flask_session.get("username")
        user_role = flask_session.get("user_type")
        if user_role != "admin" and logged_in_user != record_owner:
            return jsonify({"message": "Você não tem permissão para editar este registro."}), 403

        # 3) Carrega o array atual (se não for array, convertemos para [])
        try:
            existing_data = json.loads(existing_row_data_str) if existing_row_data_str else []
        except Exception:
            existing_data = []

        if not isinstance(existing_data, list):
            existing_data = [existing_data]

        # 4) new_items também deve ser array
        if not isinstance(new_items, list):
            new_items = [new_items]

        # -- Função para verificar se um objeto JSON está realmente vazio --
        def is_truly_empty(obj):
            """
            Considera vazio se:
            - for um dict sem chaves
            - ou se TODAS as chaves tiverem valor de string vazia.
            """
            if not isinstance(obj, dict):
                return False
            if not obj:  # dict sem nenhuma chave
                return True
            # Se cada valor for string vazia (ou só espaços), também consideramos vazio
            for val in obj.values():
                if not isinstance(val, str):
                    return False
                if val.strip() != "":
                    return False
            return True

        # 5) Remover objetos vazios do array existente
        existing_data = [item for item in existing_data if not is_truly_empty(item)]

        # 6) Remove objetos vazios dos itens novos também
        new_items = [item for item in new_items if not is_truly_empty(item)]

        # 7) Remover duplicados pela chave "ID da Amostra"
        key_field = "ID da Amostra"
        for new_obj in new_items:
            new_id_value = new_obj.get(key_field)
            if new_id_value:  # se existe algo nessa chave
                existing_data = [
                    obj for obj in existing_data
                    if obj.get(key_field) != new_id_value
                ]

        # 8) Adiciona os itens novos ao final
        existing_data.extend(new_items)

        # 9) Remover objetos vazios novamente (caso tenham surgido)
        existing_data = [item for item in existing_data if not is_truly_empty(item)]

        # 10) Salvar no banco
        final_json = json.dumps(existing_data, ensure_ascii=False)
        update_sql = text(f"""
            UPDATE `{safe_table_name}`
            SET row_data = :row_data
            WHERE id = :id
        """)
        db_session.execute(update_sql, {"row_data": final_json, "id": record_id})
        db_session.commit()

        return jsonify({
            "message": "Registro atualizado com sucesso!",
            "row_data": existing_data
        }), 200

    except Exception as e:
        db_session.rollback()
        return jsonify({"message": f"Erro ao atualizar registro em '{safe_table_name}': {e}"}), 500

@database_bp.route("/api/<table_name>/delete-record", methods=["POST"])
def delete_record(table_name):
    """
    Deleta completamente (DELETE) o registro da tabela, baseado no 'id'.
    """
    safe_table_name = sanitize_table_name(table_name)
    try:
        data = request.get_json()
        record_id = data.get("id")

        query_owner = text(f"SELECT username FROM `{safe_table_name}` WHERE id = :id")
        result = db_session.execute(query_owner, {"id": record_id}).fetchone()
        if not result:
            return jsonify({"message": f"Registro {record_id} não encontrado em '{safe_table_name}'."}), 404

        record_owner = result[0]
        logged_in_user = flask_session.get("username")
        user_role = flask_session.get("user_type")
        if user_role != "admin" and logged_in_user != record_owner:
            return jsonify({"message": "Você não tem permissão para excluir este registro."}), 403

        delete_sql = text(f"DELETE FROM `{safe_table_name}` WHERE id = :id")
        db_session.execute(delete_sql, {"id": record_id})
        db_session.commit()
        return jsonify({"message": f"Registro {record_id} deletado de '{safe_table_name}' com sucesso!"}), 200

    except Exception as e:
        db_session.rollback()
        return jsonify({"message": f"Erro ao deletar registro em '{safe_table_name}': {e}"}), 500


@database_bp.route("/api/list-tables", methods=["GET"])
def list_tables():
    try:
        query = text("SHOW TABLES")
        result = db_session.execute(query)
        tables = [row[0] for row in result.fetchall()]
        return jsonify({"tables": tables}), 200
    except Exception as e:
        return jsonify({"message": f"Erro ao listar tabelas: {e}"}), 500


@database_bp.route("/api/get-filter-options", methods=["GET"])
def get_filter_options():
    """
    Retorna as combinações distintas de (username, file_name) de várias tabelas,
    para fins de filtragem no front-end.
    """
    try:
        query = text("""
            SELECT DISTINCT username, file_name FROM (
                SELECT username, file_name FROM uploads
                UNION ALL
                SELECT username, file_name FROM amostra
                UNION ALL
                SELECT username, file_name FROM dpp
                UNION ALL
                SELECT username, file_name FROM elisa
                UNION ALL
                SELECT username, file_name FROM expedição
                UNION ALL
                SELECT username, file_name FROM mamíferos_domésticos
                UNION ALL
                SELECT username, file_name FROM mamíferos_silvestres
                UNION ALL
                SELECT username, file_name FROM molecular
                UNION ALL
                SELECT username, file_name FROM parasitologico_direto
                UNION ALL
                SELECT username, file_name FROM parasitologico_indireto
                UNION ALL
                SELECT username, file_name FROM rifi
                UNION ALL
                SELECT username, file_name FROM trfl
                UNION ALL
                SELECT username, file_name FROM vetores
            ) as all_tables
            WHERE username IS NOT NULL AND file_name IS NOT NULL
        """)
        result = db_session.execute(query).fetchall()
        usernames = list(set(row[0] for row in result if row[0]))
        files = list(set(row[1] for row in result if row[1]))
        return jsonify({"usernames": usernames, "files": files}), 200
    except Exception as e:
        return jsonify({"message": f"Erro ao buscar usernames e arquivos: {e}"}), 500
