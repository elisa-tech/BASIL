from datetime import datetime
from typing import Optional

from db.models.db_base import Base
from db.models.user import UserModel
from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship


class CommentModel(Base):
    __tablename__ = "comments"
    extend_existing = True
    id: Mapped[int] = mapped_column(Integer(), primary_key=True, autoincrement=True)
    parent_table: Mapped[str] = mapped_column(String(100))
    parent_id: Mapped[int] = mapped_column(Integer())
    comment: Mapped[str] = mapped_column(String())
    todo: Mapped[bool] = mapped_column(Boolean, default=False)
    done: Mapped[bool] = mapped_column(Boolean, default=False)
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    created_by: Mapped["UserModel"] = relationship("UserModel",
                                                   foreign_keys="CommentModel.created_by_id")
    done_by_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=True
    )
    done_by: Mapped[Optional["UserModel"]] = relationship(
        "UserModel", foreign_keys="CommentModel.done_by_id"
    )
    done_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    def __init__(self, parent_table, parent_id, created_by, comment, todo=False):
        self.parent_table = parent_table
        self.parent_id = parent_id
        self.created_by = created_by
        self.created_by_id = created_by.id
        self.comment = comment
        self.todo = todo
        self.done = False
        self.done_by = None
        self.done_by_id = None
        self.done_at = None
        self.created_at = datetime.now()
        self.updated_at = self.created_at

    def as_dict(self, full_data=False):
        tmp = {"id": self.id,
               "comment": self.comment,
               "todo": self.todo,
               "done": self.done,
               "done_by": self.done_by.username if self.done_by else None,
               "done_by_id": self.done_by.id if self.done_by else None,
               "done_at": self.done_at.strftime(Base.dt_short_format_str) if self.done_at else None,
               "created_by": self.created_by.username,
               "created_by_id": self.created_by.id,
               "created_at": self.created_at.strftime(Base.dt_short_format_str),
               "updated_at": self.updated_at.strftime(Base.dt_short_format_str)}
        return tmp

    def __repr__(self) -> str:
        return f"CommentModel(id={self.id!r}, " \
               f"created_by={self.created_by.username!r}, " \
               f"created_by_id={self.created_by.id!r}, " \
               f"comment={self.comment!r}), " \
               f"todo={self.todo!r}, " \
               f"done={self.done!r}, " \
               f"done_by={self.done_by.username!r} if self.done_by else None, " \
               f"done_by_id={self.done_by.id!r} if self.done_by else None, " \
               f"done_at={self.done_at.strftime(Base.dt_short_format_str)!r} if self.done_at else None, " \
               f"parent_table={self.parent_table!r}, " \
               f"parent_id={self.parent_id!r}"
