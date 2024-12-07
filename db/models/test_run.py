from datetime import datetime
from db.models.db_base import Base
from db.models.api import ApiModel
from db.models.test_run_config import TestRunConfigModel
from db.models.user import UserModel
from sqlalchemy import BigInteger, DateTime, Integer, String
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from typing import Optional
import uuid


class TestRunModel(Base):
    __tablename__ = "test_runs"
    __table_args__ = {"sqlite_autoincrement": True}
    extend_existing = True
    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"),
                                    primary_key=True)
    uid: Mapped[str] = mapped_column(String())
    title: Mapped[Optional[str]] = mapped_column(String())
    status: Mapped[str] = mapped_column(String(20))
    result: Mapped[Optional[str]] = mapped_column(String(20))
    log: Mapped[Optional[str]] = mapped_column(String())
    bugs: Mapped[Optional[str]] = mapped_column(String())
    fixes: Mapped[Optional[str]] = mapped_column(String())
    notes: Mapped[Optional[str]] = mapped_column(String())
    report: Mapped[Optional[str]] = mapped_column(String(), default='')
    api_id: Mapped[int] = mapped_column(ForeignKey("apis.id"))
    api: Mapped["ApiModel"] = relationship("ApiModel", foreign_keys="TestRunModel.api_id")
    mapping_to: Mapped[str] = mapped_column(String())
    mapping_id: Mapped[int] = mapped_column(Integer())
    test_run_config_id: Mapped[int] = mapped_column(ForeignKey("test_run_configs.id"))
    test_run_config: Mapped["UserModel"] = relationship("TestRunConfigModel",
                                                        foreign_keys="TestRunModel.test_run_config_id")
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_by: Mapped["UserModel"] = relationship("UserModel",
                                                   foreign_keys="TestRunModel.created_by_id")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    def __init__(self, api, title, notes, test_run_config, mapping_to, mapping_id, created_by):
        self.api = api
        self.api_id = api.id
        self.title = title
        self.notes = notes
        self.report = ''
        self.uid = str(uuid.uuid4())
        self.status = 'created'
        self.test_run_config_id = test_run_config.id
        self.test_run_config = test_run_config
        self.mapping_to = mapping_to
        self.mapping_id = mapping_id
        self.created_by = created_by
        self.created_by_id = created_by.id
        self.created_at = datetime.now()
        self.updated_at = self.created_at

    def __repr__(self) -> str:
        tmp = "TestRunModel("
        for field in self.__table__.columns.keys():
            tmp += f"{field}={getattr(self, field)}, "
        tmp += ")"
        return tmp

    def as_dict(self, full_data=False):
        _dict = {'id': self.id,
                 'bugs': self.bugs,
                 'fixes': self.fixes,
                 'config': self.test_run_config.as_dict(),
                 'created_by': self.created_by.email,
                 'log': self.log,
                 'notes': self.notes,
                 'report': self.report,
                 'result': self.result,
                 'title': self.title,
                 'status': self.status,
                 'uid': self.uid,
                 }

        if full_data:
            _dict["created_at"] = self.created_at.strftime(Base.dt_format_str)
            _dict["updated_at"] = self.updated_at.strftime(Base.dt_format_str)
        return _dict
