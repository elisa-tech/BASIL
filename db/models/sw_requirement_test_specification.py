from api_sw_requirement import *
from test_specification import *

class SwRequirementTestSpecificationModel(Base):
    __tablename__ = "test_specification_mapping_sw_requirement"
    __table_args__ = {"sqlite_autoincrement": True}
    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"),
                                    primary_key=True)
    sw_requirement_mapping_api: Mapped["ApiSwRequirementModel"] = relationship("ApiSwRequirementModel", foreign_keys="SwRequirementTestSpecificationModel.sw_requirement_mapping_api_id")
    sw_requirement_mapping_api_id : Mapped[int] = mapped_column(ForeignKey("sw_requirement_mapping_api.id"))
    test_specification_id: Mapped[int] = mapped_column(ForeignKey("test_specifications.id"))
    test_specification: Mapped["TestSpecificationModel"] = relationship("TestSpecificationModel", foreign_keys="SwRequirementTestSpecificationModel.test_specification_id")
    coverage: Mapped[int] = mapped_column(Integer())
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    def __init__(self, sw_requirement_mapping_api, test_specification, coverage):
        self.test_specification = test_specification
        self.test_specification_id = test_specification.id
        self.sw_requirement_mapping_api = sw_requirement_mapping_api
        self.sw_requirement_mapping_api_id = sw_requirement_mapping_api.id
        self.coverage = coverage
        self.created_at = datetime.now()
        self.updated_at = self.created_at

    def __repr__(self) -> str:
        return f"SwRequirementTestSpecificationModel(id={self.id!r}, " \
               f"test_specification_id={self.test_specification_id!r}, " \
               f"sw_requirement_mapping_api_id={self.sw_requirement_mapping_api_id!r}, " \
               f"coverage={self.coverage!r})"

    def current_version(self, db_session):
        last_mapping = db_session.query(SwRequirementTestSpecificationHistoryModel).filter(
            SwRequirementTestSpecificationHistoryModel.id == self.id).order_by(
            SwRequirementTestSpecificationHistoryModel.version.desc()).limit(1).all()[0]
        last_item = db_session.query(TestSpecificationHistoryModel).filter(
            TestSpecificationHistoryModel.id == self.test_specification_id).order_by(
            TestSpecificationHistoryModel.version.desc()).limit(1).all()[0]
        return f'{last_item.version}.{last_mapping.version}'

    def as_dict(self, full_data=False, db_session=None):
        _dict = {'relation_id': self.id,
                 'sw_requirement_mapping_api': self.sw_requirement_mapping_api.as_dict(),
                 'sw_requirement_mapping_api_id': self.sw_requirement_mapping_api_id,
                 'api': {'id': self.sw_requirement_mapping_api.api_id},
                 'sw_requirement': {'id': self.sw_requirement_mapping_api.sw_requirement_id},
                 'coverage': self.get_waterfall_coverage(db_session)}

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
            ts = db_session.query(TestSpecificationModel).filter( \
                TestSpecificationModel.id == self.test_specification_id).one()
            return ts.as_dict()
        except:
            return None

    def get_waterfall_coverage(self, db_session):
        if db_session == None:
            return self.coverage

        from test_specification_test_case import TestSpecificationTestCaseModel
        #Calc children(TestSpecificationTestCase) coverage
        #filtering with test_specification_mapping_sw_requirement_id
        #Return self.coverage * Sum(childrend coverage)

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
    last_query = select(SwRequirementTestSpecificationHistoryModel.version).where( \
        SwRequirementTestSpecificationHistoryModel.id == target.id).order_by( \
        SwRequirementTestSpecificationHistoryModel.version.desc()).limit(1)
    version = -1
    for row in connection.execute(last_query):
        version = row[0]

    if version > -1:
        insert_query = insert(SwRequirementTestSpecificationHistoryModel).values(
            id=target.id,
            sw_requirement_mapping_api_id=target.sw_requirement_mapping_api_id,
            test_specification_id=target.test_specification_id,
            coverage=target.coverage,
            version=version + 1
        )
        connection.execute(insert_query)

@event.listens_for(SwRequirementTestSpecificationModel, "after_insert")
def receive_after_insert(mapper, connection, target):
    insert_query = insert(SwRequirementTestSpecificationHistoryModel).values(
        id=target.id,
        sw_requirement_mapping_api_id=target.sw_requirement_mapping_api_id,
        test_specification_id=target.test_specification_id,
        coverage=target.coverage,
        version=1
    )
    connection.execute(insert_query)


class SwRequirementTestSpecificationHistoryModel(Base):
    __tablename__ = 'test_specification_mapping_sw_requirement_history'
    __table_args__ = {"sqlite_autoincrement": True}
    row_id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"),
                                        primary_key=True)
    id: Mapped[int] = mapped_column(Integer())
    sw_requirement_mapping_api_id: Mapped[int] = mapped_column(Integer())
    test_specification_id: Mapped[int] = mapped_column(Integer())
    coverage: Mapped[int] = mapped_column(Integer())
    version: Mapped[int] = mapped_column(Integer())
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    def __init__(self, id, sw_requirement_mapping_api_id, test_specification_id, coverage, version):
        self.id = id
        self.sw_requirement_mapping_api_id = sw_requirement_mapping_api_id
        self.test_specification_id = test_specification_id
        self.coverage = coverage
        self.version = version
        self.created_at = datetime.now()

    def __repr__(self) -> str:
        return f"SwRequirementTestSpecificationHistoryModel(row_id={self.row_id!r}, " \
               f"id={self.id!r}, " \
               f"version={self.version!r}, " \
               f"test_specification_id={self.test_specification_id!r}, " \
               f"sw_requirement_mapping_api_id={self.sw_requirement_mapping_api_id!r}, " \
               f"coverage={self.coverage!r}, " \
               f"version={self.version!r})"