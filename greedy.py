"""
Módulo Greedy (Voraz) — Asignación y ruteo óptimo local.

Algoritmos implementados:
1. pedido_mas_cercano(origen, pedidos)  → Pedido más próximo desde un punto
2. ruta_greedy_completa(origen, pedidos) → Ruta completa por vecino más cercano (NN Heuristic)
3. asignar_repartidor_greedy(repartidores, pedido) → Repartidor más cercano al pedido

Complejidad:
- pedido_mas_cercano:        O(n)
- ruta_greedy_completa:      O(n²)
- asignar_repartidor_greedy: O(r) donde r = nro. de repartidores
"""

from geopy.distance import geodesic


def pedido_mas_cercano(origen: tuple, pedidos: list):
    """
    Encuentra el pedido más cercano a un punto de origen.
    Complejidad: O(n)

    Args:
        origen: Tupla (latitud, longitud) del punto de partida.
        pedidos: Lista de objetos Pedido no entregados.

    Returns:
        (Pedido, distancia_km) o (None, inf) si no hay pedidos.
    """
    mejor_pedido = None
    mejor_distancia = float('inf')

    for pedido in pedidos:
        if pedido.entregado:
            continue
        distancia = geodesic(origen, (pedido.latitud, pedido.longitud)).km
        if distancia < mejor_distancia:
            mejor_distancia = distancia
            mejor_pedido = pedido

    return mejor_pedido, mejor_distancia


def ruta_greedy_completa(origen: tuple, pedidos: list) -> list:
    """
    Construye una ruta completa de entrega usando el heurístico
    del Vecino Más Cercano (Nearest Neighbor).

    En cada paso se elige el pedido no visitado más próximo
    a la posición actual del repartidor — decisión localmente
    óptima pero no necesariamente globalmente óptima.

    Complejidad: O(n²)

    Args:
        origen: Tupla (lat, lon) de inicio del repartidor.
        pedidos: Lista de Pedidos a entregar.

    Returns:
        Lista ordenada de tuplas:
        [(pedido, distancia_desde_anterior_km), ...]
    """
    pendientes=[]
    for p in pedidos:
        if not p.entregado:
            pendientes.append(p)
    ruta = []
    pos_actual = origen
    distancia_total = 0.0
    #--- Mientras queden pedidos por entregar...
    while pendientes:
        # 1. Encontrar el pedido mas cercano a la posicion actual
        pedido_cercano, dist = pedido_mas_cercano(pos_actual, pendientes)
        #---Si no hay pedidos cercanos (todos entregados o lista vacia),terminamos
        if pedido_cercano is None:
            break
        # 2.Agregarlo a la ruta y actualizar la posicion actual
        ruta.append((pedido_cercano, dist))
        distancia_total += dist
        # 3.Actualizar la posicion actual
        pos_actual = (pedido_cercano.latitud, pedido_cercano.longitud)
        # 4.Eliminarlo de los pendientes para no volver a visitarlo
        pendientes.remove(pedido_cercano)

    return ruta, distancia_total


def asignar_repartidor_greedy(repartidores: list, pedido) -> tuple:
    """
    Asigna el repartidor más cercano al pedido (greedy de asignación).
    Respeta la restricción de capacidad del repartidor.

    Complejidad: O(r) — r = número de repartidores.

    Returns:
        (Repartidor, distancia_km) o (None, inf) si no hay disponibles.
    """
    mejor_repartidor = None
    mejor_distancia = float('inf')
    #--- Para cada repartidor, verificamos si tiene capacidad y calculamos la distancia al pedido
    for rep in repartidores:
        # Calculamos el peso ya cargado por el repartidor para verificar capacidad
        peso_ya_cargado = 0.0
        for p in rep.pedidos_asignados:
            peso_ya_cargado += p.peso
        # Verificamos si el repartidor tiene capacidad para el nuevo pedido
        capacidad_libre = rep.capacidad_kg - peso_ya_cargado
        # Si el repartidor tiene capacidad, calculamos la distancia al pedido
        if pedido.peso <= capacidad_libre:
            # Calculamos la distancia entre el repartidor y el pedido
            dist = geodesic((rep.latitud, rep.longitud), (pedido.latitud, pedido.longitud)).km
            # Si esta distancia es menor que la mejor distancia encontrada 
            # hasta ahora, actualizamos el mejor repartidor y la mejor distancia
            if dist < mejor_distancia:
                mejor_distancia = dist
                mejor_repartidor = rep
    return mejor_repartidor, mejor_distancia