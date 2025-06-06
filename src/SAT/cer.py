import re, os, base64, hashlib
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import load_der_private_key
from cryptography.exceptions import InvalidSignature

class CertSAT:
    def __init__(self, path_cer: str, path_key: str = None, path_pwd: str = None):
        self.path_cer = path_cer
        self.path_key = path_key
        self.path_pwd = path_pwd
        self._info = None
        self._cer_bytes = None
        self._key_bytes = None
        self._pwd = None

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
        """Valida que la llave privada corresponda al certificado público"""
        if not self.path_key or not self.path_pwd:
            return  # No se requiere validación si no se proporcionan ambos

        try:
            private_key = load_der_private_key(self.key_bytes, password=self.pwd.encode(), backend=default_backend())
        except Exception as e:
            raise ValueError(f"No se pudo cargar la llave privada: {e}")

        # Probar firma y verificación
        mensaje = b"mensaje de prueba"
        firma = private_key.sign(mensaje, padding.PKCS1v15(), hashes.SHA256())

        try:
            cert.public_key().verify(firma, mensaje, padding.PKCS1v15(), hashes.SHA256())
        except InvalidSignature:
            raise ValueError("La llave privada no corresponde al certificado proporcionado.")

    @property
    def info(self) -> dict:
        if self._info is not None:
            return self._info

        if not os.path.exists(self.path_cer):
            raise FileNotFoundError(f"El archivo '{self.path_cer}' no existe.")

        try:
            cert = x509.load_der_x509_certificate(self.cer_bytes, default_backend())
        except Exception as e:
            raise ValueError(f"No se pudo leer el certificado: {e}")

        # Validar que el .key y la contraseña corresponden
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
                partes = [x.strip() for x in value.split("/")]
                rfc_list.extend(partes)

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
        """Firma un mensaje y devuelve la firma en base64"""
        if not self.path_key or not self.path_pwd:
            raise ValueError("Para firmar se requiere la llave y la contraseña.")
        try:
            private_key = load_der_private_key(self.key_bytes, password=self.pwd.encode(), backend=default_backend())
        except Exception as e:
            raise ValueError(f"No se pudo cargar la llave privada: {e}")
        firma = private_key.sign(mensaje, padding.PKCS1v15(), hashes.SHA256())
        return base64.b64encode(firma).decode("utf-8")

    def validar_firma(self, mensaje: bytes, firma_b64: str) -> bool:
        """Valida que la firma (en base64) corresponde al certificado"""
        cert = x509.load_der_x509_certificate(self.cer_bytes, default_backend())
        try:
            firma = base64.b64decode(firma_b64)
            cert.public_key().verify(firma, mensaje, padding.PKCS1v15(), hashes.SHA256())
            return True
        except (InvalidSignature, ValueError, TypeError):
            return False

    def firmar_archivo(self, path: str) -> dict:
        """Firma un archivo, retorna dict con firma base64, hash SHA256 y nombre"""
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

    def verificar_firma_archivo(self, path: str, firma_b64: str) -> bool:
        """Valida que la firma corresponde al contenido del archivo"""
        if not os.path.exists(path):
            raise FileNotFoundError(f"El archivo '{path}' no existe.")

        with open(path, "rb") as f:
            contenido = f.read()
        return self.validar_firma(contenido, firma_b64)




# Ejemplo de uso
cert = CertSAT("files/EXP6812035X3/EXP6812035X3.cer","files/EXP6812035X3/EXP6812035X3.key","files/EXP6812035X3/key.txt")
for k, v in cert:
    print(f"{k}: {v}")
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
