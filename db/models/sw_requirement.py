from datetime import datetime
from db.models.db_base import Base
from db.models.user import UserModel
from sqlalchemy import DateTime, Integer, String
from sqlalchemy import delete, event, insert, select
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from typing import Optional


class SwRequirementModel(Base):
    __tablename__ = 'sw_requirements'
    _description = 'Software Requirement'
    extend_existing = True
    id: Mapped[int] = mapped_column(Integer(), primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String())
    description: Mapped[Optional[str]] = mapped_column(String())
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    created_by: Mapped["UserModel"] = relationship("UserModel",
                                                   foreign_keys="SwRequirementModel.created_by_id")
    edited_by_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    edited_by: Mapped["UserModel"] = relationship("UserModel",
                                                  foreign_keys="SwRequirementModel.edited_by_id")
    status: Mapped[str] = mapped_column(String(30))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    def __init__(self, title, description, created_by):
        self.title = title
        self.description = description
        self.created_by = created_by
        self.created_by_id = created_by.id
        self.edited_by = created_by
        self.edited_by_id = created_by.id
        self.status = Base.STATUS_NEW
        self.created_at = datetime.now()
        self.updated_at = self.created_at

    def __repr__(self) -> str:
        return f"SwRequirementModel(id={self.id!r}, " \
               f"title={self.title!r}, " \
               f"description={self.description!r}), " \
               f"status={self.status!r}), " \
               f"created_by={self.created_by.username!r}, " \
               f"edited_by={self.edited_by.username!r}"

    def current_version(self, db_session):
        last_item = db_session.query(SwRequirementHistoryModel).filter(
                     SwRequirementHistoryModel.id == self.id).order_by(
                     SwRequirementHistoryModel.version.desc()).limit(1).all()[0]
        return f'{last_item.version}'

    def as_dict(self, full_data=False, db_session=None):
        _dict = {"id": self.id,
                 "title": self.title,
                 "description": self.description,
                 "status": self.status,
                 "created_by": self.created_by.username,
                 }

        if db_session:
            _dict['version'] = self.current_version(db_session)

        if full_data:
            _dict["created_at"] = self.created_at.strftime(Base.dt_format_str)
            _dict["updated_at"] = self.updated_at.strftime(Base.dt_format_str)
        return _dict

    def fork(self, created_by, db_session=None):
        new_sw_requirement = SwRequirementModel(
            title=self.title,
            description=self.description,
            created_by=created_by
        )
        db_session.add(new_sw_requirement)
        db_session.commit()
        return new_sw_requirement


@event.listens_for(SwRequirementModel, "after_update")
def receive_after_update(mapper, connection, target):
    last_query = select(SwRequirementHistoryModel.version).where(
        SwRequirementHistoryModel.id == target.id).order_by(
        SwRequirementHistoryModel.version.desc()).limit(1)
    version = -1
    for row in connection.execute(last_query):
        version = row[0]

    if version > -1:
        insert_query = insert(SwRequirementHistoryModel).values(
            id=target.id,
            title=target.title,
            description=target.description,
            status=target.status,
            created_by_id=target.created_by_id,
            edited_by_id=target.edited_by_id,
            version=version + 1
        )
        connection.execute(insert_query)


@event.listens_for(SwRequirementModel, "after_insert")
def receive_after_insert(mapper, connection, target):
    insert_query = insert(SwRequirementHistoryModel).values(
        id=target.id,
        title=target.title,
        description=target.description,
        status=target.status,
        created_by_id=target.created_by_id,
        edited_by_id=target.edited_by_id,
        version=1
    )
    connection.execute(insert_query)


@event.listens_for(SwRequirementModel, "before_delete")
def receive_before_delete(mapper, connection, target):
    # Purge history rows for this mapping id
    del_stmt = delete(SwRequirementHistoryModel).where(SwRequirementHistoryModel.id == target.id)
    connection.execute(del_stmt)


class SwRequirementHistoryModel(Base):
    __tablename__ = 'sw_requirements_history'
    extend_existing = True
    row_id: Mapped[int] = mapped_column(Integer(), primary_key=True, autoincrement=True)
    id: Mapped[int] = mapped_column(Integer())
    title: Mapped[str] = mapped_column(String())
    description: Mapped[Optional[str]] = mapped_column(String())
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    created_by: Mapped["UserModel"] = relationship("UserModel",
                                                   foreign_keys="SwRequirementHistoryModel.created_by_id")
    edited_by_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    edited_by: Mapped["UserModel"] = relationship("UserModel",
                                                  foreign_keys="SwRequirementHistoryModel.edited_by_id")
    status: Mapped[str] = mapped_column(String(30))
    version: Mapped[int] = mapped_column(Integer())
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    def __init__(self, id, title, description, created_by_id, edited_by_id,
                 status, version):
        self.id = id
        self.title = title
        self.description = description
        self.status = status
        self.version = version
        self.created_by_id = created_by_id
        self.edited_by_id = edited_by_id
        self.created_at = datetime.now()

    def __repr__(self) -> str:
        return f"SwRequirementHistoryModel(row_id={self.row_id!r}, " \
               f"id={self.id!r}, " \
               f"version={self.version!r}, " \
               f"title={self.title!r}, " \
               f"status={self.status!r}, " \
               f"created_by={self.created_by.username!r}, " \
               f"description={self.description!r})"
