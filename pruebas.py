"""
pruebas.py - Pruebas automaticas de ArquiSelect (base de 11 estilos +
aprendizaje en caliente).

    python pruebas.py      -> imprime el resultado y regenera evidencia_pruebas.txt

Reglas de las pruebas:
- Cada prueba llama antes a olvidar_aprendizaje/0, asi el resultado no depende
  de lo que el usuario haya ensenado desde la app.
- Nunca se escribe el conocimiento_aprendido.pl real: la persistencia se prueba
  con guardar_aprendizaje/1 y cargar_aprendizaje/2 en una carpeta temporal.
- Toda la logica la resuelve Prolog; aqui solo se consulta y se compara.

Cada esperado lleva su justificacion (puntajes hechos a mano a partir de
aporta/3 y penaliza/3). Al final de evidencia_pruebas.txt se listan los
esperados que cambiaron al pasar de 5 a 11 estilos y por que.
"""
import os
import sys
import shutil
import tempfile
import platform
from datetime import datetime
from importlib import metadata

from main import PuenteProlog, RUTA_BASE_CONOCIMIENTO, atomo, lista_prolog, lista_pares_prolog

RUTA_EVIDENCIA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "evidencia_pruebas.txt")

puente = PuenteProlog(RUTA_BASE_CONOCIMIENTO)
TMP = tempfile.mkdtemp(prefix="arquiselect_pruebas_")

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


# ---------------------------------------------------------------------------
# Ayudas de consulta (solo leen lo que responde Prolog)
# ---------------------------------------------------------------------------
def q(meta):
    """Primera solucion de una meta o None."""
    return puente.una_solucion("prueba", meta)


def diag(reqs):
    return puente.diagnosticar(reqs)


def ranking(reqs):
    return [(e, p) for e, p, _pr, _ri in diag(reqs)["Ranking"]]


def puntajes(reqs):
    return dict(ranking(reqs))


def estado(reqs, negados=()):
    return puente.que_falta(reqs, negados)


def ensenar(nombre, favorece, incompatibles=(), descripcion=""):
    """Llama ensenar_estilo/6 y devuelve (Resultado como texto, Advertencias)."""
    r = q(f"ensenar_estilo({atomo(nombre)}, {atomo(descripcion)}, "
          f"{lista_pares_prolog(favorece)}, {lista_prolog(incompatibles)}, R, Adv), "
          "term_to_atom(R, Txt)")
    return r["Txt"], r["Adv"]


def ids_estilos():
    return set(puente.estilos())


# ---------------------------------------------------------------------------
# A. Casos de la guia (README) recalculados con 11 estilos
# ---------------------------------------------------------------------------
CASO1 = ["equipo_pequeno", "presupuesto_bajo", "entrega_rapida"]
CASO2 = ["muchos_usuarios", "carga_variable"]


@prueba("A1", "Caso 1 de la guia: equipo pequeno + presupuesto bajo + entrega rapida")
def a1():
    d, f = diag(CASO1), estado(CASO1)
    return [
        ("mejor estilo", d["Mejor"], "monolito_capas",
         "atributos simplicidad, bajo_costo, rapidez_desarrollo: capas 3+3+3 = 9 (sin cambios)"),
        ("prioridad", d["Prioridad"], "alta", "9 >= umbral alta 8"),
        ("estado", f["Estado"], "definitivo", "margen 9 - 7 = 2 >= umbral_desempate 2"),
        ("ranking (5 primeros)", ranking(CASO1)[:5],
         [("monolito_capas", 9), ("monolito_modular", 7), ("mvc", 7),
          ("cliente_servidor", 6), ("serverless", 6)],
         "CAMBIO: entran mvc 2+2+3 = 7 y cliente_servidor 2+2+2 = 6; empates por orden alfabetico de setof"),
        ("hipotesis en competencia", f["Competencia"], ["monolito_capas", "monolito_modular", "mvc"],
         "CAMBIO: max_competidores = 3 y mvc (7) desplaza a serverless (6)"),
        ("primera pregunta sugerida", f["Sugerencias"][0][:2], ["despliegue_independiente", 5],
         "CAMBIO: antes latencia_critica (poder 7) porque descartaba a serverless; ahora serverless ya "
         "no compite y latencia solo da capas +2, modular +2, mvc 0 (poder 2). despliegue_independiente: "
         "capas descartado (-5), modular -2, mvc 0 -> poder 0 - (-5) = 5"),
        ("microservicios descartado", ["microservicios", "exclusion", "equipo_pequeno"] in puente.descartes(CASO1),
         True, "incompatible(microservicios, equipo_pequeno)"),
    ]


@prueba("A2", "Caso 2 de la guia: muchos usuarios + carga variable (empate)")
def a2():
    f = estado(CASO2)
    return [
        ("ranking (3 primeros)", ranking(CASO2)[:3],
         [("serverless", 6), ("microservicios", 5), ("eventos", 4)],
         "serverless 3+3, microservicios 3+2, eventos 2+2 (sin cambios)"),
        ("puntaje soa", puntajes(CASO2).get("soa"), 2, "NUEVO: soa aporta escalabilidad 2"),
        ("estado", f["Estado"], "empate", "margen 6 - 5 = 1 < 2"),
        ("competencia", f["Competencia"], ["serverless", "microservicios"], "a menos de 2 puntos del lider"),
        ("primera pregunta", f["Sugerencias"][0][:2], ["equipo_pequeno", 7],
         "serverless +2 (simplicidad), microservicios descartado (-5): poder 7 (sin cambios)"),
    ]


@prueba("A3", "Caso 2 + responder SI a equipo pequeno")
def a3():
    reqs = CASO2 + ["equipo_pequeno"]
    d, f = diag(reqs), estado(reqs)
    return [
        ("mejor", (d["Mejor"], puntajes(reqs)[d["Mejor"]]), ("serverless", 8), "3+3+2 = 8 (sin cambios)"),
        ("estado", f["Estado"], "definitivo", "8 contra eventos 3"),
    ]


@prueba("A4", "Evaluacion vacia")
def a4():
    d, f = diag([]), estado([])
    descs = puente.descartes([])
    return [
        ("mejor (fallback)", (d["Mejor"], d["Prioridad"]), ("monolito_modular", "por_defecto"),
         "mejor_estilo/3 por defecto (sin cambios)"),
        ("estado", f["Estado"], "vacio", ""),
        ("descartes sin_evidencia", len(descs), 11,
         "CAMBIO: antes 5; ahora los 11 estilos salen como sin_evidencia con puntaje 0"),
    ]


@prueba("A5", "Un solo requisito: evidencia insuficiente")
def a5():
    reqs = ["muchos_usuarios"]
    return [
        ("estado", estado(reqs)["Estado"], "insuficiente", "suficiencia/2 con 1 requisito"),
        ("mejor", diag(reqs)["Mejor"], "microservicios",
         "empate 3-3 con serverless, gana por orden alfabetico (sin cambios)"),
    ]


@prueba("A6", "Plantilla alta demanda")
def a6():
    reqs = ["muchos_usuarios", "disponibilidad_alta"]
    return [
        ("perfil", diag(reqs)["Perfil"], "alta_demanda", ""),
        ("mejor", ranking(reqs)[0], ("microservicios", 6), "escalabilidad 3 + disponibilidad 3 (sin cambios)"),
        ("estado", estado(reqs)["Estado"], "definitivo", "6 contra eventos 4"),
    ]


@prueba("A7", "Plantilla empresarial (equipo grande + dominio complejo)")
def a7():
    reqs = ["equipo_grande", "dominio_complejo"]
    return [
        ("perfil", diag(reqs)["Perfil"], "empresarial", ""),
        ("ranking (3 primeros)", ranking(reqs)[:3],
         [("clean", 3), ("microservicios", 3), ("monolito_modular", 3)],
         "CAMBIO: los dos requisitos exigen el MISMO atributo (modularidad) y clean tambien lo da con 3; "
         "triple empate a 3 que setof ordena alfabeticamente, asi clean queda primero (antes microservicios)"),
        ("mejor", diag(reqs)["Mejor"], "clean", "CAMBIO: ver fila anterior; no es una ventaja por evidencia"),
        ("estado", estado(reqs)["Estado"], "insuficiente", "3 < umbral media 4 (sin cambios)"),
    ]


@prueba("A8", "Exclusiones duras: procesos largos + latencia critica")
def a8():
    descs = puente.descartes(["procesos_largos", "latencia_critica"])
    return [
        ("serverless excluido", ["serverless", "exclusion", "procesos_largos"] in descs, True,
         "primer motivo de incompatible/2"),
        ("soa excluido", ["soa", "exclusion", "latencia_critica"] in descs, True,
         "NUEVO: incompatible(soa, latencia_critica)"),
    ]


@prueba("A9", "Entrada sucia: mayusculas, repetidos y requisito desconocido")
def a9():
    d = diag(["Equipo_Pequeno", "xyz", "equipo_pequeno"])
    return [
        ("desconocidos", d["Desconocidos"], ["xyz"], "validar_entrada/2 + desconocidos/2"),
        ("mejor", d["Mejor"], "monolito_capas", "simplicidad: capas 3 contra 2 de los demas"),
        ("suficiencia", d["Suficiencia"], "insuficiente", "un solo requisito valido tras quitar repetidos"),
    ]


@prueba("A10", "candidatos + descartes cubren los 11 estilos sin repetir")
def a10():
    filas = []
    for reqs in (CASO1, CASO2, [], ["procesos_largos", "latencia_critica"]):
        cands = [c[0] for c in puente.candidatos(reqs)]
        descs = [x[0] for x in puente.descartes(reqs)]
        todos = cands + descs
        filas.append((f"{reqs or '[]'}", (len(todos), sorted(set(todos)) == sorted(ids_estilos())),
                      (11, True), "particion exacta de estilo/2"))
    return filas


# ---------------------------------------------------------------------------
# B. Cada estilo nuevo gana en un escenario razonable
# ---------------------------------------------------------------------------
def caso_gana(reqs, ganador, puntos, segundo, estado_esp, calculo):
    rk = ranking(reqs)
    return [
        ("ganador", rk[0], (ganador, puntos), calculo),
        ("segundo", rk[1], segundo, ""),
        ("estado", estado(reqs)["Estado"], estado_esp, "umbral_desempate = 2"),
    ]


@prueba("B1", "clean: mantenibilidad + testabilidad + independencia tecnologica + dominio complejo")
def b1():
    return caso_gana(["mantenibilidad_largo_plazo", "testabilidad_alta", "independencia_tecnologica",
                      "dominio_complejo"], "clean", 12, ("hexagonal", 10), "definitivo",
                     "clean 3+3+3+3 = 12; hexagonal 2+3+3+2 = 10; onion 3+3+2+2 = 10")


@prueba("B1b", "clean sin dominio complejo: gana pero en empate tecnico")
def b1b():
    return caso_gana(["mantenibilidad_largo_plazo", "testabilidad_alta", "independencia_tecnologica"],
                     "clean", 9, ("hexagonal", 8), "empate",
                     "clean 3+3+3 = 9; hexagonal 2+3+3 = 8 y onion 3+3+2 = 8 -> margen 1")


@prueba("B2", "onion: mantenibilidad + testabilidad + consistencia estricta")
def b2():
    return caso_gana(["mantenibilidad_largo_plazo", "testabilidad_alta", "consistencia_estricta"],
                     "onion", 8, ("clean", 6), "definitivo",
                     "onion 3+3+2 = 8; clean 3+3+0 = 6 (clean no aporta consistencia); eventos excluido")


@prueba("B3", "hexagonal: testabilidad + independencia tecnologica + mensajes + presupuesto bajo")
def b3():
    return caso_gana(["testabilidad_alta", "independencia_tecnologica", "integracion_asincrona",
                      "presupuesto_bajo"], "hexagonal", 9, ("clean", 7), "definitivo",
                     "hexagonal 3+3+3 = 9 sin penalizacion; clean 3+3+2 - 1 (presupuesto_bajo) = 7")


@prueba("B4", "soa: integrar heredados + mensajes + despliegue independiente")
def b4():
    return caso_gana(["integracion_sistemas_heredados", "integracion_asincrona", "despliegue_independiente"],
                     "soa", 7, ("eventos", 5), "definitivo",
                     "soa 3+2+2 = 7; eventos 2+3 = 5; microservicios 2+3 = 5; capas y cliente_servidor excluidos")


@prueba("B5", "cliente_servidor: datos centralizados + consistencia estricta")
def b5():
    filas = caso_gana(["datos_centralizados", "consistencia_estricta"], "cliente_servidor", 6,
                      ("monolito_capas", 5), "empate",
                      "cliente_servidor 3+3 = 6; monolito_capas 2+3 = 5")
    filas.append(("con presupuesto bajo (tal como se pidio)",
                  ranking(["datos_centralizados", "presupuesto_bajo"])[:2],
                  [("cliente_servidor", 5), ("monolito_capas", 5)],
                  "LIMITACION de los pesos propuestos: 3+2 = 5 contra 2+3 = 5, gana solo por orden alfabetico"))
    return filas


@prueba("B6", "mvc: separar interfaz y logica + entrega rapida")
def b6():
    filas = caso_gana(["separar_interfaz_logica", "entrega_rapida"], "mvc", 6, ("monolito_capas", 5),
                      "empate", "mvc 3+3 = 6; monolito_capas 2+3 = 5")
    reqs = ["separar_interfaz_logica", "entrega_rapida", "disponibilidad_alta"]
    filas.append(("con alta disponibilidad", (ranking(reqs)[0], estado(reqs)["Estado"]),
                  (("mvc", 6), "definitivo"),
                  "capas 5 - 2 = 3 y modular 4 - 1 = 3 son penalizados; mvc no"))
    return filas


# ---------------------------------------------------------------------------
# C. Aprendizaje en caliente
# ---------------------------------------------------------------------------
ENTRADA_C = ["latencia_critica", "disponibilidad_alta", "muchos_usuarios"]
FAV_C = [("latencia_critica", 3), ("disponibilidad_alta", 3), ("muchos_usuarios", 3)]


@prueba("C1", "Antes y despues de ensenar_estilo con la misma entrada")
def c1():
    antes = ranking(ENTRADA_C)
    txt, adv = ensenar("Mi arquitectura de prueba", FAV_C)
    despues = ranking(ENTRADA_C)
    return [
        ("antes: no aparece", any(e == "mi_arquitectura_de_prueba" for e, _ in antes), False, ""),
        ("resultado", txt, "ok(mi_arquitectura_de_prueba,[])", "id derivado del nombre"),
        ("advertencias", adv, [], "3 de 20 requisitos (15 %) < 70 %"),
        ("despues: primero del ranking", despues[0], ("mi_arquitectura_de_prueba", 9),
         "rendimiento 3 + disponibilidad 3 + escalabilidad 3 = 9"),
        ("lider anterior sigue en el ranking", antes[0] in despues, True,
         f"{antes[0]} no cambia su puntaje"),
        ("aparece en estilos_disponibles", "mi_arquitectura_de_prueba" in ids_estilos(), True, ""),
        ("aparece en candidatos", "mi_arquitectura_de_prueba" in [c[0] for c in puente.candidatos(ENTRADA_C)],
         True, ""),
    ]


@prueba("C2", "que_falta recalcula competencia y poder de desempate")
def c2():
    reqs = ["latencia_critica", "disponibilidad_alta"]
    antes = estado(reqs)
    ensenar("Mi arquitectura de prueba", FAV_C)
    despues = estado(reqs)
    sugs_despues = {s[0]: s[1] for s in despues["Sugerencias"]}
    efectos = [e[0] for s in despues["Sugerencias"] for e in s[3]]
    return [
        ("competencia antes", "mi_arquitectura_de_prueba" in antes["Competencia"], False, ""),
        ("competencia despues", despues["Competencia"][0], "mi_arquitectura_de_prueba",
         "rendimiento 3 + disponibilidad 3 = 6, lidera"),
        ("las sugerencias cambian", antes["Sugerencias"] != despues["Sugerencias"], True,
         "el estilo nuevo compite y cambia el poder de cada pregunta"),
        ("muchos_usuarios ya no se pregunta con el mismo poder",
         sugs_despues.get("muchos_usuarios"), None,
         "ahora la mayoria de competidores suben juntos con escalabilidad; deja el top 3"),
        ("efectos incluyen el estilo nuevo", "mi_arquitectura_de_prueba" in efectos, True, ""),
    ]


@prueba("C3", "Requisitos sin atributo se ignoran en Favorece y se informan")
def c3():
    txt, _ = ensenar("Estilo con procesos", [("procesos_largos", 2), ("equipo_pequeno", 3)])
    m = q("mensaje_resultado(ok(estilo_con_procesos,[procesos_largos]), M)")["M"]
    return [
        ("resultado", txt, "ok(estilo_con_procesos,[procesos_largos])", "procesos_largos no tiene requisito_atributo/2"),
        ("aporta creados", q("findall(_A-_P, aporta(estilo_con_procesos, _A, _P), _L), term_to_atom(_L, T)")["T"],
         "[simplicidad-3]", "solo equipo_pequeno -> simplicidad"),
        ("mensaje lo informa", "Procesos largos" in m, True, m),
    ]


@prueba("C4", "Incompatible se traduce a incompatible/2 y descarta")
def c4():
    ensenar("Estilo caro", [("disponibilidad_alta", 3)], incompatibles=["presupuesto_bajo"])
    descs = puente.descartes(["disponibilidad_alta", "presupuesto_bajo"])
    return [("descartado por presupuesto_bajo", ["estilo_caro", "exclusion", "presupuesto_bajo"] in descs,
             True, "incompatible(estilo_caro, presupuesto_bajo)")]


@prueba("C5", "Advertencia de estilo demasiado general (> 70 %)")
def c5():
    reqs = [r["id"] for r in puente.requisitos_disponibles()]
    _, adv14 = ensenar("General catorce", [(r, 1) for r in reqs[:14]])
    _, adv15 = ensenar("General quince", [(r, 1) for r in reqs[:15]])
    txt_todos, adv20 = ensenar("General todos", [(r, 2) for r in reqs])
    return [
        ("total de requisitos", len(reqs), 20, "14 originales + 6 nuevos"),
        ("14 de 20 (70 %)", adv14, [], "70 % no supera el umbral"),
        ("15 de 20 (75 %)", len(adv15), 1, "75 % > 70 %"),
        ("20 de 20 se guarda igual", txt_todos.startswith("ok(general_todos"), True,
         "la advertencia no impide guardar"),
        ("texto", "demasiado general" in adv20[0], True, adv20[0]),
    ]


@prueba("C6", "Nombre con tildes y enie (pyswip en Windows)")
def c6():
    txt, _ = ensenar("  Arquitectura Ñandú-Café  ", [("equipo_pequeno", 2)])
    nombre = puente.estilos().get("arquitectura_nandu_cafe", ("?",))[0]
    return [
        ("id ASCII", txt, "ok(arquitectura_nandu_cafe,[])", "minusculas, sin tildes, guion a _"),
        ("nombre conserva tildes", nombre, "Arquitectura Ñandú-Café", "ida y vuelta por pyswip sin perdidas"),
    ]


@prueba("C7", "Dos requisitos con el mismo atributo -> un aporta/3 con el peso mayor")
def c7():
    ensenar("Estilo modular", [("equipo_grande", 1), ("dominio_complejo", 3)])
    return [("aporta", q("findall(_A-_P, aporta(estilo_modular, _A, _P), _L), term_to_atom(_L, T)")["T"],
             "[modularidad-3]", "aporte_total/3 cuenta cada atributo una vez")]


# ---------------------------------------------------------------------------
# D. Errores de validacion (Prolog responde error(Motivo) y no toca la base)
# ---------------------------------------------------------------------------
@prueba("D1", "Errores de validacion")
def d1():
    ensenar("Mi arquitectura de prueba", FAV_C)
    n_antes = len(ids_estilos())
    casos = [
        ("nombre duplicado (aprendido)", ensenar("Mi Arquitectura de  PRUEBA", FAV_C)[0],
         "error(nombre_duplicado(mi_arquitectura_de_prueba))", "mismo id derivado"),
        ("nombre duplicado (experto)", ensenar("Microservicios", FAV_C)[0],
         "error(nombre_duplicado(microservicios))", "no se puede pisar un estilo del experto"),
        ("sin requisitos", ensenar("Vacia", [])[0], "error(sin_requisitos)", ""),
        ("mismo requisito en ambas columnas",
         ensenar("Ambas", [("equipo_pequeno", 2)], incompatibles=["equipo_pequeno"])[0],
         "error(requisito_en_ambas(equipo_pequeno))", ""),
        ("nombre vacio", ensenar("   ", [("equipo_pequeno", 2)])[0], "error(nombre_vacio)", ""),
        ("nombre solo simbolos", ensenar("!!!", [("equipo_pequeno", 2)])[0], "error(nombre_invalido)", ""),
        ("peso fuera de rango", ensenar("Pesada", [("equipo_pequeno", 4)])[0],
         "error(peso_invalido(equipo_pequeno,4))", "pesos 1..3"),
        ("requisito desconocido", ensenar("Rara", [("volar", 2)])[0],
         "error(requisito_desconocido(volar))", ""),
        ("solo requisitos sin atributo", ensenar("Larga", [("procesos_largos", 2)])[0],
         "error(sin_requisitos_utiles([procesos_largos]))", ""),
    ]
    casos.append(("los errores no agregan estilos", len(ids_estilos()), n_antes, ""))
    return casos


# ---------------------------------------------------------------------------
# E. Olvidar
# ---------------------------------------------------------------------------
@prueba("E1", "olvidar_estilo quita el estilo aprendido de todo el razonamiento")
def e1():
    ensenar("Mi arquitectura de prueba", FAV_C)
    antes = ranking(ENTRADA_C)[0][0]
    ok = puente.olvidar_estilo("mi_arquitectura_de_prueba")
    return [
        ("antes lideraba", antes, "mi_arquitectura_de_prueba", ""),
        ("olvidar_estilo tuvo exito", ok, True, ""),
        ("ya no esta en el ranking", "mi_arquitectura_de_prueba" in dict(ranking(ENTRADA_C)), False, ""),
        ("no quedan hechos", q("aggregate_all(count, ( aporta(mi_arquitectura_de_prueba,_,_) ; "
                               "estilo(mi_arquitectura_de_prueba,_) ; estilo_aprendido(mi_arquitectura_de_prueba) ), N)")["N"],
         0, ""),
        ("vuelven los 11 estilos", len(ids_estilos()), 11, ""),
    ]


@prueba("E2", "olvidar_estilo nunca borra un estilo del experto")
def e2():
    return [
        ("olvidar microservicios falla", puente.olvidar_estilo("microservicios"), False,
         "solo pasa la marca estilo_aprendido/1"),
        ("microservicios sigue", "microservicios" in ids_estilos(), True, ""),
        ("olvidar inexistente falla", puente.olvidar_estilo("no_existe"), False, ""),
    ]


@prueba("E3", "olvidar_aprendizaje borra todo lo aprendido")
def e3():
    ensenar("Uno", [("equipo_pequeno", 2)])
    ensenar("Dos", [("equipo_grande", 2)])
    con = len(ids_estilos())
    q("olvidar_aprendizaje")
    return [("con 2 aprendidos", con, 13, ""), ("despues", len(ids_estilos()), 11, ""),
            ("estilos_aprendidos", puente.estilos_aprendidos(), [], "")]


# ---------------------------------------------------------------------------
# F. Persistencia (siempre en carpeta temporal)
# ---------------------------------------------------------------------------
def ruta_tmp(nombre):
    return os.path.join(TMP, nombre).replace("\\", "/")


def cargar(ruta):
    r = q(f"cargar_aprendizaje({atomo(ruta)}, E), estado_carga(E, Tipo, Detalle)")
    return r["Tipo"], r["Detalle"]


@prueba("F1", "guardar_aprendizaje/1 + cargar_aprendizaje/2 (ida y vuelta)")
def f1():
    ruta = ruta_tmp("ida_vuelta.pl")
    ensenar("Arquitectura Ñandú", FAV_C, incompatibles=["presupuesto_bajo"], descripcion="Prueba con tildes: café")
    antes = puntajes(ENTRADA_C)
    q(f"guardar_aprendizaje({atomo(ruta)})")
    q("olvidar_aprendizaje")
    sin = "arquitectura_nandu" in ids_estilos()
    tipo = cargar(ruta)
    return [
        ("se olvido en memoria", sin, False, ""),
        ("estado de carga", tipo, ("cargado", 1), ""),
        ("mismos puntajes", puntajes(ENTRADA_C), antes, "aporta/3 recuperados"),
        ("descripcion con tildes", puente.estilos()["arquitectura_nandu"][1], "Prueba con tildes: café", ""),
        ("incompatible recuperado", ["arquitectura_nandu", "exclusion", "presupuesto_bajo"]
         in puente.descartes(["presupuesto_bajo"]), True, ""),
    ]


@prueba("F2", "Cargar dos veces y reconsultar la base no duplica hechos")
def f2():
    ruta = ruta_tmp("doble.pl")
    ensenar("Mi arquitectura de prueba", FAV_C)
    q(f"guardar_aprendizaje({atomo(ruta)})")
    cargar(ruta)
    cargar(ruta)
    puente.prolog.consult(puente.ruta)          # lo mismo que hace recargar()
    cargar(ruta)
    return [
        ("estilo/2", q("aggregate_all(count, estilo(mi_arquitectura_de_prueba,_), N)")["N"], 1, ""),
        ("aporta/3", q("aggregate_all(count, aporta(mi_arquitectura_de_prueba,_,_), N)")["N"], 3, ""),
        ("estilos del experto intactos", len(ids_estilos()), 12, "11 + 1 aprendido"),
    ]


@prueba("F3", "Archivo inexistente o danado: la base arranca igual")
def f3():
    tipo_sin = cargar(ruta_tmp("no_existe.pl"))
    danado = ruta_tmp("danado.pl")
    with open(danado, "w", encoding="utf-8") as f:
        f.write("estilo_aprendido(x).\nestilo(x, 'sin cerrar.\naporta(x,, 3).\n")
    tipo, respaldo = cargar(danado)
    return [
        ("sin archivo", tipo_sin, ("sin_archivo", 0), ""),
        ("danado", tipo, "danado", "error de sintaxis atrapado con catch/3"),
        ("respaldo creado", os.path.exists(respaldo) and not os.path.exists(danado), True, respaldo),
        ("quedan los 11 estilos", len(ids_estilos()), 11, ""),
        ("la inferencia funciona", diag(CASO1)["Mejor"], "monolito_capas", ""),
    ]


@prueba("F4", "Archivo editado a mano: solo se aceptan hechos validos de estilos aprendidos")
def f4():
    ruta = ruta_tmp("manipulado.pl")
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(":- halt.\n"
                "estilo_aprendido(microservicios).\naporta(microservicios, rendimiento, 3).\n"
                "estilo_aprendido(bueno).\nestilo(bueno, 'Bueno').\naporta(bueno, simplicidad, 2).\n"
                "aporta(bueno, rendimiento, 9).\nincompatible(bueno, volar).\n"
                "puntaje(_, _, 100).\n")
    tipo = cargar(ruta)
    return [
        ("estado", tipo, ("cargado", 1), "solo 'bueno'; la directiva y puntaje/3 se ignoran"),
        ("microservicios intacto", q("aggregate_all(count, aporta(microservicios, rendimiento, _), N)")["N"], 0, ""),
        ("peso invalido ignorado", q("findall(_A-_P, aporta(bueno,_A,_P), _L), term_to_atom(_L, T)")["T"],
         "[simplicidad-2]", ""),
        ("requisito desconocido ignorado", q("aggregate_all(count, incompatible(bueno,_), N)")["N"], 0, ""),
    ]


# ---------------------------------------------------------------------------
# Estadisticas de la base (para la ficha del proyecto)
# ---------------------------------------------------------------------------
def estadisticas_base():
    """Cuenta clausulas de base_conocimiento.pl: hecho = cuerpo true, regla = con cuerpo.
    directorio_base/1 cuenta como hecho (lo agrega la directiva de carga)."""
    q("olvidar_aprendizaje")
    # Variables internas con "_" para que pyswip no las devuelva sin ligar.
    r = q("findall(_P-_T, ( source_file(_H, _F), sub_atom(_F, _, _, 0, 'base_conocimiento.pl'),"
          " functor(_H, _N, _Ar), _P = _N/_Ar, clause(_H, _B),"
          " ( _B == true -> _T = h ; _T = r ) ), _L),"
          " aggregate_all(count, member(_-h, _L), NH),"
          " aggregate_all(count, member(_-r, _L), NR),"
          " findall(_X, member(_X-h, _L), _PH0), sort(_PH0, _PH), length(_PH, NPH),"
          " findall(_Y, member(_Y-r, _L), _PR0), sort(_PR0, _PR), length(_PR, NPR),"
          " findall(_Z, member(_Z-_, _L), _PT0), sort(_PT0, _PT), length(_PT, NPT)")
    return r


# ---------------------------------------------------------------------------
CAMBIOS = [
    "A1 (caso 1): mismo dictamen (monolito_capas 9, definitivo). Cambian el ranking (entran mvc 7 y "
    "cliente_servidor 6), la competencia (mvc reemplaza a serverless por max_competidores = 3) y la "
    "primera pregunta: antes latencia_critica (poder 7), ahora despliegue_independiente (poder 5).",
    "A2/A3/A5/A6: mismo dictamen, mismo estado y misma primera pregunta; solo aparece soa en el ranking "
    "con puntajes bajos (escalabilidad 2 / disponibilidad 1).",
    "A4 (vacio): descartes pasa de 5 a 11 estilos sin evidencia.",
    "A7 (empresarial): CAMBIA el estilo recomendado de microservicios a clean. No es por evidencia: "
    "equipo_grande y dominio_complejo exigen el mismo atributo (modularidad) y clean, microservicios y "
    "monolito_modular lo aportan con 3; setof ordena el triple empate alfabeticamente. El estado sigue "
    "siendo 'insuficiente', asi que la interfaz lo presenta como tentativo.",
    "A8: soa tambien aparece descartado por latencia_critica (nuevo incompatible/2).",
    "B5: con los pesos propuestos cliente_servidor solo supera a monolito_capas por centralizacion_datos "
    "(3 contra 2), asi que su mejor escenario termina en empate tecnico; con datos_centralizados + "
    "presupuesto_bajo empatan 5-5 y gana solo por orden alfabetico. Si se quiere un dictamen definitivo "
    "hay que ajustar pesos (p. ej. bajar monolito_capas/centralizacion_datos a 1).",
]


def main():
    log("=" * 78)
    log("EVIDENCIA DE PRUEBAS - ArquiSelect (11 estilos + aprendizaje en caliente)")
    log(f"Fecha: {datetime.now():%Y-%m-%d %H:%M:%S}   Python {platform.python_version()}   "
        f"pyswip {metadata.version('pyswip')}   SO {platform.system()} {platform.release()}")
    v = q("current_prolog_flag(version, V)")
    log(f"SWI-Prolog {v['V'] if v else '?'}   Carpeta temporal de persistencia: {TMP}")
    log("=" * 78)

    total = fallos = 0
    for codigo, titulo, func in PRUEBAS:
        q("olvidar_aprendizaje")                     # cada prueba parte de la base del experto
        log("")
        log(f"[{codigo}] {titulo}")
        try:
            filas = func()
        except Exception as error:                   # una excepcion cuenta como fallo
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
    q("olvidar_aprendizaje")

    e = estadisticas_base()
    log("")
    log("=" * 78)
    log(f"RESULTADO: {total - fallos}/{total} verificaciones correctas, {fallos} fallas.")
    log("")
    log("TAMANO DE LA BASE (base_conocimiento.pl, sin lo aprendido):")
    log(f"   hechos (clausulas sin cuerpo) ........ {e['NH']}  en {e['NPH']} predicados")
    log(f"   reglas (clausulas con cuerpo) ........ {e['NR']}  en {e['NPR']} predicados")
    log(f"   predicados distintos ................. {e['NPT']}")
    log("")
    log("CAMBIOS EN LOS ESPERADOS AL PASAR DE 5 A 11 ESTILOS:")
    for c in CAMBIOS:
        log(f" - {c}")

    with open(RUTA_EVIDENCIA, "w", encoding="utf-8") as f:
        f.write("\n".join(salida).replace(TMP, "<carpeta temporal>") + "\n")
    shutil.rmtree(TMP, ignore_errors=True)
    print(f"\nEvidencia escrita en {RUTA_EVIDENCIA}")
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
