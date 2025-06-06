import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

import logging
from pathlib import Path

class LoggerFactory:
    _instance = None

    COLOR_MAP = {
        'DEBUG': '\033[94m',     # Blue
        'INFO': '\033[92m',      # Green
        'WARNING': '\033[93m',   # Yellow
        'ERROR': '\033[91m',     # Red
        'CRITICAL': '\033[95m'   # Magenta
    }
    RESET = '\033[0m'

    def __new__(cls, base_dir: Path = None):
        if cls._instance is None:
            cls._instance = super(LoggerFactory, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, base_dir: Path = None):
        if self._initialized:
            return
        self._initialized = True

        if base_dir is None:
            self.log_dir = Path(__file__).resolve().parents[2] / "logs"
        else:
            self.log_dir = Path(base_dir) / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def get_logger(self, nombre: str, archivo_log: str, consola: bool = False) -> logging.Logger:
        log_file = self.log_dir / archivo_log

        logger = logging.getLogger(nombre)

        if not logger.handlers:
            class FileLineFormatter(logging.Formatter):
                def format(self_inner, record):
                    base_filename = Path(record.pathname).name
                    lineno = record.lineno
                    message = super(FileLineFormatter, self_inner).format(record)
                    return f"{base_filename} >{lineno:06}<    {message}"

            handler_file = logging.FileHandler(log_file, encoding="utf-8")
            handler_file.setFormatter(FileLineFormatter("%(asctime)s [%(levelname)s] %(message)s"))
            logger.setLevel(logging.INFO)
            logger.addHandler(handler_file)

            if consola:
                class ColoredFormatter(logging.Formatter):
                    def format(self_inner, record):
                        color = LoggerFactory.COLOR_MAP.get(record.levelname, '')
                        try:
                            with log_file.open("r", encoding="utf-8") as f:
                                linea_log = sum(1 for _ in f) 
                        except FileNotFoundError:
                            linea_log = 1
                        message = super(ColoredFormatter, self_inner).format(record)
                        return f"{color}{archivo_log}({linea_log:06}) <- {message}{LoggerFactory.RESET}"

                handler_console = logging.StreamHandler()
                handler_console.setFormatter(ColoredFormatter("%(asctime)s [%(levelname)s] %(message)s"))
                logger.addHandler(handler_console)

        logger.propagate = False
        return logger
