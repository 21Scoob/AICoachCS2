from sqlalchemy import ForeignKey, String, Integer, Numeric, DateTime, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
import datetime

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "user_account"

    id : Mapped[int] = mapped_column(primary_key=True)
    username : Mapped[str] = mapped_column(String(30))
    password : Mapped[str] = mapped_column(String(40))
    email : Mapped[str] = mapped_column(String(40))
    steamid_64 : Mapped[str] = mapped_column(String(40), nullable = True)
    leetify_id: Mapped[str] = mapped_column(String(40), nullable = True)

    stats : Mapped[list["PlayerMatchStats"]] = relationship(back_populates="user")

class Match(Base):
    __tablename__ = "matches"

    id : Mapped[str] = mapped_column(String(64), primary_key=True)
    map_name: Mapped[str] = mapped_column(String(12))
    date : Mapped[datetime.datetime] = mapped_column(DateTime)
    score : Mapped[str] = mapped_column(String(40))
    duration : Mapped[int | None] = mapped_column(Integer, nullable = True)

    player_stats : Mapped[list["PlayerMatchStats"]] = relationship(back_populates="match")

class PlayerMatchStats(Base):
    __tablename__ = "player_stats"
    __table_args__ = (
        UniqueConstraint('user_id', 'match_id', name = "uq_userandmatch"),
    )
    
    user_id : Mapped[int] = mapped_column(ForeignKey("user_account.id"))
    match_id : Mapped[str] = mapped_column(ForeignKey("matches.id"))

    user : Mapped["User"] = relationship(back_populates = "stats")
    match : Mapped["Match"] = relationship(back_populates = "player_stats")

    id : Mapped[int] = mapped_column(primary_key=True)
    kd_ratio : Mapped[float] = mapped_column(Numeric(5, 2))
    utility_use : Mapped[float] = mapped_column(Numeric(5, 2))
    kar_ratio : Mapped[float] = mapped_column(Numeric(5, 2))
    hs_percentage : Mapped[float] = mapped_column(Numeric(5, 2))


