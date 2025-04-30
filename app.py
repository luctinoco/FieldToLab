# app.py

from flask import Flask, render_template, redirect, url_for, send_from_directory, session as flask_session, jsonify
from flask_cors import CORS
from flask_session import Session
from flask_limiter import Limiter, util
from config.config import Config

# Blueprints que você tem
from route.auth import auth_bp          # se existir
from route.users import users_bp        # se existir
from route.barcodes import barcodes_bp  # se existir
from route.create_user import create_user_bp  # se existir
from route.database_management import database_bp
from route.excel import excel_bp
from route.tabela_geral import tabela_geral_bp

app = Flask(__name__, template_folder="templates")
app.config.from_object(Config)  # 🔹 Carrega configurações do `config.py`

# 🔹 Teste para verificar se a sessão está sendo aplicada corretamente
Session(app)  # 🔹 Inicializa a sessão

# Registrar os Blueprints


# =======================
# Rotas Principais
# =======================

@app.route('/')
def home():
    return render_template('login.html')  # Ajuste se usar outro nome
@app.route('/tabela-geral')
def tabela_geral_page():
    # Caso precise checar login ou algo assim, faça aqui
    return render_template('tabela_geral.html')
@app.route('/dashboard')
def dashboard():
    if 'username' not in flask_session:
        return redirect(url_for('home'))
    return render_template('dashboard.html')
@app.route('/upload')
def upload_page():
    return render_template('upload_excel.html')
@app.route('/change-password')
def change_password():
    if 'username' not in flask_session:
        return redirect(url_for('home'))
    return render_template('change_password.html')
@app.route('/code-generator')
def code_generator():
    if 'username' not in flask_session:
        return redirect(url_for('home'))
    return render_template('code_generator.html')
@app.route('/database-management')
def database_management():
    # Esta rota carrega o HTML com o script que chama "/database/api/<table_name>/..."
    return render_template('database_management.html')
@app.route('/create_user')
def create_user():
    return render_template('create_user.html')

UPLOAD_FOLDER = "uploads"
@app.route('/download/<file_name>')
def download_file(file_name):
    return send_from_directory(UPLOAD_FOLDER, file_name, as_attachment=True)
@app.route('/open/<file_name>')
def open_file(file_name):
    return send_from_directory(UPLOAD_FOLDER, file_name)
@app.route('/manage-users')
def manage_users():
    if 'username' not in flask_session or flask_session.get('user_type') != 'admin':
        return redirect(url_for('dashboard'))
    return render_template('manage_users.html')

if __name__ == '__main__':
    app.run(debug=False)
