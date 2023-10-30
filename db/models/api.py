from datetime import datetime
from typing import List
from typing import Optional

from sqlalchemy import *
from sqlalchemy import event

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

from db.models.db_base import Base

class ApiModel(Base):
    __tablename__ = "apis"
    __table_args__ = {"sqlite_autoincrement": True}
    extend_existing = True
    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"),
                                    primary_key=True)
    api: Mapped[str] = mapped_column(String(100))
    library: Mapped[str] = mapped_column(String(100))
    category: Mapped[str] = mapped_column(String(100))
    library_version: Mapped[str] = mapped_column(String())
    implementation_file: Mapped[Optional[str]] = mapped_column(String())
    implementation_file_from_row: Mapped[Optional[int]] = mapped_column(Integer())
    implementation_file_to_row: Mapped[Optional[int]] = mapped_column(Integer())
    raw_specification_url: Mapped[str] = mapped_column(String())
    tags: Mapped[str] = mapped_column(String())
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    def __init__(self, api, library, library_version, raw_specification_url, \
                 category, implementation_file, \
                 implementation_file_from_row, implementation_file_to_row, tags):
        self.api = api
        self.library = library
        self.library_version = library_version
        self.raw_specification_url = raw_specification_url
        self.category = category
        self.implementation_file = implementation_file
        self.implementation_file_from_row = implementation_file_from_row
        self.implementation_file_to_row = implementation_file_to_row
        self.tags = tags
        self.created_at = datetime.now()
        self.updated_at = self.created_at

    def __repr__(self) -> str:
        return f"Api(id={self.id!r}, " \
               f"api={self.api!r}, " \
               f"library={self.library!r}, " \
               f"library_version={self.library_version!r}, " \
               f"raw_specification_url={self.raw_specification_url!r}, " \
               f"category={self.category!r}, " \
               f"implementation_file={self.implementation_file!r}, " \
               f"implementation_file_from_row={self.implementation_file_from_row!r}, " \
               f"implementation_file_to_row={self.implementation_file_to_row!r}," \
               f"tags={self.tags!r})"

    def current_version(self, db_session):
        last_item = db_session.query(ApiHistoryModel).filter(
            ApiHistoryModel.id == self.id).order_by(
            ApiHistoryModel.version.desc()).limit(1).all()[0]

        return f'{last_item.version}'

    def as_dict(self, full_data=False, db_session=None):
        _dict = {"id": self.id,
                 "api": self.api,
                 "library": self.library,
                 "library_version": self.library_version,
                 "raw_specification_url": self.raw_specification_url,
                 "category": self.category,
                 "implementation_file": self.implementation_file,
                 "implementation_file_from_row": self.implementation_file_from_row,
                 "implementation_file_to_row": self.implementation_file_to_row,
                 "tags": self.tags}

        if db_session is not None:
            from db.models.api_sw_requirement import ApiSwRequirementModel
            from db.models.api_test_specification import ApiTestSpecificationModel
            from db.models.api_test_case import ApiTestCaseModel

            _dict['version'] = self.current_version(db_session)
            #Calc coverage
            srs_query = db_session.query(ApiSwRequirementModel).filter(
                ApiSwRequirementModel.api_id == self.id
            )
            srs = srs_query.all()
            srs_cov = sum([x.get_waterfall_coverage(db_session) for x in srs])
            print(f'srs_cov: {srs_cov}')

            tss_query = db_session.query(ApiTestSpecificationModel).filter(
                ApiTestSpecificationModel.api_id == self.id
            )
            tss = tss_query.all()
            tss_cov = sum([x.get_waterfall_coverage(db_session) for x in tss])
            print(f'tss_cov: {tss_cov}')

            tcs_query = db_session.query(ApiTestCaseModel).filter(
                ApiTestCaseModel.api_id == self.id
            )
            tcs = tcs_query.all()
            tcs_cov = sum([x.as_dict()['coverage'] for x in tcs])
            print(f'tcs_cov: {tcs_cov}')

            coverage = srs_cov + tss_cov + tcs_cov
            print(f'coverage: {coverage}')
            _dict['coverage'] = coverage

        if full_data:
            _dict["created_at"] = self.created_at.strftime(Base.dt_format_str)
            _dict["updated_at"] = self.updated_at.strftime(Base.dt_format_str)
        return _dict

@event.listens_for(ApiModel, "after_update")
def receive_after_update(mapper, connection, target):
    last_query = select(ApiHistoryModel.version).where(ApiHistoryModel.id == target.id).order_by(ApiHistoryModel.version.desc()).limit(1)
    version = -1
    for row in connection.execute(last_query):
        version = row[0]

    if version > -1:
        insert_query = insert(ApiHistoryModel).values(
            id=target.id,
            api=target.api,
            library=target.library,
            library_version=target.library_version,
            raw_specification_url=target.raw_specification_url,
            category=target.category,
            implementation_file=target.implementation_file,
            implementation_file_from_row=target.implementation_file_from_row,
            implementation_file_to_row=target.implementation_file_to_row,
            tags=target.tags,
            version=version + 1
        )
        connection.execute(insert_query)

@event.listens_for(ApiModel, "after_insert")
def receive_after_insert(mapper, connection, target):
    insert_query = insert(ApiHistoryModel).values(
        id=target.id,
        api=target.api,
        library=target.library,
        library_version=target.library_version,
        raw_specification_url=target.raw_specification_url,
        category=target.category,
        implementation_file=target.implementation_file,
        implementation_file_from_row=target.implementation_file_from_row,
        implementation_file_to_row=target.implementation_file_to_row,
        tags=target.tags,
        version=1
    )
    connection.execute(insert_query)

class ApiHistoryModel(Base):
    __tablename__ = "apis_history"
    __table_args__ = {"sqlite_autoincrement": True}
    extend_existing = True
    row_id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"),
                                    primary_key=True)
    id: Mapped[int] = mapped_column(Integer())
    api: Mapped[str] = mapped_column(String(100))
    library: Mapped[str] = mapped_column(String(100))
    category: Mapped[str] = mapped_column(String(100))
    library_version: Mapped[str] = mapped_column(String())
    implementation_file: Mapped[Optional[str]] = mapped_column(String())
    implementation_file_from_row: Mapped[Optional[int]] = mapped_column(Integer())
    implementation_file_to_row: Mapped[Optional[int]] = mapped_column(Integer())
    raw_specification_url: Mapped[str] = mapped_column(String())
    tags: Mapped[str] = mapped_column(String())
    version: Mapped[int] = mapped_column(Integer())
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)


    def __init__(self, id, api, library, library_version, raw_specification_url, \
                 category, implementation_file, \
                 implementation_file_from_row, implementation_file_to_row, tags,
                 version):
        self.id = id
        self.api = api
        self.library = library
        self.library_version = library_version
        self.raw_specification_url = raw_specification_url
        self.category = category
        self.implementation_file = implementation_file
        self.implementation_file_from_row = implementation_file_from_row
        self.implementation_file_to_row = implementation_file_to_row
        self.tags = tags
        self.version = version
        self.created_at = datetime.now()
        self.updated_at = self.created_at

    def __repr__(self) -> str:
        return f"ApiHistory(id={self.id!r}, " \
               f"api={self.api!r}, " \
               f"library={self.library!r}, " \
               f"library_version={self.library_version!r}, " \
               f"raw_specification_url={self.raw_specification_url!r}, " \
               f"category={self.category!r}, " \
               f"implementation_file={self.implementation_file!r}, " \
               f"implementation_file_from_row={self.implementation_file_from_row!r}, " \
               f"implementation_file_to_row={self.implementation_file_to_row!r}," \
               f"tags={self.tags!r}, " \
               f"version={self.version!r})"
