import datetime

from sqlalchemy import BigInteger, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from database.connection import Base


class ServerSetting(Base):
    __tablename__ = "server_settings"
    server_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    server_name: Mapped[str]
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
