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

## 👥 Controle de Acesso

- **Administradores**: podem criar usuários, acessar todos os dados, e editar qualquer planilha
- **Usuários regulares**: acessam e editam apenas os registros que enviaram

---

## 🛡 Segurança

- Sessão protegida com cookies assinados
- Senhas armazenadas com hash seguro (`werkzeug.security`)
- Controle de upload por extensão e validação de conteúdo
- Geração de código de barras rastreável por data, localidade e tipo

---

## 📜 Licença

Este projeto é distribuído sob a licença [MIT](LICENSE).

---

## ✍️ Autor

**Lucas F. T. Leonardo**  
Cientista de Dados e desenvolvedor de aplicações web
