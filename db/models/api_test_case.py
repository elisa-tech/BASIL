from datetime import datetime
from db.models.api import ApiModel
from db.models.db_base import Base
from db.models.test_case import TestCaseModel, TestCaseHistoryModel
from db.models.comment import CommentModel
from db.models.user import UserModel
from sqlalchemy import DateTime, Integer, String
from sqlalchemy import delete, event, insert, select
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column


class ApiTestCaseModel(Base):
    __tablename__ = "test_case_mapping_api"
    extend_existing = True
    id: Mapped[int] = mapped_column(Integer(), primary_key=True, autoincrement=True)
    api_id: Mapped[int] = mapped_column(ForeignKey("apis.id", ondelete="CASCADE"))
    api: Mapped["ApiModel"] = relationship("ApiModel", foreign_keys="ApiTestCaseModel.api_id")
    test_case_id: Mapped[int] = mapped_column(ForeignKey("test_cases.id", ondelete="CASCADE"))
    test_case: Mapped["TestCaseModel"] = relationship("TestCaseModel", foreign_keys="ApiTestCaseModel.test_case_id")
    section: Mapped[str] = mapped_column(String())
    offset: Mapped[int] = mapped_column(Integer())
    coverage: Mapped[int] = mapped_column(Integer())
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    created_by: Mapped["UserModel"] = relationship("UserModel",
                                                   foreign_keys="ApiTestCaseModel.created_by_id")
    edited_by_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    edited_by: Mapped["UserModel"] = relationship("UserModel",
                                                  foreign_keys="ApiTestCaseModel.edited_by_id")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    def __init__(self, api, test_case, section, offset, coverage, created_by):
        self.api = api
        self.api_id = api.id
        self.test_case = test_case
        self.test_case_id = test_case.id
        self.section = section
        self.offset = offset
        self.coverage = coverage
        self.created_by = created_by
        self.created_by_id = created_by.id
        self.edited_by = created_by
        self.edited_by_id = created_by.id
        self.created_at = datetime.now()
        self.updated_at = self.created_at

    def __repr__(self) -> str:
        return f"ApiTestCaseModel(id={self.id!r}, " \
               f"api_id={self.api_id!r}, " \
               f"test_case_id={self.test_case_id!r}, " \
               f"section={self.section!r}, " \
               f"coverage={self.coverage!r}), " \
               f"offset={self.offset!r})  - " \
               f"created_by={self.created_by.username!r}, " \
               f"{str(self.api)!r} - " \
               f"{str(self.test_case)!r}"

    def current_version(self, db_session):
        last_mapping = db_session.query(ApiTestCaseHistoryModel).filter(
                        ApiTestCaseHistoryModel.id == self.id).order_by(
                        ApiTestCaseHistoryModel.version.desc()).limit(1).all()[0]
        last_item = db_session.query(TestCaseHistoryModel).filter(
                     TestCaseHistoryModel.id == self.test_case_id).order_by(
                     TestCaseHistoryModel.version.desc()).limit(1).all()[0]
        return f'{last_item.version}.{last_mapping.version}'

    def as_dict(self, full_data=False, db_session=None):
        _dict = {'test_case': self.test_case.as_dict(full_data=full_data, db_session=db_session),
                 'relation_id': self.id,
                 'section': self.section,
                 'offset': self.offset,
                 'coverage': self.coverage,
                 'covered': self.coverage,
                 'created_by': self.created_by.username}

        _dict['gap'] = _dict['coverage'] - _dict['covered']

        if db_session:
            _dict['version'] = self.current_version(db_session)
            # Comments
            _dict['test_case']['comment_count'] = len(db_session.query(CommentModel).filter(
                CommentModel.parent_table == self.__tablename__
            ).filter(
                CommentModel.parent_id == self.id
            ).all())

        if full_data:
            _dict['api'] = self.api.as_dict(full_data=full_data, db_session=db_session)
            _dict["created_at"] = self.created_at.strftime(Base.dt_format_str)
            _dict["updated_at"] = self.updated_at.strftime(Base.dt_format_str)
        return _dict

    def fork(self, new_api, db_session):
        new_api_test_case = ApiTestCaseModel(
            api=new_api,
            test_case=self.test_case,
            section=self.section,
            offset=self.offset,
            coverage=self.coverage,
            created_by=self.created_by
        )
        db_session.add(new_api_test_case)
        db_session.commit()
        return new_api_test_case


@event.listens_for(ApiTestCaseModel, "after_update")
def receive_after_update(mapper, connection, target):
    last_query = select(ApiTestCaseHistoryModel.version).where(
        ApiTestCaseHistoryModel.id == target.id).order_by(
        ApiTestCaseHistoryModel.version.desc()).limit(1)
    version = -1
    for row in connection.execute(last_query):
        version = row[0]

    if version > -1:
        insert_query = insert(ApiTestCaseHistoryModel).values(
            id=target.id,
            api_id=target.api_id,
            test_case_id=target.test_case_id,
            section=target.section,
            offset=target.offset,
            coverage=target.coverage,
            created_by_id=target.created_by_id,
            edited_by_id=target.edited_by_id,
            version=version + 1
        )
        connection.execute(insert_query)


@event.listens_for(ApiTestCaseModel, "after_insert")
def receive_after_insert(mapper, connection, target):
    insert_query = insert(ApiTestCaseHistoryModel).values(
        id=target.id,
        api_id=target.api_id,
        test_case_id=target.test_case_id,
        section=target.section,
        offset=target.offset,
        coverage=target.coverage,
        created_by_id=target.created_by_id,
        edited_by_id=target.edited_by_id,
        version=1
    )
    connection.execute(insert_query)


@event.listens_for(ApiTestCaseModel, "before_delete")
def receive_before_delete(mapper, connection, target):
    # Purge history rows for this mapping id
    del_stmt = delete(ApiTestCaseHistoryModel).where(ApiTestCaseHistoryModel.id == target.id)
    connection.execute(del_stmt)


class ApiTestCaseHistoryModel(Base):
    __tablename__ = 'test_case_mapping_api_history'
    extend_existing = True
    row_id: Mapped[int] = mapped_column(Integer(), primary_key=True, autoincrement=True)
    id: Mapped[int] = mapped_column(Integer())
    api_id: Mapped[int] = mapped_column(Integer())
    test_case_id: Mapped[int] = mapped_column(Integer())
    section: Mapped[str] = mapped_column(String())
    offset: Mapped[int] = mapped_column(Integer())
    coverage: Mapped[int] = mapped_column(Integer())
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    created_by: Mapped["UserModel"] = relationship("UserModel",
                                                   foreign_keys="ApiTestCaseHistoryModel.created_by_id")
    edited_by_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    edited_by: Mapped["UserModel"] = relationship("UserModel",
                                                  foreign_keys="ApiTestCaseHistoryModel.edited_by_id")
    version: Mapped[int] = mapped_column(Integer())
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    def __init__(self, id, api_id, test_case_id, section, offset,
                 coverage, created_by_id, edited_by_id, version):
        self.id = id
        self.api_id = api_id
        self.test_case_id = test_case_id
        self.section = section
        self.offset = offset
        self.coverage = coverage
        self.created_by_id = created_by_id
        self.edited_by_id = edited_by_id
        self.version = version
        self.created_at = datetime.now()

    def __repr__(self) -> str:
        return f"ApiTestCaseHistoryModel(row_id={self.row_id!r}, " \
               f"id={self.id!r}, " \
               f"version={self.version!r}, " \
               f"api_id={self.api_id!r}, " \
               f"test_case_id={self.test_case_id!r}, " \
               f"coverage={self.coverage!r}, " \
               f"offset={self.offset!r}, " \
               f"created_by={self.created_by.username!r}, " \
               f"version={self.version!r})"
