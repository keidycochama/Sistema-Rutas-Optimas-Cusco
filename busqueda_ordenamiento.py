"""
Módulo de búsqueda y ordenamiento.

Complejidades:
- ordenar_por_prioridad:  O(n log n)  — Timsort de Python
- ordenar_por_distancia:  O(n log n)  — Timsort de Python
- busqueda_binaria:       O(log n)    — búsqueda binaria clásica
- busqueda_lineal:        O(n)        — búsqueda por nombre/distrito
"""

from geopy.distance import geodesic


# ─────────────────────────────────────────────────────────
# ORDENAMIENTO
# ─────────────────────────────────────────────────────────

def ordenar_por_prioridad(lista: list) -> list:
    """
    Ordena pedidos de mayor a menor prioridad.
    Complejidad: O(n log n)
    """
    return sorted(lista, key=lambda x: x.prioridad, reverse=True)


def ordenar_por_distancia(lista: list, origen: tuple) -> list:
    """
    Ordena pedidos por distancia geodésica desde un origen (lat, lon).
    Complejidad: O(n log n)
    """
    return sorted(
        lista,
        key=lambda p: geodesic(origen, (p.latitud, p.longitud)).km
    )


def ordenar_por_valor(lista: list) -> list:
    """
    Ordena pedidos de mayor a menor valor económico.
    Complejidad: O(n log n)
    """
    return sorted(lista, key=lambda x: x.valor, reverse=True)


def ordenar_por_peso(lista: list) -> list:
    """
    Ordena pedidos de menor a mayor peso.
    Complejidad: O(n log n)
    """
    return sorted(lista, key=lambda x: x.peso)


# ─────────────────────────────────────────────────────────
# BÚSQUEDA
# ─────────────────────────────────────────────────────────

def busqueda_binaria_id(lista: list, objetivo_id: int):
    """
    Búsqueda binaria por ID de pedido (requiere lista ordenada por ID).
    Complejidad: O(log n)
    Retorna: Pedido | None
    """
    lista_ordenada = sorted(lista, key=lambda p: p.id_pedido)
    izquierda, derecha = 0, len(lista_ordenada) - 1

    while izquierda <= derecha:
        medio = (izquierda + derecha) // 2
        if lista_ordenada[medio].id_pedido == objetivo_id:
            return lista_ordenada[medio]
        elif lista_ordenada[medio].id_pedido < objetivo_id:
            izquierda = medio + 1
        else:
            derecha = medio - 1
    return None


def busqueda_lineal_cliente(lista: list, nombre: str) -> list:
    """
    Búsqueda lineal por nombre de cliente (parcial, insensible a mayúsculas).
    Complejidad: O(n)
    """
    nombre = nombre.lower()
    return [p for p in lista if nombre in p.cliente.lower()]


def busqueda_por_distrito(lista: list, distrito: str) -> list:
    """
    Filtra pedidos por distrito.
    Complejidad: O(n)
    """
    distrito = distrito.upper()
    return [p for p in lista if p.distrito.upper() == distrito]


def busqueda_repartidor_id(lista: list, objetivo_id: int):
    """
    Búsqueda binaria de repartidor por ID.
    Complejidad: O(log n)
    """
    lista_ord = sorted(lista, key=lambda r: r.id_repartidor)
    izq, der = 0, len(lista_ord) - 1
    while izq <= der:
        mid = (izq + der) // 2
        if lista_ord[mid].id_repartidor == objetivo_id:
            return lista_ord[mid]
        elif lista_ord[mid].id_repartidor < objetivo_id:
            izq = mid + 1
        else:
            der = mid - 1
    return None
