import os, sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from datetime import date, datetime
from pathlib import Path

from satcfdi.models import Signer
from satcfdi.pacs.sat import SAT, EstadoSolicitud, TipoDescargaMasivaTerceros


class WSSAT:
    def __init__(self, cer, key, passwd):
        self.firmante = Signer.load(
            certificate=open(cer, "rb").read(),
            key=open(key, "rb").read(),
            password=open(passwd, "r").read().strip(),
        )
        self.Servicio = SAT(signer=self.firmante)

        # Mapeo legible de estados
        self.estado_legible = {
            EstadoSolicitud.ACEPTADA: "Solicitud aceptada, en espera",
            EstadoSolicitud.EN_PROCESO: "SAT está procesando",
            EstadoSolicitud.TERMINADA: "¡Lista para descarga!",
            EstadoSolicitud.RECHAZADA: "Rechazada",
            EstadoSolicitud.VENCIDA: "Vencida",
            EstadoSolicitud.ERROR: "Error desconocido"
        }

    def Solicitud(self, fi: date, ff: date, tipo: str = "recibidos") -> dict:
        tipo = tipo.lower()
        if tipo not in {"recibidos", "emitidos"}:
            raise ValueError("El tipo debe ser 'recibidos' o 'emitidos'.")
        self.periodo=[fi,ff]
        kwargs = {
            "fecha_inicial": fi,
            "fecha_final": ff,
            "tipo_solicitud": TipoDescargaMasivaTerceros.CFDI,
        }

        if tipo == "recibidos":
            kwargs["rfc_receptor"] = self.firmante.rfc
        else:
            kwargs["rfc_emisor"] = self.firmante.rfc

        response = self.Servicio.recover_comprobante_request(**kwargs)

        return {
            "id_solicitud": response.get("IdSolicitud"),
            "RFC_solicitante":self.firmante.rfc,
            "fecha_solicitud":datetime.now().isoformat(),
            "tipo":tipo,
            "ini_periodo":fi,
            "fin_periodo":ff,
            "estado": response.get("EstadoSolicitud"),
            "mensaje": response.get("Mensaje"),
        }
    
    def check_status(self, id_solicitud: str):
        pass

    def descarga(self,paquetes):
        pass

