from datetime import datetime
from db.models.db_base import Base
from sqlalchemy import BigInteger, DateTime, Integer, String
from sqlalchemy import event, insert, select
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from typing import Optional


class JustificationModel(Base):
    __tablename__ = 'justifications'
    __table_args__ = {"sqlite_autoincrement": True}
    extend_existing = True
    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"),
                                    primary_key=True)
    description: Mapped[Optional[str]] = mapped_column(String())
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    def __init__(self, description):
        self.description = description
        self.created_at = datetime.now()
        self.updated_at = self.created_at

    def __repr__(self) -> str:
        return f"JustificationModel(id={self.id!r}, " \
               f"description={self.description!r})"

    def current_version(self, db_session):
        last_item = db_session.query(JustificationHistoryModel).filter(
                     JustificationHistoryModel.id == self.id).order_by(
                     JustificationHistoryModel.version.desc()).limit(1).all()[0]
        return f'{last_item.version}'

    def as_dict(self, full_data=False, db_session=None):
        _dict = {"id": self.id,
                 "description": self.description,
                 }

        if db_session:
            _dict['version'] = self.current_version(db_session)

        if full_data:
            _dict["created_at"] = self.created_at.strftime(Base.dt_format_str)
            _dict["updated_at"] = self.updated_at.strftime(Base.dt_format_str)
        return _dict


@event.listens_for(JustificationModel, "after_update")
def receive_after_update(mapper, connection, target):
    print("---------> after update")
    last_query = select(JustificationHistoryModel.version,
                        JustificationHistoryModel.description).where(
        JustificationHistoryModel.id == target.id).order_by(
        JustificationHistoryModel.version.desc()).limit(1)
    version = -1
    description = None
    for row in connection.execute(last_query):
        version = row[0]
        description = row[1]

    if version > -1 and description != target.description:
        print(f"description: {description}")
        print(f"target.description: {target.description}")
        insert_query = insert(JustificationHistoryModel).values(
            id=target.id,
            description=target.description,
            version=version + 1
        )
        connection.execute(insert_query)


@event.listens_for(JustificationModel, "after_insert")
def receive_after_insert(mapper, connection, target):
    print("---------> after insert")
    insert_query = insert(JustificationHistoryModel).values(
        id=target.id,
        description=target.description,
        version=1
    )
    connection.execute(insert_query)


class JustificationHistoryModel(Base):
    __tablename__ = 'justifications_history'
    __table_args__ = {"sqlite_autoincrement": True}
    extend_existing = True
    row_id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"),
                                        primary_key=True)
    id: Mapped[int] = mapped_column(Integer())
    description: Mapped[Optional[str]] = mapped_column(String())
    version: Mapped[int] = mapped_column(Integer())
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    def __init__(self, id, description, version):
        self.id = id
        self.description = description
        self.version = version
        self.created_at = datetime.now()

    def __repr__(self) -> str:
        return f"JustificationHistoryModel(row_id={self.row_id!r}, " \
               f"id={self.id!r}, " \
               f"version={self.version!r}, " \
               f"description={self.description!r})"
