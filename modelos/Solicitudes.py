from sqlalchemy import Column, String, Date, DateTime
from src import Base
from datetime import datetime

class SolicitudSAT(Base):
    __tablename__ = "solicitudes_sat"

    id = Column(String, primary_key=True)
    fi = Column(Date, nullable=False)
    ff = Column(Date, nullable=False)
    solicitado = Column(DateTime, default=datetime.now)
    tipo = Column(String)
    estado = Column(String, default="pendiente")
