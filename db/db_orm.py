import os

from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine


class DbInterface():

    DB_TYPE = "sqlite3"

    def __init__(self, db_name="basil.db"):
        currentdir = os.path.dirname(os.path.realpath(__file__))
        if not os.path.exists(os.path.join(currentdir, self.DB_TYPE)):
            os.mkdir(os.path.join(currentdir, self.DB_TYPE))
        self.engine = create_engine(f"sqlite:///{currentdir}/{self.DB_TYPE}/{db_name}", echo=False)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
