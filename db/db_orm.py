import os.path

from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

class DbInterface():

    engine = None
    session = None

    def __init__(self, db_name="basil.db"):
        currentdir = os.path.dirname(os.path.realpath(__file__))
        self.engine = create_engine(f"sqlite:///{currentdir}/{db_name}", echo=True)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
