import os, sys
from sqlalchemy import create_engine

currentdir = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(1, os.path.dirname(os.path.dirname(currentdir)))

from db.models.db_base import Base
from db.models.api import *
from db.models.api_justification import *
from db.models.api_sw_requirement import *
from db.models.api_test_case import *
from db.models.api_test_specification import *
from db.models.comment import *
from db.models.justification import *
from db.models.note import *
from db.models.sw_requirement import *
from db.models.sw_requirement_test_case import *
from db.models.sw_requirement_test_specification import *
from db.models.test_case import *
from db.models.test_specification import *
from db.models.test_specification_test_case import *

def initialization(db_name='basil.db'):

    db_path = os.path.join(currentdir, '..', db_name)
    if db_name == 'test.db':
        if os.path.exists(db_path):
            os.unlink(db_path)
    engine = create_engine(f"sqlite:///{db_path}", echo=True)
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    initialization()
