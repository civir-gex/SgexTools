import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from src import MSSQLDBManager, MySQLDBManager, PostgreSQLDBManager, SQLiteDBManager, LoggerFactory


# Obtener logger centralizado
db_logger = LoggerFactory().get_logger("db_factory", "db.log")

class DBFactory:
    @staticmethod
    def get(db_type: str, db_name: str, **kwargs):
        db_type = db_type.lower()
        db_logger.info(f"Inicializando gestor para base de datos tipo '{db_type}' con nombre '{db_name}'")

        if db_type == "mssql":
            return MSSQLDBManager(db_name, **kwargs)
        elif db_type == "mysql":
            return MySQLDBManager(db_name, **kwargs)
        elif db_type in ("postgresql", "pg"):
            return PostgreSQLDBManager(db_name, **kwargs)
        elif db_type == "sqlite":
            return SQLiteDBManager(file_path=db_name, **kwargs)
        else:
            db_logger.error(f"Tipo de base de datos no soportado: {db_type}")
            raise ValueError(f"Tipo de base de datos no soportado: {db_type}")
