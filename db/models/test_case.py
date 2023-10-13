from datetime import datetime
from typing import List
from typing import Optional
from sqlalchemy import ForeignKey
from sqlalchemy import *
from sqlalchemy import event
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from db_base import Base

class TestCaseModel(Base):
    __tablename__ = "test_cases"
    __table_args__ = {"sqlite_autoincrement": True}
    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"),
                                    primary_key=True)
    repository: Mapped[str] = mapped_column(String())
    relative_path: Mapped[str] = mapped_column(String())
    title: Mapped[str] = mapped_column(String())
    description: Mapped[str] = mapped_column(String())
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    def __init__(self, repository, relative_path, title, description):
        self.repository = repository
        self.relative_path = relative_path
        self.title = title
        self.description = description
        self.created_at = datetime.now()
        self.updated_at = self.created_at

    def __repr__(self) -> str:
        return f"TestCaseModel(id={self.id!r}, " \
               f"repository={self.repository!r}, " \
               f"relative_path={self.relative_path!r}," \
               f"title={self.title!r}, " \
               f"description={self.description!r})"

    def current_version(self, db_session):
        last_item = db_session.query(TestCaseHistoryModel).filter(
                     TestCaseHistoryModel.id == self.id).order_by(
                     TestCaseHistoryModel.version.desc()).limit(1).all()[0]
        return f'{last_item.version}'

    def as_dict(self, full_data=False, db_session=None):
        _dict = {"id": self.id,
                 "repository": self.repository,
                 "relative_path": self.relative_path,
                 "title": self.title,
                 "description": self.description,
                 }

        if db_session:
            _dict['version'] = self.current_version(db_session)

        if full_data:
            _dict["created_at"] = self.created_at.strftime(Base.dt_format_str)
            _dict["updated_at"] = self.updated_at.strftime(Base.dt_format_str)
        return _dict

@event.listens_for(TestCaseModel, "after_update")
def receive_after_update(mapper, connection, target):
    last_query = select(TestCaseHistoryModel.version).where( \
        TestCaseHistoryModel.id == target.id).order_by(
        TestCaseHistoryModel.version.desc()).limit(1)
    version = -1
    for row in connection.execute(last_query):
        version = row[0]

    if version > -1:
        insert_query = insert(TestCaseHistoryModel).values(
            id=target.id,
            repository=target.repository,
            relative_path=target.relative_path,
            title=target.title,
            description=target.description,
            version=version + 1
        )
        connection.execute(insert_query)

@event.listens_for(TestCaseModel, "after_insert")
def receive_after_insert(mapper, connection, target):
    insert_query = insert(TestCaseHistoryModel).values(
        id=target.id,
        repository=target.repository,
        relative_path=target.relative_path,
        title=target.title,
        description=target.description,
        version=1
    )
    connection.execute(insert_query)


class TestCaseHistoryModel(Base):
    __tablename__ = 'test_cases_history'
    __table_args__ = {"sqlite_autoincrement": True}
    row_id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"),
                                        primary_key=True)
    id: Mapped[int] = mapped_column(Integer())
    repository: Mapped[str] = mapped_column(String())
    relative_path: Mapped[str] = mapped_column(String())
    title: Mapped[str] = mapped_column(String())
    description: Mapped[str] = mapped_column(String())
    version: Mapped[int] = mapped_column(Integer())
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    def __init__(self, id, repository, relative_path, title, description, version):
        self.id = id
        self.repository = repository
        self.relative_path = relative_path
        self.title = title
        self.description = description
        self.version = version
        self.created_at = datetime.now()

    def __repr__(self) -> str:
        return f"TestCaseHistoryModel(row_id={self.row_id!r}, " \
               f"id={self.id!r}, " \
               f"version={self.version!r}, " \
               f"repository={self.repository!r}, " \
               f"relative_path={self.relative_path!r}, " \
               f"title={self.title!r}, " \
               f"description={self.description!r})"