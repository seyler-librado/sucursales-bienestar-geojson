"""Paso 3: convierte el listado de coordenadas a GeoJSON.

Uso:
    python convertir_geojson.py                       # rutas por defecto
    python convertir_geojson.py entrada.json salida.geojson
"""
import sys

from config import ARCHIVO_COORDENADAS, ARCHIVO_GEOJSON, guardar_json, leer_json


def convertir(datos):
    features = []
    for estado, municipios in datos.items():
        for municipio, puntos in municipios.items():
            for p in puntos:
                try:
                    lat = float(p["latitud"])
                    lon = float(p["longitud"])
                except (KeyError, ValueError, TypeError):
                    print(f"Se omite (coordenadas inválidas): {p.get('nombre')}", file=sys.stderr)
                    continue

                # Todo lo que no sea coordenada pasa a "properties"
                propiedades = {k: v for k, v in p.items() if k not in ("latitud", "longitud")}
                propiedades["estado"] = estado
                propiedades["municipio"] = municipio

                features.append({
                    "type": "Feature",
                    # OJO: GeoJSON usa el orden [longitud, latitud]
                    "geometry": {"type": "Point", "coordinates": [lon, lat]},
                    "properties": propiedades,
                })

    return {"type": "FeatureCollection", "features": features}


def main():
    entrada = sys.argv[1] if len(sys.argv) > 1 else ARCHIVO_COORDENADAS
    salida = sys.argv[2] if len(sys.argv) > 2 else ARCHIVO_GEOJSON

    geojson = convertir(leer_json(entrada))
    guardar_json(geojson, salida, indent=2)
    print(f"{len(geojson['features'])} puntos guardados en {salida}")


if __name__ == "__main__":
    main()
