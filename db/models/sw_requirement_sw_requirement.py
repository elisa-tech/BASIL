from datetime import datetime
from db.models.api_sw_requirement import ApiSwRequirementModel
from db.models.db_base import Base
from db.models.comment import CommentModel
from db.models.user import UserModel
from db.models.sw_requirement import SwRequirementModel, SwRequirementHistoryModel
from sqlalchemy import BigInteger, DateTime, Integer
from sqlalchemy import event, insert, select
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from typing import Optional


class SwRequirementSwRequirementModel(Base):
    __tablename__ = "sw_requirement_mapping_sw_requirement"
    __table_args__ = {"sqlite_autoincrement": True}
    extend_existing = True
    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"),
                                    primary_key=True)
    sw_requirement_mapping_api: Mapped[Optional["ApiSwRequirementModel"]] = relationship(
        "ApiSwRequirementModel", foreign_keys="SwRequirementSwRequirementModel.sw_requirement_mapping_api_id")
    sw_requirement_mapping_api_id: Mapped[Optional[int]] = mapped_column(ForeignKey("sw_requirement_mapping_api.id"))
    sw_requirement_mapping_sw_requirement: Mapped[Optional["SwRequirementSwRequirementModel"]] = relationship(
        "SwRequirementSwRequirementModel",
        remote_side=id,
        foreign_keys="SwRequirementSwRequirementModel.sw_requirement_mapping_sw_requirement_id")
    sw_requirement_mapping_sw_requirement_id: Mapped[Optional[int]] = mapped_column(ForeignKey(id))
    sw_requirement_id: Mapped[int] = mapped_column(ForeignKey("sw_requirements.id"))
    sw_requirement: Mapped["SwRequirementModel"] = relationship(
        "SwRequirementModel",
        foreign_keys="SwRequirementSwRequirementModel.sw_requirement_id")
    coverage: Mapped[int] = mapped_column(Integer())
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_by: Mapped["UserModel"] = relationship("UserModel",
                                                   foreign_keys="SwRequirementSwRequirementModel.created_by_id")
    edited_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    edited_by: Mapped["UserModel"] = relationship("UserModel",
                                                  foreign_keys="SwRequirementSwRequirementModel.edited_by_id")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    def __init__(self,
                 sw_requirement_mapping_api,
                 sw_requirement_mapping_sw_requirement,
                 sw_requirement,
                 coverage,
                 created_by):
        if sw_requirement_mapping_api:
            self.sw_requirement_mapping_api = sw_requirement_mapping_api
            self.sw_requirement_mapping_api_id = sw_requirement_mapping_api.id
        if sw_requirement_mapping_sw_requirement:
            self.sw_requirement_mapping_sw_requirement = sw_requirement_mapping_sw_requirement
            self.sw_requirement_mapping_sw_requirement_id = sw_requirement_mapping_sw_requirement.id
        self.sw_requirement = sw_requirement
        self.sw_requirement_id = sw_requirement.id
        self.coverage = coverage
        self.created_by = created_by
        self.created_by_id = created_by.id
        self.edited_by = created_by
        self.edited_by_id = created_by.id
        self.created_at = datetime.now()
        self.updated_at = self.created_at

    def __repr__(self) -> str:
        tmp = "SwRequirementSwRequirementModel("
        for field in self.__table__.columns.keys():
            tmp += f"{field}={getattr(self, field)}, "
        tmp += ")"
        return tmp

    def get_parent_sw_requirement(self):
        if self.sw_requirement_mapping_api_id:
            return self.sw_requirement_mapping_api.sw_requirement
        if self.sw_requirement_mapping_sw_requirement_id:
            return self.sw_requirement_mapping_sw_requirement.sw_requirement
        return None

    def current_version(self, db_session):
        last_mapping = db_session.query(SwRequirementSwRequirementHistoryModel).filter(
            SwRequirementSwRequirementHistoryModel.id == self.id).order_by(
            SwRequirementSwRequirementHistoryModel.version.desc()).limit(1).all()[0]
        last_item = db_session.query(SwRequirementHistoryModel).filter(
            SwRequirementHistoryModel.id == self.sw_requirement_id).order_by(
            SwRequirementHistoryModel.version.desc()).limit(1).all()[0]
        return f'{last_item.version}.{last_mapping.version}'

    def as_dict(self, full_data=False, db_session=None):
        _dict = {'relation_id': self.id,
                 'sw_requirement_mapping_api_id': self.sw_requirement_mapping_api_id,
                 'sw_requirement_mapping_sw_requirement_id': self.sw_requirement_mapping_api_id,
                 'coverage': self.coverage,
                 'covered': self.get_waterfall_coverage(db_session),
                 'created_by': self.created_by.email,
                 '__tablename__': self.__tablename__}

        _dict['gap'] = _dict['coverage'] - _dict['covered']

        if self.sw_requirement_mapping_api_id:
            _dict['api'] = {'id': self.sw_requirement_mapping_api.api_id}
            _dict['direct_sw_requirement'] = {'id': self.sw_requirement_mapping_api.sw_requirement.id}
        elif self.sw_requirement_mapping_sw_requirement_id:
            print(f"self.sw_requirement_mapping_sw_requirement_id: {self.sw_requirement_mapping_sw_requirement_id}")
            _dict['indirect_sw_requirement'] = {
                'id': self.sw_requirement_mapping_sw_requirement.get_parent_sw_requirement().id}
            _dict['direct_sw_requirement'] = {'id': self.sw_requirement_mapping_sw_requirement.sw_requirement.id}

        if db_session is not None:
            _dict['version'] = self.current_version(db_session)
            _dict['sw_requirement'] = self.sw_requirement.as_dict(full_data=full_data, db_session=db_session)
            # Comments
            _dict['sw_requirement']['comment_count'] = len(db_session.query(CommentModel).filter(
                CommentModel.parent_table == self.__tablename__
            ).filter(
                CommentModel.parent_id == self.id
            ).all())
        else:
            _dict['sw_requirement'] = {'id': self.sw_requirement_id}

        if full_data:
            _dict["created_at"] = self.created_at.strftime(Base.dt_format_str)
            _dict["updated_at"] = self.updated_at.strftime(Base.dt_format_str)
        return _dict

    def get_waterfall_coverage(self, db_session):
        from db.models.sw_requirement_test_case import SwRequirementTestCaseModel
        from db.models.sw_requirement_test_specification import SwRequirementTestSpecificationModel
        # Return SR-SR waterfall coverage

        if db_session is None:
            return self.coverage

        srs_coverage = 0
        tss_coverage = 0
        tcs_coverage = 0

        # Sw Requirements
        srs = db_session.query(SwRequirementSwRequirementModel).filter(
            SwRequirementSwRequirementModel.sw_requirement_mapping_sw_requirement_id == self.id
        ).all()
        print(srs)
        if len(srs) > 0:
            srs_coverage = sum([x.get_waterfall_coverage(db_session) for x in srs])
            print(f"srs_coverage: {srs_coverage}")

        # Test Specifications
        ts_query = db_session.query(SwRequirementTestSpecificationModel).filter(
            SwRequirementTestSpecificationModel.sw_requirement_mapping_sw_requirement_id == self.id
        )
        tss = ts_query.all()
        if len(tss) > 0:
            tss_coverage = sum([x.get_waterfall_coverage(db_session) for x in tss])
            print(f"tss_coverage: {tss_coverage}")

        # Test Cases
        tc_query = db_session.query(SwRequirementTestCaseModel).filter(
            SwRequirementTestCaseModel.sw_requirement_mapping_sw_requirement_id == self.id
        )
        tcs = tc_query.all()
        if len(tcs) > 0:
            tcs_coverage = sum([x.as_dict()['coverage'] for x in tcs])
            print(f"tcs_coverage: {tss_coverage}")

        if len(tcs) == len(tss) == len(srs) == 0:
            waterfall_coverage = self.coverage
        else:
            waterfall_coverage = (min(max(0, srs_coverage + tss_coverage + tcs_coverage), 100) * self.coverage) / 100.0

        waterfall_coverage = min(max(0, waterfall_coverage), 100)
        return waterfall_coverage


@event.listens_for(SwRequirementSwRequirementModel, "after_update")
def receive_after_update(mapper, connection, target):
    last_query = select(SwRequirementSwRequirementHistoryModel.version).where(
        SwRequirementSwRequirementHistoryModel.id == target.id).order_by(
        SwRequirementSwRequirementHistoryModel.version.desc()).limit(1)
    version = -1
    for row in connection.execute(last_query):
        version = row[0]

    if version > -1:
        insert_query = insert(SwRequirementSwRequirementHistoryModel).values(
            id=target.id,
            sw_requirement_mapping_api_id=target.sw_requirement_mapping_api_id,
            sw_requirement_mapping_sw_requirement_id=target.sw_requirement_mapping_sw_requirement_id,
            sw_requirement_id=target.sw_requirement_id,
            coverage=target.coverage,
            created_by_id=target.created_by_id,
            edited_by_id=target.edited_by_id,
            version=version + 1
        )
        connection.execute(insert_query)


@event.listens_for(SwRequirementSwRequirementModel, "after_insert")
def receive_after_insert(mapper, connection, target):
    insert_query = insert(SwRequirementSwRequirementHistoryModel).values(
        id=target.id,
        sw_requirement_mapping_api_id=target.sw_requirement_mapping_api_id,
        sw_requirement_mapping_sw_requirement_id=target.sw_requirement_mapping_sw_requirement_id,
        sw_requirement_id=target.sw_requirement_id,
        coverage=target.coverage,
        created_by_id=target.created_by_id,
        edited_by_id=target.edited_by_id,
        version=1
    )
    connection.execute(insert_query)


class SwRequirementSwRequirementHistoryModel(Base):
    __tablename__ = 'sw_requirement_mapping_sw_requirement_history'
    __table_args__ = {"sqlite_autoincrement": True}
    extend_existing = True
    row_id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"),
                                        primary_key=True)
    id: Mapped[int] = mapped_column(Integer())
    sw_requirement_mapping_api_id: Mapped[Optional[int]] = mapped_column(Integer())
    sw_requirement_mapping_sw_requirement_id: Mapped[Optional[int]] = mapped_column(Integer())
    sw_requirement_id: Mapped[int] = mapped_column(Integer())
    coverage: Mapped[int] = mapped_column(Integer())
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_by: Mapped["UserModel"] = relationship("UserModel",
                                                   foreign_keys="SwRequirementSwRequirementHistoryModel.created_by_id")
    edited_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    edited_by: Mapped["UserModel"] = relationship("UserModel",
                                                  foreign_keys="SwRequirementSwRequirementHistoryModel.edited_by_id")
    version: Mapped[int] = mapped_column(Integer())
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    def __init__(self,
                 id,
                 sw_requirement_mapping_api_id,
                 sw_requirement_mapping_sw_requirement_id,
                 sw_requirement_id,
                 coverage,
                 created_by_id,
                 edited_by_id,
                 version):
        self.id = id
        self.sw_requirement_mapping_api_id = sw_requirement_mapping_api_id
        self.sw_requirement_mapping_sw_requirement_id = sw_requirement_mapping_sw_requirement_id
        self.sw_requirement_id = sw_requirement_id
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
