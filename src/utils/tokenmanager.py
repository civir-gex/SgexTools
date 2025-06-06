import jwt
import os
from datetime import datetime, timedelta, timezone
from jwt import ExpiredSignatureError, PyJWTError
from fastapi import Request, HTTPException, Depends
import logging

auth_logger = logging.getLogger("authuser")

class TokenManager:
    def __init__(self, secret: str = None, algorithm: str = None, expire_minutes: int = None):
        self.secret = secret or os.getenv("SECRET_KEY", "defaultsecret")
        self.algorithm = algorithm or os.getenv("ALGORITHM", "HS256")
        self.expire_minutes = int(expire_minutes or os.getenv("EXPIRE_MINUTES", 60))

    def generar(self, data: dict) -> str:
        to_encode = data.copy()
        exp = datetime.now(timezone.utc) + timedelta(minutes=self.expire_minutes)
        to_encode["exp"] = exp

        token = jwt.encode(to_encode, self.secret, algorithm=self.algorithm)

        usuario = data.get("usuario", "desconocido")
        desde = data.get("desde", "origen desconocido")
        fecha_exp = exp.astimezone().strftime("%d/%m/%Y %H:%M")

        auth_logger.info(f"Token generado para: {usuario}, conectado desde: {desde} con expiración {fecha_exp}")
        return token

    def leer(self, token: str) -> dict:
        try:
            decoded = jwt.decode(token, self.secret, algorithms=[self.algorithm])
            exp_ts = decoded.get("exp")
            if exp_ts:
                fecha = datetime.fromtimestamp(exp_ts, tz=timezone.utc).astimezone()
                self.expira = fecha.strftime("%d/%m/%Y %H:%M")
            else:
                self.expira = None
            return decoded
        except ExpiredSignatureError as e:
            auth_logger.warning("Token expirado.")
            raise ValueError("El token ha expirado") from e
        except PyJWTError as e:
            auth_logger.warning(f"Error de validación de token: {e}")
            raise ValueError("Token inválido") from e

    def actualizar(self, token: str) -> str:
        data = self.leer(token)
        anterior_exp = data.get("exp")
        data.pop("exp", None)
        nuevo_token = self.generar(data)

        if anterior_exp:
            anterior_dt = datetime.fromtimestamp(anterior_exp, tz=timezone.utc).astimezone()
            nueva_dt = datetime.now(tz=timezone.utc) + timedelta(minutes=self.expire_minutes)
            usuario = data.get("usuario", "desconocido")
            auth_logger.info(
                f"Token actualizado para: {usuario}, de {anterior_dt.strftime('%d/%m/%Y %H:%M')} "
                f"a {nueva_dt.strftime('%d/%m/%Y %H:%M')}"
            )

        return nuevo_token

    def validar(self, token: str) -> bool:
        try:
            self.leer(token)
            return True
        except Exception:
            return False

    @staticmethod
    async def extraer_token(request: Request) -> tuple[str | None, str]:
        """
        Extrae el token de la cabecera, cookie, query o cuerpo.
        Retorna (token, origen) o (None, 'desconocido') si no se encuentra.
        """
        token = None
        origen = "desconocido"

        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.lower().startswith("bearer "):
            token = auth_header[7:].strip()
            origen = "Authorization header"

        elif "token" in request.cookies:
            token = request.cookies["token"]
            origen = "cookie"

        elif "token" in request.query_params:
            token = request.query_params["token"]
            origen = "query param"

        elif request.method in ("POST", "PUT", "PATCH"):
            try:
                body = await request.json()
                if isinstance(body, dict) and "token" in body:
                    token = body["token"]
                    origen = "body JSON"
            except Exception:
                pass

        return token, origen

    @classmethod
    async def verificar_token(cls, request: Request) -> str:
        token, origen = await cls.extraer_token(request)

        if not token:
            auth_logger.warning("Token no proporcionado")
            raise HTTPException(status_code=401, detail="Token no proporcionado")

        try:
            if not cls().validar(token):
                auth_logger.warning(f"Token inválido desde {origen}")
                raise HTTPException(status_code=401, detail="Token inválido o expirado")
        except Exception as e:
            auth_logger.warning(f"Error al validar token desde {origen}: {e}")
            raise HTTPException(status_code=401, detail="Token inválido")

        auth_logger.info(f"Token válido recibido desde {origen}")
        return token

    @staticmethod
    async def require_token(request: Request = Depends()) -> str:
        """
        Dependencia FastAPI para rutas protegidas. Verifica que el token sea válido.
        """
        return await TokenManager.verificar_token(request)