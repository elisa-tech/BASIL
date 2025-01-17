import os
from sqlalchemy import create_engine
import sys

currentdir = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(1, os.path.dirname(os.path.dirname(currentdir)))

from db import db_orm
from db.models.db_base import Base
from db.models.api import ApiModel, ApiHistoryModel
from db.models.api_document import ApiDocumentModel, ApiDocumentHistoryModel
from db.models.api_justification import ApiJustificationModel, ApiJustificationHistoryModel
from db.models.api_sw_requirement import ApiSwRequirementModel, ApiSwRequirementHistoryModel
from db.models.api_test_case import ApiTestCaseModel, ApiTestCaseHistoryModel
from db.models.api_test_specification import ApiTestSpecificationModel, ApiTestSpecificationHistoryModel
from db.models.comment import CommentModel
from db.models.document import DocumentModel, DocumentHistoryModel
from db.models.justification import JustificationModel, JustificationHistoryModel
from db.models.note import NoteModel
from db.models.notification import NotificationModel
from db.models.ssh_key import SshKeyModel
from db.models.sw_requirement_sw_requirement import SwRequirementSwRequirementModel
from db.models.sw_requirement_sw_requirement import SwRequirementSwRequirementHistoryModel
from db.models.sw_requirement_test_case import SwRequirementTestCaseModel
from db.models.sw_requirement_test_case import SwRequirementTestCaseHistoryModel
from db.models.sw_requirement_test_specification import SwRequirementTestSpecificationModel
from db.models.sw_requirement_test_specification import SwRequirementTestSpecificationHistoryModel
from db.models.sw_requirement import SwRequirementModel, SwRequirementHistoryModel
from db.models.test_case import TestCaseModel, TestCaseHistoryModel
from db.models.test_run_config import TestRunConfigModel
from db.models.test_run import TestRunModel
from db.models.test_specification_test_case import TestSpecificationTestCaseModel
from db.models.test_specification_test_case import TestSpecificationTestCaseHistoryModel
from db.models.test_specification import TestSpecificationModel, TestSpecificationHistoryModel
from db.models.user import UserModel


def initialization(db_name='basil.db'):

    db_path = os.path.join(currentdir, '..', db_name)
    if db_name == 'test.db':
        if os.path.exists(db_path):
            os.unlink(db_path)

    dbi = db_orm.DbInterface(db_name)
    Base.metadata.create_all(bind=dbi.engine)

    if os.getenv('BASIL_ADMIN_PASSWORD', '') != '':
        admin_count = dbi.session.query(UserModel).filter(
            UserModel.email == "admin").filter(
            UserModel.role == 'ADMIN'
        ).count()
        if not admin_count:
            admin = UserModel("admin", os.getenv('BASIL_ADMIN_PASSWORD'), 'ADMIN')
            dbi.session.add(admin)
        del os.environ['BASIL_ADMIN_PASSWORD']

    if db_name == 'test.db':
        guest = UserModel("dummy_guest", "dummy_guest", "GUEST")
        dbi.session.add(guest)
        test_user = UserModel("dummy_user", "dummy_user", "USER")
        dbi.session.add(test_user)

    dbi.session.commit()


if __name__ == "__main__":
    initialization()
