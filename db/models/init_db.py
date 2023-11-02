import os
from sqlalchemy import create_engine
import sys

currentdir = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(1, os.path.dirname(os.path.dirname(currentdir)))

from db.models.db_base import Base


def initialization(db_name='basil.db'):

    db_path = os.path.join(currentdir, '..', db_name)
    if db_name == 'test.db':
        if os.path.exists(db_path):
            os.unlink(db_path)
    engine = create_engine(f"sqlite:///{db_path}", echo=True)
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    initialization()
