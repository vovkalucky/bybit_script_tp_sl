import datetime
from typing import Annotated, Optional
from db.database import Base
from settings import TABLE_DEALS, TABLE_COINS

from sqlalchemy import (
    text, Interval
)
from sqlalchemy.orm import Mapped, mapped_column

intpk = Annotated[int, mapped_column(primary_key=True)]
created_at = Annotated[datetime.datetime, mapped_column(server_default=text("TIMEZONE('utc', now())"))]

class Deals(Base):
    __tablename__ = TABLE_DEALS

    id: Mapped[intpk]
    coin: Mapped[str]
    order_id_open: Mapped[str] = mapped_column(unique=True)
    side_open: Mapped[str]
    qty_open: Mapped[str]
    money_open: Mapped[float]
    tax_open: Mapped[float]
    order_id_close: Mapped[str] = mapped_column(unique=True)
    side_close: Mapped[Optional[str]] = mapped_column(nullable=True)
    qty_close: Mapped[Optional[str]] = mapped_column(nullable=True)
    money_close: Mapped[float]
    tax_close: Mapped[float]
    status: Mapped[str]
    time_open: Mapped[datetime.datetime] = mapped_column(server_default=text("now()"))
    time_close: Mapped[datetime.datetime] = mapped_column(nullable=True)
    time_in_deal: Mapped[datetime.timedelta] = mapped_column(Interval, nullable=True)
    earn: Mapped[float] = mapped_column(nullable=True)

class Coins(Base):
    __tablename__ = TABLE_COINS

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    coin: Mapped[str] = mapped_column(unique=True)
    in_deal: Mapped[int] = mapped_column(default=0)
    last_deal_time: Mapped[datetime.datetime] = mapped_column(nullable=True)