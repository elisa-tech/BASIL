from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

class DbInterface():

    engine = None
    session = None

    def __init__(self, db_path="db/basil.db"):
        self.engine = create_engine(f"sqlite:///{db_path}", echo=True)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

