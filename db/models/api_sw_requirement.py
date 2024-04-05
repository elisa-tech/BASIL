from datetime import datetime
from db.models.api import ApiModel
from db.models.db_base import Base
from db.models.user import UserModel
from db.models.sw_requirement import SwRequirementModel, SwRequirementHistoryModel
from db.models.comment import CommentModel
from sqlalchemy import BigInteger, DateTime, Integer, String
from sqlalchemy import event, insert, select
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column


class ApiSwRequirementModel(Base):
    __tablename__ = "sw_requirement_mapping_api"
    __table_args__ = {"sqlite_autoincrement": True}
    extend_existing = True
    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"),
                                    primary_key=True)
    api_id: Mapped[int] = mapped_column(ForeignKey("apis.id"))
    api: Mapped["ApiModel"] = relationship("ApiModel", foreign_keys="ApiSwRequirementModel.api_id")
    sw_requirement_id: Mapped[int] = mapped_column(ForeignKey("sw_requirements.id"))
    sw_requirement: Mapped["SwRequirementModel"] = relationship("SwRequirementModel",
                                                                foreign_keys="ApiSwRequirementModel.sw_requirement_id")
    section: Mapped[str] = mapped_column(String())
    offset: Mapped[int] = mapped_column(Integer())
    coverage: Mapped[int] = mapped_column(Integer())
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_by: Mapped["UserModel"] = relationship("UserModel",
                                                   foreign_keys="ApiSwRequirementModel.created_by_id")
    edited_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    edited_by: Mapped["UserModel"] = relationship("UserModel",
                                                  foreign_keys="ApiSwRequirementModel.edited_by_id")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    def __init__(self, api, sw_requirement, section, offset, coverage, created_by):
        self.api = api
        self.api_id = api.id
        self.sw_requirement = sw_requirement
        self.sw_requirement_id = sw_requirement.id
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
        return f"ApiSwRequirementModel(id={self.id!r}, " \
               f"section={self.section!r}, " \
               f"offset={self.offset!r}, " \
               f"coverage={self.coverage!r}," \
               f"api_id={self.api_id!r}, " \
               f"created_by={self.created_by.email!r}, " \
               f"sw_requirement_id={self.sw_requirement_id!r}) - {str(self.api)!r} " \
               f"- {str(self.sw_requirement)!r}"

    def get_indirect_test_cases(self, db_session):
        from db.models.sw_requirement_test_case import SwRequirementTestCaseModel
        sr_tc_mapping = []
        sr_tcs = db_session.query(SwRequirementTestCaseModel).filter(
                SwRequirementTestCaseModel.sw_requirement_mapping_api_id == self.id).all()

        for i in range(len(sr_tcs)):
            tmp = sr_tcs[i].as_dict(db_session=db_session)
            tmp['direct-relation-id'] = self.id  # ApiSwRequirementModel
            tmp['indirect-relation-id'] = tmp['id']  # SwRequirementTestCaseModel
            tmp['mapped-to'] = "sw-requirement"
            tmp['direct'] = 0
            tmp['section'] = self.section
            tmp['offset'] = self.offset
            tmp['coverage'] = ((self.coverage/100) * (sr_tcs[i].coverage / 100)) * 100
            tmp['test_case'] = sr_tcs[i].test_case.as_dict(db_session=db_session)
            sr_tc_mapping += [tmp]

        return sr_tc_mapping

    def get_indirect_test_specifications(self, db_session):
        from db.models.sw_requirement_test_specification import SwRequirementTestSpecificationModel
        sr_ts_mapping = []
        sr_tss = db_session.query(SwRequirementTestSpecificationModel).filter(
                SwRequirementTestSpecificationModel.sw_requirement_mapping_api_id == self.id).all()

        for i in range(len(sr_tss)):
            tmp = sr_tss[i].as_dict(db_session=db_session)
            tmp['direct-relation-id'] = self.id  # ApiSwRequirementModel
            tmp['indirect-relation-id'] = tmp['id']  # SwRequirementTestSpecifcationModel
            tmp['mapped-to'] = "sw-requirement"
            tmp['test_specification'] = sr_tss[i].test_specification.as_dict(db_session=db_session)
            tmp['direct'] = 0
            tmp['section'] = self.section
            tmp['offset'] = self.offset
            tmp['coverage'] = ((self.coverage / 100) * (sr_tss[i].coverage / 100)) * 100
            sr_ts_mapping += [tmp]
        return sr_ts_mapping

    def current_version(self, db_session):
        last_mapping = db_session.query(ApiSwRequirementHistoryModel).filter(
                        ApiSwRequirementHistoryModel.id == self.id).order_by(
                        ApiSwRequirementHistoryModel.version.desc()).limit(1).all()[0]

        last_item = db_session.query(SwRequirementHistoryModel).filter(
                     SwRequirementHistoryModel.id == self.sw_requirement_id).order_by(
                     SwRequirementHistoryModel.version.desc()).limit(1).all()[0]

        return f'{last_item.version}.{last_mapping.version}'

    def as_dict(self, full_data=False, db_session=None):
        _dict = {'sw_requirement': self.sw_requirement.as_dict(full_data=full_data, db_session=db_session),
                 'relation_id': self.id,
                 'section': self.section,
                 'offset': self.offset,
                 'direct': True,
                 'coverage': self.coverage,
                 'created_by': self.created_by.email,
                 'covered': self.get_waterfall_coverage(db_session),
                 '__tablename__': self.__tablename__}

        _dict['gap'] = _dict['coverage'] - _dict['covered']

        if db_session:
            _dict['version'] = self.current_version(db_session)
            # Comments
            _dict['sw_requirement']['comment_count'] = len(db_session.query(CommentModel).filter(
                CommentModel.parent_table == self.__tablename__
            ).filter(
                CommentModel.parent_id == self.id
            ).all())

        if full_data:
            _dict['api'] = self.api.as_dict(full_data=full_data, db_session=db_session)
            _dict["created_at"] = self.created_at.strftime(Base.dt_format_str)
            _dict["updated_at"] = self.updated_at.strftime(Base.dt_format_str)
        return _dict

    def get_waterfall_coverage(self, db_session):
        from db.models.sw_requirement_sw_requirement import SwRequirementSwRequirementModel
        from db.models.sw_requirement_test_case import SwRequirementTestCaseModel
        from db.models.sw_requirement_test_specification import SwRequirementTestSpecificationModel
        # Return Api-SR waterfall coverage

        if db_session is None:
            return self.coverage

        srs_coverage = 0
        tss_coverage = 0
        tcs_coverage = 0

        # Sw Requirements
        sr_query = db_session.query(SwRequirementSwRequirementModel).filter(
            SwRequirementSwRequirementModel.sw_requirement_mapping_api_id == self.id
        )
        srs = sr_query.all()
        if len(srs) > 0:
            srs_coverage = sum([x.get_waterfall_coverage(db_session) for x in srs])

        # Test Specifications
        ts_query = db_session.query(SwRequirementTestSpecificationModel).filter(
            SwRequirementTestSpecificationModel.sw_requirement_mapping_api_id == self.id
        )
        tss = ts_query.all()
        if len(tss) > 0:
            tss_coverage = sum([x.get_waterfall_coverage(db_session) for x in tss])

        # Test Cases
        tc_query = db_session.query(SwRequirementTestCaseModel).filter(
            SwRequirementTestCaseModel.sw_requirement_mapping_api_id == self.id
        )
        tcs = tc_query.all()
        if len(tcs) > 0:
            tcs_coverage = sum([x.as_dict()['coverage'] for x in tcs])

        if len(tcs) == len(tss) == len(srs) == 0:
            waterfall_coverage = self.coverage
        else:
            waterfall_coverage = (min(max(0, srs_coverage + tss_coverage + tcs_coverage), 100) * self.coverage) / 100.0

        waterfall_coverage = min(max(0, waterfall_coverage), 100)
        return waterfall_coverage


@event.listens_for(ApiSwRequirementModel, "after_update")
def receive_after_update(mapper, connection, target):
    last_query = select(ApiSwRequirementHistoryModel.version).where(
        ApiSwRequirementHistoryModel.id == target.id).order_by(
        ApiSwRequirementHistoryModel.version.desc()).limit(1)
    version = -1
    for row in connection.execute(last_query):
        version = row[0]

    if version > -1:
        insert_query = insert(ApiSwRequirementHistoryModel).values(
            id=target.id,
            api_id=target.api_id,
            sw_requirement_id=target.sw_requirement_id,
            section=target.section,
            offset=target.offset,
            coverage=target.coverage,
            created_by_id=target.created_by_id,
            edited_by_id=target.edited_by_id,
            version=version + 1
        )
        connection.execute(insert_query)


@event.listens_for(ApiSwRequirementModel, "after_insert")
def receive_after_insert(mapper, connection, target):
    insert_query = insert(ApiSwRequirementHistoryModel).values(
        id=target.id,
        api_id=target.api_id,
        sw_requirement_id=target.sw_requirement_id,
        section=target.section,
        offset=target.offset,
        coverage=target.coverage,
        created_by_id=target.created_by_id,
        edited_by_id=target.edited_by_id,
        version=1
    )
    connection.execute(insert_query)


class ApiSwRequirementHistoryModel(Base):
    __tablename__ = 'sw_requirement_mapping_api_history'
    __table_args__ = {"sqlite_autoincrement": True}
    extend_existing = True
    row_id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"),
                                        primary_key=True)
    id: Mapped[int] = mapped_column(Integer())
    api_id: Mapped[int] = mapped_column(Integer())
    sw_requirement_id: Mapped[int] = mapped_column(Integer())
    section: Mapped[str] = mapped_column(String())
    offset: Mapped[int] = mapped_column(Integer())
    coverage: Mapped[int] = mapped_column(Integer())
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_by: Mapped["UserModel"] = relationship("UserModel",
                                                   foreign_keys="ApiSwRequirementHistoryModel.created_by_id")
    edited_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    edited_by: Mapped["UserModel"] = relationship("UserModel",
                                                  foreign_keys="ApiSwRequirementHistoryModel.edited_by_id")
    version: Mapped[int] = mapped_column(Integer())
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    def __init__(self, id, api_id, sw_requirement_id, section,
                 offset, coverage, created_by_id, edited_by_id, version):
        self.id = id
        self.api_id = api_id
        self.sw_requirement_id = sw_requirement_id
        self.section = section
        self.offset = offset
        self.coverage = coverage
        self.created_by_id = created_by_id
        self.edited_by_id = edited_by_id
        self.version = version
        self.created_at = datetime.now()

    def __repr__(self) -> str:
        return f"ApiSwRequirementHistoryModel(row_id={self.row_id!r}, " \
               f"id={self.id!r}, " \
               f"version={self.version!r}, " \
               f"api_id={self.api_id!r}, " \
               f"sw_requirement_id={self.sw_requirement_id!r}, " \
               f"coverage={self.coverage!r}, " \
               f"offset={self.offset!r}, " \
               f"created_by={self.created_by.email!r}, " \
               f"version={self.version!r})"
