from datetime import datetime
from db.models.db_base import Base
from db.models.user import UserModel
from sqlalchemy import BigInteger, DateTime, Integer, String
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship


class CommentModel(Base):
    __tablename__ = "comments"
    __table_args__ = {"sqlite_autoincrement": True}
    extend_existing = True
    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"),
                                    primary_key=True)
    parent_table: Mapped[str] = mapped_column(String(100))
    parent_id: Mapped[int] = mapped_column(Integer())
    comment: Mapped[str] = mapped_column(String())
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_by: Mapped["UserModel"] = relationship("UserModel",
                                                   foreign_keys="CommentModel.created_by_id")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    def __init__(self, parent_table, parent_id, created_by, comment):
        self.parent_table = parent_table
        self.parent_id = parent_id
        self.created_by = created_by
        self.created_by_id = created_by.id
        self.comment = comment
        self.created_at = datetime.now()
        self.updated_at = self.created_at

    def as_dict(self, full_data=False):
        tmp = {"id": self.id,
               "comment": self.comment,
               "created_by": self.created_by.username,
               "created_at": self.created_at.strftime(Base.dt_short_format_str)}
        return tmp

    def __repr__(self) -> str:
        return f"CommentModel(id={self.id!r}, " \
               f"created_by={self.created_by.eamil!r}, " \
               f"comment={self.comment!r}), " \
               f"parent_table={self.parent_table!r}, " \
               f"parent_id={self.parent_id!r}"
