from db.models.api import *
from db.models.test_specification import *
from db.models.comment import *

class ApiTestSpecificationModel(Base):
    __tablename__ = "test_specification_mapping_api"
    __table_args__ = {"sqlite_autoincrement": True}
    extend_existing = True
    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"),
                                    primary_key=True)
    api_id: Mapped[int] = mapped_column(ForeignKey("apis.id"))
    api: Mapped["ApiModel"] = relationship("ApiModel", foreign_keys="ApiTestSpecificationModel.api_id")
    test_specification_id: Mapped[int] = mapped_column(ForeignKey("test_specifications.id"))
    test_specification: Mapped["TestSpecificationModel"] = relationship("TestSpecificationModel",
                                                                   foreign_keys="ApiTestSpecificationModel.test_specification_id")
    section: Mapped[str] = mapped_column(String())
    offset: Mapped[int] = mapped_column(Integer())
    coverage: Mapped[int] = mapped_column(Integer())
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    def __init__(self, api, test_specification, section, offset, coverage):
        self.api = api
        self.api_id = api.id
        self.test_specification = test_specification
        self.test_specification_id = test_specification.id
        self.section = section
        self.offset = offset
        self.coverage = coverage
        self.created_at = datetime.now()
        self.updated_at = self.created_at
    def __repr__(self) -> str:
        return f"ApiTestSpecificationModel(id={self.id!r}, " \
               f"section={self.section!r}, " \
               f"coverage={self.coverage!r}," \
               f"api_id={self.api_id!r}, " \
               f"offset={self.offset!r}, " \
               f"test_specification_id={self.test_specification_id!r}) - " \
               f"{str(self.api)!r} - " \
               f"{str(self.test_specification)!r}"

    def get_indirect_test_cases(self, db_session):
        from test_specification_test_case import TestSpecificationTestCaseModel
        ts_tc_mapping = []
        ts_tcs = db_session.query(TestSpecificationTestCaseModel).filter(
            TestSpecificationTestCaseModel.test_specification_mapping_api_id == self.id).all()

        for i in range(len(ts_tcs)):
            tmp = ts_tcs[i].as_dict(db_session=db_session)
            tmp['direct-relation-id'] = self.id  # ApiTestSpecification
            tmp['indirect-relation-id'] = tmp['id']  # TestSpecificationTestCaseModel
            tmp['mapped-to'] = "test-specification"
            tmp['direct'] = 0
            tmp['section'] = self.section
            tmp['offset'] = self.offset
            tmp['coverage'] = ((self.coverage / 100) * (ts_tcs[i].coverage / 100)) * 100
            tmp['test_case'] = ts_tcs[i].test_case.as_dict(db_session=db_session)
            ts_tc_mapping += [tmp]
            print("\n\n      ----------------    ")
            print(f"ApiSwRequirementModel.coverage: {self.coverage}")
            print(f"SwRequirementTestCaseModel.coverage: {ts_tcs[i].coverage}")
            print(f"coverage: {tmp['coverage']}")

        print(f'    * ts_tc_mapping: {ts_tc_mapping}')
        return ts_tc_mapping

    def current_version(self, db_session):
        last_mapping = db_session.query(ApiTestSpecificationHistoryModel).filter(
                        ApiTestSpecificationHistoryModel.id == self.id).order_by(
                        ApiTestSpecificationHistoryModel.version.desc()).limit(1).all()[0]

        last_item = db_session.query(TestSpecificationHistoryModel).filter(
                     TestSpecificationHistoryModel.id == self.test_specification_id).order_by(
                     TestSpecificationHistoryModel.version.desc()).limit(1).all()[0]

        return f'{last_item.version}.{last_mapping.version}'

    def as_dict(self, full_data=False, db_session=None):
        _dict = {'test_specification': self.test_specification.as_dict(full_data=full_data, db_session=db_session),
                 'relation_id': self.id,
                 'section': self.section,
                 'offset': self.offset,
                 'coverage': self.get_waterfall_coverage(db_session)}

        if db_session:
            _dict['version'] = self.current_version(db_session)
            # Comments
            _dict['test_specification']['comment_count'] = len(db_session.query(CommentModel).filter(
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
        if db_session == None:
            return self.coverage

        from db.models.test_specification_test_case import TestSpecificationTestCaseModel
        tcs_coverage = 0

        # Test Cases
        tc_query = db_session.query(TestSpecificationTestCaseModel).filter(
            TestSpecificationTestCaseModel.test_specification_mapping_api_id == self.id
        )
        tcs = tc_query.all()
        if len(tcs) > 0:
            tcs_coverage = sum([x.as_dict()['coverage'] for x in tcs])
        else:
            tcs_coverage = 100


        waterfall_coverage = (min(max(0, tcs_coverage), 100) * self.coverage) / 100.0
        waterfall_coverage = min(max(0, waterfall_coverage), 100)
        print(f'tcs_coverage: {tcs_coverage}')
        print(f'waterfall_coverage: {waterfall_coverage}')
        print(f'self.coverage: {self.coverage}')
        return waterfall_coverage

@event.listens_for(ApiTestSpecificationModel, "after_update")
def receive_after_update(mapper, connection, target):
    last_query = select(ApiTestSpecificationHistoryModel.version).where( \
        ApiTestSpecificationHistoryModel.id == target.id).order_by( \
        ApiTestSpecificationHistoryModel.version.desc()).limit(1)
    version = -1
    for row in connection.execute(last_query):
        version = row[0]

    if version > -1:
        insert_query = insert(ApiTestSpecificationHistoryModel).values(
            id=target.id,
            api_id=target.api_id,
            test_specification_id=target.test_specification_id,
            section=target.section,
            offset=target.offset,
            coverage=target.coverage,
            version=version + 1
        )
        connection.execute(insert_query)

@event.listens_for(ApiTestSpecificationModel, "after_insert")
def receive_after_insert(mapper, connection, target):
    insert_query = insert(ApiTestSpecificationHistoryModel).values(
        id=target.id,
        api_id=target.api_id,
        test_specification_id=target.test_specification_id,
        section=target.section,
        offset=target.offset,
        coverage=target.coverage,
        version=1
    )
    connection.execute(insert_query)


class ApiTestSpecificationHistoryModel(Base):
    __tablename__ = 'test_specification_mapping_api_history'
    __table_args__ = {"sqlite_autoincrement": True}
    extend_existing = True
    row_id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"),
                                        primary_key=True)
    id: Mapped[int] = mapped_column(Integer())
    api_id: Mapped[int] = mapped_column(Integer())
    test_specification_id: Mapped[int] = mapped_column(Integer())
    section: Mapped[str] = mapped_column(String())
    offset: Mapped[str] = mapped_column(String())
    coverage: Mapped[int] = mapped_column(Integer())
    version: Mapped[int] = mapped_column(Integer())
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    def __init__(self, id, api_id, test_specification_id, section, offset, coverage, version):
        self.id = id
        self.api_id = api_id
        self.test_specification_id = test_specification_id
        self.section = section
        self.offset = offset
        self.coverage = coverage
        self.version = version
        self.created_at = datetime.now()

    def __repr__(self) -> str:
        return f"ApiTestSpecificationHistoryModel(row_id={self.row_id!r}, " \
               f"id={self.id!r}, " \
               f"version={self.version!r}, " \
               f"api_id={self.api_id!r}, " \
               f"test_specification_id={self.test_specification_id!r}, " \
               f"coverage={self.coverage!r}, " \
               f"offset={self.offset!r}, " \
               f"version={self.version!r})"
