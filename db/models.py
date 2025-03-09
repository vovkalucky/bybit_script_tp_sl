import datetime
import enum
from typing import Annotated, Optional
from db.database import Base

from sqlalchemy import (
    # TIMESTAMP,
    # CheckConstraint,
    Column,
    # Enum,
    # ForeignKey,
    # Index,
    Integer,
    MetaData,
    # PrimaryKeyConstraint,
    String,
    Table,
    text, Interval,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

#from database import Base, str_256

intpk = Annotated[int, mapped_column(primary_key=True)]
created_at = Annotated[datetime.datetime, mapped_column(server_default=text("TIMEZONE('utc', now())"))]
# updated_at = Annotated[datetime.datetime, mapped_column(
#     server_default=text("TIMEZONE('utc', now())"),
#     onupdate=datetime.datetime.now,
# )]


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
    #time_open: Mapped[created_at]
    time_open: Mapped[datetime.datetime] = mapped_column(server_default=text("TIMEZONE('Europe/Moscow', now())"))
    time_close: Mapped[datetime.datetime] = mapped_column(nullable=True)
    time_in_deal: Mapped[datetime.timedelta] = mapped_column(Interval, nullable=True)
    earn: Mapped[float] = mapped_column(nullable=True)

class Coins(Base):
    __tablename__ = "coins"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    coin: Mapped[str] = mapped_column(unique=True)
    in_deal: Mapped[bool] = mapped_column(default=False)

class ListOfOpenDeals(Base):
    __tablename__ = "list_of_open_deals"

    id: Mapped[intpk]
    coin: Mapped[str] = mapped_column(unique=True)
    order_id: Mapped[str] = mapped_column(unique=True)

#metadata_obj = MetaData()



# deals_table = Table(
#     "deals",
#     metadata_obj,
#     Column("id", Integer, primary_key=True),
#     Column("coin", String),
#     Column("order_id_buy", String),
#     Column("order_id_sell", String)
# )
#
# coins = Table(
#     "coins",
#     metadata_obj,
# Column("id", Integer, primary_key=True),
#     Column("coin", String, unique=True)
# )




    # resumes: Mapped[list["ResumesOrm"]] = relationship(
    #     back_populates="worker",
    # )
#
#     resumes_parttime: Mapped[list["ResumesOrm"]] = relationship(
#         back_populates="worker",
#         primaryjoin="and_(WorkersOrm.id == ResumesOrm.worker_id, ResumesOrm.workload == 'parttime')",
#         order_by="ResumesOrm.id.desc()",
#     )


# class Workload(enum.Enum):
#     parttime = "parttime"
#     fulltime = "fulltime"


# class ResumesOrm(Base):
#     __tablename__ = "resumes"
#
#     id: Mapped[intpk]
#     title: Mapped[str_256]
#     compensation: Mapped[Optional[int]]
#     workload: Mapped[Workload]
#     worker_id: Mapped[int] = mapped_column(ForeignKey("workers.id", ondelete="CASCADE"))
#     created_at: Mapped[created_at]
#     updated_at: Mapped[updated_at]
#
#     worker: Mapped["WorkersOrm"] = relationship(
#         back_populates="resumes",
#     )
#
#     vacancies_replied: Mapped[list["VacanciesOrm"]] = relationship(
#         back_populates="resumes_replied",
#         secondary="vacancies_replies",
#     )
#
#     repr_cols_num = 2
#     repr_cols = ("created_at",)
#
#     __table_args__ = (
#         Index("title_index", "title"),
#         CheckConstraint("compensation > 0", name="checl_compensation_positive"),
#     )
#
#
# class VacanciesOrm(Base):
#     __tablename__ = "vacancies"
#
#     id: Mapped[intpk]
#     title: Mapped[str_256]
#     compensation: Mapped[Optional[int]]
#
#     resumes_replied: Mapped[list["ResumesOrm"]] = relationship(
#         back_populates="vacancies_replied",
#         secondary="vacancies_replies",
#     )
#
#
# class VacanciesRepliesOrm(Base):
#     __tablename__ = "vacancies_replies"
#
#     resume_id: Mapped[int] = mapped_column(
#         ForeignKey("resumes.id", ondelete="CASCADE"),
#         primary_key=True,
#     )
#     vacancy_id: Mapped[int] = mapped_column(
#         ForeignKey("vacancies.id", ondelete="CASCADE"),
#         primary_key=True,
#     )
#
#     cover_letter: Mapped[Optional[str]]