"""
Modelos de datos del sistema de rutas de Cusco.
"""


class Pedido:
    """Representa un pedido de entrega."""

    def __init__(
            self,
            id_pedido: int,
            cliente: str,
            distrito: str,
            latitud: float,
            longitud: float,
            prioridad: int,
            peso: float,
            valor: float,
            descripcion: str = ""):

        self.id_pedido = id_pedido
        self.cliente = cliente
        self.distrito = distrito
        self.latitud = latitud
        self.longitud = longitud
        self.prioridad = prioridad      # 1-5 (5 = máxima urgencia)
        self.peso = peso                # kg
        self.valor = valor              # soles
        self.descripcion = descripcion
        self.entregado = False

    def __str__(self):
        return f"#{self.id_pedido} - {self.cliente} ({self.distrito})"

    def to_dict(self):
        return {
            "id_pedido": self.id_pedido,
            "cliente": self.cliente,
            "distrito": self.distrito,
            "latitud": self.latitud,
            "longitud": self.longitud,
            "prioridad": self.prioridad,
            "peso": self.peso,
            "valor": self.valor,
            "descripcion": self.descripcion,
            "entregado": self.entregado
        }


class Repartidor:
    """Representa un repartidor del sistema."""

    def __init__(
            self,
            id_repartidor: int,
            nombre: str,
            distrito: str,
            latitud: float,
            longitud: float,
            capacidad_kg: float,
            vehiculo: str = "Moto"):

        self.id_repartidor = id_repartidor
        self.nombre = nombre
        self.distrito = distrito
        self.latitud = latitud
        self.longitud = longitud
        self.capacidad_kg = capacidad_kg
        self.vehiculo = vehiculo
        self.pedidos_asignados = []

    def __str__(self):
        return f"{self.nombre} ({self.distrito})"

    def to_dict(self):
        return {
            "id_repartidor": self.id_repartidor,
            "nombre": self.nombre,
            "distrito": self.distrito,
            "latitud": self.latitud,
            "longitud": self.longitud,
            "capacidad_kg": self.capacidad_kg,
            "vehiculo": self.vehiculo
        }
