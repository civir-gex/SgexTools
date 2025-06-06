# SgexTools

**SgexTools** es un conjunto de herramientas desarrolladas en Python para interactuar con distintos sistemas y formatos de información, incluyendo:

- 📦 Bases de datos: SQLite, MySQL, PostgreSQL, SQL Server
- 📄 Archivos PDF y XML
- 📊 Archivos Excel (.xls/.xlsx)
- 🧾 SAT México: descarga y procesamiento de CFDI
- 🏢 SAP Business One (Service Layer)

---

## 🚀 Estructura del Proyecto

```
├──files/
├──modelos/            # modelos ORM
├──src/
│   ├──DB/                 # Módulos para conexión a bases de datos
│   │   ├── __init__.py
│   │   ├── BaseDBM.py
│   │   ├── MSSQLDBM.py
│   │   ├── MySQLDBM.py
│   │   ├── PostgreSQLDBM.py
│   │   ├── SQLiteDBM.py
│   │   └──script.sh
│   │       ├── ODBC_Alpine.sh
│   │       ├── ODBC_Debian.sh
│   │       ├── ODBC_RHEL_Oracle.sh
│   │       ├── ODBC_SLES.sh
│   │       └── ODBC_Ubuntu.sh
│   ├──PDF/                # Herramientas para extracción y manejo de PDFs
│   │   ├── __init__.py
│   │   └── . . .
│   ├──SAP/                # Integración con SAP B1
│   │   ├── __init__.py
│   │   └── . . .
│   ├──SAT/                # Automatización con el SAT (CFDI, e.firma)
│   │   ├── __init__.py
│   │   ├── ws.py               
│   │   └── . . .
│   ├──XLS/                # Lectura y escritura de archivos Excel
│   │   ├── __init__.py
│   │   └── . . .
│   ├──XML/                # Procesamiento de archivos XML
│   │   ├── __init__.py
│   │   └── . . .
│   ├──...
│   │   ├── __init__.py
│   │   └── . . .
│   ├──config.py           # Configuración global del proyecto
│   │   ├── __init__.py
│   │   └── . . .
│   └──utils/              # funciones comunes
│       ├── __init__.py
│       ├── VariablesAmbiente.py
│       └── . . .
├──tests/              # pruebas unitarias
├── requirements.txt
├── CHANGELOG.md
├── README.md
└── .env
```

---

## ⚙️ Instalación

```bash
# Crear y activar entorno virtual (si no existe)
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows

# Instalar dependencias
pip install -r requirements.txt
```

---

## 🔐 Variables de Entorno

Cada módulo (`DB`, `SAP`, `SAT`, etc.) contiene su propio archivo `.env` ubicado en su respectiva carpeta:

```env
src/
├── DB/
│ └── .env
├── SAP/
│ └── .env
├── SAT/
│ └── .env
...
```

---

## 🧪 Pruebas

Las pruebas estarán ubicadas en el directorio `tests/`. Se recomienda usar `pytest`.

---

## 📄 Licencia

MIT License.
