from typing import Annotated
from sqlalchemy import String, create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from config import POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB

sync_engine = None

def get_engine():
    global sync_engine
    if sync_engine is None:
        sync_engine = create_engine(
            url=f"postgresql+psycopg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}",
            #echo=True, #вывод логов (все запросы алхимии к БД)
            # pool_size=5, размер количества соединений
            # max_overflow=10, дополнительные подключения к БД
        )
    return sync_engine

session_factory = sessionmaker(get_engine())
str_256 = Annotated[str, 256]

class Base(DeclarativeBase):
    type_annotation_map = {
        str_256: String(256)
    }
