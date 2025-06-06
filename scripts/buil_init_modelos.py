import sys
from pathlib import Path
import importlib.util
import importlib
import inspect
import os

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

modelos_path = ROOT_DIR / "modelos"
init_path = modelos_path / "__init__.py"

lines = []
all_exports = []

for file in modelos_path.glob("*.py"):
    if file.name.startswith("_") or not file.name.endswith(".py"):
        continue

    module_name = f"modelos.{file.stem}"
    try:
        spec = importlib.util.find_spec(module_name)
        if not spec:
            continue

        module = importlib.import_module(module_name)
        for name, cls in inspect.getmembers(module, inspect.isclass):
            if hasattr(cls, "__tablename__"):
                lines.append(f"from .{file.stem} import {name}")
                all_exports.append(f'"{name}"')
    except Exception as e:
        print(f"Error importando {module_name}: {e}")

# Crear __init__.py
with open(init_path, "w", encoding="utf-8") as f:
    for line in sorted(lines):
        f.write(line + "\n")
    f.write("\n__all__ = [\n    " + ",\n    ".join(sorted(all_exports)) + "\n]\n")

print(f"✅ Archivo generado: {init_path}")
