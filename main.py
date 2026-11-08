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
import hmac
import json
import hashlib
from datetime import datetime

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from tkinter import font as tkfont

# ===========================================================================
# 1. CONSTANTES, RUTAS Y PALETA MINIMALISTA CONTEMPORÁNEA
# ===========================================================================
CARPETA_PROYECTO = os.path.dirname(os.path.abspath(__file__))
RUTA_BASE_CONOCIMIENTO = os.path.join(CARPETA_PROYECTO, "base_conocimiento.pl")
RUTA_HISTORIAL = os.path.join(CARPETA_PROYECTO, "historial_evaluaciones.json")

# Control de acceso del Modo Experto (DEMOSTRACIÓN, no es seguridad real: el
# hash está en el código y cualquiera con acceso al archivo puede cambiarlo).
# sha256("experto2026"). La variable de entorno ARQUISELECT_PIN lo reemplaza.
PIN_EXPERTO_SHA256 = "4c1f262f6be6d62444f693baf98a639df268b734fd1464056d397d43691465f2"


def _sha256(texto):
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def pin_valido(pin):
    """True si el PIN coincide con ARQUISELECT_PIN (si está definida) o con el
    hash por defecto. compare_digest evita comparar carácter por carácter."""
    esperado = os.environ.get("ARQUISELECT_PIN")
    esperado = _sha256(esperado) if esperado else PIN_EXPERTO_SHA256
    return hmac.compare_digest(_sha256(pin or ""), esperado)

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
    "condicion": "condición", "alfabetico": "alfabético", "esta": "está",
    # textos de los estilos y requisitos agregados y del aprendizaje
    "logica": "lógica", "automatica": "automática", "automaticas": "automáticas",
    "anos": "años", "vivira": "vivirá", "debera": "deberá", "pequenas": "pequeñas",
    "concentricas": "concéntricas", "facil": "fácil", "nucleo": "núcleo",
    "maxima": "máxima", "tecnologica": "tecnológica", "codigo": "código", "faciles": "fáciles",
    "mas": "más", "numero": "número", "tendera": "tenderá",
    "contradiccion": "contradicción", "tension": "tensión", "pequeno": "pequeño",
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
# 2. FORMATO DE DATOS HACIA PROLOG (Python solo empaqueta; Prolog valida)
# ===========================================================================
def atomo(texto):
    """Texto como átomo Prolog entre comillas simples (nunca variable libre).
    Se escapan barra, comilla y saltos de línea para que la consulta sea válida.
    Robustez: los surrogates sueltos (emojis mal partidos) se cambian por "�"
    porque no se pueden codificar en UTF-8, y los demás caracteres de control
    (NUL, ESC, tab...) se envían como espacio: un NUL cortaría la consulta."""
    s = str(texto).encode("utf-16", "surrogatepass").decode("utf-16", "replace")
    s = (s.replace("\\", "\\\\").replace("'", "\\'")
         .replace("\n", "\\n").replace("\r", ""))
    s = re.sub(r"[\x00-\x09\x0b-\x1f\x7f]", " ", s)
    return f"'{s}'"


def lista_prolog(elementos):
    return "[" + ",".join(atomo(e) for e in elementos) + "]"


def lista_pares_prolog(pares):
    """[(requisito, peso), ...] -> "[['req',2],...]" (formato de ensenar_estilo/6)."""
    return "[" + ",".join(f"[{atomo(r)},{int(p)}]" for r, p in pares) + "]"


def a_python(valor):
    if isinstance(valor, (bytes, bytearray)):
        return valor.decode("utf-8", errors="replace")
    if isinstance(valor, (list, tuple)):
        return [a_python(v) for v in valor]
    if isinstance(valor, (int, float, str)):
        return valor
    if type(valor).__name__ == "Variable":
        # Variable que quedó sin ligar (p. ej. la plantilla de un findall).
        # Leer su .value con la consulta ya cerrada usa un term_t inválido y
        # SWI-Prolog aborta el proceso, así que se devuelve None sin tocarla.
        return None
    interno = getattr(valor, "value", None)
    if isinstance(interno, (str, bytes)):
        return a_python(interno)
    return str(valor)


# ===========================================================================
# 3. CONTROLADOR PYSWIP / PUENTE PROLOG (Motor Simbólico)
# ===========================================================================
class PuenteProlog:
    """Encapsula todas las consultas a base_conocimiento.pl."""

    def __init__(self, ruta=RUTA_BASE_CONOCIMIENTO, ruta_aprendizaje=None):
        """ruta_aprendizaje: archivo de aprendizaje alternativo (las pruebas usan
        uno temporal para no tocar conocimiento_aprendido.pl)."""
        from pyswip import Prolog # type: ignore
        self.ruta = ruta.replace("\\", "/")
        self.ruta_aprendizaje = ruta_aprendizaje.replace("\\", "/") if ruta_aprendizaje else None
        self.prolog = Prolog()
        self.ultimas_metas = {}
        self.estado_aprendizaje = ("sin_archivo", 0)
        self.recargar()

    def recargar(self):
        """Consulta (o reconsulta) la base y vuelve a leer lo aprendido.
        Reconsultar el .pl no garantiza borrar lo agregado con assertz, por eso
        Prolog olvida primero lo aprendido y luego lo carga desde
        conocimiento_aprendido.pl. catch/3: la primera vez el predicado aún no existe."""
        self.consultar("catch(olvidar_aprendizaje, _, true)")
        self.prolog.consult(self.ruta)
        if self.ruta_aprendizaje:
            self.consultar(f"usar_archivo_aprendizaje({atomo(self.ruta_aprendizaje)})")
        r = self.una_solucion(
            "aprendizaje",
            "ruta_aprendizaje(Ruta), cargar_aprendizaje(Ruta, Estado), "
            "estado_carga(Estado, Tipo, Detalle)")
        self.estado_aprendizaje = (r["Tipo"], r["Detalle"]) if r else ("sin_archivo", 0)

    def consultar(self, meta):
        soluciones = list(self.prolog.query(meta))
        return [{k: a_python(v) for k, v in s.items()} for s in soluciones]

    def una_solucion(self, nombre, meta):
        self.ultimas_metas[nombre] = meta
        soluciones = self.consultar(f"once(({meta}))")
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

    def consistencia(self, requisitos, negados=()):
        """consistencia_entrada/4 (sección 10): {Estado, Lista}; Estado es
        consistente | advertencia | bloqueado y Lista [[A, B, Tipo, Mensaje], ...]."""
        meta = (f"consistencia_entrada({lista_prolog(requisitos)}, {lista_prolog(negados)}, "
                "Estado, Lista)")
        return self.una_solucion("consistencia", meta) or {"Estado": "consistente", "Lista": []}

    def resumen(self, requisitos):
        meta = (f"resumen_dictamen({lista_prolog(requisitos)}, "
                "Mejor, AFavor, EnContra, SinEfecto)")
        return self.una_solucion("resumen", meta)

    # --- Aprendizaje en caliente (sección 8 de la base) ---
    def ensenar_estilo(self, nombre, descripcion, favorece, incompatibles):
        """Envía lo marcado a ensenar_estilo/6. Prolog valida y responde; aquí
        solo se devuelve {tipo: ok|error, id, mensaje, advertencias}."""
        meta = (f"ensenar_estilo({atomo(nombre)}, {atomo(descripcion)}, "
                f"{lista_pares_prolog(favorece)}, {lista_prolog(incompatibles)}, "
                "Resultado, Advertencias), "
                "tipo_resultado(Resultado, Tipo, Id), mensaje_resultado(Resultado, Mensaje)")
        r = self.una_solucion("ensenar", meta)
        if not r:
            return {"tipo": "error", "id": "", "advertencias": [],
                    "mensaje": "Prolog no respondio a ensenar_estilo/6."}
        return {"tipo": r["Tipo"], "id": r["Id"], "mensaje": r["Mensaje"],
                "advertencias": r["Advertencias"]}

    def olvidar_estilo(self, id_estilo):
        """True si Prolog lo borró (solo borra estilos aprendidos)."""
        return self.una_solucion("olvidar", f"olvidar_estilo({atomo(id_estilo)})") is not None

    def guardar_aprendizaje(self):
        if self.una_solucion("guardar", "guardar_aprendizaje") is None:
            raise RuntimeError("guardar_aprendizaje/0 fallo")

    def estilos_aprendidos(self):
        return [(i, n) for i, n in self._lista("aprendidos", "estilos_aprendidos(Lista)")]

    # --- Explicabilidad (sección 5) ---
    def explicar(self, requisitos):
        """explicar_diagnostico/5: reglas disparadas, hechos validados e
        hipótesis descartadas, tal como las arma Prolog."""
        meta = (f"explicar_diagnostico({lista_prolog(requisitos)}, "
                "Mejor, Reglas, Hechos, Descartadas)")
        return self.una_solucion("explicacion", meta)

    def reglas_disparadas(self, requisitos):
        """[[Id, Estilo, Efecto, Peso, Explicacion], ...] reglas expertas que se
        disparan con esos requisitos."""
        return self._lista("disparadas",
                           f"reglas_expertas_disparadas({lista_prolog(requisitos)}, Lista)")

    # --- Lenguaje natural (lenguaje_natural.pl, entregable 3) ---
    def interpretar(self, texto):
        """interpretar_texto/5. Devuelve {requisitos, negados, no_entendido,
        arbol}; arbol son las líneas con sangría que arma arbol_lineas/2.
        Nunca lanza excepción: si la consulta misma falla se responde vacío."""
        meta = (f"interpretar_texto({atomo(texto)}, Requisitos, Negados, NoEntendido, _Arbol), "
                "arbol_lineas(_Arbol, Lineas)")
        try:
            r = self.una_solucion("interpretar", meta)
        except Exception:
            return {"requisitos": [], "negados": [], "no_entendido": ["(entrada no procesable)"],
                    "arbol": []}
        if not r:
            return {"requisitos": [], "negados": [], "no_entendido": [], "arbol": []}
        return {"requisitos": r["Requisitos"], "negados": r["Negados"],
                "no_entendido": [str(p) for p in r["NoEntendido"]], "arbol": r["Lineas"]}

    def ensenar_sinonimo(self, frase, requisito, polaridad="afirma"):
        meta = (f"ensenar_sinonimo({atomo(frase)}, {atomo(requisito)}, {atomo(polaridad)}, R), "
                "mensaje_sinonimo(R, Mensaje), ( R = ok(_) -> Tipo = ok ; Tipo = error )")
        r = self.una_solucion("sinonimo", meta)
        if not r:
            return {"tipo": "error", "mensaje": "Prolog no respondio a ensenar_sinonimo/4."}
        return {"tipo": r["Tipo"], "mensaje": r["Mensaje"]}

    def olvidar_sinonimo(self, frase):
        return self.una_solucion("olvidar_sinonimo", f"olvidar_sinonimo({atomo(frase)})") is not None

    def sinonimos_aprendidos(self):
        return self._lista("sinonimos", "sinonimos_aprendidos(Lista)")

    def formulaciones(self, requisito):
        return self._lista("formulaciones", f"formulaciones({atomo(requisito)}, Lista)")

    # --- Modo Experto: reglas inyectadas (sección 9) ---
    def ensenar_regla(self, id_regla, explicacion, estilo, efecto, peso, condiciones, exclusiones):
        """Envía SOLO datos a ensenar_regla/8; Prolog valida, construye la
        cláusula, hace assertz y la escribe en el archivo de aprendizaje."""
        try:
            peso_txt = str(int(peso))
        except (TypeError, ValueError):
            peso_txt = atomo(peso)          # Prolog lo rechaza como peso_invalido
        meta = (f"ensenar_regla({atomo(id_regla)}, {atomo(explicacion)}, {atomo(estilo)}, "
                f"{atomo(efecto)}, {peso_txt}, {lista_prolog(condiciones)}, "
                f"{lista_prolog(exclusiones)}, R), tipo_resultado_regla(R, Tipo), "
                "mensaje_regla(R, Mensaje), "
                "( R = ok(Id) -> clausula_regla_texto(Id, Clausula) ; Id = '', Clausula = '' )")
        r = self.una_solucion("ensenar_regla", meta)
        if not r:
            return {"tipo": "error", "id": "", "clausula": "",
                    "mensaje": "Prolog no respondio a ensenar_regla/8."}
        return {"tipo": r["Tipo"], "id": r["Id"], "mensaje": r["Mensaje"],
                "clausula": r["Clausula"]}

    def olvidar_regla(self, id_regla):
        return self.una_solucion("olvidar_regla", f"olvidar_regla({atomo(id_regla)})") is not None

    def reglas_aprendidas(self):
        """[{id, estilo, efecto, peso, condiciones, exclusiones, explicacion}, ...]"""
        return [{"id": i, "estilo": e, "efecto": ef, "peso": p, "condiciones": c,
                 "exclusiones": x, "explicacion": ex}
                for i, e, ef, p, c, x, ex in self._lista("reglas", "reglas_aprendidas(Lista)")]


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

    def guardar_evaluacion(self, requisitos, estilo, prioridad, estado, estilo_id=None):
        consultas = self._leer()

        nuevo_registro = {
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "requisitos": requisitos,
            "estilo": estilo,
            "estilo_id": estilo_id,
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

    # Rol actual (Usuario / Experto); el controlador lo actualiza al cambiar.
    controlador = getattr(padre, "controlador", None)
    if controlador is not None and hasattr(controlador, "registrar_etiqueta_rol"):
        lbl_rol = tk.Label(fila, text="", font=(FUENTE_BASE, 8, "bold"), padx=10, pady=3)
        lbl_rol.pack(side="right", padx=(4, 10))
        controlador.registrar_etiqueta_rol(lbl_rol)

    # Divisor inferior sutil de 1px
    divisor = tk.Frame(padre, bg="#1e293b", height=1)
    divisor.pack(fill="x")
    return marco


def recortar_texto(fuente, texto, limite):
    """Recorta texto con "…" para que mida a lo sumo `limite` píxeles."""
    if fuente.measure(texto) <= limite:
        return texto
    while texto and fuente.measure(texto + "…") > limite:
        texto = texto[:-1]
    return texto.rstrip() + "…"


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

        # Selector de rol: Usuario / Experto (Experto pide PIN)
        fila_rol = tk.Frame(caja_centro, bg=COLOR_FONDO)
        fila_rol.pack(pady=(0, 18))
        tk.Label(fila_rol, text="ROL:", font=(FUENTE_BASE, 9, "bold"), bg=COLOR_FONDO,
                 fg=COLOR_TEXTO_MUTED).pack(side="left", padx=(0, 8))
        self.var_rol = tk.StringVar(value=controlador.rol)
        for valor, texto in (("usuario", "👤 Usuario"), ("experto", "🛡 Experto")):
            ttk.Radiobutton(fila_rol, text=texto, value=valor, variable=self.var_rol,
                            style="Rol.TRadiobutton",
                            command=self._al_cambiar_rol).pack(side="left", padx=4)

        # Cuadrícula de Tarjetas de Acción Minimalistas
        fila_tarjetas = tk.Frame(caja_centro, bg=COLOR_FONDO)
        fila_tarjetas.pack()
        self.fila_tarjetas = fila_tarjetas

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
            },
            {
                "icono": "🧠",
                "tag": "SOLO EXPERTO",
                "tag_bg": COLOR_AMBAR_BG,
                "tag_fg": COLOR_AMBAR_TEXT,
                "titulo": "Modo Experto",
                "desc": "Enseñe reglas lógicas, arquitecturas nuevas y vocabulario. Se agregan con assertz y quedan guardados en disco.",
                "btn_texto": "Abrir Modo Experto →",
                "btn_estilo": "Secundario.TButton",
                "comando": lambda: controlador.abrir_modo_experto(0),
                "experto": True,
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
            card.pack_propagate(False)
            if info.get("experto"):
                self.card_experto = card       # se muestra solo con rol Experto
            else:
                card.pack(side="left", padx=10)

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

    def _al_cambiar_rol(self):
        """El controlador pide el PIN; si falla, el selector vuelve a Usuario."""
        self.controlador.cambiar_rol(self.var_rol.get())
        self.actualizar_rol()

    def actualizar_rol(self):
        self.var_rol.set(self.controlador.rol)
        if self.controlador.rol == "experto":
            self.card_experto.pack(side="left", padx=10)
        else:
            self.card_experto.pack_forget()


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
        # Lo que marcó la última interpretación en lenguaje natural: al
        # interpretar de nuevo se reemplaza (no se acumula).
        self._nl_requisitos = []
        self._nl_negados = []
        self._nl_arbol = []
        self._ultima_explicacion = None
        self._reglas_disparadas = []
        self._porque_abierto = False
        self._consistencia = {"Estado": "consistente", "Lista": []}   # consistencia_entrada/4

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

        # 0. Describe tu proyecto (lenguaje natural -> DCG en Prolog)
        card_nl = tk.Frame(col, bg=COLOR_TARJETA, bd=0, highlightthickness=1,
                           highlightbackground=COLOR_PRIMARIO, padx=12, pady=10)
        card_nl.pack(fill="x", pady=(0, 8))
        tk.Label(card_nl, text="DESCRIBE TU PROYECTO", font=(FUENTE_BASE, 8, "bold"),
                 bg=COLOR_TARJETA, fg=COLOR_PRIMARIO).pack(anchor="w", pady=(0, 4))
        self.txt_nl = tk.Text(card_nl, height=4, wrap="word", font=(FUENTE_BASE, 9),
                              relief="flat", bg=COLOR_SUPERFICIE, fg=COLOR_TEXTO,
                              highlightthickness=1, highlightbackground=COLOR_BORDE,
                              padx=6, pady=4)
        self.txt_nl.pack(fill="x")
        self.txt_nl.insert("1.0", "")
        Tooltip(self.txt_nl, "Ej.: «Somos un equipo de tres personas con poco presupuesto "
                             "y necesitamos entregar rápido». Prolog lo analiza con una DCG.")
        fila_nl = tk.Frame(card_nl, bg=COLOR_TARJETA)
        fila_nl.pack(fill="x", pady=(6, 0))
        ttk.Button(fila_nl, text="🔎 Interpretar", style="Primario.TButton",
                   command=self.interpretar_texto).pack(side="left")
        self.lnk_arbol = tk.Label(fila_nl, text="Ver análisis sintáctico", font=(FUENTE_BASE, 9, "underline"),
                                  bg=COLOR_TARJETA, fg=COLOR_TEXTO_MUTED, cursor="hand2")
        self.lnk_arbol.pack(side="right")
        self.lnk_arbol.bind("<Button-1>", lambda _e: self.ver_analisis_sintactico())
        self.lbl_nl_ok = tk.Label(card_nl, text="", font=(FUENTE_BASE, 9), bg=COLOR_TARJETA,
                                  fg=COLOR_EXITO_TEXT, wraplength=320, justify="left")
        self.lbl_nl_no = tk.Label(card_nl, text="", font=(FUENTE_BASE, 9), bg=COLOR_TARJETA,
                                  fg=COLOR_AMBAR_TEXT, wraplength=320, justify="left")

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

        # 3. Otros requisitos: enseñar una arquitectura nueva (Modo Experto, solo rol Experto)
        card_otros = tk.Frame(col, bg=COLOR_TARJETA, bd=0, highlightthickness=1, highlightbackground=COLOR_BORDE, padx=12, pady=10)
        card_otros.pack(fill="x", pady=(8, 0))

        tk.Label(
            card_otros, text="OTROS REQUISITOS",
            font=(FUENTE_BASE, 8, "bold"), bg=COLOR_TARJETA, fg=COLOR_TEXTO_MUTED
        ).pack(anchor="w", pady=(0, 6))

        btn_nueva = ttk.Button(
            card_otros, text="➕ Crear arquitectura nueva…", style="Secundario.TButton",
            command=lambda: self.controlador.abrir_modo_experto(1)
        )
        btn_nueva.pack(fill="x")
        Tooltip(btn_nueva, "Requiere rol Experto: abre el Modo Experto en la pestaña "
                           "«Arquitectura nueva». Se agrega a la base sin reiniciar.")

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

        # Banner ámbar de tensiones (consistencia_entrada/4): solo advierte,
        # el diagnóstico sigue visible. Se empaqueta solo cuando hay tensiones.
        self.lbl_tension = tk.Label(
            self.card_dictamen, text="", font=(FUENTE_BASE, 9), bg=COLOR_AMBAR_BG,
            fg=COLOR_AMBAR_TEXT, padx=12, pady=6, anchor="w", justify="left", wraplength=820
        )

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

        # 4) ¿Por qué? (auditoría): plegable, sale de explicar_diagnostico/5
        self.sec_porque = tk.Frame(cuerpo, bg=COLOR_TARJETA, bd=0, highlightthickness=1,
                                   highlightbackground=COLOR_BORDE, padx=18, pady=10)
        self.btn_porque = ttk.Button(self.sec_porque, text="▸ ¿Por qué? (auditoría)",
                                     style="Suave.TButton", command=self.alternar_porque)
        self.btn_porque.pack(anchor="w")
        self.zona_porque = tk.Frame(self.sec_porque, bg=COLOR_TARJETA)

    def _linea(self, padre, texto, color, negrita=False, tamano=10, sangria=12):
        tk.Label(padre, text=texto, font=(FUENTE_BASE, tamano, "bold" if negrita else "normal"),
                 bg=COLOR_TARJETA, fg=color,
                 wraplength=760, justify="left").pack(anchor="w", padx=(sangria, 0), pady=1)

    # --- Lenguaje natural ---
    def interpretar_texto(self):
        """Envía el texto a interpretar_texto/5 y aplica lo que Prolog entendió:
        marca casillas, agrega negados y relanza las preguntas guiadas."""
        texto = self.txt_nl.get("1.0", "end").strip()
        if not texto:
            self._mostrar_nl("", "Escribe una descripción del proyecto", COLOR_TEXTO_MUTED)
            return
        try:
            r = self.puente.interpretar(texto)
        except Exception as error:
            messagebox.showerror("Error en Prolog", f"No se pudo interpretar el texto:\n{error}")
            return

        # Reemplazar lo que marcó la interpretación anterior (sin duplicar).
        for req in self._nl_requisitos:
            if req in self.vars:
                self.vars[req].set(0)
        self.negados = [n for n in self.negados if n not in self._nl_negados]
        self.respuestas = [(q, a) for q, a in self.respuestas
                           if q not in self._nl_requisitos and q not in self._nl_negados]

        for req in r["requisitos"]:
            if req in self.vars:
                self.vars[req].set(1)
        for req in r["negados"]:
            if req not in self.negados:
                self.negados.append(req)
            self.respuestas.append((req, False))
        self._nl_requisitos = list(r["requisitos"])
        self._nl_negados = list(r["negados"])
        self._nl_arbol = r["arbol"]

        partes = [self.etiquetas.get(q, q) for q in r["requisitos"]]
        partes += [f"NO: {self.etiquetas.get(q, q)}" for q in r["negados"]]
        ok = ("✔ Entendí: " + "; ".join(partes)) if partes else "✔ Entendí: (ningún requisito)"
        no = ("⚠ No entendí: " + ", ".join(r["no_entendido"])) if r["no_entendido"] else ""
        self._mostrar_nl(ok, no, COLOR_EXITO_TEXT if partes else COLOR_TEXTO_MUTED)
        self.pestanas.select(0)
        self.recalcular()

    def _mostrar_nl(self, ok, no, color_ok):
        self.lbl_nl_ok.pack_forget()
        self.lbl_nl_no.pack_forget()
        if ok:
            self.lbl_nl_ok.configure(text=ok, fg=color_ok)
            self.lbl_nl_ok.pack(anchor="w", pady=(6, 0))
        if no:
            self.lbl_nl_no.configure(text=no)
            self.lbl_nl_no.pack(anchor="w", pady=(2, 0))

    def ver_analisis_sintactico(self):
        """Muestra el árbol de la DCG (líneas con sangría armadas en Prolog)."""
        ventana = tk.Toplevel(self)
        ventana.title("Análisis sintáctico (DCG)")
        ventana.geometry("620x480")
        ventana.configure(bg=COLOR_FONDO)
        tk.Label(ventana, text="Árbol devuelto por interpretar_texto/5 → arbol_lineas/2",
                 font=(FUENTE_BASE, 10, "bold"), bg=COLOR_FONDO, fg=COLOR_TEXTO).pack(anchor="w", padx=12, pady=(10, 4))
        txt = tk.Text(ventana, font=("Consolas", 10), bg=COLOR_TARJETA, fg=COLOR_TEXTO,
                      relief="flat", padx=10, pady=8)
        txt.pack(fill="both", expand=True, padx=12, pady=(0, 6))
        lineas = self._nl_arbol or ["(Todavía no hay análisis: escriba una descripción y pulse 🔎 Interpretar)"]
        txt.insert("1.0", "\n".join(lineas))
        txt.configure(state="disabled")
        ttk.Button(ventana, text="Cerrar", style="Suave.TButton",
                   command=ventana.destroy).pack(anchor="e", padx=12, pady=(0, 10))

    # --- ¿Por qué? (auditoría) ---
    def alternar_porque(self):
        self._porque_abierto = not self._porque_abierto
        self._dibujar_porque()

    def _dibujar_porque(self):
        flecha = "▾" if self._porque_abierto else "▸"
        self.btn_porque.configure(text=f"{flecha} ¿Por qué? (auditoría)")
        for h in self.zona_porque.winfo_children():
            h.destroy()
        if not self._porque_abierto or not self._ultima_explicacion:
            self.zona_porque.pack_forget()
            return
        ex = self._ultima_explicacion
        self.zona_porque.pack(fill="x", pady=(8, 0))
        z = self.zona_porque

        self._linea(z, "REGLAS DISPARADAS (encadenamiento nivel 1 → 2 → 3)", COLOR_PRIMARIO, True, 9, 0)
        nombres_nivel = {1: "Nivel 1 · validación", 2: "Nivel 2 · inferencia intermedia", 3: "Nivel 3 · conclusión"}
        nivel_actual = None
        for nivel, regla, detalle in ex["Reglas"]:
            if nivel != nivel_actual:
                nivel_actual = nivel
                self._linea(z, nombres_nivel.get(nivel, f"Nivel {nivel}"), COLOR_TEXTO, True, 9, 4)
            experta = str(regla).startswith("regla_experta")
            color = COLOR_AMBAR_TEXT if experta else COLOR_TEXTO_MUTED
            self._linea(z, f"{'★' if experta else '•'} {regla}: {detalle}", color, experta, 9, 16)

        self._linea(z, "HECHOS VALIDADOS", COLOR_PRIMARIO, True, 9, 0)
        if not ex["Hechos"]:
            self._linea(z, "• (ninguno)", COLOR_TEXTO_MUTED, False, 9, 16)
        for req, grupo, atributo in ex["Hechos"]:
            self._linea(z, f"• {self.etiquetas.get(req, req)}  →  grupo {grupo}, exige {bonito(atributo)}",
                        COLOR_EXITO_TEXT, False, 9, 16)

        self._linea(z, "HIPÓTESIS DESCARTADAS", COLOR_PRIMARIO, True, 9, 0)
        if not ex["Descartadas"]:
            self._linea(z, "• (ninguna)", COLOR_TEXTO_MUTED, False, 9, 16)
        for estilo, tipo, detalle, comparte in ex["Descartadas"]:
            extra = f" · compartía: {', '.join(bonito(a) for a in comparte)}" if comparte else ""
            self._linea(z, f"✖ {self.nombre_estilo(estilo)} ({bonito(tipo)}): {detalle}{extra}",
                        COLOR_PELIGRO_TEXT, False, 9, 16)

    # --- Acciones y sincronización ---
    def al_mostrar(self):
        # Al volver de otra vista se conservan casillas, negados y respuestas;
        # solo se releen los estilos (pudieron cambiar) y se recalcula.
        self.refrescar_conocimiento()

    def refrescar_conocimiento(self):
        """Relee de Prolog lo que cambia con el aprendizaje en caliente (estilos y
        descripciones) y recalcula dictamen, ranking, comparativa y preguntas."""
        self.estilos = self.puente.estilos()
        self.recalcular()

    def seleccion(self):
        return [r for r, v in self.vars.items() if v.get() == 1]

    def limpiar(self):
        self.cargar_ejemplo(())

    def cargar_ejemplo(self, reqs):
        for r, v in self.vars.items():
            v.set(1 if r in reqs else 0)
        self.negados = []
        self.respuestas = []
        self._nl_requisitos = []
        self._nl_negados = []
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
        # Un requisito marcado y también "No aplica" ya NO se corrige aquí:
        # se envía tal cual y Prolog lo detecta como contradicción (sección 10).
        self._sincronizar_respuestas(reqs)

        try:
            self._consistencia = self.puente.consistencia(reqs, self.negados)
            d = self.puente.diagnosticar(reqs)
            qf = self.puente.que_falta(reqs, self.negados)
            rs = self.puente.resumen(reqs)
            cands = self.puente.candidatos(reqs)
            descs = self.puente.descartes(reqs)
            self._ultima_explicacion = self.puente.explicar(reqs)
            self._reglas_disparadas = self.puente.reglas_disparadas(reqs)
        except Exception as error:
            messagebox.showerror("Error en Prolog", f"Ocurrió un error al consultar SWI-Prolog:\n{error}")
            return

        if not d or not qf or not rs:
            return

        self._mostrar_dictamen(d, qf)
        self._mostrar_preguntas(d, qf)
        self._mostrar_resumen(d, qf, rs, cands, descs)
        self._dibujar_porque()

    def guardar_en_historial(self):
        reqs = self.seleccion()
        if not reqs:
            messagebox.showwarning("Atención", "Seleccione al menos un requisito antes de guardar en el historial.")
            return

        d = self.puente.diagnosticar(reqs)
        qf = self.puente.que_falta(reqs, self.negados)
        if not d:
            return
        if qf and qf["Estado"] == "contradictorio":
            messagebox.showwarning("Atención", "No se puede guardar: Prolog detectó una contradicción "
                                               "dura en los requisitos.")
            return

        estilo_nom = self.estilos.get(d["Mejor"], (d["Mejor"], ""))[0]
        reqs_legibles = [self.etiquetas.get(r, r) for r in reqs]

        self.controlador.historial.guardar_evaluacion(
            reqs_legibles,
            estilo_nom,
            bonito(d["Prioridad"]),
            bonito(qf["Estado"]),
            estilo_id=d["Mejor"],
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

    def _texto_contradicciones(self, tipo):
        """Mensajes de consistencia_entrada/4 del tipo dado (dura | tension), legibles."""
        return [con_tildes(bonito(m)) for _a, _b, t, m in self._consistencia["Lista"] if t == tipo]

    def _mostrar_dictamen(self, d, qf):
        estado = qf["Estado"]
        tensiones = self._texto_contradicciones("tension")
        if estado == "contradictorio":
            # Contradicción dura: Prolog no dio recomendación (sección 10).
            self.lbl_estilo.configure(text="⛔ Sin recomendación")
            self.lbl_desc_estilo.configure(text="Los requisitos se contradicen. Corrija las casillas, "
                                                "las respuestas «No aplica» o el texto para continuar.")
            for c in self.chips:
                self._chip(c, None)
            lineas = (["⛔ " + m for m in self._texto_contradicciones("dura")]
                      + ["⚠ " + m for m in tensiones])
            self.lbl_estado.configure(text="\n".join(lineas), bg=COLOR_PELIGRO_BG, fg=COLOR_PELIGRO_TEXT)
            self.lbl_tension.pack_forget()
            return
        if tensiones:
            self.lbl_tension.configure(text="\n".join("⚠ " + m for m in tensiones))
            self.lbl_tension.pack(fill="x", pady=(6, 0))
        else:
            self.lbl_tension.pack_forget()
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

    def _mostrar_preguntas(self, d, qf):
        """Flujo tipo asistente: una pregunta a la vez, tomada de que_falta/6."""
        bloqueado = qf["Estado"] == "contradictorio"
        lider = "ninguno (entrada contradictoria)" if bloqueado else self.nombre_estilo(d["Mejor"])
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

        if bloqueado:
            tk.Label(card, text="⛔ Evaluación bloqueada", font=(FUENTE_BASE, 14, "bold"),
                     bg=COLOR_TARJETA, fg=COLOR_PELIGRO_TEXT).pack(anchor="w")
            tk.Label(card, text="Prolog encontró una contradicción dura (ver el aviso rojo de arriba). "
                                "Corrija los requisitos o use «↶ Deshacer última».",
                     font=(FUENTE_BASE, 10), bg=COLOR_TARJETA, fg=COLOR_TEXTO_MUTED,
                     wraplength=760, justify="left").pack(anchor="w", pady=(4, 0))
        elif terminado:
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

        for sec in (self.sec_vacio, self.sec_respuesta, self.sec_comp, self.sec_descartes,
                    self.sec_porque):
            sec.pack_forget()

        if qf["Estado"] in ("vacio", "contradictorio"):
            self.sec_vacio.configure(text="Responde las preguntas para ver las opciones"
                                     if qf["Estado"] == "vacio" else
                                     "⛔ Sin ranking: la entrada tiene una contradicción dura.")
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
            self._linea(self.zona_razones, f"✔ Favorece {con_tildes(bonito(atributo))} (+{peso}) debido a: {causas}", COLOR_EXITO_TEXT)
        for req, peso in rs["EnContra"]:
            self._linea(self.zona_razones, f"✖ Penalizado con -{peso} puntos por: {self.etiquetas.get(req, req)}", COLOR_PELIGRO_TEXT)
        for id_regla, estilo, efecto, peso, expl in self._reglas_disparadas:
            if estilo == rs["Mejor"] and efecto == "recomendar":
                self._linea(self.zona_razones, f"★ Regla experta {id_regla} (+{peso}): {expl}",
                            COLOR_AMBAR_TEXT, True)
        self.sec_respuesta.pack(fill="x", pady=(0, 12), padx=(0, 4))

        # 2) Comparativa
        self.sec_comp.pack(fill="x", pady=(0, 12), padx=(0, 4))
        self._dibujar_comparacion()

        # 3) Descartados (solo si hay)
        for h in self.zona_descartes.winfo_children():
            h.destroy()
        explicaciones = {r[0]: r[4] for r in self._reglas_disparadas}
        for estilo, tipo, motivo in descs:
            if tipo == "exclusion":
                txt = f"✖ {self.nombre_estilo(estilo)}: incompatible con «{self.etiquetas.get(motivo, motivo)}»"
            elif tipo == "regla_experta":
                txt = (f"✖ {self.nombre_estilo(estilo)}: descartado por la regla experta «{motivo}»: "
                       f"{explicaciones.get(motivo, '')}")
            else:
                txt = f"✖ {self.nombre_estilo(estilo)}: sin evidencia a favor (puntaje {motivo})"
            self._linea(self.zona_descartes, txt, COLOR_PELIGRO_TEXT)
        if descs:
            self.sec_descartes.pack(fill="x", padx=(0, 4), pady=(0, 12))

        # 4) ¿Por qué? (auditoría)
        self.sec_porque.pack(fill="x", padx=(0, 4))

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
        # La columna de nombres se ajusta al nombre más largo (hay estilos como
        # "Arquitectura Hexagonal (puertos y adaptadores)" y los aprendidos),
        # con tope del 45 % del ancho; lo que no cabe se recorta con "…".
        if not hasattr(self, "_fuente_comp"):
            self._fuente_comp = tkfont.Font(family=FUENTE_BASE, size=9, weight="bold")
        fuente = self._fuente_comp
        textos = [self.nombre_estilo(e) for e, _, _ in filas]
        ancho_nombres = max(fuente.measure("★ " + t) for t in textos)
        x0 = min(max(ancho_nombres + 28, 160), int(ancho * 0.45))
        limite_txt = x0 - 24
        xmax = max(ancho - 80, x0 + 60)
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

            nombre = recortar_texto(fuente, ico + textos[i], limite_txt)
            c.create_text(14, y + 10, anchor="w", text=nombre, fill=col_txt, font=fnt)

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
# 6.3 PANEL: CREAR ARQUITECTURA NUEVA (pestaña 2 del Modo Experto)
# ---------------------------------------------------------------------------
def _tarjeta(padre, **kw):
    return tk.Frame(padre, bg=COLOR_TARJETA, bd=0, highlightthickness=1,
                    highlightbackground=COLOR_BORDE, **kw)


def _titulo(padre, texto, color=COLOR_TEXTO_MUTED):
    return tk.Label(padre, text=texto, font=(FUENTE_BASE, 8, "bold"),
                    bg=COLOR_TARJETA, fg=color)


def _pintar_mensaje(etiqueta, texto, tipo):
    colores = {
        "exito": (COLOR_EXITO_BG, COLOR_EXITO_TEXT),
        "advertencia": (COLOR_AMBAR_BG, COLOR_AMBAR_TEXT),
        "error": (COLOR_PELIGRO_BG, COLOR_PELIGRO_TEXT),
    }
    bg_c, fg_c = colores.get(tipo, (COLOR_FONDO, COLOR_TEXTO))
    etiqueta.configure(text=texto, bg=bg_c, fg=fg_c)


def _etiqueta_mensaje(padre):
    lbl = tk.Label(padre, text="", font=(FUENTE_BASE, 9), anchor="w",
                   justify="left", padx=12, pady=6, bg=COLOR_FONDO)
    lbl.bind("<Configure>", lambda e: lbl.configure(wraplength=max(e.width - 24, 200)))
    return lbl


class PanelArquitecturaNueva(ttk.Frame):
    """Formulario para enseñar un estilo nuevo (antes VistaNuevaArquitectura).
    Python solo reúne lo marcado y lo envía a ensenar_estilo/6; Prolog valida,
    lo traduce a hechos aporta/3 e incompatible/2 y responde con el mensaje
    que aquí se muestra."""

    def __init__(self, padre, controlador):
        super().__init__(padre, style="Fondo.TFrame", padding=(6, 8, 6, 6))
        self.controlador = controlador
        self.puente = controlador.puente
        self.requisitos = self.puente.requisitos_disponibles()
        self.filas = {}   # requisito -> (var_favorece, var_peso, var_incompatible, combo_peso)

        self._construir_datos(self)
        self._construir_acciones(self)
        self._construir_requisitos(self)

    def _construir_datos(self, padre):
        card = _tarjeta(padre, padx=14, pady=10)
        card.pack(fill="x", side="top", pady=(0, 8))
        card.grid_columnconfigure(0, weight=1)
        card.grid_columnconfigure(1, weight=2)

        _titulo(card, "NOMBRE DE LA ARQUITECTURA").grid(row=0, column=0, sticky="w")
        _titulo(card, "DESCRIPCIÓN CORTA (OPCIONAL)").grid(row=0, column=1, sticky="w", padx=(12, 0))
        self.var_nombre = tk.StringVar()
        self.var_desc = tk.StringVar()
        ttk.Entry(card, textvariable=self.var_nombre, font=(FUENTE_BASE, 10)).grid(
            row=1, column=0, sticky="ew", pady=(4, 0))
        ttk.Entry(card, textvariable=self.var_desc, font=(FUENTE_BASE, 10)).grid(
            row=1, column=1, sticky="ew", padx=(12, 0), pady=(4, 0))

    def _construir_requisitos(self, padre):
        panel = PanelDesplazable(padre)
        panel.pack(fill="both", expand=True, side="top")

        grupos = {}
        for r in self.requisitos:
            grupos.setdefault(r["grupo"], []).append(r)

        for grupo, items in grupos.items():
            marco = _tarjeta(panel.interior, padx=12, pady=8)
            marco.pack(fill="x", pady=4, padx=(0, 4))
            # Columnas de ancho fijo junto a la etiqueta; la columna 4 vacía
            # absorbe el espacio sobrante.
            marco.grid_columnconfigure(0, minsize=400)
            for col, ancho in ((1, 90), (2, 80), (3, 110)):
                marco.grid_columnconfigure(col, minsize=ancho)
            marco.grid_columnconfigure(4, weight=1)

            _titulo(marco, NOMBRE_GRUPO.get(grupo, bonito(grupo)).upper()).grid(
                row=0, column=0, sticky="w", pady=(0, 4))
            for col, txt in ((1, "FAVORECE"), (2, "PESO"), (3, "INCOMPATIBLE")):
                _titulo(marco, txt).grid(row=0, column=col, pady=(0, 4))

            for fila, r in enumerate(items, start=1):
                req = r["id"]
                lbl = tk.Label(marco, text=con_tildes(r["etiqueta"]), font=(FUENTE_BASE, 9),
                               bg=COLOR_TARJETA, fg=COLOR_TEXTO, anchor="w")
                lbl.grid(row=fila, column=0, sticky="w", pady=2)
                if r["pregunta"]:
                    Tooltip(lbl, "¿" + con_tildes(r["pregunta"]))

                var_fav, var_inc = tk.IntVar(value=0), tk.IntVar(value=0)
                var_peso = tk.StringVar(value="2")
                ttk.Checkbutton(marco, variable=var_fav, style="Sintoma.TCheckbutton",
                                command=lambda q=req: self._al_marcar(q, "favorece")).grid(row=fila, column=1)
                combo = ttk.Combobox(marco, textvariable=var_peso, values=("1", "2", "3"),
                                     width=3, state="disabled", font=(FUENTE_BASE, 9))
                combo.grid(row=fila, column=2)
                ttk.Checkbutton(marco, variable=var_inc, style="Sintoma.TCheckbutton",
                                command=lambda q=req: self._al_marcar(q, "incompatible")).grid(row=fila, column=3)
                self.filas[req] = (var_fav, var_peso, var_inc, combo)

    def _construir_acciones(self, padre):
        zona = ttk.Frame(padre, style="Fondo.TFrame")
        zona.pack(fill="x", side="bottom", pady=(8, 0))

        fila = ttk.Frame(zona, style="Fondo.TFrame")
        fila.pack(fill="x")
        ttk.Button(fila, text="☑ Seleccionar todo (Favorece)", style="Suave.TButton",
                   command=self.seleccionar_todo).pack(side="left", padx=(0, 6))
        ttk.Button(fila, text="✕ Limpiar selección", style="Suave.TButton",
                   command=self.limpiar_seleccion).pack(side="left")
        ttk.Button(fila, text="💾 Guardar arquitectura", style="Primario.TButton",
                   command=self.guardar).pack(side="right")

        self.lbl_mensaje = _etiqueta_mensaje(zona)
        self.lbl_mensaje.pack(fill="x", pady=(8, 0))

    def _al_marcar(self, req, columna):
        """Favorece e Incompatible son excluyentes en la misma fila; el peso solo
        se puede elegir si la fila está en Favorece (Prolog lo vuelve a validar)."""
        var_fav, _peso, var_inc, combo = self.filas[req]
        if columna == "favorece" and var_fav.get():
            var_inc.set(0)
        elif columna == "incompatible" and var_inc.get():
            var_fav.set(0)
        combo.configure(state="readonly" if var_fav.get() else "disabled")

    def seleccionar_todo(self):
        for var_fav, _peso, var_inc, combo in self.filas.values():
            var_fav.set(1)
            var_inc.set(0)
            combo.configure(state="readonly")

    def limpiar_seleccion(self):
        for var_fav, var_peso, var_inc, combo in self.filas.values():
            var_fav.set(0)
            var_inc.set(0)
            var_peso.set("2")
            combo.configure(state="disabled")

    def guardar(self):
        favorece = [(req, var_peso.get()) for req, (var_fav, var_peso, _i, _c) in self.filas.items()
                    if var_fav.get()]
        incompatibles = [req for req, (_f, _p, var_inc, _c) in self.filas.items() if var_inc.get()]
        try:
            res = self.puente.ensenar_estilo(self.var_nombre.get(), self.var_desc.get(),
                                             favorece, incompatibles)
        except Exception as error:
            _pintar_mensaje(self.lbl_mensaje, f"Error al consultar SWI-Prolog: {error}", "error")
            return

        if res["tipo"] != "ok":
            _pintar_mensaje(self.lbl_mensaje, "✖ " + con_tildes(res["mensaje"]), "error")
            return

        texto = "✔ " + con_tildes(res["mensaje"])
        try:
            self.puente.guardar_aprendizaje()
        except Exception as error:
            texto += f"\n⚠ Quedó en memoria, pero no se pudo escribir en disco: {error}"
        for adv in res["advertencias"]:
            texto += "\n⚠ " + con_tildes(adv)
        _pintar_mensaje(self.lbl_mensaje, texto, "advertencia" if res["advertencias"] else "exito")

        self.var_nombre.set("")
        self.var_desc.set("")
        self.limpiar_seleccion()
        self.controlador.conocimiento_actualizado()


# ---------------------------------------------------------------------------
# 6.3b VISTA: MODO EXPERTO (adquisición de conocimiento en caliente)
# ---------------------------------------------------------------------------
class VistaModoExperto(ttk.Frame):
    """Solo accesible con rol Experto. Cuatro pestañas: regla nueva,
    arquitectura nueva, vocabulario del DCG y conocimiento aprendido.
    Toda validación y construcción de cláusulas ocurre en Prolog: aquí solo se
    reúnen los datos del formulario y se muestra la respuesta."""

    def __init__(self, padre, controlador):
        super().__init__(padre, style="Fondo.TFrame")
        self.controlador = controlador
        self.puente = controlador.puente
        self.requisitos = self.puente.requisitos_disponibles()
        self.ids_req = [r["id"] for r in self.requisitos]
        self.etiquetas = {r["id"]: con_tildes(r["etiqueta"]) for r in self.requisitos}
        self.estilos = {}

        construir_encabezado(
            self,
            "🧠 Modo Experto",
            "Adquisición de conocimiento en caliente: reglas lógicas, arquitecturas y vocabulario (assertz + archivo .pl)",
            accion_derecha=lambda: controlador.mostrar_vista("VistaInicio"),
            texto_accion="⬅ Volver al Inicio"
        )

        cuerpo = ttk.Frame(self, style="Fondo.TFrame", padding=(18, 12, 18, 12))
        cuerpo.pack(fill="both", expand=True)
        self.pestanas = ttk.Notebook(cuerpo)
        self.pestanas.pack(fill="both", expand=True)

        self._pestana_regla()
        tab_arq = ttk.Frame(self.pestanas, padding=6)
        self.pestanas.add(tab_arq, text="  🏛 Arquitectura nueva  ")
        self.panel_arquitectura = PanelArquitecturaNueva(tab_arq, controlador)
        self.panel_arquitectura.pack(fill="both", expand=True)
        self._pestana_vocabulario()
        self._pestana_aprendido()

    # --- Pestaña 1: Regla nueva ---
    def _lista_multiple(self, padre, titulo, color):
        marco = _tarjeta(padre, padx=10, pady=8)
        _titulo(marco, titulo, color).pack(anchor="w", pady=(0, 4))
        caja = tk.Frame(marco, bg=COLOR_TARJETA)
        caja.pack(fill="both", expand=True)
        lb = tk.Listbox(caja, selectmode="multiple", exportselection=False, height=14,
                        font=(FUENTE_BASE, 9), relief="flat", bg=COLOR_SUPERFICIE,
                        selectbackground=color, activestyle="none")
        sb = ttk.Scrollbar(caja, orient="vertical", command=lb.yview)
        lb.configure(yscrollcommand=sb.set)
        lb.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        for rid in self.ids_req:
            lb.insert("end", self.etiquetas[rid])
        return marco, lb

    def _pestana_regla(self):
        tab = ttk.Frame(self.pestanas, padding=10)
        self.pestanas.add(tab, text="  📐 Regla nueva  ")

        datos = _tarjeta(tab, padx=14, pady=10)
        datos.pack(fill="x", pady=(0, 8))
        datos.grid_columnconfigure(1, weight=1)

        _titulo(datos, "ID DE LA REGLA").grid(row=0, column=0, sticky="w")
        _titulo(datos, "EXPLICACIÓN EN LENGUAJE CLARO (OBLIGATORIA)").grid(row=0, column=1, sticky="w", padx=(12, 0))
        self.var_id_regla = tk.StringVar()
        self.var_expl_regla = tk.StringVar()
        ttk.Entry(datos, textvariable=self.var_id_regla, width=34, font=(FUENTE_BASE, 10)).grid(
            row=1, column=0, sticky="w", pady=(4, 8))
        ttk.Entry(datos, textvariable=self.var_expl_regla, font=(FUENTE_BASE, 10)).grid(
            row=1, column=1, sticky="ew", padx=(12, 0), pady=(4, 8))

        fila = tk.Frame(datos, bg=COLOR_TARJETA)
        fila.grid(row=2, column=0, columnspan=2, sticky="w")
        tk.Label(fila, text="EFECTO", font=(FUENTE_BASE, 8, "bold"), bg=COLOR_TARJETA,
                 fg=COLOR_TEXTO_MUTED).pack(side="left", padx=(0, 6))
        self.var_efecto = tk.StringVar(value="recomendar")
        for valor, texto in (("recomendar", "Recomendar (bonus)"), ("descartar", "Descartar")):
            ttk.Radiobutton(fila, text=texto, value=valor, variable=self.var_efecto,
                            style="Tarjeta.TRadiobutton",
                            command=self._al_cambiar_efecto).pack(side="left", padx=(0, 8))
        tk.Label(fila, text="PESO", font=(FUENTE_BASE, 8, "bold"), bg=COLOR_TARJETA,
                 fg=COLOR_TEXTO_MUTED).pack(side="left", padx=(14, 6))
        self.var_peso_regla = tk.StringVar(value="3")
        self.spin_peso = ttk.Spinbox(fila, from_=1, to=5, width=4, textvariable=self.var_peso_regla,
                                     font=(FUENTE_BASE, 10))
        self.spin_peso.pack(side="left")
        tk.Label(fila, text="ESTILO AFECTADO", font=(FUENTE_BASE, 8, "bold"), bg=COLOR_TARJETA,
                 fg=COLOR_TEXTO_MUTED).pack(side="left", padx=(18, 6))
        self.var_estilo_regla = tk.StringVar()
        self.combo_estilo = ttk.Combobox(fila, textvariable=self.var_estilo_regla, state="readonly",
                                         width=44, font=(FUENTE_BASE, 9))
        self.combo_estilo.pack(side="left")

        listas = tk.Frame(tab, bg=COLOR_FONDO)
        listas.pack(fill="both", expand=True)
        m1, self.lb_condiciones = self._lista_multiple(
            listas, "CONDICIONES: requisitos que DEBEN cumplirse (multi selección)", COLOR_PRIMARIO)
        m2, self.lb_exclusiones = self._lista_multiple(
            listas, "EXCLUSIONES: requisitos que NO deben estar (se traducen a \\+)", COLOR_PELIGRO)
        m1.pack(side="left", fill="both", expand=True, padx=(0, 6))
        m2.pack(side="left", fill="both", expand=True, padx=(6, 0))

        acciones = tk.Frame(tab, bg=COLOR_FONDO)
        acciones.pack(fill="x", pady=(8, 0))
        ttk.Button(acciones, text="✕ Limpiar", style="Suave.TButton",
                   command=self.limpiar_regla).pack(side="left")
        ttk.Button(acciones, text="💾 Guardar regla", style="Primario.TButton",
                   command=self.guardar_regla).pack(side="right")

        self.lbl_msg_regla = _etiqueta_mensaje(tab)
        self.lbl_msg_regla.pack(fill="x", pady=(8, 0))
        self.txt_clausula = tk.Text(tab, height=4, font=("Consolas", 10), bg=COLOR_HEADER,
                                    fg="#e2e8f0", relief="flat", padx=10, pady=6)
        self.txt_clausula.insert("1.0", "% Aquí aparecerá la cláusula que Prolog construye y escribe en el archivo.")
        self.txt_clausula.configure(state="disabled")
        self.txt_clausula.pack(fill="x", pady=(6, 0))

    def _al_cambiar_efecto(self):
        self.spin_peso.configure(state="normal" if self.var_efecto.get() == "recomendar" else "disabled")

    def _seleccionados(self, lb):
        return [self.ids_req[i] for i in lb.curselection()]

    def limpiar_regla(self):
        self.var_id_regla.set("")
        self.var_expl_regla.set("")
        self.var_peso_regla.set("3")
        self.var_efecto.set("recomendar")
        self._al_cambiar_efecto()
        self.lb_condiciones.selection_clear(0, "end")
        self.lb_exclusiones.selection_clear(0, "end")

    def guardar_regla(self):
        nombre = self.var_estilo_regla.get()
        estilo = next((i for i, (n, _d) in self.estilos.items() if n == nombre), nombre)
        try:
            res = self.puente.ensenar_regla(
                self.var_id_regla.get(), self.var_expl_regla.get(), estilo,
                self.var_efecto.get(), self.var_peso_regla.get(),
                self._seleccionados(self.lb_condiciones), self._seleccionados(self.lb_exclusiones))
        except Exception as error:
            _pintar_mensaje(self.lbl_msg_regla, f"Error al consultar SWI-Prolog: {error}", "error")
            return
        if res["tipo"] != "ok":
            _pintar_mensaje(self.lbl_msg_regla, "✖ " + con_tildes(res["mensaje"]), "error")
            return
        _pintar_mensaje(self.lbl_msg_regla, "✔ " + con_tildes(res["mensaje"]), "exito")
        self.txt_clausula.configure(state="normal")
        self.txt_clausula.delete("1.0", "end")
        self.txt_clausula.insert("1.0", res["clausula"])
        self.txt_clausula.configure(state="disabled")
        self.limpiar_regla()
        self.controlador.conocimiento_actualizado()

    # --- Pestaña 3: Vocabulario ---
    def _pestana_vocabulario(self):
        tab = ttk.Frame(self.pestanas, padding=10)
        self.pestanas.add(tab, text="  🔤 Vocabulario  ")

        card = _tarjeta(tab, padx=14, pady=10)
        card.pack(fill="x", pady=(0, 8))
        card.grid_columnconfigure(0, weight=1)
        _titulo(card, "FRASE EN LENGUAJE NATURAL").grid(row=0, column=0, sticky="w")
        _titulo(card, "REQUISITO AL QUE EQUIVALE").grid(row=0, column=1, sticky="w", padx=(12, 0))
        _titulo(card, "POLARIDAD").grid(row=0, column=2, sticky="w", padx=(12, 0))
        self.var_frase = tk.StringVar()
        ttk.Entry(card, textvariable=self.var_frase, font=(FUENTE_BASE, 10)).grid(
            row=1, column=0, sticky="ew", pady=(4, 0))
        self.var_req_sin = tk.StringVar()
        self.combo_req = ttk.Combobox(card, textvariable=self.var_req_sin, state="readonly", width=48,
                                      values=[self.etiquetas[r] for r in self.ids_req], font=(FUENTE_BASE, 9))
        self.combo_req.grid(row=1, column=1, padx=(12, 0), pady=(4, 0))
        self.combo_req.bind("<<ComboboxSelected>>", lambda _e: self._mostrar_formulaciones())
        fila_pol = tk.Frame(card, bg=COLOR_TARJETA)
        fila_pol.grid(row=1, column=2, padx=(12, 0), pady=(4, 0))
        self.var_pol = tk.StringVar(value="afirma")
        for valor, texto in (("afirma", "Afirma"), ("niega", "Niega")):
            ttk.Radiobutton(fila_pol, text=texto, value=valor, variable=self.var_pol,
                            style="Tarjeta.TRadiobutton").pack(side="left", padx=(0, 6))
        ttk.Button(card, text="💾 Guardar sinónimo", style="Primario.TButton",
                   command=self.guardar_sinonimo).grid(row=1, column=3, padx=(12, 0), pady=(4, 0))
        tk.Label(card, text="«Niega» sirve para frases como «carga estable» (niega Carga variable).",
                 font=(FUENTE_BASE, 8), bg=COLOR_TARJETA, fg=COLOR_TEXTO_MUTED).grid(
            row=2, column=0, columnspan=4, sticky="w", pady=(6, 0))

        self.lbl_msg_sin = _etiqueta_mensaje(tab)
        self.lbl_msg_sin.pack(fill="x")

        prueba = _tarjeta(tab, padx=14, pady=10)
        prueba.pack(fill="x", pady=(8, 8))
        _titulo(prueba, "PROBAR LA INTERPRETACIÓN (sin reiniciar)").pack(anchor="w")
        fila_p = tk.Frame(prueba, bg=COLOR_TARJETA)
        fila_p.pack(fill="x", pady=(4, 0))
        self.var_prueba = tk.StringVar()
        ttk.Entry(fila_p, textvariable=self.var_prueba, font=(FUENTE_BASE, 10)).pack(
            side="left", fill="x", expand=True)
        ttk.Button(fila_p, text="🔎 Probar", style="Suave.TButton",
                   command=self.probar_frase).pack(side="left", padx=(8, 0))
        self.lbl_prueba = tk.Label(prueba, text="", font=(FUENTE_BASE, 9), bg=COLOR_TARJETA,
                                   fg=COLOR_TEXTO, justify="left", anchor="w")
        self.lbl_prueba.pack(fill="x", pady=(6, 0))

        form = _tarjeta(tab, padx=14, pady=10)
        form.pack(fill="both", expand=True)
        _titulo(form, "FORMULACIONES QUE YA ENTIENDE ESTE REQUISITO").pack(anchor="w")
        self.lbl_formulaciones = tk.Label(form, text="Elija un requisito arriba.", font=(FUENTE_BASE, 9),
                                          bg=COLOR_TARJETA, fg=COLOR_TEXTO_MUTED, justify="left",
                                          anchor="nw", wraplength=1000)
        self.lbl_formulaciones.pack(fill="both", expand=True, pady=(4, 0))

    def _req_elegido(self):
        etiqueta = self.var_req_sin.get()
        return next((r for r in self.ids_req if self.etiquetas[r] == etiqueta), etiqueta)

    def _mostrar_formulaciones(self):
        req = self._req_elegido()
        try:
            frases = self.puente.formulaciones(req)
        except Exception:
            frases = []
        self.lbl_formulaciones.configure(
            text=" · ".join(f"«{f}»" for f in frases) if frases else "(ninguna)", fg=COLOR_TEXTO)

    def guardar_sinonimo(self):
        try:
            res = self.puente.ensenar_sinonimo(self.var_frase.get(), self._req_elegido(), self.var_pol.get())
        except Exception as error:
            _pintar_mensaje(self.lbl_msg_sin, f"Error al consultar SWI-Prolog: {error}", "error")
            return
        if res["tipo"] != "ok":
            _pintar_mensaje(self.lbl_msg_sin, "✖ " + con_tildes(res["mensaje"]), "error")
            return
        _pintar_mensaje(self.lbl_msg_sin, "✔ " + con_tildes(res["mensaje"]), "exito")
        self.var_prueba.set(self.var_frase.get())
        self.var_frase.set("")
        self._mostrar_formulaciones()
        self.controlador.conocimiento_actualizado()

    def probar_frase(self):
        r = self.puente.interpretar(self.var_prueba.get())
        partes = [self.etiquetas.get(q, q) for q in r["requisitos"]]
        partes += [f"NO: {self.etiquetas.get(q, q)}" for q in r["negados"]]
        txt = "✔ Entendí: " + ("; ".join(partes) if partes else "(nada)")
        if r["no_entendido"]:
            txt += "\n⚠ No entendí: " + ", ".join(r["no_entendido"])
        self.lbl_prueba.configure(text=txt)

    # --- Pestaña 4: Reglas y conocimiento aprendido ---
    def _pestana_aprendido(self):
        tab = ttk.Frame(self.pestanas, padding=10)
        self.pestanas.add(tab, text="  📚 Reglas y conocimiento aprendido  ")
        self.lbl_msg_apr = _etiqueta_mensaje(tab)
        self.lbl_msg_apr.pack(fill="x", side="bottom", pady=(6, 0))
        panel = PanelDesplazable(tab)
        panel.pack(fill="both", expand=True)
        self.zona_aprendido = panel.interior

    def refrescar(self):
        """Relee de Prolog estilos (también los aprendidos) y lo aprendido."""
        self.estilos = self.puente.estilos()
        nombres = [n for n, _d in self.estilos.values()]
        self.combo_estilo.configure(values=nombres)
        if self.var_estilo_regla.get() not in nombres:
            self.var_estilo_regla.set(nombres[0] if nombres else "")
        self._dibujar_aprendido()

    def _seccion(self, titulo, items, vacio, dibujar_item):
        card = _tarjeta(self.zona_aprendido, padx=14, pady=10)
        card.pack(fill="x", pady=(0, 8), padx=(0, 4))
        _titulo(card, f"{titulo} ({len(items)})", COLOR_PRIMARIO).pack(anchor="w", pady=(0, 4))
        if not items:
            tk.Label(card, text=vacio, font=(FUENTE_BASE, 9), bg=COLOR_TARJETA,
                     fg=COLOR_TEXTO_MUTED).pack(anchor="w")
        for it in items:
            fila = tk.Frame(card, bg=COLOR_TARJETA)
            fila.pack(fill="x", pady=2)
            texto, accion = dibujar_item(it)
            ttk.Button(fila, text="🗑", width=3, style="Peligro.TButton",
                       command=accion).pack(side="right", padx=(6, 0))
            tk.Label(fila, text=texto, font=(FUENTE_BASE, 9), bg=COLOR_TARJETA, fg=COLOR_TEXTO,
                     justify="left", anchor="w", wraplength=1050).pack(side="left", fill="x")

    def _dibujar_aprendido(self):
        for h in self.zona_aprendido.winfo_children():
            h.destroy()
        reglas = self.puente.reglas_aprendidas()
        estilos = self.puente.estilos_aprendidos()
        sinonimos = self.puente.sinonimos_aprendidos()

        def item_regla(r):
            nombre = self.estilos.get(r["estilo"], (r["estilo"], ""))[0]
            efecto = f"+{r['peso']} a {nombre}" if r["efecto"] == "recomendar" else f"descarta {nombre}"
            conds = ", ".join(self.etiquetas.get(c, c) for c in r["condiciones"])
            excl = ", ".join(self.etiquetas.get(x, x) for x in r["exclusiones"]) or "—"
            texto = (f"{r['id']}  ·  {efecto}\n   SI: {conds}\n   Y NO: {excl}\n"
                     f"   «{con_tildes(r['explicacion'])}»")
            return texto, lambda i=r["id"]: self.eliminar_regla(i)

        def item_estilo(e):
            id_estilo, nombre = e
            return f"{nombre}  ({id_estilo})", lambda i=id_estilo, n=nombre: self.eliminar_estilo(i, n)

        def item_sinonimo(s):
            frase, req, pol = s
            return (f"«{frase}» → {self.etiquetas.get(req, req)} ({pol})",
                    lambda f=frase: self.eliminar_sinonimo(f))

        self._seccion("REGLAS EXPERTAS", reglas, "Todavía no hay reglas aprendidas.", item_regla)
        self._seccion("ARQUITECTURAS APRENDIDAS", estilos, "Todavía no hay arquitecturas aprendidas.", item_estilo)
        self._seccion("SINÓNIMOS DEL VOCABULARIO", sinonimos, "Todavía no hay sinónimos aprendidos.", item_sinonimo)

    def _tras_eliminar(self, ok, texto_ok, texto_fallo):
        _pintar_mensaje(self.lbl_msg_apr, texto_ok if ok else texto_fallo, "exito" if ok else "error")
        self.controlador.conocimiento_actualizado()

    def eliminar_regla(self, id_regla):
        if not messagebox.askyesno("Confirmar", f"¿Eliminar la regla experta «{id_regla}»?\n"
                                   "Se retracta de la base y se reescribe el archivo de aprendizaje."):
            return
        try:
            ok = self.puente.olvidar_regla(id_regla)
        except Exception as error:
            ok, id_regla = False, f"{id_regla} ({error})"
        self._tras_eliminar(ok, f"✔ Regla «{id_regla}» eliminada.", f"✖ No se pudo eliminar «{id_regla}».")

    def eliminar_estilo(self, id_estilo, nombre):
        if not messagebox.askyesno("Confirmar", f"¿Eliminar la arquitectura «{nombre}» ({id_estilo})?\n"
                                   "También se eliminan las reglas expertas que hablan de ella."):
            return
        if not self.puente.olvidar_estilo(id_estilo):
            self._tras_eliminar(False, "", f"✖ Prolog no eliminó «{nombre}»: no es una arquitectura aprendida.")
            return
        try:
            self.puente.guardar_aprendizaje()
            self._tras_eliminar(True, f"✔ Arquitectura «{nombre}» eliminada.", "")
        except Exception as error:
            self._tras_eliminar(False, "", f"⚠ Se eliminó en memoria, pero no se pudo actualizar el archivo: {error}")

    def eliminar_sinonimo(self, frase):
        if not messagebox.askyesno("Confirmar", f"¿Eliminar el sinónimo «{frase}»?"):
            return
        try:
            ok = self.puente.olvidar_sinonimo(frase)
        except Exception:
            ok = False
        self._tras_eliminar(ok, f"✔ Sinónimo «{frase}» eliminado.", f"✖ No se pudo eliminar «{frase}».")

    def al_mostrar(self):
        self.refrescar()

    def ir_a_pestana(self, indice):
        self.pestanas.select(indice)


# ---------------------------------------------------------------------------
# 6.4 VISTA: HISTORIAL DE EVALUACIONES
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
        estilos_actuales = self.controlador.puente.estilos()
        for c in consultas:
            # Si el estilo era aprendido y luego se eliminó, se muestra su id.
            estilo = c.get("estilo", "")
            id_estilo = c.get("estilo_id")
            if id_estilo and id_estilo not in estilos_actuales:
                estilo = f"{id_estilo} (eliminada)"
            self.tabla.insert(
                "", "end",
                values=(
                    c.get("fecha", ""),
                    ", ".join(c.get("requisitos", [])),
                    estilo,
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
        self.rol = "usuario"              # usuario | experto
        self._etiquetas_rol = []          # chips de rol de cada encabezado

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
        for ClaseVista in (VistaInicio, VistaEvaluacion, VistaModoExperto, VistaHistorial):
            vista = ClaseVista(contenedor, self)
            self.vistas[ClaseVista.__name__] = vista
            vista.grid(row=0, column=0, sticky="nsew")

        self._actualizar_etiquetas_rol()
        self.mostrar_vista("VistaInicio")
        self.after(400, self._avisar_aprendizaje_danado)

    # --- Rol (control de acceso de DEMOSTRACIÓN) ---
    def registrar_etiqueta_rol(self, etiqueta):
        self._etiquetas_rol.append(etiqueta)

    def _actualizar_etiquetas_rol(self):
        if self.rol == "experto":
            texto, bg_c, fg_c = "🛡 ROL: EXPERTO", COLOR_AMBAR_BG, COLOR_AMBAR_TEXT
        else:
            texto, bg_c, fg_c = "👤 ROL: USUARIO", "#1e293b", COLOR_HEADER_SUB
        for lbl in self._etiquetas_rol:
            lbl.configure(text=texto, bg=bg_c, fg=fg_c)

    def cambiar_rol(self, rol, pin=None):
        """Experto exige el PIN (pin_valido compara su sha256). Devuelve True si
        el rol quedó aplicado. pin=None lo pide con un diálogo."""
        pedido = rol
        if rol == "experto" and self.rol != "experto":
            if pin is None:
                pin = simpledialog.askstring("Modo Experto", "PIN del experto:", show="*", parent=self)
            if not pin_valido(pin):
                if pin is not None:
                    messagebox.showerror("Modo Experto", "PIN incorrecto. Se mantiene el rol Usuario.")
                rol = "usuario"
        if rol not in ("usuario", "experto"):
            rol = "usuario"
        self.rol = rol
        self._actualizar_etiquetas_rol()
        inicio = self.vistas.get("VistaInicio")
        if inicio is not None:
            inicio.actualizar_rol()
        return self.rol == pedido

    def abrir_modo_experto(self, pestana=0):
        if self.rol != "experto":
            messagebox.showinfo("Modo Experto",
                                "Esta función requiere el rol Experto.\n"
                                "Cámbielo en la pantalla de Inicio (se pide el PIN).")
            return False
        self.mostrar_vista("VistaModoExperto")
        self.vistas["VistaModoExperto"].ir_a_pestana(pestana)
        return True

    def _avisar_aprendizaje_danado(self):
        tipo, detalle = self.puente.estado_aprendizaje
        if tipo == "danado":
            messagebox.showwarning(
                "ArquiSelect",
                "El archivo conocimiento_aprendido.pl estaba dañado y no se cargó.\n"
                f"Se guardó una copia en:\n{detalle}\n\n"
                "La aplicación funciona con la base del experto.")

    def conocimiento_actualizado(self):
        """Tras enseñar u olvidar un estilo: refresca lo que depende de la base
        sin reiniciar (estilos, descripciones, comparativa, ranking, dictamen,
        preguntas guiadas y la lista de aprendidas)."""
        self.vistas["VistaEvaluacion"].refrescar_conocimiento()
        self.vistas["VistaModoExperto"].refrescar()

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
        estilo.configure("Rol.TRadiobutton", background=COLOR_FONDO, foreground=COLOR_TEXTO,
                         font=(FUENTE_BASE, 10, "bold"))
        estilo.map("Rol.TRadiobutton", background=[("active", COLOR_SUPERFICIE)])
        estilo.configure("Tarjeta.TRadiobutton", background=COLOR_TARJETA, foreground=COLOR_TEXTO,
                         font=(FUENTE_BASE, 9))
        estilo.map("Tarjeta.TRadiobutton", background=[("active", COLOR_SUPERFICIE)])

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
        if nombre_vista == "VistaModoExperto" and self.rol != "experto":
            return                         # con rol Usuario no hay acceso
        vista = self.vistas[nombre_vista]
        if hasattr(vista, "al_mostrar"):
            vista.al_mostrar()
        vista.tkraise()

    def recargar_kb(self):
        try:
            self.puente.recargar()
            self.conocimiento_actualizado()
            self._avisar_aprendizaje_danado()
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
