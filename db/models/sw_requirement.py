from datetime import datetime
from db.models.db_base import Base
from sqlalchemy import BigInteger, DateTime, Integer, String
from sqlalchemy import event, insert, select
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from typing import Optional


class SwRequirementModel(Base):
    __tablename__ = 'sw_requirements'
    __table_args__ = {"sqlite_autoincrement": True}
    extend_existing = True
    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"),
                                    primary_key=True)
    title: Mapped[str] = mapped_column(String())
    description: Mapped[Optional[str]] = mapped_column(String())
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    def __init__(self, title, description):
        self.title = title
        self.description = description
        self.created_at = datetime.now()
        self.updated_at = self.created_at

    def __repr__(self) -> str:
        return f"SwRequirementModel(id={self.id!r}, " \
               f"title={self.title!r}, " \
               f"description={self.description!r})"

    def current_version(self, db_session):
        last_item = db_session.query(SwRequirementHistoryModel).filter(
                     SwRequirementHistoryModel.id == self.id).order_by(
                     SwRequirementHistoryModel.version.desc()).limit(1).all()[0]
        return f'{last_item.version}'

    def as_dict(self, full_data=False, db_session=None):
        _dict = {"id": self.id,
                 "title": self.title,
                 "description": self.description,
                 }

        if db_session:
            _dict['version'] = self.current_version(db_session)

        if full_data:
            _dict["created_at"] = self.created_at.strftime(Base.dt_format_str)
            _dict["updated_at"] = self.updated_at.strftime(Base.dt_format_str)
        return _dict


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
            version=version + 1
        )
        connection.execute(insert_query)


@event.listens_for(SwRequirementModel, "after_insert")
def receive_after_insert(mapper, connection, target):
    insert_query = insert(SwRequirementHistoryModel).values(
        id=target.id,
        title=target.title,
        description=target.description,
        version=1
    )
    connection.execute(insert_query)


class SwRequirementHistoryModel(Base):
    __tablename__ = 'sw_requirements_history'
    __table_args__ = {"sqlite_autoincrement": True}
    extend_existing = True
    row_id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"),
                                        primary_key=True)
    id: Mapped[int] = mapped_column(Integer())
    title: Mapped[str] = mapped_column(String())
    description: Mapped[Optional[str]] = mapped_column(String())
    version: Mapped[int] = mapped_column(Integer())
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    def __init__(self, id, title, description, version):
        self.id = id
        self.title = title
        self.description = description
        self.version = version
        self.created_at = datetime.now()

    def __repr__(self) -> str:
        return f"SwRequirementHistoryModel(row_id={self.row_id!r}, " \
               f"id={self.id!r}, " \
               f"version={self.version!r}, " \
               f"title={self.title!r}, " \
               f"description={self.description!r})"
