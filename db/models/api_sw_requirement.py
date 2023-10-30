from db.models.api import *
from db.models.sw_requirement import *
from db.models.sw_requirement_test_case import *
from db.models.sw_requirement_test_specification import *
from db.models.comment import *
from db.models.db_base import Base

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
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    def __init__(self, api, sw_requirement, section, offset, coverage):
        self.api = api
        self.api_id = api.id
        self.sw_requirement = sw_requirement
        self.sw_requirement_id = sw_requirement.id
        self.section = section
        self.offset = offset
        self.coverage = coverage
        self.created_at = datetime.now()
        self.updated_at = self.created_at
    def __repr__(self) -> str:
        return f"ApiSwRequirementModel(id={self.id!r}, section={self.section!r}, " \
               f"offset={self.offset!r}, coverage={self.coverage!r}," \
               f"api_id={self.api_id!r}, sw_requirement_id={self.sw_requirement_id!r}) - {str(self.api)!r} " \
               f"- {str(self.sw_requirement)!r}"

    def get_indirect_test_cases(self, db_session):
        sr_tc_mapping = []
        sr_tcs = db_session.query(SwRequirementTestCaseModel).filter(
                SwRequirementTestCaseModel.sw_requirement_mapping_api_id == self.id).all()

        for i in range(len(sr_tcs)):
            tmp = sr_tcs[i].as_dict(db_session=db_session)
            tmp['direct-relation-id'] = self.id #ApiSwRequirementModel
            tmp['indirect-relation-id'] = tmp['id'] #SwRequirementTestCaseModel
            tmp['mapped-to'] = "sw-requirement"
            tmp['direct'] = 0
            tmp['section'] = self.section
            tmp['offset'] = self.offset
            tmp['coverage'] = ((self.coverage/100) * (sr_tcs[i].coverage / 100)) * 100
            tmp['test_case'] = sr_tcs[i].test_case.as_dict(db_session=db_session)
            sr_tc_mapping += [tmp]
            print("\n\n      ----------------    ")
            print(f"ApiSwRequirementModel.coverage: {self.coverage}")
            print(f"SwRequirementTestCaseModel.coverage: {sr_tcs[i].coverage}")
            print(f"coverage: {tmp['coverage']}")

        print(f'    * sr_tc_mapping: {sr_tc_mapping}')
        return sr_tc_mapping

    def get_indirect_test_specifications(self, db_session):
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
                 'coverage': self.get_waterfall_coverage(db_session)}

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
        #Return Api-SR waterfall coverage

        if db_session == None:
            return self.coverage

        tss_coverage = 0
        tcs_coverage = 0
        #Test Specifications
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

        if len(tcs) == len(tss) == 0:
            waterfall_coverage = self.coverage
        else:
            waterfall_coverage = (min(max(0, tss_coverage + tcs_coverage), 100) * self.coverage) / 100.0

        waterfall_coverage = min(max(0, waterfall_coverage), 100)
        return waterfall_coverage

@event.listens_for(ApiSwRequirementModel, "after_update")
def receive_after_update(mapper, connection, target):
    last_query = select(ApiSwRequirementHistoryModel.version).where(ApiSwRequirementHistoryModel.id == target.id).order_by(ApiSwRequirementHistoryModel.version.desc()).limit(1)
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
    version: Mapped[int] = mapped_column(Integer())
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    def __init__(self, id, api_id, sw_requirement_id, section, offset, coverage, version):
        self.id = id
        self.api_id = api_id
        self.sw_requirement_id = sw_requirement_id
        self.section = section
        self.offset = offset
        self.coverage = coverage
        self.version = version
        self.created_at = datetime.now()

    def __repr__(self) -> str:
        return f"ApiSwRequirementHistoryModel(row_id={self.row_id!r}, id={self.id!r}, version={self.version!r}, " \
               f"api_id={self.api_id!r}, sw_requirement_id={self.sw_requirement_id!r}, " \
               f"coverage={self.coverage!r}, offset={self.offset!r}, version={self.version!r})"
