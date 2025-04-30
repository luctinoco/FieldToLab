from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, func
from route.database import Base, engine  # 🔹 Importação corrigida


class User(Base):
    __tablename__ = "users"  # 🔹 Garante que o SQLAlchemy sabe que a tabela se chama "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    email = Column(String(100), unique=True)
    role = Column(String(20), nullable=False)  # 🔹 Deve ser "admin" ou "regular"


class BarcodeRequest(Base):
    __tablename__ = 'barcode_requests'
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(255), nullable=False)
    code_type = Column(String(10), nullable=False)
    state = Column(String(2), nullable=False)
    municipality = Column(String(255), nullable=False)
    date = Column(String(10), nullable=False)
    sequential_start = Column(Integer, nullable=False)
    sequential_end = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=func.now())
    barcode_links = Column(Text, nullable=True)
    barcode_texts = Column(Text, nullable=True)

class Upload(Base):
    __tablename__ = 'uploads'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(255), nullable=False)
    file_name = Column(String(255), nullable=False)
    upload_date = Column(DateTime, default=func.now())  # 🛠 Adiciona um valor padrão


# Criar tabelas no banco de dados
Base.metadata.create_all(engine)  # 🔹 Agora o `engine` é reconhecido corretamente


