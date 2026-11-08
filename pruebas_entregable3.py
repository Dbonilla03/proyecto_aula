"""
pruebas_entregable3.py - Pruebas del Entregable 3 de ArquiSelect (consola).

    python pruebas_entregable3.py     -> imprime el resultado y escribe
                                         evidencia_entregable3.txt

A. Lenguaje natural con DCG (interpretar_texto/5).
B. Modo Experto: reglas inyectadas con ensenar_regla/8 (efecto en el
   razonamiento y validaciones negativas).
C. Persistencia: la regla y el sinonimo sobreviven a un PROCESO NUEVO de
   Python/SWI-Prolog (subprocess) y se pueden eliminar.
D. No regresion: pruebas.py (entregable 2) sigue pasando y, sin reglas que se
   disparen, nada cambia.

Reglas de las pruebas:
- Los resultados esperados estan definidos ANTES de ejecutar (constantes
  ESPERADO_* y en cada prueba con su justificacion). No se ajustan a lo que
  salga: si una prueba falla, se corrige el codigo o se justifica el cambio.
- Cada prueba arranca con limpiar_aprendizaje/1: olvida lo aprendido en
  memoria y borra el archivo de aprendizaje TEMPORAL. El archivo real
  conocimiento_aprendido.pl nunca se toca (se verifica al final).
- Toda la logica la resuelve Prolog; aqui solo se consulta y se compara.
"""
import os
import sys
import json
import shutil
import tempfile
import platform
import subprocess
from datetime import datetime
from importlib import metadata

from main import PuenteProlog, RUTA_BASE_CONOCIMIENTO, atomo, lista_prolog

CARPETA = os.path.dirname(os.path.abspath(__file__))
RUTA_EVIDENCIA = os.path.join(CARPETA, "evidencia_entregable3.txt")
RUTA_REAL = os.path.join(CARPETA, "conocimiento_aprendido.pl")

# ---------------------------------------------------------------------------
# Resultados esperados (definidos antes de ejecutar)
# ---------------------------------------------------------------------------
# (texto, Requisitos, Negados, NoEntendido)
ESPERADO_DCG = {
    "a": ("Somos un equipo de tres personas con poco presupuesto y necesitamos entregar rapido",
          ["equipo_pequeno", "presupuesto_bajo", "entrega_rapida"], [], []),
    "b": ("La aplicacion tendra muchos usuarios al mismo tiempo y debe estar disponible las 24 horas",
          ["muchos_usuarios", "disponibilidad_alta"], [], []),
    "c": ("El equipo no tiene experiencia en DevOps",
          ["sin_experiencia_devops"], [], []),
    "d": ("No necesitamos alta disponibilidad",
          [], ["disponibilidad_alta"], []),
    "e": ("Equipo de 20 personas y dominio complejo con muchas reglas de negocio",
          ["equipo_grande", "dominio_complejo"], [], []),
    "f": ("Necesitamos poder cambiar la base de datos sin reescribir todo",
          ["independencia_tecnologica"], [], []),
    "g": ("asdf qwerty", [], [], ["asdf", "qwerty"]),
    "h1": ("", [], [], []),
    "h2": ("   ", [], [], []),
    "i": ("PRESUPUESTO LIMITADO Y ENTREGA RÁPIDA",
          ["presupuesto_bajo", "entrega_rapida"], [], []),
}

# Casos adicionales: (texto, Requisitos, Negados, justificacion)
ESPERADO_EXTRA = [
    ("carga estable y pocos usuarios", [], ["carga_variable", "muchos_usuarios"],
     "polaridad 'niega' en el lexico"),
    ("no necesitamos alta disponibilidad ni despliegue independiente", [],
     ["disponibilidad_alta", "despliegue_independiente"], "'ni' es otra negacion"),
    ("no tenemos carga estable", ["carga_variable"], [], "doble negacion afirma"),
    ("poco presupuesto pero presupuesto amplio", [], ["presupuesto_bajo"],
     "si un requisito se menciona dos veces gana la ultima mencion"),
    ("sin caidas", ["disponibilidad_alta"], [], "frase lexica que empieza con 'sin' (no es negacion)"),
    ("equipo de 7 personas", [], [], "5 <= 7 < 10: no cumple ningun umbral"),
    ("somos 4", ["equipo_pequeno"], [], "4 < 5"),
    ("somos 12 desarrolladores", ["equipo_grande"], [], "12 >= 10"),
    ("500 usuarios", [], [], "500 < 1000"),
    ("mas de 1000 usuarios", ["muchos_usuarios"], [], "1000 >= 1000"),
    ("10 mil usuarios concurrentes", ["muchos_usuarios"], [], "10 mil = 10000"),
    ("miles de usuarios", ["muchos_usuarios"], [], "frase lexica"),
    ("responder en menos de 100 ms", ["latencia_critica"], [], "100 <= 100 ms"),
    ("respuesta en 2 segundos", [], [], "2000 ms > 100 ms"),
    ("entregar en 3 semanas", ["entrega_rapida"], [], "3 <= 6 semanas"),
    ("salir en 30 dias", ["entrega_rapida"], [], "30 dias -> 5 semanas"),
    ("entregar en 6 meses", [], [], "6 meses -> 24 semanas > 6"),
    ("disponible 24/7, legacy y transacciones", ["disponibilidad_alta",
     "integracion_sistemas_heredados", "consistencia_estricta"], [], "signos separan tokens"),
]

CASO_DEMO = ["equipo_pequeno", "separar_interfaz_logica"]
REGLA_DEMO = ("mvc_para_equipos_pequenos",
              "Para equipos pequenos que separan interfaz y logica, MVC es suficiente",
              "mvc", "recomendar", 3, CASO_DEMO, ["dominio_complejo"])
# Sin la regla: monolito_capas 3+2 = 5 y mvc 2+3 = 5 empatan; setof ordena
# alfabeticamente ('mo' < 'mv'). Con la regla: mvc 5 + 3 = 8.
ESPERADO_RANKING_SIN_REGLA = [("monolito_capas", 5), ("mvc", 5)]
ESPERADO_RANKING_CON_REGLA = [("mvc", 8), ("monolito_capas", 5)]

# ---------------------------------------------------------------------------
# Modo hijo: proceso NUEVO que solo carga lo aprendido y reporta en JSON
# ---------------------------------------------------------------------------
if len(sys.argv) == 3 and sys.argv[1] == "--hijo":
    hijo = PuenteProlog(RUTA_BASE_CONOCIMIENTO, ruta_aprendizaje=sys.argv[2])
    hijo.consultar(f"cargar_aprendizaje({atomo(sys.argv[2].replace(chr(92), '/'))})")
    ranking = [[e, p] for e, p, _a, _b in hijo.candidatos(CASO_DEMO)][:2]
    print(json.dumps({
        "reglas": [r["id"] for r in hijo.reglas_aprendidas()],
        "sinonimos": hijo.sinonimos_aprendidos(),
        "ranking": ranking,
        "recursos_escasos": hijo.interpretar("recursos escasos")["requisitos"],
        "pid": os.getpid(),
    }))
    sys.exit(0)

# ---------------------------------------------------------------------------
TMP = tempfile.mkdtemp(prefix="arquiselect_e3_")
RUTA_TMP = os.path.join(TMP, "aprendizaje_pruebas.pl").replace("\\", "/")
REAL_ANTES = (os.path.exists(RUTA_REAL), os.path.getmtime(RUTA_REAL) if os.path.exists(RUTA_REAL) else None)

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


def nl(texto):
    return puente.interpretar(texto)


def regla(id_r, expl, estilo, efecto, peso, conds, excls):
    """ensenar_regla/8; devuelve el Resultado como texto Prolog."""
    peso_txt = str(peso) if isinstance(peso, int) else atomo(peso)
    r = q(f"ensenar_regla({atomo(id_r)}, {atomo(expl)}, {atomo(estilo)}, {atomo(efecto)}, "
          f"{peso_txt}, {lista_prolog(conds)}, {lista_prolog(excls)}, R), term_to_atom(R, T)")
    return r["T"] if r else None


def top(reqs, n=2):
    return [(e, p) for e, p, _a, _b in puente.candidatos(reqs)][:n]


def n_reglas():
    return len(puente.reglas_aprendidas())


def leer_tmp():
    if not os.path.exists(RUTA_TMP):
        return ""
    with open(RUTA_TMP, encoding="utf-8") as f:
        return f.read()


def proceso_hijo():
    """Lanza un proceso NUEVO de Python + SWI-Prolog que solo carga el archivo."""
    r = subprocess.run([sys.executable, os.path.abspath(__file__), "--hijo", RUTA_TMP],
                       capture_output=True, text=True, encoding="utf-8", cwd=CARPETA, timeout=120)
    linea = [ln for ln in r.stdout.splitlines() if ln.startswith("{")]
    return json.loads(linea[-1]) if linea else {"error": r.stderr[-400:]}


# ---------------------------------------------------------------------------
# A. Lenguaje natural (DCG)
# ---------------------------------------------------------------------------
@prueba("A1", "Casos minimos a-i del enunciado")
def a1():
    filas = []
    for clave, (texto, reqs, negs, no_ent) in ESPERADO_DCG.items():
        r = nl(texto)
        filas.append((f"{clave}) {texto!r}",
                      (r["requisitos"], r["negados"], r["no_entendido"]),
                      (reqs, negs, no_ent), "(Requisitos, Negados, NoEntendido)"))
    return filas


@prueba("A2", "c) 'sin experiencia en DevOps' es un requisito, NO una negacion")
def a2():
    r = nl("El equipo no tiene experiencia en DevOps")
    r2 = nl("Equipo sin experiencia en devops")
    return [
        ("no aparece en Negados", "sin_experiencia_devops" in r["negados"], False,
         "lexico/3 la marca con polaridad afirma y se prueba ANTES que la negacion"),
        ("arbol: frase lexica, sin nodo de negacion",
         [ln.strip() for ln in r["arbol"] if "negacion" in ln or "frase lexica" in ln],
         ['frase lexica: "no tiene experiencia en devops" -> sin_experiencia_devops (afirma)'], ""),
        ("variante con 'sin'", (r2["requisitos"], r2["negados"]), (["sin_experiencia_devops"], []), ""),
    ]


@prueba("A3", "d) negacion gramatical en el arbol")
def a3():
    r = nl("No necesitamos alta disponibilidad")
    return [
        ("arbol", r["arbol"],
         ["oracion", "  sintagma 1", "    negacion: no", "    relleno: necesitamos",
          '    frase lexica: "alta disponibilidad" -> disponibilidad_alta (afirma)',
          "    => disponibilidad_alta NEGADO"],
         "sintagma = negacion opcional + rellenos + nucleo"),
    ]


@prueba("A4", "h) entradas vacias o no textuales nunca lanzan excepcion")
def a4():
    filas = []
    for meta, desc in (("interpretar_texto('', R, N, E, A)", "atomo vacio"),
                       ('interpretar_texto("", R, N, E, A)', "string vacio"),
                       ("interpretar_texto('!!! ??? ...', R, N, E, A)", "solo signos de puntuacion"),
                       ("interpretar_texto(123, R, N, E, A)", "numero"),
                       ("interpretar_texto(_, R, N, E, A)", "variable libre"),
                       ("interpretar_texto(f(x), R, N, E, A)", "termino compuesto")):
        r = q(meta)
        filas.append((desc, (r["R"], r["N"], r["E"]) if r else None, ([], [], []), "listas vacias"))
    r = nl("@@ ##")
    filas.append(("simbolos raros -> NoEntendido", (r["requisitos"], r["no_entendido"]), ([], ["@@", "##"]), ""))
    return filas


@prueba("A5", "Atomo y string dan el mismo resultado")
def a5():
    t = ESPERADO_DCG["a"][0]
    ra = q(f"interpretar_texto({atomo(t)}, R, N, E, _)")
    rs = q(f'interpretar_texto("{t}", R, N, E, _)')
    return [("atomo == string", (ra["R"], ra["N"], ra["E"]), (rs["R"], rs["N"], rs["E"]), "")]


@prueba("A6", "Frases numericas, polaridad 'niega', negacion 'ni', doble negacion y ultima mencion")
def a6():
    filas = []
    for texto, reqs, negs, por_que in ESPERADO_EXTRA:
        r = nl(texto)
        filas.append((repr(texto), (r["requisitos"], r["negados"]), (reqs, negs), por_que))
    return filas


@prueba("A7", "Umbrales como hechos: cambiar umbral_numerico/3 cambia el resultado")
def a7():
    antes = nl("equipo de 7 personas")["requisitos"]
    q("retract(umbral_numerico(equipo_pequeno, menor, 5)), "
      "asserta(umbral_numerico(equipo_pequeno, menor, 8))")
    despues = nl("equipo de 7 personas")["requisitos"]
    q("retract(umbral_numerico(equipo_pequeno, menor, 8)), "
      "asserta(umbral_numerico(equipo_pequeno, menor, 5))")
    return [("con umbral 5", antes, [], "7 no es < 5"),
            ("con umbral 8", despues, ["equipo_pequeno"], "7 < 8"),
            ("umbral restaurado", nl("equipo de 7 personas")["requisitos"], [], "")]


@prueba("A8", "Lexico: los 20 requisitos tienen al menos 3 formulaciones (afirma)")
def a8():
    reqs = [r["id"] for r in puente.requisitos_disponibles()]
    pocos = {r: len(f) for r in reqs
             if len(f := [x for x in puente.formulaciones(r) if not x.endswith("(niega)")]) < 3}
    total = q("aggregate_all(count, lexico(_,_,_), N)")["N"]
    return [("requisitos", len(reqs), 20, ""),
            ("con menos de 3 formulaciones", pocos, {}, ""),
            ("entradas de lexico/3", total >= 60, True, f"{total} frases")]


@prueba("A9", "j) Sinonimo agregado en caliente: 'recursos escasos' -> presupuesto_bajo")
def a9():
    antes = nl("tenemos recursos escasos")
    res = q("ensenar_sinonimo('recursos escasos', presupuesto_bajo, R), term_to_atom(R, T)")["T"]
    despues = nl("tenemos recursos escasos")
    dup = q("ensenar_sinonimo('Recursos  ESCASOS', presupuesto_bajo, R), term_to_atom(R, T)")["T"]
    conflicto = q("ensenar_sinonimo('poco presupuesto', entrega_rapida, R), term_to_atom(R, T)")["T"]
    funcional = q("ensenar_sinonimo('el de la', entrega_rapida, R), term_to_atom(R, T)")["T"]
    return [
        ("antes", (antes["requisitos"], antes["no_entendido"]), ([], ["recursos", "escasos"]), ""),
        ("ensenar_sinonimo/3", res, "ok([recursos,escasos])", ""),
        ("despues (sin reiniciar)", despues["requisitos"], ["presupuesto_bajo"], ""),
        ("duplicado (mayusculas/espacios)", dup, "error(ya_existe(presupuesto_bajo))", "misma normalizacion"),
        ("conflicto con el lexico", conflicto, "error(conflicto(presupuesto_bajo))", ""),
        ("solo palabras funcionales", funcional, "error(frase_solo_funcional)", ""),
        ("escrito en el archivo", "lexico([recursos, escasos], presupuesto_bajo, afirma)." in leer_tmp(), True, ""),
    ]


# ---------------------------------------------------------------------------
# B. Modo Experto: reglas inyectadas
# ---------------------------------------------------------------------------
@prueba("B1", "La regla del demo cambia el ranking sin reiniciar")
def b1():
    antes = top(CASO_DEMO)
    res = regla(*REGLA_DEMO)
    despues = top(CASO_DEMO)
    excl = top(CASO_DEMO + ["dominio_complejo"], 1)
    clausula = q(f"clausula_regla_texto({REGLA_DEMO[0]}, T)")["T"]
    return [
        ("ranking sin regla", antes, ESPERADO_RANKING_SIN_REGLA, "empate 5-5, orden alfabetico"),
        ("ensenar_regla/8", res, "ok(mvc_para_equipos_pequenos)", ""),
        ("ranking con regla", despues, ESPERADO_RANKING_CON_REGLA, "mvc 5 + 3"),
        ("es una clausula con cuerpo (clause/2)",
         q("clause(regla_experta(mvc_para_equipos_pequenos,_,_,_,_), B), B \\== true") is not None, True, ""),
        ("exclusion (\\+) impide el disparo", excl[0][0] != "mvc" or excl[0][1] != 8, True,
         f"con dominio_complejo: {excl}"),
        ("clausula escrita con portray_clause", clausula.strip() in leer_tmp(), True, clausula.strip()),
    ]


@prueba("B2", "razones/3 y explicar_diagnostico/5 incluyen la regla experta")
def b2():
    regla(*REGLA_DEMO)
    d = puente.diagnosticar(CASO_DEMO)
    ex = puente.explicar(CASO_DEMO)
    pasos = [p for p in ex["Reglas"] if p[1] == "regla_experta/5"]
    puntaje = [p[2] for p in ex["Reglas"] if p[1] == "puntaje/3"]
    return [
        ("mejor", d["Mejor"], "mvc", ""),
        ("razones", [r for r in d["Razones"] if r.startswith("Regla experta")],
         ["Regla experta mvc_para_equipos_pequenos: Para equipos pequenos que separan interfaz y logica, "
          "MVC es suficiente (+3)"], ""),
        ("paso regla_experta/5 en el nivel 2", [p[0] for p in pasos], [2], ""),
        ("puntaje/3 muestra el bonus", puntaje, ["puntaje de mvc = 5 - 0 + 3 (reglas expertas) = 8"], ""),
    ]


@prueba("B3", "Efecto 'descartar': descartes, motivo_descarte y que_falta")
def b3():
    caso = ["integracion_sistemas_heredados", "presupuesto_bajo"]
    antes_c = [c[0] for c in puente.candidatos(caso)]
    ef_antes = q("efecto_dato(soa, [integracion_sistemas_heredados], presupuesto_bajo, D, T)")
    res = regla("soa_no_para_presupuesto_bajo", "Un bus empresarial no cabe en un presupuesto bajo",
                "soa", "descartar", 4, ["presupuesto_bajo"], [])
    despues_c = [c[0] for c in puente.candidatos(caso)]
    descs = puente.descartes(caso)
    ef_desp = q("efecto_dato(soa, [integracion_sistemas_heredados], presupuesto_bajo, D, T)")
    expl = puente.explicar(caso)
    return [
        ("soa era candidato", "soa" in antes_c, True, "interoperabilidad 3 - presupuesto 2 = 1"),
        ("resultado", res, "ok(soa_no_para_presupuesto_bajo)", "el peso se ignora en 'descartar' (queda 0)"),
        ("soa ya no es candidato", "soa" in despues_c, False, ""),
        ("descartes", [d for d in descs if d[0] == "soa"],
         [["soa", "regla_experta", "soa_no_para_presupuesto_bajo"]], ""),
        ("que_falta: efecto del dato", (ef_antes["T"], ef_antes["D"], ef_desp["T"], ef_desp["D"]),
         ("resta", -2, "descarta", -5), "peso_exclusion = 5"),
        ("hipotesis descartada", [h[2] for h in expl["Descartadas"] if h[0] == "soa"],
         ["condicion excluyente: regla experta soa_no_para_presupuesto_bajo"], ""),
    ]


@prueba("B4", "Validaciones negativas de ensenar_regla/8 (la base y el archivo no cambian)")
def b4():
    regla(*REGLA_DEMO)
    n_antes, archivo_antes = n_reglas(), leer_tmp()
    casos = [
        ("id duplicado", regla(*REGLA_DEMO), "error(id_duplicado(mvc_para_equipos_pequenos))"),
        ("estilo inexistente", regla("r1", "x", "estilo_que_no_existe", "recomendar", 2, ["equipo_pequeno"], []),
         "error(estilo_desconocido(estilo_que_no_existe))"),
        ("sin condiciones", regla("r2", "x", "mvc", "recomendar", 2, [], ["dominio_complejo"]),
         "error(sin_condiciones)"),
        ("solape condicion/exclusion", regla("r3", "x", "mvc", "recomendar", 2, ["equipo_pequeno"],
                                             ["equipo_pequeno"]), "error(requisito_en_ambas(equipo_pequeno))"),
        ("peso 0", regla("r4", "x", "mvc", "recomendar", 0, ["equipo_pequeno"], []), "error(peso_invalido(0))"),
        ("peso 6", regla("r5", "x", "mvc", "recomendar", 6, ["equipo_pequeno"], []), "error(peso_invalido(6))"),
        ("peso no numerico", regla("r6", "x", "mvc", "recomendar", "alto", ["equipo_pequeno"], []),
         "error(peso_invalido(alto))"),
        ("explicacion vacia", regla("r7", "   ", "mvc", "recomendar", 2, ["equipo_pequeno"], []),
         "error(explicacion_vacia)"),
        ("requisito desconocido", regla("r8", "x", "mvc", "recomendar", 2, ["volar"], []),
         "error(requisito_desconocido(volar))"),
        ("efecto invalido", regla("r9", "x", "mvc", "borrar", 2, ["equipo_pequeno"], []),
         "error(efecto_invalido(borrar))"),
        ("id vacio", regla("  ", "x", "mvc", "recomendar", 2, ["equipo_pequeno"], []), "error(id_invalido)"),
        ("id = requisito", regla("equipo_pequeno", "x", "mvc", "recomendar", 2, ["presupuesto_bajo"], []),
         "error(id_reservado(equipo_pequeno))"),
        ("condiciones contradictorias", regla("r10", "x", "mvc", "recomendar", 2,
                                              ["equipo_pequeno", "equipo_grande"], []),
         "error(condiciones_contradictorias(equipo_pequeno,equipo_grande))"),
        ("regla repetida con otro id", regla("r11", "x", "mvc", "recomendar", 1,
                                             ["separar_interfaz_logica", "equipo_pequeno"], ["dominio_complejo"]),
         "error(regla_repetida(mvc_para_equipos_pequenos))"),
    ]
    filas = [(n, obtenido, esperado, "") for n, obtenido, esperado in casos]
    filas.append(("los errores no agregan reglas", n_reglas(), n_antes, ""))
    filas.append(("el archivo no cambia con errores", leer_tmp() == archivo_antes, True, ""))
    filas.append(("texto Prolog como id: se normaliza, no se ejecuta",
                  regla("x) :- halt, (y", "x", "mvc", "recomendar", 2, ["latencia_critica"], []),
                  "ok(x_halt_y)", "nombre_a_id/2; la clausula se arma con terminos, no con texto"))
    return filas


@prueba("B5", "Regla sobre un estilo aprendido; olvidar el estilo borra sus reglas")
def b5():
    q("ensenar_estilo('Estilo Ligero', '', [[equipo_pequeno, 3]], [], _, _)")
    res = regla("ligero_rapido", "Ligero sirve para entregar rapido", "estilo_ligero", "recomendar", 5,
                ["entrega_rapida"], [])
    pts = dict(top(["equipo_pequeno", "entrega_rapida"], 11)).get("estilo_ligero")
    q("olvidar_estilo(estilo_ligero), guardar_aprendizaje")
    return [("resultado", res, "ok(ligero_rapido)", ""),
            ("puntaje", pts, 8, "simplicidad 3 + bonus 5"),
            ("regla borrada con el estilo", n_reglas(), 0, ""),
            ("archivo sin la regla", "ligero_rapido" in leer_tmp(), False, "")]


# ---------------------------------------------------------------------------
# C. Persistencia con un proceso nuevo
# ---------------------------------------------------------------------------
@prueba("C1", "Regla + sinonimo sobreviven a un PROCESO NUEVO y se eliminan")
def c1():
    regla(*REGLA_DEMO)
    q("ensenar_sinonimo('recursos escasos', presupuesto_bajo, _)")
    h1 = proceso_hijo()
    ok_r = q("olvidar_regla(mvc_para_equipos_pequenos)") is not None
    ok_s = q("olvidar_sinonimo('recursos escasos')") is not None
    h2 = proceso_hijo()
    return [
        ("proceso distinto", h1.get("pid") not in (None, os.getpid()), True, f"pid hijo {h1.get('pid')}"),
        ("hijo 1: regla cargada", h1.get("reglas"), ["mvc_para_equipos_pequenos"], ""),
        ("hijo 1: sinonimo cargado", h1.get("sinonimos"), [["recursos escasos", "presupuesto_bajo", "afirma"]], ""),
        ("hijo 1: ranking cambia por la regla", [tuple(x) for x in h1.get("ranking", [])],
         ESPERADO_RANKING_CON_REGLA, ""),
        ("hijo 1: entiende el sinonimo", h1.get("recursos_escasos"), ["presupuesto_bajo"], ""),
        ("eliminar (retract + reescritura)", (ok_r, ok_s), (True, True), ""),
        ("hijo 2: nada cargado", (h2.get("reglas"), h2.get("sinonimos")), ([], []), ""),
        ("hijo 2: ranking inicial", [tuple(x) for x in h2.get("ranking", [])], ESPERADO_RANKING_SIN_REGLA, ""),
        ("hijo 2: ya no entiende el sinonimo", h2.get("recursos_escasos"), [], ""),
        ("existe la copia .bak", os.path.exists(RUTA_TMP + ".bak"), True, ""),
        ("no quedan .tmp", os.path.exists(RUTA_TMP + ".tmp"), False, "rename_file atomico"),
    ]


@prueba("C2", "Archivo de aprendizaje danado o manipulado: la app arranca igual")
def c2():
    with open(RUTA_TMP, "w", encoding="utf-8") as f:
        f.write("explicacion_regla(r_mala, 'x').\n"
                "regla_experta(r_mala, mvc, recomendar, 3, A) :- halt.\n"            # cuerpo no permitido
                "explicacion_regla(r_peso, 'x').\n"
                "regla_experta(r_peso, mvc, recomendar, 99, A) :- contiene_todos([equipo_pequeno], A).\n"
                "explicacion_regla(r_buena, 'Buena').\n"
                "regla_experta(r_buena, mvc, recomendar, 2, A) :- contiene_todos([equipo_pequeno], A).\n"
                "regla_experta(r_sin_explicacion, mvc, recomendar, 2, A) :- contiene_todos([entrega_rapida], A).\n"
                "lexico_aprendido([hola]).\nlexico([hola], volar, afirma).\n"
                "lexico([equipo, pequeno], presupuesto_bajo, afirma).\n")
    tipo = q(f"cargar_aprendizaje({atomo(RUTA_TMP)}, E), estado_carga(E, T, _)")["T"]
    reglas = [r["id"] for r in puente.reglas_aprendidas()]
    sin = puente.sinonimos_aprendidos()
    pequeno = nl("equipo pequeno")["requisitos"]
    with open(RUTA_TMP, "w", encoding="utf-8") as f:
        f.write("regla_experta(x, mvc, recomendar, 3, A) :- contiene_todos([equipo_pequeno], A\n")
    tipo2 = q(f"cargar_aprendizaje({atomo(RUTA_TMP)}, E), estado_carga(E, T, _)")["T"]
    return [
        ("estado", tipo, "cargado", ""),
        ("solo la regla valida", reglas, ["r_buena"], "cuerpo distinto, peso 99 o sin explicacion se ignoran"),
        ("sinonimos invalidos ignorados", sin, [], "requisito desconocido / lexico sin marca"),
        ("el lexico del experto no se pisa", pequeno, ["equipo_pequeno"], ""),
        ("archivo con error de sintaxis", tipo2, "danado", "se renombra a .danado (aviso existente)"),
        ("la inferencia sigue", puente.diagnosticar(CASO_DEMO)["Mejor"], "monolito_capas", ""),
    ]


@prueba("C3", "limpiar_aprendizaje/1 se niega a borrar el archivo real")
def c3():
    real = RUTA_REAL.replace("\\", "/")
    return [("limpiar_aprendizaje(real) falla", q(f"limpiar_aprendizaje({atomo(real)})"), None, ""),
            ("la ruta activa sigue siendo la temporal", q("ruta_aprendizaje(R)")["R"], RUTA_TMP, "")]


# ---------------------------------------------------------------------------
# D. No regresion
# ---------------------------------------------------------------------------
CASOS_D = [["equipo_pequeno", "presupuesto_bajo", "entrega_rapida"], ["muchos_usuarios", "carga_variable"],
           [], ["procesos_largos", "latencia_critica"], ["equipo_grande", "dominio_complejo"], CASO_DEMO]


def foto(reqs):
    """Todo lo que ve el usuario para un caso. De que_falta se excluyen las
    Sugerencias: una regla que no se dispara SI puede cambiar el efecto
    hipotetico de preguntar por su condicion (eso es correcto)."""
    d = puente.diagnosticar(reqs)
    qf = puente.que_falta(reqs, [])
    return (d["Mejor"], d["Prioridad"], d["Ranking"], d["Razones"], d["Descartados"],
            qf["Estado"], qf["Confianza"], qf["Competencia"],
            puente.candidatos(reqs), puente.descartes(reqs), puente.explicar(reqs))


@prueba("D1", "Una regla que NO se dispara no cambia el dictamen ni la explicacion")
def d1():
    antes = [foto(c) for c in CASOS_D]
    regla("solo_heredados", "x", "soa", "recomendar", 5, ["integracion_sistemas_heredados"], [])
    despues = [foto(c) for c in CASOS_D]
    return [(f"caso {c or '[]'}", a == b, True,
             "diagnostico, estado, competencia, candidatos, descartes y explicacion identicos")
            for c, a, b in zip(CASOS_D, antes, despues)]


@prueba("D2", "pruebas.py (entregable 2) sigue pasando")
def d2():
    r = subprocess.run([sys.executable, os.path.join(CARPETA, "pruebas.py")], capture_output=True,
                       text=True, encoding="utf-8", errors="replace", cwd=CARPETA, timeout=600)
    linea = next((ln for ln in r.stdout.splitlines() if ln.startswith("RESULTADO")), "sin RESULTADO")
    return [("codigo de salida", r.returncode, 0, linea),
            ("0 fallas", linea.endswith(" 0 fallas."), True, "")]


# ---------------------------------------------------------------------------
def estadisticas():
    """Clausulas por archivo (clause_property/2 = archivo de origen real de
    cada clausula), sin lo aprendido."""
    q(f"limpiar_aprendizaje({atomo(RUTA_TMP)})")
    filas = {}
    for archivo in ("base_conocimiento.pl", "lenguaje_natural.pl"):
        r = q("findall(_N/_A-_T, ( predicate_property(user:_H, number_of_clauses(_)),"
              " \\+ predicate_property(user:_H, imported_from(_)), functor(_H, _N, _A),"
              f" clause(user:_H, _B, _R), clause_property(_R, file(_F)), sub_atom(_F, _, _, 0, '{archivo}'),"
              " ( _B == true -> _T = h ; _T = r ) ), _L),"
              " aggregate_all(count, member(_-h, _L), NH), aggregate_all(count, member(_-r, _L), NR),"
              " findall(_X, member(_X-h, _L), _PH0), sort(_PH0, _PH), length(_PH, NPH),"
              " findall(_Y, member(_Y-r, _L), _PR0), sort(_PR0, _PR), length(_PR, NPR),"
              " findall(_Z, member(_Z-_, _L), _PT0), sort(_PT0, _PT), length(_PT, NPT)")
        filas[archivo] = r
    return filas


def main():
    log("=" * 78)
    log("EVIDENCIA DE PRUEBAS - ArquiSelect ENTREGABLE 3 (DCG + Modo Experto + persistencia)")
    log(f"Fecha: {datetime.now():%Y-%m-%d %H:%M:%S}   Python {platform.python_version()}   "
        f"pyswip {metadata.version('pyswip')}   SO {platform.system()} {platform.release()}")
    v = q("current_prolog_flag(version, V)")
    log(f"SWI-Prolog {v['V'] if v else '?'}   Archivo de aprendizaje de pruebas: <temporal>/aprendizaje_pruebas.pl")
    log("=" * 78)

    total = fallos = 0
    for codigo, titulo, func in PRUEBAS:
        inicio = q(f"limpiar_aprendizaje({atomo(RUTA_TMP)})")      # cada prueba parte de cero
        log("")
        log(f"[{codigo}] {titulo}")
        if inicio is None:
            total += 1
            fallos += 1
            log("   FALLA  limpiar_aprendizaje/1 no tuvo exito")
            continue
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

    real_despues = (os.path.exists(RUTA_REAL), os.path.getmtime(RUTA_REAL) if os.path.exists(RUTA_REAL) else None)
    total += 1
    ok_real = real_despues == REAL_ANTES
    fallos += not ok_real
    log("")
    log(f"[Z] {'OK   ' if ok_real else 'FALLA'}  conocimiento_aprendido.pl real intacto durante las pruebas")

    e = estadisticas()
    log("")
    log("=" * 78)
    log(f"RESULTADO: {total - fallos}/{total} verificaciones correctas, {fallos} fallas.")
    log("")
    log("TAMANO DE LA BASE (sin lo aprendido; cada clausula contada en su archivo de origen):")
    for archivo, r in e.items():
        log(f"   {archivo}:")
        log(f"      hechos (clausulas sin cuerpo) ... {r['NH']}  en {r['NPH']} predicados")
        log(f"      reglas (clausulas con cuerpo) ... {r['NR']}  en {r['NPR']} predicados")
        log(f"      predicados distintos ............ {r['NPT']}")
    th = sum(r["NH"] for r in e.values())
    tr = sum(r["NR"] for r in e.values())
    log(f"   TOTAL: {th} hechos + {tr} reglas = {th + tr} clausulas")

    with open(RUTA_EVIDENCIA, "w", encoding="utf-8") as f:
        f.write("\n".join(salida).replace(TMP.replace("\\", "/"), "<temporal>").replace(TMP, "<temporal>") + "\n")
    shutil.rmtree(TMP, ignore_errors=True)
    print(f"\nEvidencia escrita en {RUTA_EVIDENCIA}")
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
