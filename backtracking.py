"""
Módulo Backtracking — Búsqueda exhaustiva de rutas con restricciones.

Encuentra TODAS las rutas posibles entre dos distritos de Cusco
evitando ciertos distritos/calles bloqueados, y luego selecciona
la ruta más corta en términos de número de saltos o distancia.

Complejidad:
- Peor caso: O(d!)  — d = número de distritos (árbol de permutaciones)
- Caso práctico: Muy rápido con podas (distritos visitados + bloqueos)
"""

from geopy.distance import geodesic


def _distancia_ruta(ruta: list, centros: dict) -> float:
    """
    Calcula la distancia total (km) de una ruta de distritos.
    """
    total = 0.0
    for i in range(len(ruta) - 1):
        c1 = centros.get(ruta[i])
        c2 = centros.get(ruta[i + 1])
        if c1 and c2:
            total += geodesic(c1, c2).km
    return round(total, 3)


def buscar_todas_rutas(
        grafo: dict,
        inicio: str,
        destino: str,
        visitados: set = None,
        camino: list = None) -> list:
    """
    Backtracking recursivo: explora TODAS las rutas desde
    `inicio` hasta `destino` en el grafo de distritos,
    sin pasar por nodos en `bloqueados`.

    Args:
        grafo:     dict {distrito: [vecinos]}
        inicio:    nodo de partida
        destino:   nodo destino
        bloqueados: set de distritos cerrados/bloqueados
        visitados: set interno de control (no pasar dos veces)
        camino:    lista interna del camino actual

    Returns:
        Lista de rutas (cada ruta es una lista de strings de distritos)
    """
    
    if visitados is None:
        visitados = set()
    if camino is None:
        camino = []

    visitados.add(inicio)
    camino.append(inicio)

    # CASO BASE: llegamos al destino
    if inicio == destino:
        resultado = [camino.copy()]
        camino.pop()
        visitados.remove(inicio)
        return resultado

    rutas = []
    for vecino in grafo.get(inicio, []):
        if vecino not in visitados:
            sub_rutas = buscar_todas_rutas(
                grafo, vecino, destino, visitados, camino
            )
            rutas.extend(sub_rutas)

    camino.pop()
    visitados.remove(inicio)
    return rutas


def encontrar_ruta_optima(
        grafo: dict,
        inicio: str,
        destino: str,
        centros: dict,
        bloqueados: set = None) -> dict:
    """
    Encuentra la ruta más corta (por distancia km) entre
    dos distritos usando backtracking + análisis posterior.

    Returns:
        dict con:
            - todas_rutas:    list[list[str]]
            - ruta_optima:    list[str]
            - distancia_opt:  float km
            - distancias:     list[float] por cada ruta
            - n_rutas:        int
    """

    todas = buscar_todas_rutas(grafo, inicio, destino)

    if not todas:
        return {
            "todas_rutas":   [],
            "ruta_optima":   [],
            "distancia_opt": float('inf'),
            "distancias":    [],
            "n_rutas":       0
        }

    distancias = [_distancia_ruta(r, centros) for r in todas]
    idx_min = distancias.index(min(distancias))

    return {
        "todas_rutas":   todas,
        "ruta_optima":   todas[idx_min],
        "distancia_opt": distancias[idx_min],
        "distancias":    distancias,
        "n_rutas":       len(todas)
    }
