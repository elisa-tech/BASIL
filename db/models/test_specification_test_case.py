from datetime import datetime
from db.models.test_case import TestCaseModel, TestCaseHistoryModel
from db.models.api_test_specification import ApiTestSpecificationModel
from db.models.sw_requirement_test_specification import SwRequirementTestSpecificationModel
from db.models.user import UserModel
from db.models.db_base import Base
from sqlalchemy import BigInteger, DateTime, Integer
from sqlalchemy import event, insert, select
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm.exc import NoResultFound
from typing import Optional


class TestSpecificationTestCaseModel(Base):
    __tablename__ = "test_case_mapping_test_specification"
    __table_args__ = {"sqlite_autoincrement": True}
    extend_existing = True
    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"),
                                    primary_key=True)
    test_specification_mapping_api_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("test_specification_mapping_api.id"))
    test_specification_mapping_api: Mapped[Optional["ApiTestSpecificationModel"]] = relationship(
        "ApiTestSpecificationModel", foreign_keys="TestSpecificationTestCaseModel.test_specification_mapping_api_id")
    test_specification_mapping_sw_requirement_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("test_specification_mapping_sw_requirement.id"))
    test_specification_mapping_sw_requirement: Mapped[Optional["SwRequirementTestSpecificationModel"]] = relationship(
        "SwRequirementTestSpecificationModel",
        foreign_keys="TestSpecificationTestCaseModel.test_specification_mapping_sw_requirement_id")
    test_case_id: Mapped[int] = mapped_column(ForeignKey("test_cases.id"))
    test_case: Mapped["TestCaseModel"] = relationship(
        "TestCaseModel", foreign_keys="TestSpecificationTestCaseModel.test_case_id")
    coverage: Mapped[int] = mapped_column(Integer())
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_by: Mapped["UserModel"] = relationship("UserModel",
                                                   foreign_keys="TestSpecificationTestCaseModel.created_by_id")
    edited_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    edited_by: Mapped["UserModel"] = relationship("UserModel",
                                                  foreign_keys="TestSpecificationTestCaseModel.edited_by_id")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    def __init__(self,
                 test_specification_mapping_api,
                 test_specification_mapping_sw_requirement,
                 test_case,
                 coverage,
                 created_by):

        if test_specification_mapping_api:
            self.test_specification_mapping_api = test_specification_mapping_api
            self.test_specification_mapping_api_id = test_specification_mapping_api.id
        if test_specification_mapping_sw_requirement:
            self.test_specification_mapping_sw_requirement = test_specification_mapping_sw_requirement
            self.test_specification_mapping_sw_requirement_id = test_specification_mapping_sw_requirement.id
        self.test_case = test_case
        self.test_case_id = test_case.id
        self.coverage = coverage
        self.created_by = created_by
        self.created_by_id = created_by.id
        self.edited_by = created_by
        self.edited_by_id = created_by.id
        self.created_at = datetime.now()
        self.updated_at = self.created_at

    def __repr__(self) -> str:
        return f"TestSpecificationTestCaseModel(id={self.id!r}, " \
               f"test_specification_mapping_api_id={self.test_specification_mapping_api_id!r}, " \
               f"test_specification_mapping_sw_requirement={self.test_specification_mapping_sw_requirement_id!r}, " \
               f"test_case_id={self.test_case_id!r}, " \
               f"coverage={self.coverage!r})"

    def as_dict(self, full_data=False, db_session=None):

        _dict = {'relation_id': self.id,
                 'test_specification_mapping_api_id': self.test_specification_mapping_api_id,
                 'test_specification_mapping_sw_requirement_id': self.test_specification_mapping_sw_requirement_id,
                 'coverage': self.coverage,
                 'covered': self.coverage,
                 'created_by': self.created_by.email}

        _dict['gap'] = _dict['coverage'] - _dict['covered']

        if self.test_specification_mapping_api_id:
            _dict['api'] = {'id': self.test_specification_mapping_api.api_id}
            _dict['test_specification'] = {'id': self.test_specification_mapping_api.test_specification.id}
        if self.test_specification_mapping_sw_requirement_id:
            if self.test_specification_mapping_sw_requirement.sw_requirement_mapping_api:
                _dict['sw_requirement'] = {
                    'id': self.test_specification_mapping_sw_requirement
                    .sw_requirement_mapping_api.sw_requirement_id}
            else:
                _dict['sw_requirement'] = {
                    'id': self.test_specification_mapping_sw_requirement
                    .sw_requirement_mapping_sw_requirement.sw_requirement_id}
            _dict['test_specification'] = {'id': self.test_specification_mapping_sw_requirement.test_specification.id}

        if db_session is not None:
            _dict['version'] = self.current_version(db_session)
            _dict['test_case'] = self.test_case_as_dict(db_session)
        else:
            _dict['test_case'] = {'id': self.test_case_id}

        if full_data:
            _dict["created_at"] = self.created_at.strftime(Base.dt_format_str)
            _dict["updated_at"] = self.updated_at.strftime(Base.dt_format_str)

        return _dict

    def current_version(self, db_session):
        last_mapping = db_session.query(TestSpecificationTestCaseHistoryModel).filter(
            TestSpecificationTestCaseHistoryModel.id == self.id).order_by(
            TestSpecificationTestCaseHistoryModel.version.desc()).limit(1).all()[0]

        last_item = db_session.query(TestCaseHistoryModel).filter(
            TestCaseHistoryModel.id == self.test_case_id).order_by(
            TestCaseHistoryModel.version.desc()).limit(1).all()[0]

        return f'{last_item.version}.{last_mapping.version}'

    def test_case_as_dict(self, db_session):
        try:
            tc = db_session.query(TestCaseModel).filter(
                TestCaseModel.id == self.test_case_id).one()
            return tc.as_dict(db_session)
        except NoResultFound:
            return None


@event.listens_for(TestSpecificationTestCaseModel, "after_update")
def receive_after_update(mapper, connection, target):
    last_query = select(TestSpecificationTestCaseHistoryModel.version).where(
        TestSpecificationTestCaseHistoryModel.id == target.id).order_by(
        TestSpecificationTestCaseHistoryModel.version.desc()).limit(1)
    version = -1
    for row in connection.execute(last_query):
        version = row[0]

    if version > -1:
        insert_query = insert(TestSpecificationTestCaseHistoryModel).values(
            id=target.id,
            test_specification_mapping_api_id=target.test_specification_mapping_api_id,
            test_specification_mapping_sw_requirement_id=target.test_specification_mapping_sw_requirement_id,
            test_case_id=target.test_case_id,
            coverage=target.coverage,
            created_by_id=target.created_by_id,
            edited_by_id=target.edited_by_id,
            version=version + 1
        )
        connection.execute(insert_query)


@event.listens_for(TestSpecificationTestCaseModel, "after_insert")
def receive_after_insert(mapper, connection, target):
    insert_query = insert(TestSpecificationTestCaseHistoryModel).values(
        id=target.id,
        test_specification_mapping_api_id=target.test_specification_mapping_api_id,
        test_specification_mapping_sw_requirement_id=target.test_specification_mapping_sw_requirement_id,
        test_case_id=target.test_case_id,
        coverage=target.coverage,
        created_by_id=target.created_by_id,
        edited_by_id=target.edited_by_id,
        version=1
    )
    connection.execute(insert_query)


class TestSpecificationTestCaseHistoryModel(Base):
    __tablename__ = 'test_case_mapping_test_specification_history'
    __table_args__ = {"sqlite_autoincrement": True}
    extend_existing = True
    row_id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"),
                                        primary_key=True)
    id: Mapped[int] = mapped_column(Integer())
    test_specification_mapping_api_id: Mapped[Optional[int]] = mapped_column(Integer())
    test_specification_mapping_sw_requirement_id: Mapped[Optional[int]] = mapped_column(Integer())
    test_case_id: Mapped[int] = mapped_column(Integer())
    coverage: Mapped[int] = mapped_column(Integer())
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_by: Mapped["UserModel"] = relationship("UserModel",
                                                   foreign_keys="TestSpecificationTestCaseHistoryModel.created_by_id")
    edited_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    edited_by: Mapped["UserModel"] = relationship("UserModel",
                                                  foreign_keys="TestSpecificationTestCaseHistoryModel.edited_by_id")
    version: Mapped[int] = mapped_column(Integer())
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    def __init__(self, id,
                 test_specification_mapping_api_id,
                 test_specification_mapping_sw_requirement_id,
                 test_case_id, coverage, created_by_id, edited_by_id, version):

        self.id = id
        self.test_specification_mapping_api_id = test_specification_mapping_api_id
        self.test_specification_mapping_sw_requirement_id = test_specification_mapping_sw_requirement_id
        self.test_case_id = test_case_id
        self.coverage = coverage
        self.created_by_id = created_by_id
        self.edited_by_id = edited_by_id
        self.version = version
        self.created_at = datetime.now()

    def __repr__(self) -> str:
        return f"TestSpecificationTestCaseHistoryModel(row_id={self.row_id!r}, " \
               f"id={self.id!r}, version={self.version!r}, " \
               f"test_specification_mapping_api_id={self.test_specification_mapping_api_id!r}, " \
               f"test_specification_mapping_sw_requirement_id=" \
               f"{self.test_specification_mapping_sw_requirement_id!r}, " \
               f"test_case_id={self.test_case_id!r}, " \
               f"created_by={self.created_by.email!r}, " \
               f"coverage={self.coverage!r}, version={self.version!r})"
