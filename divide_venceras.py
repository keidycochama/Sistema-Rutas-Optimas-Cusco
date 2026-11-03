"""
Módulo Divide y Venceras: Segmentacion de la ciudad..

Estrategia:
    Divide el problema de rutas en sub-problemas más pequeños
    asignando cada pedido a su distrito (zona) real usando el
    GeoJSON de Cusco. Luego se resuelve la ruta óptima
    local de cada distrito de forma independiente.

Algoritmos:
1. asignar_distrito_geojson()  → Detecta a qué distrito pertenece un punto
2. dividir_por_distritos()     → Agrupa pedidos por su distrito real
3. ruta_optima_zona()          → Vecino mas cercano dentro de una zona
4. resolver_todas_zonas()      → Aplica DyV completo

Complejidad:
- Clasificación por punto en poligono: O(n * v) — n pedidos, v vértices promedio
- Ordenamiento interno de zona:         O(k² ) — k pedidos por zona
- Total:                                O(n * v + n²) ≈ O(n²) en la práctica
"""

import json
import os
from geopy.distance import geodesic

# Ruta al GeoJSON
_BASE = os.path.dirname(os.path.abspath(__file__))
_GEOJSON_PATH = os.path.join(_BASE, "mapa_cusco.geojson")

# CARGA DISTRITOS
def cargar_distritos():
    """
    Carga el GeoJSON de distritos.
    """
    with open(_GEOJSON_PATH, encoding="utf-8") as f:
        data = json.load(f)
    features_cusco = []
    for feature in data["features"]:
        dep = feature["properties"].get("NOMBDEP","").upper()
        if dep == "CUSCO":
            features_cusco.append(feature)
    return features_cusco
DISTRITOS = cargar_distritos()

# ALGORITMO PUNTO EN POLIGONO

def punto_en_poligono(lat: float, lon: float, coords: list) -> bool:
    dentro = False
    j = len(coords) - 1
    for i in range(len(coords)):
        xi, yi = coords[i][0], coords[i][1]
        xj, yj = coords[j][0], coords[j][1]
        intersecta = (
            ((yi > lat) != (yj > lat)) and
            (lon < (xj - xi) * (lat - yi) / (yj - yi + 0.0000001) + xi))
        if intersecta:
            dentro = not dentro
        j = i
    return dentro

def asignar_distrito_geojson(lat, lon):
    """
    Determina a cual distrito pertenece un pedido y devuelve el nombre del distrito
    """
    #Recorre todos los distritos 
    for feature in DISTRITOS:
        #Obtiene los nombres y su forma 
        nombre = feature["properties"].get("NOMBDIST","DESCONOCIDO")
        geometry = feature["geometry"]
        # poligono entonces obtiene coordenadas del borde y verifica que el pedido este dentro 
        if geometry["type"] == "Polygon":
            poligono = geometry["coordinates"][0]
            if punto_en_poligono(lat,lon,poligono):
                return nombre
        # Distritos con varias partes separadas 
        elif geometry["type"] == "MultiPolygon":
            #Recorre cada parte
            for parte in geometry["coordinates"]:
                #Obtiene coordenadas 
                poligono = parte[0]
                #Verifica si pertenece y retorna el nombre 
                if punto_en_poligono(lat,lon,poligono):
                    return nombre
    return "FUERA DE CUSCO"

#DIVIDE Y VENCERAS
def dividir_por_distritos(pedidos):
    """DIVIDE: Agrupa pedidos en zonas (distritos) según su ubicación real.
    Complejidad: O(n * d * v)"""
    zonas = {}
    #Recorre pedidos 
    for pedido in pedidos:
        # Detectar distrito según sus coordenadas
        distrito = asignar_distrito_geojson(pedido.latitud,pedido.longitud)
        pedido.distrito = distrito
        #Si el distrito no existe se crea una lista vacia y se agrega el nuevo pedido ahi 
        if distrito not in zonas:
            zonas[distrito] = []
        zonas[distrito].append(pedido)
    return zonas

# VENCER
#Calcula ruta local dentro de una zona
def ruta_optima_zona(centro_zona,pedidos_zona):
    """
    VENCER: Resuelve la ruta óptima local de una zona usando el heurístico Vecino Más Cercano.
    Complejidad: O(k²) — k = pedidos en la zona.
    """
    if not pedidos_zona:
        return [], 0.0

    pendientes = pedidos_zona[:]
    ruta = []
    #empieza desde el centro del distrito 
    posicion_actual = centro_zona
    #acumulador de distancia 
    distancia_total = 0.0
    while pendientes:
        mejor_pedido = None
        mejor_distancia = float("inf")
        # Buscar pedido más cercano
        for pedido in pendientes:
            distancia = geodesic(posicion_actual,(pedido.latitud,pedido.longitud)).km
            #Si encuentra uno mas cercano se actualiza la mejor opcion 
            if distancia < mejor_distancia:
                mejor_distancia = distancia
                mejor_pedido = pedido
        #agrega pedido a la ruta y se suma 
        ruta.append(mejor_pedido)
        distancia_total += mejor_distancia
        posicion_actual = (mejor_pedido.latitud,mejor_pedido.longitud)
        pendientes.remove(mejor_pedido)
    return ruta, round(distancia_total, 2)
    
#combinar
def resolver_todas_zonas(pedidos,centros):
    """ Une Divide y vencecras    """
    # 1. Divide la ciudad
    zonas = dividir_por_distritos(pedidos)
    resultado = {}
    for distrito, lista_pedidos in zonas.items():
        centro = centros.get(distrito, (-13.5170, -71.9780))
        # 2. VENCER: calcula la ruta local 
        ruta, dist_total = ruta_optima_zona(centro, lista_pedidos)
        # 3. COMBINAR: guarda los resultados or distrito 
        resultado[distrito] = {"pedidos": lista_pedidos,"ruta": ruta,"distancia_total": dist_total}
    return resultado


def obtener_poligonos_distritos():
    """Devuelve los polígonos GeoJSON de cada distrito de Cusco para dibujarlos en el mapa con colores."""
    resultado = {}
    for feature in DISTRITOS:
        nombre = feature["properties"].get("NOMBDIST", "?")
        geometry = feature["geometry"]
        lista_poligonos = []
        # poligono entonces obtiene coordenadas del borde y verifica que el pedido este dentro
        if geometry["type"] == "Polygon":
            coords = geometry["coordinates"][0]
            poligono = [(c[1], c[0])for c in coords]
            lista_poligonos.append(poligono)

        # Distritos con varias partes separadas 
        elif geometry["type"] == "MultiPolygon":
            for parte in geometry["coordinates"]:
                coords = parte[0]
                poligono = [(c[1], c[0]) for c in coords]
                lista_poligonos.append(poligono)
        resultado[nombre] = lista_poligonos

    return resultado
        
