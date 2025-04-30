from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from config.config import Config  # 🔹 Certifique-se de que `config.py` está correto

# Inicialização do Banco de Dados
engine = create_engine(Config.DATABASE_URL)
Base = declarative_base()
Session = sessionmaker(bind=engine)
db_session = Session()
