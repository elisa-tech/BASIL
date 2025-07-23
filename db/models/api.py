from datetime import datetime
from db.models.db_base import Base
from db.models.user import UserModel
from sqlalchemy import BigInteger, DateTime, Integer, String
from sqlalchemy import event, insert, inspect, select
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from typing import Optional


class ApiModel(Base):
    __tablename__ = "apis"
    __table_args__ = {"sqlite_autoincrement": True}
    _description = "Software Component"
    extend_existing = True
    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"),
                                    primary_key=True)
    api: Mapped[str] = mapped_column(String(100))
    library: Mapped[str] = mapped_column(String(100))
    category: Mapped[str] = mapped_column(String(100))
    default_view: Mapped[Optional[str]] = mapped_column(String(30))
    checksum: Mapped[Optional[str]] = mapped_column(String(100))
    library_version: Mapped[str] = mapped_column(String())
    implementation_file: Mapped[Optional[str]] = mapped_column(String())
    implementation_file_from_row: Mapped[Optional[int]] = mapped_column(Integer())
    implementation_file_to_row: Mapped[Optional[int]] = mapped_column(Integer())
    raw_specification_url: Mapped[str] = mapped_column(String())
    tags: Mapped[str] = mapped_column(String())
    last_coverage: Mapped[str] = mapped_column(String(10))
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_by: Mapped["UserModel"] = relationship("UserModel",
                                                   foreign_keys="ApiModel.created_by_id")
    edited_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    edited_by: Mapped["UserModel"] = relationship("UserModel",
                                                  foreign_keys="ApiModel.edited_by_id")
    delete_permissions: Mapped[str] = mapped_column(String())
    edit_permissions: Mapped[str] = mapped_column(String())
    manage_permissions: Mapped[str] = mapped_column(String())
    read_denials: Mapped[str] = mapped_column(String())
    write_permissions: Mapped[str] = mapped_column(String())
    write_permission_requests: Mapped[str] = mapped_column(String())
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    def __init__(self, api, library, library_version, raw_specification_url,
                 category, checksum, implementation_file,
                 implementation_file_from_row, implementation_file_to_row, tags,
                 created_by):
        self.api = api
        self.library = library
        self.library_version = library_version
        self.raw_specification_url = raw_specification_url
        self.category = category
        self.checksum = checksum
        self.implementation_file = implementation_file
        self.implementation_file_from_row = implementation_file_from_row
        self.implementation_file_to_row = implementation_file_to_row
        self.tags = tags
        self.created_by = created_by
        self.created_by_id = created_by.id
        self.edited_by = created_by
        self.edited_by_id = created_by.id
        self.delete_permissions = f"{[created_by.id]}"
        self.edit_permissions = f"{[created_by.id]}"
        self.manage_permissions = f"{[created_by.id]}"
        self.read_denials = ""
        self.write_permissions = f"{[created_by.id]}"
        self.write_permission_requests = ""
        self.last_coverage = "0"
        self.created_at = datetime.now()
        self.updated_at = self.created_at

    def __repr__(self) -> str:
        return f"Api(id={self.id!r}, " \
               f"api={self.api!r}, " \
               f"library={self.library!r}, " \
               f"library_version={self.library_version!r}, " \
               f"raw_specification_url={self.raw_specification_url!r}, " \
               f"category={self.category!r}, " \
               f"checksum={self.checksum!r}, " \
               f"default_view={self.default_view!r}, " \
               f"implementation_file={self.implementation_file!r}, " \
               f"implementation_file_from_row={self.implementation_file_from_row!r}, " \
               f"implementation_file_to_row={self.implementation_file_to_row!r}," \
               f"created_by={self.created_by.username!r}," \
               f"edited_by={self.edited_by.username!r}," \
               f"last_coverage={self.last_coverage!r}," \
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
                 "checksum": self.checksum,
                 "default_view": self.default_view,
                 "implementation_file": self.implementation_file,
                 "implementation_file_from_row": self.implementation_file_from_row,
                 "implementation_file_to_row": self.implementation_file_to_row,
                 "created_by": self.created_by.username,
                 "edited_by": self.edited_by.username,
                 "last_coverage": self.last_coverage,
                 "tags": self.tags}

        if db_session is not None:
            from db.models.api_sw_requirement import ApiSwRequirementModel
            from db.models.api_test_specification import ApiTestSpecificationModel
            from db.models.api_test_case import ApiTestCaseModel

            _dict['version'] = self.current_version(db_session)
            # Calc coverage
            srs_query = db_session.query(ApiSwRequirementModel).filter(
                ApiSwRequirementModel.api_id == self.id
            )
            srs = srs_query.all()
            srs_cov = sum([x.get_waterfall_coverage(db_session) for x in srs])

            tss_query = db_session.query(ApiTestSpecificationModel).filter(
                ApiTestSpecificationModel.api_id == self.id
            )
            tss = tss_query.all()
            tss_cov = sum([x.get_waterfall_coverage(db_session) for x in tss])

            tcs_query = db_session.query(ApiTestCaseModel).filter(
                ApiTestCaseModel.api_id == self.id
            )
            tcs = tcs_query.all()
            tcs_cov = sum([x.as_dict()['coverage'] for x in tcs])

            _dict['srs_coverage'] = srs_cov
            _dict['tss_coverage'] = tss_cov
            _dict['tcs_coverage'] = tcs_cov

        if full_data:
            _dict["created_at"] = self.created_at.strftime(Base.dt_format_str)
            _dict["updated_at"] = self.updated_at.strftime(Base.dt_format_str)
        return _dict


@event.listens_for(ApiModel, "after_update")
def receive_after_update(mapper, connection, target):
    # Avoid to update the version if the only change is related to last_coverage
    state = inspect(target)
    changes = {}
    for attr in state.attrs:
        hist = state.get_history(attr.key, True)
        old_value = hist.deleted[0] if hist.deleted else None
        new_value = hist.added[0] if hist.added else None
        if old_value is not None or new_value is not None:
            if old_value != new_value:
                changes[attr.key] = [old_value, new_value]
        affected_fields = list(changes.keys())
        if len(affected_fields) == 1:
            if affected_fields[0] == 'last_coverage':
                return

    last_query = select(ApiHistoryModel.version).where(ApiHistoryModel.id ==
                                                       target.id).order_by(ApiHistoryModel.version.desc()).limit(1)
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
            checksum=target.checksum,
            default_view=target.default_view,
            implementation_file=target.implementation_file,
            implementation_file_from_row=target.implementation_file_from_row,
            implementation_file_to_row=target.implementation_file_to_row,
            tags=target.tags,
            created_by_id=target.created_by_id,
            edited_by_id=target.edited_by_id,
            delete_permissions=target.delete_permissions,
            edit_permissions=target.edit_permissions,
            manage_permissions=target.manage_permissions,
            read_denials=target.read_denials,
            write_permissions=target.write_permissions,
            write_permission_requests=target.write_permission_requests,
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
        checksum=target.checksum,
        default_view=target.default_view,
        implementation_file=target.implementation_file,
        implementation_file_from_row=target.implementation_file_from_row,
        implementation_file_to_row=target.implementation_file_to_row,
        tags=target.tags,
        created_by_id=target.created_by_id,
        edited_by_id=target.edited_by_id,
        delete_permissions=target.delete_permissions,
        edit_permissions=target.edit_permissions,
        manage_permissions=target.manage_permissions,
        read_denials=target.read_denials,
        write_permissions=target.write_permissions,
        write_permission_requests=target.write_permission_requests,
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
    checksum: Mapped[Optional[str]] = mapped_column(String(100))
    default_view: Mapped[Optional[str]] = mapped_column(String(30))
    library_version: Mapped[str] = mapped_column(String())
    implementation_file: Mapped[Optional[str]] = mapped_column(String())
    implementation_file_from_row: Mapped[Optional[int]] = mapped_column(Integer())
    implementation_file_to_row: Mapped[Optional[int]] = mapped_column(Integer())
    raw_specification_url: Mapped[str] = mapped_column(String())
    tags: Mapped[str] = mapped_column(String())
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_by: Mapped["UserModel"] = relationship("UserModel",
                                                   foreign_keys="ApiHistoryModel.created_by_id")
    edited_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    edited_by: Mapped["UserModel"] = relationship("UserModel",
                                                  foreign_keys="ApiHistoryModel.edited_by_id")
    delete_permissions: Mapped[str] = mapped_column(String())
    edit_permissions: Mapped[str] = mapped_column(String())
    manage_permissions: Mapped[str] = mapped_column(String())
    read_denials: Mapped[str] = mapped_column(String())
    write_permissions: Mapped[str] = mapped_column(String())
    write_permission_requests: Mapped[str] = mapped_column(String())
    version: Mapped[int] = mapped_column(Integer())
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    def __init__(self, id, api, library, library_version, raw_specification_url,
                 category, checksum, default_view, implementation_file,
                 implementation_file_from_row, implementation_file_to_row, tags,
                 created_by_id, edited_by_id, delete_permissions, edit_permissions,
                 manage_permissions, read_denials, write_permissions, write_permission_requests, version):
        self.id = id
        self.api = api
        self.library = library
        self.library_version = library_version
        self.raw_specification_url = raw_specification_url
        self.category = category
        self.checksum = checksum
        self.default_view = default_view
        self.implementation_file = implementation_file
        self.implementation_file_from_row = implementation_file_from_row
        self.implementation_file_to_row = implementation_file_to_row
        self.tags = tags
        self.created_by_id = created_by_id
        self.edited_by_id = edited_by_id
        self.delete_permissions = delete_permissions
        self.edit_permissions = edit_permissions
        self.manage_permissions = manage_permissions
        self.read_denials = read_denials
        self.write_permissions = write_permissions
        self.write_permission_requests = write_permission_requests
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
               f"checksum={self.checksum!r}, " \
               f"default_view={self.default_view!r}, " \
               f"implementation_file={self.implementation_file!r}, " \
               f"implementation_file_from_row={self.implementation_file_from_row!r}, " \
               f"implementation_file_to_row={self.implementation_file_to_row!r}," \
               f"edited_by_id={self.edited_by_id!r}, " \
               f"tags={self.tags!r}, " \
               f"version={self.version!r})"
