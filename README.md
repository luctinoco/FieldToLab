# 🧪 FieldToLab

Plataforma web para laboratórios e expedições, que permite:
- Upload de planilhas Excel
- Visualização e edição de dados via CRUD
- Geração de códigos de barras para amostras
- Gerenciamento de usuários com permissões

---

## 🚀 Como executar localmente

1. Clone o repositório:
```bash
git clone https://github.com/seunome/FieldToLab.git
cd FieldToLab
```

2. Crie um ambiente virtual (opcional, mas recomendado):
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

4. Configure as variáveis de ambiente:
Crie um arquivo `.env` baseado no `.env.example`.

5. Execute o servidor:
```bash
python app.py
```

---

## 📁 Estrutura
- `app.py`: ponto de entrada da aplicação
- `config/`: configurações Flask e banco
- `route/`: arquivos que manipulam as rotas
- `models/`: definição do banco com SQLAlchemy
- `templates/`: front-end HTML com Jinja2

---

## 👥 Usuários
- Admins: podem gerenciar todos os dados
- Usuários comuns: podem visualizar e editar somente seus envios

---

## 🛡 Segurança
- Sessão com cookies assinado
- Senhas com hash seguro (Werkzeug)
- Geração de código com controle de acesso

---

## 📜 Licença
MIT (ou defina no seu LICENSE)

---

## ✍️ Autor
Lucas F. T. Leonardo – Cientista de Dados e desenvolvedor de aplicações Flask
