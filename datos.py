"""
Datos iniciales del sistema: pedidos y repartidores de ejemplo en Cusco.
"""

from modelos import Pedido, Repartidor

# ─────────────────────────────────────────────
# PEDIDOS DE EJEMPLO
# ─────────────────────────────────────────────
pedidos_iniciales = [
    Pedido(1, "Juan Quispe",     "CUSCO",        -13.5170, -71.9780, 5, 3.0,  80.0,  "Documentos urgentes"),
    Pedido(2, "María Ccoa",      "WANCHAQ",      -13.5226, -71.9673, 3, 5.0,  120.0, "Ropa y calzado"),
    Pedido(3, "Carlos Huanca",   "SANTIAGO",     -13.5319, -71.9810, 4, 8.0,  180.0, "Electrodoméstico pequeño"),
    Pedido(4, "Ana Mamani",      "SAN JERONIMO", -13.5442, -71.8865, 2, 12.0, 300.0, "Materiales de construcción"),
    Pedido(5, "Luis Ttito",      "SAN SEBASTIAN",-13.5310, -71.9070, 4, 7.0,  150.0, "Computadora"),
    Pedido(6, "Rosa Challco",    "CUSCO",        -13.5200, -71.9750, 5, 2.0,  50.0,  "Medicina urgente"),
    Pedido(7, "Pedro Condori",   "WANCHAQ",      -13.5250, -71.9650, 1, 15.0, 400.0, "Muebles"),
    Pedido(8, "Elena Vargas",    "SANTIAGO",     -13.5340, -71.9820, 3, 4.0,  100.0, "Abarrotes"),
    Pedido(9, "Marco Flores",    "SAN SEBASTIAN",-13.5290, -71.9050, 2, 6.0,  130.0, "Herramientas"),
    Pedido(10,"Sofía Ramos",     "SAN JERONIMO", -13.5460, -71.8900, 4, 9.0,  220.0, "Libros universitarios"),
]

# ─────────────────────────────────────────────
# REPARTIDORES DE EJEMPLO
# ─────────────────────────────────────────────
repartidores_iniciales = [
    Repartidor(1, "Diego Auccapuri", "CUSCO",        -13.5175, -71.9785, 20.0, "Moto"),
    Repartidor(2, "Yolanda Soto",    "WANCHAQ",      -13.5230, -71.9680, 15.0, "Moto"),
    Repartidor(3, "Raul Pumayalli",  "SANTIAGO",     -13.5325, -71.9815, 50.0, "Furgoneta"),
    Repartidor(4, "Carmen Cusi",     "SAN SEBASTIAN",-13.5300, -71.9060, 20.0, "Moto"),
]

# ─────────────────────────────────────────────
# GRAFO DE DISTRITOS DE CUSCO (para Backtracking)
# Nodos = distritos, aristas = conexiones viales
# ─────────────────────────────────────────────
GRAFO_DISTRITOS = {
    "CUSCO":        ["WANCHAQ", "SANTIAGO", "SAN SEBASTIAN", "CCORCA", "POROY"],
    "WANCHAQ":      ["CUSCO", "SANTIAGO", "SAN SEBASTIAN"],
    "SANTIAGO":     ["CUSCO", "WANCHAQ", "CCORCA", "SAYLLA"],
    "SAN SEBASTIAN":["CUSCO", "WANCHAQ", "SAN JERONIMO"],
    "SAN JERONIMO": ["SAN SEBASTIAN", "SAYLLA"],
    "SAYLLA":       ["SAN JERONIMO", "SANTIAGO"],
    "CCORCA":       ["CUSCO", "SANTIAGO"],
    "POROY":        ["CUSCO"],
}

# Coordenadas centrales de cada distrito (lat, lon)
CENTROS_DISTRITOS = {
    "CUSCO":         (-13.5170, -71.9780),
    "WANCHAQ":       (-13.5226, -71.9673),
    "SANTIAGO":      (-13.5340, -71.9820),
    "SAN SEBASTIAN": (-13.5300, -71.9070),
    "SAN JERONIMO":  (-13.5450, -71.8880),
    "SAYLLA":        (-13.5600, -71.8600),
    "CCORCA":        (-13.4900, -72.0400),
    "POROY":         (-13.4600, -72.0100),
}

# Colores para cada distrito en el mapa
COLORES_DISTRITOS = {
    "CUSCO":         "#E74C3C",  # Rojo
    "WANCHAQ":       "#3498DB",  # Azul
    "SANTIAGO":      "#2ECC71",  # Verde
    "SAN SEBASTIAN": "#F39C12",  # Naranja
    "SAN JERONIMO":  "#9B59B6",  # Púrpura
    "SAYLLA":        "#1ABC9C",  # Verde azulado
    "CCORCA":        "#E67E22",  # Naranja oscuro
    "POROY":         "#34495E",  # Gris azulado
}
