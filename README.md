# Sistema de Gestión de Rutas Óptimas – Cusco
**Universidad Nacional de San Antonio Abad del Cusco (UNSAAC)**  
Programación III — 2026

---

## Instalación

### 1. Requisitos
- Python 3.9 o superior
- pip actualizado

### 2. Instalar dependencias
```bash
pip install -r requirements.txt
```

Paquetes que se instalarán:
| Paquete | Uso |
|---|---|
| `customtkinter` | Interfaz gráfica moderna (dark mode) |
| `tkintermapview` | Mapa interactivo de Cusco con OpenStreetMap |
| `geopy` | Cálculo de distancias geodésicas reales |
| `requests` | Necesario para descargar tiles del mapa |
| `Pillow` | Procesamiento de imágenes del mapa |

### 3. Ejecutar
```bash
cd SISTEMARUTASCUSCO
python main.py
```

---

## Estructura del Proyecto
```
SISTEMARUTASCUSCO/
├── main.py                   # Punto de entrada
├── interfaz.py               # GUI principal (CustomTkinter + MapView)
├── modelos.py                # Clases Pedido y Repartidor
├── datos.py                  # Datos iniciales + grafo de distritos
├── greedy.py                 # Algoritmo Greedy (Vecino Más Cercano)
├── divide_venceras.py        # Divide y Vencerás (zonas GeoJSON)
├── dinamica.py               # Programación Dinámica (Knapsack 0/1)
├── backtracking.py           # Backtracking (rutas con restricciones)
├── busqueda_ordenamiento.py  # Búsqueda binaria + ordenamientos
├── mapa_cusco.geojson        # Polígonos oficiales de distritos de Cusco
└── requirements.txt
```

---

## Funcionalidades

### Gestión de Datos
- **Registrar pedidos** con coordenadas reales en el mapa
- **Registrar repartidores** con capacidad y vehículo
- **Buscar pedidos** por ID (búsqueda binaria O(log n)), cliente (lineal O(n)) o distrito
- **Ordenar pedidos** por prioridad, distancia o valor

### Algoritmos Implementados

#### ⚡ Greedy — Vecino Más Cercano
- Construye la ruta completa eligiendo siempre el pedido más cercano
- Asignación masiva: distribuye todos los pedidos a repartidores por prioridad + distancia
- Complejidad: O(n²)

#### 🔵 Divide y Vencerás — Zonas Distritales
- Usa el GeoJSON oficial para detectar en qué distrito está cada punto (ray-casting)
- Dibuja los 8 distritos de Cusco en el mapa con colores y bordes distintos
- Resuelve la ruta óptima local de cada zona independientemente
- Complejidad: O(n·v + k²)

#### 🟣 Programación Dinámica — Mochila 0/1
- Dado un repartidor, selecciona los pedidos que maximizan el valor total
- Sin superar la capacidad de carga en kg
- Muestra los pedidos seleccionados y la tabla DP
- Complejidad: O(n·W)

#### 🔴 Backtracking — Rutas con Restricciones
- Encuentra TODAS las rutas posibles entre dos distritos
- Permite bloquear distritos (calles cerradas, mantenimiento)
- Identifica y dibuja la ruta óptima (menor distancia km)
- Complejidad: O(d!) con podas por visitados + bloqueos

---

## Distritos de Cusco incluidos
- CUSCO (centro histórico)
- WANCHAQ
- SANTIAGO
- SAN SEBASTIÁN
- SAN JERÓNIMO
- SAYLLA
- CCORCA
- POROY
