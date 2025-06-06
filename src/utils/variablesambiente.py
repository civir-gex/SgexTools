import sys, os, json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from pathlib import Path
from dotenv import dotenv_values, set_key, load_dotenv
from .logger import LoggerFactory

logger_var = LoggerFactory().get_logger("varenv", "variables.log", consola=True)

class VarEnv:
    def __init__(self, debuger: bool = False):
        try:
            self.debuger = debuger
            self.project_root = Path(__file__).resolve().parents[2]
            self.env_file = self.project_root / ".env"
            self.rel_env_path = "/" + str(self.env_file.relative_to(self.project_root))

            logger_var.info(f"Verificando archivo .env en: {self.rel_env_path}")

            if not self.env_file.exists():
                self.env_file.touch()
                logger_var.warning(f"Archivo .env no existía, se ha creado vacío en: {self.rel_env_path}")

            self.variables = dotenv_values(self.env_file)
            logger_var.info(f"{len(self.variables)} variables cargadas desde {self.rel_env_path}")

            if not isinstance(self.variables, dict):
                raise ValueError("El archivo .env no contiene variables válidas.")

            load_dotenv(dotenv_path=self.env_file, override=True)
            logger_var.info("Variables cargadas a os.environ con éxito.")

        except Exception as e:
            logger_var.exception("Error al inicializar VarEnv")
            raise RuntimeError(f"Error al inicializar las variables de entorno: {e}")

    def _safe_value(self, key, value):
        return value if self.debuger else "***"

    def get(self, key: str, default=None):
        value = self.variables.get(key, default)
        log_val = self._safe_value(key, value)
        if key in self.variables:
            logger_var.info(f"Obtenido: {key} = {log_val}")
        else:
            logger_var.info(f"{key} no definido, se usa valor por defecto: {log_val}")
        return value

    def exists(self, key: str) -> bool:
        existe = key in self.variables
        logger_var.info(f"Verificación existencia '{key}': {existe}")
        return existe

    def set(self, key: str, value: str):
        value = str(value)
        set_key(str(self.env_file), key, value, quote_mode="never")
        self.variables[key] = value
        logger_var.info(f"Variable establecida: {key} = {self._safe_value(key, value)} en {self.rel_env_path}")

    def remove(self, key: str):
        if key in self.variables:
            lines = self.env_file.read_text().splitlines()
            lines = [line for line in lines if not line.strip().startswith(f"{key}=")]
            self.env_file.write_text("\n".join(lines) + "\n")
            self.variables.pop(key)
            logger_var.info(f"Variable eliminada: {key} de {self.rel_env_path}")
        else:
            logger_var.warning(f"Intento de eliminar '{key}' que no existe en {self.rel_env_path}")

    def reload(self):
        self.variables = dotenv_values(self.env_file)
        logger_var.info(f"Variables recargadas desde {self.rel_env_path}")

    def get_remote_first(self, key: str, default=None):
        """
        Intenta obtener la variable desde la API REST local (http://localhost:8000/varenv/get?key=...)
        Si falla, recurre al archivo .env como respaldo.
        """
        try:
            import requests
            from requests.exceptions import RequestException

            url = f"http://localhost:8000/varenv/get?key={key}"
            response = requests.get(url, timeout=2)

            if response.status_code == 200:
                value = response.json().get("value", default)
                if value is not None:
                    logger_var.info(f"Variable '{key}' obtenida vía API: {self._safe_value(key, value)}")
                    return value
        except RequestException as e:
            logger_var.warning(f"No se pudo obtener '{key}' desde la API. Se usará .env. Detalle: {e}")

        return self.get(key, default)

    def export_to_json(self, path: str):
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.variables, f, indent=4, ensure_ascii=False)
            logger_var.info(f"Variables exportadas a JSON en: {path}")
        except Exception as e:
            logger_var.error(f"Error al exportar a JSON: {e}")
            raise

    def import_from_json(self, path: str):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for key, value in data.items():
                self.set(key, str(value))
            logger_var.info(f"Variables importadas desde JSON: {path}")
        except Exception as e:
            logger_var.error(f"Error al importar desde JSON: {e}")
            raise

# VarEnv(True).export_to_json("backup_env.json")