import datetime
from typing import Annotated
from db.database import Base

from sqlalchemy import (
    text, Interval
)
from sqlalchemy.orm import Mapped, mapped_column

intpk = Annotated[int, mapped_column(primary_key=True)]
created_at = Annotated[datetime.datetime, mapped_column(server_default=text("TIMEZONE('utc', now())"))]

class Deals(Base):
    __tablename__ = "deals"

    id: Mapped[intpk]
    coin: Mapped[str]
    order_id_buy: Mapped[str]
    order_id_sell: Mapped[str]
    money_buy: Mapped[float]
    tax_buy: Mapped[float]
    money_sell: Mapped[float]
    tax_sell: Mapped[float]
    status: Mapped[str]
    time_open: Mapped[datetime.datetime] = mapped_column(server_default=text("now()"))
    time_close: Mapped[datetime.datetime] = mapped_column(nullable=True)
    time_in_deal: Mapped[datetime.timedelta] = mapped_column(Interval, nullable=True)
    earn: Mapped[float] = mapped_column(nullable=True)

class Coins(Base):
    __tablename__ = "coins"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    coin: Mapped[str] = mapped_column(unique=True)
    in_deal: Mapped[bool] = mapped_column(default=False)