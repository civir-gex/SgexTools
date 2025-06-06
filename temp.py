from modelos.certificado_sat import CertificadoSAT
from tools.sat.cert import CertSAT  # tu clase para leer info del .cer

def registrar_certificado_sat(db, ruta_cer, ruta_key, ruta_pwd):
    cert_info = CertSAT(ruta_cer).info

    with open(ruta_cer, "rb") as f:
        cer_bytes = f.read()
    with open(ruta_key, "rb") as f:
        key_bytes = f.read()
    with open(ruta_pwd, "r") as f:
        pwd = f.read().strip()

    certificado = CertificadoSAT(
        rfc_empresa=cert_info["rfc_empresa"],
        rfc_representante=cert_info["rfc_representante"],
        razon_social=cert_info["razon_social"],
        email=cert_info["email"],
        serie=cert_info["serie"],
        valido_desde=cert_info["valido_desde"],
        valido_hasta=cert_info["valido_hasta"],
        cer=cer_bytes,
        key=key_bytes,
        pwd=pwd
    )

    db.add_record(certificado)
