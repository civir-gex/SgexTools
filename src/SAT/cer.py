import os
import re
import json
import base64
import hashlib
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import load_der_private_key

class CertSAT:
    def __init__(self, path_cer: str, path_key: str = None, path_pwd: str = None):
        self.path_cer = path_cer
        self.path_key = path_key
        self.path_pwd = path_pwd
        self._cer_bytes = None
        self._key_bytes = None
        self._pwd = None
        self._info = None

    def __iter__(self):
        return iter(self.info.items())

    @property
    def cer_bytes(self) -> bytes:
        if self._cer_bytes is None:
            with open(self.path_cer, "rb") as f:
                self._cer_bytes = f.read()
        return self._cer_bytes

    @property
    def key_bytes(self) -> bytes:
        if self.path_key and self._key_bytes is None:
            with open(self.path_key, "rb") as f:
                self._key_bytes = f.read()
        return self._key_bytes

    @property
    def pwd(self) -> str:
        if self.path_pwd and self._pwd is None:
            with open(self.path_pwd, "r", encoding="utf-8") as f:
                self._pwd = f.readline().strip()
        return self._pwd

    def validar_correspondencia(self, cert: x509.Certificate):
        if not self.path_key or not self.path_pwd:
            return
        try:
            private_key = load_der_private_key(self.key_bytes, password=self.pwd.encode(), backend=default_backend())
        except Exception as e:
            raise ValueError(f"No se pudo cargar la llave privada: {e}")

        mensaje = b"test-firma"
        firma = private_key.sign(mensaje, padding.PKCS1v15(), hashes.SHA256())
        try:
            cert.public_key().verify(firma, mensaje, padding.PKCS1v15(), hashes.SHA256())
        except InvalidSignature:
            raise ValueError("La llave privada no corresponde al certificado.")

    @property
    def info(self) -> dict:
        if self._info is not None:
            return self._info

        if not os.path.exists(self.path_cer):
            raise FileNotFoundError(f"El archivo '{self.path_cer}' no existe.")

        cert = x509.load_der_x509_certificate(self.cer_bytes, default_backend())
        self.validar_correspondencia(cert)

        subject = cert.subject
        razon_social = None
        email = None
        rfc_list = []

        for attr in subject:
            oid = attr.oid.dotted_string
            value = attr.value.strip()
            if attr.oid == NameOID.COMMON_NAME:
                razon_social = value
            elif attr.oid == NameOID.EMAIL_ADDRESS:
                email = value
            elif oid == "2.5.4.45":
                rfc_list.extend([x.strip() for x in value.split("/")])

        rfc_validos = [r for r in rfc_list if re.fullmatch(r"[A-Z\u00d1&]{3,4}\d{6}[A-Z0-9]{3}", r)]
        rfc_empresa = rfc_validos[0] if rfc_validos else None
        rfc_representante = rfc_validos[1] if len(rfc_validos) > 1 else None

        self._info = {
            "rfc_empresa": rfc_empresa,
            "rfc_representante": rfc_representante,
            "razon_social": razon_social,
            "email": email,
            "serie": str(cert.serial_number),
            "valido_desde": cert.not_valid_before_utc,
            "valido_hasta": cert.not_valid_after_utc,
            "cer": self.cer_bytes,
            "key": self.key_bytes,
            "pwd": self.pwd,
        }
        return self._info

    def firmar(self, mensaje: bytes) -> str:
        if not self.path_key or not self.path_pwd:
            raise ValueError("Para firmar se requiere la llave y la contraseña.")
        private_key = load_der_private_key(self.key_bytes, password=self.pwd.encode(), backend=default_backend())
        firma = private_key.sign(mensaje, padding.PKCS1v15(), hashes.SHA256())
        return base64.b64encode(firma).decode("utf-8")

    def validar_firma(self, mensaje: bytes, firma_b64: str) -> bool:
        cert = x509.load_der_x509_certificate(self.cer_bytes, default_backend())
        try:
            firma = base64.b64decode(firma_b64)
            cert.public_key().verify(firma, mensaje, padding.PKCS1v15(), hashes.SHA256())
            return True
        except Exception:
            return False

    def firmar_archivo(self, path: str) -> dict:
        if not os.path.exists(path):
            raise FileNotFoundError(f"El archivo '{path}' no existe.")

        with open(path, "rb") as f:
            contenido = f.read()
        firma_b64 = self.firmar(contenido)
        sha256_hash = hashlib.sha256(contenido).hexdigest()

        return {
            "archivo": os.path.basename(path),
            "firma": firma_b64,
            "hash": sha256_hash
        }

    def firmar_archivo_con_guardado(self, path: str, destino: str = None) -> dict:
        resultado = self.firmar_archivo(path)
        if destino is None:
            destino = f"{path}.firma.json"
        with open(destino, "w", encoding="utf-8") as f:
            json.dump(resultado, f, indent=4, ensure_ascii=False)
        return resultado

    def verificar_firma_archivo(self, path: str, firma_b64: str) -> bool:
        if not os.path.exists(path):
            raise FileNotFoundError(f"El archivo '{path}' no existe.")
        with open(path, "rb") as f:
            contenido = f.read()
        return self.validar_firma(contenido, firma_b64)

    def verificar_firma_desde_json(self, path_archivo: str, path_json: str) -> dict:
        resultado = {
            "archivo_valido": False,
            "hash_valido": False,
            "firma_valida": False,
            "detalle": ""
        }

        if not os.path.exists(path_archivo):
            resultado["detalle"] = f"Archivo no encontrado: {path_archivo}"
            return resultado
        if not os.path.exists(path_json):
            resultado["detalle"] = f"Archivo de firma no encontrado: {path_json}"
            return resultado

        try:
            with open(path_archivo, "rb") as f:
                contenido = f.read()
            with open(path_json, "r", encoding="utf-8") as f:
                datos = json.load(f)
        except Exception as e:
            resultado["detalle"] = f"Error al leer archivos: {e}"
            return resultado

        resultado["archivo_valido"] = os.path.basename(path_archivo) == datos.get("archivo")
        resultado["hash_valido"] = hashlib.sha256(contenido).hexdigest() == datos.get("hash")
        resultado["firma_valida"] = self.validar_firma(contenido, datos.get("firma"))

        if all([resultado["archivo_valido"], resultado["hash_valido"], resultado["firma_valida"]]):
            resultado["detalle"] = "Verificación completa exitosa."
        else:
            errores = []
            if not resultado["archivo_valido"]:
                errores.append("nombre de archivo")
            if not resultado["hash_valido"]:
                errores.append("hash SHA256")
            if not resultado["firma_valida"]:
                errores.append("firma digital")
            resultado["detalle"] = f"Fallo en: {', '.join(errores)}"

        return resultado



# Ejemplo de uso
cert = CertSAT("files/EXP6812035X3/EXP6812035X3.cer","files/EXP6812035X3/EXP6812035X3.key","files/EXP6812035X3/key.txt")
for k, v in cert:
    print(f"{k}: {v}\n")
# print(cer.info)

mensaje = b"Mensaje importante"
firma = cert.firmar(mensaje)
print(firma)
es_valida = cert.validar_firma(mensaje, firma)
print("Firma válida:", es_valida)

# cert = CertSAT("archivos/cert.cer", "archivos/cert.key", "archivos/cert.txt")

# resultado = cert.firmar_archivo("documentos/mi_archivo.pdf")
# print("Firma generada:")
# print(resultado)

# valido = cert.verificar_firma_archivo("documentos/mi_archivo.pdf", resultado["firma"])
# print("¿Firma válida?", valido)
