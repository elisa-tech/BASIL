from datetime import datetime
from db.models.db_base import Base
from db.models.user import UserModel
from sqlalchemy import BigInteger, DateTime, Integer, String
from sqlalchemy import event, insert, select
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from typing import Optional


class DocumentModel(Base):
    __tablename__ = 'documents'
    __table_args__ = {"sqlite_autoincrement": True}
    _description = 'Document'
    extend_existing = True
    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"),
                                    primary_key=True)
    title: Mapped[Optional[str]] = mapped_column(String(200))
    description: Mapped[Optional[str]] = mapped_column(String())
    document_type: Mapped[Optional[str]] = mapped_column(String(), default="file")
    spdx_relation: Mapped[Optional[str]] = mapped_column(String(200))
    url: Mapped[Optional[str]] = mapped_column(String())
    section: Mapped[str] = mapped_column(String(), default="")
    offset: Mapped[int] = mapped_column(Integer(), default=-1)
    valid: Mapped[int] = mapped_column(Integer(), default=-1)
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_by: Mapped["UserModel"] = relationship("UserModel",
                                                   foreign_keys="DocumentModel.created_by_id")
    edited_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    edited_by: Mapped["UserModel"] = relationship("UserModel",
                                                  foreign_keys="DocumentModel.edited_by_id")
    status: Mapped[str] = mapped_column(String(30))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    def __init__(self, title, description, document_type, spdx_relation, url, section, offset, valid, created_by):
        self.title = title
        self.description = description
        self.document_type = document_type
        self.spdx_relation = spdx_relation
        self.url = url
        self.section = section
        self.offset = offset
        self.valid = valid
        self.created_by = created_by
        self.created_by_id = created_by.id
        self.edited_by = created_by
        self.edited_by_id = created_by.id
        self.status = Base.STATUS_NEW
        self.created_at = datetime.now()
        self.updated_at = self.created_at

    def __repr__(self) -> str:
        tmp = "DocumentModel("
        for field in self.__table__.columns.keys():
            tmp += f"{field}={getattr(self, field)}, "
        tmp += ")"
        return tmp

    def current_version(self, db_session):
        last_item = db_session.query(DocumentHistoryModel).filter(
                     DocumentHistoryModel.id == self.id).order_by(
                     DocumentHistoryModel.version.desc()).limit(1).all()[0]
        return f'{last_item.version}'

    def as_dict(self, full_data=False, db_session=None):
        _dict = {"id": self.id,
                 "title": self.title,
                 "document_type": self.document_type,
                 "description": self.description,
                 "spdx_relation": self.spdx_relation,
                 "url": self.url,
                 "offset": self.offset,
                 "section": self.section,
                 "status": self.status,
                 "valid": self.valid,
                 "created_by": self.created_by.email,
                 }

        if db_session:
            _dict['version'] = self.current_version(db_session)

        if full_data:
            _dict["created_at"] = self.created_at.strftime(Base.dt_format_str)
            _dict["updated_at"] = self.updated_at.strftime(Base.dt_format_str)
        return _dict


@event.listens_for(DocumentModel, "after_update")
def receive_after_update(mapper, connection, target):
    last_query = select(DocumentHistoryModel.version,
                        DocumentHistoryModel.description).where(
        DocumentHistoryModel.id == target.id).order_by(
        DocumentHistoryModel.version.desc()).limit(1)
    version = -1
    for row in connection.execute(last_query):
        version = row[0]

    if version > -1:
        insert_query = insert(DocumentHistoryModel).values(
            id=target.id,
            title=target.title,
            description=target.description,
            document_type=target.document_type,
            spdx_relation=target.spdx_relation,
            url=target.url,
            section=target.section,
            offset=target.offset,
            valid=target.valid,
            created_by_id=target.created_by_id,
            edited_by_id=target.edited_by_id,
            status=target.status,
            version=version + 1
        )
        connection.execute(insert_query)


@event.listens_for(DocumentModel, "after_insert")
def receive_after_insert(mapper, connection, target):
    insert_query = insert(DocumentHistoryModel).values(
        id=target.id,
        title=target.title,
        description=target.description,
        document_type=target.document_type,
        spdx_relation=target.spdx_relation,
        url=target.url,
        section=target.section,
        offset=target.offset,
        valid=target.valid,
        created_by_id=target.created_by_id,
        edited_by_id=target.edited_by_id,
        status=target.status,
        version=1
    )
    connection.execute(insert_query)


class DocumentHistoryModel(Base):
    __tablename__ = 'documents_history'
    __table_args__ = {"sqlite_autoincrement": True}
    extend_existing = True
    row_id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"),
                                        primary_key=True)
    id: Mapped[int] = mapped_column(Integer())
    title: Mapped[Optional[str]] = mapped_column(String(200))
    description: Mapped[Optional[str]] = mapped_column(String())
    document_type: Mapped[Optional[str]] = mapped_column(String())
    spdx_relation: Mapped[Optional[str]] = mapped_column(String(200))
    url: Mapped[Optional[str]] = mapped_column(String())
    section: Mapped[str] = mapped_column(String())
    offset: Mapped[int] = mapped_column(Integer())
    valid: Mapped[int] = mapped_column(Integer())
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_by: Mapped["UserModel"] = relationship("UserModel",
                                                   foreign_keys="DocumentHistoryModel.created_by_id")
    edited_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    edited_by: Mapped["UserModel"] = relationship("UserModel",
                                                  foreign_keys="DocumentHistoryModel.edited_by_id")
    status: Mapped[str] = mapped_column(String(30))
    version: Mapped[int] = mapped_column(Integer())
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    def __init__(self, id, title, description, document_type, spdx_relation, url, section, offset,
                 valid, created_by_id, edited_by_id, status, version):
        self.id = id
        self.title = title
        self.description = description
        self.document_type = document_type
        self.spdx_relation = spdx_relation
        self.url = url
        self.section = section
        self.offset = offset
        self.valid = valid
        self.created_by_id = created_by_id
        self.edited_by_id = edited_by_id
        self.status = status
        self.version = version
        self.created_at = datetime.now()

    def __repr__(self) -> str:
        tmp = "DocumentHistoryModel("
        for field in self.__table__.columns.keys():
            tmp += f"{field}={getattr(self, field)}, "
        tmp += ")"
        return tmp
