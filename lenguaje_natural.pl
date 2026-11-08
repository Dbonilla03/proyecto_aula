/* ==========================================================================
   ArquiSelect - Modulo de lenguaje natural (ENTREGABLE 3, parte A)
   Lo carga base_conocimiento.pl con ensure_loaded/1.

   El usuario describe su proyecto con sus palabras ("somos un equipo de
   tres personas con poco presupuesto...") y este modulo lo traduce a los
   mismos ids de requisito que usan las casillas. Python solo envia el
   texto y muestra lo que se devuelve: la normalizacion, la gramatica, el
   lexico y las restricciones numericas viven aqui.

   Flujo:  Texto --normalizar_texto/2--> Tokens --phrase(oracion(A))--> Arbol
           Arbol --menciones/resolucion--> Requisitos, Negados, NoEntendido
   ========================================================================== */

:- encoding(utf8).

/* --- N.0 Predicados dinamicos --------------------------------------------
        lexico(Tokens, Requisito, Polaridad): el vocabulario. Es dinamico
        para que el Modo Experto agregue sinonimos en caliente (assertz).
        lexico_aprendido(Tokens) marca los sinonimos agregados por el
        experto: solo esos se pueden olvidar o se escriben en el archivo de
        aprendizaje. umbral_numerico/3 es dinamico para poder ajustarlo sin
        tocar la gramatica. --------------------------------------------- */
:- dynamic lexico/3.
:- dynamic lexico_aprendido/1.
:- dynamic umbral_numerico/3.

/* ==========================================================================
   SECCION N1. NORMALIZACION (texto -> lista de tokens)
   ========================================================================== */

/* normalizar_texto(+Texto, -Tokens): minusculas, sin tildes, signos
   separados y numeros convertidos a enteros. Acepta atomo o string; con
   cualquier otra cosa (variable, numero, lista) devuelve [] en lugar de
   fallar o lanzar excepcion. El corte deja una sola tokenizacion (la
   gramatica de tokens es determinista por construccion, el corte evita
   puntos de eleccion abiertos que Python no necesita). */
normalizar_texto(Texto, Tokens) :-
    texto_a_codigos(Texto, Cs0), !,
    maplist(codigo_normalizado, Cs0, Cs),
    phrase(tokens(Tokens), Cs), !.
normalizar_texto(_, []).

/* texto_a_codigos(+T, -Codigos): string_lower/2 tambien baja las letras
   con tilde (A con tilde -> a con tilde). Solo atomos y strings. */
texto_a_codigos(T, Cs) :-
    ( atom(T) ; string(T) ), !,
    string_lower(T, Min),
    string_codes(Min, Cs).

/* codigo_normalizado(+C, -B): reutiliza sin_tilde/2 de la seccion 8 de la
   base (vocal con tilde -> vocal, enie -> n). Corte: si hubo traduccion no
   se aplica la clausula identidad. */
codigo_normalizado(C, B) :-
    sin_tilde(C, B), !.
codigo_normalizado(C, C).

/* --- N1.1 Gramatica de tokens (DCG sobre codigos) -------------------------
   Cada token es: una palabra (letras), un entero (digitos, admite punto de
   miles "1.000"), una coma (conector) o un grupo de simbolos raros (que
   terminara en NoEntendido). Espacios y signos de puntuacion separan. Los
   cortes despues de reconocer un token hacen determinista la division:
   una palabra se toma completa (maximal munch) y no se reintenta partirla. */
tokens(Ts) --> separadores, tokens_resto(Ts).

tokens_resto([T|Ts]) --> token(T), !, separadores, tokens_resto(Ts).
tokens_resto([])     --> [].

token(P) --> letra(C), letras(Cs), { atom_codes(P, [C|Cs]) }.
token(N) --> digito(D), digitos(Ds), { number_codes(N, [D|Ds]) }.
token(',') --> [C], { coma(C) }.
token(S) --> simbolo(C), simbolos(Cs), { atom_codes(S, [C|Cs]) }.

letras([C|Cs]) --> letra(C), !, letras(Cs).
letras([])     --> [].

/* digitos//1: "1.000.000" -> 1000000. El punto solo se acepta si lo siguen
   exactamente tres digitos (punto de miles); "2.5" queda como 2 y 5. */
digitos([D|Ds]) --> digito(D), !, digitos(Ds).
digitos(Ds)     --> [0'.], digito(A), digito(B), digito(C), \+ digito(_), !,
                    digitos(R), { Ds = [A, B, C|R] }.
digitos([])     --> [].

simbolos([C|Cs]) --> simbolo(C), !, simbolos(Cs).
simbolos([])     --> [].

separadores --> [C], { separador(C) }, !, separadores.
separadores --> [].

letra(C)   --> [C], { es_letra(C) }.
digito(C)  --> [C], { between(0'0, 0'9, C) }.
simbolo(C) --> [C], { es_simbolo(C) }.

/* Clases de caracteres. es_letra/1 admite letras no ASCII que no tengan
   traduccion (p. ej. griego) para no partirlas en simbolos. */
es_letra(C) :- between(0'a, 0'z, C), !.
es_letra(C) :- C > 127, code_type(C, alpha), \+ code_type(C, digit(_)).

coma(0',).
coma(0';).

/* separador(C): espacios, saltos de linea y puntuacion de oracion. */
separador(C) :- code_type(C, space), !.
separador(C) :- memberchk(C, `.:!?()"'[]{}-/\\_`), !.
separador(C) :- memberchk(C, [161, 191, 171, 187]).   % inv. ! ?, comillas latinas

/* es_simbolo(C): todo lo que no es letra, digito, coma ni separador. La
   negacion por fallo se aplica con C ya ligado por el DCG. */
es_simbolo(C) :-
    \+ es_letra(C),
    \+ between(0'0, 0'9, C),
    \+ coma(C),
    \+ separador(C).

/* ==========================================================================
   SECCION N2. CATEGORIAS GRAMATICALES
   ========================================================================== */

/* conector(Palabra): unen sintagmas. La coma llega como el token ','. */
conector(y).  conector(e).  conector(ademas).  conector(tambien).
conector(con). conector(pero). conector(',').  conector(o).

/* negador(Palabra): invierten la polaridad del nucleo que les sigue. */
negador(no). negador(sin). negador(ni). negador(tampoco). negador(nunca).

/* relleno(Palabra): articulos, preposiciones, pronombres, verbos comunes y
   sustantivos genericos ("el equipo", "la aplicacion") que no aportan un
   requisito por si solos. Se omiten sin error. */
relleno(P) :- memberchk(P, [
    el, la, los, las, lo, un, una, unos, unas, al, del, de, a, en, que, se,
    nos, nuestro, nuestra, nuestros, nuestras, su, sus, mi, mis,
    nosotros, nosotras, yo, ellos, usted, ustedes,
    es, son, somos, sera, seran, ser, estar, esta, estan, estamos, este, estos,
    tener, tenemos, tiene, tienen, tendra, tendran, tendremos, tengo,
    hay, habra, haber, contamos, cuenta, cuentan,
    necesitamos, necesita, necesitan, necesito, necesitara, necesitaria,
    requiere, requieren, requerimos, requiero, queremos, quiero, quiere,
    buscamos, esperamos, debe, deben, debemos, deberia, deberan,
    va, van, vamos, ir, poder, puede, pueden, podemos, pueda, puedan,
    para, por, como, muy, bastante, tan, algo, todo, toda, todos, todas,
    equipo, sistema, aplicacion, app, proyecto, plataforma, software,
    producto, empresa, solucion, servicio, cliente, negocio
    ]).

/* palabra_funcional(P): palabra que se puede omitir sin que cuente como
   "no entendida" (relleno, conector o negador suelto). */
palabra_funcional(P) :- relleno(P), !.
palabra_funcional(P) :- conector(P), !.
palabra_funcional(P) :- negador(P).

/* numeral(Palabra, Valor): numeros escritos con letras. "un/una" se dejan
   fuera a proposito: casi siempre son articulos ("una persona usara..."). */
numeral(uno, 1).      numeral(dos, 2).        numeral(tres, 3).
numeral(cuatro, 4).   numeral(cinco, 5).      numeral(seis, 6).
numeral(siete, 7).    numeral(ocho, 8).       numeral(nueve, 9).
numeral(diez, 10).    numeral(once, 11).      numeral(doce, 12).
numeral(trece, 13).   numeral(catorce, 14).   numeral(quince, 15).
numeral(dieciseis, 16). numeral(diecisiete, 17). numeral(dieciocho, 18).
numeral(diecinueve, 19). numeral(veinte, 20). numeral(treinta, 30).
numeral(cuarenta, 40). numeral(cincuenta, 50). numeral(cien, 100).
numeral(mil, 1000).

/* ==========================================================================
   SECCION N3. GRAMATICA DE LA ORACION (DCG sobre tokens)
   oracion(oracion(Ss))  --> sintagmas(Ss).
   sintagma              --> conectores, negacion opcional, rellenos,
                             nucleo (frase lexica o frase numerica).
   ========================================================================== */

/* oracion//1: la descripcion completa es una secuencia de sintagmas. */
oracion(oracion(Ss)) --> sintagmas(Ss).

/* sintagmas//1: en cada posicion se intenta, EN ESTE ORDEN:
   1) un sintagma completo (con nucleo que aporta un requisito);
   2) omitir una palabra funcional (relleno, conector o negador suelto);
   3) omitir cualquier otra palabra, que se anota como no_entendido.
   Los cortes fijan la primera alternativa que funciona: si ya se reconocio
   un sintagma NO se debe reintentar leyendo sus palabras como "no
   entendidas" (eso daria analisis alternativos con menos requisitos). La
   clausula 3 es la omision que pide el enunciado y va DESPUES de intentar
   los sintagmas; como siempre consume un token, la recursion termina. */
sintagmas([S|Ss]) --> sintagma(S), !, sintagmas(Ss).
sintagmas([funcional(P)|Ss]) --> [P], { palabra_funcional(P) }, !, sintagmas(Ss).
sintagmas([no_entendido(P)|Ss]) --> [P], !, sintagmas(Ss).
sintagmas([]) --> [].

/* sintagma//1: conectores y rellenos se aceptan en cualquier cantidad; la
   negacion es opcional y se prueba PRIMERO sin negacion. Asi una entrada
   del lexico que empieza con "no" o "sin" ("no tiene experiencia en
   devops", "sin caidas") se reconoce como frase lexica con su propia
   polaridad, y solo si no existe esa frase se interpreta "no"/"sin" como
   negacion gramatical ("no necesitamos alta disponibilidad"). */
sintagma(sintagma(Cs, Neg, Rs, Nucleo)) -->
    conectores(Cs),
    negacion_opcional(Neg),
    rellenos(Rs),
    nucleo(Nucleo).

/* conectores//1: voraz pero con vuelta atras (sin corte), por si una
   palabra conectora fuera el inicio de una frase del lexico. */
conectores([C|Cs]) --> [C], { conector(C) }, conectores(Cs).
conectores([])     --> [].

negacion_opcional(ninguna)     --> [].
negacion_opcional(negacion(P)) --> [P], { negador(P) }.

/* rellenos//1: PEREZOSO (primero la lista vacia). En cada punto se intenta
   antes el nucleo, de modo que "equipo" se lee dentro de "equipo de 3
   personas" y no se pierde como relleno. */
rellenos([])     --> [].
rellenos([R|Rs]) --> [R], { relleno(R) }, rellenos(Rs).

/* nucleo//1: primero la frase del lexico (vocabulario explicito), despues
   la frase numerica (patron + restriccion aritmetica). */
nucleo(N) --> frase_lexica(N).
nucleo(N) --> frase_numerica(N).

/* --- N3.1 Frase lexica: coincidencia mas larga ------------------------------
   frase_lexica(lexica(Tokens, Requisito, Polaridad)): se mira el resto de
   la entrada sin consumirlo (resto//1), se elige la entrada de lexico/3
   MAS LARGA que sea prefijo y se consumen exactamente esos tokens. Elegir
   la mas larga evita que [muchos, usuarios] gane a [muchos, usuarios, al,
   mismo, tiempo] y deje palabras sueltas. */
frase_lexica(lexica(Toks, Req, Pol)) -->
    resto(Entrada),
    { coincidencia_mas_larga(Entrada, Toks, Req, Pol) },
    consumir(Toks).

resto(L, L, L).

consumir([])     --> [].
consumir([T|Ts]) --> [T], consumir(Ts).

/* coincidencia_mas_larga(+Entrada, -Toks, -Req, -Pol): keysort/2 es estable,
   asi ante dos frases del mismo largo gana la primera de la base (las del
   experto antes que los sinonimos aprendidos). El corte deja una sola. */
coincidencia_mas_larga(Entrada, Toks, Req, Pol) :-
    Entrada = [Primero|_],
    findall(NL-(T-R-P),
            ( lexico(T, R, P), T = [Primero|_], prefijo(T, Entrada),
              length(T, L), NL is -L ),
            Pares),
    keysort(Pares, [_-(Toks-Req-Pol)|_]), !.

/* prefijo(+Pre, +Lista) */
prefijo([], _).
prefijo([X|Xs], [X|Ys]) :- prefijo(Xs, Ys).

/* --- N3.2 Frase numerica con restriccion aritmetica -------------------------
   frase_numerica(numerica(Magnitud, Valor, Requisito)): el patron fija la
   magnitud (personas, usuarios, milisegundos, semanas) y el valor; despues
   requisito_por_umbral/3 aplica la restriccion aritmetica con los hechos
   umbral_numerico/3. Si ningun umbral se cumple ("equipo de 7 personas")
   el requisito es 'ninguno': la frase se entendio pero no aporta. */
frase_numerica(numerica(Mag, Valor, Req)) -->
    patron_numerico(Mag, Valor),
    { requisito_por_umbral(Mag, Valor, Req) }.

% personas: "equipo de 3 personas", "grupo de cuatro", "somos 4",
%           "somos 4 desarrolladores", "3 desarrolladores"
patron_numerico(personas, N) --> [G], { memberchk(G, [equipo, grupo]) }, [de],
                                 numero(N), unidad_personas_opcional.
patron_numerico(personas, N) --> [somos], numero(N), unidad_personas_opcional.
patron_numerico(personas, N) --> numero(N), unidad_personas.
% usuarios: "mas de 1000 usuarios", "10 mil usuarios concurrentes"
patron_numerico(usuarios, N) --> cuantificador_opcional, numero(N),
                                 unidad_usuarios, calificador_usuarios_opcional.
% milisegundos: "responder en menos de 100 ms", "respuesta en 2 segundos"
patron_numerico(milisegundos, Ms) --> verbo_respuesta_opcional, en_opcional,
                                      cuantificador_opcional, numero(N),
                                      unidad_tiempo_respuesta(F), { Ms is N * F }.
% semanas: "entregar en 3 semanas", "salir en 30 dias", "en 2 meses"
patron_numerico(semanas, S) --> verbo_entrega_opcional, en_opcional,
                                cuantificador_opcional, numero(N),
                                unidad_plazo(U), { a_semanas(U, N, S) }.

/* numero//1: entero o numeral, con multiplicador "mil" ("10 mil", "diez
   mil"). Los cortes despues de [mil] impiden que, al volver atras, "10 mil"
   se lea solo como 10 y "mil" quede suelto. */
numero(N) --> [A], { integer(A) }, [mil], !, { N is A * 1000 }.
numero(N) --> [P], { numeral(P, A), A < 1000 }, [mil], !, { N is A * 1000 }.
numero(N) --> [N], { integer(N) }.
numero(N) --> [P], { numeral(P, N) }.

unidad_personas --> [U], { memberchk(U, [personas, persona, desarrolladores,
    desarrollador, integrantes, miembros, programadores, ingenieros, devs]) }.
unidad_personas_opcional --> unidad_personas.
unidad_personas_opcional --> [].

unidad_usuarios --> [U], { memberchk(U, [usuarios, usuario, clientes,
    visitantes, conexiones, peticiones]) }.
calificador_usuarios_opcional --> [C], { memberchk(C, [concurrentes,
    simultaneos, activos, diarios]) }.
calificador_usuarios_opcional --> [].

cuantificador_opcional --> [mas, de].
cuantificador_opcional --> [menos, de].
cuantificador_opcional --> [como, maximo].
cuantificador_opcional --> [maximo].
cuantificador_opcional --> [hasta].
cuantificador_opcional --> [unos].
cuantificador_opcional --> [alrededor, de].
cuantificador_opcional --> [].

en_opcional --> [en].
en_opcional --> [].

verbo_respuesta_opcional --> [V], { memberchk(V, [responder, responda,
    respuesta, respuestas, contestar, responde]) }.
verbo_respuesta_opcional --> [].

/* unidad_tiempo_respuesta(-Factor): factor para pasar a milisegundos. */
unidad_tiempo_respuesta(1)    --> [U], { memberchk(U, [ms, milisegundos, milisegundo]) }.
unidad_tiempo_respuesta(1000) --> [U], { memberchk(U, [segundos, segundo, s]) }.

verbo_entrega_opcional --> [V], { memberchk(V, [entregar, entrega, lanzar,
    salir, terminar, publicar, listo, lista, estar]) }.
verbo_entrega_opcional --> [].

unidad_plazo(semanas) --> [U], { memberchk(U, [semanas, semana]) }.
unidad_plazo(dias)    --> [U], { memberchk(U, [dias, dia]) }.
unidad_plazo(meses)   --> [U], { memberchk(U, [meses, mes]) }.

/* a_semanas(+Unidad, +N, -Semanas): 30 dias -> 5 semanas (redondeo hacia
   arriba), 2 meses -> 8 semanas. */
a_semanas(semanas, N, N).
a_semanas(dias, N, S)  :- S is (N + 6) // 7.
a_semanas(meses, N, S) :- S is N * 4.

/* --- N3.3 Umbrales numericos (ajustables sin tocar la gramatica) ----------
   umbral_numerico(Requisito, Comparacion, Valor)
   magnitud_requisito(Magnitud, Requisito): que requisitos puede producir
   cada magnitud; se prueban en este orden. */
umbral_numerico(equipo_pequeno,   menor,       5).     % N < 5 personas
umbral_numerico(equipo_grande,    mayor_igual, 10).    % N >= 10 personas
umbral_numerico(muchos_usuarios,  mayor_igual, 1000).  % N >= 1000 usuarios
umbral_numerico(latencia_critica, menor_igual, 100).   % N <= 100 ms
umbral_numerico(entrega_rapida,   menor_igual, 6).     % N <= 6 semanas

magnitud_requisito(personas,     equipo_pequeno).
magnitud_requisito(personas,     equipo_grande).
magnitud_requisito(usuarios,     muchos_usuarios).
magnitud_requisito(milisegundos, latencia_critica).
magnitud_requisito(semanas,      entrega_rapida).

/* requisito_por_umbral(+Magnitud, +N, -Req): primer requisito cuyo umbral
   se cumple. Corte: un valor produce un solo requisito. Si ninguno se
   cumple, 'ninguno' (fallback). */
requisito_por_umbral(Mag, N, Req) :-
    magnitud_requisito(Mag, Req),
    umbral_numerico(Req, Op, V),
    cumple_umbral(Op, N, V), !.
requisito_por_umbral(_, _, ninguno).

cumple_umbral(menor,       N, V) :- N < V.
cumple_umbral(menor_igual, N, V) :- N =< V.
cumple_umbral(mayor,       N, V) :- N > V.
cumple_umbral(mayor_igual, N, V) :- N >= V.

/* ==========================================================================
   SECCION N4. INTERPRETACION (predicado principal que llama Python)
   ========================================================================== */

/* interpretar_texto(+Texto, -Requisitos, -Negados, -NoEntendido, -Arbol)
   - Requisitos : ids afirmados, sin repetidos, en orden de aparicion.
   - Negados    : ids negados ("no necesitamos alta disponibilidad"); van a
                  la lista de "no aplica" de las preguntas guiadas.
   - NoEntendido: palabras que no formaron parte de ningun sintagma.
   - Arbol      : oracion([...]) con el analisis sintactico.
   Nunca lanza excepcion: catch/3 convierte cualquier error en listas
   vacias. La gramatica siempre analiza la entrada completa porque la
   clausula de omision consume cualquier token; el corte deja ese unico
   analisis. */
interpretar_texto(Texto, Requisitos, Negados, NoEntendido, Arbol) :-
    catch(interpretar_seguro(Texto, Requisitos, Negados, NoEntendido, Arbol),
          _Error,
          ( Requisitos = [], Negados = [], NoEntendido = [], Arbol = oracion([]) )).

interpretar_seguro(Texto, Requisitos, Negados, NoEntendido, Arbol) :-
    normalizar_texto(Texto, Tokens),
    phrase(oracion(Arbol), Tokens), !,
    Arbol = oracion(Ss),
    findall(R-P, ( member(S, Ss), mencion(S, R, P) ), Menciones),
    resolver_menciones(Menciones, Requisitos, Negados),
    findall(W, member(no_entendido(W), Ss), NoEntendido).

/* mencion(+Sintagma, -Req, -Polaridad): requisito y polaridad final de un
   sintagma. Un nucleo numerico que no cumple umbral ('ninguno') o un
   requisito que ya no existe en la base no produce mencion. */
mencion(sintagma(_, Neg, _, Nucleo), R, PolFinal) :-
    nucleo_requisito(Nucleo, R, Pol),
    R \== ninguno,
    requisito_categoria(R, _),
    polaridad_final(Neg, Pol, PolFinal).

nucleo_requisito(lexica(_, R, Pol), R, Pol).
nucleo_requisito(numerica(_, _, R), R, afirma).

/* polaridad_final(+Negacion, +PolaridadLexico, -Final): la negacion
   gramatical invierte la polaridad de la frase (doble negacion afirma). */
polaridad_final(ninguna,     Pol,    Pol).
polaridad_final(negacion(_), afirma, niega).
polaridad_final(negacion(_), niega,  afirma).

/* resolver_menciones(+Menciones, -Afirmados, -Negados): si un requisito se
   menciona varias veces gana la ULTIMA mencion (el usuario se corrigio).
   Asi un id nunca queda a la vez en Requisitos y en Negados. */
resolver_menciones(Ms, Afirmados, Negados) :-
    findall(R, member(R-_, Ms), Rs0),
    list_to_set(Rs0, Rs),
    findall(R, ( member(R, Rs), ultima_polaridad(R, Ms, afirma) ), Afirmados),
    findall(R, ( member(R, Rs), ultima_polaridad(R, Ms, niega) ), Negados).

ultima_polaridad(R, Ms, Pol) :-
    findall(P, member(R-P, Ms), Ps),
    last(Ps, Pol).

/* --- N4.1 Arbol como texto con sangria (lo muestra la interfaz) ---------- */

/* arbol_lineas(+Arbol, -Lineas): una linea por nodo. Los sintagmas se
   numeran en orden (1, 2, ...) sin contar las palabras omitidas. */
arbol_lineas(oracion(Ss), ['oracion'|Ls]) :- !,
    numerar_nodos(Ss, 1, Ls0),
    append(Ls0, Ls).
arbol_lineas(_, []).

numerar_nodos([], _, []).
numerar_nodos([S|Ss], I, [L|Ls]) :-
    linea_nodo(I, S, L),
    ( S = sintagma(_, _, _, _) -> I1 is I + 1 ; I1 = I ),
    numerar_nodos(Ss, I1, Ls).

linea_nodo(I, sintagma(Cs, Neg, Rs, Nucleo), Lineas) :- !,
    format(atom(L0), '  sintagma ~w', [I]),
    findall(L, ( member(C, Cs), format(atom(L), '    conector: ~w', [C]) ), LC),
    lineas_negacion(Neg, LN),
    findall(L, ( member(R, Rs), format(atom(L), '    relleno: ~w', [R]) ), LR),
    lineas_nucleo(Nucleo, LNu),
    linea_resultado(Neg, Nucleo, LRes),
    append([[L0], LC, LN, LR, LNu, LRes], Lineas).
linea_nodo(_, funcional(P), [L]) :- !,
    format(atom(L), '  palabra funcional (se omite): ~w', [P]).
linea_nodo(_, no_entendido(P), [L]) :-
    format(atom(L), '  NO ENTENDIDO: ~w', [P]).

lineas_negacion(ninguna, []) :- !.
lineas_negacion(negacion(P), [L]) :- format(atom(L), '    negacion: ~w', [P]).

lineas_nucleo(lexica(Toks, R, Pol), [L]) :- !,
    atomic_list_concat(Toks, ' ', T),
    format(atom(L), '    frase lexica: "~w" -> ~w (~w)', [T, R, Pol]).
lineas_nucleo(numerica(Mag, V, R), [L]) :-
    texto_umbral(R, TU),
    format(atom(L), '    frase numerica: ~w = ~w -> ~w~w', [Mag, V, R, TU]).

texto_umbral(ninguno, ' (no cumple ningun umbral)') :- !.
texto_umbral(R, T) :-
    umbral_numerico(R, Op, V), !,
    format(atom(T), ' (umbral: ~w ~w)', [Op, V]).
texto_umbral(_, '').

linea_resultado(Neg, Nucleo, [L]) :-
    nucleo_requisito(Nucleo, R, Pol), R \== ninguno, !,
    polaridad_final(Neg, Pol, F),
    ( F == afirma -> Txt = 'AFIRMADO' ; Txt = 'NEGADO' ),
    format(atom(L), '    => ~w ~w', [R, Txt]).
linea_resultado(_, _, []).

/* ==========================================================================
   SECCION N5. VOCABULARIO EN CALIENTE (Modo Experto, pestana Vocabulario)
   ========================================================================== */

/* ensenar_sinonimo(+Frase, +Requisito, -Resultado)
   ensenar_sinonimo(+Frase, +Requisito, +Polaridad, -Resultado)
   Resultado = ok(Tokens) | error(Motivo). La frase pasa por el mismo
   normalizador que el texto del usuario, asi se guarda como se va a leer.
   Si es valida: assertz/1 en memoria y se ANEXA al archivo de aprendizaje
   (anexar_aprendizaje/1, seccion 9 de la base). Si no se puede escribir
   en disco se deshace el assertz: memoria y archivo nunca difieren. */
ensenar_sinonimo(Frase, Req, Resultado) :-
    ensenar_sinonimo(Frase, Req, afirma, Resultado).

ensenar_sinonimo(Frase, Req0, Pol0, Resultado) :-
    normalizar_texto(Frase, Toks),
    atomo_minuscula(Req0, Req),
    atomo_minuscula(Pol0, Pol),
    primer_error_sinonimo(Toks, Req, Pol, Error),
    aplicar_sinonimo(Error, Toks, Req, Pol, Resultado).

/* atomo_minuscula(+X, -A): atomo o string en minuscula; otra cosa -> ''. */
atomo_minuscula(X, A) :- atom(X), !, downcase_atom(X, A).
atomo_minuscula(X, A) :- string(X), !, atom_string(A0, X), downcase_atom(A0, A).
atomo_minuscula(_, '').

/* primer_error_sinonimo(+Toks, +Req, +Pol, -Error): validaciones en orden;
   cada clausula termina en corte (la primera que falla decide). Las \+
   se evaluan con Toks ya ligado. */
primer_error_sinonimo([], _, _, frase_vacia) :- !.
primer_error_sinonimo(Toks, _, _, frase_con_signos) :-
    memberchk(',', Toks), !.
primer_error_sinonimo(Toks, _, _, frase_solo_funcional) :-
    \+ ( member(T, Toks), \+ palabra_funcional(T) ), !.
primer_error_sinonimo(_, Req, _, requisito_desconocido(Req)) :-
    \+ requisito_categoria(Req, _), !.
primer_error_sinonimo(_, _, Pol, polaridad_invalida(Pol)) :-
    \+ memberchk(Pol, [afirma, niega]), !.
primer_error_sinonimo(Toks, Req, _, ya_existe(Req)) :-
    lexico(Toks, Req, _), !.
primer_error_sinonimo(Toks, _, _, conflicto(Otro)) :-
    lexico(Toks, Otro, _), !.
primer_error_sinonimo(_, _, _, ninguno).

/* aplicar_sinonimo(+Error, ...): con error la base no se toca. */
aplicar_sinonimo(Error, _, _, _, error(Error)) :-
    Error \== ninguno, !.
aplicar_sinonimo(ninguno, Toks, Req, Pol, Resultado) :-
    assertz(lexico_aprendido(Toks)),
    assertz(lexico(Toks, Req, Pol)),
    persistir_o_deshacer(
        anexar_aprendizaje([lexico_aprendido(Toks), lexico(Toks, Req, Pol)]),
        ( retractall(lexico_aprendido(Toks)), retractall(lexico(Toks, _, _)) ),
        ok(Toks), Resultado).

/* olvidar_sinonimo(+Frase): borra un sinonimo APRENDIDO (nunca uno de la
   base: la marca lexico_aprendido/1 es la unica puerta) y reescribe el
   archivo. Falla si la frase no es un sinonimo aprendido. */
olvidar_sinonimo(Frase) :-
    normalizar_texto(Frase, Toks),
    lexico_aprendido(Toks), !,
    retractall(lexico_aprendido(Toks)),
    retractall(lexico(Toks, _, _)),
    guardar_aprendizaje.

/* borrar_sinonimos_aprendidos: lo usa olvidar_aprendizaje/0. */
borrar_sinonimos_aprendidos :-
    forall(lexico_aprendido(T), retractall(lexico(T, _, _))),
    retractall(lexico_aprendido(_)).

/* sinonimos_aprendidos(-Lista): [[Frase, Requisito, Polaridad], ...] */
sinonimos_aprendidos(Lista) :-
    findall([F, R, P],
            ( lexico_aprendido(T), lexico(T, R, P), atomic_list_concat(T, ' ', F) ),
            Lista).

/* formulaciones(+Requisito, -Lista): frases que el sistema entiende para
   ese requisito (la interfaz y el README las muestran). */
formulaciones(Req, Lista) :-
    findall(F,
            ( lexico(T, Req, Pol), atomic_list_concat(T, ' ', F0),
              ( Pol == niega -> format(atom(F), '~w (niega)', [F0]) ; F = F0 ) ),
            Lista).

/* mensaje_sinonimo(+Resultado, -Texto) */
mensaje_sinonimo(ok(T), M) :- !,
    atomic_list_concat(T, ' ', F),
    lexico(T, R, P),
    format(atom(M), 'Sinonimo guardado: "~w" -> ~w (~w). Ya se reconoce en la caja de texto.', [F, R, P]).
mensaje_sinonimo(error(frase_vacia), 'Escriba una frase (al menos una palabra).') :- !.
mensaje_sinonimo(error(frase_con_signos), 'La frase no puede tener comas ni punto y coma.') :- !.
mensaje_sinonimo(error(frase_solo_funcional),
    'La frase solo tiene articulos, conectores o verbos comunes; agregue una palabra con contenido.') :- !.
mensaje_sinonimo(error(requisito_desconocido(R)), M) :- !,
    format(atom(M), 'El requisito ~w no esta en la base de conocimiento.', [R]).
mensaje_sinonimo(error(polaridad_invalida(P)), M) :- !,
    format(atom(M), 'Polaridad invalida: ~w (use afirma o niega).', [P]).
mensaje_sinonimo(error(ya_existe(R)), M) :- !,
    format(atom(M), 'Esa frase ya se reconoce como ~w.', [R]).
mensaje_sinonimo(error(conflicto(R)), M) :- !,
    format(atom(M), 'Esa frase ya significa ~w; no puede apuntar a otro requisito.', [R]).
mensaje_sinonimo(error(persistencia(E)), M) :- !,
    format(atom(M), 'No se pudo escribir el archivo de aprendizaje (~w). No se guardo nada.', [E]).
mensaje_sinonimo(R, M) :-
    format(atom(M), 'Resultado no reconocido: ~w', [R]).

/* ==========================================================================
   SECCION N6. LEXICO DEL EXPERTO: lexico(Tokens, Requisito, Polaridad)
   Polaridad afirma: la frase afirma el requisito. niega: la frase lo niega
   ("carga estable" niega carga_variable). Las frases que EMPIEZAN con "no"
   o "sin" pero significan un requisito ("sin experiencia en devops") van
   con polaridad afirma: el lexico se prueba antes que la negacion.
   Al menos 3 formulaciones por cada uno de los 20 requisitos.
   ========================================================================== */

% --- equipo ---
lexico([equipo, pequeno],                 equipo_pequeno, afirma).
lexico([equipo, reducido],                equipo_pequeno, afirma).
lexico([equipo, chico],                   equipo_pequeno, afirma).
lexico([pocos, desarrolladores],          equipo_pequeno, afirma).
lexico([pocas, personas],                 equipo_pequeno, afirma).
lexico([equipo, de, pocas, personas],     equipo_pequeno, afirma).
lexico([somos, pocos],                    equipo_pequeno, afirma).

lexico([equipo, grande],                  equipo_grande, afirma).
lexico([equipo, numeroso],                equipo_grande, afirma).
lexico([muchos, desarrolladores],         equipo_grande, afirma).
lexico([varios, equipos],                 equipo_grande, afirma).
lexico([muchos, equipos],                 equipo_grande, afirma).
lexico([equipos, distribuidos],           equipo_grande, afirma).

lexico([sin, experiencia, en, devops],    sin_experiencia_devops, afirma).
lexico([sin, experiencia, devops],        sin_experiencia_devops, afirma).
lexico([sin, devops],                     sin_experiencia_devops, afirma).
lexico([no, tiene, experiencia, en, devops],   sin_experiencia_devops, afirma).
lexico([no, tienen, experiencia, en, devops],  sin_experiencia_devops, afirma).
lexico([no, tenemos, experiencia, en, devops], sin_experiencia_devops, afirma).
lexico([poca, experiencia, en, devops],   sin_experiencia_devops, afirma).
lexico([no, sabemos, devops],             sin_experiencia_devops, afirma).
lexico([no, sabemos, de, devops],         sin_experiencia_devops, afirma).
lexico([sin, experiencia, en, contenedores], sin_experiencia_devops, afirma).
lexico([experiencia, en, devops],         sin_experiencia_devops, niega).

% --- presupuesto ---
lexico([poco, presupuesto],               presupuesto_bajo, afirma).
lexico([presupuesto, limitado],           presupuesto_bajo, afirma).
lexico([presupuesto, ajustado],           presupuesto_bajo, afirma).
lexico([bajo, presupuesto],               presupuesto_bajo, afirma).
lexico([presupuesto, bajo],               presupuesto_bajo, afirma).
lexico([presupuesto, reducido],           presupuesto_bajo, afirma).
lexico([pocos, recursos],                 presupuesto_bajo, afirma).
lexico([poco, dinero],                    presupuesto_bajo, afirma).
lexico([bajo, costo],                     presupuesto_bajo, afirma).
lexico([presupuesto, amplio],             presupuesto_bajo, niega).
lexico([mucho, presupuesto],              presupuesto_bajo, niega).

% --- tiempo ---
lexico([entregar, rapido],                entrega_rapida, afirma).
lexico([entrega, rapida],                 entrega_rapida, afirma).
lexico([entregar, pronto],                entrega_rapida, afirma).
lexico([poco, tiempo],                    entrega_rapida, afirma).
lexico([plazo, corto],                    entrega_rapida, afirma).
lexico([plazos, cortos],                  entrega_rapida, afirma).
lexico([lanzar, rapido],                  entrega_rapida, afirma).
lexico([salir, rapido],                   entrega_rapida, afirma).
lexico([cuanto, antes],                   entrega_rapida, afirma).
lexico([lo, antes, posible],              entrega_rapida, afirma).
lexico([entrega, urgente],                entrega_rapida, afirma).
lexico([sin, prisa],                      entrega_rapida, niega).
lexico([plazo, amplio],                   entrega_rapida, niega).

% --- carga ---
lexico([muchos, usuarios],                muchos_usuarios, afirma).
lexico([muchos, usuarios, al, mismo, tiempo], muchos_usuarios, afirma).
lexico([miles, de, usuarios],             muchos_usuarios, afirma).
lexico([millones, de, usuarios],          muchos_usuarios, afirma).
lexico([millon, de, usuarios],            muchos_usuarios, afirma).
lexico([usuarios, concurrentes],          muchos_usuarios, afirma).
lexico([usuarios, simultaneos],           muchos_usuarios, afirma).
lexico([alto, trafico],                   muchos_usuarios, afirma).
lexico([mucho, trafico],                  muchos_usuarios, afirma).
lexico([pocos, usuarios],                 muchos_usuarios, niega).

lexico([carga, variable],                 carga_variable, afirma).
lexico([carga, impredecible],             carga_variable, afirma).
lexico([picos, de, demanda],              carga_variable, afirma).
lexico([picos, de, trafico],              carga_variable, afirma).
lexico([demanda, variable],               carga_variable, afirma).
lexico([demanda, impredecible],           carga_variable, afirma).
lexico([trafico, variable],               carga_variable, afirma).
lexico([demanda, estacional],             carga_variable, afirma).
lexico([carga, estable],                  carga_variable, niega).
lexico([demanda, constante],              carga_variable, niega).

lexico([procesos, largos],                procesos_largos, afirma).
lexico([tareas, largas],                  procesos_largos, afirma).
lexico([tareas, pesadas],                 procesos_largos, afirma).
lexico([procesos, pesados],               procesos_largos, afirma).
lexico([procesamiento, por, lotes],       procesos_largos, afirma).
lexico([tareas, de, varios, minutos],     procesos_largos, afirma).
lexico([procesos, que, tardan],           procesos_largos, afirma).

lexico([baja, latencia],                  latencia_critica, afirma).
lexico([latencia, baja],                  latencia_critica, afirma).
lexico([latencia, critica],               latencia_critica, afirma).
lexico([tiempo, real],                    latencia_critica, afirma).
lexico([respuesta, inmediata],            latencia_critica, afirma).
lexico([respuestas, instantaneas],        latencia_critica, afirma).
lexico([en, milisegundos],                latencia_critica, afirma).

% --- operacion ---
lexico([alta, disponibilidad],            disponibilidad_alta, afirma).
lexico([disponibilidad, alta],            disponibilidad_alta, afirma).
lexico([disponible, las, 24, horas],      disponibilidad_alta, afirma).
lexico([disponible, 24, horas],           disponibilidad_alta, afirma).
lexico([24, horas],                       disponibilidad_alta, afirma).
lexico([24, 7],                           disponibilidad_alta, afirma).
lexico([sin, caidas],                     disponibilidad_alta, afirma).
lexico([siempre, disponible],             disponibilidad_alta, afirma).
lexico([disponible, todo, el, tiempo],    disponibilidad_alta, afirma).
lexico([tolerante, a, fallos],            disponibilidad_alta, afirma).

lexico([despliegue, independiente],       despliegue_independiente, afirma).
lexico([despliegues, independientes],     despliegue_independiente, afirma).
lexico([desplegar, por, separado],        despliegue_independiente, afirma).
lexico([desplegar, partes, por, separado], despliegue_independiente, afirma).
lexico([desplegar, modulos, por, separado], despliegue_independiente, afirma).
lexico([actualizar, partes, por, separado], despliegue_independiente, afirma).
lexico([actualizar, sin, redesplegar, todo], despliegue_independiente, afirma).

lexico([integrar, sistemas, existentes],  integracion_sistemas_heredados, afirma).
lexico([sistemas, existentes],            integracion_sistemas_heredados, afirma).
lexico([sistemas, heredados],             integracion_sistemas_heredados, afirma).
lexico([sistemas, legados],               integracion_sistemas_heredados, afirma).
lexico([sistemas, legacy],                integracion_sistemas_heredados, afirma).
lexico([sistemas, antiguos],              integracion_sistemas_heredados, afirma).
lexico([legacy],                          integracion_sistemas_heredados, afirma).

lexico([datos, centralizados],            datos_centralizados, afirma).
lexico([base, de, datos, central],        datos_centralizados, afirma).
lexico([base, de, datos, centralizada],   datos_centralizados, afirma).
lexico([servidor, central],               datos_centralizados, afirma).
lexico([datos, en, un, solo, lugar],      datos_centralizados, afirma).
lexico([centralizar, los, datos],         datos_centralizados, afirma).
lexico([varios, clientes],                datos_centralizados, afirma).

% --- dominio ---
lexico([dominio, complejo],               dominio_complejo, afirma).
lexico([muchas, reglas, de, negocio],     dominio_complejo, afirma).
lexico([reglas, de, negocio, complejas],  dominio_complejo, afirma).
lexico([negocio, complejo],               dominio_complejo, afirma).
lexico([logica, de, negocio, compleja],   dominio_complejo, afirma).
lexico([muchos, subdominios],             dominio_complejo, afirma).

lexico([integracion, asincrona],          integracion_asincrona, afirma).
lexico([comunicacion, asincrona],         integracion_asincrona, afirma).
lexico([mensajes, asincronos],            integracion_asincrona, afirma).
lexico([colas, de, mensajes],             integracion_asincrona, afirma).
lexico([mensajeria],                      integracion_asincrona, afirma).
lexico([eventos],                         integracion_asincrona, afirma).
lexico([sin, esperar, respuesta],         integracion_asincrona, afirma).

lexico([consistencia, estricta],          consistencia_estricta, afirma).
lexico([consistencia, fuerte],            consistencia_estricta, afirma).
lexico([transacciones],                   consistencia_estricta, afirma).
lexico([operaciones, transaccionales],    consistencia_estricta, afirma).
lexico([datos, siempre, consistentes],    consistencia_estricta, afirma).
lexico([integridad, de, datos],           consistencia_estricta, afirma).

lexico([mantenibilidad],                  mantenibilidad_largo_plazo, afirma).
lexico([largo, plazo],                    mantenibilidad_largo_plazo, afirma).
lexico([facil, de, mantener],             mantenibilidad_largo_plazo, afirma).
lexico([mantener, por, anos],             mantenibilidad_largo_plazo, afirma).
lexico([muchos, anos],                    mantenibilidad_largo_plazo, afirma).
lexico([evolucionar, con, facilidad],     mantenibilidad_largo_plazo, afirma).
lexico([sistema, mantenible],             mantenibilidad_largo_plazo, afirma).

lexico([testabilidad],                    testabilidad_alta, afirma).
lexico([alta, testabilidad],              testabilidad_alta, afirma).
lexico([pruebas, automaticas],            testabilidad_alta, afirma).
lexico([pruebas, unitarias],              testabilidad_alta, afirma).
lexico([tests, automatizados],            testabilidad_alta, afirma).
lexico([facil, de, probar],               testabilidad_alta, afirma).
lexico([probar, la, logica],              testabilidad_alta, afirma).

lexico([independencia, tecnologica],      independencia_tecnologica, afirma).
lexico([cambiar, la, base, de, datos],    independencia_tecnologica, afirma).
lexico([cambiar, de, base, de, datos],    independencia_tecnologica, afirma).
lexico([cambiar, el, framework],          independencia_tecnologica, afirma).
lexico([cambiar, de, framework],          independencia_tecnologica, afirma).
lexico([cambiar, de, tecnologia],         independencia_tecnologica, afirma).
lexico([no, depender, del, framework],    independencia_tecnologica, afirma).
lexico([sin, reescribir, todo],           independencia_tecnologica, afirma).

lexico([separar, interfaz, y, logica],    separar_interfaz_logica, afirma).
lexico([separar, interfaz, de, logica],   separar_interfaz_logica, afirma).
lexico([separar, la, interfaz, de, la, logica], separar_interfaz_logica, afirma).
lexico([separar, la, interfaz, y, la, logica],  separar_interfaz_logica, afirma).
lexico([separar, vista, y, logica],       separar_interfaz_logica, afirma).
lexico([separacion, de, responsabilidades], separar_interfaz_logica, afirma).
lexico([interfaz, separada],              separar_interfaz_logica, afirma).
lexico([modelo, vista, controlador],      separar_interfaz_logica, afirma).
