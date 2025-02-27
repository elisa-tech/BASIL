import base64
from datetime import datetime
from db.models.db_base import Base
from sqlalchemy import BigInteger, DateTime, Integer, String
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from typing import Optional
from uuid import uuid4


class UserModel(Base):
    __tablename__ = "users"
    __table_args__ = {"sqlite_autoincrement": True}
    extend_existing = True
    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"),
                                    primary_key=True)
    username: Mapped[Optional[str]] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255))
    pwd: Mapped[str] = mapped_column(String)
    reset_pwd: Mapped[Optional[str]] = mapped_column(String(100))
    reset_token: Mapped[Optional[str]] = mapped_column(String(100))
    enabled: Mapped[int] = mapped_column(Integer)
    role: Mapped[str] = mapped_column(String(100))
    token: Mapped[str] = mapped_column(String(255))
    api_notifications: Mapped[Optional[str]] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    def __init__(self, username, email, pwd, role):
        self.username = username
        self.email = email
        self.pwd = base64.b64encode(pwd.encode('utf-8')).decode('utf-8')
        self.reset_pwd = ''
        self.reset_token = ''
        self.role = role
        self.enabled = 1
        self.token = str(uuid4())
        self.created_at = datetime.now()
        self.updated_at = self.created_at

    def __repr__(self) -> str:
        return f"User(id={self.id!r}, " \
               f"username={self.username!r}, " \
               f"email={self.email!r}, " \
               f"enabled={self.enabled!r}, " \
               f"role={self.role!r}"

    def as_dict(self, full_data=False, db_session=None):
        _dict = {"id": self.id,
                 "username": self.username,
                 "email": self.email,
                 "enabled": self.enabled,
                 "role": self.role,
                 "api_notifications": self.api_notifications}

        if full_data:
            _dict["created_at"] = self.created_at.strftime(Base.dt_format_str)
            _dict["updated_at"] = self.updated_at.strftime(Base.dt_format_str)
        return _dict
