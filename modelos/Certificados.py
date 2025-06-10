from sqlalchemy import Column, String, LargeBinary, DateTime
from src import Base

class CertificadoSAT(Base):
    __tablename__ = 'certificados'

    rfc_empresa = Column(String(20), primary_key=True)  # RFC de la empresa como ID
    rfc_representante = Column(String(20))
    razon_social = Column(String(255))
    email = Column(String(255))
    serie = Column(String(100))
    valido_desde = Column(DateTime)
    valido_hasta = Column(DateTime)
    # cer = Column(LargeBinary, nullable=True)  # Acepta NULL
    # key = Column(LargeBinary, nullable=True)  # Acepta NULL
    pwd = Column(String(255))