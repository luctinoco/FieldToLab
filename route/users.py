from flask import Blueprint, render_template, session as flask_session, redirect, url_for, jsonify
from route.database import db_session
from models.models import User, BarcodeRequest


# 🔹 Middleware para verificar se o usuário é admin
def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in flask_session or flask_session.get('user_type') != 'admin':
            return jsonify({"message": "Acesso negado. Apenas administradores podem acessar."}), 403
        return f(*args, **kwargs)
    return decorated_function

# 🔹 Rota para exibir usuários (somente admin)
@users_bp.route('/manage-users', methods=['GET'])
@admin_required
def manage_users():
    users = db_session.query(User).all()
    user_data = [
        {"id": u.id, "username": u.username, "email": u.email, "role": u.role} for u in users
    ]
    return render_template('manage_users.html', users=user_data)

# 🔹 Rota para exibir detalhes de um usuário
@users_bp.route('/user-details/<int:user_id>', methods=['GET'])
@admin_required
def user_details(user_id):
    user = db_session.query(User).filter_by(id=user_id).first()
    if not user:
        return redirect(url_for('users.manage_users'))

    barcode_requests = db_session.query(BarcodeRequest).filter_by(username=user.username).all()
    request_data = [
        {
            "id": r.id,
            "code_type": r.code_type,
            "state": r.state,
            "municipality": r.municipality,
            "date": r.date,
            "sequential_start": r.sequential_start,
            "sequential_end": r.sequential_end,
            "created_at": r.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            "barcode_text": r.barcode_texts,
            "barcode_link": r.barcode_links,
        } for r in barcode_requests
    ]
    return render_template('user_details.html', user={"username": user.username, "email": user.email, "role": user.role}, requests=request_data)

@users_bp.route('/delete-user/<int:user_id>', methods=['POST'])
@admin_required
def delete_user(user_id):
    user = db_session.query(User).filter_by(id=user_id).first()

    if not user:
        return jsonify({"error": "Usuário não encontrado"}), 404

    try:
        db_session.delete(user)
        db_session.commit()
        return jsonify({"message": "Usuário deletado com sucesso!"}), 200
    except Exception as e:
        db_session.rollback()
        return jsonify({"error": str(e)}), 500


