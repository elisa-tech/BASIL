from datetime import datetime
from db.models.api_document import ApiDocumentModel
from db.models.comment import CommentModel
from db.models.db_base import Base
from db.models.document import DocumentModel, DocumentHistoryModel
from db.models.user import UserModel
from sqlalchemy import DateTime, Integer, String
from sqlalchemy import delete, event, insert, select
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from typing import Optional


class DocumentDocumentModel(Base):
    __tablename__ = "document_mapping_document"
    extend_existing = True
    id: Mapped[int] = mapped_column(Integer(), primary_key=True, autoincrement=True)
    document_mapping_api: Mapped[Optional["ApiDocumentModel"]] = relationship(
        "ApiDocumentModel", foreign_keys="DocumentDocumentModel.document_mapping_api_id")
    document_mapping_api_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("document_mapping_api.id", ondelete="CASCADE"), nullable=True)
    document_mapping_document_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("document_mapping_document.id", ondelete="CASCADE"), nullable=True)
    document_mapping_document: Mapped[Optional["DocumentDocumentModel"]] = relationship(
        "DocumentDocumentModel",
        foreign_keys="DocumentDocumentModel.document_mapping_document_id",
        remote_side=[id],
        passive_deletes=True
    )
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"))
    document: Mapped["DocumentModel"] = relationship("DocumentModel",
                                                     foreign_keys="DocumentDocumentModel.document_id")
    section: Mapped[str] = mapped_column(String())
    offset: Mapped[int] = mapped_column(Integer())
    coverage: Mapped[int] = mapped_column(Integer())
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    created_by: Mapped["UserModel"] = relationship("UserModel",
                                                   foreign_keys="DocumentDocumentModel.created_by_id")
    edited_by_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    edited_by: Mapped["UserModel"] = relationship("UserModel",
                                                  foreign_keys="DocumentDocumentModel.edited_by_id")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    def __init__(self, document_mapping_document, document_mapping_api, document,
                 section, offset, coverage, created_by):
        if document_mapping_api:
            self.document_mapping_api = document_mapping_api
            self.document_mapping_api_id = document_mapping_api.id
        if document_mapping_document:
            self.document_mapping_document = document_mapping_document
            self.document_mapping_document_id = document_mapping_document.id

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
        tmp = "DocumentDocumentModel("
        for field in self.__table__.columns.keys():
            tmp += f"{field}={getattr(self, field)}, "
        tmp += ")"
        return tmp

    def get_parent_document(self):
        if self.document_mapping_api_id:
            return self.document_mapping_api.document
        if self.document_mapping_document_id:
            return self.document_mapping_document.document
        return None

    def current_version(self, db_session):
        last_mapping = db_session.query(DocumentDocumentHistoryModel).filter(
            DocumentDocumentHistoryModel.id == self.id).order_by(
            DocumentDocumentHistoryModel.version.desc()).limit(1).all()[0]
        last_item = db_session.query(DocumentHistoryModel).filter(
            DocumentHistoryModel.id == self.document_id).order_by(
            DocumentHistoryModel.version.desc()).limit(1).all()[0]
        return f'{last_item.version}.{last_mapping.version}'

    def as_dict(self, full_data=False, db_session=None):
        _dict = {'relation_id': self.id,
                 'document_mapping_api_id': self.document_mapping_api_id,
                 'document_mapping_document_id': self.document_mapping_document_id,
                 'coverage': self.coverage,
                 'covered': self.get_waterfall_coverage(db_session),
                 'created_by': self.created_by.username,
                 '__tablename__': self.__tablename__}

        _dict['gap'] = min(max(0, _dict['coverage'] - _dict['covered']), 100)

        if self.document_mapping_api_id:
            _dict['api'] = {'id': self.document_mapping_api.api_id}
            _dict['direct_document'] = {'id': self.document_mapping_api.document.id}
        elif self.document_mapping_document_id:
            _dict['indirect_document'] = {
                'id': self.document_mapping_document.get_parent_document().id}
            _dict['direct_document'] = {'id': self.document_mapping_document.document.id}

        if db_session is not None:
            _dict['version'] = self.current_version(db_session)
            _dict['document'] = self.document.as_dict(full_data=full_data, db_session=db_session)
            # Comments
            _dict['document']['comment_count'] = len(db_session.query(CommentModel).filter(
                CommentModel.parent_table == self.__tablename__
            ).filter(
                CommentModel.parent_id == self.id
            ).all())
        else:
            _dict['document'] = {'id': self.document_id}

        if full_data:
            _dict["created_at"] = self.created_at.strftime(Base.dt_format_str)
            _dict["updated_at"] = self.updated_at.strftime(Base.dt_format_str)
        return _dict

    def get_waterfall_coverage(self, db_session, _visited=None):
        # Return Document-Document waterfall coverage
        if db_session is None:
            return self.coverage
        # Cycle protection in case of unexpected document cycles
        if _visited is None:
            _visited = set()
        if self.id in _visited:
            return 0
        _visited.add(self.id)

        docs_coverage = 0

        # Documents
        docs = db_session.query(DocumentDocumentModel).filter(
            DocumentDocumentModel.document_mapping_document_id == self.id
        ).all()
        if len(docs) > 0:
            docs_coverage = sum([x.get_waterfall_coverage(db_session, _visited) for x in docs])
            waterfall_coverage = (min(max(0, docs_coverage), 100) * self.coverage) / 100.0
        else:
            waterfall_coverage = self.coverage

        waterfall_coverage = min(max(0, waterfall_coverage), 100)
        return waterfall_coverage

    def fork(self, new_document_mapping_document=None, new_document_mapping_api=None, db_session=None):
        new_document_document = DocumentDocumentModel(
            document_mapping_document=new_document_mapping_document,
            document_mapping_api=new_document_mapping_api,
            document=self.document,
            section=self.section,
            offset=self.offset,
            coverage=self.coverage,
            created_by=self.created_by
        )
        db_session.add(new_document_document)

        doc_docs = db_session.query(DocumentDocumentModel).filter(
            DocumentDocumentModel.document_mapping_document_id == self.id
        ).all()
        for doc_doc in doc_docs:
            doc_doc.fork(
                new_document_mapping_document=new_document_document,
                new_document_mapping_api=None,
                db_session=db_session
            )
        db_session.commit()
        return new_document_document


@event.listens_for(DocumentDocumentModel, "after_update")
def receive_after_update(mapper, connection, target):
    last_query = select(DocumentDocumentHistoryModel.version).where(
                   DocumentDocumentHistoryModel.id == target.id).order_by(
                   DocumentDocumentHistoryModel.version.desc()).limit(1)
    version = -1

    for row in connection.execute(last_query):
        version = row[0]

    if version > -1:
        insert_query = insert(DocumentDocumentHistoryModel).values(
            id=target.id,
            document_mapping_api_id=target.document_mapping_api_id,
            document_mapping_document_id=target.document_mapping_document_id,
            document_id=target.document_id,
            section=target.section,
            offset=target.offset,
            coverage=target.coverage,
            created_by_id=target.created_by_id,
            edited_by_id=target.edited_by_id,
            version=version + 1
        )
        connection.execute(insert_query)


@event.listens_for(DocumentDocumentModel, "after_insert")
def receive_after_insert(mapper, connection, target):
    insert_query = insert(DocumentDocumentHistoryModel).values(
        id=target.id,
        document_mapping_api_id=target.document_mapping_api_id,
        document_mapping_document_id=target.document_mapping_document_id,
        document_id=target.document_id,
        section=target.section,
        offset=target.offset,
        coverage=target.coverage,
        created_by_id=target.created_by_id,
        edited_by_id=target.edited_by_id,
        version=1
    )
    connection.execute(insert_query)


@event.listens_for(DocumentDocumentModel, "before_delete")
def receive_before_delete(mapper, connection, target):
    # Purge history rows for this mapping id
    del_stmt = delete(DocumentDocumentHistoryModel).where(DocumentDocumentHistoryModel.id == target.id)
    connection.execute(del_stmt)


class DocumentDocumentHistoryModel(Base):
    __tablename__ = "document_mapping_document_history"
    extend_existing = True
    row_id: Mapped[int] = mapped_column(Integer(), primary_key=True, autoincrement=True)
    id: Mapped[int] = mapped_column(Integer())
    document_mapping_api_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("document_mapping_api.id", ondelete="CASCADE"), nullable=True
    )
    document_mapping_document_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("document_mapping_document.id", ondelete="CASCADE"), nullable=True
    )
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"))
    section: Mapped[str] = mapped_column(String())
    offset: Mapped[int] = mapped_column(Integer())
    coverage: Mapped[int] = mapped_column(Integer())
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    created_by: Mapped["UserModel"] = relationship("UserModel",
                                                   foreign_keys="DocumentDocumentHistoryModel.created_by_id")
    edited_by_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    edited_by: Mapped["UserModel"] = relationship("UserModel",
                                                  foreign_keys="DocumentDocumentHistoryModel.edited_by_id")
    version: Mapped[int] = mapped_column(Integer())
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    def __init__(self, id, document_mapping_api_id, document_mapping_document_id, document_id, section, offset,
                 coverage, created_by_id, edited_by_id, version):
        self.id = id
        self.document_mapping_api_id = document_mapping_api_id
        self.document_mapping_document_id = document_mapping_document_id
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
        return f"DocumentDocumentModel(id={self.id!r}, " \
               f"section={self.section!r}, " \
               f"offset={self.offset!r}, " \
               f"coverage={self.coverage!r}," \
               f"document_mapping_api_id={self.document_mapping_api_id!r}, " \
               f"document_mapping_document_id={self.document_mapping_document_id!r}, " \
               f"document_id={self.document_id!r}), " \
               f"created_by={self.created_by.username!r})"

    def as_dict(self, full_data=False):
        _dict = {'id': self.id,
                 'document_mapping_api_id': self.document_mapping_api_id,
                 'document_mapping_document_id': self.document_mapping_document_id,
                 'document_id': self.document_id,
                 'section': self.section,
                 'offset': self.offset,
                 'coverage': self.coverage,
                 'created_by': self.created_by.username,
                 'version': self.version}
        if full_data:
            _dict["created_at"] = self.created_at
            _dict["updated_at"] = self.updated_at
        return _dict
