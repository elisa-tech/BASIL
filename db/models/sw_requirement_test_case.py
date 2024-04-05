from datetime import datetime
from db.models.api_sw_requirement import ApiSwRequirementModel
from db.models.db_base import Base
from db.models.user import UserModel
from db.models.sw_requirement_sw_requirement import SwRequirementSwRequirementModel
from db.models.test_case import TestCaseModel, TestCaseHistoryModel
from db.models.test_specification_test_case import TestSpecificationTestCaseModel
from sqlalchemy import BigInteger, DateTime, Integer
from sqlalchemy import event, insert, select
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm.exc import NoResultFound
from typing import Optional


class SwRequirementTestCaseModel(Base):
    __tablename__ = "test_case_mapping_sw_requirement"
    __table_args__ = {"sqlite_autoincrement": True}
    extend_existing = True
    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"),
                                    primary_key=True)
    sw_requirement_mapping_api: Mapped[Optional["ApiSwRequirementModel"]] = relationship(
        "ApiSwRequirementModel", foreign_keys="SwRequirementTestCaseModel.sw_requirement_mapping_api_id")
    sw_requirement_mapping_api_id: Mapped[Optional[int]] = mapped_column(ForeignKey("sw_requirement_mapping_api.id"))
    sw_requirement_mapping_sw_requirement: Mapped[Optional["SwRequirementSwRequirementModel"]] = relationship(
        "SwRequirementSwRequirementModel",
        foreign_keys="SwRequirementTestCaseModel.sw_requirement_mapping_sw_requirement_id")
    sw_requirement_mapping_sw_requirement_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("sw_requirement_mapping_sw_requirement.id"))
    test_case_id: Mapped[int] = mapped_column(ForeignKey("test_cases.id"))
    test_case: Mapped["TestCaseModel"] = relationship(
        "TestCaseModel", foreign_keys="SwRequirementTestCaseModel.test_case_id")
    coverage: Mapped[int] = mapped_column(Integer())
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_by: Mapped["UserModel"] = relationship("UserModel",
                                                   foreign_keys="SwRequirementTestCaseModel.created_by_id")
    edited_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    edited_by: Mapped["UserModel"] = relationship("UserModel",
                                                  foreign_keys="SwRequirementTestCaseModel.edited_by_id")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    def __init__(self,
                 sw_requirement_mapping_api,
                 sw_requirement_mapping_sw_requirement,
                 test_case,
                 coverage,
                 created_by):
        if sw_requirement_mapping_api:
            self.sw_requirement_mapping_api = sw_requirement_mapping_api
            self.sw_requirement_mapping_api_id = sw_requirement_mapping_api.id
        if sw_requirement_mapping_sw_requirement:
            self.sw_requirement_mapping_sw_requirement = sw_requirement_mapping_sw_requirement
            self.sw_requirement_mapping_sw_requirement_id = sw_requirement_mapping_sw_requirement.id
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
        tmp = "SwRequirementTestCaseModel("
        for field in self.__table__.columns.keys():
            tmp += f"{field}={getattr(self, field)}, "
        tmp += ")"
        return tmp

    def current_version(self, db_session):
        last_mapping = db_session.query(SwRequirementTestCaseHistoryModel).filter(
            SwRequirementTestCaseHistoryModel.id == self.id).order_by(
            SwRequirementTestCaseHistoryModel.version.desc()).limit(1).all()[0]
        last_item = db_session.query(TestCaseHistoryModel).filter(
            TestCaseHistoryModel.id == self.test_case_id).order_by(
            TestCaseHistoryModel.version.desc()).limit(1).all()[0]
        return f'{last_item.version}.{last_mapping.version}'

    def as_dict(self, full_data=False, db_session=None):
        _dict = {'relation_id': self.id,
                 'coverage': self.coverage,
                 'covered': self.coverage,
                 'created_by': self.created_by.email}

        _dict['gap'] = _dict['coverage'] - _dict['covered']

        if self.sw_requirement_mapping_api_id:
            _dict['api'] = {'id': self.sw_requirement_mapping_api.api_id}
            _dict['sw_requirement'] = {'id': self.sw_requirement_mapping_api.sw_requirement.id}
        if self.sw_requirement_mapping_sw_requirement_id:
            _dict['direct_sw_requirement'] = {
                'id': self.sw_requirement_mapping_sw_requirement.get_parent_sw_requirement().id}
            _dict['sw_requirement'] = {'id': self.sw_requirement_mapping_sw_requirement.sw_requirement.id}

        if db_session is not None:
            _dict['version'] = self.current_version(db_session)
            _dict['test_case'] = self.test_case_as_dict(db_session)
        else:
            _dict['test_case'] = {'id': self.test_case_id}

        if full_data:
            _dict["created_at"] = self.created_at.strftime(Base.dt_format_str)
            _dict["updated_at"] = self.updated_at.strftime(Base.dt_format_str)
        return _dict

    def test_case_as_dict(self, db_session):
        try:
            tc = db_session.query(TestCaseModel).filter(
                TestCaseModel.id == self.test_case_id).one()
            return tc.as_dict()
        except NoResultFound:
            return None

    def get_indirect_test_cases(self, db_session):
        ts_tc_mapping = []
        ts_tcs = db_session.query(TestSpecificationTestCaseModel).filter(
            TestSpecificationTestCaseModel.test_specification_mapping_sw_requirement_id == self.id).all()

        for i in range(len(ts_tcs)):
            tmp = ts_tcs[i].as_dict(db_session=db_session)
            tmp['direct-relation-id'] = self.id  # ApiTestSpecification
            tmp['indirect-relation-id'] = tmp['id']  # TestSpecificationTestCaseModel
            tmp['mapped-to'] = "sw-requirement"
            tmp['direct'] = 0
            tmp['section'] = self.section
            tmp['offset'] = self.offset
            tmp['coverage'] = ((self.coverage / 100) * (ts_tcs[i].coverage / 100)) * 100
            tmp['test_case'] = ts_tcs[i].test_case.as_dict(db_session=db_session)
            ts_tc_mapping += [tmp]
        return ts_tc_mapping


@event.listens_for(SwRequirementTestCaseModel, "after_update")
def receive_after_update(mapper, connection, target):
    last_query = select(SwRequirementTestCaseHistoryModel.version).where(
        SwRequirementTestCaseHistoryModel.id == target.id).order_by(
        SwRequirementTestCaseHistoryModel.version.desc()).limit(1)
    version = -1
    for row in connection.execute(last_query):
        version = row[0]

    if version > -1:
        insert_query = insert(SwRequirementTestCaseHistoryModel).values(
            id=target.id,
            sw_requirement_mapping_api_id=target.sw_requirement_mapping_api_id,
            sw_requirement_mapping_sw_requirement_id=target.sw_requirement_mapping_sw_requirement_id,
            test_case_id=target.test_case_id,
            coverage=target.coverage,
            created_by_id=target.created_by_id,
            edited_by_id=target.edited_by_id,
            version=version + 1
        )
        connection.execute(insert_query)


@event.listens_for(SwRequirementTestCaseModel, "after_insert")
def receive_after_insert(mapper, connection, target):
    insert_query = insert(SwRequirementTestCaseHistoryModel).values(
        id=target.id,
        sw_requirement_mapping_api_id=target.sw_requirement_mapping_api_id,
        sw_requirement_mapping_sw_requirement_id=target.sw_requirement_mapping_sw_requirement_id,
        test_case_id=target.test_case_id,
        coverage=target.coverage,
        created_by_id=target.created_by_id,
        edited_by_id=target.edited_by_id,
        version=1
    )
    connection.execute(insert_query)


class SwRequirementTestCaseHistoryModel(Base):
    __tablename__ = 'test_case_mapping_sw_requirement_history'
    __table_args__ = {"sqlite_autoincrement": True}
    extend_existing = True
    row_id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"),
                                        primary_key=True)
    id: Mapped[int] = mapped_column(Integer())
    sw_requirement_mapping_api_id: Mapped[Optional[int]] = mapped_column(Integer())
    sw_requirement_mapping_sw_requirement_id: Mapped[Optional[int]] = mapped_column(Integer())
    test_case_id: Mapped[int] = mapped_column(Integer())
    coverage: Mapped[int] = mapped_column(Integer())
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_by: Mapped["UserModel"] = relationship("UserModel",
                                                   foreign_keys="SwRequirementTestCaseHistoryModel.created_by_id")
    edited_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    edited_by: Mapped["UserModel"] = relationship("UserModel",
                                                  foreign_keys="SwRequirementTestCaseHistoryModel.edited_by_id")
    version: Mapped[int] = mapped_column(Integer())
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    def __init__(self, id, sw_requirement_mapping_api_id, sw_requirement_mapping_sw_requirement_id,
                 test_case_id, coverage, created_by_id, edited_by_id, version):
        self.id = id
        self.sw_requirement_mapping_api_id = sw_requirement_mapping_api_id
        self.sw_requirement_mapping_sw_requirement_id = sw_requirement_mapping_sw_requirement_id
        self.test_case_id = test_case_id
        self.coverage = coverage
        self.created_by_id = created_by_id
        self.edited_by_id = edited_by_id
        self.version = version
        self.created_at = datetime.now()

    def __repr__(self) -> str:
        tmp = "SwRequirementTestCaseHistoryModel("
        for field in self.__table__.columns.keys():
            tmp += f"{field}={getattr(self, field)}, "
        tmp += ")"
        return tmp
