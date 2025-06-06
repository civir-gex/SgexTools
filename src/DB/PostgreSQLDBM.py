import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from BaseDBM import BaseDBManager
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from src import LoggerFactory

logger = LoggerFactory().get_logger("db", "db.log", consola=True)

load_dotenv("../../.env")

class PostgreSQLDBManager(BaseDBManager):
    def __init__(self, db_name, **kwargs):
        self.user = kwargs.get("user", os.getenv("PG_USER"))
        self.password = kwargs.get("password", os.getenv("PG_PASSWORD"))
        self.host = kwargs.get("host", os.getenv("PG_HOST", "localhost"))
        self.port = int(kwargs.get("port", os.getenv("PG_PORT", 5432)))
        self.database = db_name
        uri = self._build_uri()
        super().__init__(uri)

    def _build_uri(self):
        return f"postgresql+psycopg2://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"

    def _check_or_create_database(self):
        try:
            root_uri = f"postgresql+psycopg2://{self.user}:{self.password}@{self.host}:{self.port}/postgres"
            temp_engine = create_engine(root_uri)
            with temp_engine.connect() as conn:
                conn.execution_options(isolation_level="AUTOCOMMIT").execute(
                    f"CREATE DATABASE {self.database} WITH ENCODING 'UTF8'"
                )
            logger.info(f"Base de datos '{self.database}' creada.")
            return True
        except Exception as e:
            if "already exists" in str(e):
                logger.warning(f"Base de datos '{self.database}' ya existe.")
                return True
            logger.error(f"ERROR al verificar o crear base PostgreSQL: {e}")
            return False
