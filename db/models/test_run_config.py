from datetime import datetime
from db.models.db_base import Base
from db.models.ssh_key import SshKeyModel
from db.models.user import UserModel
from sqlalchemy import DateTime, Integer, String
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from typing import Optional


class TestRunConfigModel(Base):
    __tablename__ = "test_run_configs"
    _description = 'Test Run Configuration'
    extend_existing = True
    id: Mapped[int] = mapped_column(Integer(), primary_key=True, autoincrement=True)
    plugin: Mapped[Optional[str]] = mapped_column(String(20), default='tmt')
    plugin_preset: Mapped[Optional[str]] = mapped_column(String(50), default='')
    plugin_vars: Mapped[Optional[str]] = mapped_column(String(), default='')
    title: Mapped[Optional[str]] = mapped_column(String())
    git_repo_ref: Mapped[str] = mapped_column(String())
    context_vars: Mapped[Optional[str]] = mapped_column(String())
    environment_vars: Mapped[Optional[str]] = mapped_column(String())
    provision_type: Mapped[str] = mapped_column(String(20))
    provision_guest: Mapped[Optional[str]] = mapped_column(String(200))
    provision_guest_port: Mapped[Optional[str]] = mapped_column(String(10))
    ssh_key_id: Mapped[Optional[int]] = mapped_column(ForeignKey("ssh_keys.id", ondelete="CASCADE"))
    ssh_key: Mapped[Optional["UserModel"]] = relationship("SshKeyModel",
                                                          foreign_keys="TestRunConfigModel.ssh_key_id")
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    created_by: Mapped["UserModel"] = relationship("UserModel",
                                                   foreign_keys="TestRunConfigModel.created_by_id")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    def __init__(self, plugin, plugin_preset, plugin_vars, title, git_repo_ref, context_vars, environment_vars,
                 provision_type, provision_guest, provision_guest_port,
                 ssh_key, created_by):
        self.plugin = plugin
        self.plugin_preset = plugin_preset
        self.plugin_vars = plugin_vars
        self.title = title
        self.git_repo_ref = git_repo_ref
        self.context_vars = context_vars
        self.environment_vars = environment_vars
        self.provision_type = provision_type
        self.provision_guest = provision_guest
        self.provision_guest_port = provision_guest_port
        self.ssh_key = ssh_key
        self.created_by = created_by
        self.created_by_id = created_by.id
        self.created_at = datetime.now()
        self.updated_at = self.created_at

    def __repr__(self) -> str:
        tmp = "TestRunConfigModel("
        for field in self.__table__.columns.keys():
            tmp += f"{field}={getattr(self, field)}, "
        tmp += ")"
        return tmp

    def as_dict(self, full_data=False):
        _dict = {'id': self.id,
                 'plugin': self.plugin,
                 'plugin_preset': self.plugin_preset,
                 'plugin_vars': self.plugin_vars,
                 'title': self.title,
                 'git_repo_ref': self.git_repo_ref,
                 'context_vars': self.context_vars,
                 'ssh_key': self.ssh_key_id,
                 'environment_vars': self.environment_vars,
                 'provision_type': self.provision_type,
                 'provision_guest': self.provision_guest,
                 'provision_guest_port': self.provision_guest_port,
                 'created_by': self.created_by.username,
                 }

        if full_data:
            _dict["created_at"] = self.created_at.strftime(Base.dt_format_str)
            _dict["updated_at"] = self.updated_at.strftime(Base.dt_format_str)
        return _dict
