import os
from fastapi import APIRouter, HTTPException, Request, Response 
from pydantic import BaseModel
from dotenv import load_dotenv
from src import AuthUser, TokenManager

load_dotenv("../.env")

AuthUser.usr = os.getenv("usrAD") 
AuthUser.pwd = os.getenv("passAD") 
AuthUser.ip = os.getenv("ipAD") 
AuthUser.dom = os.getenv("dominioAD") 
AuthUser.contr = f"ldap://{AuthUser.ip}:389"

router = APIRouter()

class AuthRequest(BaseModel):
    usuario: str
    contrasena: str

@router.post("/login")
def login(request: AuthRequest, response: Response):
    user = AuthUser(request.usuario, request.contrasena)
    if not user.autentificado:
        raise HTTPException(status_code=401, detail=user.msg or "Autenticación fallida.")

    # Establecer token como cookie
    response.set_cookie(
        key="token",
        value=user.token,
        httponly=True,
        samesite="lax",
        secure=False  # Cámbialo a True si usas HTTPS
    )

    return user.aDiccionario

@router.get("/login")
async def validar_token(request: Request):
    token, origen = await TokenManager.extraer_token(request)
    if not token:
        raise HTTPException(status_code=401, detail="Token no proporcionado")

    tk = TokenManager()
    if tk.validar(token):
        return {"msg": f"Válido hasta {tk.expira}", "origen": origen}
    
    raise HTTPException(status_code=401, detail="Token inválido o expirado")

@router.post("/extend")
async def extender_token(request: Request, response: Response):
    token, origen = await TokenManager.extraer_token(request)
    if not token:
        raise HTTPException(status_code=401, detail="Token no proporcionado")

    tk = TokenManager()
    if not tk.validar(token):
        raise HTTPException(status_code=401, detail="Token inválido o expirado")

    nuevo_token = tk.actualizar(token)

    # Actualiza cookie
    response.set_cookie(
        key="token",
        value=nuevo_token,
        httponly=True,
        samesite="lax",
        secure=False  # Cambia a True si usas HTTPS
    )

    return {"status": "ok", "token": nuevo_token, "origen": origen}
