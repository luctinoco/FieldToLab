import json
import traceback
from flask import Blueprint, jsonify, request
from sqlalchemy import text
from route.database import db_session  # Ajuste se seu db_session estiver em outro lugar



@tabela_geral_bp.route("/api/tabela-geral/all", methods=["GET"])
def get_all_tables():
    """
    Retorna, em um único JSON, todos os registros de todas as tabelas,
    permitindo filtrar pelos valores das colunas (chaves) presentes em row_data.

    Para cada registro, se a chave "nome_arquivo" não estiver presente em row_data,
    ela é adicionada com o valor de file_name (seguindo a lógica de excel.py).
    """
    try:
        tables = [
            "amostra",
            "dpp",
            "elisa",
            "expedição",
            "mamíferos_domésticos",
            "mamíferos_silvestres",
            "molecular",
            "parasitologico_direto",
            "parasitologico_indireto",
            "rifi",
            "trfl",
            "vetores"
        ]

        # Filtros vindos da URL (ex.: ?Ordem=Hemiptera)
        filters = request.args.to_dict()

        all_results = []

        for tbl in tables:
            # 1) Descobre quais colunas existem de fato
            check_columns_sql = text(f"SHOW COLUMNS FROM `{tbl}`")
            columns_info = db_session.execute(check_columns_sql).fetchall()
            existing_cols = {row[0] for row in columns_info}

            # 2) Monta a lista de colunas para SELECT
            select_cols = []

            # Se existir "id", use-o; senão, se existir "id_da_amostra", use-o como id.
            if "id" in existing_cols:
                select_cols.append("id")
            elif "id_da_amostra" in existing_cols:
                select_cols.append("id_da_amostra as id")
            # Adiciona as demais colunas esperadas
            for col in ["row_data", "created_at", "file_name", "username"]:
                if col in existing_cols:
                    select_cols.append(col)

            if not select_cols:
                continue

            # 3) Monta a query SELECT
            sql = f"SELECT {', '.join(select_cols)} FROM `{tbl}`"
            stmt = text(sql)
            rows = db_session.execute(stmt).mappings().all()

            # 4) Processa cada registro, decodificando row_data e garantindo a presença da coluna "nome_arquivo"
            for r in rows:
                row_id = r.get("id") or "N/A"
                row_data_text = r.get("row_data", None)

                try:
                    row_data_dict = json.loads(row_data_text) if row_data_text else {}
                except Exception:
                    row_data_dict = {"raw_data": row_data_text}

                # Se "nome_arquivo" não existir no row_data, adiciona com o valor de file_name
                if "nome_arquivo" not in row_data_dict:
                    row_data_dict["nome_arquivo"] = r.get("file_name", "N/A")

                data = {
                    "table_name": tbl,
                    "id": row_id,
                    "username": r.get("username", "Desconhecido"),
                    "file_name": r.get("file_name", "N/A"),
                    "created_at": r.get("created_at", "N/A"),
                    "row_data": row_data_dict
                }
                all_results.append(data)

        # Filtro simples: para cada chave no filtro, exige que row_data[key] seja exatamente igual
        def passa_no_filtro(registro):
            rd = registro["row_data"]
            for col, valor_procurado in filters.items():
                if rd.get(col) != valor_procurado:
                    return False
            return True

        filtered_results = [r for r in all_results if passa_no_filtro(r)]

        return jsonify(filtered_results), 200

    except Exception as e:
        return jsonify({"message": f"Erro ao carregar dados em tabela_geral: {e}"}), 500
