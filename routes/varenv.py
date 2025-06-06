from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict
from src import VarEnv

router = APIRouter()
env = VarEnv(True)

class Variable(BaseModel):
    key: str
    value: str

@router.get("/get")
def get_variable(key: str, default: Optional[str] = None):
    value = env.get(key, default)
    return {"key": key, "value": value}

@router.post("/set")
def set_variable(data: Variable):
    env.set(data.key, data.value)
    env.reload()
    return {"message": f"Variable {data.key} establecida con éxito"}

@router.delete("/remove")
def remove_variable(key: str):
    if not env.exists(key):
        raise HTTPException(status_code=404, detail=f"La variable {key} no existe.")
    env.remove(key)
    return {"message": f"Variable {key} eliminada con éxito"}

# @router.get("/all")
# def list_all():
#     return env.variables

@router.post("/reload")
def reload_env():
    env.reload()
    return {"message": "Variables recargadas desde .env"}

@router.get("/export")
def export_variables():
    return env.variables

@router.post("/import")
def import_variables(payload: Dict[str, str]):
    for key, value in payload.items():
        env.set(key, value)
    return {"message": f"{len(payload)} variables importadas al .env"}
