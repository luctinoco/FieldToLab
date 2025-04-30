from flask import render_template, redirect, url_for, Flask, session
from flask import Blueprint, request, jsonify, session as flask_session
from werkzeug.security import check_password_hash, generate_password_hash
from route.database import db_session
from models.models import User



# 🔹 Rota para processar login
@auth_bp.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    # 🔹 Busca o usuário no banco de dados usando a tabela "users"
    user = db_session.query(User).filter_by(username=username).first()

    if user and check_password_hash(user.password, password):
        flask_session.permanent = True  # 🔹 Mantém a sessão ativa
        flask_session["username"] = user.username  # 🔹 Salva o nome do usuário na sessão
        flask_session["user_type"] = user.role  # 🔹 Salva o tipo de usuário na sessão


        return jsonify({
            "message": "Login realizado com sucesso!",
            "username": user.username,
            "user_type": user.role
        }), 200

    return jsonify({"message": "Credenciais inválidas"}), 401


@auth_bp.route('/api/get-user-type', methods=['GET'])
def get_user_type():

    # 🔹 Garante que sempre retorna "username" e "user_type"
    username = flask_session.get("username")
    user_type = flask_session.get("user_type")

    if not username:
        return jsonify({"message": "Sessão expirada ou inválida."}), 401

    response = {
        "username": username,
        "user_type": user_type
    }
    return jsonify(response), 200

# 🔹 Rota para fazer logout
@auth_bp.route('/logout', methods=['GET'])
def logout():
    flask_session.clear()  # 🔹 Garante que a sessão seja completamente apagada
    return redirect(url_for('auth.home'))

# 🔹 Rota para carregar a página de login
@auth_bp.route('/')
def home():
    return render_template('login.html')

@auth_bp.route('/api/change-password', methods=['POST'])
def change_password():
    """
    Allows users to change their password.
    """
    try:
        data = request.get_json()
        current_password = data.get('currentPassword')
        new_password = data.get('newPassword')

        if not current_password or not new_password:
            return jsonify({"message": "Todos os campos são obrigatórios."}), 400

        username = flask_session.get('username')
        if not username:
            return jsonify({"message": "Usuário não autenticado."}), 401

        user = db_session.query(User).filter_by(username=username).first()
        if not user:
            return jsonify({"message": "Usuário não encontrado."}), 404

        # Check if the current password is correct
        if not check_password_hash(user.password, current_password):
            return jsonify({"message": "Senha atual incorreta."}), 401

        # Update the password
        user.password = generate_password_hash(new_password)
        db_session.commit()

        return jsonify({"message": "Senha alterada com sucesso!"}), 200
    except Exception as e:
        db_session.rollback()
        return jsonify({"message": "Erro ao alterar a senha.", "error": str(e)}), 500
