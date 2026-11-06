"""Configuración y utilidades compartidas por todos los scripts."""
import json
import os
from pathlib import Path

import requests
from bs4 import BeautifulSoup

# Rutas absolutas: los scripts funcionan sin importar desde qué carpeta se ejecuten
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
ARCHIVO_ESTADOS = DATA_DIR / "estados.json"
ARCHIVO_MUNICIPIOS = DATA_DIR / "listado_municipios.json"
ARCHIVO_COORDENADAS = DATA_DIR / "listado_coordenadas.json"
ARCHIVO_GEOJSON = BASE_DIR / "salida.geojson"

# URLs públicas del directorio de sucursales
URL_BASE = "https://directoriodesucursales.bancodelbienestar.gob.mx"
URL_INICIO = f"{URL_BASE}/"
URL_MUNICIPIOS = f"{URL_BASE}/Home/ListarMunalc"
URL_BUSQUEDA = f"{URL_BASE}/Busqueda"

TIMEOUT = 30  # segundos por petición

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/155.0.0.0 Safari/537.36"
    ),
    "Referer": URL_INICIO,
    "Origin": URL_BASE,
}


def crear_sesion():
    """Crea una sesión con los headers y obtiene las cookies de la página de inicio.

    Regresa (sesion, respuesta_de_inicio).
    """
    s = requests.Session()
    s.headers.update(HEADERS)
    r = s.get(URL_INICIO, timeout=TIMEOUT)
    r.raise_for_status()
    return s, r


def obtener_token(respuesta_inicio):
    """Extrae el token antiforgery del HTML de la página de inicio."""
    soup = BeautifulSoup(respuesta_inicio.content, "html.parser")
    token_input = soup.find("input", {"name": "__RequestVerificationToken"})
    if token_input is None:
        raise SystemExit("No encontré el token en la página de inicio; revisa URL_INICIO en config.py")
    return token_input["value"]


def buscar_sucursales(s, token, clave_entidad, municipio):
    """Hace la búsqueda de un municipio.

    Regresa (lista_de_sucursales | None, respuesta). None si la página no trajo datos.
    """
    r = s.post(
        URL_BUSQUEDA,
        data={
            "entidades": clave_entidad,
            "entidad": clave_entidad,
            "munalc": municipio,
            "__RequestVerificationToken": token,
        },
        timeout=TIMEOUT,
    )
    soup = BeautifulSoup(r.content, "html.parser")
    data_suc = soup.find("div", {"id": "dataSuc"})
    if data_suc is None or not data_suc.get("data-sucursales"):
        return None, r
    info = json.loads(data_suc["data-sucursales"])
    return info.get("response") or [], r


def leer_json(ruta):
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)


def guardar_json(datos, ruta, indent=4):
    """Guarda de forma segura: escribe a un temporal y luego lo reemplaza.

    Así, si el script se interrumpe a mitad de la escritura, no se corrompe el archivo.
    """
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    temporal = ruta.with_suffix(ruta.suffix + ".tmp")
    with open(temporal, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=indent)
    try:
        os.replace(temporal, ruta)
    except PermissionError:
        # Windows no deja reemplazar un archivo abierto en otro programa (p. ej. QGIS);
        # en ese caso se sobrescribe directamente su contenido.
        with open(ruta, "wb") as f:
            f.write(temporal.read_bytes())
        temporal.unlink()
