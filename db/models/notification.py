from datetime import datetime
from db.models.api import ApiModel
from db.models.db_base import Base
from sqlalchemy import BigInteger, DateTime, Integer, String
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from typing import Optional


class NotificationModel(Base):
    __tablename__ = "notifications"
    __table_args__ = {"sqlite_autoincrement": True}
    extend_existing = True
    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"),
                                    primary_key=True)
    api_id: Mapped[Optional[int]] = mapped_column(ForeignKey("apis.id"))
    api: Mapped[Optional["ApiModel"]] = relationship("ApiModel", foreign_keys="NotificationModel.api_id")
    category: Mapped[str] = mapped_column(String(20))
    title: Mapped[str] = mapped_column(String())
    description: Mapped[str] = mapped_column(String())
    read_by: Mapped[Optional[str]] = mapped_column(String())
    url: Mapped[str] = mapped_column(String())
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    def __init__(self, api, category, title, description, read_by, url):
        if api:
            self.api = api
            self.api_id = api.id
        self.category = category
        self.title = title
        self.description = description
        self.read_by = read_by
        self.url = url
        self.created_at = datetime.now()
        self.updated_at = self.created_at

    def as_dict(self, full_data=False):
        tmp = {"category": self.category,
               "title": self.title,
               "description": self.description,
               "read_by": self.read_by.split(","),  # Return a list
               "url": self.url,
               "created_at": self.created_at.strftime(Base.dt_short_format_str)}

        if self.api:
            tmp['api'] = self.api.api

        return tmp

    def __repr__(self) -> str:
        return f"NotificationModel(id={self.id!r}, " \
               f"api={self.api!r}, " \
               f"category={self.category!r}, " \
               f"title={self.title!r}, " \
               f"description={self.description!r}, " \
               f"read_by={self.read_by!r}), " \
               f"url={self.url!r}, " \
               f"created_at={self.created_at.strftime(Base.dt_short_format_str)!r}"
