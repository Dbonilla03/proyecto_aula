"""
motor.py - Puente Python <-> SWI-Prolog para ArquiSelect.

RESPONSABILIDAD ESTRICTA: este modulo NO contiene logica de inferencia.
Solo (1) carga base_conocimiento.pl, (2) arma la consulta con los datos de
entrada, (3) invoca el predicado de Prolog y (4) devuelve/presenta lo que
Prolog respondio. Validacion, descarte, listas y severidad viven en Prolog.
"""
import os
from pyswip import Prolog

# atomo/lista_prolog viven en main.py: una sola implementación para ambos puentes
from main import lista_prolog

RUTA_BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "base_conocimiento.pl")


class MotorInferencia:
    """Carga la base de conocimiento y expone consultas hacia Prolog."""

    def __init__(self, ruta=RUTA_BASE):
        self.prolog = Prolog()
        self.prolog.consult(ruta.replace("\\", "/"))

    def consultar(self, meta):
        """Ejecuta una meta Prolog completa y devuelve la lista de soluciones.
        Se usa list(...) para consumir el generador de pyswip y liberar la
        consulta (si no, SWI-Prolog queda con la consulta abierta)."""
        return list(self.prolog.query(meta))

    def diagnosticar(self, requisitos):
        """Invoca diagnosticar_arquitectura/9 y devuelve un dict con las salidas.
        Nunca lanza excepcion por lista vacia: Prolog aplica su valor por defecto."""
        soluciones = self.consultar(f"once({self.meta_diagnostico(requisitos)})")
        if not soluciones:
            return None
        return soluciones[0]

    def meta_diagnostico(self, requisitos):
        """Devuelve la consulta Prolog usada (para documentarla en pruebas)."""
        return (f"diagnosticar_arquitectura({lista_prolog(requisitos)}, "
                "Mejor, Prioridad, Ranking, Descartados, Razones, Perfil, "
                "Desconocidos, Suficiencia)")


def mostrar_resultado(r):
    """Presenta en consola lo que respondio Prolog (solo formato de salida)."""
    if r is None:
        print("  Prolog no devolvio solucion.")
        return
    print(f"  Perfil detectado   : {r['Perfil']}")
    print(f"  Suficiencia datos  : {r['Suficiencia']}")
    if r["Desconocidos"]:
        print(f"  Requisitos ignorados (no reconocidos): {list(r['Desconocidos'])}")
    print(f"  RECOMENDACION      : {r['Mejor']}  (prioridad: {r['Prioridad']})")
    if r["Ranking"]:
        print("  Ranking (estilo | puntaje | prioridad | riesgo):")
        for estilo, puntaje, prioridad, riesgo in r["Ranking"]:
            print(f"    - {estilo:<18} {puntaje:>3}   {prioridad:<6} {riesgo}")
    if r["Descartados"]:
        print("  Descartados por incompatibilidad:")
        for estilo, motivo in r["Descartados"]:
            print(f"    - {estilo} (por {motivo})")
    if r["Razones"]:
        print(f"  Por que {r['Mejor']}:")
        for razon in r["Razones"]:
            print(f"    * {razon}")


def main():
    """Modo interactivo por consola: el usuario escribe requisitos separados por coma."""
    motor = MotorInferencia()
    print("ArquiSelect - Seleccion de arquitectura de software")
    print("Escribe los requisitos separados por coma (ej: equipo_pequeno, presupuesto_bajo).")
    print("Linea vacia = caso por defecto. 'salir' para terminar.\n")
    while True:
        entrada = input("Requisitos> ").strip()
        if entrada.lower() == "salir":
            break
        requisitos = [r.strip() for r in entrada.split(",") if r.strip()]
        mostrar_resultado(motor.diagnosticar(requisitos))
        print()


if __name__ == "__main__":
    main()
