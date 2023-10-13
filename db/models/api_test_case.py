from api import *
from test_case import *
from comment import *

class ApiTestCaseModel(Base):
    __tablename__ = "test_case_mapping_api"
    __table_args__ = {"sqlite_autoincrement": True}
    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"),
                                    primary_key=True)
    api_id: Mapped[int] = mapped_column(ForeignKey("apis.id"))
    api: Mapped["ApiModel"] = relationship("ApiModel", foreign_keys="ApiTestCaseModel.api_id")
    test_case_id: Mapped[int] = mapped_column(ForeignKey("test_cases.id"))
    test_case: Mapped["TestCaseModel"] = relationship("TestCaseModel", foreign_keys="ApiTestCaseModel.test_case_id")
    section: Mapped[str] = mapped_column(String())
    offset: Mapped[int] = mapped_column(Integer())
    coverage: Mapped[int] = mapped_column(Integer())
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    def __init__(self, api, test_case, section, offset, coverage):
        self.api = api
        self.api_id = api.id
        self.test_case = test_case
        self.test_case_id = test_case.id
        self.section = section
        self.offset = offset
        self.coverage = coverage
        self.created_at = datetime.now()
        self.updated_at = self.created_at

    def __repr__(self) -> str:
        return f"ApiTestCaseModel(id={self.id!r}, api_id={self.api_id!r}, test_case_id={self.test_case_id!r}, " \
               f"section={self.section!r}, coverage={self.coverage!r}), offset={self.offset!r})  - " \
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
                 'coverage': self.coverage}

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

@event.listens_for(ApiTestCaseModel, "after_update")
def receive_after_update(mapper, connection, target):
    last_query = select(ApiTestCaseHistoryModel.version).where( \
        ApiTestCaseHistoryModel.id == target.id).order_by( \
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
        version=1
    )
    connection.execute(insert_query)


class ApiTestCaseHistoryModel(Base):
    __tablename__ = 'test_case_mapping_api_history'
    __table_args__ = {"sqlite_autoincrement": True}
    row_id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"),
                                        primary_key=True)
    id: Mapped[int] = mapped_column(Integer())
    api_id: Mapped[int] = mapped_column(Integer())
    test_case_id: Mapped[int] = mapped_column(Integer())
    section: Mapped[str] = mapped_column(String())
    offset: Mapped[int] = mapped_column(Integer())
    coverage: Mapped[int] = mapped_column(Integer())
    version: Mapped[int] = mapped_column(Integer())
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    def __init__(self, id, api_id, test_case_id, section, offset, coverage, version):
        self.id = id
        self.api_id = api_id
        self.test_case_id = test_case_id
        self.section = section
        self.offset = offset
        self.coverage = coverage
        self.version = version
        self.created_at = datetime.now()

    def __repr__(self) -> str:
        return f"ApiTestCaseHistoryModel(row_id={self.row_id!r}, id={self.id!r}, version={self.version!r}, " \
               f"api_id={self.api_id!r}, test_case_id={self.test_case_id!r}, " \
               f"coverage={self.coverage!r}, offset={self.offset!r}, version={self.version!r})"