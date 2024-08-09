from datetime import datetime
from db.models.api import ApiModel
from db.models.comment import CommentModel
from db.models.db_base import Base
from db.models.document import DocumentModel, DocumentHistoryModel
from db.models.user import UserModel
from sqlalchemy import BigInteger, DateTime, Integer, String
from sqlalchemy import event, insert, select
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column


class ApiDocumentModel(Base):
    __tablename__ = "document_mapping_api"
    __table_args__ = {"sqlite_autoincrement": True}
    extend_existing = True
    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"),
                                    primary_key=True)
    api_id: Mapped[int] = mapped_column(ForeignKey("apis.id"))
    api: Mapped["ApiModel"] = relationship("ApiModel", foreign_keys="ApiDocumentModel.api_id")
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"))
    document: Mapped["DocumentModel"] = relationship("DocumentModel",
                                                     foreign_keys="ApiDocumentModel.document_id")
    section: Mapped[str] = mapped_column(String())
    offset: Mapped[int] = mapped_column(Integer())
    coverage: Mapped[int] = mapped_column(Integer())
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_by: Mapped["UserModel"] = relationship("UserModel",
                                                   foreign_keys="ApiDocumentModel.created_by_id")
    edited_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    edited_by: Mapped["UserModel"] = relationship("UserModel",
                                                  foreign_keys="ApiDocumentModel.edited_by_id")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    def __init__(self, api, document, section, offset, coverage, created_by):
        self.api = api
        self.api_id = api.id
        self.document = document
        self.document_id = document.id
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
        return f"ApiDocumentModel(id={self.id!r}, " \
               f"section={self.section!r}, " \
               f"offset={self.offset!r}, " \
               f"coverage={self.coverage!r}, " \
               f"api_id={self.api_id!r}, " \
               f"created_by={self.created_by.email!r}, " \
               f"document_id={self.document_id!r}) - {str(self.api)!r} " \
               f"- {str(self.document)!r}"

    def current_version(self, db_session):
        last_mapping_query = db_session.query(ApiDocumentHistoryModel).filter(
                        ApiDocumentHistoryModel.id == self.id).order_by(
                        ApiDocumentHistoryModel.version.desc()).limit(1)
        last_mapping = last_mapping_query.all()[0]

        last_item_query = db_session.query(DocumentHistoryModel).filter(
                     DocumentHistoryModel.id == self.document_id).order_by(
                     DocumentHistoryModel.version.desc()).limit(1)

        last_item = last_item_query.all()[0]
        return f'{last_item.version}.{last_mapping.version}'

    def as_dict(self, full_data=False, db_session=None):
        _dict = {'document': self.document.as_dict(full_data=full_data, db_session=db_session),
                 'relation_id': self.id,
                 'section': self.section,
                 'offset': self.offset,
                 'coverage': self.coverage,
                 'covered': self.coverage,
                 'created_by': self.created_by.email}

        _dict['gap'] = _dict['coverage'] - _dict['covered']

        if db_session is not None:
            _dict['version'] = self.current_version(db_session)
            # Comments
            _dict['document']['comment_count'] = len(db_session.query(CommentModel).filter(
                CommentModel.parent_table == self.__tablename__
            ).filter(
                CommentModel.parent_id == self.id
            ).all())

        if full_data:
            _dict['api'] = self.api.as_dict(full_data=full_data, db_session=db_session)
            _dict["created_at"] = self.created_at.strftime(Base.dt_format_str)
            _dict["updated_at"] = self.updated_at.strftime(Base.dt_format_str)
        return _dict


@event.listens_for(ApiDocumentModel, "after_update")
def receive_after_update(mapper, connection, target):
    last_query = select(ApiDocumentHistoryModel.version,
                        ApiDocumentHistoryModel.section,
                        ApiDocumentHistoryModel.offset,
                        ApiDocumentHistoryModel.coverage).where(
                   ApiDocumentHistoryModel.id == target.id).order_by(
                   ApiDocumentHistoryModel.version.desc()).limit(1)
    version = -1
    section = None
    offset = None
    coverage = 0

    for row in connection.execute(last_query):
        version = row[0]
        section = row[1]
        offset = row[2]
        coverage = row[3]

    if version > -1 and (section != target.section or offset != target.offset or coverage != target.coverage):
        insert_query = insert(ApiDocumentHistoryModel).values(
            id=target.id,
            api_id=target.api_id,
            document_id=target.document_id,
            section=target.section,
            offset=target.offset,
            coverage=target.coverage,
            created_by_id=target.created_by_id,
            edited_by_id=target.edited_by_id,
            version=version + 1
        )
        connection.execute(insert_query)


@event.listens_for(ApiDocumentModel, "after_insert")
def receive_after_insert(mapper, connection, target):
    insert_query = insert(ApiDocumentHistoryModel).values(
        id=target.id,
        api_id=target.api_id,
        document_id=target.document_id,
        section=target.section,
        offset=target.offset,
        coverage=target.coverage,
        created_by_id=target.created_by_id,
        edited_by_id=target.edited_by_id,
        version=1
    )
    connection.execute(insert_query)


class ApiDocumentHistoryModel(Base):
    __tablename__ = "document_mapping_api_history"
    __table_args__ = {"sqlite_autoincrement": True}
    extend_existing = True
    row_id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"),
                                        primary_key=True)
    id: Mapped[int] = mapped_column(Integer())
    api_id: Mapped[int] = mapped_column(ForeignKey("apis.id"))
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"))
    section: Mapped[str] = mapped_column(String())
    offset: Mapped[int] = mapped_column(Integer())
    coverage: Mapped[int] = mapped_column(Integer())
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_by: Mapped["UserModel"] = relationship("UserModel",
                                                   foreign_keys="ApiDocumentHistoryModel.created_by_id")
    edited_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    edited_by: Mapped["UserModel"] = relationship("UserModel",
                                                  foreign_keys="ApiDocumentHistoryModel.edited_by_id")
    version: Mapped[int] = mapped_column(Integer())
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    def __init__(self, id, api_id, document_id, section, offset,
                 coverage, created_by_id, edited_by_id, version):
        self.id = id
        self.api_id = api_id
        self.document_id = document_id
        self.section = section
        self.offset = offset
        self.coverage = coverage
        self.created_by_id = created_by_id
        self.edited_by_id = edited_by_id
        self.version = version
        self.created_at = datetime.now()
        self.updated_at = self.created_at

    def __repr__(self) -> str:
        return f"ApiDocumentModel(id={self.id!r}, " \
               f"section={self.section!r}, " \
               f"offset={self.offset!r}, " \
               f"coverage={self.coverage!r}," \
               f"api_id={self.api_id!r}, " \
               f"document_id={self.document_id!r}), " \
               f"created_by={self.created_by.email!r}"

    def as_dict(self, full_data=False):
        _dict = {'id': self.id,
                 'api_id': self.api_id,
                 'document_id': self.document_id,
                 'section': self.section,
                 'offset': self.offset,
                 'coverage': self.coverage,
                 'created_by': self.created_by.email,
                 'version': self.version}
        if full_data:
            _dict["created_at"] = self.created_at
            _dict["updated_at"] = self.updated_at
        return _dict
