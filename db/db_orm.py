import logging
import os
import psycopg2

from sqlalchemy import create_engine
from sqlalchemy.engine.url import make_url
from sqlalchemy.orm import scoped_session, sessionmaker

logger = logging.getLogger(__name__)


class DbInterface():

    DB_TYPE = "postgresql"
    DB_USER = "basil-admin"
    DB_PORT = os.environ.get("BASIL_DB_PORT", 5432)
    DB_PASSWORD = os.environ.get("BASIL_DB_PASSWORD", "")
    DB_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@localhost:{DB_PORT}"

    def __init__(self, db_name="basil"):
        try:
            self.DB_URL = f"{self.DB_URL}/{db_name}"
            self.ensure_database_exists()
            self.engine = create_engine(self.DB_URL, echo=False, pool_pre_ping=True)
            Session = scoped_session(sessionmaker(bind=self.engine))
            self.session = Session()
        except Exception as e:
            logger.error(f"Unable to connect to the database: {db_name}\n{e}")

    def __del__(self):
        if hasattr(self, 'session') and self.session:
            try:
                self.close()
            except Exception as e:
                logger.warning(f"Error closing session in __del__: {e}")

    def close(self):
        try:
            self.session.close()
        except Exception as e:
            logging.error(f"Error closing session: {e}")
        try:
            self.engine.dispose()
        except Exception as e:
            logging.error(f"Error disposing engine: {e}")

    def ensure_database_exists(self):
        url = make_url(self.DB_URL)
        db_name = url.database
        url = url.set(database="postgres")  # Connect to default postgres DB
        conn = psycopg2.connect(
            dbname=url.database,
            user=url.username,
            password=url.password,
            host=url.host,
            port=url.port
        )
        conn.autocommit = True

        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
            exists = cur.fetchone()
            if not exists:
                logger.info(f"✅ Database created: {db_name}")
                cur.execute(f'CREATE DATABASE "{db_name}"')

        conn.close()
