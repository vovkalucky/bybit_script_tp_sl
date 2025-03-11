from config import POSTGRES_HOST, POSTGRES_PASSWORD, POSTGRES_USER, POSTGRES_DB, POSTGRES_PORT

def DATABASE_URL_psycopg() -> str:
    # DSN
    # postgresql+psycopg://postgres:postgres@localhost:5432/sa
    return f"postgresql+psycopg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"


#settings = Settings()
#print(DATABASE_URL_psycopg)