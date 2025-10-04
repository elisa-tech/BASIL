from datetime import datetime
from db.models.db_base import Base
from db.models.user import UserModel
from sqlalchemy import DateTime, Integer, String
from sqlalchemy import event, insert, select
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from typing import Optional


class JustificationModel(Base):
    __tablename__ = 'justifications'
    _description = 'Justification'
    extend_existing = True
    id: Mapped[int] = mapped_column(Integer(), primary_key=True, autoincrement=True)
    description: Mapped[Optional[str]] = mapped_column(String())
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_by: Mapped["UserModel"] = relationship("UserModel",
                                                   foreign_keys="JustificationModel.created_by_id")
    edited_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    edited_by: Mapped["UserModel"] = relationship("UserModel",
                                                  foreign_keys="JustificationModel.edited_by_id")
    status: Mapped[str] = mapped_column(String(30))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    def __init__(self, description, created_by):
        self.description = description
        self.created_by = created_by
        self.created_by_id = created_by.id
        self.edited_by = created_by
        self.edited_by_id = created_by.id
        self.status = Base.STATUS_NEW
        self.created_at = datetime.now()
        self.updated_at = self.created_at

    def __repr__(self) -> str:
        return f"JustificationModel(id={self.id!r}, " \
               f"created_by={self.created_by.username!r}, " \
               f"status={self.status!r}), " \
               f"description={self.description!r})"

    def current_version(self, db_session):
        last_item = db_session.query(JustificationHistoryModel).filter(
                     JustificationHistoryModel.id == self.id).order_by(
                     JustificationHistoryModel.version.desc()).limit(1).all()[0]
        return f'{last_item.version}'

    def as_dict(self, full_data=False, db_session=None):
        _dict = {"id": self.id,
                 "description": self.description,
                 "status": self.status,
                 'created_by': self.created_by.username,
                 }

        if db_session:
            _dict['version'] = self.current_version(db_session)

        if full_data:
            _dict["created_at"] = self.created_at.strftime(Base.dt_format_str)
            _dict["updated_at"] = self.updated_at.strftime(Base.dt_format_str)
        return _dict


@event.listens_for(JustificationModel, "after_update")
def receive_after_update(mapper, connection, target):
    last_query = select(JustificationHistoryModel.version,
                        JustificationHistoryModel.description).where(
        JustificationHistoryModel.id == target.id).order_by(
        JustificationHistoryModel.version.desc()).limit(1)
    version = -1
    for row in connection.execute(last_query):
        version = row[0]

    if version > -1:
        insert_query = insert(JustificationHistoryModel).values(
            id=target.id,
            description=target.description,
            created_by_id=target.created_by_id,
            edited_by_id=target.edited_by_id,
            status=target.status,
            version=version + 1
        )
        connection.execute(insert_query)


@event.listens_for(JustificationModel, "after_insert")
def receive_after_insert(mapper, connection, target):
    insert_query = insert(JustificationHistoryModel).values(
        id=target.id,
        description=target.description,
        created_by_id=target.created_by_id,
        edited_by_id=target.edited_by_id,
        status=target.status,
        version=1
    )
    connection.execute(insert_query)


class JustificationHistoryModel(Base):
    __tablename__ = 'justifications_history'
    extend_existing = True
    row_id: Mapped[int] = mapped_column(Integer(), primary_key=True, autoincrement=True)
    id: Mapped[int] = mapped_column(Integer())
    description: Mapped[Optional[str]] = mapped_column(String())
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_by: Mapped["UserModel"] = relationship("UserModel",
                                                   foreign_keys="JustificationHistoryModel.created_by_id")
    edited_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    edited_by: Mapped["UserModel"] = relationship("UserModel",
                                                  foreign_keys="JustificationHistoryModel.edited_by_id")
    status: Mapped[str] = mapped_column(String(30))
    version: Mapped[int] = mapped_column(Integer())
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    def __init__(self, id, description, created_by_id, edited_by_id,
                 status, version):
        self.id = id
        self.description = description
        self.created_by_id = created_by_id
        self.edited_by_id = edited_by_id
        self.status = status
        self.version = version
        self.created_at = datetime.now()

    def __repr__(self) -> str:
        return f"JustificationHistoryModel(row_id={self.row_id!r}, " \
               f"id={self.id!r}, " \
               f"created_by={self.created_by.username!r}, " \
               f"description={self.description!r}), " \
               f"status={self.status!r}, " \
               f"version={self.version!r}"
