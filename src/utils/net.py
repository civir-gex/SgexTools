import platform
import subprocess

def is_host_alive(ip: str) -> bool:
    try:
        system = platform.system().lower()
        if system == "windows":
            command = ["ping", "-n", "1", "-w", "1000", ip]
        else:
            command = ["ping", "-c", "1", "-W", "1", ip]

        result = subprocess.run(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return result.returncode == 0
    except Exception as e:
        print(f"[!] Error al hacer ping a {ip}: {e}")
        return False
