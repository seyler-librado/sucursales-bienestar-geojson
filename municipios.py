"""Paso 1: descarga la lista de municipios de cada entidad.

Uso: python municipios.py
Genera data/listado_municipios.json
"""
import time

from config import (
    ARCHIVO_ESTADOS,
    ARCHIVO_MUNICIPIOS,
    TIMEOUT,
    URL_MUNICIPIOS,
    crear_sesion,
    guardar_json,
    leer_json,
)

PAUSA = 5  # segundos entre peticiones para no saturar el servidor


def main():
    s, _ = crear_sesion()
    json_municipios = {}

    for e in leer_json(ARCHIVO_ESTADOS):
        nombre, clave = e["descripcion"], e["id_entidad"]
        r = s.post(URL_MUNICIPIOS, data={"idEnt": clave}, timeout=TIMEOUT)
        r.raise_for_status()
        municipios = r.json()["response"]
        json_municipios[nombre] = [m["munalc"] for m in municipios]
        print(f"{nombre} ({clave}): {len(municipios)} municipios")
        time.sleep(PAUSA)

    guardar_json(json_municipios, ARCHIVO_MUNICIPIOS)
    print(f"Guardado en {ARCHIVO_MUNICIPIOS}")


if __name__ == "__main__":
    main()
