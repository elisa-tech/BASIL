from datetime import datetime
from db.models.db_base import Base
from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column


class NoteModel(Base):
    __tablename__ = "notes"
    extend_existing = True
    id: Mapped[int] = mapped_column(Integer(), primary_key=True, autoincrement=True)
    parent_table: Mapped[str] = mapped_column(String(100))
    parent_id: Mapped[int] = mapped_column(Integer())
    username: Mapped[str] = mapped_column(String(100))
    note: Mapped[str] = mapped_column(String())
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)
    parent_object = None

    def __init__(self, parent_object, username, note):
        self.parent_object = parent_object
        self.parent_table = self.parent_object.__tablename__
        self.parent_id = self.parent_object.id
        self.username = username
        self.note = note
        self.created_at = datetime.now()
        self.updated_at = self.created_at

    def __repr__(self) -> str:
        return f"NoteModel(id={self.id!r}, " \
               f"username={self.username!r}, " \
               f"note={self.note!r}), " \
               f"parent_table={self.parent_table!r}, " \
               f"parent_id={self.parent_id!r}"
