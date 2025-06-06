from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from routes import varenv, auth, dbm 
from src import TokenManager

app = FastAPI(title="SgexTools API")

# Lista de orígenes permitidos (puede ser frontend en React/Vue/etc.)
origins = [
    "http://localhost",
    "http://127.0.0.1"    # Cambia este origen según sea necesario
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,              # Orígenes permitidos
    allow_credentials=True,             # <-- Esto es importante
    allow_methods=["*"],                # Permitir todos los métodos (GET, POST, etc.)
    allow_headers=["*"],                # Permitir todas las cabeceras (incluye Authorization, Content-Type, etc.)
)

app.include_router(
    auth.router, 
    prefix="/auth", 
    tags=["Autenticación"]
    )

app.include_router(
    varenv.router, 
    prefix="/env", 
    tags=["Variables de Entorno"],
    dependencies=[Depends(TokenManager.verificar_token)]
    )

app.include_router(
    dbm.router, 
    prefix="/dbm", 
    tags=["Acciones para bases de datos"],
    dependencies=[Depends(TokenManager.verificar_token)]
    )