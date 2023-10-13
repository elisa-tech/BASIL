from db_base import Base
from sqlalchemy import create_engine

from api import *
from api_justification import *
from api_sw_requirement import *
from api_test_case import *
from api_test_specification import *
from comment import *
from justification import *
from note import *
from sw_requirement import *
from sw_requirement_test_case import *
from sw_requirement_test_specification import *
from test_case import *
from test_specification import *
from test_specification_test_case import *

if __name__ == "__main__":
    db_path = "../basil.db"
    engine = create_engine(f"sqlite:///{db_path}", echo=True)
    Base.metadata.create_all(bind=engine)