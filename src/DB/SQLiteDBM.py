import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from BaseDBM import BaseDBManager
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from src import LoggerFactory

logger = LoggerFactory().get_logger("db", "db.log", consola=True)

load_dotenv("../../.env")

class SQLiteDBManager(BaseDBManager):
    def __init__(self, file_path="db.sqlite", **kwargs):
        self.file_path = kwargs.get("file_path", file_path)
        uri = f"sqlite:///{self.file_path}"
        super().__init__(uri)

    def _check_or_create_database(self):
        # SQLite crea la base al conectar si no existe
        return True
