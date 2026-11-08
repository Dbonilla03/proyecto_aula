/* conocimiento_aprendido.pl - generado por ArquiSelect.
   Estilos, reglas expertas y sinonimos ensenados desde la interfaz.
   Lo lee cargar_aprendizaje/1, que valida cada termino (no se
   consulta directamente). */


explicacion_regla(mvc_para_equipos_pequenos, 'Un equipo pequeño que necesita separar interfaz y lógica rinde bien con MVC, siempre que el dominio sea simple.').
regla_experta(mvc_para_equipos_pequenos, soa, recomendar, 3, A) :-
    contiene_todos([equipo_pequeno, separar_interfaz_logica], A),
    \+ contiene_alguno([dominio_complejo], A).

lexico_aprendido([recursos, escasos]).
lexico([recursos, escasos], presupuesto_bajo, afirma).
