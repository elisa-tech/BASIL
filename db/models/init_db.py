import logging
import os
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

logger = logging.getLogger(__name__)


def initialization(db_name='basil'):
    logger.info(f"Database initialization: {db_name}")

    dbi = db_orm.DbInterface(db_name)

    try:
        if db_name == 'test':
            logger.info("Drop all tables")
            Base.metadata.drop_all(bind=dbi.engine)

        logger.info("Creating all the tables")
        Base.metadata.create_all(bind=dbi.engine)
    except Exception as e:
        logger.error(f"Unable to run database create_all\n{e}")

    admin_pwd = os.getenv('BASIL_ADMIN_PASSWORD', 'admin')

    admin_count = dbi.session.query(UserModel).filter(
        UserModel.email == "admin").filter(
        UserModel.role == 'ADMIN'
    ).count()
    if not admin_count:
        logger.info("No admin users, creating the default one")
        admin = UserModel("admin", "admin", admin_pwd, 'ADMIN')
        dbi.session.add(admin)

    if db_name != 'test':
        if 'BASIL_ADMIN_PASSWORD' in os.environ:
            del os.environ['BASIL_ADMIN_PASSWORD']
    else:
        logger.info("Creating dummy_guest user with GUEST role")
        guest = UserModel("dummy_guest", "dummy_guest", "dummy_guest", "GUEST")
        dbi.session.add(guest)
        logger.info("Creating dummy_user user with USER role")
        test_user = UserModel("dummy_user", "dummy_user", "dummy_user", "USER")
        dbi.session.add(test_user)

    dbi.session.commit()


if __name__ == "__main__":
    initialization()
