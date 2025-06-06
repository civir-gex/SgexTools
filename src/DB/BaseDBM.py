import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import NullPool
from src import LoggerFactory

Base = declarative_base()
logger = LoggerFactory().get_logger("db", "db.log", consola=True)

class DataBaseFail(Exception):
    pass

class BaseDBManager:
    def __init__(self, database_uri):
        self.database_uri = database_uri
        self.engine = None
        self.Session = None
        self._database_ready = self._check_or_create_database()

    def _check_or_create_database(self):
        return True

    def connect(self):
        if not self._database_ready:
            raise DataBaseFail("Base de datos no conectada.")
        self.engine = create_engine(self.database_uri, poolclass=NullPool)
        self.Session = sessionmaker(bind=self.engine)

    def create_table(self, model_class):
        if not self._database_ready:
            raise DataBaseFail("Base de datos no conectada.")
        if not self.engine:
            self.connect()
        model_class.__table__.create(self.engine, checkfirst=True)
        logger.info(f"Tabla '{model_class.__tablename__}' creada o ya existente.")
        
    def create_tables(self):
            if not self._database_ready:
                raise DataBaseFail("Base de datos no conectada.")
            if not self.engine:
                self.connect()
            Base.metadata.create_all(self.engine)
            logger.info("Tablas creadas o ya existentes.")

    def add_record(self, record):
        if not self._database_ready:
            raise DataBaseFail("Base de datos no conectada.")
        session = self.Session()
        try:
            session.add(record)
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Error al agregar registro: {e}")
            raise
        finally:
            session.close()

    def get_records(self, table_class):
        if not self._database_ready:
            raise DataBaseFail("Base de datos no conectada.")
        session = self.Session()
        try:
            return session.query(table_class).all()
        finally:
            session.close()

    def update_record(self, table_class, record_id, **kwargs):
        if not self._database_ready:
            raise DataBaseFail("Base de datos no conectada.")
        session = self.Session()
        try:
            record = session.get(table_class, record_id)
            if record:
                for key, value in kwargs.items():
                    setattr(record, key, value)
                session.commit()
        except Exception as e:
            session.rollback()
            logger.info(f"Error al actualizar registro: {e}")
        finally:
            session.close()

    def delete_record(self, table_class, record_id):
        if not self._database_ready:
            raise DataBaseFail("Base de datos no conectada.")
        session = self.Session()
        try:
            record = session.get(table_class, record_id)
            if record:
                session.delete(record)
                session.commit()
        except Exception as e:
            session.rollback()
            logger.info(f"Error al eliminar registro: {e}")
        finally:
            session.close()

    def close(self):
        if self.engine:
            self.engine.dispose()
            self.engine = None
            self.Session = None
        logger.info("¡Conexión cerrada!")

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
