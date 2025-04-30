# 🧪 FieldToLab

**FieldToLab** é uma plataforma web desenvolvida em Flask para apoiar o gerenciamento de dados em laboratórios e expedições científicas. Ela permite:

- Upload de planilhas Excel com múltiplas abas
- Visualização e edição de dados via interface CRUD
- Geração automática de códigos de barras para amostras
- Gerenciamento de usuários com permissões diferenciadas (admin e regular)

---

## 🚀 Como executar localmente

1. Clone o repositório:
```bash
git clone https://github.com/seunome/FieldToLab.git
cd FieldToLab
```

2. Crie um ambiente virtual (recomendado):
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

4. Configure as variáveis de ambiente:
Copie o arquivo `.env.example` para `.env`:
```bash
cp .env.example .env
```

5. Execute a aplicação:
```bash
python app.py
```

---

## 📁 Estrutura de Pastas

- `app.py`: ponto de entrada da aplicação Flask
- `config/`: configuração da aplicação e variáveis de ambiente
- `route/`: módulos com as rotas da API e lógica de negócio
- `models/`: definição do banco de dados via SQLAlchemy
- `templates/`: front-end com HTML + Jinja2
- `uploads/`, `barcodes/`, `backup_uploads/`: pastas de arquivos gerados

---

## 👥 Funcionalidades

### Autenticação e Sessão
- Login e logout com verificação de sessão
- Sessões persistentes com `Flask-Session`
- Hash de senha com `werkzeug.security`

### Gerenciamento de Usuários
- Admin pode criar, listar e excluir usuários
- Usuários comuns acessam apenas os dados que enviaram
- Troca de senha via interface protegida

### Upload e Manipulação de Excel
- Upload de planilhas `.xlsx` com múltiplas abas
- Validação de conteúdo antes da inserção no banco
- Backup automático dos uploads

### CRUD de Registros
- Listagem, edição e exclusão de registros
- Filtros por tabela, arquivo, usuário e campos específicos
- Validação e persistência via SQLAlchemy

### Geração de Códigos de Barras
- Geração de códigos no formato `TYPE-STATE-MUNI-SEQ-DATE`
- Criação de imagem de código de barras (`python-barcode`)
- Download e histórico de solicitações

---

## 🔗 Documentação de Rotas Principais

### Autenticação
- `POST /api/login` → autentica o usuário
- `GET /logout` → encerra a sessão
- `POST /api/change-password` → altera a senha logado

### Usuários
- `GET /manage-users` → exibe painel de gerenciamento (admin)
- `GET /user-details/<id>` → exibe uploads do usuário

### Upload & Excel
- `GET /upload` → página de upload
- `POST /upload` → envia planilha e insere dados no banco

### Banco de Dados
- `GET /database-management` → painel CRUD
- `POST /api/data` → lista registros com filtros
- `PUT /api/data` → edita registro
- `DELETE /api/data` → exclui registro

### Código de Barras
- `GET /code-generator` → formulário de geração
- `POST /generate-barcode` → cria e salva o código

### Tabela Geral
- `GET /tabela-geral` → visualização consolidada dos dados

---

## 🛡 Segurança

- Sessão protegida com cookies assinados
- Senhas armazenadas com hash seguro (`werkzeug.security`)
- Validação de uploads, permissões e filtros
- Controle por tipo de usuário (admin e comum)

---

## 📜 Licença

Este projeto é distribuído sob a licença [MIT](LICENSE).

---

## ✍️ Autor

**Lucas F. T. Leonardo**  
Cientista de Dados e desenvolvedor de aplicações web.
