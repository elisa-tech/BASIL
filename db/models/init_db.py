import os
from sqlalchemy import create_engine
import sys

currentdir = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(1, os.path.dirname(os.path.dirname(currentdir)))

from db.models.db_base import Base
from db.models.api import ApiModel, ApiHistoryModel
from db.models.api_justification import ApiJustificationModel, ApiJustificationHistoryModel
from db.models.api_sw_requirement import ApiSwRequirementModel, ApiSwRequirementHistoryModel
from db.models.api_test_case import ApiTestCaseModel, ApiTestCaseHistoryModel
from db.models.api_test_specification import ApiTestSpecificationModel, ApiTestSpecificationHistoryModel
from db.models.comment import CommentModel
from db.models.justification import JustificationModel, JustificationHistoryModel
from db.models.note import NoteModel
from db.models.sw_requirement_sw_requirement import SwRequirementSwRequirementModel
from db.models.sw_requirement_sw_requirement import SwRequirementSwRequirementHistoryModel
from db.models.sw_requirement_test_case import SwRequirementTestCaseModel
from db.models.sw_requirement_test_case import SwRequirementTestCaseHistoryModel
from db.models.sw_requirement_test_specification import SwRequirementTestSpecificationModel
from db.models.sw_requirement_test_specification import SwRequirementTestSpecificationHistoryModel
from db.models.sw_requirement import SwRequirementModel, SwRequirementHistoryModel
from db.models.test_case import TestCaseModel, TestCaseHistoryModel
from db.models.test_specification_test_case import TestSpecificationTestCaseModel
from db.models.test_specification_test_case import TestSpecificationTestCaseHistoryModel
from db.models.test_specification import TestSpecificationModel, TestSpecificationHistoryModel


def initialization(db_name='basil.db'):

    db_path = os.path.join(currentdir, '..', db_name)
    if db_name == 'test.db':
        if os.path.exists(db_path):
            os.unlink(db_path)
    engine = create_engine(f"sqlite:///{db_path}", echo=True)
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    initialization()
