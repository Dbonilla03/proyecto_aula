/* ==========================================================================
   ArquiSelect - Sistema Experto para la Seleccion de Estilos de Arquitectura
   ========================================================================== */

:- encoding(utf8).

/* --- 0.1 Predicados dinamicos (aprendizaje en caliente, seccion 8) -------
        Los hechos de estos predicados pueden crecer en tiempo de ejecucion
        con assertz/1 cuando el usuario ensena una arquitectura nueva.
        estilo_aprendido/1 marca lo aprendido para distinguirlo de lo que
        escribio el experto: solo lo marcado se puede olvidar o guardar. --- */
:- dynamic estilo/2.
:- dynamic aporta/3.
:- dynamic incompatible/2.
:- dynamic penaliza/3.
:- dynamic descripcion_estilo/2.
:- dynamic estilo_aprendido/1.

/* --- 0.1b Predicados dinamicos del ENTREGABLE 3 ---------------------------
        regla_experta/5   : reglas que el experto ensena en caliente (seccion
                            9). Cada una es una CLAUSULA con cuerpo, no un
                            hecho. Sin reglas, la llamada simplemente falla
                            y el razonamiento queda igual que en el
                            entregable 2.
        explicacion_regla/2: texto claro de cada regla experta.
        lexico/3          : vocabulario de la DCG (lenguaje_natural.pl); el
                            experto le agrega sinonimos con assertz.
        ruta_aprendizaje_fijada/1: permite que las pruebas usen un archivo de
                            aprendizaje temporal en vez del real. --------- */
:- dynamic regla_experta/5.
:- dynamic explicacion_regla/2.
:- dynamic lexico/3.
:- dynamic ruta_aprendizaje_fijada/1.

:- use_module(library(filesex)).        % copy_file/2 para la copia .bak

/* --- 0.2 Carpeta de este archivo: directorio_base(Dir) -------------------
        Se fija al consultar el .pl para que guardar_aprendizaje/0 escriba
        conocimiento_aprendido.pl junto a la base, sin depender de Python. */
:- dynamic directorio_base/1.
:- prolog_load_context(directory, Dir),
   retractall(directorio_base(_)),
   assertz(directorio_base(Dir)).

/* --- 0.3 Modulo de lenguaje natural (DCG, entregable 3) -------------------
        La ruta es relativa a ESTE archivo (ensure_loaded la resuelve desde
        la carpeta del .pl que se esta cargando, no desde Python). */
:- ensure_loaded('lenguaje_natural.pl').

/* ==========================================================================
   SECCION 1. HECHOS
   ========================================================================== */

/* --- 1.1 Estilos arquitectonicos: estilo(Id, Nombre) -------------------- */
estilo(monolito_capas,    'Monolito en capas').
estilo(monolito_modular,  'Monolito modular').
estilo(microservicios,    'Microservicios').
estilo(serverless,        'Serverless (funciones como servicio)').
estilo(eventos,           'Arquitectura orientada a eventos').
estilo(mvc,               'MVC (Modelo-Vista-Controlador)').
estilo(onion,             'Arquitectura Onion (cebolla)').
estilo(hexagonal,         'Arquitectura Hexagonal (puertos y adaptadores)').
estilo(soa,               'SOA (arquitectura orientada a servicios)').
estilo(cliente_servidor,  'Cliente-Servidor').
estilo(clean,             'Clean Architecture').

/* --- 1.2 Requisitos reconocidos: requisito_categoria(Requisito, Categoria)
        Sirven para validar la lista que llega desde Python. -------------- */
requisito_categoria(equipo_pequeno,          equipo).
requisito_categoria(equipo_grande,           equipo).
requisito_categoria(sin_experiencia_devops,  equipo).
requisito_categoria(presupuesto_bajo,        presupuesto).
requisito_categoria(entrega_rapida,          tiempo).
requisito_categoria(muchos_usuarios,         carga).
requisito_categoria(carga_variable,          carga).
requisito_categoria(procesos_largos,         carga).
requisito_categoria(latencia_critica,        carga).
requisito_categoria(disponibilidad_alta,     operacion).
requisito_categoria(despliegue_independiente, operacion).
requisito_categoria(dominio_complejo,        dominio).
requisito_categoria(integracion_asincrona,   dominio).
requisito_categoria(consistencia_estricta,   dominio).
requisito_categoria(mantenibilidad_largo_plazo,     dominio).
requisito_categoria(testabilidad_alta,              dominio).
requisito_categoria(independencia_tecnologica,      dominio).
requisito_categoria(separar_interfaz_logica,        dominio).
requisito_categoria(integracion_sistemas_heredados, operacion).
requisito_categoria(datos_centralizados,            operacion).

/* --- 1.3 Requisito -> atributo de calidad que exige ---------------------
        requisito_atributo(Requisito, Atributo) --------------------------- */
requisito_atributo(equipo_pequeno,          simplicidad).
requisito_atributo(sin_experiencia_devops,  simplicidad).
requisito_atributo(presupuesto_bajo,        bajo_costo).
requisito_atributo(entrega_rapida,          rapidez_desarrollo).
requisito_atributo(muchos_usuarios,         escalabilidad).
requisito_atributo(carga_variable,          elasticidad).
requisito_atributo(latencia_critica,        rendimiento).
requisito_atributo(disponibilidad_alta,     disponibilidad).
requisito_atributo(despliegue_independiente, independencia_despliegue).
requisito_atributo(equipo_grande,           modularidad).
requisito_atributo(dominio_complejo,        modularidad).
requisito_atributo(integracion_asincrona,   desacople).
requisito_atributo(consistencia_estricta,   consistencia).
requisito_atributo(mantenibilidad_largo_plazo,     mantenibilidad).
requisito_atributo(testabilidad_alta,              testabilidad).
requisito_atributo(independencia_tecnologica,      independencia_tecnologica).
requisito_atributo(integracion_sistemas_heredados, interoperabilidad).
requisito_atributo(separar_interfaz_logica,        separacion_responsabilidades).
requisito_atributo(datos_centralizados,            centralizacion_datos).

/* --- 1.4 Aporte de cada estilo a un atributo (peso 1..3) ----------------
        aporta(Estilo, Atributo, Peso)
        Los pesos de los 6 estilos nuevos (mvc ... clean) y los que se
        agregaron a los estilos originales por los atributos nuevos
        (marcados con "% nuevo") son VALORES INICIALES PROPUESTOS: salen
        de la literatura general de cada estilo y se pueden ajustar con el
        experto sin tocar ninguna regla. -------------------------------- */
aporta(monolito_capas,   simplicidad,         3).
aporta(monolito_capas,   bajo_costo,          3).
aporta(monolito_capas,   rapidez_desarrollo,  3).
aporta(monolito_capas,   consistencia,        3).
aporta(monolito_capas,   rendimiento,         2).
aporta(monolito_capas,   separacion_responsabilidades, 2).   % nuevo
aporta(monolito_capas,   centralizacion_datos,         2).   % nuevo

aporta(monolito_modular, modularidad,         3).
aporta(monolito_modular, bajo_costo,          3).
aporta(monolito_modular, consistencia,        3).
aporta(monolito_modular, simplicidad,         2).
aporta(monolito_modular, rapidez_desarrollo,  2).
aporta(monolito_modular, rendimiento,         2).
aporta(monolito_modular, mantenibilidad,      2).            % nuevo
aporta(monolito_modular, separacion_responsabilidades, 2).   % nuevo

aporta(microservicios,   escalabilidad,             3).
aporta(microservicios,   disponibilidad,            3).
aporta(microservicios,   modularidad,               3).
aporta(microservicios,   independencia_despliegue,  3).
aporta(microservicios,   elasticidad,               2).
aporta(microservicios,   independencia_tecnologica, 2).      % nuevo
aporta(microservicios,   interoperabilidad,         2).      % nuevo

aporta(serverless,       elasticidad,         3).
aporta(serverless,       escalabilidad,       3).
aporta(serverless,       bajo_costo,          2).
aporta(serverless,       rapidez_desarrollo,  2).
aporta(serverless,       simplicidad,         2).

aporta(eventos,          desacople,           3).
aporta(eventos,          escalabilidad,       2).
aporta(eventos,          disponibilidad,      2).
aporta(eventos,          elasticidad,         2).
aporta(eventos,          modularidad,         1).
aporta(eventos,          interoperabilidad,   2).            % nuevo

aporta(mvc,              separacion_responsabilidades, 3).
aporta(mvc,              rapidez_desarrollo,  3).
aporta(mvc,              simplicidad,         2).
aporta(mvc,              bajo_costo,          2).
aporta(mvc,              mantenibilidad,      1).

aporta(onion,            mantenibilidad,      3).
aporta(onion,            testabilidad,        3).
aporta(onion,            independencia_tecnologica, 2).
aporta(onion,            modularidad,         2).
aporta(onion,            consistencia,        2).

aporta(hexagonal,        independencia_tecnologica, 3).
aporta(hexagonal,        testabilidad,        3).
aporta(hexagonal,        desacople,           3).
aporta(hexagonal,        mantenibilidad,      2).
aporta(hexagonal,        modularidad,         2).

aporta(soa,              interoperabilidad,   3).
aporta(soa,              modularidad,         2).
aporta(soa,              escalabilidad,       2).
aporta(soa,              independencia_despliegue, 2).
aporta(soa,              desacople,           2).
aporta(soa,              disponibilidad,      1).

aporta(cliente_servidor, centralizacion_datos, 3).
aporta(cliente_servidor, consistencia,        3).
aporta(cliente_servidor, simplicidad,         2).
aporta(cliente_servidor, bajo_costo,          2).
aporta(cliente_servidor, rapidez_desarrollo,  2).

aporta(clean,            mantenibilidad,      3).
aporta(clean,            testabilidad,        3).
aporta(clean,            independencia_tecnologica, 3).
aporta(clean,            modularidad,         3).
aporta(clean,            desacople,           2).

/* --- 1.5 Exclusiones duras: el estilo NO es viable con ese requisito ----
        incompatible(Estilo, Requisito) ----------------------------------- */
incompatible(microservicios,   equipo_pequeno).
incompatible(microservicios,   sin_experiencia_devops).
incompatible(serverless,       procesos_largos).
incompatible(serverless,       latencia_critica).
incompatible(monolito_capas,   despliegue_independiente).
incompatible(eventos,          consistencia_estricta).
incompatible(soa,              latencia_critica).          % el bus agrega saltos de red
incompatible(cliente_servidor, despliegue_independiente).  % el servidor es una sola pieza

/* --- 1.6 Penalizaciones blandas: el estilo es viable pero pierde puntos --
        penaliza(Estilo, Requisito, Peso) --------------------------------- */
penaliza(microservicios,   presupuesto_bajo,        2).
penaliza(microservicios,   entrega_rapida,          2).
penaliza(monolito_capas,   muchos_usuarios,         2).
penaliza(monolito_capas,   disponibilidad_alta,     2).
penaliza(monolito_capas,   carga_variable,          1).
penaliza(monolito_modular, disponibilidad_alta,     1).
penaliza(monolito_modular, despliegue_independiente, 2).
penaliza(serverless,       consistencia_estricta,   1).
penaliza(eventos,          entrega_rapida,          1).
penaliza(eventos,          equipo_pequeno,          1).
% Penalizaciones de los estilos nuevos (valores iniciales propuestos)
penaliza(mvc,              dominio_complejo,        1).
penaliza(mvc,              muchos_usuarios,         1).
penaliza(onion,            entrega_rapida,          2).
penaliza(onion,            equipo_pequeno,          1).
penaliza(onion,            presupuesto_bajo,        1).
penaliza(hexagonal,        entrega_rapida,          2).
penaliza(hexagonal,        equipo_pequeno,          1).
penaliza(clean,            entrega_rapida,          2).
penaliza(clean,            equipo_pequeno,          1).
penaliza(clean,            presupuesto_bajo,        1).
penaliza(soa,              sin_experiencia_devops,  2).
penaliza(soa,              presupuesto_bajo,        2).
penaliza(soa,              entrega_rapida,          1).
penaliza(soa,              latencia_critica,        1).
penaliza(cliente_servidor, muchos_usuarios,         2).
penaliza(cliente_servidor, disponibilidad_alta,     2).
penaliza(cliente_servidor, carga_variable,          1).
penaliza(cliente_servidor, despliegue_independiente, 1).

/* --- 1.7 Umbrales de prioridad: umbral_prioridad(Nivel, PuntajeMinimo) --
        Se evaluan de mayor a menor en nivel_prioridad/2. ----------------- */
umbral_prioridad(alta,  8).
umbral_prioridad(media, 4).

/* --- 1.8 Perfiles de proyecto: perfil(Nombre, RequisitosQueLoDefinen) ---
        El orden importa: se escoge el primero que se cumpla. ------------- */
perfil(alta_demanda, [muchos_usuarios, disponibilidad_alta]).
perfil(startup,      [equipo_pequeno, presupuesto_bajo]).
perfil(empresarial,  [equipo_grande, dominio_complejo]).

/* --- 1.9 Etiquetas legibles de cada requisito (las usa la interfaz) -----
        etiqueta(Requisito, Texto). Los textos van sin tildes para evitar
        problemas de codificacion al pasar por pyswip en Windows. -------- */
etiqueta(equipo_pequeno,          'Equipo reducido (menos de 5 personas)').
etiqueta(equipo_grande,           'Equipo grande (varios equipos de trabajo)').
etiqueta(sin_experiencia_devops,  'El equipo no tiene experiencia en DevOps').
etiqueta(presupuesto_bajo,        'Presupuesto bajo').
etiqueta(entrega_rapida,          'Hay que entregar en poco tiempo').
etiqueta(muchos_usuarios,         'Muchos usuarios concurrentes').
etiqueta(carga_variable,          'Carga variable o impredecible').
etiqueta(procesos_largos,         'Procesos largos (tareas de varios minutos)').
etiqueta(latencia_critica,        'Respuesta en milisegundos (latencia baja)').
etiqueta(disponibilidad_alta,     'Alta disponibilidad (24/7)').
etiqueta(despliegue_independiente, 'Desplegar partes del sistema por separado').
etiqueta(dominio_complejo,        'Dominio complejo (muchas reglas de negocio)').
etiqueta(integracion_asincrona,   'Intercambio de mensajes sin esperar respuesta').
etiqueta(consistencia_estricta,   'Consistencia estricta de datos (transacciones)').
etiqueta(mantenibilidad_largo_plazo,     'El sistema debe mantenerse y evolucionar por anos').
etiqueta(testabilidad_alta,              'Pruebas automaticas faciles (alta testabilidad)').
etiqueta(independencia_tecnologica,      'Poder cambiar base de datos o framework sin reescribir').
etiqueta(integracion_sistemas_heredados, 'Integrar sistemas existentes o heredados').
etiqueta(separar_interfaz_logica,        'Separar interfaz de usuario y logica').
etiqueta(datos_centralizados,            'Datos centralizados con varios clientes').

/* --- 1.10 Pregunta que el sistema hace cuando necesita ese dato ---------
        pregunta(Requisito, Texto). Se usa en el modulo "Que falta?". ---- */
pregunta(equipo_pequeno,          'El equipo de desarrollo tiene menos de 5 personas?').
pregunta(equipo_grande,           'Trabajaran varios equipos sobre el mismo sistema?').
pregunta(sin_experiencia_devops,  'Al equipo le falta experiencia con contenedores, CI/CD y monitoreo?').
pregunta(presupuesto_bajo,        'El presupuesto para infraestructura es limitado?').
pregunta(entrega_rapida,          'La primera version debe salir en pocas semanas?').
pregunta(muchos_usuarios,         'Se esperan muchos usuarios usando el sistema al mismo tiempo?').
pregunta(carga_variable,          'La demanda sube y baja de forma impredecible (picos)?').
pregunta(procesos_largos,         'Hay tareas que tardan varios minutos en ejecutarse?').
pregunta(latencia_critica,        'Las respuestas deben llegar en milisegundos?').
pregunta(disponibilidad_alta,     'El sistema debe estar disponible 24/7 sin caidas?').
pregunta(despliegue_independiente, 'Se necesita actualizar una parte sin redesplegar todo?').
pregunta(dominio_complejo,        'El negocio tiene muchas reglas y subdominios distintos?').
pregunta(integracion_asincrona,   'Los modulos o sistemas se comunican por mensajes o eventos?').
pregunta(consistencia_estricta,   'Las operaciones exigen transacciones con datos siempre consistentes?').
pregunta(mantenibilidad_largo_plazo,     'El sistema vivira muchos anos y debera evolucionar con facilidad?').
pregunta(testabilidad_alta,              'Es importante probar la logica de negocio de forma automatica y aislada?').
pregunta(independencia_tecnologica,      'Puede cambiar la base de datos, el framework o la interfaz en el futuro?').
pregunta(integracion_sistemas_heredados, 'Debe conectarse con sistemas ya existentes o heredados?').
pregunta(separar_interfaz_logica,        'Se necesita separar claramente la interfaz de usuario de la logica?').
pregunta(datos_centralizados,            'Los datos deben vivir en un solo lugar al que acceden varios clientes?').

/* --- 1.11 Requisitos que no pueden estar juntos -------------------------
        excluyentes(A, B): si ya se ingreso uno, no se sugiere el otro. -- */
excluyentes(equipo_pequeno, equipo_grande).

/* --- 1.12 Parametros del razonamiento de explicacion y desempate -------- */
umbral_desempate(2).       % diferencia minima entre 1o y 2o para no ser empate
peso_exclusion(5).         % castigo con que se representa un descarte (\+)
max_sugerencias(3).        % cuantos datos sugiere el modulo "Que falta?"
max_competidores(3).       % hipotesis que se comparan cuando falta evidencia

/* --- 1.13 Confianza segun el estado del dictamen ------------------------
        confianza_estado(Estado, Confianza) ------------------------------ */
confianza_estado(definitivo,   alta).
confianza_estado(empate,       media).
confianza_estado(insuficiente, baja).
confianza_estado(vacio,        nula).
confianza_estado(contradictorio, nula).   % seccion 10: entrada bloqueada

/* --- 1.14 Descripcion corta de cada estilo (la muestra la interfaz) -----
        descripcion_estilo(Estilo, Texto). Sin tildes, igual que 1.9. --- */
descripcion_estilo(monolito_capas,
    'Una sola aplicacion organizada en capas (presentacion, negocio, datos). Simple, barata y rapida de construir.').
descripcion_estilo(monolito_modular,
    'Una sola aplicacion dividida en modulos bien separados. Ordenada como microservicios, pero con un unico despliegue.').
descripcion_estilo(microservicios,
    'Varios servicios pequenos e independientes que se despliegan y escalan por separado. Potente, pero exige equipo y DevOps.').
descripcion_estilo(serverless,
    'Funciones que se ejecutan bajo demanda en la nube. Escala sola y se paga por uso, pero no sirve para tareas largas.').
descripcion_estilo(eventos,
    'Componentes que se comunican publicando y escuchando eventos. Muy desacoplada, pero con consistencia eventual.').
descripcion_estilo(mvc,
    'Separa la aplicacion en Modelo, Vista y Controlador. Ordena la interfaz y la logica; ideal para aplicaciones web y de escritorio pequenas o medianas.').
descripcion_estilo(onion,
    'Capas concentricas con el dominio en el centro y las dependencias apuntando hacia adentro. Facil de probar y de mantener a largo plazo.').
descripcion_estilo(hexagonal,
    'El nucleo de negocio se comunica con el exterior mediante puertos y adaptadores. Permite cambiar base de datos, framework o interfaz sin tocar el dominio.').
descripcion_estilo(soa,
    'Servicios de negocio reutilizables que se integran, normalmente por un bus empresarial. Pensada para conectar sistemas existentes en organizaciones grandes.').
descripcion_estilo(cliente_servidor,
    'Clientes que piden servicios a un servidor central que concentra datos y logica. Simple y facil de administrar, pero el servidor es un punto unico de falla.').
descripcion_estilo(clean,
    'Capas con reglas de dependencia estrictas: entidades, casos de uso, adaptadores y frameworks. Maxima independencia tecnologica y capacidad de prueba, con mas codigo inicial.').

/* ==========================================================================
   SECCION 2. REGLAS - NIVEL 1 (validacion preliminar y listas)
   ========================================================================== */

/* validar_entrada(+Entrada, -Limpia): primera barrera contra datos mal
   formados que lleguen desde Python. Si Entrada no es una lista cerrada
   devuelve []. Cada elemento debe ser un atomo sin variables (ground/1);
   se pasa a minuscula y lo que no cumpla se ignora. */
validar_entrada(Entrada, Limpia) :-
    is_list(Entrada), !,
    normalizar_lista(Entrada, Limpia).
validar_entrada(_, []).

normalizar_lista([], []).
normalizar_lista([X|T], [Y|L]) :-
    ground(X), atom(X), !,
    downcase_atom(X, Y),
    normalizar_lista(T, L).
normalizar_lista([_|T], L) :-          % variable libre, numero o termino
    normalizar_lista(T, L).

/* preparar_requisitos(+Entrada, -Validos, -Desconocidos): punto UNICO de
   entrada de datos. Valida una sola vez, separa los requisitos reconocidos
   (sin repetidos) de los que no estan en la base. La usan los tres
   predicados principales que llama Python. */
preparar_requisitos(Entrada, Validos, Desconocidos) :-
    validar_entrada(Entrada, Limpia),
    filtrar_validos(Limpia, V0),
    list_to_set(V0, Validos),
    desconocidos(Limpia, Desconocidos).

/* preparar_requisitos(+Entrada, -Validos): version corta cuando no se
   necesitan los desconocidos (modulo "Que falta?"). */
preparar_requisitos(Entrada, Validos) :-
    preparar_requisitos(Entrada, Validos, _).

/* requisito_conocido(+R): R aparece en la tabla de requisitos reconocidos. */
requisito_conocido(R) :-
    requisito_categoria(R, _).

/* filtrar_validos(+Lista, -Validos): conserva solo los requisitos conocidos.
   El corte de la 2a clausula hace las dos ultimas mutuamente excluyentes:
   si R es conocido NO se debe intentar la clausula que lo descarta. */
filtrar_validos([], []).
filtrar_validos([R|T], [R|V]) :-
    requisito_conocido(R), !,
    filtrar_validos(T, V).
filtrar_validos([_|T], V) :-
    filtrar_validos(T, V).

/* desconocidos(+Lista, -Desc): requisitos enviados que no se reconocen.
   Mismo patron con corte (clausulas excluyentes). */
desconocidos([], []).
desconocidos([R|T], D) :-
    requisito_conocido(R), !,
    desconocidos(T, D).
desconocidos([R|T], [R|D]) :-
    desconocidos(T, D).

/* contiene_todos(+Sub, +Lista): Sub es subconjunto de Lista (recursion
   sobre Sub; la recursion siempre consume la lista, no hay ciclos). */
contiene_todos([], _).
contiene_todos([H|T], Lista) :-
    memberchk(H, Lista),
    contiene_todos(T, Lista).

/* contiene_alguno(+Sub, +Lista): al menos un elemento de Sub esta en Lista.
   Las reglas expertas lo usan negado (\+) para sus exclusiones; el corte
   detiene la busqueda en el primer elemento comun (basta con uno). */
contiene_alguno(Sub, Lista) :-
    member(X, Sub),
    memberchk(X, Lista), !.

/* atributo_requerido(+Reqs, ?Atributo): un requisito de la lista exige el
   atributo de calidad. */
atributo_requerido(Reqs, Atributo) :-
    member(R, Reqs),
    requisito_atributo(R, Atributo).

/* atributos_requeridos(+Reqs, -Atributos): lista sin duplicados y ordenada.
   Si no hay ninguno, setof falla y la segunda clausula devuelve []. */
atributos_requeridos(Reqs, Atributos) :-
    setof(A, atributo_requerido(Reqs, A), Atributos), !.
atributos_requeridos(_, []).

/* suficiencia(+Validos, -Estado): cuantos datos utiles llegaron.
   Cortes: las 3 clausulas son excluyentes; la ultima es el caso general. */
suficiencia(Validos, vacia) :-
    length(Validos, 0), !.
suficiencia(Validos, insuficiente) :-
    length(Validos, 1), !.
suficiencia(_, suficiente).

/* ==========================================================================
   SECCION 3. REGLAS - NIVEL 2 (inferencia intermedia)
   ========================================================================== */

/* motivo_descarte(+Estilo, +Reqs, -Motivo): el estilo choca con un requisito
   (usa incompatible/2, un hecho de exclusion dura). La 2a clausula agrega
   las reglas expertas con efecto "descartar": Motivo es el id de la regla.
   Sin reglas aprendidas la 2a clausula no tiene soluciones. */
motivo_descarte(Estilo, Reqs, Motivo) :-
    member(Motivo, Reqs),
    incompatible(Estilo, Motivo).
motivo_descarte(Estilo, Reqs, Id) :-
    regla_descarta(Estilo, Reqs, Id).

/* regla_descarta(?Estilo, +Reqs, -Id): una regla experta de descarte se
   dispara con los requisitos dados. */
regla_descarta(Estilo, Reqs, Id) :-
    regla_experta(Id, Estilo, descartar, _, Reqs).

/* bonus_reglas(+Estilo, +Reqs, -Bonus): suma de los pesos de las reglas
   expertas "recomendar" que se disparan para el estilo (0 si no hay). */
bonus_reglas(Estilo, Reqs, Bonus) :-
    findall(P, regla_experta(_, Estilo, recomendar, P, Reqs), Ps),
    sum_list(Ps, Bonus).

/* estilo_viable(?Estilo, +Reqs): NEGACION POR FALLO.
   estilo/2 instancia Estilo ANTES de \+, asi la negacion se evalua con
   variables ligadas. Un estilo es viable si NO existe ningun motivo de
   descarte. */
estilo_viable(Estilo, Reqs) :-
    estilo(Estilo, _),
    \+ motivo_descarte(Estilo, Reqs, _).

/* aporte_total(+Estilo, +Reqs, -Total): suma los pesos de los atributos
   exigidos que el estilo favorece. */
aporte_total(Estilo, Reqs, Total) :-
    atributos_requeridos(Reqs, Atributos),
    findall(P, ( member(A, Atributos), aporta(Estilo, A, P) ), Pesos),
    sum_list(Pesos, Total).

/* penalizacion_total(+Estilo, +Reqs, -Total): suma las penalizaciones
   blandas que producen los requisitos recibidos. */
penalizacion_total(Estilo, Reqs, Total) :-
    findall(P, ( member(R, Reqs), penaliza(Estilo, R, P) ), Pesos),
    sum_list(Pesos, Total).

/* puntaje(+Estilo, +Reqs, -Puntaje): aporte menos penalizacion, mas el
   bonus de las reglas expertas disparadas (entregable 3). Como ranking,
   candidatos, que_falta y descartes pasan por aqui, todos toman en cuenta
   las reglas sin cambiar de firma. Sin reglas el bonus es 0. */
puntaje(Estilo, Reqs, Puntaje) :-
    aporte_total(Estilo, Reqs, Aporte),
    penalizacion_total(Estilo, Reqs, Penal),
    bonus_reglas(Estilo, Reqs, Bonus),
    Puntaje is Aporte - Penal + Bonus.

/* cubiertos(+Estilo, +Reqs, -Cubiertos, -Cantidad): FILTRA y CUENTA los
   atributos exigidos que el estilo realmente favorece. */
cubiertos(Estilo, Reqs, Cubiertos, Cantidad) :-
    atributos_requeridos(Reqs, Atributos),
    findall(A, ( member(A, Atributos), aporta(Estilo, A, _) ), Cubiertos),
    length(Cubiertos, Cantidad).

/* nivel_prioridad(+Puntaje, -Nivel): SEVERIDAD/PRIORIDAD en 3 niveles.
   Cortes: cada clausula excluye a las siguientes (primer umbral que cumple).
   La ultima clausula es el valor por defecto (fallback): baja. */
nivel_prioridad(Puntaje, alta) :-
    umbral_prioridad(alta, U), Puntaje >= U, !.
nivel_prioridad(Puntaje, media) :-
    umbral_prioridad(media, U), Puntaje >= U, !.
nivel_prioridad(_, baja).

/* nivel_riesgo(+Estilo, +Reqs, -Riesgo): cuanto "castigan" los requisitos
   al estilo. Corte para que solo aplique un nivel. */
nivel_riesgo(Estilo, Reqs, bajo) :-
    penalizacion_total(Estilo, Reqs, P), P =:= 0, !.
nivel_riesgo(Estilo, Reqs, medio) :-
    penalizacion_total(Estilo, Reqs, P), P =< 2, !.
nivel_riesgo(_, _, alto).

/* perfil_proyecto(+Reqs, -Perfil): primer perfil cuyos requisitos esten
   todos presentes (usa contiene_todos/2 sobre listas). El corte evita que
   en backtracking aparezcan varios perfiles; 'general' es el fallback. */
perfil_proyecto(Reqs, Perfil) :-
    perfil(Perfil, Requeridos),
    contiene_todos(Requeridos, Reqs), !.
perfil_proyecto(_, general).

/* ==========================================================================
   SECCION 4. REGLAS - NIVEL 3 (conclusion final y recoleccion)
   ========================================================================== */

/* recomendar(?Estilo, +Reqs, -Puntaje, -Prioridad, -Riesgo): un estilo
   viable con su puntaje, prioridad y riesgo. Integra reglas de nivel 2. */
recomendar(Estilo, Reqs, Puntaje, Prioridad, Riesgo) :-
    estilo_viable(Estilo, Reqs),
    puntaje(Estilo, Reqs, Puntaje),
    nivel_prioridad(Puntaje, Prioridad),
    nivel_riesgo(Estilo, Reqs, Riesgo).

/* ranking(+Reqs, -Ranking): RECOLECCION con setof/3 (sin duplicados).
   La clave es -Puntaje para que el mejor quede primero; los empates se
   ordenan alfabeticamente por estilo. Cada elemento sale como lista
   [Estilo, Puntaje, Prioridad, Riesgo] para que Python la reciba facil. */
ranking([], []) :- !.          % sin requisitos validos no hay nada que ordenar
ranking(Reqs, Ranking) :-
    setof(NP-E-Pr-Ri,
          P^( recomendar(E, Reqs, P, Pr, Ri), NP is -P ),
          Ordenados), !,
    maplist(fila_ranking, Ordenados, Ranking).
ranking(_, []).

fila_ranking(NP-E-Pr-Ri, [E, P, Pr, Ri]) :-
    P is -NP.

/* mejor_estilo(+Reqs, -Estilo, -Prioridad): el primero del ranking, siempre
   que tenga puntaje positivo. Si no hay ranking, o ningun estilo aporta
   algo (lista vacia, todo descartado, requisitos sin efecto) entra el
   FALLBACK: monolito_modular, el estilo mas conservador. El corte impide
   que el fallback se alcance cuando ya hubo una recomendacion. */
mejor_estilo(Reqs, Estilo, Prioridad) :-
    ranking(Reqs, [[Estilo, Puntaje, Prioridad, _]|_]),
    Puntaje > 0, !.
mejor_estilo(_, monolito_modular, por_defecto).

/* candidatos(+Reqs, -Lista): estilos que todavia pueden ser la respuesta.
   Toma el ranking/2 (que ya solo contiene estilos viables) y conserva las
   filas con puntaje positivo, en el mismo orden y con la misma forma
   [Estilo, Puntaje, Prioridad, Riesgo]. Pasa por preparar_requisitos/2
   como los demas predicados que llama Python. Lista vacia -> []. */
candidatos(Reqs, Lista) :-
    preparar_requisitos(Reqs, V),
    ranking(V, Ranking),
    findall([E, P, Pr, Ri],
            ( member([E, P, Pr, Ri], Ranking), P > 0 ),
            Lista).

/* descartes(+Reqs, -Lista): complemento de candidatos/2. Devuelve
   [[Estilo, Tipo, Motivo], ...] para cada estilo que NO es candidato, asi
   candidatos + descartes cubren todos los estilos sin repetir ninguno.
   NEGACION POR FALLO: estilo/2 instancia E antes de \+, y memberchk/2
   compara con la fila [E, ...] ya ligada. Lista vacia -> todos los estilos
   salen como sin_evidencia con puntaje 0. */
descartes(Reqs, Lista) :-
    preparar_requisitos(Reqs, V),
    candidatos(V, Cands),
    findall([E, Tipo, Motivo],
            ( estilo(E, _),
              \+ memberchk([E|_], Cands),
              motivo_no_candidato(E, V, Tipo, Motivo) ),
            Lista).

/* motivo_no_candidato(+Estilo, +Reqs, -Tipo, -Motivo):
   1) exclusion: el estilo choca con un requisito (incompatible/2). El
      corte deja un solo motivo aunque varios requisitos lo excluyan, para
      que el estilo aparezca una sola vez, e impide caer en las siguientes.
   1b) regla_experta: lo descarta una regla experta (Motivo = id de la
      regla). Va despues de 1) para que, sin reglas, el resultado sea
      identico al del entregable 2.
   2) sin_evidencia: el estilo es viable pero su puntaje es <= 0 (si fuera
      positivo estaria en candidatos/2). Motivo = puntaje. */
motivo_no_candidato(E, V, exclusion, R) :-
    member(R, V), incompatible(E, R), !.
motivo_no_candidato(E, V, regla_experta, Id) :-
    regla_descarta(E, V, Id), !.
motivo_no_candidato(E, V, sin_evidencia, P) :-
    estilo_viable(E, V),
    puntaje(E, V, P).

/* descartados(+Reqs, -Lista): [[Estilo, RequisitoQueLoDescarta], ...] */
descartados(Reqs, Lista) :-
    setof([E, M],
          N^( estilo(E, N), motivo_descarte(E, Reqs, M) ),
          Lista), !.
descartados(_, []).

/* razones(+Estilo, +Reqs, -Razones): explicacion legible del puntaje.
   Genera una frase por cada atributo que favorece y por cada penalizacion. */
razones(Estilo, Reqs, Razones) :-
    findall(Frase,
            ( atributo_requerido(Reqs, A),
              aporta(Estilo, A, P),
              format(atom(Frase), 'favorece ~w (+~w)', [A, P]) ),
            Favores0),
    sort(Favores0, Favores),
    findall(Frase,
            ( member(R, Reqs),
              penaliza(Estilo, R, P),
              format(atom(Frase), 'penalizado por ~w (-~w)', [R, P]) ),
            Penales),
    findall(Frase,
            ( regla_experta(Id, Estilo, recomendar, P, Reqs),
              explicacion_regla(Id, Ex),
              format(atom(Frase), 'Regla experta ~w: ~w (+~w)', [Id, Ex, P]) ),
            Expertas),
    append([Favores, Penales, Expertas], Razones).

/* diagnosticar_arquitectura(+Reqs, -Resultado...): PREDICADO PRINCIPAL.
   Orquesta todo el razonamiento. Python solo lo invoca y lee las salidas.
   1a clausula (seccion 10): con una contradiccion dura NO hay recomendacion.
   Mejor = ninguno, Prioridad = bloqueado y Razones = mensajes de la
   contradiccion. El corte impide llegar a la 2a clausula (la que
   recomienda). Las salidas se ligan DESPUES del corte, no en la cabeza: asi
   el predicado es "steadfast" y aunque se llame con Mejor ya fijado no se
   salta el bloqueo. */
diagnosticar_arquitectura(Reqs, Mejor, Prioridad, Ranking, Descartados,
                          Razones, Perfil, Desconocidos, Suficiencia) :-
    bloqueo_duro(Reqs, [], Mensajes), !,
    preparar_requisitos(Reqs, _, Desconocidos),
    Mejor = ninguno, Prioridad = bloqueado, Ranking = [], Descartados = [],
    Razones = Mensajes, Perfil = ninguno, Suficiencia = contradictoria.
diagnosticar_arquitectura(Reqs, Mejor, Prioridad, Ranking, Descartados,
                          Razones, Perfil, Desconocidos, Suficiencia) :-
    preparar_requisitos(Reqs, Validos, Desconocidos),
    suficiencia(Validos, Suficiencia),
    perfil_proyecto(Validos, Perfil),
    mejor_estilo(Validos, Mejor, Prioridad),
    ranking(Validos, Ranking),
    descartados(Validos, Descartados),
    razones(Mejor, Validos, Razones).

/* ==========================================================================
   SECCION 5. MODULO DE EXPLICABILIDAD ("Por que?") - ENTREGABLE 2
   Construye la traza de auditoria: reglas disparadas, hechos comprobados
   como verdaderos e hipotesis alternativas descartadas.
   ========================================================================== */

/* regla_disparada(+Validos, +Mejor, -Paso): cada solucion es un paso de la
   traza con la forma [Nivel, Regla, Detalle]. Las clausulas estan en el
   mismo orden del encadenamiento (nivel 1 -> 2 -> 3), asi findall/3
   devuelve la traza ya ordenada. Solo aparecen las reglas que realmente
   tuvieron exito: si una meta falla, ese paso no entra en la traza. */

% Nivel 1 - validacion preliminar
regla_disparada(V, _, [1, 'requisito_conocido/1', D]) :-
    member(R, V),
    requisito_categoria(R, C),
    format(atom(D), '~w es un requisito reconocido (grupo ~w)', [R, C]).
regla_disparada(V, _, [1, 'suficiencia/2', D]) :-
    suficiencia(V, S),
    length(V, N),
    format(atom(D), '~w requisito(s) util(es), suficiencia: ~w', [N, S]).

% Nivel 2 - inferencia intermedia
regla_disparada(V, _, [2, 'requisito_atributo/2', D]) :-
    member(R, V),
    requisito_atributo(R, A),
    format(atom(D), '~w exige el atributo de calidad ~w', [R, A]).
regla_disparada(V, _, [2, 'perfil_proyecto/2', D]) :-
    perfil_proyecto(V, P),
    format(atom(D), 'perfil del proyecto detectado: ~w', [P]).
regla_disparada(V, M, [2, 'estilo_viable/2 (\\+)', D]) :-
    estilo_viable(M, V),
    format(atom(D), '~w no choca con ningun requisito (negacion por fallo)', [M]).
regla_disparada(V, M, [2, 'aporta/3', D]) :-
    atributos_requeridos(V, As),
    member(A, As),
    aporta(M, A, P),
    format(atom(D), '~w favorece ~w (+~w)', [M, A, P]).
regla_disparada(V, M, [2, 'penaliza/3', D]) :-
    member(R, V),
    penaliza(M, R, P),
    format(atom(D), '~w es penalizado por ~w (-~w)', [M, R, P]).
% Reglas expertas (entregable 3): una linea por regla que se dispara, para
% cualquier estilo (las de descarte afectan a estilos que no son el mejor).
regla_disparada(V, _, [2, 'regla_experta/5', D]) :-
    regla_experta(Id, E, Ef, P, V),
    explicacion_regla(Id, Ex),
    texto_efecto_regla(Ef, P, E, TE),
    format(atom(D), 'Regla experta ~w: ~w (~w)', [Id, Ex, TE]).
regla_disparada(V, M, [2, 'puntaje/3', D]) :-
    aporte_total(M, V, A),
    penalizacion_total(M, V, Pe),
    bonus_reglas(M, V, B),
    puntaje(M, V, Pt),
    detalle_puntaje(M, A, Pe, B, Pt, D).
regla_disparada(V, M, [2, 'nivel_prioridad/2', D]) :-
    puntaje(M, V, Pt),
    nivel_prioridad(Pt, N),
    format(atom(D), 'puntaje ~w -> prioridad (severidad) ~w', [Pt, N]).
regla_disparada(V, M, [2, 'nivel_riesgo/3', D]) :-
    nivel_riesgo(M, V, R),
    penalizacion_total(M, V, P),
    format(atom(D), 'penalizacion acumulada ~w -> riesgo ~w', [P, R]).

% Nivel 3 - conclusion
regla_disparada(V, M, [3, 'recomendar/5', D]) :-
    recomendar(M, V, P, Pr, Ri),
    format(atom(D), '~w es viable: puntaje ~w, prioridad ~w, riesgo ~w',
           [M, P, Pr, Ri]).
regla_disparada(V, M, [3, 'ranking/2', D]) :-
    ranking(V, Rk),
    Rk = [[M, P|_]|Resto],
    detalle_primer_lugar(M, P, Resto, D).
regla_disparada(V, M, [3, 'mejor_estilo/3', D]) :-
    mejor_estilo(V, M2, Pr),
    M2 == M,
    Pr \== por_defecto,
    format(atom(D), '~w se recomienda con prioridad ~w', [M, Pr]).
regla_disparada(V, M, [3, 'mejor_estilo/3 (por defecto)', D]) :-
    mejor_estilo(V, M2, por_defecto),
    M2 == M,
    format(atom(D), 'ningun estilo obtuvo puntaje positivo: se aplica ~w por defecto', [M]).
regla_disparada(V, _, [3, 'estado_dictamen/2', D]) :-
    estado_dictamen(V, E),
    confianza_estado(E, C),
    format(atom(D), 'dictamen ~w con confianza ~w', [E, C]).

/* detalle_puntaje(+M, +Aporte, +Penal, +Bonus, +Puntaje, -D): sin bonus se
   conserva el texto del entregable 2; con bonus se muestra la suma. Corte =
   clausulas excluyentes. */
detalle_puntaje(M, A, Pe, 0, Pt, D) :- !,
    format(atom(D), 'puntaje de ~w = ~w - ~w = ~w', [M, A, Pe, Pt]).
detalle_puntaje(M, A, Pe, B, Pt, D) :-
    format(atom(D), 'puntaje de ~w = ~w - ~w + ~w (reglas expertas) = ~w',
           [M, A, Pe, B, Pt]).

/* texto_efecto_regla(+Efecto, +Peso, +Estilo, -Texto) */
texto_efecto_regla(recomendar, P, E, T) :- !,
    format(atom(T), '+~w a ~w', [P, E]).
texto_efecto_regla(descartar, _, E, T) :-
    format(atom(T), 'descarta ~w', [E]).

/* detalle_primer_lugar(+Mejor, +Puntaje, +Resto, -Detalle): texto del paso
   ranking/2. Si otros estilos tienen el MISMO puntaje lo dice de forma
   explicita: el orden entre ellos lo fija setof/3 (alfabetico), no la
   evidencia. Corte = clausulas excluyentes. */
detalle_primer_lugar(M, P, Resto, D) :-
    findall(E, member([E, P|_], Resto), Empatados),
    Empatados \== [], !,
    atomic_list_concat(Empatados, ', ', Txt),
    format(atom(D),
           '~w queda primero con ~w pts, EMPATADO con ~w (orden alfabetico de setof, no por evidencia)',
           [M, P, Txt]).
detalle_primer_lugar(M, P, _, D) :-
    format(atom(D), '~w ocupa el primer lugar del ranking con ~w pts (setof)', [M, P]).

/* hechos_verdaderos(+Validos, -Hechos): evidencia ingresada que unifico con
   la base. Cada hecho sale como [Requisito, Grupo, AtributoQueExige]. */
hechos_verdaderos(V, Hechos) :-
    findall([R, C, A],
            ( member(R, V),
              requisito_categoria(R, C),
              atributo_o_ninguno(R, A) ),
            Hechos).

/* atributo_o_ninguno(+R, -A): procesos_largos, por ejemplo, no exige un
   atributo: solo sirve para excluir estilos. Corte = clausulas excluyentes. */
atributo_o_ninguno(R, A) :-
    requisito_atributo(R, A), !.
atributo_o_ninguno(_, ninguno).

/* hipotesis_descartada(+Validos, +Mejor, -H): estilos que compartian parte
   de la evidencia pero quedaron fuera. H = [Estilo, Tipo, Detalle, Comparte]
   - Tipo exclusion   : hay una condicion excluyente (incompatible/2, \+).
   - Tipo sin_evidencia: es viable pero su puntaje no es positivo, es decir,
                         le falta evidencia critica a su favor.
   Comparte es la lista de atributos exigidos que el estilo si cubria.
   Para sin_evidencia se exige que el estilo se haya relacionado con el
   caso (comparte algo o fue penalizado). */
hipotesis_descartada(V, _, [E, exclusion, Detalle, Comparte]) :-
    estilo(E, _),
    findall(T, ( motivo_descarte(E, V, R), texto_motivo(R, T) ), Motivos),
    Motivos \== [],
    atomic_list_concat(Motivos, ', ', Txt),
    format(atom(Detalle), 'condicion excluyente: ~w', [Txt]),
    cubiertos(E, V, Comparte, _).
hipotesis_descartada(V, Mejor, [E, sin_evidencia, Detalle, Comparte]) :-
    estilo_viable(E, V),
    E \== Mejor,
    puntaje(E, V, Pt),
    Pt =< 0,
    cubiertos(E, V, Comparte, _),
    relacionado_con_caso(E, V, Comparte),
    format(atom(Detalle), 'puntaje ~w: no hay evidencia critica a su favor', [Pt]).

/* texto_motivo(+Motivo, -Texto): un requisito se muestra tal cual; el id de
   una regla experta se marca como tal. Corte = clausulas excluyentes. */
texto_motivo(M, T) :-
    explicacion_regla(M, _), !,
    format(atom(T), 'regla experta ~w', [M]).
texto_motivo(M, M).

/* relacionado_con_caso(+E, +V, +Comparte): el estilo tuvo que ver con el
   caso, porque cubria algun atributo o porque algun requisito lo penalizo.
   Asi no se listan como "descartados" estilos que ni se tocaron. */
relacionado_con_caso(_, _, Comparte) :-
    Comparte \== [], !.
relacionado_con_caso(E, V, _) :-
    penalizacion_total(E, V, P),
    P > 0.

/* explicar_diagnostico(+Reqs, -Mejor, -Reglas, -Hechos, -Descartadas):
   PREDICADO PRINCIPAL DEL MODULO "Por que?". Python lo llama una vez y
   recibe la traza completa ya armada. */
explicar_diagnostico(Reqs, Mejor, Reglas, Hechos, Descartadas) :-
    preparar_requisitos(Reqs, V, Desc),
    mejor_estilo(V, Mejor, _),
    findall([1, 'desconocidos/2', D],
            ( member(X, Desc),
              format(atom(D), '~w no esta en la base y se ignora', [X]) ),
            PasosDesc),
    findall(P, regla_disparada(V, Mejor, P), Pasos),
    append(PasosDesc, Pasos, Reglas),
    hechos_verdaderos(V, Hechos),
    findall(H, hipotesis_descartada(V, Mejor, H), Descartadas).

/* ==========================================================================
   SECCION 6. MODULO DE RECOMENDACION ("Que falta?") - ENTREGABLE 2
   Decide si la evidencia alcanza, que hipotesis siguen en competencia y
   que dato aun no ingresado tiene mas peso para desempatarlas.
   ========================================================================== */

/* mejor_puntaje(+V, -P) y margen_lider(+V, -M): datos del ranking que usa
   estado_dictamen/2. Si hay un solo estilo viable el margen es amplio.
   Se llama a ranking/2 con variable libre y luego se unifica: asi el
   predicado es "steadfast" y no se salta los cortes de ranking/2. */
mejor_puntaje(V, P) :-
    ranking(V, Rk),
    Rk = [[_, P, _, _]|_], !.
mejor_puntaje(_, 0).

margen_lider(V, M) :-
    ranking(V, Rk),
    Rk = [[_, P1, _, _], [_, P2, _, _]|_], !,
    M is P1 - P2.
margen_lider(_, 100).

/* estado_dictamen(+V, -Estado): vacio | insuficiente | empate | definitivo.
   Cortes: se aplica la primera condicion que se cumpla; la ultima clausula
   es el caso general (dictamen definitivo). */
estado_dictamen(V, vacio) :-
    V == [], !.
estado_dictamen(V, insuficiente) :-
    suficiencia(V, insuficiente), !.
estado_dictamen(V, insuficiente) :-
    mejor_puntaje(V, P),
    umbral_prioridad(media, U),
    P < U, !.
estado_dictamen(V, empate) :-
    margen_lider(V, M),
    umbral_desempate(D),
    M < D, !.
estado_dictamen(_, definitivo).

/* hipotesis_en_competencia(+V, -Comp): estilos que siguen "parcialmente
   activos". estado_dictamen/2 se consulta con variable libre y despues se
   compara con ==, porque llamarlo con la salida ya fijada saltaria sus
   cortes (un vacio podria pasar como empate).
   1) Empate: los que estan a menos de umbral_desempate puntos del lider.
   2) Si no: los mejores estilos con puntaje positivo (max_competidores).
   3) Si ninguno suma (lista vacia, por ejemplo): todos los viables. */
hipotesis_en_competencia(V, Comp) :-
    estado_dictamen(V, Estado),
    Estado == empate, !,
    ranking(V, Rk),
    Rk = [[_, P1, _, _]|_],
    umbral_desempate(D),
    findall(E, ( member([E, P, _, _], Rk), P1 - P < D ), Comp).
hipotesis_en_competencia(V, Comp) :-
    ranking(V, Rk),
    findall(E, ( member([E, P, _, _], Rk), P > 0 ), Activas),
    Activas \== [], !,
    max_competidores(N),
    primeros(N, Activas, Comp).
hipotesis_en_competencia(V, Comp) :-
    findall(E, estilo_viable(E, V), Comp).

/* primeros(+N, +Lista, -Prefijo): los N primeros elementos (o menos). */
primeros(0, _, []) :- !.
primeros(_, [], []) :- !.
primeros(N, [X|T], [X|R]) :-
    N1 is N - 1,
    primeros(N1, T, R).

/* dato_candidato(+V, +Negados, ?R): requisito reconocido que aun NO se
   ingreso, que el usuario NO respondio con "no aplica" y que no contradice
   lo ya ingresado (excluyentes/2). Negacion por fallo con R ya instanciado
   por requisito_categoria/2. */
dato_candidato(V, Negados, R) :-
    requisito_categoria(R, _),
    \+ memberchk(R, V),
    \+ memberchk(R, Negados),
    \+ choca_con_ingresado(R, V).

choca_con_ingresado(R, V) :-
    member(X, V),
    ( excluyentes(R, X) ; excluyentes(X, R) ).

/* efecto_dato(+Estilo, +V, +R, -Delta, -Tipo): cuanto cambiaria el puntaje
   del estilo si el usuario confirmara R. Si R lo excluye, el efecto es un
   descarte y se representa con -peso_exclusion. */
efecto_dato(E, _, R, Delta, descarta) :-
    incompatible(E, R), !,
    peso_exclusion(P),
    Delta is -P.
% Regla experta de descarte que se dispararia SOLO al agregar R (no antes).
% \+ con E, V y R ya ligados. Sin reglas aprendidas esta clausula no aplica.
efecto_dato(E, V, R, Delta, descarta) :-
    regla_descarta(E, [R|V], _),
    \+ regla_descarta(E, V, _), !,
    peso_exclusion(P),
    Delta is -P.
efecto_dato(E, V, R, Delta, Tipo) :-
    puntaje(E, V, Antes),
    puntaje(E, [R|V], Despues),
    Delta is Despues - Antes,
    tipo_cambio(Delta, Tipo).

tipo_cambio(D, suma)  :- D > 0, !.
tipo_cambio(D, resta) :- D < 0, !.
tipo_cambio(_, neutro).

/* poder_desempate(+Comp, +V, +R, -Poder, -Efectos): peso del dato R para
   separar las hipotesis en competencia. Con dos o mas hipotesis es la
   distancia entre el efecto mas favorable y el menos favorable (un dato
   que sube a una y baja o descarta a otra separa mucho). Con una sola
   hipotesis es cuanto la confirmaria o debilitaria. */
poder_desempate(Comp, V, R, Poder, Efectos) :-
    findall([E, Tipo, Delta],
            ( member(E, Comp), efecto_dato(E, V, R, Delta, Tipo) ),
            Efectos),
    findall(D, member([_, _, D], Efectos), Deltas),
    max_list(Deltas, Max),
    min_list(Deltas, Min),
    length(Comp, N),
    poder_segun_cantidad(N, Max, Min, Poder).

poder_segun_cantidad(1, Max, _, Poder) :- !,
    Poder is abs(Max).
poder_segun_cantidad(_, Max, Min, Poder) :-
    Poder is Max - Min.

/* sugerencias_desempate(+V, +Negados, +Comp, -Top): datos a preguntar
   ordenados de mayor a menor poder. Cada uno sale como [Requisito, Poder,
   Pregunta, Efectos]. keysort/2 es estable: ante empate de poder se respeta
   el orden de la base de conocimiento. Solo se sugieren datos con poder > 0
   y que el usuario no haya descartado (Negados). */
sugerencias_desempate(_, _, [], []) :- !.
sugerencias_desempate(V, Negados, Comp, Top) :-
    findall(NP-[R, Poder, Pregunta, Efectos],
            ( dato_candidato(V, Negados, R),
              poder_desempate(Comp, V, R, Poder, Efectos),
              Poder > 0,
              pregunta(R, Pregunta),
              NP is -Poder ),
            Pares),
    keysort(Pares, Ordenados),
    valores_de_pares(Ordenados, Todas),
    max_sugerencias(N),
    primeros(N, Todas, Top).

valores_de_pares([], []).
valores_de_pares([_-X|T], [X|R]) :-
    valores_de_pares(T, R).

/* que_falta(+Reqs, -Estado, -Confianza, -Competencia, -Sugerencias):
   version sin respuestas negativas (Negados = []). */
que_falta(Reqs, Estado, Confianza, Competencia, Sugerencias) :-
    que_falta(Reqs, [], Estado, Confianza, Competencia, Sugerencias).

/* que_falta(+Reqs, +Negados, -Estado, -Confianza, -Competencia, -Sugerencias):
   PREDICADO PRINCIPAL DEL MODULO "Que falta?". Negados son los requisitos
   a los que el usuario respondio "no aplica": no se vuelven a preguntar.
   Pasan por la misma validacion que Reqs.
   1a clausula (seccion 10): con una contradiccion dura (incluido un
   requisito afirmado y negado a la vez) Estado = contradictorio, sin
   competencia ni sugerencias. Mismo patron que diagnosticar_arquitectura/9:
   corte para no llegar a la 2a clausula y salidas ligadas despues del corte. */
que_falta(Reqs, Negados, Estado, Confianza, Competencia, Sugerencias) :-
    bloqueo_duro(Reqs, Negados, _), !,
    Estado = contradictorio,
    confianza_estado(Estado, Confianza),
    Competencia = [], Sugerencias = [].
que_falta(Reqs, Negados, Estado, Confianza, Competencia, Sugerencias) :-
    preparar_requisitos(Reqs, V),
    preparar_requisitos(Negados, N),
    estado_dictamen(V, Estado),
    confianza_estado(Estado, Confianza),
    hipotesis_en_competencia(V, Competencia),
    sugerencias_desempate(V, N, Competencia, Sugerencias).

/* resumen_dictamen(+Reqs, -Mejor, -AFavor, -EnContra, -SinEfecto):
   explicacion en lenguaje sencillo para la pestana "Resumen".
   - AFavor   : [[Atributo, Peso, RequisitosQueLoExigen], ...] atributos
                exigidos que el estilo recomendado favorece (un atributo se
                cuenta una vez, igual que en aporte_total/3).
   - EnContra : [[Requisito, Peso], ...] penalizaciones blandas.
   - SinEfecto: requisitos que no suman ni restan al estilo recomendado. */
resumen_dictamen(Reqs, Mejor, AFavor, EnContra, SinEfecto) :-
    preparar_requisitos(Reqs, V),
    mejor_estilo(V, Mejor, _),
    atributos_requeridos(V, Atributos),
    findall([A, P, Rs],
            ( member(A, Atributos),
              aporta(Mejor, A, P),
              findall(R, ( member(R, V), requisito_atributo(R, A) ), Rs) ),
            AFavor),
    findall([R, P], ( member(R, V), penaliza(Mejor, R, P) ), EnContra),
    findall(R, ( member(R, V), sin_efecto(Mejor, R) ), SinEfecto).

/* sin_efecto(+Estilo, +R): R no aporta ni penaliza al estilo. Negacion por
   fallo con ambos argumentos ya instanciados. */
sin_efecto(E, R) :-
    \+ ( requisito_atributo(R, A), aporta(E, A, _) ),
    \+ penaliza(E, R, _).

/* ==========================================================================
   SECCION 7. CONSULTAS DE APOYO PARA LA INTERFAZ
   La interfaz arma sus controles a partir de la base, asi un requisito
   nuevo aparece en pantalla sin tocar Python.
   ========================================================================== */

/* requisitos_disponibles(-Lista): [[Requisito, Grupo, Etiqueta, Pregunta], ...]
   La pregunta se usa como ayuda (tooltip) de cada casilla. */
requisitos_disponibles(Lista) :-
    findall([R, C, T, P],
            ( requisito_categoria(R, C), etiqueta(R, T),
              ( pregunta(R, P) -> true ; P = '' ) ),
            Lista).

/* estilos_disponibles(-Lista): [[Id, Nombre, Descripcion], ...] */
estilos_disponibles(Lista) :-
    findall([E, N, D],
            ( estilo(E, N),
              ( descripcion_estilo(E, D) -> true ; D = '' ) ),
            Lista).

/* perfiles_disponibles(-Lista): [[Perfil, Requisitos], ...]. La interfaz
   los ofrece como "ejemplos rapidos" para cargar un caso tipico. */
perfiles_disponibles(Lista) :-
    findall([P, Rs], perfil(P, Rs), Lista).

/* ==========================================================================
   SECCION 8. APRENDIZAJE EN CALIENTE (adquisicion de conocimiento)
   El usuario describe un estilo nuevo eligiendo requisitos; Prolog valida,
   lo traduce a hechos aporta/3 e incompatible/2 y lo agrega con assertz/1.
   Como todas las reglas de las secciones 2 a 7 consultan estos hechos, el
   estilo nuevo compite en ranking, candidatos, descartes y "Que falta?"
   sin reiniciar. Python solo envia los datos y muestra la respuesta.
   ========================================================================== */

/* --- 8.1 Parametros del aprendizaje -------------------------------------- */
umbral_generalidad(70).    % porcentaje de requisitos en "Favorece" a partir
                           % del cual el estilo se considera demasiado general
descripcion_por_defecto('Arquitectura definida por el usuario.').
archivo_aprendizaje('conocimiento_aprendido.pl').

/* sin_tilde(+Codigo, -CodigoAscii): vocal con tilde, dieresis o acento
   (y enie / cedilla) -> letra ASCII. Se escriben como codigos numericos
   para que el .pl siga sin caracteres especiales. Solo minusculas, porque
   nombre_a_id/2 pasa el nombre a minuscula antes de traducir. */
sin_tilde(225, 0'a). sin_tilde(224, 0'a). sin_tilde(228, 0'a). sin_tilde(226, 0'a).
sin_tilde(233, 0'e). sin_tilde(232, 0'e). sin_tilde(235, 0'e). sin_tilde(234, 0'e).
sin_tilde(237, 0'i). sin_tilde(236, 0'i). sin_tilde(239, 0'i). sin_tilde(238, 0'i).
sin_tilde(243, 0'o). sin_tilde(242, 0'o). sin_tilde(246, 0'o). sin_tilde(244, 0'o).
sin_tilde(250, 0'u). sin_tilde(249, 0'u). sin_tilde(252, 0'u). sin_tilde(251, 0'u).
sin_tilde(241, 0'n). sin_tilde(231, 0'c).

/* separador_nombre(+Codigo): caracteres que separan palabras en el nombre
   y se convierten en "_" (espacio, guion y guion bajo). */
separador_nombre(32). separador_nombre(45). separador_nombre(95).

/* --- 8.2 Normalizacion de textos y del identificador --------------------- */

/* texto_limpio(+T, -Atomo): T como atomo, sin espacios al inicio ni al
   final y con espacios internos simples. Si T no es texto devuelve ''
   (asi la validacion lo reporta como nombre vacio). Corte = clausulas
   excluyentes. */
texto_limpio(T, A) :-
    ( atom(T) ; string(T) ), !,
    normalize_space(atom(A), T).
texto_limpio(_, '').

/* nombre_a_id(+Nombre, -Id): identificador derivado del nombre:
   minusculas, letras con tilde a su letra base, espacios y guiones a "_",
   cualquier otro simbolo se elimina, sin "_" repetidos ni en los bordes.
   'Mi Arquitectura de Prueba!' -> mi_arquitectura_de_prueba */
nombre_a_id(Nombre, Id) :-
    downcase_atom(Nombre, Min),
    atom_codes(Min, Cs),
    maplist(traducir_codigo, Cs, Partes),
    append(Partes, Cs1),
    colapsar_guiones(Cs1, Cs2),
    recortar_guiones(Cs2, Cs3),
    atom_codes(Id, Cs3).

/* traducir_codigo(+C, -Lista): 0 o 1 codigos ASCII que reemplazan a C.
   Los cortes hacen las clausulas excluyentes: la primera que reconoce el
   caracter decide, y la ultima (eliminar) solo se alcanza si ninguna lo
   reconocio. */
traducir_codigo(C, [C]) :- between(0'a, 0'z, C), !.
traducir_codigo(C, [C]) :- between(0'0, 0'9, C), !.
traducir_codigo(C, [B]) :- sin_tilde(C, B), !.
traducir_codigo(C, [95]) :- separador_nombre(C), !.
traducir_codigo(_, []).

/* colapsar_guiones(+Cs, -Rs): "__" -> "_" (95 es el codigo de "_"). El
   corte evita que, en backtracking, la clausula general deje pasar el
   guion repetido. */
colapsar_guiones([], []).
colapsar_guiones([95, 95|T], R) :- !,
    colapsar_guiones([95|T], R).
colapsar_guiones([C|T], [C|R]) :-
    colapsar_guiones(T, R).

/* recortar_guiones(+Cs, -Rs): quita "_" al inicio y al final. */
recortar_guiones(Cs, Rs) :-
    quitar_guiones_inicio(Cs, C1),
    reverse(C1, R1),
    quitar_guiones_inicio(R1, R2),
    reverse(R2, Rs).

quitar_guiones_inicio([95|T], R) :- !,       % corte: habia guion, se quita
    quitar_guiones_inicio(T, R).
quitar_guiones_inicio(L, L).

/* --- 8.3 Normalizacion de las listas que llegan desde Python ------------- */

/* favorece_normalizado(+F, -Pares): [[Req, Peso], ...] -> [Req-Peso, ...].
   Si F no es lista devuelve el atomo formato_invalido. Un elemento mal
   formado se conserva como mal(Elemento) para que la validacion lo
   reporte en vez de ignorarlo en silencio. Cortes = clausulas
   excluyentes. */
favorece_normalizado(F, Pares) :-
    is_list(F), !,
    maplist(par_favorece, F, Pares).
favorece_normalizado(_, formato_invalido).

par_favorece([R0, P], R-P) :-
    atom(R0), !,
    downcase_atom(R0, R).
par_favorece(X, mal(X)).

/* incompatibles_normalizados(+I, -Lista): requisitos en minuscula y sin
   repetidos, o formato_invalido si I no es lista. */
incompatibles_normalizados(I, Lista) :-
    is_list(I), !,
    maplist(req_incompatible, I, L0),
    list_to_set(L0, Lista).
incompatibles_normalizados(_, formato_invalido).

req_incompatible(R0, R) :-
    atom(R0), !,
    downcase_atom(R0, R).
req_incompatible(X, mal(X)).

/* peso_valido(+P): entero entre 1 y 3, la misma escala de aporta/3. */
peso_valido(P) :-
    integer(P), P >= 1, P =< 3.

/* ignorado_en_favorece(+Fav, -R): requisito marcado en "Favorece" que no
   exige ningun atributo de calidad (p. ej. procesos_largos). Negacion por
   fallo con R ya instanciado por member/2. */
ignorado_en_favorece(Fav, R) :-
    member(R-_, Fav),
    \+ requisito_atributo(R, _).

/* --- 8.4 Validacion ---------------------------------------------------------
   primer_error(+Nombre, +Id, +Fav, +Inc, -Error): revisa las reglas de
   validacion EN ORDEN y devuelve la primera que se incumple, o 'ninguno'.
   Cada clausula termina en corte: si su condicion se cumple ya no se deben
   probar las siguientes (son excluyentes por orden). Las condiciones con
   \+ se evaluan con la variable ya ligada por member/2, asi la negacion
   por fallo es segura. */
primer_error('', _, _, _, nombre_vacio) :- !.
primer_error(_, '', _, _, nombre_invalido) :- !.
primer_error(_, Id, _, _, nombre_duplicado(Id)) :-
    estilo(Id, _), !.
primer_error(_, _, formato_invalido, _, formato_invalido) :- !.
primer_error(_, _, _, formato_invalido, formato_invalido) :- !.
primer_error(_, _, Fav, Inc, formato_invalido) :-
    ( memberchk(mal(_), Fav) ; memberchk(mal(_), Inc) ), !.
primer_error(_, _, Fav, _, requisito_desconocido(R)) :-
    member(R-_, Fav), \+ requisito_conocido(R), !.
primer_error(_, _, _, Inc, requisito_desconocido(R)) :-
    member(R, Inc), \+ requisito_conocido(R), !.
primer_error(_, _, Fav, _, peso_invalido(R, P)) :-
    member(R-P, Fav), \+ peso_valido(P), !.
primer_error(_, _, [], _, sin_requisitos) :- !.
primer_error(_, _, Fav, Inc, requisito_en_ambas(R)) :-
    member(R-_, Fav), memberchk(R, Inc), !.
primer_error(_, _, Fav, _, sin_requisitos_utiles(Ign)) :-
    \+ ( member(R-_, Fav), requisito_atributo(R, _) ), !,
    findall(X, ignorado_en_favorece(Fav, X), Ign).
primer_error(_, _, _, _, ninguno).

/* --- 8.5 Ensenar un estilo -------------------------------------------------
   ensenar_estilo(+Nombre, +Descripcion, +Favorece, +Incompatibles, -Resultado)
     Favorece      = [[Requisito, Peso], ...]   (Peso entre 1 y 3)
     Incompatibles = [Requisito, ...]
     Resultado     = ok(Id, Ignorados) | error(Motivo)
   Ignorados son los requisitos de "Favorece" sin atributo de calidad: no
   se pueden traducir a aporta/3 y se informan al usuario.
   ensenar_estilo/6 devuelve ademas Advertencias (lista de textos) y es la
   que usa la interfaz. Una advertencia NO impide guardar. */
ensenar_estilo(Nombre, Descripcion, Favorece, Incompatibles, Resultado) :-
    ensenar_estilo(Nombre, Descripcion, Favorece, Incompatibles, Resultado, _).

ensenar_estilo(Nombre, Descripcion, Favorece, Incompatibles, Resultado, Advertencias) :-
    texto_limpio(Nombre, Nom),
    nombre_a_id(Nom, Id),
    favorece_normalizado(Favorece, Fav),
    incompatibles_normalizados(Incompatibles, Inc),
    primer_error(Nom, Id, Fav, Inc, Error),
    aplicar_ensenanza(Error, Id, Nom, Descripcion, Fav, Inc, Resultado, Advertencias).

/* aplicar_ensenanza(+Error, ...): si hubo error la base no se toca. El
   corte de la 1a clausula impide registrar un estilo invalido. */
aplicar_ensenanza(Error, _, _, _, _, _, error(Error), []) :-
    Error \== ninguno, !.
aplicar_ensenanza(ninguno, Id, Nom, Descripcion, Fav, Inc, ok(Id, Ignorados), Advertencias) :-
    texto_limpio(Descripcion, D0),
    descripcion_o_defecto(D0, Desc),
    findall(R, ignorado_en_favorece(Fav, R), Ignorados),
    registrar_estilo(Id, Nom, Desc, Fav, Inc),
    advertencias_estilo(Fav, Advertencias).

/* descripcion_o_defecto(+D0, -D): la descripcion es opcional. */
descripcion_o_defecto('', D) :- !,
    descripcion_por_defecto(D).
descripcion_o_defecto(D, D).

/* registrar_estilo(+Id, +Nombre, +Desc, +Fav, +Inc): traduce lo marcado a
   hechos. Cada requisito de "Favorece" se vuelve aporta(Id, Atributo, Peso)
   usando requisito_atributo/2. Si dos requisitos exigen el mismo atributo
   (equipo_grande y dominio_complejo -> modularidad) se guarda UN solo
   aporta/3 con el peso mayor, porque aporte_total/3 cuenta cada atributo
   una vez. Cada requisito de "Incompatible" se vuelve incompatible/2. */
registrar_estilo(Id, Nom, Desc, Fav, Inc) :-
    assertz(estilo_aprendido(Id)),
    assertz(estilo(Id, Nom)),
    assertz(descripcion_estilo(Id, Desc)),
    findall(A-P, ( member(R-P, Fav), requisito_atributo(R, A) ), AP),
    findall(A, member(A-_, AP), As0),
    sort(As0, As),
    forall(member(A, As),
           ( aggregate_all(max(P), member(A-P, AP), Max),
             assertz(aporta(Id, A, Max)) )),
    forall(member(R, Inc), assertz(incompatible(Id, R))).

/* advertencias_estilo(+Fav, -Advertencias): si se marco como "Favorece" mas
   del umbral_generalidad (70 %) de los requisitos conocidos, el estilo
   sumara puntos en casi cualquier caso y tendera a ganar siempre. El corte
   hace excluyente la clausula por defecto (sin advertencias). */
advertencias_estilo(Fav, [Texto]) :-
    length(Fav, N),
    aggregate_all(count, requisito_categoria(_, _), Total),
    umbral_generalidad(U),
    N * 100 > U * Total, !,
    format(atom(Texto),
           'Estilo demasiado general: favorece ~w de ~w requisitos (mas del ~w %), tendera a ganar siempre.',
           [N, Total, U]).
advertencias_estilo(_, []).

/* --- 8.6 Mensajes legibles (sin tildes, igual que las etiquetas) ---------
   mensaje_resultado(+Resultado, -Texto). Cortes = clausulas excluyentes. */
mensaje_resultado(ok(Id, []), T) :- !,
    estilo(Id, N),
    format(atom(T), 'Arquitectura "~w" guardada con el identificador ~w.', [N, Id]).
mensaje_resultado(ok(Id, Ign), T) :- !,
    estilo(Id, N),
    textos_requisitos(Ign, Txt),
    format(atom(T),
           'Arquitectura "~w" guardada con el identificador ~w. Se ignoraron en Favorece porque no exigen ningun atributo de calidad: ~w.',
           [N, Id, Txt]).
mensaje_resultado(error(M), T) :-
    mensaje_error(M, T), !.
mensaje_resultado(R, T) :-
    format(atom(T), 'Resultado no reconocido: ~w', [R]).

mensaje_error(nombre_vacio, 'Escriba un nombre para la arquitectura.').
mensaje_error(nombre_invalido, 'El nombre debe tener al menos una letra o un numero.').
mensaje_error(nombre_duplicado(Id), T) :-
    format(atom(T), 'Ya existe una arquitectura con el identificador ~w. Use otro nombre.', [Id]).
mensaje_error(formato_invalido, 'Los datos enviados no tienen el formato esperado.').
mensaje_error(requisito_desconocido(R), T) :-
    format(atom(T), 'El requisito ~w no esta en la base de conocimiento.', [R]).
mensaje_error(peso_invalido(R, P), T) :-
    texto_requisito(R, Tr),
    format(atom(T), 'El peso de "~w" debe estar entre 1 y 3 (llego ~w).', [Tr, P]).
mensaje_error(sin_requisitos, 'Marque al menos un requisito en la columna Favorece.').
mensaje_error(requisito_en_ambas(R), T) :-
    texto_requisito(R, Tr),
    format(atom(T), 'El requisito "~w" esta marcado como Favorece e Incompatible a la vez.', [Tr]).
mensaje_error(sin_requisitos_utiles(Ign), T) :-
    textos_requisitos(Ign, Txt),
    format(atom(T),
           'Ningun requisito de Favorece exige un atributo de calidad (~w). Marque al menos otro.',
           [Txt]).

/* tipo_resultado(+Resultado, -Tipo, -Id): permite que la interfaz lea la
   respuesta (ok / error) sin interpretar terminos compuestos. */
tipo_resultado(ok(Id, _), ok, Id).
tipo_resultado(error(_), error, '').

/* texto_requisito(+R, -T): etiqueta del requisito o, si no tiene, su id. */
texto_requisito(R, T) :-
    etiqueta(R, T), !.
texto_requisito(R, R).

textos_requisitos(Rs, Txt) :-
    maplist(texto_requisito, Rs, Ts),
    atomic_list_concat(Ts, ', ', Txt).

/* --- 8.7 Olvidar -----------------------------------------------------------
   olvidar_estilo(+Id): borra un estilo APRENDIDO con todos sus hechos.
   Falla si Id es del experto o no existe: la marca estilo_aprendido/1 es
   la unica puerta, asi nunca se borra conocimiento del experto. El corte
   evita reintentar despues de borrar. */
olvidar_estilo(Id) :-
    atom(Id),
    estilo_aprendido(Id), !,
    borrar_hechos_estilo(Id).

/* borrar_hechos_estilo(+Id): tambien borra las reglas expertas que hablan
   de ese estilo; si no, quedarian reglas apuntando a un estilo que ya no
   existe. */
borrar_hechos_estilo(Id) :-
    retractall(estilo_aprendido(Id)),
    retractall(estilo(Id, _)),
    retractall(descripcion_estilo(Id, _)),
    retractall(aporta(Id, _, _)),
    retractall(incompatible(Id, _)),
    retractall(penaliza(Id, _, _)),
    findall(R, clause(regla_experta(R, Id, _, _, _), _), Rs),
    forall(member(R, Rs), borrar_regla(R)).

/* olvidar_aprendizaje: borra TODO lo aprendido EN MEMORIA (estilos, reglas
   expertas y sinonimos); no toca ningun archivo. Lo usan las pruebas y la
   recarga. findall primero para no modificar estilo_aprendido/1 mientras
   se recorre. Siempre tiene exito. */
olvidar_aprendizaje :-
    findall(Id, estilo_aprendido(Id), Ids),
    forall(member(Id, Ids), borrar_hechos_estilo(Id)),
    retractall(regla_experta(_, _, _, _, _)),
    retractall(explicacion_regla(_, _)),
    borrar_sinonimos_aprendidos.

/* estilos_aprendidos(-Lista): [[Id, Nombre], ...] para la interfaz. */
estilos_aprendidos(Lista) :-
    findall([Id, N], ( estilo_aprendido(Id), estilo(Id, N) ), Lista).

/* --- 8.8 Persistencia ------------------------------------------------------
   ruta_aprendizaje(-Ruta): conocimiento_aprendido.pl en la carpeta de la
   base (directorio_base/1 se fija al consultar este archivo). */
/* Si las pruebas fijaron otra ruta (usar_archivo_aprendizaje/1) se usa esa;
   si no, la ruta por defecto. Corte = clausulas excluyentes. */
ruta_aprendizaje(Ruta) :-
    ruta_aprendizaje_fijada(Ruta), !.
ruta_aprendizaje(Ruta) :-
    ruta_aprendizaje_defecto(Ruta).

ruta_aprendizaje_defecto(Ruta) :-
    directorio_base(Dir),
    archivo_aprendizaje(Archivo),
    directory_file_path(Dir, Archivo, Ruta).

/* usar_archivo_aprendizaje(+Ruta): todo lo que se ensene a partir de ahora
   se escribe en Ruta (las pruebas usan un archivo temporal). */
usar_archivo_aprendizaje(Ruta0) :-
    atom_string(Ruta, Ruta0),
    retractall(ruta_aprendizaje_fijada(_)),
    assertz(ruta_aprendizaje_fijada(Ruta)).

/* limpiar_aprendizaje(+Ruta): punto de partida de cada prueba. Olvida lo
   aprendido en memoria, borra el archivo de PRUEBAS (y sus .bak/.tmp) y lo
   deja como archivo activo. Se niega a borrar el archivo real: si Ruta es
   la ruta por defecto, falla sin tocar nada. */
limpiar_aprendizaje(Ruta0) :-
    atom_string(Ruta, Ruta0),
    ruta_aprendizaje_defecto(Def),
    absolute_file_name(Ruta, A1),
    absolute_file_name(Def, A2),
    A1 \== A2,
    olvidar_aprendizaje,
    forall(( member(Suf, ['', '.bak', '.tmp']), atom_concat(Ruta, Suf, F),
             exists_file(F) ),
           delete_file(F)),
    usar_archivo_aprendizaje(Ruta).

/* guardar_aprendizaje: escribe todo lo aprendido en la ruta activa.
   guardar_aprendizaje(+Ruta): idem en otra ruta (las pruebas la usan para
   no tocar el archivo real). REESCRITURA ATOMICA: se escribe un .tmp, se
   copia el archivo anterior a .bak y el .tmp reemplaza al original con
   rename_file/2; si algo falla a mitad, el archivo original queda intacto.
   setup_call_cleanup cierra el archivo aunque falle la escritura. */
guardar_aprendizaje :-
    ruta_aprendizaje(Ruta),
    guardar_aprendizaje(Ruta).

guardar_aprendizaje(Ruta) :-
    atom_concat(Ruta, '.tmp', Tmp),
    setup_call_cleanup(open(Tmp, write, S, [encoding(utf8)]),
                       escribir_aprendizaje(S),
                       close(S)),
    reemplazar_archivo(Tmp, Ruta).

/* reemplazar_archivo(+Tmp, +Ruta): copia .bak del original (si existe) y
   renombra Tmp sobre Ruta. */
reemplazar_archivo(Tmp, Ruta) :-
    respaldar_archivo(Ruta),
    rename_file(Tmp, Ruta).

respaldar_archivo(Ruta) :-
    exists_file(Ruta), !,
    atom_concat(Ruta, '.bak', Bak),
    copy_file(Ruta, Bak).
respaldar_archivo(_).

escribir_cabecera(S) :-
    format(S, '/* conocimiento_aprendido.pl - generado por ArquiSelect.~n', []),
    format(S, '   Estilos, reglas expertas y sinonimos ensenados desde la interfaz.~n', []),
    format(S, '   Lo lee cargar_aprendizaje/1, que valida cada termino (no se~n', []),
    format(S, '   consulta directamente). */~n~n', []).

escribir_aprendizaje(S) :-
    escribir_cabecera(S),
    forall(estilo_aprendido(Id),
           ( forall(hecho_de_estilo(Id, H), portray_clause(S, H)),
             nl(S) )),
    forall(termino_de_regla(T), portray_clause(S, T)),
    forall(termino_de_sinonimo(T), portray_clause(S, T)).

/* termino_de_regla(-T): explicacion y clausula de cada regla experta, en
   el orden en que se ensenaron. */
termino_de_regla(T) :-
    clause(regla_experta(Id, E, Ef, P, R), B),
    ( T = explicacion_regla(Id, Ex), explicacion_regla(Id, Ex)
    ; T = (regla_experta(Id, E, Ef, P, R) :- B) ).

termino_de_sinonimo(T) :-
    lexico_aprendido(Toks),
    lexico(Toks, R, P),
    ( T = lexico_aprendido(Toks) ; T = lexico(Toks, R, P) ).

/* anexar_aprendizaje(+Terminos): agrega terminos al FINAL del archivo
   activo (modo append) con escritura atomica: se copia el archivo a un
   .tmp, se anexa ahi, se guarda .bak del original y el .tmp lo reemplaza.
   Si el archivo no existe se crea con su cabecera. */
anexar_aprendizaje(Terminos) :-
    ruta_aprendizaje(Ruta),
    anexar_aprendizaje(Ruta, Terminos).

anexar_aprendizaje(Ruta, Terminos) :-
    atom_concat(Ruta, '.tmp', Tmp),
    preparar_temporal(Ruta, Tmp),
    setup_call_cleanup(open(Tmp, append, S, [encoding(utf8)]),
                       ( nl(S), forall(member(T, Terminos), portray_clause(S, T)) ),
                       close(S)),
    reemplazar_archivo(Tmp, Ruta).

preparar_temporal(Ruta, Tmp) :-
    exists_file(Ruta), !,
    copy_file(Ruta, Tmp).
preparar_temporal(_, Tmp) :-
    setup_call_cleanup(open(Tmp, write, S, [encoding(utf8)]),
                       escribir_cabecera(S),
                       close(S)).

/* persistir_o_deshacer(+Escribir, +Deshacer, +Ok, -Resultado): ejecuta la
   escritura en disco; si falla o lanza excepcion, deshace lo hecho en
   memoria y devuelve error(persistencia(Motivo)). Asi memoria y archivo
   no difieren nunca. */
persistir_o_deshacer(Escribir, Deshacer, Ok, Resultado) :-
    catch(( call(Escribir) -> Res = Ok ; Res = error(persistencia(fallo)) ),
          E,
          ( message_to_codes_seguro(E, Txt), Res = error(persistencia(Txt)) )),
    ( Res = error(_) -> call(Deshacer) ; true ),
    Resultado = Res.

message_to_codes_seguro(E, Txt) :-
    catch(term_to_atom(E, Txt), _, Txt = excepcion).

/* hecho_de_estilo(+Id, -Hecho): todos los hechos que describen un estilo. */
hecho_de_estilo(Id, estilo_aprendido(Id)).
hecho_de_estilo(Id, estilo(Id, N))             :- estilo(Id, N).
hecho_de_estilo(Id, descripcion_estilo(Id, D)) :- descripcion_estilo(Id, D).
hecho_de_estilo(Id, aporta(Id, A, P))          :- aporta(Id, A, P).
hecho_de_estilo(Id, incompatible(Id, R))       :- incompatible(Id, R).
hecho_de_estilo(Id, penaliza(Id, R, P))        :- penaliza(Id, R, P).

/* cargar_aprendizaje(+Ruta): lo llama la interfaz al iniciar y despues de
   reconsultar la base. Primero olvida lo aprendido, asi nunca se duplica
   nada aunque se llame dos veces.
   El archivo NO se consulta: se leen sus terminos y solo se aceptan los
   hechos de la lista blanca, con tipos validos y para ids que no sean del
   experto. Asi un archivo editado a mano no puede redefinir reglas.
   cargar_aprendizaje(+Ruta, -Estado): Estado = cargado(N) | sin_archivo |
   danado(Respaldo). Si el archivo esta danado se renombra a Respaldo, la
   base queda solo con lo del experto y la aplicacion arranca igual. */
cargar_aprendizaje(Ruta) :-
    cargar_aprendizaje(Ruta, _).

/* estado_carga(+Estado, -Tipo, -Detalle): lectura simple del estado para
   la interfaz (cuantos estilos se cargaron o donde quedo el respaldo). */
estado_carga(cargado(N), cargado, N).
estado_carga(sin_archivo, sin_archivo, 0).
estado_carga(danado(Respaldo), danado, Respaldo).

cargar_aprendizaje(Ruta, Estado) :-
    olvidar_aprendizaje,
    cargar_archivo_aprendizaje(Ruta, Estado).

/* Cortes = clausulas excluyentes: sin archivo / leido bien / danado. */
cargar_archivo_aprendizaje(Ruta, sin_archivo) :-
    \+ exists_file(Ruta), !.
cargar_archivo_aprendizaje(Ruta, Estado) :-
    catch(leer_terminos_archivo(Ruta, Terminos), _Error, fail), !,
    incorporar_terminos(Terminos),
    aggregate_all(count, estilo_aprendido(_), N),
    Estado = cargado(N).
cargar_archivo_aprendizaje(Ruta, danado(Respaldo)) :-
    atom_concat(Ruta, '.danado', Respaldo),
    catch(( exists_file(Respaldo) -> delete_file(Respaldo) ; true ), _, true),
    catch(rename_file(Ruta, Respaldo), _, true).

leer_terminos_archivo(Ruta, Terminos) :-
    setup_call_cleanup(open(Ruta, read, S, [encoding(utf8)]),
                       leer_terminos(S, Terminos),
                       close(S)).

/* leer_terminos(+Stream, -Terminos): lee hasta end_of_file. Un error de
   sintaxis lanza excepcion y se atrapa en cargar_archivo_aprendizaje/2.
   Corte = fin de archivo excluye seguir leyendo. */
leer_terminos(S, Terminos) :-
    read_term(S, T, []),
    leer_terminos_resto(T, S, Terminos).

leer_terminos_resto(end_of_file, _, []) :- !.
leer_terminos_resto(T, S, [T|R]) :-
    leer_terminos(S, R).

/* incorporar_terminos(+Ts): agrega los estilos marcados como aprendidos.
   \+ estilo(Id, _) con Id ya ligado: un id del experto nunca se acepta. */
incorporar_terminos(Ts) :-
    findall(Id,
            ( member(estilo_aprendido(Id), Ts), atom(Id), \+ estilo(Id, _) ),
            Ids0),
    list_to_set(Ids0, Ids),
    forall(member(Id, Ids), incorporar_estilo(Id, Ts)),
    incorporar_reglas(Ts),          % despues de los estilos: una regla puede
    incorporar_sinonimos(Ts).       % hablar de un estilo aprendido

/* incorporar_reglas(+Ts): una regla del archivo se acepta solo si su cuerpo
   tiene EXACTAMENTE la forma que construye construir_clausula/8 (se
   reconoce por unificacion, NUNCA se ejecuta el cuerpo leido) y si pasa la
   misma validacion que ensenar_regla/8. La clausula se vuelve a construir
   desde los datos validados. Lo que no cumple se ignora. */
incorporar_reglas(Ts) :-
    forall(( member((H :- B), Ts),
             H = regla_experta(Id, E, Ef, P, R),
             cuerpo_regla(B, R, Conds, Excls),
             memberchk(explicacion_regla(Id, Ex), Ts) ),
           incorporar_regla(Id, Ex, E, Ef, P, Conds, Excls)).

incorporar_regla(Id, Ex, E, Ef, P, Conds, Excls) :-
    preparar_regla(Id, Ex, E, Ef, P, Conds, Excls, Datos, Error),
    Error == ninguno, !,
    registrar_regla(Datos).
incorporar_regla(_, _, _, _, _, _, _).

/* incorporar_sinonimos(+Ts): un sinonimo se acepta si esta marcado como
   aprendido, sus tokens son atomos o enteros, apunta a un requisito
   conocido, tiene polaridad valida y la frase no existe ya en el lexico. */
incorporar_sinonimos(Ts) :-
    forall(( member(lexico_aprendido(T), Ts),
             is_list(T), T \== [],
             forall(member(X, T), ( atom(X) ; integer(X) )),
             memberchk(lexico(T, R, P), Ts),
             requisito_conocido(R),
             memberchk(P, [afirma, niega]),
             \+ lexico(T, _, _) ),
           ( assertz(lexico_aprendido(T)), assertz(lexico(T, R, P)) )).

/* incorporar_estilo(+Id, +Ts): un estilo sin nombre valido no se carga
   (2a clausula). El corte de la 1a evita tomar un segundo nombre. */
incorporar_estilo(Id, Ts) :-
    member(estilo(Id, Nom), Ts), atom(Nom), !,
    assertz(estilo_aprendido(Id)),
    assertz(estilo(Id, Nom)),
    descripcion_cargada(Id, Ts, Desc),
    assertz(descripcion_estilo(Id, Desc)),
    forall(( member(aporta(Id, A, P), Ts), atom(A), peso_valido(P) ),
           assertz(aporta(Id, A, P))),
    forall(( member(incompatible(Id, R), Ts), atom(R), requisito_conocido(R) ),
           assertz(incompatible(Id, R))),
    forall(( member(penaliza(Id, R, P), Ts), atom(R), requisito_conocido(R),
             peso_valido(P) ),
           assertz(penaliza(Id, R, P))).
incorporar_estilo(_, _).

/* descripcion_cargada(+Id, +Ts, -D): descripcion guardada o la de defecto. */
descripcion_cargada(Id, Ts, D) :-
    member(descripcion_estilo(Id, D), Ts), atom(D), !.
descripcion_cargada(_, _, D) :-
    descripcion_por_defecto(D).

/* ==========================================================================
   SECCION 9. MODO EXPERTO: REGLAS INYECTADAS EN CALIENTE (ENTREGABLE 3)
   El experto describe una regla con datos (id, explicacion, condiciones,
   exclusiones, efecto, peso y estilo). Python SOLO envia esos datos: aqui
   se validan y se construye la clausula, que se inserta con assertz/1 y se
   anexa a conocimiento_aprendido.pl con portray_clause/2. Nunca se ejecuta
   texto Prolog escrito por el usuario: la clausula se arma con terminos,
   no con texto, asi que no hay inyeccion posible.

   Forma de cada regla (una CLAUSULA real, no un hecho):
     regla_experta(Id, Estilo, Efecto, Peso, Reqs) :-
         contiene_todos([cond1, cond2], Reqs),
         \+ contiene_alguno([excl1], Reqs).
   Efecto recomendar: puntaje/3 suma Peso (bonus_reglas/3).
   Efecto descartar : motivo_descarte/3 excluye el estilo (Peso = 0).
   ========================================================================== */

/* --- 9.1 Parametros ------------------------------------------------------- */
peso_regla_minimo(1).
peso_regla_maximo(5).
efecto_regla(recomendar).
efecto_regla(descartar).

/* --- 9.2 Construccion y lectura de la clausula ---------------------------
   construir_clausula(+Id, +Estilo, +Efecto, +Peso, +Conds, +Excls, -Clausula)
   Sin exclusiones no se agrega el \+ (cuerpo mas simple). Corte = clausulas
   excluyentes. */
construir_clausula(Id, E, Ef, P, Conds, [],
                   (regla_experta(Id, E, Ef, P, R) :- contiene_todos(Conds, R))) :- !.
construir_clausula(Id, E, Ef, P, Conds, Excls,
                   (regla_experta(Id, E, Ef, P, R) :-
                        contiene_todos(Conds, R),
                        \+ contiene_alguno(Excls, R))).

/* cuerpo_regla(+Cuerpo, +R, -Conds, -Excls): reconoce un cuerpo con la forma
   exacta de construir_clausula/7 (R debe ser la MISMA variable de la
   cabeza, por eso ==). Lo usan el listado y la carga del archivo; jamas se
   llama al cuerpo leido. Corte = la forma sin exclusiones no se reintenta. */
cuerpo_regla(contiene_todos(C, R0), R, C, []) :-
    R0 == R, !.
cuerpo_regla((contiene_todos(C, R0), \+ contiene_alguno(X, R1)), R, C, X) :-
    R0 == R, R1 == R.

/* --- 9.3 Normalizacion y validacion ------------------------------------
   preparar_regla(+Id0, +Expl0, +Estilo0, +Efecto0, +Peso0, +Conds0, +Excls0,
                  -Datos, -Error)
   Normaliza lo que llega de Python y devuelve el primer error o 'ninguno'.
   Datos = regla(Id, Expl, Estilo, Efecto, Peso, Conds, Excls). Para
   "descartar" el peso no se usa y se guarda 0. */
preparar_regla(Id0, Expl0, E0, Ef0, P0, C0, X0, regla(Id, Ex, E, Ef, P, C, X), Error) :-
    texto_limpio(Id0, IdT),
    nombre_a_id(IdT, Id),
    texto_limpio(Expl0, Ex),
    atomo_minuscula(E0, E),
    atomo_minuscula(Ef0, Ef),
    incompatibles_normalizados(C0, C),
    incompatibles_normalizados(X0, X),
    peso_segun_efecto(Ef, P0, P),
    primer_error_regla(Id, Ex, E, Ef, P, C, X, Error).

peso_segun_efecto(descartar, _, 0) :- !.
peso_segun_efecto(_, P, P).

/* primer_error_regla(...): validaciones EN ORDEN; cada clausula termina en
   corte porque la primera que falla decide (son excluyentes por orden).
   Las \+ se evaluan con los argumentos ya ligados. */
primer_error_regla('', _, _, _, _, _, _, id_invalido) :- !.
primer_error_regla(Id, _, _, _, _, _, _, id_duplicado(Id)) :-
    clause(regla_experta(Id, _, _, _, _), _), !.
primer_error_regla(Id, _, _, _, _, _, _, id_reservado(Id)) :-
    ( requisito_conocido(Id) ; estilo(Id, _) ), !.
primer_error_regla(_, '', _, _, _, _, _, explicacion_vacia) :- !.
primer_error_regla(_, _, _, _, _, formato_invalido, _, formato_invalido) :- !.
primer_error_regla(_, _, _, _, _, _, formato_invalido, formato_invalido) :- !.
primer_error_regla(_, _, _, _, _, C, X, formato_invalido) :-
    ( memberchk(mal(_), C) ; memberchk(mal(_), X) ), !.
primer_error_regla(_, _, E, _, _, _, _, estilo_desconocido(E)) :-
    \+ estilo(E, _), !.
primer_error_regla(_, _, _, Ef, _, _, _, efecto_invalido(Ef)) :-
    \+ efecto_regla(Ef), !.
primer_error_regla(_, _, _, _, _, [], _, sin_condiciones) :- !.
primer_error_regla(_, _, _, _, _, C, _, requisito_desconocido(R)) :-
    member(R, C), \+ requisito_conocido(R), !.
primer_error_regla(_, _, _, _, _, _, X, requisito_desconocido(R)) :-
    member(R, X), \+ requisito_conocido(R), !.
primer_error_regla(_, _, _, _, _, C, X, requisito_en_ambas(R)) :-
    member(R, C), memberchk(R, X), !.
primer_error_regla(_, _, _, _, _, C, _, condiciones_contradictorias(A, B)) :-
    member(A, C), member(B, C), excluyentes(A, B), !.
primer_error_regla(_, _, _, recomendar, P, _, _, peso_invalido(P)) :-
    \+ peso_regla_valido(P), !.
primer_error_regla(_, _, E, Ef, _, C, X, regla_repetida(Otra)) :-
    msort(C, Cs), msort(X, Xs),
    clause(regla_experta(Otra, E, Ef, _, R), B),
    cuerpo_regla(B, R, C2, X2),
    msort(C2, Cs), msort(X2, Xs), !.
primer_error_regla(_, _, _, _, _, _, _, ninguno).

peso_regla_valido(P) :-
    integer(P),
    peso_regla_minimo(Min), peso_regla_maximo(Max),
    P >= Min, P =< Max.

/* --- 9.4 Ensenar una regla ------------------------------------------------
   ensenar_regla(+Id, +Explicacion, +Estilo, +Efecto, +Peso, +Condiciones,
                 +Exclusiones, -Resultado)      Resultado = ok(Id) | error(M)
   Con error la base no se toca. Si es valida: assertz/1 de la clausula y
   de su explicacion, y se ANEXA al archivo de aprendizaje; si el disco
   falla se retracta todo (persistir_o_deshacer/4). */
ensenar_regla(Id0, Expl0, E0, Ef0, P0, C0, X0, Resultado) :-
    preparar_regla(Id0, Expl0, E0, Ef0, P0, C0, X0, Datos, Error),
    aplicar_regla(Error, Datos, Resultado).

aplicar_regla(Error, _, error(Error)) :-
    Error \== ninguno, !.
aplicar_regla(ninguno, Datos, Resultado) :-
    Datos = regla(Id, Ex, E, Ef, P, C, X),
    registrar_regla(Datos),
    construir_clausula(Id, E, Ef, P, C, X, Clausula),
    persistir_o_deshacer(anexar_aprendizaje([explicacion_regla(Id, Ex), Clausula]),
                         borrar_regla(Id),
                         ok(Id), Resultado).

/* registrar_regla(+Datos): la clausula se inserta con assertz/1. */
registrar_regla(regla(Id, Ex, E, Ef, P, C, X)) :-
    construir_clausula(Id, E, Ef, P, C, X, Clausula),
    assertz(Clausula),
    assertz(explicacion_regla(Id, Ex)).

/* --- 9.5 Eliminar ---------------------------------------------------------
   olvidar_regla(+Id): retract de la clausula y REESCRITURA atomica del
   archivo sin ella. Falla si no existe esa regla (el corte evita
   reintentar despues de borrar). */
olvidar_regla(Id0) :-
    atomo_minuscula(Id0, Id),
    clause(regla_experta(Id, _, _, _, _), _), !,
    borrar_regla(Id),
    guardar_aprendizaje.

borrar_regla(Id) :-
    retractall(regla_experta(Id, _, _, _, _)),
    retractall(explicacion_regla(Id, _)).

/* --- 9.6 Consultas para la interfaz ---------------------------------------
   reglas_aprendidas(-Lista): [[Id, Estilo, Efecto, Peso, Conds, Excls,
   Explicacion], ...] leidas de las clausulas mismas (clause/2). */
reglas_aprendidas(Lista) :-
    findall([Id, E, Ef, P, C, X, Ex],
            ( clause(regla_experta(Id, E, Ef, P, R), B),
              cuerpo_regla(B, R, C, X),
              explicacion_regla(Id, Ex) ),
            Lista).

/* reglas_expertas_disparadas(+Reqs, -Lista): [[Id, Estilo, Efecto, Peso,
   Explicacion], ...] reglas que se disparan con esos requisitos. */
reglas_expertas_disparadas(Reqs, Lista) :-
    preparar_requisitos(Reqs, V),
    findall([Id, E, Ef, P, Ex],
            ( regla_experta(Id, E, Ef, P, V), explicacion_regla(Id, Ex) ),
            Lista).

/* clausula_regla_texto(+Id, -Texto): la clausula tal como queda escrita en
   el archivo (portray_clause/2), para mostrarla en la interfaz. */
clausula_regla_texto(Id, Texto) :-
    clause(regla_experta(Id, E, Ef, P, R), B), !,
    with_output_to(string(Texto),
                   portray_clause((regla_experta(Id, E, Ef, P, R) :- B))).

/* resumen_aprendizaje(-Estilos, -Reglas, -Sinonimos): cantidades. */
resumen_aprendizaje(NE, NR, NS) :-
    aggregate_all(count, estilo_aprendido(_), NE),
    aggregate_all(count, clause(regla_experta(_, _, _, _, _), _), NR),
    aggregate_all(count, lexico_aprendido(_), NS).

/* --- 9.7 Mensajes legibles (sin tildes) -----------------------------------
   mensaje_regla(+Resultado, -Texto). Cortes = clausulas excluyentes. */
mensaje_regla(ok(Id), T) :- !,
    format(atom(T), 'Regla "~w" guardada. Ya forma parte del razonamiento y del archivo de aprendizaje.', [Id]).
mensaje_regla(error(M), T) :-
    mensaje_error_regla(M, T), !.
mensaje_regla(R, T) :-
    format(atom(T), 'Resultado no reconocido: ~w', [R]).

mensaje_error_regla(id_invalido, 'Escriba un identificador para la regla (letras o numeros).').
mensaje_error_regla(id_duplicado(Id), T) :-
    format(atom(T), 'Ya existe una regla con el identificador ~w.', [Id]).
mensaje_error_regla(id_reservado(Id), T) :-
    format(atom(T), 'El identificador ~w ya es un requisito o un estilo; use otro.', [Id]).
mensaje_error_regla(explicacion_vacia,
    'La explicacion es obligatoria: diga en lenguaje claro por que se aplica la regla.').
mensaje_error_regla(formato_invalido, 'Los datos enviados no tienen el formato esperado.').
mensaje_error_regla(estilo_desconocido(E), T) :-
    format(atom(T), 'El estilo ~w no existe en la base.', [E]).
mensaje_error_regla(efecto_invalido(E), T) :-
    format(atom(T), 'Efecto invalido: ~w (use recomendar o descartar).', [E]).
mensaje_error_regla(sin_condiciones, 'Elija al menos una condicion (requisito que debe cumplirse).').
mensaje_error_regla(requisito_desconocido(R), T) :-
    format(atom(T), 'El requisito ~w no esta en la base de conocimiento.', [R]).
mensaje_error_regla(requisito_en_ambas(R), T) :-
    texto_requisito(R, Tr),
    format(atom(T), '"~w" esta a la vez en condiciones y en exclusiones.', [Tr]).
mensaje_error_regla(condiciones_contradictorias(A, B), T) :-
    format(atom(T), 'Las condiciones ~w y ~w no pueden darse juntas: la regla nunca se dispararia.', [A, B]).
mensaje_error_regla(peso_invalido(P), T) :-
    peso_regla_minimo(Min), peso_regla_maximo(Max),
    format(atom(T), 'El peso debe ser un entero entre ~w y ~w (llego ~w).', [Min, Max, P]).
mensaje_error_regla(regla_repetida(Otra), T) :-
    format(atom(T), 'La regla ~w ya tiene las mismas condiciones, exclusiones, efecto y estilo.', [Otra]).
mensaje_error_regla(persistencia(E), T) :-
    format(atom(T), 'No se pudo escribir el archivo de aprendizaje (~w). No se guardo nada.', [E]).

/* tipo_resultado_regla(+Resultado, -Tipo): ok | error, sin terminos
   compuestos para Python. */
tipo_resultado_regla(ok(_), ok).
tipo_resultado_regla(error(_), error).

/* ==========================================================================
   SECCION 10. CONTRADICCIONES EN LA ENTRADA
   Antes de recomendar se revisa que los requisitos no se contradigan.
   - dura   : la entrada es imposible. BLOQUEA: diagnosticar_arquitectura/9
              y que_falta/6 no dan recomendacion (ver sus primeras clausulas).
   - tension: la entrada es posible pero costosa o arriesgada. Solo ADVIERTE:
              el diagnostico se calcula igual.
   Los mensajes van sin tildes, como el resto de la base (la interfaz las
   agrega al mostrarlos).
   ========================================================================== */

/* --- 10.1 Hechos: contradiccion(ReqA, ReqB, Tipo, Mensaje) ---------------
   Cada par se escribe UNA sola vez: conflicto/6 busca los dos requisitos
   con memberchk/2, asi que el orden en que los marco el usuario no importa.
   La primera clausula reutiliza excluyentes/2 (seccion 1.11), de modo que un
   par excluyente nuevo se vuelve contradiccion dura sin tocar esta seccion.
   excluyentes/2 liga A y B antes de format/3. */
contradiccion(A, B, dura, Mensaje) :-
    excluyentes(A, B),
    format(atom(Mensaje),
           'Contradiccion: ~w y ~w son excluyentes; el proyecto no puede tener los dos.',
           [A, B]).
contradiccion(latencia_critica, procesos_largos, dura,
    'Contradiccion: latencia_critica exige responder en milisegundos y procesos_largos implica tareas de varios minutos.').
contradiccion(disponibilidad_alta, presupuesto_bajo, tension,
    'Tension: disponibilidad_alta (24/7, redundancia) suele costar mas de lo que permite presupuesto_bajo.').
contradiccion(consistencia_estricta, integracion_asincrona, tension,
    'Tension: integracion_asincrona por mensajes da consistencia eventual, lo que dificulta consistencia_estricta.').

/* --- 10.2 conflicto(+V, +N, -A, -B, -Tipo, -Mensaje) ---------------------
   V = requisitos afirmados y N = negados ("no aplica"), ya validados.
   1a clausula: un par de 10.1 con los dos requisitos presentes en V.
   2a clausula (dura): el mismo requisito esta afirmado y negado a la vez.
   member/2 recorre V (puede haber varios); memberchk/2 solo comprueba,
   porque N no tiene repetidos y basta una coincidencia.
   Sin cortes: findall/3 necesita TODAS las soluciones. */
conflicto(V, _, A, B, Tipo, Mensaje) :-
    contradiccion(A, B, Tipo, Mensaje),
    memberchk(A, V),
    memberchk(B, V).
conflicto(V, N, R, R, dura, Mensaje) :-
    member(R, V),
    memberchk(R, N),
    format(atom(Mensaje),
           'Contradiccion: ~w esta marcado como requisito y tambien como "no aplica".',
           [R]).

/* --- 10.3 contradicciones(+Reqs, +Negados, -Lista) -----------------------
   PREDICADO NUEVO. Lista = [[A, B, Tipo, Mensaje], ...] (lista de listas,
   facil de leer en Python). Pasa por preparar_requisitos/2 como los demas
   predicados que llama Python: minusculas, sin repetidos, sin desconocidos.
   Sin contradicciones -> []. findall/3 nunca falla. */
contradicciones(Reqs, Negados, Lista) :-
    preparar_requisitos(Reqs, V),
    preparar_requisitos(Negados, N),
    findall([A, B, Tipo, M], conflicto(V, N, A, B, Tipo, M), Lista).

/* --- 10.4 consistencia_entrada(+Reqs, +Negados, -Estado, -Lista) ---------
   PREDICADO NUEVO. Estado = bloqueado | advertencia | consistente. */
consistencia_entrada(Reqs, Negados, Estado, Lista) :-
    contradicciones(Reqs, Negados, Lista),
    estado_consistencia(Lista, Estado).

/* estado_consistencia(+Lista, -Estado): la PRIMERA clausula que se cumple
   decide. Los cortes hacen las clausulas excluyentes: si hay una dura no se
   debe responder tambien 'advertencia' al pedir otra solucion. La ultima es
   el caso general (sin contradicciones). Se compara con \== en vez de \+
   porque Lista ya esta ligada: basta comparar terminos. */
estado_consistencia(Lista, bloqueado) :-
    memberchk([_, _, dura, _], Lista), !.
estado_consistencia(Lista, advertencia) :-
    Lista \== [], !.
estado_consistencia(_, consistente).

/* --- 10.5 bloqueo_duro(+Reqs, +Negados, -Mensajes) -----------------------
   Tiene exito solo si hay al menos una contradiccion dura; Mensajes son
   sus textos. Lo usan las primeras clausulas de diagnosticar_arquitectura/9
   (con Negados = [], porque su firma no recibe negados) y de que_falta/6. */
bloqueo_duro(Reqs, Negados, Mensajes) :-
    contradicciones(Reqs, Negados, Lista),
    findall(M, member([_, _, dura, M], Lista), Mensajes),
    Mensajes \== [].
