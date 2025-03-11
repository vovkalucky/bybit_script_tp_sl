import asyncio
from typing import Annotated
from sqlalchemy import String, create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from config import POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB

sync_engine = create_engine(
    url=f"postgresql+psycopg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}",
    echo=True, #вывод логов (все запросы алхимии к БД)
    # pool_size=5, размер количества соединений
    # max_overflow=10, дополнительные подключения к БД
)

### Проверка соединения ###
# with sync_engine.connect() as conn:
#     res = conn.execute(text("SELECT VERSION()"))
#     print(res)
#     conn.commit()

session_factory = sessionmaker(sync_engine)
#print(session_factory)

str_256 = Annotated[str, 256]

class Base(DeclarativeBase):
    type_annotation_map = {
        str_256: String(256)
    }
