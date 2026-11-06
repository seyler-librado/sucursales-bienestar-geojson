"""Paso 2: obtiene las sucursales (con coordenadas) de cada municipio.

Uso:
    python sucursales.py                      # todas las entidades
    python sucursales.py "TABASCO" "YUCATAN"  # solo algunas entidades
Genera data/listado_coordenadas.json
"""
import sys
import time

import requests

from config import (
    ARCHIVO_COORDENADAS,
    ARCHIVO_ESTADOS,
    ARCHIVO_MUNICIPIOS,
    buscar_sucursales,
    crear_sesion,
    guardar_json,
    leer_json,
    obtener_token,
)

PAUSA = 2  # segundos entre peticiones para no saturar el servidor


def parsear_sucursal(suc):
    """Convierte una sucursal del sitio en un dict con sus coordenadas."""
    liga = suc.get("liga") or ""
    latitud = longitud = None
    if "q=" in liga:
        partes = liga.split("q=")[1].split(",")
        if len(partes) >= 2:
            latitud, longitud = partes[0].strip(), partes[1].strip()
    return {
        "nombre": suc.get("nomSuc"),
        "localidad": suc.get("localidad"),
        "domicilio": suc.get("domicilio"),
        "latitud": latitud,
        "longitud": longitud,
        "liga": liga,
    }


def main():
    municipios = leer_json(ARCHIVO_MUNICIPIOS)
    claves = {e["descripcion"]: e["id_entidad"] for e in leer_json(ARCHIVO_ESTADOS)}

    if len(sys.argv) > 1:
        pedidas = sys.argv[1:]
        desconocidas = [p for p in pedidas if p not in municipios]
        if desconocidas:
            print(f"Aviso: entidades no encontradas: {desconocidas}", file=sys.stderr)
        municipios = {k: v for k, v in municipios.items() if k in pedidas}

    s, inicio = crear_sesion()
    token = obtener_token(inicio)

    datos_finales = {}
    for estado, lista_munis in municipios.items():
        clave = claves[estado]
        print(f"Scrapeando entidad: {estado} ({clave})")
        datos_finales[estado] = {}
        for muni in lista_munis:
            try:
                sucursales, r = buscar_sucursales(s, token, clave, muni)
            except requests.RequestException as e:
                print(f"  {muni}: error de red ({e})", file=sys.stderr)
                sucursales, r = None, None

            if sucursales is None:
                status = r.status_code if r is not None else "-"
                print(f"  {muni}: sin datos (status {status})")
                datos_finales[estado][muni] = []
            else:
                datos_finales[estado][muni] = [parsear_sucursal(suc) for suc in sucursales]
                print(f"  {muni}: {len(sucursales)} sucursal(es)")
            time.sleep(PAUSA)

        # Se guarda al terminar cada entidad para no perder avance si algo falla
        guardar_json(datos_finales, ARCHIVO_COORDENADAS)

    total = sum(len(v) for m in datos_finales.values() for v in m.values())
    print(f"Listo: {total} sucursales guardadas en {ARCHIVO_COORDENADAS}")


if __name__ == "__main__":
    main()
