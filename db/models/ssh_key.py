from datetime import datetime
from db.models.db_base import Base
from db.models.user import UserModel
from sqlalchemy import DateTime, Integer, String
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from typing import Optional


class SshKeyModel(Base):
    __tablename__ = "ssh_keys"
    extend_existing = True
    id: Mapped[int] = mapped_column(Integer(), primary_key=True, autoincrement=True)
    title: Mapped[Optional[str]] = mapped_column(String())
    ssh_key: Mapped[str] = mapped_column(String())
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    created_by: Mapped["UserModel"] = relationship("UserModel",
                                                   foreign_keys="SshKeyModel.created_by_id")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    def __init__(self, title, ssh_key, created_by):
        self.title = title
        self.ssh_key = ssh_key
        self.created_by = created_by
        self.created_by_id = created_by.id
        self.created_at = datetime.now()
        self.updated_at = self.created_at

    def __repr__(self) -> str:
        tmp = "SshKeyModel("
        for field in self.__table__.columns.keys():
            tmp += f"{field}={getattr(self, field)}, "
        tmp += ")"
        return tmp

    def as_dict(self, full_data=False):
        _dict = {'id': self.id,
                 'title': self.title,
                 }

        if full_data:
            _dict["created_at"] = self.created_at.strftime(Base.dt_format_str)
        return _dict
