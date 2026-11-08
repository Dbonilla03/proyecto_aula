"""
pruebas_contradicciones.py - Contradicciones y robustez de ArquiSelect (consola).

    python pruebas_contradicciones.py   -> imprime el resultado y escribe
                                           evidencia_contradicciones.txt

A. Contradicciones duras: cada par bloquea, en los dos ordenes.
B. Tensiones: solo advierten; el diagnostico sigue.
C. Entrada sucia y combinaciones (mayusculas, repetidos, dura + tension).
D. Lenguaje natural: la caja "Describe tu proyecto" llega al mismo bloqueo.
E. 10 entradas hostiles al DCG + limites de longitud y de tiempo.
F. Interfaz real (Tk, ventana oculta): banner rojo / ambar.

Reglas: los resultados esperados se escribieron ANTES de ejecutar (constantes
en mayusculas y el tercer elemento de cada fila). Toda la logica la resuelve
Prolog; aqui solo se consulta y se compara. Se usa un archivo de aprendizaje
TEMPORAL: conocimiento_aprendido.pl no se toca.
"""
import os
import sys
import shutil
import tempfile
import platform
from datetime import datetime
from importlib import metadata

from main import PuenteProlog, RUTA_BASE_CONOCIMIENTO, lista_prolog

CARPETA = os.path.dirname(os.path.abspath(__file__))
RUTA_EVIDENCIA = os.path.join(CARPETA, "evidencia_contradicciones.txt")
TMP = tempfile.mkdtemp(prefix="arquiselect_contra_")
RUTA_TMP = os.path.join(TMP, "aprendizaje_pruebas.pl").replace("\\", "/")

# ---------------------------------------------------------------------------
# Resultados esperados (definidos antes de ejecutar)
# ---------------------------------------------------------------------------
PARES_DUROS = [("equipo_pequeno", "equipo_grande"), ("latencia_critica", "procesos_largos")]
PARES_TENSION = [("disponibilidad_alta", "presupuesto_bajo"),
                 ("consistencia_estricta", "integracion_asincrona")]
MENSAJE_EQUIPO = ("Contradiccion: equipo_pequeno y equipo_grande son excluyentes; "
                  "el proyecto no puede tener los dos.")
MENSAJE_AMBAS = 'Contradiccion: presupuesto_bajo esta marcado como requisito y tambien como "no aplica".'
AVISO_LARGO = "(texto demasiado largo: maximo 2000 caracteres)"
AVISO_TIEMPO = "(tiempo de analisis agotado)"

# (descripcion, texto, Requisitos esperados, Negados esperados)
HOSTILES = [
    ("vacio", "", [], []),
    ("solo espacios, tab y salto de linea", "   \n\t  ", [], []),
    ("solo emojis", "😀🚀🔥", [], []),
    ("emoji en medio de una frase valida", "equipo pequeño 😀 y poco presupuesto",
     ["equipo_pequeno", "presupuesto_bajo"], []),
    ("intento de inyeccion sin comillas", "foo), halt(", [], []),
    ("comillas simples y dobles", "it's \"quoted\" 'text'", [], []),
    ("inyeccion con barra y comilla", "\\'), halt, ('", [], []),
    ("caracteres de control (NUL, BEL, ESC)", "equipo\x00pequeño\x07 \x1b[31m", ["equipo_pequeno"], []),
    ("surrogate suelto (emoji partido)", "\ud83d solo poco presupuesto", ["presupuesto_bajo"], []),
    ("texto muy largo (4500 caracteres)", "equipo pequeño " * 300, [], []),
]

puente = PuenteProlog(RUTA_BASE_CONOCIMIENTO, ruta_aprendizaje=RUTA_TMP)
PRUEBAS = []
salida = []


def log(texto=""):
    print(texto)
    salida.append(texto)


def prueba(codigo, titulo):
    def registrar(func):
        PRUEBAS.append((codigo, titulo, func))
        return func
    return registrar


def q(meta):
    return puente.una_solucion("prueba", meta)


def consistencia(reqs, negados=()):
    return puente.consistencia(list(reqs), list(negados))


def bloqueo_completo(reqs, negados=()):
    """Lo que debe pasar con una contradiccion dura, en una tupla comparable."""
    c = consistencia(reqs, negados)
    d = puente.diagnosticar(list(reqs))
    qf = puente.que_falta(list(reqs), list(negados))
    return (c["Estado"], d["Mejor"], d["Prioridad"], d["Ranking"],
            qf["Estado"], qf["Competencia"], qf["Sugerencias"])


BLOQUEADO = ("bloqueado", "ninguno", "bloqueado", [], "contradictorio", [], [])


# ---------------------------------------------------------------------------
# A. Contradicciones duras
# ---------------------------------------------------------------------------
@prueba("A1", "Cada par duro bloquea diagnosticar_arquitectura/9 y que_falta/6, en ambos ordenes")
def a1():
    filas = []
    for a, b in PARES_DUROS:
        for reqs in ([a, b], [b, a], [a, "presupuesto_bajo", b]):
            filas.append((f"{reqs}", bloqueo_completo(reqs), BLOQUEADO,
                          "(consistencia, Mejor, Prioridad, Ranking, Estado qf, Competencia, Sugerencias)"))
    return filas


@prueba("A2", "Requisito afirmado y negado a la vez (Requisitos y Negados)")
def a2():
    reqs, negs = ["presupuesto_bajo", "equipo_pequeno"], ["presupuesto_bajo"]
    c = consistencia(reqs, negs)
    qf = puente.que_falta(reqs, negs)
    d = puente.diagnosticar(reqs)
    return [
        ("consistencia_entrada", (c["Estado"], c["Lista"]),
         ("bloqueado", [["presupuesto_bajo", "presupuesto_bajo", "dura", MENSAJE_AMBAS]]), ""),
        ("que_falta/6", (qf["Estado"], qf["Confianza"], qf["Sugerencias"]), ("contradictorio", "nula", []),
         "1a clausula de que_falta/6"),
        ("diagnosticar/9 NO lo ve (su firma no recibe Negados)", d["Mejor"] != "ninguno", True,
         "por eso la interfaz decide con el Estado de que_falta/6"),
        ("sin el negado ya no hay bloqueo", consistencia(reqs, [])["Estado"], "consistente", ""),
    ]


@prueba("A3", "Mensaje de Prolog para el par excluyente (reutiliza excluyentes/2)")
def a3():
    d = puente.diagnosticar(["equipo_grande", "equipo_pequeno"])
    return [("Razones", d["Razones"], [MENSAJE_EQUIPO], "el orden del mensaje sale de excluyentes/2"),
            ("Perfil y Suficiencia", (d["Perfil"], d["Suficiencia"]), ("ninguno", "contradictoria"), "")]


@prueba("A4", "Steadfast: llamar con Mejor ya fijado no se salta el bloqueo")
def a4():
    meta = (f"diagnosticar_arquitectura({lista_prolog(['equipo_pequeno', 'equipo_grande'])}, "
            "monolito_capas, _, _, _, _, _, _, _)")
    return [("diagnosticar_arquitectura(..., monolito_capas, ...) falla", q(meta), None,
             "las salidas se ligan despues del corte")]


# ---------------------------------------------------------------------------
# B. Tensiones
# ---------------------------------------------------------------------------
@prueba("B1", "Cada tension advierte y NO bloquea, en ambos ordenes")
def b1():
    filas = []
    for a, b in PARES_TENSION:
        for reqs in ([a, b], [b, a]):
            c = consistencia(reqs)
            d = puente.diagnosticar(reqs)
            qf = puente.que_falta(reqs, [])
            filas.append((f"{reqs}",
                          (c["Estado"], len(c["Lista"]), c["Lista"][0][2] if c["Lista"] else None,
                           d["Mejor"] != "ninguno", d["Prioridad"] != "bloqueado",
                           qf["Estado"] != "contradictorio"),
                          ("advertencia", 1, "tension", True, True, True),
                          "(Estado, n, Tipo, hay recomendacion, prioridad normal, que_falta normal)"))
    return filas


@prueba("B2", "La tension no se mete en el diagnostico (solo la informa consistencia_entrada/4)")
def b2():
    reqs = ["disponibilidad_alta", "presupuesto_bajo", "equipo_pequeno"]
    d = puente.diagnosticar(reqs)
    return [("Ranking no vacio", len(d["Ranking"]) > 0, True, ""),
            ("Razones sin el aviso de tension", any("Tension" in str(r) for r in d["Razones"]), False,
             "diagnosticar_arquitectura/9 solo cambia con contradicciones duras")]


# ---------------------------------------------------------------------------
# C. Entrada sucia y combinaciones
# ---------------------------------------------------------------------------
@prueba("C1", "Caso normal: consistente")
def c1():
    c = consistencia(["equipo_pequeno", "presupuesto_bajo", "entrega_rapida"])
    return [("consistencia_entrada", (c["Estado"], c["Lista"]), ("consistente", []), "")]


@prueba("C2", "Mayusculas, repetidos y desconocidos pasan por preparar_requisitos/2")
def c2():
    c1_ = consistencia(["Equipo_Pequeno", "EQUIPO_GRANDE"])
    c2_ = consistencia(["latencia_critica", "procesos_largos", "latencia_critica", "xyz"])
    return [("mayusculas", c1_["Estado"], "bloqueado", "downcase_atom/2"),
            ("repetido: una sola contradiccion", len(c2_["Lista"]), 1, "list_to_set/2"),
            ("Desconocidos se siguen informando",
             puente.diagnosticar(["equipo_pequeno", "equipo_grande", "xyz"])["Desconocidos"], ["xyz"], "")]


@prueba("C3", "Dura + tension juntas: manda la dura y se listan las dos")
def c3():
    c = consistencia(["equipo_pequeno", "equipo_grande", "disponibilidad_alta", "presupuesto_bajo"])
    return [("Estado", c["Estado"], "bloqueado", "1a clausula de estado_consistencia/2"),
            ("Tipos", sorted(x[2] for x in c["Lista"]), ["dura", "tension"], "")]


@prueba("C4", "Entradas no lista no rompen contradicciones/3")
def c4():
    r = q("contradicciones(hola, f(x), L), consistencia_entrada(_, 3, E, _)")
    return [("contradicciones(hola, f(x), L)", (r["L"], r["E"]) if r else None, ([], "consistente"),
             "validar_entrada/2 devuelve [] con algo que no es lista")]


# ---------------------------------------------------------------------------
# D. Lenguaje natural
# ---------------------------------------------------------------------------
@prueba("D1", "La caja 'Describe tu proyecto' llega al mismo bloqueo / aviso")
def d1():
    r1 = puente.interpretar("equipo de 3 personas y equipo de 20 personas")
    r2 = puente.interpretar("responder en menos de 100 ms y procesos largos")
    r3 = puente.interpretar("alta disponibilidad con poco presupuesto")
    return [
        ("texto 1 -> requisitos", r1["requisitos"], ["equipo_pequeno", "equipo_grande"], "umbrales 5 y 10"),
        ("texto 1 -> bloqueado", consistencia(r1["requisitos"], r1["negados"])["Estado"], "bloqueado", ""),
        ("texto 2 -> bloqueado", consistencia(r2["requisitos"], r2["negados"])["Estado"], "bloqueado", ""),
        ("texto 3 -> advertencia", consistencia(r3["requisitos"], r3["negados"])["Estado"], "advertencia", ""),
    ]


# ---------------------------------------------------------------------------
# E. Entradas hostiles al DCG
# ---------------------------------------------------------------------------
@prueba("E1", "10 entradas hostiles: sin excepcion, resultado esperado y Prolog sigue vivo")
def e1():
    filas = []
    for desc, texto, reqs, negs in HOSTILES:
        try:
            r = puente.interpretar(texto)
            obtenido = (r["requisitos"], r["negados"])
        except Exception as error:                      # no deberia ocurrir nunca
            obtenido = f"EXCEPCION {error!r}"
        vivo = puente.interpretar("poco presupuesto")["requisitos"] == ["presupuesto_bajo"]
        filas.append((desc, (obtenido, vivo), ((reqs, negs), True), "((Requisitos, Negados), Prolog vivo)"))
    return filas


@prueba("E2", "Limite de longitud: 2000 se analiza, 2001 se rechaza con aviso")
def e2():
    r2000 = puente.interpretar("poco presupuesto".ljust(2000))
    r2001 = puente.interpretar("poco presupuesto".ljust(2001))
    largo = puente.interpretar(HOSTILES[-1][1])
    return [("2000 caracteres", (r2000["requisitos"], r2000["no_entendido"]), (["presupuesto_bajo"], []), ""),
            ("2001 caracteres", (r2001["requisitos"], r2001["no_entendido"]), ([], [AVISO_LARGO]),
             "1a clausula de interpretar_texto/5"),
            ("4500 caracteres", largo["no_entendido"], [AVISO_LARGO], "")]


@prueba("E3", "Limite de tiempo: con un limite minimo el analisis se corta y avisa")
def e3():
    texto = ("equipo pequeño y poco presupuesto " * 58)[:1999]
    normal = puente.interpretar(texto)
    q("retractall(limite_interpretacion(segundos, _)), assertz(limite_interpretacion(segundos, 0.000001))")
    try:
        cortado = puente.interpretar(texto)
    finally:
        q("retractall(limite_interpretacion(segundos, _)), assertz(limite_interpretacion(segundos, 2))")
    despues = puente.interpretar("poco presupuesto")
    return [("con limite normal (2 s)", normal["requisitos"], ["equipo_pequeno", "presupuesto_bajo"], ""),
            ("con limite 0.000001 s", (cortado["requisitos"], cortado["no_entendido"]), ([], [AVISO_TIEMPO]),
             "call_with_time_limit/2 lanza time_limit_exceeded y catch/3 lo atrapa"),
            ("restaurado", despues["requisitos"], ["presupuesto_bajo"], "")]


# ---------------------------------------------------------------------------
# F. Interfaz real (Tk con ventana oculta; los dialogos se registran, no se muestran)
# ---------------------------------------------------------------------------
@prueba("F1", "Interfaz: banner rojo sin recomendacion, banner ambar con diagnostico, texto hostil")
def f1():
    import tkinter as tk
    import main as app_main
    dialogos = []
    for nombre in ("showerror", "showwarning", "showinfo"):
        setattr(app_main.messagebox, nombre, lambda *a, _n=nombre, **k: dialogos.append(_n))
    historial = app_main.GestorHistorial(os.path.join(TMP, "historial.json"))
    app = app_main.ControladorApp(puente, historial)
    app.withdraw()
    try:
        v = app.vistas["VistaEvaluacion"]

        def escribir(texto):
            v.txt_nl.delete("1.0", "end")
            v.txt_nl.insert("1.0", texto)
            v.interpretar_texto()
            app.update_idletasks()
            return (v.lbl_estilo.cget("text"), v.lbl_estado.cget("bg"),
                    v.lbl_tension.winfo_manager() == "pack")

        rojo = escribir("equipo de 3 personas y equipo de 20 personas")
        texto_rojo = v.lbl_estado.cget("text")
        v.guardar_en_historial()
        ambar = escribir("alta disponibilidad con poco presupuesto")
        texto_ambar = v.lbl_tension.cget("text")
        hostil = escribir("foo), halt( 😀 \x00 '\"")
        v.limpiar()
        v.vars["presupuesto_bajo"].set(1)
        v.negar_dato("presupuesto_bajo")          # marcado y "No aplica" a la vez
        app.update_idletasks()
        ambas = (v.lbl_estilo.cget("text"), v.lbl_estado.cget("bg"))
    finally:
        app.destroy()
    return [
        ("dura: estilo / fondo rojo / sin banner ambar", rojo,
         ("⛔ Sin recomendación", app_main.COLOR_PELIGRO_BG, False), ""),
        ("dura: el banner muestra el mensaje de Prolog", "excluyentes" in texto_rojo, True, ""),
        ("dura: guardar en historial se niega", dialogos[:1], ["showwarning"], ""),
        ("tension: hay recomendacion y banner ambar visible", (ambar[0] != "⛔ Sin recomendación", ambar[2]),
         (True, True), ""),
        ("tension: texto del banner", texto_ambar.startswith("⚠ Tension") or texto_ambar.startswith("⚠ Tensión"),
         True, ""),
        ("texto hostil: la app sigue y no hay dialogo de error", (hostil[2], "showerror" in dialogos),
         (False, False), ""),
        ("marcado + No aplica: banner rojo", ambas, ("⛔ Sin recomendación", app_main.COLOR_PELIGRO_BG),
         "Python ya no quita el negado: decide Prolog"),
    ]


def main():
    log("=" * 78)
    log("EVIDENCIA DE PRUEBAS - ArquiSelect: CONTRADICCIONES Y ROBUSTEZ DEL DCG")
    log(f"Fecha: {datetime.now():%Y-%m-%d %H:%M:%S}   Python {platform.python_version()}   "
        f"pyswip {metadata.version('pyswip')}   SO {platform.system()} {platform.release()}")
    v = q("current_prolog_flag(version, V)")
    log(f"SWI-Prolog {v['V'] if v else '?'}")
    log("=" * 78)

    total = fallos = 0
    for codigo, titulo, func in PRUEBAS:
        log("")
        log(f"[{codigo}] {titulo}")
        try:
            filas = func()
        except Exception as error:
            total += 1
            fallos += 1
            log(f"   FALLA  excepcion: {error!r}")
            continue
        for chequeo, obtenido, esperado, por_que in filas:
            total += 1
            ok = obtenido == esperado
            fallos += not ok
            log(f"   {'OK   ' if ok else 'FALLA'}  {chequeo}: {obtenido!r}")
            if not ok:
                log(f"          esperado: {esperado!r}")
            if por_que:
                log(f"          por que : {por_que}")

    log("")
    log("=" * 78)
    log(f"RESULTADO: {total - fallos}/{total} verificaciones correctas, {fallos} fallas.")
    with open(RUTA_EVIDENCIA, "w", encoding="utf-8") as f:
        f.write("\n".join(salida) + "\n")
    shutil.rmtree(TMP, ignore_errors=True)
    print(f"\nEvidencia escrita en {RUTA_EVIDENCIA}")
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
