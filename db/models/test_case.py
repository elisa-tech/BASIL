from datetime import datetime
from db.models.db_base import Base
from db.models.user import UserModel
from sqlalchemy import BigInteger, DateTime, Integer, String
from sqlalchemy import event, insert, select
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship


class TestCaseModel(Base):
    __tablename__ = "test_cases"
    __table_args__ = {"sqlite_autoincrement": True}
    _description = 'Test Case'
    extend_existing = True
    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"),
                                    primary_key=True)
    repository: Mapped[str] = mapped_column(String())
    relative_path: Mapped[str] = mapped_column(String())
    title: Mapped[str] = mapped_column(String())
    description: Mapped[str] = mapped_column(String())
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_by: Mapped["UserModel"] = relationship("UserModel",
                                                   foreign_keys="TestCaseModel.created_by_id")
    edited_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    edited_by: Mapped["UserModel"] = relationship("UserModel",
                                                  foreign_keys="TestCaseModel.edited_by_id")
    status: Mapped[str] = mapped_column(String(30))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    def __init__(self, repository, relative_path, title, description, created_by):
        self.repository = repository
        self.relative_path = relative_path
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
        return f"TestCaseModel(id={self.id!r}, " \
               f"repository={self.repository!r}, " \
               f"relative_path={self.relative_path!r}," \
               f"title={self.title!r}, " \
               f"description={self.description!r}), " \
               f"status={self.status!r}), " \
               f"created_by={self.created_by.email!r}"

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
                 "status": self.status,
                 'created_by': self.created_by.email,
                 }

        if db_session:
            _dict['version'] = self.current_version(db_session)

        if full_data:
            _dict["created_at"] = self.created_at.strftime(Base.dt_format_str)
            _dict["updated_at"] = self.updated_at.strftime(Base.dt_format_str)
        return _dict


@event.listens_for(TestCaseModel, "after_update")
def receive_after_update(mapper, connection, target):
    last_query = select(TestCaseHistoryModel.version).where(
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
            created_by_id=target.created_by_id,
            edited_by_id=target.edited_by_id,
            status=target.status,
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
        created_by_id=target.created_by_id,
        edited_by_id=target.edited_by_id,
        status=target.status,
        version=1
    )
    connection.execute(insert_query)


class TestCaseHistoryModel(Base):
    __tablename__ = 'test_cases_history'
    __table_args__ = {"sqlite_autoincrement": True}
    extend_existing = True
    row_id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"),
                                        primary_key=True)
    id: Mapped[int] = mapped_column(Integer())
    repository: Mapped[str] = mapped_column(String())
    relative_path: Mapped[str] = mapped_column(String())
    title: Mapped[str] = mapped_column(String())
    description: Mapped[str] = mapped_column(String())
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_by: Mapped["UserModel"] = relationship("UserModel",
                                                   foreign_keys="TestCaseHistoryModel.created_by_id")
    edited_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    edited_by: Mapped["UserModel"] = relationship("UserModel",
                                                  foreign_keys="TestCaseHistoryModel.edited_by_id")
    status: Mapped[str] = mapped_column(String(30))
    version: Mapped[int] = mapped_column(Integer())
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    def __init__(self, id, repository, relative_path, title, description,
                 created_by_id, edited_by_id, status, version):
        self.id = id
        self.repository = repository
        self.relative_path = relative_path
        self.title = title
        self.description = description
        self.status
        self.created_by_id = created_by_id
        self.edited_by_id = edited_by_id
        self.status = status
        self.version = version
        self.created_at = datetime.now()

    def __repr__(self) -> str:
        return f"TestCaseHistoryModel(row_id={self.row_id!r}, " \
               f"id={self.id!r}, " \
               f"repository={self.repository!r}, " \
               f"relative_path={self.relative_path!r}, " \
               f"title={self.title!r}, " \
               f"description={self.description!r}), " \
               f"created_by={self.created_by.email!r}, " \
               f"status={self.status!r}, " \
               f"version = {self.version!r},"
