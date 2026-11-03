
import tkinter as tk
from tkinter import messagebox, ttk
import customtkinter as ctk
from tkintermapview import TkinterMapView
import json, os
from urllib.parse import urlencode
from urllib.request import urlopen
from geopy.distance import geodesic
from rutas_reales import ruta_por_calles
from datos import (
    pedidos_iniciales, repartidores_iniciales,
    CENTROS_DISTRITOS, COLORES_DISTRITOS, GRAFO_DISTRITOS
)
from modelos import Pedido, Repartidor
from greedy import ruta_greedy_completa, asignar_repartidor_greedy
from divide_venceras import (
    resolver_todas_zonas, obtener_poligonos_distritos, ruta_optima_zona
)


from dinamica import mochila_tabla
from backtracking import encontrar_ruta_optima
from busqueda_ordenamiento import (
    ordenar_por_prioridad, ordenar_por_distancia, ordenar_por_valor,
    busqueda_binaria_id, busqueda_lineal_cliente, busqueda_por_distrito,
    busqueda_repartidor_id
)

# ─── Tema ───────────────────────────────────────────────
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

DARK_BG   = "#f0f2f5"
PANEL_BG  = "#e2e8f0"
CARD_BG   = "#ffffff"
ACCENT    = "#4f46e5"
TEXT_W    = "#1e293b"
TEXT_G    = "#475569"
GREEN     = "#059669"
ORANGE    = "#d97706"
PURPLE    = "#7c3aed"

def ruta_por_calles(puntos: list, perfil: str = "driving") -> tuple:
    """
    Convierte puntos [(lat, lon), ...] en una ruta real por calles usando OSRM.
    Si no hay internet o OSRM falla, devuelve los puntos originales.
    """
    if len(puntos) < 2:
        return puntos, 0.0

    try:
        coordenadas = ";".join(f"{lon},{lat}" for lat, lon in puntos)

        parametros = urlencode({
            "overview": "full",
            "geometries": "geojson",
            "steps": "false",
        })

        url = (
            f"https://router.project-osrm.org/route/v1/"
            f"{perfil}/{coordenadas}?{parametros}"
        )

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
# ════════════════════════════════════════════════════════
#  VENTANA PRINCIPAL
# ════════════════════════════════════════════════════════

class App(ctk.CTk):

    def __init__(self):
        super().__init__()
        self.title("Sistema de Rutas Óptimas – Cusco  |  Programación III UNSAAC")
        self.geometry("1600x950")
        self.configure(fg_color=PANEL_BG)
        self.resizable(True, True)

        # Estado global
        self.pedidos     = list(pedidos_iniciales)
        self.repartidores= list(repartidores_iniciales)
        self._markers    = []
        self._paths      = []
        self._polygons   = []

        self._build_ui()
        self._refresh_pedidos_list()
        self._refresh_repartidores_list()
        self._draw_all_markers()

    # ────────────────────────────────────────────────────
    # CONSTRUCCIÓN DE LA UI
    # ────────────────────────────────────────────────────

    def _build_ui(self):
        # ── Barra superior ──────────────────────────────
        top = ctk.CTkFrame(self, fg_color=PANEL_BG, height=56, corner_radius=0)
        top.pack(fill="x", side="top")
        ctk.CTkLabel(
            top,
            text="  SISTEMA DE GESTIÓN DE RUTAS ÓPTIMAS – CUSCO",
            font=ctk.CTkFont("Segoe UI", 18, "bold"),
            text_color=ACCENT
        ).pack(side="left", padx=20, pady=10)
        ctk.CTkLabel(
            top,
            text=" Programación III",
            font=ctk.CTkFont("Arial", 12),
            text_color=TEXT_G
        ).pack(side="right", padx=20)

        # ── Contenedor principal ─────────────────────────
        main = ctk.CTkFrame(self, fg_color=PANEL_BG, corner_radius=0)
        main.pack(fill="both", expand=True)

        # Panel lateral izquierdo (360 px fijo)
        self.sidebar = ctk.CTkScrollableFrame(
            main, width=360, fg_color=PANEL_BG, corner_radius=0
        )
        self.sidebar.pack(side="left", fill="y", padx=(8, 4), pady=8)

        # Mapa (resto del espacio)
        map_frame = ctk.CTkFrame(main, fg_color=DARK_BG, corner_radius=8)
        map_frame.pack(side="right", fill="both", expand=True, padx=(4, 8), pady=8)

        self.mapa = TkinterMapView(map_frame, corner_radius=8)
        self.mapa.pack(fill="both", expand=True)
        self.mapa.set_position(-13.5319, -71.9675)
        self.mapa.set_zoom(12)
        self.mapa.set_tile_server(
            "https://a.tile.openstreetmap.org/{z}/{x}/{y}.png"
        )

        self._build_sidebar()
    # ────────────────────────────────────────────────────
    # SIDEBAR
    # ────────────────────────────────────────────────────
    def _build_sidebar(self):
        sb = self.sidebar

        def section(title, color=ACCENT):
            ctk.CTkLabel(
                sb, text=title,
                font=ctk.CTkFont("Segoe UI", 13, "bold"),
                text_color=color
            ).pack(fill="x", padx=4, pady=(14, 2))
            ctk.CTkFrame(sb, height=1, fg_color=color).pack(fill="x", padx=4)

        def btn(parent, text, cmd, color=ACCENT):
            ctk.CTkButton(
                parent, text=text, command=cmd,
                fg_color=color, hover_color="#A29E94DF" if color == ACCENT else None,
                font=ctk.CTkFont("Segoe UI", 12, "bold"),
                height=40, corner_radius=14
            ).pack(fill="x", padx=4, pady=3)

        # ── Registros ──────────────────────────────────
        section("  GESTIÓN DE DATOS")
        btn(sb, "  Registrar Pedido",     self._form_pedido,    "#27ae60")
        btn(sb, "  Registrar Repartidor", self._form_repartidor,"#2980b9")
        btn(sb, "  Buscar Pedido",        self._buscar_pedido,  "#8e44ad")
        btn(sb, "  Limpiar Mapa",         self._limpiar_mapa,   "#7f8c8d")

        # ── Lista pedidos ───────────────────────────────
        section("  PEDIDOS REGISTRADOS", TEXT_G)
        self.frame_lista_p = ctk.CTkFrame(sb, fg_color=CARD_BG, corner_radius=8)
        self.frame_lista_p.pack(fill="x", padx=4, pady=4)

        # Cabecera de la tabla pedidos
        hdr = ctk.CTkFrame(self.frame_lista_p, fg_color="#dbeafe", corner_radius=4)
        hdr.pack(fill="x", padx=2, pady=2)
        for txt, w in [("#", 3), ("Cliente", 14), ("Distrito", 12), ("Pri", 3), ("Kg", 4)]:
            ctk.CTkLabel(hdr, text=txt, width=w*7,
                         font=ctk.CTkFont("Segoe UI", 10, "bold"),
                         text_color=TEXT_G).pack(side="left", padx=2)

        self.lista_pedidos_frame = ctk.CTkScrollableFrame(
            self.frame_lista_p, height=170, fg_color=CARD_BG, corner_radius=0
        )
        self.lista_pedidos_frame.pack(fill="x")

        # Botones ordenar
        ord_f = ctk.CTkFrame(sb, fg_color="transparent")
        ord_f.pack(fill="x", padx=4, pady=2)
        ctk.CTkLabel(ord_f, text="Ordenar:", font=ctk.CTkFont("Segoe UI", 11),
                     text_color=TEXT_G).pack(side="left")
        for txt, cmd in [("Prioridad", lambda: self._ordenar("prioridad")),
                         ("Distancia", lambda: self._ordenar("distancia")),
                         ("Valor",     lambda: self._ordenar("valor"))]:
            ctk.CTkButton(ord_f, text=txt, width=78, height=26,
                          font=ctk.CTkFont("Arial", 10),
                          command=cmd, corner_radius=6).pack(side="left", padx=2)

        # ── Lista repartidores ──────────────────────────
        section("  REPARTIDORES", "#98b7cd")
        self.frame_lista_r = ctk.CTkFrame(sb, fg_color=CARD_BG, corner_radius=8)
        self.frame_lista_r.pack(fill="x", padx=4, pady=4)
        self.lista_rep_frame = ctk.CTkScrollableFrame(
            self.frame_lista_r, height=120, fg_color=CARD_BG, corner_radius=0
        )
        self.lista_rep_frame.pack(fill="x")

        # ── Algoritmos ─────────────────────────────────
        section("  ALGORITMOS")

        btn(sb, "  Greedy — Ruta completa",
            self._ejecutar_greedy, "#16a085")

        btn(sb, "  Divide y Vencerás — Zonas",
            self._ejecutar_divide, "#2471a3")

        btn(sb, "  Prog. Dinámica — Mochila",
            self._ejecutar_mochila, "#7d3c98")

        btn(sb, "  Backtracking — Rutas",
            self._form_backtracking, ACCENT)


        # ── Consola de resultados ───────────────────────
        section("  RESULTADOS", GREEN)
        self.consola = ctk.CTkTextbox(
            sb, height=220, font=ctk.CTkFont("Courier", 11),
            fg_color="#f8fafc", text_color="#1e293b",
            corner_radius=6
        )
        self.consola.pack(fill="x", padx=4, pady=4)
        self._log("Sistema iniciado correctamente ✓")
        self._log(f"Pedidos cargados: {len(self.pedidos)}")
        self._log(f"Repartidores: {len(self.repartidores)}")

    # ────────────────────────────────────────────────────
    # HELPERS UI
    # ────────────────────────────────────────────────────

    def _log(self, msg: str):
        self.consola.configure(state="normal")
        self.consola.insert("end", msg + "\n")
        self.consola.see("end")
        self.consola.configure(state="disabled")

    def _limpiar_mapa(self):
        for m in self._markers:
            try: m.delete()
            except: pass
        for p in self._paths:
            try: p.delete()
            except: pass
        for pg in self._polygons:
            try: pg.delete()
            except: pass
        self._markers.clear()
        self._paths.clear()
        self._polygons.clear()
        self._draw_all_markers()
        self._log("Mapa limpiado.")

    def _draw_all_markers(self):
        for p in self.pedidos:
            mk = self.mapa.set_marker(
                p.latitud, p.longitud,
                text=f"#{p.id_pedido} {p.cliente}",
                marker_color_circle=ACCENT,
                marker_color_outside=ACCENT
            )
            self._markers.append(mk)
        for r in self.repartidores:
            mk = self.mapa.set_marker(
                r.latitud, r.longitud,
                text=f"🚴 {r.nombre}",
                marker_color_circle="#3498db",
                marker_color_outside="#3498db"
            )
            self._markers.append(mk)

    def _refresh_pedidos_list(self):
        for w in self.lista_pedidos_frame.winfo_children():
            w.destroy()
        colores_prioridad = {5:"#e74c3c",4:"#e67e22",3:"#f1c40f",2:"#2ecc71",1:"#95a5a6"}
        for p in self.pedidos:
            row = ctk.CTkFrame(self.lista_pedidos_frame,
                               fg_color="#f1f5f9", corner_radius=4)
            row.pack(fill="x", padx=2, pady=1)
            col_p = colores_prioridad.get(p.prioridad, TEXT_G)
            for txt, w in [
                (str(p.id_pedido), 21), (p.cliente[:14], 98),
                (p.distrito[:12], 84), (str(p.prioridad), 21),
                (f"{p.peso:.0f}", 28)
            ]:
                ctk.CTkLabel(row, text=txt, width=w,
                             font=ctk.CTkFont("Arial", 10),
                             text_color=col_p if txt==str(p.prioridad) else TEXT_W
                             ).pack(side="left", padx=1)

    def _refresh_repartidores_list(self):
        for w in self.lista_rep_frame.winfo_children():
            w.destroy()
        for r in self.repartidores:
            row = ctk.CTkFrame(self.lista_rep_frame,
                               fg_color="#f1f5f9", corner_radius=4)
            row.pack(fill="x", padx=2, pady=1)
            ctk.CTkLabel(row,
                text=f"#{r.id_repartidor}  {r.nombre}  |  {r.distrito}  |  {r.capacidad_kg}kg  |  {r.vehiculo}",
                font=ctk.CTkFont("Arial", 10), text_color="#3498db"
            ).pack(side="left", padx=4)

    # ────────────────────────────────────────────────────
    # FORMULARIOS DE REGISTRO
    # ────────────────────────────────────────────────────

    def _form_pedido(self):
        win = ctk.CTkToplevel(self)
        win.title("Registrar Nuevo Pedido")
        win.geometry("460x560")
        win.configure(fg_color=PANEL_BG)
        win.grab_set()

        ctk.CTkLabel(win, text="NUEVO PEDIDO",
                     font=ctk.CTkFont("Arial", 16, "bold"),
                     text_color=ACCENT).pack(pady=14)

        distritos = ["CUSCO", "WANCHAQ", "SANTIAGO",
                     "SAN SEBASTIAN", "SAN JERONIMO", "SAYLLA", "CCORCA", "POROY"]

        campos = {}
        for lbl, ph, val in [
            ("Cliente",    "Nombre del cliente",     ""),
            ("Latitud",    "ej. -13.5170",            "-13.5170"),
            ("Longitud",   "ej. -71.9780",            "-71.9780"),
            ("Prioridad",  "1-5  (5=urgente)",         "3"),
            ("Peso (kg)",  "ej. 5.0",                  "5.0"),
            ("Valor (S/)", "ej. 150",                  "100"),
            ("Descripción","opcional",                  ""),
        ]:
            ctk.CTkLabel(win, text=lbl, font=ctk.CTkFont("Arial", 11),
                         text_color=TEXT_G).pack(anchor="w", padx=20)
            e = ctk.CTkEntry(win, placeholder_text=ph, width=380)
            e.pack(padx=20, pady=2)
            if val:
                e.insert(0, val)
            campos[lbl] = e

        ctk.CTkLabel(win, text="Distrito", font=ctk.CTkFont("Arial", 11),
                     text_color=TEXT_G).pack(anchor="w", padx=20)
        combo_d = ctk.CTkComboBox(win, values=distritos, width=380)
        combo_d.pack(padx=20, pady=2)
        combo_d.set("CUSCO")

        def guardar():
            try:
                nuevo_id = max((p.id_pedido for p in self.pedidos), default=0) + 1
                p = Pedido(
                    nuevo_id,
                    campos["Cliente"].get().strip(),
                    combo_d.get(),
                    float(campos["Latitud"].get()),
                    float(campos["Longitud"].get()),
                    int(campos["Prioridad"].get()),
                    float(campos["Peso (kg)"].get()),
                    float(campos["Valor (S/)"].get()),
                    campos["Descripción"].get()
                )
                self.pedidos.append(p)
                mk = self.mapa.set_marker(p.latitud, p.longitud,
                    text=f"#{p.id_pedido} {p.cliente}",
                    marker_color_circle=ACCENT,
                    marker_color_outside=ACCENT)
                self._markers.append(mk)
                self._refresh_pedidos_list()
                self._log(f"✅ Pedido #{nuevo_id} registrado — {p.cliente} ({combo_d.get()})")
                win.destroy()
            except Exception as ex:
                messagebox.showerror("Error", str(ex), parent=win)

        ctk.CTkButton(win, text="💾  Guardar Pedido", command=guardar,
                      fg_color=GREEN, height=38,
                      font=ctk.CTkFont("Arial", 13, "bold")).pack(pady=16)

    def _form_repartidor(self):
        win = ctk.CTkToplevel(self)
        win.title("Registrar Repartidor")
        win.geometry("460x500")
        win.configure(fg_color=PANEL_BG)
        win.grab_set()

        ctk.CTkLabel(win, text="NUEVO REPARTIDOR",
                     font=ctk.CTkFont("Arial", 16, "bold"),
                     text_color="#3498db").pack(pady=14)

        distritos = ["CUSCO", "WANCHAQ", "SANTIAGO",
                     "SAN SEBASTIAN", "SAN JERONIMO", "SAYLLA", "CCORCA", "POROY"]
        vehiculos = ["Moto", "Furgoneta", "Bicicleta", "A pie"]

        campos = {}
        for lbl, ph, val in [
            ("Nombre",        "Nombre completo",  ""),
            ("Latitud",       "ej. -13.5170",      "-13.5170"),
            ("Longitud",      "ej. -71.9780",      "-71.9780"),
            ("Capacidad (kg)","ej. 20",             "20"),
        ]:
            ctk.CTkLabel(win, text=lbl, font=ctk.CTkFont("Arial", 11),
                         text_color=TEXT_G).pack(anchor="w", padx=20)
            e = ctk.CTkEntry(win, placeholder_text=ph, width=380)
            e.pack(padx=20, pady=2)
            if val: e.insert(0, val)
            campos[lbl] = e

        ctk.CTkLabel(win, text="Distrito", font=ctk.CTkFont("Arial", 11),
                     text_color=TEXT_G).pack(anchor="w", padx=20)
        combo_d = ctk.CTkComboBox(win, values=distritos, width=380)
        combo_d.pack(padx=20, pady=2); combo_d.set("CUSCO")

        ctk.CTkLabel(win, text="Vehículo", font=ctk.CTkFont("Arial", 11),
                     text_color=TEXT_G).pack(anchor="w", padx=20)
        combo_v = ctk.CTkComboBox(win, values=vehiculos, width=380)
        combo_v.pack(padx=20, pady=2); combo_v.set("Moto")

        def guardar():
            try:
                nid = max((r.id_repartidor for r in self.repartidores), default=0) + 1
                centro = CENTROS_DISTRITOS.get(combo_d.get(),
                                               (float(campos["Latitud"].get()),
                                                float(campos["Longitud"].get())))
                r = Repartidor(
                    nid,
                    campos["Nombre"].get().strip(),
                    combo_d.get(),
                    float(campos["Latitud"].get()),
                    float(campos["Longitud"].get()),
                    float(campos["Capacidad (kg)"].get()),
                    combo_v.get()
                )
                self.repartidores.append(r)
                mk = self.mapa.set_marker(r.latitud, r.longitud,
                    text=f"🚴 {r.nombre}",
                    marker_color_circle="#3498db",
                    marker_color_outside="#3498db")
                self._markers.append(mk)
                self._refresh_repartidores_list()
                self._log(f"✅ Repartidor #{nid} registrado — {r.nombre}")
                win.destroy()
            except Exception as ex:
                messagebox.showerror("Error", str(ex), parent=win)

        ctk.CTkButton(win, text="💾  Guardar Repartidor", command=guardar,
                      fg_color="#2980b9", height=38,
                      font=ctk.CTkFont("Arial", 13, "bold")).pack(pady=16)

    # ────────────────────────────────────────────────────
    # BUSCAR PEDIDO
    # ────────────────────────────────────────────────────

    def _buscar_pedido(self):
        win = ctk.CTkToplevel(self)
        win.title("Buscar Pedido")
        win.geometry("400x280")
        win.configure(fg_color=PANEL_BG)
        win.grab_set()

        ctk.CTkLabel(win, text="BUSCAR PEDIDO",
                     font=ctk.CTkFont("Arial", 15, "bold"),
                     text_color=PURPLE).pack(pady=14)

        modo_var = ctk.StringVar(value="id")
        ctk.CTkRadioButton(win, text="Por ID",      variable=modo_var, value="id").pack()
        ctk.CTkRadioButton(win, text="Por Cliente", variable=modo_var, value="cliente").pack()
        ctk.CTkRadioButton(win, text="Por Distrito",variable=modo_var, value="distrito").pack()

        entry = ctk.CTkEntry(win, placeholder_text="Ingrese valor...", width=320)
        entry.pack(pady=10)
        res_lbl = ctk.CTkLabel(win, text="", font=ctk.CTkFont("Arial", 11),
                               text_color=GREEN, wraplength=360)
        res_lbl.pack()

        def buscar():
            q = entry.get().strip()
            modo = modo_var.get()
            if not q:
                return
            if modo == "id":
                r = busqueda_binaria_id(self.pedidos, int(q))
                if r:
                    self.mapa.set_position(r.latitud, r.longitud)
                    self.mapa.set_zoom(15)
                    res_lbl.configure(
                        text=f" #{r.id_pedido} {r.cliente}\n{r.distrito} | Pri:{r.prioridad} | {r.peso}kg")
                    self._log(f" Encontrado: #{r.id_pedido} {r.cliente}")
                else:
                    res_lbl.configure(text=" No encontrado", text_color=ACCENT)
            elif modo == "cliente":
                rs = busqueda_lineal_cliente(self.pedidos, q)
                res_lbl.configure(
                    text="\n".join(f"#{p.id_pedido} {p.cliente} ({p.distrito})" for p in rs)
                    or " No encontrado", text_color=GREEN)
            else:
                rs = busqueda_por_distrito(self.pedidos, q)
                res_lbl.configure(
                    text="\n".join(f"#{p.id_pedido} {p.cliente}" for p in rs)
                    or " No encontrado", text_color=GREEN)

        ctk.CTkButton(win, text=" Buscar", command=buscar,
                      fg_color=PURPLE).pack(pady=6)

    # ────────────────────────────────────────────────────
    # ORDENAR
    # ────────────────────────────────────────────────────

    def _ordenar(self, criterio: str):
        if criterio == "prioridad":
            self.pedidos = ordenar_por_prioridad(self.pedidos)
            self._log(" Pedidos ordenados por prioridad (mayor → menor)")
        elif criterio == "distancia":
            origen = (-13.5170, -71.9780)
            self.pedidos = ordenar_por_distancia(self.pedidos, origen)
            self._log(" Pedidos ordenados por distancia desde Plaza de Armas")
        elif criterio == "valor":
            self.pedidos = ordenar_por_valor(self.pedidos)
            self._log(" Pedidos ordenados por valor (mayor → menor)")
        self._refresh_pedidos_list()

    # ────────────────────────────────────────────────────
    # GREEDY
    # ────────────────────────────────────────────────────

    def _ejecutar_greedy(self):
        if not self.repartidores:
            messagebox.showwarning("Aviso", "No hay repartidores registrados.")
            return

        win = ctk.CTkToplevel(self)
        win.title("Greedy — Emergencias y ruteo local")
        win.geometry("550x700")
        win.configure(fg_color=PANEL_BG)
        win.grab_set()

        ctk.CTkLabel(win, text="OPTIMIZACION DE ENTREGAS",
                     font=ctk.CTkFont("Helvetica Neue", 18, "bold"),
                     text_color="#7e7474").pack(pady=15)
        
        # Creamos dos pestañas para los casos de uso
        tabview = ctk.CTkTabview(win, width=520, height=620)
        tabview.pack(padx=10, pady=5)

        tab_ruteo = tabview.add("Ruta Completa (Vecino cercano)")
        tab_emergencias = tabview.add("Despacho de Emergencia")
        
        # --- Boton para ruteo completo ---
        ctk.CTkLabel(tab_ruteo,
            text="Selecciona un repartidor y se construirá\nla ruta óptima local (Vecino Más Cercano)",
            font=ctk.CTkFont("Segoe UI", 11), text_color=TEXT_G).pack()
        
        # --- ComboBox para seleccionar repartidor ---
        nombres_rep = [f"#{r.id_repartidor} {r.nombre}" for r in self.repartidores]
        combo_r = ctk.CTkComboBox(tab_ruteo, values=nombres_rep, width=400)
        combo_r.pack(pady=8)
        combo_r.set(nombres_rep[0])
        
        # --- Caja de texto para mostrar resultados ---
        res_box = ctk.CTkTextbox(tab_ruteo, height=380, font=ctk.CTkFont("Courier", 11),
                                 fg_color="#898992", text_color="#1e292b", corner_radius=6)
        res_box.pack(fill="both", expand=True, padx=12, pady=6)
        
        def ejecutar_ruteo():
            idx = nombres_rep.index(combo_r.get())
            rep = self.repartidores[idx]
            origen = (rep.latitud, rep.longitud)
            pedidos_activos = [p for p in self.pedidos if not p.entregado]
            ruta, dist_total = ruta_greedy_completa(origen, pedidos_activos)
            
            # Dibuja en el mapa
            for pg in self._paths:
                try: pg.delete()
                except: pass
            self._paths.clear()
            #3333
            puntos = [origen]
            for (pedido, _) in ruta:
                puntos.append((pedido.latitud, pedido.longitud))
            if len(puntos) > 1:
                puntos_calles, distancia_calles = ruta_por_calles(puntos, perfil="driving")
                path = self.mapa.set_path(
                    puntos_calles,
                    color="#1abc9c",
                    width=4
                )
                self._paths.append(path)
                if distancia_calles > 0:
                    dist_total = distancia_calles
            self.mapa.set_position(*origen)
            self.mapa.set_zoom(12)

            # Muestra resultados
            res_box.configure(state="normal")
            res_box.delete("1.0", "end")
            res_box.insert("end",
                f"Repartidor: {rep.nombre}\nDistancia total: {dist_total:.3f} km\n"
                f"Origen: ({rep.latitud:.4f}, {rep.longitud:.4f})\n"
                f"Capacidad: {rep.capacidad_kg} kg\n"
                f"{'─'*45}\n"
                f"RUTA GREEDY (Vecino Más Cercano):\n\n"
            )
            for i, (ped, dist) in enumerate(ruta, 1):
                res_box.insert("end",
                    f"  Parada {i}: #{ped.id_pedido} {ped.cliente}\n"
                    f"    Distrito: {ped.distrito}\n"
                    f"    Distancia: {dist:.3f} km\n"
                    f"    Peso: {ped.peso} kg | Valor: S/{ped.valor:.0f}\n\n"
                )
            res_box.insert("end",
                f"{'─'*45}\n"
                f"Distancia total: {dist_total:.3f} km\n"
                f"Pedidos en ruta: {len(ruta)}\n"
            )
            res_box.configure(state="disabled")
            
        ctk.CTkButton(tab_ruteo, text="Calcular Ruta Completa", command=ejecutar_ruteo,
                      fg_color="#16a085", height=36,
                      font=ctk.CTkFont("Arial", 13, "bold")).pack(pady=8)
        
        # --- Pestaña para despacho de emergencia ---
        ctk.CTkLabel(tab_emergencias,
            text="Selecciona un pedido en estado de emergencia y se asignará automáticamente el repartidor más cercano con capacidad disponible.",
            font=ctk.CTkFont("Segoe UI", 11), 
            text_color="#e0e0e0").pack(pady=15)
         
        pedidos_no_entregados = [p for p in self.pedidos if not p.entregado]
        if pedidos_no_entregados:
            nombres_pedidos = [f"#{p.id_pedido} - {p.cliente} ({p.distrito})" for p in pedidos_no_entregados]
        else:
            nombres_pedidos = ["No hay pedidos activos"]
            
        combo_pedidos = ctk.CTkComboBox(tab_emergencias, values=nombres_pedidos, width=400)
        combo_pedidos.pack(pady=8)
        combo_pedidos.set(nombres_pedidos[0])
        
        res_box_emergencias = ctk.CTkTextbox(tab_emergencias, height=380, font=ctk.CTkFont("Courier", 11),
                                             fg_color="#898992", text_color="#1e292b", corner_radius=6)
        res_box_emergencias.pack(fill="both", expand=True, padx=12, pady=6)
        
        def ejecutar_emergencia():
            if not pedidos_no_entregados or combo_pedidos.get() == "No hay pedidos activos":
                messagebox.showinfo("Información", "No hay pedidos en estado de emergencia.")
                return
                
            # --- EXTRACTOR DE ID INFALIBLE ---
            texto_combo = combo_pedidos.get()
            # Extraemos solo los dígitos que están justo después del '#'
            id_numerico = "".join([c for c in texto_combo.split("-")[0] if c.isdigit()])
            
            # Buscamos el pedido cuyo id contenga ese número
            pedido_emergencia = next((p for p in pedidos_no_entregados if str(p.id_pedido) == id_numerico), None)
            
            # Si por alguna razón la lista falló, buscamos en la lista global como respaldo
            if not pedido_emergencia:
                pedido_emergencia = next((p for p in self.pedidos if str(p.id_pedido) == id_numerico), pedidos_no_entregados[0])
            # ─────────────────────────────────
            mejor_repartidor, dist_km = asignar_repartidor_greedy(self.repartidores, pedido_emergencia)
            
            for pg in self._paths:
                try: pg.delete()
                except: pass
            self._paths.clear()
            
            res_box_emergencias.configure(state="normal")
            res_box_emergencias.delete("1.0", "end")
            
            if mejor_repartidor:
                origen_rep = (mejor_repartidor.latitud, mejor_repartidor.longitud)
                destino_ped = (pedido_emergencia.latitud, pedido_emergencia.longitud)
                puntos_calles, distancia_calles = ruta_por_calles(
                    [origen_rep, destino_ped],
                    perfil="driving"
                )
                path = self.mapa.set_path(
                    puntos_calles,
                    color="#e74c3c",
                    width=4
                )
                self._paths.append(path)

                if distancia_calles > 0:
                    dist_km = distancia_calles

                self.mapa.set_position(*origen_rep)
                self.mapa.set_zoom(13)
                res_box_emergencias.insert("end",
                    f"Despacho de Emergencia\n\n"
                    f"{'─'*45}\n"
                    f"PEDIDO AFECTADO: #{pedido_emergencia.id_pedido} {pedido_emergencia.cliente}\n"
                    f"Ubicación: ({pedido_emergencia.latitud:.4f}, {pedido_emergencia.longitud:.4f})\n"
                    f"Peso del pedido: {pedido_emergencia.peso} kg | Valor: S/{pedido_emergencia.valor:.0f}\n\n"
                    f"REPARTIDOR ASIGNADO:\n"
                    f"{mejor_repartidor.nombre} ({mejor_repartidor.distrito})\n"
                    f"-->Distancia de respuesta: {dist_km:.3f} km\n"
                )
                self._log(f"Emergencia: Pedido #{pedido_emergencia.id_pedido} asignado a {mejor_repartidor.nombre} ({dist_km:.2f} km)")
            else:
                # 1. Aumentamos una ventana flotante de advertencia
                messagebox.showwarning(
                    "Capacidad Agotada", 
                    f"¡Alerta! Ningun repartidor tiene capacidad de carga libre para el pedido de {pedido_emergencia.peso} kg."
                )
                
                # 2. Aumentamos un texto detallado en la caja de la interfaz
                res_box_emergencias.insert("end", 
                    f"ALERTA DE LOGISTICA:\n"
                    f"No se encontró ningún repartidor disponible para el Pedido #{pedido_emergencia.id_pedido}.\n\n"
                    f"Razones posibles:\n"
                    f" - El peso del pedido ({pedido_emergencia.peso} kg) supera la capacidad actual de los repartidores.\n"
                    f" - Todos los vehículos se encuentran al límite de su carga."
                )

            
        ctk.CTkButton(tab_emergencias, text="Asignar Repartidor de Emergencia", command=ejecutar_emergencia,
                      fg_color="#e67e22", height=36, font=ctk.CTkFont("Arial", 13, "bold")).pack(pady=8)

    # ────────────────────────────────────────────────────
    # DIVIDE Y VENCERÁS
    # ────────────────────────────────────────────────────
    def _ejecutar_divide(self):
        win = ctk.CTkToplevel(self)
        win.title("Divide y Venceras - Rutas por sub-zona")
        win.geometry("720x820")
        win.configure(fg_color=PANEL_BG)
        win.grab_set()

        ctk.CTkLabel(win,text="DIVIDE Y VENCERAS",font=ctk.CTkFont("Arial", 16, "bold"), text_color="#3f2caa").pack(pady=10)
        ctk.CTkLabel(win,text="Secciona Cusco en sus 8 distritos y programa rutas optimas\n" "para los repartidores de su sub-zona asignada.",font=ctk.CTkFont("Arial", 11),
            text_color=TEXT_G).pack()
        distritos = ["TODOS"] + sorted(CENTROS_DISTRITOS.keys())
        f_sel = ctk.CTkFrame(win, fg_color="transparent")
        f_sel.pack(fill="x", padx=12, pady=(10, 2))
        ctk.CTkLabel(f_sel,text="Distrito:",width=80,text_color=TEXT_G).pack(side="left")
        combo_d = ctk.CTkComboBox(f_sel, values=distritos, width=260)
        combo_d.pack(side="left", padx=4)
        combo_d.set("TODOS")

        res_box = ctk.CTkTextbox(win,height=580,font=ctk.CTkFont("Courier", 11),fg_color="#A0A0B2",
            text_color="#1B2B3A",corner_radius=6)
        res_box.pack(fill="both", expand=True, padx=12, pady=8)

        def ejecutar():
            distrito_sel = combo_d.get().upper()
            mostrar_todos = distrito_sel == "TODOS"
            for pg in self._polygons:
                try:
                    pg.delete()
                except:
                    pass
            self._polygons.clear()

            for path in self._paths:
                try:
                    path.delete()
                except:
                    pass
            self._paths.clear()
            polys = obtener_poligonos_distritos()
            for nombre, lista_polys in polys.items():
                nombre_norm = nombre.upper()
                color = COLORES_DISTRITOS.get(nombre_norm, "#cccccc")
                seleccionado = mostrar_todos or nombre_norm == distrito_sel

                for coords in lista_polys:
                    if len(coords) > 2:
                        try:
                            pg = self.mapa.set_polygon(coords,fill_color=color,outline_color=color,
                                border_width=4 if seleccionado else 2,name=nombre)
                            self._polygons.append(pg)
                        except Exception as ex:
                            print("Error dibujando distrito:", nombre, ex)

            resultado = resolver_todas_zonas(self.pedidos, CENTROS_DISTRITOS)

            distritos_a_resolver = (sorted(resultado.keys()) if mostrar_todos else [distrito_sel])
            res_box.configure(state="normal")
            res_box.delete("1.0", "end")

            res_box.insert("end", f"DIVIDE Y VENCERAS - RUTAS POR SUB-ZONA\n" f"{'=' * 62}\n\n"
                f"DIVIDE:\n" f"  Cusco se separa en 8 distritos coloreados.\n" f"  Distrito elegido: {distrito_sel}\n"
                f"  Cada repartidor atiende solo pedidos de su distrito.\n\n")

            total_rutas = 0
            total_pedidos = 0
            total_distancia = 0.0
            primer_centro = None

            for distrito in distritos_a_resolver:
                datos_zona = resultado.get(distrito, {"pedidos": [], "ruta": [], "distancia_total": 0.0})
                pedidos_zona = list(datos_zona["pedidos"])
                reps_zona = [r for r in self.repartidores if r.distrito.upper() == distrito]
                centro = CENTROS_DISTRITOS.get(distrito, (-13.5170, -71.9780))
                primer_centro = primer_centro or centro

                res_box.insert("end", f"ZONA: {distrito}\n" f"  Pedidos: {len(pedidos_zona)} | " f"Repartidores: {len(reps_zona)}\n")
                if not pedidos_zona:
                    res_box.insert("end", "  No hay pedidos en esta zona.\n\n")
                    continue

                if not reps_zona:
                    res_box.insert("end", "  No hay repartidores en esta zona.\n\n")
                    continue
                paquetes = {rep.id_repartidor: [] for rep in reps_zona}
                for pedido in pedidos_zona:
                    rep = min(
                        reps_zona,
                        key=lambda r: ((r.latitud - pedido.latitud) ** 2 + (r.longitud - pedido.longitud) ** 2))
                    paquetes[rep.id_repartidor].append(pedido)

                for rep in reps_zona:
                    pedidos_rep = paquetes[rep.id_repartidor]

                    if not pedidos_rep:
                        continue
                    origen = (rep.latitud, rep.longitud)
                    ruta_rep, dist_geo = ruta_optima_zona(origen, pedidos_rep)
                    ruta_normalizada = []
                    posicion_actual = origen

                    for item in ruta_rep:
                        if isinstance(item, tuple):
                            pedido, distancia = item
                        else:
                            pedido = item
                            distancia = geodesic(posicion_actual,(pedido.latitud, pedido.longitud)).km
                        ruta_normalizada.append((pedido, distancia))
                        posicion_actual = (pedido.latitud, pedido.longitud)

                    puntos = [origen] + [(pedido.latitud, pedido.longitud) for pedido, _ in ruta_normalizada
                    ]

                    puntos_mapa, dist_calles = ruta_por_calles(puntos)

                    distancia_final = dist_calles if dist_calles > 0 else dist_geo
                    color = COLORES_DISTRITOS.get(distrito, "#2471a3")

                    if len(puntos_mapa) > 1:
                        path = self.mapa.set_path(puntos_mapa,color=color,width=4)
                        self._paths.append(path)

                    res_box.insert(
                        "end",
                        f"  Repartidor #{rep.id_repartidor}: {rep.nombre}\n"
                        f"    Inicio: ({rep.latitud:.4f}, {rep.longitud:.4f})\n"
                        f"    Pedidos asignados: {len(pedidos_rep)}\n"
                        f"    Distancia ruta: {distancia_final:.3f} km"
                        f"{' por calles' if dist_calles > 0 else ' geodesica'}\n"
                    )

                    for i, (ped, dist) in enumerate(ruta_normalizada, 1):
                        res_box.insert("end", f"      {i}. #{ped.id_pedido} {ped.cliente} " f"({dist:.3f} km)\n")

                    total_rutas += 1
                    total_pedidos += len(pedidos_rep)
                    total_distancia += distancia_final

                res_box.insert("end", "\n")

            res_box.insert(
                "end",
                f"{'-' * 62}\n"
                f"COMBINAR:\n"
                f"  Rutas programadas: {total_rutas}\n"
                f"  Pedidos en rutas: {total_pedidos}\n"
                f"  Distancia total dibujada: {total_distancia:.3f} km\n\n"
                f"Complejidad division: O(n*d*v)\n"
                f"Complejidad ruta local por repartidor: O(k_i^2)\n"
                f"Ventaja: no se resuelve toda la ciudad junta, sino por sub-zonas.\n"
            )

            res_box.configure(state="disabled")

            self.mapa.set_position(*(primer_centro or (-13.5300, -71.9400)))
            self.mapa.set_zoom(11 if mostrar_todos else 13)

            self._log( f"Divide y Venceras [{distrito_sel}]: " f"{total_rutas} rutas, {total_pedidos} pedidos")

        ctk.CTkButton(win,text="Programar rutas por sub-zona",command=ejecutar,fg_color="#5E7889",
            height=36,
            font=ctk.CTkFont("Arial", 13, "bold")
        ).pack(pady=8)
    
    

    # ────────────────────────────────────────────────────
    # PROGRAMACIÓN DINÁMICA — MOCHILA
    # ────────────────────────────────────────────────────

    def _ejecutar_mochila(self):
        if not self.repartidores:
            messagebox.showwarning("Aviso", "No hay repartidores registrados.")
            return

        win = ctk.CTkToplevel(self)
        win.title("Programación Dinámica — Problema de la Mochila 0/1")
        win.geometry("680x780")
        win.configure(fg_color=PANEL_BG)
        win.grab_set()

        ctk.CTkLabel(win, text=" PROGRAMACIÓN DINÁMICA (KNAPSACK)",
                     font=ctk.CTkFont("Segoe UI", 17, "bold"),
                     text_color="#a855f7").pack(pady=12)

        ctk.CTkLabel(win,
            text="Seleccionara los pedidos que aumentaran el valor o costo total\n"
                 "cargado en el vehiculo sin exceder su capacidad.",
            font=ctk.CTkFont("Segoe UI", 12),
            text_color="#86909c").pack()

        ctk.CTkFrame(win, height=1, fg_color="#7668ad").pack(fill="x", padx=16, pady=8)

        ctk.CTkLabel(win,
            text="  Variables:   PESO (kg)  →  Es limitado   |     VALOR (Costo)  →  se maximiza",
            font=ctk.CTkFont("Segoe UI", 11, "bold"),
            text_color="#c4b5fd").pack(anchor="w", padx=16)

        ctk.CTkFrame(win, height=1, fg_color="#9f8ee4").pack(fill="x", padx=16, pady=8)

        nombres = [f"{r.id_repartidor}. {r.nombre}  —  capacidad: {r.capacidad_kg} kg  ({r.vehiculo})"
                   for r in self.repartidores]
        _ejecutar_ref = [None]
        combo_r = ctk.CTkComboBox(win, values=nombres, width=560,
                                  font=ctk.CTkFont("Segoe UI", 12),
                                  command=lambda _: _ejecutar_ref[0] and _ejecutar_ref[0]())
        combo_r.pack(pady=6)
        combo_r.set(nombres[0])

        res_box = ctk.CTkTextbox(
            win,
            height=500,
            font=ctk.CTkFont("Segoe UI", 13),
            fg_color="#918d95",
            text_color="#222020",
            corner_radius=8
        )
        res_box.pack(fill="both", expand=True, padx=14, pady=6)

        def ejecutar():
            idx = nombres.index(combo_r.get())
            rep = self.repartidores[idx]
            resultado = mochila_tabla(self.pedidos, rep.capacidad_kg)

            sel      = resultado["pedidos_sel"]
            val_max  = resultado["valor_maximo"]
            peso_tot = resultado["peso_total"]
            n        = resultado["n_pedidos"]
            W        = resultado["capacidad_W"]

            res_box.configure(state="normal")
            res_box.delete("1.0", "end")

            # ── Encabezado ──
            res_box.insert("end",
                f"{'═' * 52}\n"
                f"  REPARTIDOR : {rep.nombre}\n"
                f"  VEHÍCULO   : {rep.vehiculo}\n"
                f"  CAPACIDAD  : {rep.capacidad_kg} kg\n"
                f"  CANDIDATOS : {n} pedidos evaluados\n"
                f"{'═' * 52}\n\n"
            )

            # ── Explicación del problema ──
            res_box.insert("end",
                "  PROBLEMA DE LA MOCHILA:\n"
                "  Dado un conjunto de pedidos, cada uno con un\n"
                "  peso y un valor o costo, se busca la combinación\n"
                "  que maximice el valor total sin superar la capacidad\n"
                "  de carga del vehiculo del repartidor.\n\n"
                "  Cada pedido se incluye 1 o ninguna vez → Knapsack 0/1\n\n"
                f"{'─' * 52}\n\n"
            )

            # ── Todos los pedidos evaluados ──
            res_box.insert("end", "  PEDIDOS EVALUADOS:\n\n")
            for p in self.pedidos:
                marca = "  ✅ SELECCIONADO" if p in sel else "  ⬜ no seleccionado"
                res_box.insert("end",
                    f"  #{p.id_pedido:02d}  {p.cliente:<18}"
                    f"  Peso: {p.peso:5.1f} kg   Valor: S/{p.valor:6.1f}"
                    f"{marca}\n"
                )

            # ── Resultado óptimo ──
            res_box.insert("end", f"\n{'─' * 52}\n\n")

            if not sel:
                res_box.insert("end",
                    " Ningún pedido cabe dentro de la capacidad\n"
                    "     disponible del repartidor.\n"
                )
            else:
                res_box.insert("end",
                    f" ({len(sel)} PEDIDOS SELECCIONADOS):\n\n"
                )
                for i, p in enumerate(sel, 1):
                    res_box.insert("end",
                        f"  {i}.  #{p.id_pedido:02d}  {p.cliente}\n"
                        f"       Peso : {p.peso} kg\n"
                        f"       Valor: S/ {p.valor:.2f}\n\n"
                    )

            res_box.insert("end",
                f"{'═' * 52}\n"
                f"  Valor máximo alcanzado : S/ {val_max:.2f}\n"
                f"  Peso total cargado     : {peso_tot:.2f} kg  /  {rep.capacidad_kg} kg\n"
                f"  Capacidad usada        : {(peso_tot/rep.capacidad_kg*100):.1f} %\n"
                f"{'─' * 52}\n\n"
        
            )
            res_box.configure(state="disabled")

            # ── Marcadores en el mapa ──
            for pg in self._paths:
                try: pg.delete()
                except: pass
            self._paths.clear()

            if sel:
                puntos = [(rep.latitud, rep.longitud)]
                for p in sel:
                    puntos.append((p.latitud, p.longitud))

                coords_ruta, dist_calles = ruta_por_calles(puntos)
                if len(coords_ruta) > 1:
                    path = self.mapa.set_path(
                        coords_ruta, color="#9b59b6", width=4)
                    self._paths.append(path)

                mk_rep = self.mapa.set_marker(
                    rep.latitud, rep.longitud,
                    text=f"🚴 {rep.nombre}",
                    marker_color_circle="#7c3aed",
                    marker_color_outside="#4c1d95")
                self._paths.append(mk_rep)

                for i, p in enumerate(sel, 1):
                    mk = self.mapa.set_marker(
                        p.latitud, p.longitud,
                        text=f"✅ #{i} {p.cliente}",
                        marker_color_circle="#9b59b6",
                        marker_color_outside="#9b59b6")
                    self._paths.append(mk)

                self.mapa.set_position(rep.latitud, rep.longitud)
                self.mapa.set_zoom(12)

            self._log(f"🟣 Mochila [{rep.nombre}]: S/{val_max:.0f} máximo, "
                      f"{len(sel)} pedidos, {peso_tot:.1f} kg")

        _ejecutar_ref[0] = ejecutar

        ctk.CTkButton(win, text=" Resolver Mochila (Programación Dinámica)",
                      command=ejecutar,
                      fg_color="#7c3aed", hover_color="#5b21b6",
                      height=40, corner_radius=8,
                      font=ctk.CTkFont("Segoe UI", 13, "bold")).pack(pady=10)

    # ────────────────────────────────────────────────────
    # BACKTRACKING
    # ────────────────────────────────────────────────────

    def _form_backtracking(self):
        win = ctk.CTkToplevel(self)
        win.title("Backtracking — Rutas con Restricciones")
        win.geometry("580x700")
        win.configure(fg_color=PANEL_BG)
        win.grab_set()

        ctk.CTkLabel(win, text="🔴 BACKTRACKING",
                     font=ctk.CTkFont("Arial", 16, "bold"),
                     text_color=ACCENT).pack(pady=10)
        ctk.CTkLabel(win,
            text="Encuentra TODAS las rutas posibles entre dos distritos\n",
            font=ctk.CTkFont("Arial", 11), text_color=TEXT_G).pack()

        distritos = list(GRAFO_DISTRITOS.keys())

        f1 = ctk.CTkFrame(win, fg_color="transparent")
        f1.pack(fill="x", padx=12, pady=4)
        ctk.CTkLabel(f1, text="Origen:", width=70, text_color=TEXT_G).pack(side="left")
        combo_orig = ctk.CTkComboBox(f1, values=distritos, width=220)
        combo_orig.pack(side="left"); combo_orig.set("CUSCO")

        f2 = ctk.CTkFrame(win, fg_color="transparent")
        f2.pack(fill="x", padx=12, pady=4)
        ctk.CTkLabel(f2, text="Destino:", width=70, text_color=TEXT_G).pack(side="left")
        combo_dest = ctk.CTkComboBox(f2, values=distritos, width=220)
        combo_dest.pack(side="left"); combo_dest.set("SAN JERONIMO")

        
        res_box = ctk.CTkTextbox(win, height=340, font=ctk.CTkFont("Courier", 11),
                                 fg_color="#0a0a1a", text_color="#ff7675", corner_radius=6)
        res_box.pack(fill="both", expand=True, padx=12, pady=6)

        def ejecutar():
            orig  = combo_orig.get()
            dest  = combo_dest.get()

            if orig == dest:
                messagebox.showwarning("Aviso", "Origen y destino deben ser distintos.", parent=win)
                return

            resultado = encontrar_ruta_optima(
                GRAFO_DISTRITOS, orig, dest, CENTROS_DISTRITOS
            )

            res_box.configure(state="normal")
            res_box.delete("1.0", "end")
            res_box.insert("end",
                f"Origen: {orig}  →  Destino: {dest}\n"
                f"{'─'*50}\n"
                f"Total rutas encontradas: {resultado['n_rutas']}\n\n"
            )

            if resultado["n_rutas"] == 0:
                res_box.insert("end", "❌ No existe ruta posible con esas restricciones.\n")
            else:
                for i, (ruta, dist) in enumerate(
                    zip(resultado["todas_rutas"], resultado["distancias"]), 1
                ):
                    marca = " ← ÓPTIMA ✅" if ruta == resultado["ruta_optima"] else ""
                    res_box.insert("end",
                        f"  Ruta {i}{marca}\n"
                        f"  {' → '.join(ruta)}\n"
                        f"  Distancia: {dist:.3f} km\n\n"
                    )

                res_box.insert("end",
                    f"{'─'*50}\n"
                    f"RUTA ÓPTIMA: {' → '.join(resultado['ruta_optima'])}\n"
                    f"Distancia:   {resultado['distancia_opt']:.3f} km\n\n"
                    f"Complejidad: O(d!) en peor caso\n"
                    f"Con podas (visited set + bloqueados) es mucho\nmás rápido en la práctica.\n"
                )

                # Dibujar ruta óptima en mapa
                for pg in self._paths:
                    try: pg.delete()
                    except: pass
                self._paths.clear()
                coords_ruta = [
                    CENTROS_DISTRITOS[d]
                    for d in resultado["ruta_optima"]
                    if d in CENTROS_DISTRITOS
                ]
                if len(coords_ruta) > 1:
                    puntos_calles, _ = ruta_por_calles(coords_ruta, perfil="driving")
                    path = self.mapa.set_path(puntos_calles, color=ACCENT, width=4)
                    self._paths.append(path)
                self.mapa.set_position(*CENTROS_DISTRITOS.get(orig, (-13.52, -71.97)))
                self.mapa.set_zoom(11)

            res_box.configure(state="disabled")
            self._log(f"🔴 Backtracking: {resultado['n_rutas']} rutas, óptima {resultado['distancia_opt']:.2f} km")

        ctk.CTkButton(win, text="▶  Ejecutar Backtracking", command=ejecutar,
                      fg_color=ACCENT, height=36,
                      font=ctk.CTkFont("Arial", 13, "bold")).pack(pady=8)

    # ────────────────────────────────────────────────────
    # ASIGNACIÓN MASIVA GREEDY
    # ────────────────────────────────────────────────────

    def _ejecutar_asignacion_masiva(self):
        if not self.repartidores:
            messagebox.showwarning("Aviso", "No hay repartidores registrados.")
            return

        resultado = asignacion_masiva_greedy(self.repartidores, self.pedidos)

        win = ctk.CTkToplevel(self)
        win.title("Asignación Masiva Greedy")
        win.geometry("600x680")
        win.configure(fg_color=PANEL_BG)
        win.grab_set()

        ctk.CTkLabel(win, text="🟠 ASIGNACIÓN MASIVA GREEDY",
                     font=ctk.CTkFont("Arial", 16, "bold"),
                     text_color="#e67e22").pack(pady=10)
        ctk.CTkLabel(win,
            text="Asigna TODOS los pedidos a repartidores\northogonales por prioridad y distancia.",
            font=ctk.CTkFont("Arial", 11), text_color=TEXT_G).pack()

        res_box = ctk.CTkTextbox(win, height=530, font=ctk.CTkFont("Courier", 11),
                                 fg_color="#0a0a1a", text_color="#ffeaa7", corner_radius=6)
        res_box.pack(fill="both", expand=True, padx=12, pady=10)

        res_box.configure(state="normal")
        res_box.insert("end", f"{'═'*50}\nASIGNACIÓN MASIVA DE PEDIDOS\n{'═'*50}\n\n")

        for rep in self.repartidores:
            asignados = resultado.get(rep.id_repartidor, [])
            peso_tot = sum(p.peso for p, _ in asignados)
            valor_tot = sum(p.valor for p, _ in asignados)
            res_box.insert("end",
                f"🚴 {rep.nombre} ({rep.vehiculo}, {rep.capacidad_kg}kg)\n"
                f"   Pedidos asignados: {len(asignados)}\n"
                f"   Carga: {peso_tot:.1f} kg / {rep.capacidad_kg} kg\n"
                f"   Valor total: S/ {valor_tot:.0f}\n"
            )
            for ped, dist in asignados:
                res_box.insert("end",
                    f"   • #{ped.id_pedido} {ped.cliente} ({ped.distrito}) — {dist:.3f} km\n"
                )
            res_box.insert("end", "\n")

        sin_asig = resultado.get("sin_asignar", [])
        if sin_asig:
            res_box.insert("end", f"⚠ SIN ASIGNAR ({len(sin_asig)}):\n")
            for p in sin_asig:
                res_box.insert("end", f"  • #{p.id_pedido} {p.cliente} ({p.peso}kg)\n")
        else:
            res_box.insert("end", "✅ Todos los pedidos fueron asignados.\n")

        res_box.insert("end",
            f"\n{'─'*50}\n"
            f"Complejidad: O(n log n + n·r)\n"
            f"n=pedidos, r=repartidores\n"
        )
        res_box.configure(state="disabled")
        self._log(f"🟠 Asignación masiva: {len(self.pedidos)-len(sin_asig)} pedidos asignados")
