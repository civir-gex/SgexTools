import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from BaseDBM import BaseDBManager
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from src import LoggerFactory

logger = LoggerFactory().get_logger("db", "db.log", consola=True)

load_dotenv("../../.env")

class MySQLDBManager(BaseDBManager):
    def __init__(self, db_name, **kwargs):
        self.user = kwargs.get("user", os.getenv("MYSQL_USER"))
        self.password = kwargs.get("password", os.getenv("MYSQL_PASSWORD"))
        self.host = kwargs.get("host", os.getenv("MYSQL_HOST", "localhost"))
        self.port = int(kwargs.get("port", os.getenv("MYSQL_PORT", 3306)))
        self.database = db_name
        uri = self._build_uri()
        super().__init__(uri)

    def _build_uri(self):
        return f"mysql+pymysql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"

    def _check_or_create_database(self):
        try:
            root_uri = f"mysql+pymysql://{self.user}:{self.password}@{self.host}:{self.port}/"
            temp_engine = create_engine(root_uri)
            with temp_engine.connect() as conn:
                conn.execute(f"CREATE DATABASE IF NOT EXISTS {self.database}")
            logger.info(f"Base de datos '{self.database}' verificada o creada.")
            return True
        except Exception as e:
            logger.error(f"ERROR al verificar o crear base MySQL: {e}")
            return False

