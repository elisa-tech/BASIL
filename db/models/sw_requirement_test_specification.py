from datetime import datetime
from db.models.api_sw_requirement import ApiSwRequirementModel
from db.models.db_base import Base
from db.models.user import UserModel
from db.models.sw_requirement_sw_requirement import SwRequirementSwRequirementModel
from db.models.test_specification import TestSpecificationModel, TestSpecificationHistoryModel
from sqlalchemy import BigInteger, DateTime, Integer
from sqlalchemy import event, insert, select
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm.exc import NoResultFound
from typing import Optional


class SwRequirementTestSpecificationModel(Base):
    __tablename__ = "test_specification_mapping_sw_requirement"
    __table_args__ = {"sqlite_autoincrement": True}
    extend_existing = True
    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"),
                                    primary_key=True)
    sw_requirement_mapping_api: Mapped[Optional["ApiSwRequirementModel"]] = relationship(
        "ApiSwRequirementModel", foreign_keys="SwRequirementTestSpecificationModel.sw_requirement_mapping_api_id")
    sw_requirement_mapping_api_id: Mapped[Optional[int]] = mapped_column(ForeignKey("sw_requirement_mapping_api.id"))
    sw_requirement_mapping_sw_requirement: Mapped[Optional["SwRequirementSwRequirementModel"]] = relationship(
        "SwRequirementSwRequirementModel",
        foreign_keys="SwRequirementTestSpecificationModel.sw_requirement_mapping_sw_requirement_id")
    sw_requirement_mapping_sw_requirement_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("sw_requirement_mapping_sw_requirement.id"))
    test_specification_id: Mapped[int] = mapped_column(ForeignKey("test_specifications.id"))
    test_specification: Mapped["TestSpecificationModel"] = relationship(
        "TestSpecificationModel", foreign_keys="SwRequirementTestSpecificationModel.test_specification_id")
    coverage: Mapped[int] = mapped_column(Integer())
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_by: Mapped["UserModel"] = relationship("UserModel",
                                                   foreign_keys="SwRequirementTestSpecificationModel.created_by_id")
    edited_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    edited_by: Mapped["UserModel"] = relationship("UserModel",
                                                  foreign_keys="SwRequirementTestSpecificationModel.edited_by_id")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    def __init__(self,
                 sw_requirement_mapping_api,
                 sw_requirement_mapping_sw_requirement,
                 test_specification,
                 coverage,
                 created_by):
        if sw_requirement_mapping_api:
            self.sw_requirement_mapping_api = sw_requirement_mapping_api
            self.sw_requirement_mapping_api_id = sw_requirement_mapping_api.id
        if sw_requirement_mapping_sw_requirement:
            self.sw_requirement_mapping_sw_requirement = sw_requirement_mapping_sw_requirement
            self.sw_requirement_mapping_sw_requirement_id = sw_requirement_mapping_sw_requirement.id
        self.test_specification = test_specification
        self.test_specification_id = test_specification.id
        self.coverage = coverage
        self.created_by = created_by
        self.created_by_id = created_by.id
        self.edited_by = created_by
        self.edited_by_id = created_by.id
        self.created_at = datetime.now()
        self.updated_at = self.created_at

    def __repr__(self) -> str:
        tmp = "SwRequirementTestSpecificationModel("
        for field in self.__table__.columns.keys():
            tmp += f"{field}={getattr(self, field)}, "
        tmp += ")"
        return tmp

    def current_version(self, db_session):
        last_mapping = db_session.query(SwRequirementTestSpecificationHistoryModel).filter(
            SwRequirementTestSpecificationHistoryModel.id == self.id).order_by(
            SwRequirementTestSpecificationHistoryModel.version.desc()).limit(1).all()[0]
        last_item = db_session.query(TestSpecificationHistoryModel).filter(
            TestSpecificationHistoryModel.id == self.test_specification_id).order_by(
            TestSpecificationHistoryModel.version.desc()).limit(1).all()[0]
        return f'{last_item.version}.{last_mapping.version}'

    def as_dict(self, full_data=False, db_session=None):
        print(self)
        _dict = {'relation_id': self.id,
                 'coverage': self.coverage,
                 'covered': self.get_waterfall_coverage(db_session),
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
            _dict['test_specification'] = self.test_specification_as_dict(db_session)
        else:
            _dict['test_specification'] = {'id': self.test_specification_id}

        if full_data:
            _dict["created_at"] = self.created_at.strftime(Base.dt_format_str)
            _dict["updated_at"] = self.updated_at.strftime(Base.dt_format_str)
        return _dict

    def test_specification_as_dict(self, db_session):
        try:
            ts = db_session.query(TestSpecificationModel).filter(
                TestSpecificationModel.id == self.test_specification_id).one()
            return ts.as_dict()
        except NoResultFound:
            return None

    def get_waterfall_coverage(self, db_session):
        if db_session is None:
            return self.coverage

        from db.models.test_specification_test_case import TestSpecificationTestCaseModel
        # Calc children(TestSpecificationTestCase) coverage
        # filtering with test_specification_mapping_sw_requirement_id
        # Return self.coverage * Sum(childrend coverage)

        tcs_coverage = 0

        # Test Cases
        tc_query = db_session.query(TestSpecificationTestCaseModel).filter(
            TestSpecificationTestCaseModel.test_specification_mapping_sw_requirement_id == self.id
        )
        tcs = tc_query.all()
        if len(tcs) > 0:
            tcs_coverage = sum([x.as_dict()['coverage'] for x in tcs])
        else:
            tcs_coverage = 100

        tcs_coverage = min(max(0, tcs_coverage), 100)
        waterfall_coverage = (self.coverage * tcs_coverage) / 100
        waterfall_coverage = min(max(0, waterfall_coverage), 100)
        return waterfall_coverage


@event.listens_for(SwRequirementTestSpecificationModel, "after_update")
def receive_after_update(mapper, connection, target):
    last_query = select(SwRequirementTestSpecificationHistoryModel.version).where(
        SwRequirementTestSpecificationHistoryModel.id == target.id).order_by(
        SwRequirementTestSpecificationHistoryModel.version.desc()).limit(1)
    version = -1
    for row in connection.execute(last_query):
        version = row[0]

    if version > -1:
        insert_query = insert(SwRequirementTestSpecificationHistoryModel).values(
            id=target.id,
            sw_requirement_mapping_api_id=target.sw_requirement_mapping_api_id,
            sw_requirement_mapping_sw_requirement_id=target.sw_requirement_mapping_sw_requirement_id,
            test_specification_id=target.test_specification_id,
            coverage=target.coverage,
            created_by_id=target.created_by_id,
            edited_by_id=target.edited_by_id,
            version=version + 1
        )
        connection.execute(insert_query)


@event.listens_for(SwRequirementTestSpecificationModel, "after_insert")
def receive_after_insert(mapper, connection, target):
    insert_query = insert(SwRequirementTestSpecificationHistoryModel).values(
        id=target.id,
        sw_requirement_mapping_api_id=target.sw_requirement_mapping_api_id,
        sw_requirement_mapping_sw_requirement_id=target.sw_requirement_mapping_sw_requirement_id,
        test_specification_id=target.test_specification_id,
        coverage=target.coverage,
        created_by_id=target.created_by_id,
        edited_by_id=target.edited_by_id,
        version=1
    )
    connection.execute(insert_query)


class SwRequirementTestSpecificationHistoryModel(Base):
    __tablename__ = 'test_specification_mapping_sw_requirement_history'
    __table_args__ = {"sqlite_autoincrement": True}
    extend_existing = True
    row_id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"),
                                        primary_key=True)
    id: Mapped[int] = mapped_column(Integer())
    sw_requirement_mapping_api_id: Mapped[Optional[int]] = mapped_column(Integer())
    sw_requirement_mapping_sw_requirement_id: Mapped[Optional[int]] = mapped_column(Integer())
    test_specification_id: Mapped[int] = mapped_column(Integer())
    coverage: Mapped[int] = mapped_column(Integer())
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_by: Mapped["UserModel"] = relationship("UserModel",
                                                   foreign_keys="SwRequirementTestSpecificationHistoryModel"
                                                                ".created_by_id")
    edited_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    edited_by: Mapped["UserModel"] = relationship("UserModel",
                                                  foreign_keys="SwRequirementTestSpecificationHistoryModel."
                                                               "edited_by_id")
    version: Mapped[int] = mapped_column(Integer())
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    def __init__(self, id, sw_requirement_mapping_api_id, sw_requirement_mapping_sw_requirement_id,
                 test_specification_id, coverage, created_by_id, edited_by_id, version):
        self.id = id
        self.sw_requirement_mapping_api_id = sw_requirement_mapping_api_id
        self.sw_requirement_mapping_sw_requirement_id = sw_requirement_mapping_sw_requirement_id
        self.test_specification_id = test_specification_id
        self.coverage = coverage
        self.created_by_id = created_by_id
        self.edited_by_id = edited_by_id
        self.version = version
        self.created_at = datetime.now()

    def __repr__(self) -> str:
        tmp = "SwRequirementTestSpecificationHistoryModel("
        for field in self.__table__.columns.keys():
            tmp += f"{field}={getattr(self, field)}, "
        tmp += ")"
        return tmp
