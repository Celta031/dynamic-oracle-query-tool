import os
from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env para o ambiente
load_dotenv()

class Config:
    DB_USER = os.environ.get('DB_USER')
    DB_PASSWORD = os.environ.get('DB_PASSWORD')
    DB_HOST = os.environ.get('DB_HOST')
    DB_PORT = os.environ.get('DB_PORT')
    DB_SERVICE = os.environ.get('DB_SERVICE')
    DB_ROLE_PASSWORD = os.environ.get('DB_ROLE_PASSWORD')
    
    if not all([DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_SERVICE]):
        raise ValueError("ERRO: Defina todas as variáveis de banco de dados no arquivo .env")

    DB_DSN = f"{DB_HOST}:{DB_PORT}/{DB_SERVICE}"