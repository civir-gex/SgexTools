import sys, os, json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from pathlib import Path
from ldap3 import Server, Connection, ALL, SUBTREE, NTLM
from ldap3.core.exceptions import LDAPBindError
from src import VarEnv, is_host_alive, TokenManager, LoggerFactory

auth_logger=LoggerFactory().get_logger("authuser", "authuser.log", consola=True)

# Variables de entorno
class varAD:
    usr=""
    pwd=""
    ip=""
    dom=""
    contr=""
    
## Modelos
class UserAD(varAD):
    def __repr__(self):
        return f'"{self.usr}","{self.pwd}"'

class ServAD(UserAD):
    def __repr__(self):
        return f'"{self.ip}","{self.dom}","{self.contr}"'

    @property
    def adminAD(self):
        return f'"{self.usr}","{self.pwd}","{self.dom}","{self.contr}"'

    @property
    def listo(self):
        return is_host_alive(self.ip)

class User:
    givenName = None
    sn = None
    pwd = None
    displayName = None
    mail = None
    telephoneNumber = None
    memberOf = None
    description = None
    msg = None
    msg_err = None
    autentificado = False
    token = 'ZmFsc28K'

class AuthUser(ServAD, User):
    def __init__(self, usuario, contrasena):
        self.msg = None
        self.msg_err = None
        self.autentificado = False

        try:
            import socket
            client_ip = socket.gethostbyname(socket.gethostname())
        except Exception:
            client_ip = "localhost"
        
        auth_logger.info(f"Inicio de autenticación para usuario: {usuario} desde IP: {client_ip}")

        if not self.listo:
            self.msg = f"No se encuentra el servidor para validar el usuario: {usuario}"
            auth_logger.warning(f"Servidor {self.dom} no responde. IP: {self.ip}")
            return

        try:
            server = Server(self.contr, get_info=ALL)
            conexion = Connection(
                server,
                user=f"{self.dom}\\{usuario}",
                password=contrasena,
                authentication=NTLM,
                auto_bind=True
            )

            if conexion.bind():
                self.autentificado = True
                self.msg = f"Autenticación exitosa: {usuario}"
                auth_logger.info(self.msg)

                filtro = f"(&(sAMAccountName={usuario}))"
                atributos = ['*']
                conexion.search(
                    search_base='DC=gex,DC=local',
                    search_filter=filtro,
                    search_scope=SUBTREE,
                    attributes=atributos
                )

                entry = conexion.entries[0]

                def safe_ldap_value(entry, attr):
                    return getattr(entry, attr).value if attr in entry else None

                self.givenName = safe_ldap_value(entry, "givenName")
                self.sn = safe_ldap_value(entry, "sn")
                self.displayName = safe_ldap_value(entry, "displayName")
                self.mail = safe_ldap_value(entry, "mail")
                self.pwd = contrasena
                self.telephoneNumber = safe_ldap_value(entry, "telephoneNumber")
                self.description = safe_ldap_value(entry, "description")
                self.memberOf = ', '.join(entry.memberOf.values) if 'memberOf' in entry else None

                self.token = TokenManager().generar({"usuario": usuario, "desde":client_ip})

                conexion.unbind()
            else:
                self.msg = f"Autenticación fallida: {usuario}"
                auth_logger.warning(self.msg)

        except LDAPBindError as e:
            self.msg = f"Credenciales inválidas para el usuario: {usuario}"
            self.msg_err = str(e)
            auth_logger.warning(f"{self.msg} - {e}")

        except Exception as e:
            self.msg_err = str(e)
            auth_logger.exception(f"Error inesperado durante autenticación para usuario: {usuario}")

    def grupos(self):
        try:
            lista = [item.strip() for item in self.memberOf.split(",")] if self.memberOf else []
            lista_sin_duplicados = sorted(set(lista))
            diccionario = {}
            for item in lista_sin_duplicados:
                if '=' in item:
                    key, value = item.split('=', 1)
                    diccionario.setdefault(key, []).append(value)
            return diccionario
        except Exception:
            return {}

    @property
    def aDiccionario(self):
        return {
            'Nombre': self.givenName,
            'Apellidos': self.sn,
            'NombreMostrar': self.displayName,
            'Teléfono': self.telephoneNumber,
            'CorreoElectrónico': self.mail,
            'MiembroDe': self.grupos(),
            'Autentificado': self.autentificado,
            'Descripción': self.description,
            'Token': self.token
        }

    @property
    def aJson(self):
        return json.dumps(self.aDiccionario, ensure_ascii=False, indent=4)

    def __repr__(self):
        return f'< Usuario: {self.displayName}, Correo: {self.mail}, Telefono: {self.telephoneNumber}, Miembro de: {self.memberOf} >'
