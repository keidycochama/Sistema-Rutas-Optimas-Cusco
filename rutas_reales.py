import json
from urllib.request import urlopen
from urllib.parse import urlencode


def ruta_por_calles(puntos: list, perfil: str = "driving") -> tuple:
    """
    Convierte puntos [(lat, lon), ...] en una ruta real por calles usando OSRM.
    Devuelve coordenadas listas para TkinterMapView.
    """
    if len(puntos) < 2:
        return puntos, 0.0

    try:
        coordenadas = ";".join(
            f"{lon},{lat}" for lat, lon in puntos
        )

        parametros = urlencode({
            "overview": "full",
            "geometries": "geojson",
            "steps": "false"
        })

        url = f"https://router.project-osrm.org/route/v1/{perfil}/{coordenadas}?{parametros}"

        with urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))

        if data.get("code") != "Ok" or not data.get("routes"):
            return puntos, 0.0

        ruta = data["routes"][0]

        puntos_por_calles = [
            (lat, lon)
            for lon, lat in ruta["geometry"]["coordinates"]
        ]

        distancia_km = ruta["distance"] / 1000

        return puntos_por_calles, distancia_km

    except Exception as ex:
        print("Error calculando ruta por calles:", ex)
        return puntos, 0.0