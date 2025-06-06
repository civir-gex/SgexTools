from fastapi import APIRouter, HTTPException, Request
from src import LoggerFactory, DBFactory
import os, importlib, importlib.util,inspect
from pathlib import Path


router = APIRouter()
logger = LoggerFactory().get_logger("db", "db.log", consola=True)

@router.post("/db")
async def crear_db(request: Request):
    content_type = request.headers.get("content-type", "").lower()
    tipo = nombre = None

    try:
        if "application/json" in content_type:
            body = await request.json()
            tipo = body.get("tipo")
            nombre = body.get("nombre")
        elif "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type:
            form = await request.form()
            tipo = form.get("tipo")
            nombre = form.get("nombre")
        else:
            raise HTTPException(status_code=400, detail="Formato de contenido no soportado")

        if not tipo or not nombre:
            raise HTTPException(status_code=422, detail="Faltan campos requeridos: 'tipo' y 'nombre'")

        with DBFactory.get(tipo, nombre) as db:
            logger.info(f"Base '{nombre}' verificada o creada correctamente.")
            return {"status": "ok", "message": f"Base '{nombre}' lista."}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al conectar/crear base '{nombre}': {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/tabla")
async def crear_tabla(request: Request):
    try:
        content_type = request.headers.get("content-type", "").lower()
        if "application/json" not in content_type:
            raise HTTPException(status_code=400, detail="Solo se acepta JSON como contenido")

        body = await request.json()
        tipo = body.get("tipo", "mssql")
        base = body.get("base")
        tabla = body.get("tabla")
        registro = body.get("registro")

        if not base or not tabla:
            raise HTTPException(status_code=422, detail="Faltan campos requeridos: 'base' y 'tabla'")

        modelos_path = Path(__file__).resolve().parents[1] / "modelos"
        modelo = None

        for archivo in modelos_path.glob("*.py"):
            if archivo.name.startswith("_"):
                continue

            modulo_name = f"modelos.{archivo.stem}"
            try:
                spec = importlib.util.find_spec(modulo_name)
                if not spec:
                    continue
                mod = importlib.import_module(modulo_name)
                for nombre, clase in inspect.getmembers(mod, inspect.isclass):
                    if nombre == tabla and hasattr(clase, "__tablename__"):
                        modelo = clase
                        break
                if modelo:
                    break
            except Exception as e:
                logger.warning(f"No se pudo cargar modelo desde {modulo_name}: {e}")

        if not modelo:
            raise HTTPException(status_code=404, detail=f"Modelo '{tabla}' no encontrado en 'modelos/'.")

        with DBFactory.get(tipo, base) as db:
            db.create_table(modelo)
            logger.info(f"Tabla '{tabla}' verificada en base '{base}'.")

            inserted_pk = None
            if registro:
                try:
                    instancia = modelo(**registro)
                    db.add_record(instancia)
                    logger.info(f"Registro insertado en tabla '{tabla}'.")
                    # Obtener el valor del campo PK
                    inserted_pk = getattr(instancia, "rfc_empresa", None)
                except Exception as e:
                    logger.error(f"Error al insertar registro en '{tabla}'")
                    raise HTTPException(status_code=400, detail=f"Registro inválido para el modelo '{tabla}'.")

            return {
                "status": "ok",
                "message": f"Tabla '{tabla}' lista en base '{base}'." + (" Registro insertado." if inserted_pk else ""),
                "id": inserted_pk
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en creación de tabla o inserción de registro: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tabla")
def listar_modelos():
    try:
        modelos_path = Path(__file__).resolve().parents[1] / "modelos"
        modelos_disponibles = []

        for archivo in modelos_path.glob("*.py"):
            if archivo.name.startswith("_"):
                continue  # ignorar __init__.py u otros privados

            nombre_modulo = f"modelos.{archivo.stem}"
            try:
                modulo = importlib.import_module(nombre_modulo)
                for nombre, clase in inspect.getmembers(modulo, inspect.isclass):
                    if hasattr(clase, "__tablename__"):
                        modelos_disponibles.append(nombre)
            except Exception as e:
                logger.warning(f"No se pudo cargar {nombre_modulo}: {e}")

        return {
            "status": "ok",
            "modelos_disponibles": sorted(modelos_disponibles)
        }

    except Exception as e:
        logger.error(f"Error al listar modelos: {e}")
        raise HTTPException(status_code=500, detail=str(e))