from datetime import datetime
from db.models.api import ApiModel
from db.models.comment import CommentModel
from db.models.db_base import Base
from db.models.justification import JustificationModel, JustificationHistoryModel
from sqlalchemy import BigInteger, DateTime, Integer, String
from sqlalchemy import event, insert, select
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column


class ApiJustificationModel(Base):
    __tablename__ = "justification_mapping_api"
    __table_args__ = {"sqlite_autoincrement": True}
    extend_existing = True
    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"),
                                    primary_key=True)
    api_id: Mapped[int] = mapped_column(ForeignKey("apis.id"))
    api: Mapped["ApiModel"] = relationship("ApiModel", foreign_keys="ApiJustificationModel.api_id")
    justification_id: Mapped[int] = mapped_column(ForeignKey("justifications.id"))
    justification: Mapped["JustificationModel"] = relationship("JustificationModel",
                                                               foreign_keys="ApiJustificationModel.justification_id")
    section: Mapped[str] = mapped_column(String())
    offset: Mapped[int] = mapped_column(Integer())
    coverage: Mapped[int] = mapped_column(Integer())
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    def __init__(self, api, justification, section, offset, coverage):
        self.api = api
        self.api_id = api.id
        self.justification = justification
        self.justification_id = justification.id
        self.section = section
        self.offset = offset
        self.coverage = coverage
        self.created_at = datetime.now()
        self.updated_at = self.created_at

    def __repr__(self) -> str:
        return f"ApiJustificationModel(id={self.id!r}, section={self.section!r}, " \
               f"offset={self.offset!r}, coverage={self.coverage!r}, " \
               f"api_id={self.api_id!r}, justification_id={self.justification_id!r}) - {str(self.api)!r} " \
               f"- {str(self.justification)!r}"

    def current_version(self, db_session):
        last_mapping_query = db_session.query(ApiJustificationHistoryModel).filter(
                        ApiJustificationHistoryModel.id == self.id).order_by(
                        ApiJustificationHistoryModel.version.desc()).limit(1)
        last_mapping = last_mapping_query.all()[0]

        last_item_query = db_session.query(JustificationHistoryModel).filter(
                     JustificationHistoryModel.id == self.justification_id).order_by(
                     JustificationHistoryModel.version.desc()).limit(1)

        last_item = last_item_query.all()[0]
        return f'{last_item.version}.{last_mapping.version}'

    def as_dict(self, full_data=False, db_session=None):
        _dict = {'justification': self.justification.as_dict(full_data=full_data, db_session=db_session),
                 'relation_id': self.id,
                 'section': self.section,
                 'offset': self.offset,
                 'coverage': self.coverage}

        if db_session is not None:
            _dict['version'] = self.current_version(db_session)
            # Comments
            _dict['justification']['comment_count'] = len(db_session.query(CommentModel).filter(
                CommentModel.parent_table == self.__tablename__
            ).filter(
                CommentModel.parent_id == self.id
            ).all())

        if full_data:
            _dict['api'] = self.api.as_dict(full_data=full_data, db_session=db_session)
            _dict["created_at"] = self.created_at.strftime(Base.dt_format_str)
            _dict["updated_at"] = self.updated_at.strftime(Base.dt_format_str)
        return _dict


@event.listens_for(ApiJustificationModel, "after_update")
def receive_after_update(mapper, connection, target):
    last_query = select(ApiJustificationHistoryModel.version,
                        ApiJustificationHistoryModel.section,
                        ApiJustificationHistoryModel.offset,
                        ApiJustificationHistoryModel.coverage).where(
                   ApiJustificationHistoryModel.id == target.id).order_by(
                   ApiJustificationHistoryModel.version.desc()).limit(1)
    version = -1
    section = None
    offset = None
    coverage = 0

    for row in connection.execute(last_query):
        print(f"row: {row}")
        version = row[0]
        section = row[1]
        offset = row[2]
        coverage = row[3]

    if version > -1 and (section != target.section or offset != target.offset or coverage != target.coverage):
        insert_query = insert(ApiJustificationHistoryModel).values(
            id=target.id,
            api_id=target.api_id,
            justification_id=target.justification_id,
            section=target.section,
            offset=target.offset,
            coverage=target.coverage,
            version=version + 1
        )
        connection.execute(insert_query)


@event.listens_for(ApiJustificationModel, "after_insert")
def receive_after_insert(mapper, connection, target):
    insert_query = insert(ApiJustificationHistoryModel).values(
        id=target.id,
        api_id=target.api_id,
        justification_id=target.justification_id,
        section=target.section,
        offset=target.offset,
        coverage=target.coverage,
        version=1
    )
    connection.execute(insert_query)


class ApiJustificationHistoryModel(Base):
    __tablename__ = "justification_mapping_api_history"
    __table_args__ = {"sqlite_autoincrement": True}
    extend_existing = True
    row_id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"),
                                        primary_key=True)
    id: Mapped[int] = mapped_column(Integer())
    api_id: Mapped[int] = mapped_column(ForeignKey("apis.id"))
    justification_id: Mapped[int] = mapped_column(ForeignKey("justifications.id"))
    section: Mapped[str] = mapped_column(String())
    offset: Mapped[int] = mapped_column(Integer())
    coverage: Mapped[int] = mapped_column(Integer())
    version: Mapped[int] = mapped_column(Integer())
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    def __init__(self, id, api_id, justification_id, section, offset, coverage, version):
        self.id = id
        self.api_id = api_id
        self.justification_id = justification_id
        self.section = section
        self.offset = offset
        self.coverage = coverage
        self.version = version
        self.created_at = datetime.now()
        self.updated_at = self.created_at

    def __repr__(self) -> str:
        return f"ApiJustificationModel(id={self.id!r}, section={self.section!r}, " \
               f"offset={self.offset!r}, coverage={self.coverage!r}," \
               f"api_id={self.api_id!r}, justification_id={self.justification_id!r})"

    def as_dict(self, full_data=False):
        _dict = {'id': self.id,
                 'api_id': self.api_id,
                 'justification_id': self.justification_id,
                 'section': self.section,
                 'offset': self.offset,
                 'coverage': self.coverage,
                 'version': self.version}
        if full_data:
            _dict["created_at"] = self.created_at
            _dict["updated_at"] = self.updated_at
        return _dict
