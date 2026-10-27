"""
================================================================
ARQUISELECT: SISTEMA EXPERTO PARA SELECCIÓN DE ARQUITECTURAS
Arquitectura: Base de Conocimiento (Prolog) + Motor de Inferencia
y Explicabilidad (PySwip) + Interfaz de Usuario (Tkinter)
================================================================

Este programa es la implementación de caja blanca (Entregable 2):
1. Base de Conocimiento: base_conocimiento.pl
2. Motor de Inferencia y Puente: PuenteProlog (PySwip sin llamadas bloqueantes)
3. Persistencia de Evaluaciones: GestorHistorial (JSON en disco)
4. Interfaz Gráfica: ControladorApp con diseño minimalista contemporáneo:
- VistaInicio: Portal minimalista de bienvenida y acceso a flujos
- VistaEvaluacion: Formulario de requisitos, dictamen y preguntas guiadas
- VistaHistorial: Registro auditable de evaluaciones previas
"""

import os
import re
import sys
import json
import unicodedata
from datetime import datetime

import tkinter as tk
from tkinter import ttk, messagebox

# ===========================================================================
# 1. CONSTANTES, RUTAS Y PALETA MINIMALISTA CONTEMPORÁNEA
# ===========================================================================
CARPETA_PROYECTO = os.path.dirname(os.path.abspath(__file__))
RUTA_BASE_CONOCIMIENTO = os.path.join(CARPETA_PROYECTO, "base_conocimiento.pl")
RUTA_HISTORIAL = os.path.join(CARPETA_PROYECTO, "historial_evaluaciones.json")

# Tipografía del sistema
FUENTE_BASE = "Segoe UI"

# Paleta Minimalista Contemporánea (Nordic Slate + Modern Indigo)
COLOR_FONDO = "#f8fafc"           # Slate-50: lienzo limpio, fresco y aireado
COLOR_HEADER = "#0f172a"          # Slate-900: barra de navegación oscura y elegante
COLOR_HEADER_SUB = "#94a3b8"      # Slate-400: subtítulo nítido
COLOR_TEXTO = "#0f172a"           # Slate-900: texto principal con máxima legibilidad
COLOR_TEXTO_MUTED = "#64748b"     # Slate-500: texto secundario / etiquetas
COLOR_TARJETA = "#ffffff"         # Blanco puro para tarjetas elevadas
COLOR_SUPERFICIE = "#f1f5f9"      # Slate-100: fondos sutiles para inputs/agrupaciones
COLOR_BORDE = "#e2e8f0"           # Slate-200: borde nítido de 1px, sin biseles 3D

# Acentos interactivos
COLOR_PRIMARIO = "#4f46e5"        # Indigo-600: acción principal, moderno e inteligente
COLOR_PRIMARIO_HOVER = "#4338ca"  # Indigo-700
COLOR_SECUNDARIO = "#0f172a"      # Slate-900: botones de alto impacto
COLOR_SECUNDARIO_HOVER = "#1e293b"# Slate-800
COLOR_SUAVE = "#f1f5f9"           # Slate-100: botones sutiles / utilitarios
COLOR_SUAVE_HOVER = "#e2e8f0"     # Slate-200

# Semántica de estados (estilo badges Tailwind)
COLOR_EXITO_BG = "#ecfdf5"        # Emerald-50
COLOR_EXITO_TEXT = "#065f46"      # Emerald-800

COLOR_AMBAR = "#f59e0b"           # Amber-500: empate / advertencia
COLOR_AMBAR_BG = "#fffbeb"        # Amber-50
COLOR_AMBAR_TEXT = "#92400e"      # Amber-800

COLOR_PELIGRO = "#ef4444"         # Rose-500: error / exclusión
COLOR_PELIGRO_BG = "#fef2f2"      # Rose-50
COLOR_PELIGRO_TEXT = "#991b1b"    # Rose-800

COLOR_INFO_BG = "#eff6ff"         # Blue-50

COLOR_GRIS = "#94a3b8"            # Slate-400

NOMBRE_GRUPO = {
    "equipo": "Equipo de Desarrollo",
    "presupuesto": "Presupuesto",
    "tiempo": "Tiempo de Entrega",
    "carga": "Carga y Rendimiento",
    "operacion": "Operación y Despliegue",
    "dominio": "Complejidad del Dominio",
}

NOMBRE_PERFIL = {
    "alta_demanda": "Plataforma de Alto Tráfico",
    "startup": "Startup / MVP Rápido",
    "empresarial": "Sistema Empresarial Complejo",
}

# Badges (Fondo suave, Texto oscuro temático)
COLOR_PRIORIDAD = {
    "alta": (COLOR_EXITO_BG, COLOR_EXITO_TEXT),
    "media": (COLOR_AMBAR_BG, COLOR_AMBAR_TEXT),
    "baja": (COLOR_PELIGRO_BG, COLOR_PELIGRO_TEXT),
    "bajo": (COLOR_EXITO_BG, COLOR_EXITO_TEXT),
    "medio": (COLOR_AMBAR_BG, COLOR_AMBAR_TEXT),
    "alto": (COLOR_PELIGRO_BG, COLOR_PELIGRO_TEXT),
    "por_defecto": (COLOR_SUPERFICIE, COLOR_TEXTO_MUTED),
    "nula": (COLOR_SUPERFICIE, COLOR_TEXTO_MUTED),
}

COLOR_ROL = {
    "lider": "#4f46e5",          # Indigo líder
    "competencia": "#f59e0b",    # Amber competidor
    "otro": "#94a3b8",           # Slate neutro
}

ESTADO_DICTAMEN = {
    "definitivo": (
        COLOR_EXITO_BG, COLOR_EXITO_TEXT,
        "✔ Dictamen definitivo: La evidencia es concluyente y el estilo líder supera claramente a las demás opciones."
    ),
    "empate": (
        COLOR_AMBAR_BG, COLOR_AMBAR_TEXT,
        "⚖ Empate técnico: Existen hipótesis muy cercanas en puntaje. Responda las preguntas guiadas."
    ),
    "insuficiente": (
        "#fff7ed", "#9a3412",
        "ⓘ Evidencia insuficiente: Con los datos actuales la recomendación es tentativa. Agregue más información."
    ),
    "vacio": (
        COLOR_SUPERFICIE, COLOR_TEXTO_MUTED,
        "ⓘ Sin requisitos seleccionados: Se sugiere Monolito Modular como estilo estándar por defecto."
    ),
}

TILDES_COMUNES = {
    "aplicacion": "aplicación", "presentacion": "presentación", "rapida": "rápida",
    "modulos": "módulos", "unico": "único", "pequenos": "pequeños", "version": "versión",
    "caidas": "caídas", "trabajaran": "trabajarán", "util": "útil", "ningun": "ningún",
    "negacion": "negación", "penalizacion": "penalización", "critica": "crítica",
    "condicion": "condición", "alfabetico": "alfabético", "esta": "está"
}
_PATRON_TILDES = re.compile(r"\b(" + "|".join(TILDES_COMUNES) + r")\b", re.IGNORECASE)


def con_tildes(texto: str) -> str:
    """Añade tildes en presentación para mejorar legibilidad en español."""
    def _reemplazo(m):
        pal = TILDES_COMUNES[m.group(0).lower()]
        return pal.capitalize() if m.group(0)[0].isupper() else pal
    return _PATRON_TILDES.sub(_reemplazo, str(texto))


def bonito(texto: str) -> str:
    return str(texto).replace("_", " ")


# ===========================================================================
# 2. LIMPIEZA DE ENTRADAS (Responsabilidad estricta de Python)
# ===========================================================================
def limpiar_requisito(texto):
    sin_tildes = unicodedata.normalize("NFKD", str(texto))
    sin_tildes = "".join(c for c in sin_tildes if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "_", sin_tildes.lower()).strip("_")


def limpiar_texto_libre(texto):
    partes = [limpiar_requisito(p) for p in str(texto).split(",")]
    return [p for p in partes if p]


def atomo(texto):
    s = str(texto).replace("\\", "\\\\").replace("'", "\\'")
    return f"'{s}'"


def lista_prolog(elementos):
    return "[" + ",".join(atomo(e) for e in elementos) + "]"


def a_python(valor):
    if isinstance(valor, (bytes, bytearray)):
        return valor.decode("utf-8", errors="replace")
    if isinstance(valor, (list, tuple)):
        return [a_python(v) for v in valor]
    if isinstance(valor, (int, float, str)):
        return valor
    interno = getattr(valor, "value", None)
    if isinstance(interno, (str, bytes)):
        return a_python(interno)
    return str(valor)


# ===========================================================================
# 3. CONTROLADOR PYSWIP / PUENTE PROLOG (Motor Simbólico)
# ===========================================================================
class PuenteProlog:
    """Encapsula todas las consultas a base_conocimiento.pl."""

    def __init__(self, ruta=RUTA_BASE_CONOCIMIENTO):
        from pyswip import Prolog # type: ignore
        self.ruta = ruta.replace("\\", "/")
        self.prolog = Prolog()
        self.ultimas_metas = {}
        self.recargar()

    def recargar(self):
        self.prolog.consult(self.ruta)

    def consultar(self, meta):
        soluciones = list(self.prolog.query(meta))
        return [{k: a_python(v) for k, v in s.items()} for s in soluciones]

    def una_solucion(self, nombre, meta):
        self.ultimas_metas[nombre] = meta
        soluciones = self.consultar(f"once({meta})")
        return soluciones[0] if soluciones else None

    def _lista(self, nombre, meta):
        """Devuelve la variable Lista de la meta, o [] si Prolog no respondió."""
        r = self.una_solucion(nombre, meta)
        return r["Lista"] if r and "Lista" in r else []

    def requisitos_disponibles(self):
        return [{"id": i, "grupo": g, "etiqueta": e, "pregunta": p}
                for i, g, e, p in self._lista("requisitos", "requisitos_disponibles(Lista)")]

    def estilos(self):
        return {i: (n, d) for i, n, d in self._lista("estilos", "estilos_disponibles(Lista)")}

    def perfiles(self):
        return [(p, rs) for p, rs in self._lista("perfiles", "perfiles_disponibles(Lista)")]

    def diagnosticar(self, requisitos):
        meta = (f"diagnosticar_arquitectura({lista_prolog(requisitos)}, "
                "Mejor, Prioridad, Ranking, Descartados, Razones, Perfil, "
                "Desconocidos, Suficiencia)")
        return self.una_solucion("diagnostico", meta)

    def candidatos(self, requisitos):
        return self._lista("candidatos", f"candidatos({lista_prolog(requisitos)}, Lista)")

    def descartes(self, requisitos):
        return self._lista("descartes", f"descartes({lista_prolog(requisitos)}, Lista)")

    def que_falta(self, requisitos, negados=()):
        meta = (f"que_falta({lista_prolog(requisitos)}, {lista_prolog(negados)}, "
                "Estado, Confianza, Competencia, Sugerencias)")
        return self.una_solucion("recomendacion", meta)

    def resumen(self, requisitos):
        meta = (f"resumen_dictamen({lista_prolog(requisitos)}, "
                "Mejor, AFavor, EnContra, SinEfecto)")
        return self.una_solucion("resumen", meta)


# ===========================================================================
# 4. GESTOR DE HISTORIAL (Persistencia JSON en disco)
# ===========================================================================
class GestorHistorial:
    def __init__(self, ruta_archivo: str = RUTA_HISTORIAL):
        self.ruta_archivo = ruta_archivo

    def _leer(self):
        """Lista de evaluaciones tal como está en disco ([] si no existe o está dañado)."""
        if not os.path.exists(self.ruta_archivo):
            return []
        try:
            with open(self.ruta_archivo, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return []

    def cargar(self):
        return list(reversed(self._leer()))

    def guardar_evaluacion(self, requisitos, estilo, prioridad, estado):
        consultas = self._leer()

        nuevo_registro = {
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "requisitos": requisitos,
            "estilo": estilo,
            "prioridad": prioridad,
            "estado": estado,
        }
        consultas.append(nuevo_registro)

        with open(self.ruta_archivo, "w", encoding="utf-8") as f:
            json.dump(consultas, f, ensure_ascii=False, indent=2)

    def limpiar(self):
        if os.path.exists(self.ruta_archivo):
            try:
                os.remove(self.ruta_archivo)
            except OSError:
                pass


# ===========================================================================
# 5. UTILIDADES DE WIDGETS
# ===========================================================================
def construir_encabezado(padre, titulo, subtitulo, accion_derecha=None, texto_accion=None):
    """Construye un encabezado minimalista oscuro con tipografía limpia y línea divisoria."""
    marco = ttk.Frame(padre, style="Header.TFrame", padding=(24, 14, 24, 14))
    marco.pack(fill="x")

    fila = ttk.Frame(marco, style="Header.TFrame")
    fila.pack(fill="x")

    col_textos = ttk.Frame(fila, style="Header.TFrame")
    col_textos.pack(side="left", fill="both", expand=True)

    ttk.Label(col_textos, text=titulo, style="Titulo.TLabel").pack(anchor="w")
    ttk.Label(col_textos, text=subtitulo, style="Subtitulo.TLabel").pack(anchor="w", pady=(3, 0))

    if accion_derecha and texto_accion:
        ttk.Button(fila, text=texto_accion, style="HeaderNav.TButton", command=accion_derecha).pack(side="right", padx=4)

    # Divisor inferior sutil de 1px
    divisor = tk.Frame(padre, bg="#1e293b", height=1)
    divisor.pack(fill="x")
    return marco


class Tooltip:
    """Tooltip moderno con fondo oscuro redondeado y tipografía clara."""
    def __init__(self, widget, texto):
        self.widget = widget
        self.texto = texto
        self.ventana = None
        widget.bind("<Enter>", self._mostrar, add="+")
        widget.bind("<Leave>", self._ocultar, add="+")

    def _mostrar(self, _evento=None):
        if self.ventana or not self.texto:
            return
        x = self.widget.winfo_rootx() + 16
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 4
        self.ventana = tk.Toplevel(self.widget)
        self.ventana.wm_overrideredirect(True)
        self.ventana.wm_geometry(f"+{x}+{y}")
        tk.Label(self.ventana, text=self.texto, bg="#0f172a", fg="#f8fafc",
                 padx=10, pady=6, wraplength=340, justify="left",
                 font=(FUENTE_BASE, 9)).pack()

    def _ocultar(self, _evento=None):
        if self.ventana:
            self.ventana.destroy()
            self.ventana = None


class PanelDesplazable(tk.Frame):
    """Contenedor desplazable estilizado y fluido con canvas transparente."""
    def __init__(self, padre, **kw):
        super().__init__(padre, bg=COLOR_FONDO, **kw)
        self.canvas = tk.Canvas(self, bg=COLOR_FONDO, highlightthickness=0, bd=0)
        barra = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.interior = tk.Frame(self.canvas, bg=COLOR_FONDO)
        ventana = self.canvas.create_window((0, 0), window=self.interior, anchor="nw")

        self.interior.bind("<Configure>", lambda _e: self.canvas.configure(
            scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfigure(
            ventana, width=e.width))
        self.canvas.configure(yscrollcommand=barra.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        barra.pack(side="right", fill="y")
        self.bind("<Enter>", lambda _e: self.canvas.bind_all("<MouseWheel>", self._rueda))
        self.bind("<Leave>", lambda _e: self.canvas.unbind_all("<MouseWheel>"))

    def _rueda(self, evento):
        if self.interior.winfo_height() > self.canvas.winfo_height():
            self.canvas.yview_scroll(int(-evento.delta / 120), "units")


# ===========================================================================
# 6. VISTAS DE LA APLICACIÓN (Multi-Vista Minimalista)
# ===========================================================================

# ---------------------------------------------------------------------------
# 6.1 VISTA: INICIO / PORTAL PRINCIPAL
# ---------------------------------------------------------------------------
class VistaInicio(ttk.Frame):
    def __init__(self, padre, controlador):
        super().__init__(padre, style="Fondo.TFrame")
        self.controlador = controlador

        construir_encabezado(
            self,
            "🏛️ ArquiSelect · Sistema Experto de Arquitectura",
            "Diagnóstico, auditoría y trazabilidad lógica de decisiones de software en SWI-Prolog"
        )

        marco_central = ttk.Frame(self, style="Fondo.TFrame")
        marco_central.pack(expand=True, fill="both", padx=30, pady=20)

        # Contenedor hero centrado
        caja_centro = ttk.Frame(marco_central, style="Fondo.TFrame")
        caja_centro.place(relx=0.5, rely=0.5, anchor="center")

        # Pill badge superior
        pill = tk.Label(
            caja_centro,
            text="SISTEMA EXPERTO DE CAJA BLANCA · INFERENCIA PROLOG",
            font=(FUENTE_BASE, 8, "bold"),
            bg=COLOR_INFO_BG,
            fg=COLOR_PRIMARIO,
            padx=12,
            pady=4
        )
        pill.pack(pady=(0, 10))

        # Título Hero
        tk.Label(
            caja_centro,
            text="Selección Inteligente de Arquitecturas",
            font=(FUENTE_BASE, 22, "bold"),
            bg=COLOR_FONDO,
            fg=COLOR_TEXTO
        ).pack(pady=(0, 6))

        tk.Label(
            caja_centro,
            text="Evalúa atributos de calidad, analiza penalizaciones e incompatibilidades\n"
                 "y audita paso a paso el encadenamiento de reglas lógicas en tiempo real.",
            font=(FUENTE_BASE, 10),
            bg=COLOR_FONDO,
            fg=COLOR_TEXTO_MUTED,
            justify="center"
        ).pack(pady=(0, 24))

        # Cuadrícula de 3 Tarjetas de Acción Minimalistas
        fila_tarjetas = tk.Frame(caja_centro, bg=COLOR_FONDO)
        fila_tarjetas.pack()

        tarjetas_info = [
            {
                "icono": "🎯",
                "tag": "EVALUACIÓN",
                "tag_bg": COLOR_INFO_BG,
                "tag_fg": COLOR_PRIMARIO,
                "titulo": "Nueva Evaluación",
                "desc": "Configura los requisitos de tu proyecto, compara hipótesis arquitectónicas y resuelve empates técnicos.",
                "btn_texto": "Iniciar Evaluación →",
                "btn_estilo": "Primario.TButton",
                "comando": lambda: controlador.mostrar_vista("VistaEvaluacion")
            },
            {
                "icono": "📋",
                "tag": "HISTORIAL",
                "tag_bg": COLOR_SUPERFICIE,
                "tag_fg": COLOR_TEXTO_MUTED,
                "titulo": "Historial Guardado",
                "desc": "Consulta auditorías anteriores persistidas en disco con sus métricas de prioridad, riesgo y estado.",
                "btn_texto": "Ver Historial →",
                "btn_estilo": "Secundario.TButton",
                "comando": lambda: controlador.mostrar_vista("VistaHistorial")
            },
            {
                "icono": "⚙️",
                "tag": "BASE .PL",
                "tag_bg": COLOR_SUPERFICIE,
                "tag_fg": COLOR_TEXTO_MUTED,
                "titulo": "Base de Conocimiento",
                "desc": "Recarga reglas y hechos desde base_conocimiento.pl al instante sin necesidad de reiniciar la app.",
                "btn_texto": "Recargar .pl",
                "btn_estilo": "Suave.TButton",
                "comando": controlador.recargar_kb
            }
        ]

        for info in tarjetas_info:
            card = tk.Frame(
                fila_tarjetas,
                bg=COLOR_TARJETA,
                bd=0,
                highlightthickness=1,
                highlightbackground=COLOR_BORDE,
                padx=20,
                pady=20,
                width=270,
                height=260
            )
            card.pack(side="left", padx=10)
            card.pack_propagate(False)

            top_card = tk.Frame(card, bg=COLOR_TARJETA)
            top_card.pack(fill="x", pady=(0, 10))
            tk.Label(top_card, text=info["icono"], font=(FUENTE_BASE, 20), bg=COLOR_TARJETA).pack(side="left")
            tk.Label(
                top_card,
                text=info["tag"],
                font=(FUENTE_BASE, 8, "bold"),
                bg=info["tag_bg"],
                fg=info["tag_fg"],
                padx=8,
                pady=2
            ).pack(side="right")

            tk.Label(
                card,
                text=info["titulo"],
                font=(FUENTE_BASE, 12, "bold"),
                bg=COLOR_TARJETA,
                fg=COLOR_TEXTO
            ).pack(anchor="w", pady=(0, 6))

            tk.Label(
                card,
                text=info["desc"],
                font=(FUENTE_BASE, 9),
                bg=COLOR_TARJETA,
                fg=COLOR_TEXTO_MUTED,
                wraplength=230,
                justify="left"
            ).pack(anchor="w", fill="x", expand=True)

            ttk.Button(
                card,
                text=info["btn_texto"],
                style=info["btn_estilo"],
                command=info["comando"]
            ).pack(fill="x", pady=(10, 0))

        # Micro-insignias inferiores
        pie = tk.Frame(caja_centro, bg=COLOR_FONDO)
        pie.pack(pady=(28, 0))

        puntos = [
            "✔ Razonamiento Simbólico (Prolog)",
            "✔ Explicabilidad Completa (¿Por qué?)",
            "✔ Preguntas guiadas por el sistema experto"
        ]
        for p in puntos:
            tk.Label(
                pie,
                text=p,
                font=(FUENTE_BASE, 9),
                bg=COLOR_FONDO,
                fg=COLOR_GRIS
            ).pack(side="left", padx=12)


# ---------------------------------------------------------------------------
# 6.2 VISTA: EVALUACIÓN PRINCIPAL (Caja Blanca)
# ---------------------------------------------------------------------------
class VistaEvaluacion(ttk.Frame):
    def __init__(self, padre, controlador):
        super().__init__(padre, style="Fondo.TFrame")
        self.controlador = controlador
        self.puente = controlador.puente
        self.requisitos = self.puente.requisitos_disponibles()
        self.estilos = self.puente.estilos()
        self.perfiles = self.puente.perfiles()
        self.etiquetas = {r["id"]: con_tildes(r["etiqueta"]) for r in self.requisitos}

        self.vars = {}
        self.negados = []
        self.respuestas = []   # [(requisito, aplica)] en orden de respuesta
        self._filas_comp = []

        # Encabezado
        construir_encabezado(
            self,
            "📝 Nueva Evaluación de Arquitectura",
            "Seleccione los requisitos del sistema y audite el razonamiento de Prolog en tiempo real",
            accion_derecha=lambda: controlador.mostrar_vista("VistaInicio"),
            texto_accion="⬅ Volver al Inicio"
        )

        # Contenedor dividido en 2 columnas principales
        cuerpo = ttk.Frame(self, style="Fondo.TFrame", padding=(18, 12, 18, 12))
        cuerpo.pack(fill="both", expand=True)

        self._construir_columna_izquierda(cuerpo)
        self._construir_columna_derecha(cuerpo)

    def _construir_columna_izquierda(self, padre):
        col = ttk.Frame(padre, style="Fondo.TFrame", width=360)
        col.pack(side="left", fill="y", padx=(0, 12))
        col.pack_propagate(False)

        # 1. Tarjeta de Plantillas rápidas
        card_ej = tk.Frame(col, bg=COLOR_TARJETA, bd=0, highlightthickness=1, highlightbackground=COLOR_BORDE, padx=12, pady=10)
        card_ej.pack(fill="x", pady=(0, 8))

        tk.Label(
            card_ej, text="PLANTILLAS RÁPIDAS DE PRUEBA",
            font=(FUENTE_BASE, 8, "bold"), bg=COLOR_TARJETA, fg=COLOR_TEXTO_MUTED
        ).pack(anchor="w", pady=(0, 6))

        fila_ej = tk.Frame(card_ej, bg=COLOR_TARJETA)
        fila_ej.pack(fill="x")
        iconos_perfil = {"startup": "🚀 ", "alta_demanda": "⚡ ", "empresarial": "🏢 "}
        for perfil, reqs in self.perfiles:
            nom = iconos_perfil.get(perfil, "") + NOMBRE_PERFIL.get(perfil, bonito(perfil).capitalize()).split("/")[0].strip()
            b = ttk.Button(
                fila_ej, text=nom, style="Suave.TButton",
                command=lambda r=reqs: self.cargar_ejemplo(r)
            )
            b.pack(side="left", expand=True, fill="x", padx=2)
            Tooltip(b, "Carga: " + ", ".join(self.etiquetas.get(x, x) for x in reqs))

        # 2. Panel desplazable para las categorías de requisitos
        panel_scroll = PanelDesplazable(col)
        panel_scroll.pack(fill="both", expand=True)

        grupos = {}
        for r in self.requisitos:
            grupos.setdefault(r["grupo"], []).append(r)

        for grupo, items in grupos.items():
            marco_grp = tk.Frame(
                panel_scroll.interior, bg=COLOR_TARJETA, bd=0,
                highlightthickness=1, highlightbackground=COLOR_BORDE,
                padx=12, pady=8
            )
            marco_grp.pack(fill="x", pady=4, padx=(0, 4))

            tk.Label(
                marco_grp, text=NOMBRE_GRUPO.get(grupo, bonito(grupo)).upper(),
                font=(FUENTE_BASE, 8, "bold"), bg=COLOR_TARJETA, fg=COLOR_TEXTO_MUTED
            ).pack(anchor="w", pady=(0, 4))

            for r in items:
                var = tk.IntVar(value=0)
                self.vars[r["id"]] = var
                chk = ttk.Checkbutton(
                    marco_grp, text=self.etiquetas[r["id"]], variable=var,
                    style="Sintoma.TCheckbutton", command=self.recalcular
                )
                chk.pack(anchor="w", pady=2)
                Tooltip(chk, "¿" + con_tildes(r["pregunta"]))

        # 3. Texto libre y controles inferiores
        card_txt = tk.Frame(col, bg=COLOR_TARJETA, bd=0, highlightthickness=1, highlightbackground=COLOR_BORDE, padx=12, pady=10)
        card_txt.pack(fill="x", pady=(8, 0))

        tk.Label(
            card_txt, text="OTROS REQUISITOS (TEXTO LIBRE)",
            font=(FUENTE_BASE, 8, "bold"), bg=COLOR_TARJETA, fg=COLOR_TEXTO_MUTED
        ).pack(anchor="w", pady=(0, 6))

        fila_txt = tk.Frame(card_txt, bg=COLOR_TARJETA)
        fila_txt.pack(fill="x")
        self.texto_libre = tk.StringVar()
        ent = ttk.Entry(fila_txt, textvariable=self.texto_libre, font=(FUENTE_BASE, 9))
        ent.pack(side="left", fill="x", expand=True)
        ent.bind("<Return>", lambda _e: self.recalcular())

        ttk.Button(fila_txt, text="Añadir", style="Secundario.TButton", command=self.recalcular).pack(side="left", padx=(6, 0))

        self.lbl_desconocidos = tk.Label(
            card_txt, text="", font=(FUENTE_BASE, 8),
            bg=COLOR_TARJETA, fg=COLOR_AMBAR, wraplength=320, justify="left"
        )
        self.lbl_desconocidos.pack(anchor="w", pady=(4, 0))

        # Botones de acción inferiores
        fila_acciones = ttk.Frame(col, style="Fondo.TFrame")
        fila_acciones.pack(fill="x", pady=(8, 0))
        ttk.Button(fila_acciones, text="🗑 Limpiar", style="Suave.TButton", command=self.limpiar).pack(side="left", expand=True, fill="x", padx=(0, 3))
        ttk.Button(fila_acciones, text="💾 Guardar", style="Primario.TButton", command=self.guardar_en_historial).pack(side="left", expand=True, fill="x", padx=(3, 0))

    def _construir_columna_derecha(self, padre):
        col = ttk.Frame(padre, style="Fondo.TFrame")
        col.pack(side="left", fill="both", expand=True)

        # Fila superior: Tarjeta Dictamen (ancho completo)
        fila_top = ttk.Frame(col, style="Fondo.TFrame")
        fila_top.pack(fill="x", pady=(0, 10))

        # Tarjeta Dictamen
        self.card_dictamen = tk.Frame(fila_top, bg=COLOR_TARJETA, bd=0, highlightthickness=1, highlightbackground=COLOR_BORDE, padx=18, pady=14)
        self.card_dictamen.pack(side="left", fill="both", expand=True)

        tk.Label(
            self.card_dictamen, text="ESTILO DE ARQUITECTURA RECOMENDADO",
            font=(FUENTE_BASE, 8, "bold"), bg=COLOR_TARJETA, fg=COLOR_TEXTO_MUTED
        ).pack(anchor="w")

        self.lbl_estilo = tk.Label(
            self.card_dictamen, text="", font=(FUENTE_BASE, 18, "bold"),
            bg=COLOR_TARJETA, fg=COLOR_TEXTO
        )
        self.lbl_estilo.pack(anchor="w", pady=(2, 2))

        self.lbl_desc_estilo = tk.Label(
            self.card_dictamen, text="", font=(FUENTE_BASE, 10),
            bg=COLOR_TARJETA, fg="#475569", wraplength=820, justify="left"
        )
        self.lbl_desc_estilo.pack(anchor="w", pady=(0, 8))

        # Chips de Métricas (Badges estilizados)
        fila_chips = tk.Frame(self.card_dictamen, bg=COLOR_TARJETA)
        fila_chips.pack(anchor="w", pady=(0, 8))

        self.chips = {}
        for metrica in ("Prioridad", "Riesgo", "Confianza"):
            caja = tk.Frame(fila_chips, bg=COLOR_TARJETA)
            caja.pack(side="left", padx=(0, 14))
            tk.Label(caja, text=metrica.upper(), font=(FUENTE_BASE, 8, "bold"),
                     bg=COLOR_TARJETA, fg=COLOR_TEXTO_MUTED).pack(anchor="w")
            chip = tk.Label(caja, text="—", font=(FUENTE_BASE, 9, "bold"),
                            fg=COLOR_TEXTO_MUTED, bg=COLOR_SUPERFICIE, padx=10, pady=2)
            chip.pack(anchor="w", pady=(2, 0))
            self.chips[metrica] = chip

        # Mensaje de estado (Banner limpio)
        self.lbl_estado = tk.Label(
            self.card_dictamen, text="", font=(FUENTE_BASE, 9),
            padx=12, pady=6, anchor="w", justify="left", wraplength=820
        )
        self.lbl_estado.pack(fill="x")

        # Cuaderno de Pestañas (Notebook)
        self.pestanas = ttk.Notebook(col)
        self.pestanas.pack(fill="both", expand=True)

        self._pestana_preguntas()
        self._pestana_resumen()

    def _pestana_preguntas(self):
        tab = ttk.Frame(self.pestanas, padding=12)
        self.pestanas.add(tab, text="  💬 Preguntas guiadas  ")

        self.lbl_progreso = tk.Label(tab, text="", font=(FUENTE_BASE, 10, "bold"), fg=COLOR_TEXTO)
        self.lbl_progreso.pack(anchor="w", pady=(0, 6))

        # Tarjeta de la pregunta actual (se reconstruye en cada recálculo)
        self.card_pregunta = tk.Frame(tab, bg=COLOR_TARJETA, bd=0, highlightthickness=1,
                                      highlightbackground=COLOR_BORDE, padx=18, pady=14)
        self.card_pregunta.pack(fill="x", pady=(0, 10))

        # Lista corta de respuestas dadas
        card_resp = tk.Frame(tab, bg=COLOR_TARJETA, bd=0, highlightthickness=1,
                             highlightbackground=COLOR_BORDE, padx=14, pady=10)
        card_resp.pack(fill="both", expand=True)

        fila_cab = tk.Frame(card_resp, bg=COLOR_TARJETA)
        fila_cab.pack(fill="x", pady=(0, 4))
        tk.Label(fila_cab, text="RESPUESTAS DADAS", font=(FUENTE_BASE, 8, "bold"),
                 bg=COLOR_TARJETA, fg=COLOR_TEXTO_MUTED).pack(side="left")
        self.btn_deshacer = ttk.Button(fila_cab, text="↶ Deshacer última", style="Suave.TButton",
                                       command=self.deshacer_respuesta)
        self.btn_deshacer.pack(side="right")

        panel = PanelDesplazable(card_resp)
        panel.pack(fill="both", expand=True)
        for w in (panel, panel.canvas, panel.interior):
            w.configure(bg=COLOR_TARJETA)
        self.zona_respuestas = panel.interior

    def _pestana_resumen(self):
        tab = ttk.Frame(self.pestanas, padding=12)
        self.pestanas.add(tab, text="  📊 Resumen y Ranking  ")

        panel = PanelDesplazable(tab)
        panel.pack(fill="both", expand=True)
        cuerpo = panel.interior

        # Mensaje para la evaluación vacía
        self.sec_vacio = tk.Label(cuerpo, text="Responde las preguntas para ver las opciones",
                                  font=(FUENTE_BASE, 10), bg=COLOR_FONDO, fg=COLOR_TEXTO_MUTED)

        # 1) Respuesta: estilo recomendado + razonamiento a favor
        self.sec_respuesta = tk.Frame(cuerpo, bg=COLOR_TARJETA, bd=0, highlightthickness=1,
                                      highlightbackground=COLOR_BORDE, padx=18, pady=14)
        tk.Label(self.sec_respuesta, text="RESPUESTA DEL SISTEMA EXPERTO", font=(FUENTE_BASE, 8, "bold"),
                 bg=COLOR_TARJETA, fg=COLOR_PRIMARIO).pack(anchor="w")
        self.lbl_res_nombre = tk.Label(self.sec_respuesta, text="", font=(FUENTE_BASE, 16, "bold"),
                                       bg=COLOR_TARJETA, fg=COLOR_TEXTO)
        self.lbl_res_nombre.pack(anchor="w", pady=(2, 0))
        self.lbl_res_desc = tk.Label(self.sec_respuesta, text="", font=(FUENTE_BASE, 10), bg=COLOR_TARJETA,
                                     fg="#475569", wraplength=760, justify="left")
        self.lbl_res_desc.pack(anchor="w", pady=(0, 8))
        self.zona_razones = tk.Frame(self.sec_respuesta, bg=COLOR_TARJETA)
        self.zona_razones.pack(fill="x")

        # 2) Comparativa de estilos que todavía pueden ser la respuesta
        self.sec_comp = tk.Frame(cuerpo, bg=COLOR_FONDO)
        tk.Label(self.sec_comp, text="Comparativa de Estilos Arquitectónicos:", bg=COLOR_FONDO,
                 font=(FUENTE_BASE, 10, "bold"), fg=COLOR_TEXTO).pack(anchor="w", pady=(0, 6))
        self.cv_comp = tk.Canvas(self.sec_comp, bg=COLOR_TARJETA, highlightthickness=1,
                                 highlightbackground=COLOR_BORDE, height=130)
        self.cv_comp.pack(fill="x")
        self.cv_comp.bind("<Configure>", lambda _e: self._dibujar_comparacion())

        # 3) Por qué se descartaron las demás
        self.sec_descartes = tk.Frame(cuerpo, bg=COLOR_TARJETA, bd=0, highlightthickness=1,
                                      highlightbackground=COLOR_BORDE, padx=18, pady=12)
        tk.Label(self.sec_descartes, text="POR QUÉ SE DESCARTARON LAS DEMÁS", font=(FUENTE_BASE, 8, "bold"),
                 bg=COLOR_TARJETA, fg=COLOR_PELIGRO_TEXT).pack(anchor="w", pady=(0, 4))
        self.zona_descartes = tk.Frame(self.sec_descartes, bg=COLOR_TARJETA)
        self.zona_descartes.pack(fill="x")

    def _linea(self, padre, texto, color):
        tk.Label(padre, text=texto, font=(FUENTE_BASE, 10), bg=COLOR_TARJETA, fg=color,
                 wraplength=760, justify="left").pack(anchor="w", padx=(12, 0), pady=1)

    # --- Acciones y sincronización ---
    def al_mostrar(self):
        self.recalcular()

    def seleccion(self):
        elegidos = [r for r, v in self.vars.items() if v.get() == 1]
        elegidos += limpiar_texto_libre(self.texto_libre.get())
        return list(dict.fromkeys(elegidos))

    def limpiar(self):
        self.cargar_ejemplo(())

    def cargar_ejemplo(self, reqs):
        for r, v in self.vars.items():
            v.set(1 if r in reqs else 0)
        self.texto_libre.set("")
        self.negados = []
        self.respuestas = []
        self.pestanas.select(0)
        self.recalcular()

    def agregar_dato(self, req):
        if req in self.vars:
            self.vars[req].set(1)
        self.respuestas.append((req, True))
        self.recalcular()

    def negar_dato(self, req):
        if req not in self.negados:
            self.negados.append(req)
        self.respuestas.append((req, False))
        self.recalcular()

    def deshacer_respuesta(self):
        if not self.respuestas:
            return
        req, aplica = self.respuestas.pop()
        if aplica and req in self.vars:
            self.vars[req].set(0)
        elif not aplica and req in self.negados:
            self.negados.remove(req)
        self.recalcular()

    def _sincronizar_respuestas(self, reqs):
        """Mantiene la lista de respuestas alineada con casillas y negados:
        una casilla marcada a mano cuenta como "Sí"; una desmarcada se retira."""
        self.respuestas = [(r, a) for r, a in self.respuestas
                           if (r in reqs if a else r in self.negados)]
        respondidos = {r for r, _ in self.respuestas}
        for r in reqs:
            if r in self.vars and r not in respondidos:
                self.respuestas.append((r, True))

    def recalcular(self):
        reqs = self.seleccion()
        self.negados = [n for n in self.negados if n not in reqs]
        self._sincronizar_respuestas(reqs)

        try:
            d = self.puente.diagnosticar(reqs)
            qf = self.puente.que_falta(reqs, self.negados)
            rs = self.puente.resumen(reqs)
            cands = self.puente.candidatos(reqs)
            descs = self.puente.descartes(reqs)
        except Exception as error:
            messagebox.showerror("Error en Prolog", f"Ocurrió un error al consultar SWI-Prolog:\n{error}")
            return

        if not d or not qf or not rs:
            return

        self._mostrar_dictamen(d, qf)
        self._mostrar_preguntas(d, qf)
        self._mostrar_resumen(d, qf, rs, cands, descs)

    def guardar_en_historial(self):
        reqs = self.seleccion()
        if not reqs:
            messagebox.showwarning("Atención", "Seleccione al menos un requisito antes de guardar en el historial.")
            return

        d = self.puente.diagnosticar(reqs)
        qf = self.puente.que_falta(reqs, self.negados)
        if not d:
            return

        estilo_nom = self.estilos.get(d["Mejor"], (d["Mejor"], ""))[0]
        reqs_legibles = [self.etiquetas.get(r, r) for r in reqs]

        self.controlador.historial.guardar_evaluacion(
            reqs_legibles,
            estilo_nom,
            bonito(d["Prioridad"]),
            bonito(qf["Estado"])
        )
        messagebox.showinfo("Historial", "Evaluación guardada exitosamente en el historial.")

    # --- Presentación de resultados ---
    def nombre_estilo(self, estilo):
        return self.estilos.get(estilo, (bonito(estilo), ""))[0]

    def _chip(self, nombre, valor):
        if valor in ("por_defecto", "nula", None):
            txt = "—"
            bg_c, fg_c = COLOR_SUPERFICIE, COLOR_TEXTO_MUTED
        else:
            txt = bonito(valor).upper()
            bg_c, fg_c = COLOR_PRIORIDAD.get(str(valor).lower(), (COLOR_SUPERFICIE, COLOR_TEXTO_MUTED))
        self.chips[nombre].configure(text=f"  {txt}  ", bg=bg_c, fg=fg_c)

    def _mostrar_dictamen(self, d, qf):
        estado = qf["Estado"]
        if estado == "vacio":
            self.lbl_estilo.configure(text="Monolito Modular (Por defecto)")
            self.lbl_desc_estilo.configure(text="Marque a la izquierda las características del proyecto para generar una recomendación personalizada.")
            for c in self.chips:
                self._chip(c, None)
        else:
            nom, desc = self.estilos.get(d["Mejor"], (d["Mejor"], ""))
            self.lbl_estilo.configure(text=nom)
            self.lbl_desc_estilo.configure(text=con_tildes(desc))
            riesgo = next((f[3] for f in d["Ranking"] if f[0] == d["Mejor"]), "bajo")
            self._chip("Prioridad", d["Prioridad"])
            self._chip("Riesgo", riesgo)
            self._chip("Confianza", qf["Confianza"])

        bg_est, fg_est, msg_est = ESTADO_DICTAMEN.get(
            estado,
            (COLOR_SUPERFICIE, COLOR_TEXTO, estado)
        )
        self.lbl_estado.configure(text=msg_est, bg=bg_est, fg=fg_est)

        self.lbl_desconocidos.configure(
            text=("Ignorado (no reconocido): " + ", ".join(d["Desconocidos"])) if d["Desconocidos"] else ""
        )

    def _mostrar_preguntas(self, d, qf):
        """Flujo tipo asistente: una pregunta a la vez, tomada de que_falta/6."""
        lider = self.nombre_estilo(d["Mejor"])
        if qf["Estado"] == "vacio":
            lider += " (por defecto)"
        terminado = not qf["Sugerencias"] or qf["Estado"] == "definitivo"

        if terminado:
            self.lbl_progreso.configure(
                text=f"{len(self.respuestas)} respuesta(s) · Estilo líder actual: {lider}")
        else:
            self.lbl_progreso.configure(
                text=f"Pregunta {len(self.respuestas) + 1} · Estilo líder actual: {lider}")

        card = self.card_pregunta
        for h in card.winfo_children():
            h.destroy()

        if terminado:
            tk.Label(card, text="✔ Evaluación lista", font=(FUENTE_BASE, 14, "bold"),
                     bg=COLOR_TARJETA, fg=COLOR_EXITO_TEXT).pack(anchor="w")
            motivo = ("El dictamen es definitivo." if qf["Estado"] == "definitivo"
                      else "El sistema experto no tiene más preguntas que cambien el dictamen.")
            tk.Label(card, text=f"{motivo} Recomendación: {lider}.", font=(FUENTE_BASE, 10),
                     bg=COLOR_TARJETA, fg=COLOR_TEXTO_MUTED, wraplength=760, justify="left").pack(anchor="w", pady=(4, 0))
            ttk.Button(card, text="📊 Ver resumen →", style="Primario.TButton",
                       command=lambda: self.pestanas.select(1)).pack(anchor="w", pady=(12, 0))
        else:
            req, poder, preg, efectos = qf["Sugerencias"][0]
            tk.Label(card, text="PREGUNTA DEL SISTEMA EXPERTO", font=(FUENTE_BASE, 8, "bold"),
                     bg=COLOR_TARJETA, fg=COLOR_PRIMARIO).pack(anchor="w")
            tk.Label(card, text=f"¿{con_tildes(preg)}", font=(FUENTE_BASE, 13, "bold"),
                     bg=COLOR_TARJETA, fg=COLOR_TEXTO, wraplength=760, justify="left").pack(anchor="w", pady=(6, 8))

            tk.Label(card, text=f"IMPACTO SI RESPONDE «SÍ» (Poder: {poder})", font=(FUENTE_BASE, 8, "bold"),
                     bg=COLOR_TARJETA, fg=COLOR_TEXTO_MUTED).pack(anchor="w")
            mostrados = 0
            for est, tipo, delta in efectos:
                if tipo == "descarta":
                    ef, col_ef = f"✕ {self.nombre_estilo(est)} se descarta", COLOR_PELIGRO_TEXT
                elif tipo == "neutro":
                    continue
                else:
                    signo = "+" if delta > 0 else ""
                    ef = f"{'▲' if delta > 0 else '▼'} {self.nombre_estilo(est)}: {signo}{delta} pts"
                    col_ef = COLOR_EXITO_TEXT if delta > 0 else COLOR_PELIGRO_TEXT
                tk.Label(card, text=f"   • {ef}", font=(FUENTE_BASE, 9),
                         bg=COLOR_TARJETA, fg=col_ef).pack(anchor="w")
                mostrados += 1
            if not mostrados:
                tk.Label(card, text="   • No altera puntajes principales", font=(FUENTE_BASE, 9),
                         bg=COLOR_TARJETA, fg=COLOR_TEXTO_MUTED).pack(anchor="w")

            fila_btn = tk.Frame(card, bg=COLOR_TARJETA)
            fila_btn.pack(anchor="w", pady=(12, 0))
            ttk.Button(fila_btn, text="✔ Sí, aplica", style="Primario.TButton",
                       command=lambda r=req: self.agregar_dato(r)).pack(side="left", padx=(0, 6))
            ttk.Button(fila_btn, text="✕ No aplica", style="Suave.TButton",
                       command=lambda r=req: self.negar_dato(r)).pack(side="left")

        # Respuestas dadas (más reciente arriba)
        for h in self.zona_respuestas.winfo_children():
            h.destroy()
        if not self.respuestas:
            tk.Label(self.zona_respuestas, text="Aún no hay respuestas.", font=(FUENTE_BASE, 9),
                     bg=COLOR_TARJETA, fg=COLOR_TEXTO_MUTED).pack(anchor="w")
        for i, (respondido, aplica) in reversed(list(enumerate(self.respuestas, start=1))):
            marca, col = ("✔ Sí", COLOR_EXITO_TEXT) if aplica else ("✕ No", COLOR_PELIGRO_TEXT)
            fila = tk.Frame(self.zona_respuestas, bg=COLOR_TARJETA)
            fila.pack(fill="x", pady=1)
            tk.Label(fila, text=f"{i}.", width=3, anchor="w", font=(FUENTE_BASE, 9),
                     bg=COLOR_TARJETA, fg=COLOR_TEXTO_MUTED).pack(side="left")
            tk.Label(fila, text=marca, width=5, anchor="w", font=(FUENTE_BASE, 9, "bold"),
                     bg=COLOR_TARJETA, fg=col).pack(side="left")
            tk.Label(fila, text=self.etiquetas.get(respondido, respondido), font=(FUENTE_BASE, 9),
                     bg=COLOR_TARJETA, fg=COLOR_TEXTO).pack(side="left")
        self.btn_deshacer.state(["!disabled"] if self.respuestas else ["disabled"])

    def _mostrar_resumen(self, d, qf, rs, cands, descs):
        filas = []
        for estilo, puntaje, _pr, _ri in cands:
            rol = "lider" if estilo == d["Mejor"] else ("competencia" if estilo in qf["Competencia"] else "otro")
            filas.append((estilo, puntaje, rol))
        self._filas_comp = filas

        for sec in (self.sec_vacio, self.sec_respuesta, self.sec_comp, self.sec_descartes):
            sec.pack_forget()

        if qf["Estado"] == "vacio":
            self.sec_vacio.pack(anchor="w", pady=8)
            return

        # 1) Respuesta
        nom, desc = self.estilos.get(rs["Mejor"], (bonito(rs["Mejor"]), ""))
        puntaje = next((p for e, p, _, _ in cands if e == rs["Mejor"]), None)
        sufijo = f"  ·  {puntaje} pts" if puntaje is not None else "  ·  recomendación por defecto"
        self.lbl_res_nombre.configure(text=f"★ {nom}{sufijo}")
        self.lbl_res_desc.configure(text=con_tildes(desc))

        for h in self.zona_razones.winfo_children():
            h.destroy()
        tk.Label(self.zona_razones, text=f"Razonamiento a favor de {nom}:", font=(FUENTE_BASE, 10, "bold"),
                 bg=COLOR_TARJETA, fg=COLOR_TEXTO).pack(anchor="w", pady=(4, 4))
        for atributo, peso, reqs in rs["AFavor"]:
            causas = ", ".join(self.etiquetas.get(r, r) for r in reqs)
            self._linea(self.zona_razones, f"✔ Favorece {bonito(atributo)} (+{peso}) debido a: {causas}", COLOR_EXITO_TEXT)
        for req, peso in rs["EnContra"]:
            self._linea(self.zona_razones, f"✖ Penalizado con -{peso} puntos por: {self.etiquetas.get(req, req)}", COLOR_PELIGRO_TEXT)
        self.sec_respuesta.pack(fill="x", pady=(0, 12), padx=(0, 4))

        # 2) Comparativa
        self.sec_comp.pack(fill="x", pady=(0, 12), padx=(0, 4))
        self._dibujar_comparacion()

        # 3) Descartados (solo si hay)
        for h in self.zona_descartes.winfo_children():
            h.destroy()
        for estilo, tipo, motivo in descs:
            if tipo == "exclusion":
                txt = f"✖ {self.nombre_estilo(estilo)}: incompatible con «{self.etiquetas.get(motivo, motivo)}»"
            else:
                txt = f"✖ {self.nombre_estilo(estilo)}: sin evidencia a favor (puntaje {motivo})"
            self._linea(self.zona_descartes, txt, COLOR_PELIGRO_TEXT)
        if descs:
            self.sec_descartes.pack(fill="x", padx=(0, 4))

    def _dibujar_barra_pildora(self, canvas, x1, y1, x2, y2, radio, color):
        """Dibuja una barra con extremos redondeados en el canvas."""
        ancho = x2 - x1
        alto = y2 - y1
        if ancho <= 0 or alto <= 0:
            return
        r = min(radio, alto // 2, ancho // 2)
        if r <= 1 or ancho < 2 * r:
            canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="")
            return
        d = 2 * r
        canvas.create_rectangle(x1 + r, y1, x2 - r, y2, fill=color, outline="")
        canvas.create_rectangle(x1, y1 + r, x2, y2 - r, fill=color, outline="")
        canvas.create_arc(x1, y1, x1 + d, y1 + d, start=90, extent=90, fill=color, outline="")
        canvas.create_arc(x2 - d, y1, x2, y1 + d, start=0, extent=90, fill=color, outline="")
        canvas.create_arc(x1, y2 - d, x1 + d, y2, start=180, extent=90, fill=color, outline="")
        canvas.create_arc(x2 - d, y2 - d, x2, y2, start=270, extent=90, fill=color, outline="")

    def _dibujar_comparacion(self):
        c = self.cv_comp
        c.delete("all")
        filas = self._filas_comp
        if not filas:
            c.create_text(16, 24, anchor="w", text="Responde las preguntas para ver las opciones",
                          fill=COLOR_TEXTO_MUTED, font=(FUENTE_BASE, 9))
            c.configure(height=48)
            return

        ancho = max(c.winfo_width(), 460)
        x0 = 210
        xmax = ancho - 80
        alto_fila = 28
        maximo = max([p for _, p, _ in filas] + [1])

        for i, (estilo, puntaje, rol) in enumerate(filas):
            y = 8 + i * alto_fila
            if rol == "lider":
                ico, col_txt, fnt = "★ ", COLOR_PRIMARIO, (FUENTE_BASE, 9, "bold")
            elif rol == "competencia":
                ico, col_txt, fnt = "● ", COLOR_AMBAR_TEXT, (FUENTE_BASE, 9, "bold")
            else:
                ico, col_txt, fnt = "○ ", COLOR_TEXTO, (FUENTE_BASE, 9)

            c.create_text(14, y + 10, anchor="w", text=f"{ico}{self.nombre_estilo(estilo)}",
                          fill=col_txt, font=fnt)

            # Pista de fondo (track)
            self._dibujar_barra_pildora(c, x0, y + 3, xmax, y + 17, 7, COLOR_SUPERFICIE)

            # Barra rellena
            col_barra = COLOR_ROL.get(rol, "#cbd5e1")
            ancho_pts = (xmax - x0) * max(puntaje, 0) / maximo
            if ancho_pts > 0:
                self._dibujar_barra_pildora(c, x0, y + 3, x0 + ancho_pts, y + 17, 7, col_barra)

            # Puntuación a la derecha
            c.create_text(xmax + 8, y + 10, anchor="w", text=f"{puntaje} pts",
                          font=(FUENTE_BASE, 9, "bold"), fill=col_barra if rol == "lider" else COLOR_TEXTO)

        c.configure(height=len(filas) * alto_fila + 16)



# ---------------------------------------------------------------------------
# 6.3 VISTA: HISTORIAL DE EVALUACIONES
# ---------------------------------------------------------------------------
class VistaHistorial(ttk.Frame):
    def __init__(self, padre, controlador):
        super().__init__(padre, style="Fondo.TFrame")
        self.controlador = controlador

        construir_encabezado(
            self,
            "📋 Historial de Evaluaciones",
            "Registro auditable de diagnósticos y recomendaciones guardadas en disco",
            accion_derecha=lambda: controlador.mostrar_vista("VistaInicio"),
            texto_accion="⬅ Volver al Inicio"
        )

        marco_contenido = ttk.Frame(self, style="Fondo.TFrame", padding=(24, 16, 24, 16))
        marco_contenido.pack(fill="both", expand=True)

        card_tabla = tk.Frame(
            marco_contenido, bg=COLOR_TARJETA, bd=0,
            highlightthickness=1, highlightbackground=COLOR_BORDE,
            padx=16, pady=16
        )
        card_tabla.pack(fill="both", expand=True)

        # Barra superior informativa
        fila_info = tk.Frame(card_tabla, bg=COLOR_TARJETA)
        fila_info.pack(fill="x", pady=(0, 12))

        self.lbl_contador = tk.Label(
            fila_info, text="Evaluaciones registradas",
            font=(FUENTE_BASE, 10, "bold"), bg=COLOR_TARJETA, fg=COLOR_TEXTO
        )
        self.lbl_contador.pack(side="left")

        cols = ("fecha", "requisitos", "estilo", "prioridad", "estado")
        self.tabla = ttk.Treeview(card_tabla, columns=cols, show="headings", height=16)

        self.tabla.heading("fecha", text="Fecha / Hora")
        self.tabla.heading("requisitos", text="Requisitos Seleccionados")
        self.tabla.heading("estilo", text="Estilo Recomendado")
        self.tabla.heading("prioridad", text="Prioridad")
        self.tabla.heading("estado", text="Estado del Dictamen")

        self.tabla.column("fecha", width=140, anchor="w")
        self.tabla.column("requisitos", width=420, anchor="w")
        self.tabla.column("estilo", width=220, anchor="w")
        self.tabla.column("prioridad", width=100, anchor="center")
        self.tabla.column("estado", width=140, anchor="center")

        sb = ttk.Scrollbar(card_tabla, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=sb.set)

        self.tabla.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        self.lbl_vacio = tk.Label(
            card_tabla, text="No hay evaluaciones guardadas en el historial todavía.",
            font=(FUENTE_BASE, 10, "italic"), bg=COLOR_TARJETA, fg=COLOR_TEXTO_MUTED
        )

        fila_botones = ttk.Frame(marco_contenido, style="Fondo.TFrame", padding=(0, 12, 0, 0))
        fila_botones.pack(fill="x")

        ttk.Button(
            fila_botones, text="📝 Nueva Evaluación", style="Primario.TButton",
            command=lambda: controlador.mostrar_vista("VistaEvaluacion")
        ).pack(side="left", padx=(0, 6))

        ttk.Button(
            fila_botones, text="🗑 Borrar Historial", style="Peligro.TButton",
            command=self.borrar_historial
        ).pack(side="left", padx=6)

    def al_mostrar(self):
        for f in self.tabla.get_children():
            self.tabla.delete(f)

        consultas = self.controlador.historial.cargar()
        self.lbl_contador.configure(text=f"Total de evaluaciones registradas: {len(consultas)}")
        if not consultas:
            self.lbl_vacio.place(relx=0.5, rely=0.5, anchor="center")
            return

        self.lbl_vacio.place_forget()
        for c in consultas:
            self.tabla.insert(
                "", "end",
                values=(
                    c.get("fecha", ""),
                    ", ".join(c.get("requisitos", [])),
                    c.get("estilo", ""),
                    c.get("prioridad", ""),
                    c.get("estado", "")
                )
            )

    def borrar_historial(self):
        if messagebox.askyesno("Confirmar", "¿Está seguro de eliminar todo el historial de evaluaciones?"):
            self.controlador.historial.limpiar()
            self.al_mostrar()


# ===========================================================================
# 7. CONTROLADOR PRINCIPAL (Tkinter Tk)
# ===========================================================================
class ControladorApp(tk.Tk):
    def __init__(self, puente: PuenteProlog, historial: GestorHistorial):
        super().__init__()
        self.puente = puente
        self.historial = historial

        self.title("ArquiSelect · Sistema Experto de Arquitectura de Software")
        self.geometry("1280x820")
        self.minsize(1080, 680)
        self.configure(bg=COLOR_FONDO)

        try:
            self.state("zoomed")  # Maximizado en Windows
        except tk.TclError:
            pass

        self._configurar_estilos_ttk()

        # Contenedor apilado para navegación entre vistas
        contenedor = tk.Frame(self, bg=COLOR_FONDO)
        contenedor.pack(fill="both", expand=True)
        contenedor.grid_rowconfigure(0, weight=1)
        contenedor.grid_columnconfigure(0, weight=1)

        self.vistas = {}
        for ClaseVista in (VistaInicio, VistaEvaluacion, VistaHistorial):
            vista = ClaseVista(contenedor, self)
            self.vistas[ClaseVista.__name__] = vista
            vista.grid(row=0, column=0, sticky="nsew")

        self.mostrar_vista("VistaInicio")

    def _configurar_estilos_ttk(self):
        estilo = ttk.Style(self)
        estilo.theme_use("clam")

        # Fondos generales
        estilo.configure("Fondo.TFrame", background=COLOR_FONDO)
        estilo.configure("Header.TFrame", background=COLOR_HEADER)

        # Etiquetas
        estilo.configure(
            "Titulo.TLabel", background=COLOR_HEADER, foreground="#ffffff",
            font=(FUENTE_BASE, 17, "bold")
        )
        estilo.configure(
            "Subtitulo.TLabel", background=COLOR_HEADER, foreground=COLOR_HEADER_SUB,
            font=(FUENTE_BASE, 10)
        )
        estilo.configure(
            "Sintoma.TCheckbutton", background=COLOR_TARJETA, foreground=COLOR_TEXTO,
            font=(FUENTE_BASE, 9)
        )
        estilo.map("Sintoma.TCheckbutton", background=[("active", COLOR_SUPERFICIE)])

        # Botón Primario (Indigo Moderno)
        estilo.configure(
            "Primario.TButton", background=COLOR_PRIMARIO, foreground="#ffffff",
            font=(FUENTE_BASE, 10, "bold"), padding=(12, 6), borderwidth=0, relief="flat"
        )
        estilo.map("Primario.TButton",
                   background=[("active", COLOR_PRIMARIO_HOVER), ("disabled", COLOR_GRIS)])

        # Botón Secundario (Slate-900)
        estilo.configure(
            "Secundario.TButton", background=COLOR_SECUNDARIO, foreground="#ffffff",
            font=(FUENTE_BASE, 10, "bold"), padding=(12, 6), borderwidth=0, relief="flat"
        )
        estilo.map("Secundario.TButton",
                   background=[("active", COLOR_SECUNDARIO_HOVER), ("disabled", COLOR_GRIS)])

        # Botón Suave / Ghost (Slate-100)
        estilo.configure(
            "Suave.TButton", background=COLOR_SUAVE, foreground="#334155",
            font=(FUENTE_BASE, 9), padding=(10, 5), borderwidth=0, relief="flat"
        )
        estilo.map("Suave.TButton",
                   background=[("active", COLOR_SUAVE_HOVER), ("disabled", COLOR_FONDO)])

        # Botón Peligro (Rose suave)
        estilo.configure(
            "Peligro.TButton", background=COLOR_PELIGRO_BG, foreground=COLOR_PELIGRO_TEXT,
            font=(FUENTE_BASE, 9, "bold"), padding=(10, 5), borderwidth=0, relief="flat"
        )
        estilo.map("Peligro.TButton",
                   background=[("active", "#fecaca")])

        # Botón de Navegación en Header
        estilo.configure(
            "HeaderNav.TButton", background="#1e293b", foreground="#f8fafc",
            font=(FUENTE_BASE, 9, "bold"), padding=(12, 6), borderwidth=0, relief="flat"
        )
        estilo.map("HeaderNav.TButton",
                   background=[("active", "#334155")])

        # Estilo Pestañas Notebook
        estilo.configure("TNotebook", background=COLOR_FONDO, borderwidth=0)
        estilo.configure(
            "TNotebook.Tab", padding=(16, 7), font=(FUENTE_BASE, 10),
            background=COLOR_SUPERFICIE, foreground=COLOR_TEXTO_MUTED, borderwidth=0
        )
        estilo.map("TNotebook.Tab",
                   background=[("selected", COLOR_TARJETA)],
                   foreground=[("selected", COLOR_PRIMARIO)])

        # Estilo Treeview (Tablas)
        estilo.configure(
            "Treeview", rowheight=28, background=COLOR_TARJETA,
            fieldbackground=COLOR_TARJETA, bordercolor=COLOR_BORDE,
            borderwidth=1, font=(FUENTE_BASE, 9)
        )
        estilo.configure(
            "Treeview.Heading", font=(FUENTE_BASE, 9, "bold"),
            background=COLOR_SUPERFICIE, foreground=COLOR_TEXTO_MUTED,
            relief="flat", borderwidth=0, padding=6
        )
        estilo.map("Treeview.Heading",
                   background=[("active", COLOR_BORDE)])

        # Entry
        estilo.configure("TEntry", fieldbackground=COLOR_TARJETA, bordercolor=COLOR_BORDE, padding=4)

        # Scrollbars modernos
        estilo.configure("Vertical.TScrollbar", background=COLOR_BORDE, troughcolor=COLOR_FONDO,
                         bordercolor=COLOR_FONDO, arrowcolor=COLOR_TEXTO_MUTED)

    def mostrar_vista(self, nombre_vista):
        vista = self.vistas[nombre_vista]
        if hasattr(vista, "al_mostrar"):
            vista.al_mostrar()
        vista.tkraise()

    def recargar_kb(self):
        try:
            self.puente.recargar()
            if "VistaEvaluacion" in self.vistas:
                self.vistas["VistaEvaluacion"].recalcular()
            messagebox.showinfo("ArquiSelect", "Base de conocimiento Prolog recargada correctamente.")
        except Exception as error:
            messagebox.showerror("Error al recargar", f"No se pudo recargar la base de conocimiento:\n{error}")


# ===========================================================================
# 8. PUNTO DE ENTRADA PRINCIPAL
# ===========================================================================
def main():
    try:
        puente = PuenteProlog(RUTA_BASE_CONOCIMIENTO)
    except Exception as error:
        raiz = tk.Tk()
        raiz.withdraw()
        messagebox.showerror(
            "ArquiSelect - Error",
            f"No se pudo iniciar el puente con SWI-Prolog:\n{error}\n\n"
            "Verifique que SWI-Prolog esté instalado y en el PATH del sistema."
        )
        sys.exit(1)

    gestor_historial = GestorHistorial(RUTA_HISTORIAL)
    app = ControladorApp(puente, gestor_historial)
    app.mainloop()


if __name__ == "__main__":
    main()
