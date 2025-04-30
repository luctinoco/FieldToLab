from flask import Blueprint, request, jsonify, session as flask_session
from datetime import datetime
from route.database import db_session
from models.models import BarcodeRequest
from route.code_generator import generate_sample_code, generate_barcode


# 🔹 Middleware para garantir que o usuário esteja autenticado
def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in flask_session:
            return jsonify({"message": "Sessão expirada ou inválida. Faça login novamente."}), 401
        return f(*args, **kwargs)
    return decorated_function

# 🔹 Rota para gerar código de barras
@barcodes_bp.route('/generate-barcode', methods=['POST'])
@login_required
def generate_barcode_route():
    try:
        data = request.get_json()
        username = flask_session['username']
        code_type = data['code_type']
        state = data['state']
        municipality = data['municipality']
        date_str = data['date']
        sequential_start = int(data['sequential_start'])
        sequential_end = int(data['sequential_end'])

        if sequential_start > sequential_end:
            return jsonify({"message": "O sequencial inicial deve ser menor ou igual ao sequencial final."}), 400

        barcode_paths = []
        for seq in range(sequential_start, sequential_end + 1):
            sample_code = generate_sample_code(code_type, state, municipality, datetime.strptime(date_str, '%Y-%m-%d'), seq)
            barcode_path = generate_barcode(sample_code)
            barcode_paths.append(barcode_path)

            new_request = BarcodeRequest(
                username=username,
                code_type=code_type,
                state=state,
                municipality=municipality,
                date=date_str,
                sequential_start=seq,
                sequential_end=seq,
                barcode_links=barcode_path,
                barcode_texts=sample_code
            )
            db_session.add(new_request)

        db_session.commit()
        return jsonify({"message": "Códigos gerados!", "barcode_links": barcode_paths}), 200
    except Exception as e:
        db_session.rollback()
        return jsonify({"message": "Erro ao gerar código", "error": str(e)}), 500
