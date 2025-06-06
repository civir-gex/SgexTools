import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from BaseDBM import BaseDBManager
import urllib
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from src import LoggerFactory

logger = LoggerFactory().get_logger("db", "db.log", consola=True)

load_dotenv("../../.env")

class MSSQLDBManager(BaseDBManager):
    def __init__(self, db_name, **kwargs):
        self.server = kwargs.get("server", os.getenv("dbServer"))
        self.port = int(kwargs.get("port", os.getenv("dbPuerto", 1433)))
        self.user = kwargs.get("user", os.getenv("dbUser"))
        self.password = kwargs.get("password", os.getenv("dbPasswd"))
        self.database = db_name
        uri = self._build_uri()
        super().__init__(uri)

    def _build_uri(self):
        connection_string = (
            f"DRIVER={{ODBC Driver 18 for SQL Server}};"
            f"SERVER={self.server},{self.port};"
            f"DATABASE={self.database};"
            f"UID={self.user};"
            f"PWD={self.password};"
            "Encrypt=yes;"
            "TrustServerCertificate=yes;"
            "Connection Timeout=30;"
        )
        return f"mssql+pyodbc:///?odbc_connect={urllib.parse.quote_plus(connection_string)}"

    def _check_or_create_database(self):
        try:
            connection_string = (
                f"DRIVER={{ODBC Driver 18 for SQL Server}};"
                f"SERVER={self.server},{self.port};"
                f"DATABASE=master;"
                f"UID={self.user};"
                f"PWD={self.password};"
                "Encrypt=yes;"
                "TrustServerCertificate=yes;"
                "Connection Timeout=30;"
            )
            master_uri = f"mssql+pyodbc:///?odbc_connect={urllib.parse.quote_plus(connection_string)}"
            temp_engine = create_engine(master_uri)

            with temp_engine.connect() as conn:
                result = conn.execute(
                    text("SELECT name FROM sys.databases WHERE name = :db_name"),
                    {"db_name": self.database}
                )
                if not result.fetchone():
                    logger.info(f"La base '{self.database}' no existe. Creando...")
                    with temp_engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn2:
                        conn2.execute(text(f"CREATE DATABASE [{self.database}]"))
                    logger.info(f"Base de datos '{self.database}' creada.")
                else:
                    logger.info(f"Base de datos '{self.database}' ya existe.")
            return True
        except Exception as e:
            logger.error(f"ERROR al verificar o crear la base: {e}")
            return False
