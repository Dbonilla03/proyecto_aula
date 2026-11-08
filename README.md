# ArquiSelect — Entregable 3

Sistema experto de **caja blanca** (SWI-Prolog + Python/Tkinter con PySwip) que recomienda un estilo de arquitectura de software entre 11 estilos y explica por qué. Este entregable agrega:

- **(A) Lenguaje natural con DCG:** el usuario describe su proyecto con sus palabras y Prolog lo traduce a requisitos.
- **(B) Modo Experto:** reglas lógicas, arquitecturas y vocabulario nuevos que se inyectan en caliente con `assertz` y quedan guardados en disco.
- **(C) Pruebas y evidencia:** `pruebas_entregable3.py` → `evidencia_entregable3.txt`.

**Regla del proyecto:** toda la lógica vive en Prolog. Python solo envía datos, invoca predicados y muestra respuestas.

## Ejecución

Requisitos: Python 3.9+, SWI-Prolog 9.x en el PATH (misma arquitectura de 64 bits) y `pip install pyswip`.

```bash
python main.py                    # aplicación
python pruebas_entregable3.py     # pruebas del entregable 3 (también corre pruebas.py)
python pruebas.py                 # pruebas del entregable 2
python motor.py                   # versión por consola del entregable 1
```

## Roles y PIN

En la pantalla de **Inicio** está el selector **ROL: 👤 Usuario / 🛡 Experto**. El rol actual aparece en el encabezado de todas las vistas.

- **Usuario** (por defecto): evaluación, historial y recarga de la base. No tiene acceso al Modo Experto.
- **Experto:** al elegirlo se pide un PIN. El PIN por defecto es **`experto2026`**. Se puede cambiar definiendo la variable de entorno `ARQUISELECT_PIN` antes de abrir la app, por ejemplo `set ARQUISELECT_PIN=otroPin` en Windows. Con el rol Experto aparece la tarjeta **Modo Experto** en Inicio, y el botón *Crear arquitectura nueva…* de la evaluación abre esa vista.

> ⚠ **Es un control de acceso de demostración, no seguridad real.** El hash SHA-256 del PIN está en `main.py` y quien tenga acceso a los archivos puede cambiarlo o editar el `.pl` directamente.

## Archivos

| Archivo | Contenido |
|---|---|
| `main.py` | Aplicación Tkinter: `VistaInicio` (rol), `VistaEvaluacion` (texto libre, casillas, preguntas guiadas, resumen y *¿Por qué?*), `VistaModoExperto` (4 pestañas) y `VistaHistorial`. Incluye `PuenteProlog`, que hace todas las consultas. |
| `base_conocimiento.pl` | Hechos y reglas (secciones 1-8 de los entregables 1 y 2). La **sección 9** contiene las reglas expertas (`ensenar_regla/8`). Carga `lenguaje_natural.pl`. |
| `lenguaje_natural.pl` | Normalizador, gramática DCG, léxico (`lexico/3`), umbrales numéricos y sinónimos en caliente. |
| `conocimiento_aprendido.pl` | Lo enseñado en el Modo Experto: estilos, reglas (cláusulas escritas con `portray_clause/2`) y sinónimos. Se crea al guardar lo primero. Cada escritura es atómica (`.tmp` + `rename`) y deja una copia `.bak`. Si está dañado, la app arranca igual y avisa. |
| `pruebas_entregable3.py` / `evidencia_entregable3.txt` | Pruebas del entregable 3 y su salida real. |
| `pruebas.py` / `evidencia_pruebas.txt` | Pruebas del entregable 2 (siguen pasando). |
| `pruebas_contradicciones.py` / `evidencia_contradicciones.txt` | Contradicciones duras/tensiones (sección 10 de la base), entradas hostiles al DCG, límites de longitud y tiempo, y prueba de la interfaz. |
| `GUIA_SUSTENTACION.md` | Cortes probados uno por uno, modificaciones en vivo y preguntas probables. |
| `arbol_logico.txt` | Árbol de llamadas generado del código real por `generar_arbol_logico.pl`. |
| `probar_cortes.py` + `bateria_cortes.pl` → `evidencia_cortes.txt`, `tabla_cortes.md` | Quita cada `!` en una copia temporal y compara 100 consultas. |
| `motor.py` | Consola del entregable 1. |
| `historial_evaluaciones.json` | Evaluaciones guardadas. |

## Qué entiende la caja "Describe tu proyecto"

Escriba en la tarjeta **DESCRIBE TU PROYECTO** y pulse **🔎 Interpretar**. Pasa lo siguiente:

1. Se marcan las casillas de los requisitos entendidos.
2. Lo negado pasa a "No aplica" y arrancan las preguntas guiadas.
3. Aparecen las líneas **✔ Entendí** y **⚠ No entendí**.
4. **Ver análisis sintáctico** muestra el árbol de la DCG.

Interpretar de nuevo reemplaza lo detectado antes.

La gramática divide el texto en *sintagmas*. Cada sintagma tiene conectores opcionales (`y, e, o, además, también, con, pero, ","`), una negación opcional (`no, sin, ni, tampoco, nunca`), rellenos que se omiten (artículos, verbos comunes y sustantivos genéricos como *el equipo* o *la aplicación*) y un núcleo. Mayúsculas, tildes y signos no importan.

| Requisito | Ejemplos de formulaciones (hay más en `lenguaje_natural.pl`) |
|---|---|
| equipo_pequeno | equipo pequeño/reducido/chico, pocos desarrolladores, **equipo de 3 personas**, **somos 4** (< 5) |
| equipo_grande | equipo grande/numeroso, varios equipos, **equipo de 20 personas** (≥ 10) |
| sin_experiencia_devops | sin experiencia en devops, no tiene/tenemos experiencia en devops, no sabemos devops |
| presupuesto_bajo | poco presupuesto, presupuesto limitado/ajustado/bajo, bajo presupuesto, pocos recursos, poco dinero |
| entrega_rapida | entregar rápido/pronto, entrega rápida, poco tiempo, plazo corto, cuanto antes, **entregar en 3 semanas** (≤ 6) |
| muchos_usuarios | muchos usuarios (al mismo tiempo), miles de usuarios, alto tráfico, **más de 1000 usuarios**, **10 mil usuarios** |
| carga_variable | carga variable, picos de demanda/tráfico, demanda impredecible |
| procesos_largos | procesos largos, tareas largas/pesadas, procesamiento por lotes |
| latencia_critica | baja latencia, tiempo real, respuesta inmediata, **responder en menos de 100 ms** |
| disponibilidad_alta | alta disponibilidad, disponible las 24 horas, 24/7, sin caídas, tolerante a fallos |
| despliegue_independiente | despliegue independiente, desplegar (partes) por separado |
| dominio_complejo | dominio complejo, muchas reglas de negocio, lógica de negocio compleja |
| integracion_asincrona | comunicación asíncrona, colas de mensajes, mensajería, eventos |
| consistencia_estricta | consistencia estricta/fuerte, transacciones, integridad de datos |
| mantenibilidad_largo_plazo | largo plazo, fácil de mantener, muchos años, mantenibilidad |
| testabilidad_alta | pruebas automáticas/unitarias, fácil de probar, testabilidad |
| independencia_tecnologica | cambiar la base de datos, cambiar el framework, sin reescribir todo |
| integracion_sistemas_heredados | sistemas heredados/legados/legacy/existentes |
| separar_interfaz_logica | separar interfaz y lógica, separación de responsabilidades, modelo vista controlador |
| datos_centralizados | datos centralizados, base de datos central, servidor central, varios clientes |

Las frases en **negrita** son **frases numéricas**: la regla aritmética se evalúa dentro de la DCG y los umbrales están en `umbral_numerico/3`. Se aceptan números escritos con letras (*tres*, *veinte*, *diez mil*).

**Negaciones:**

- *"No necesitamos alta disponibilidad"* → `disponibilidad_alta` va a **Negados**.
- *"Sin experiencia en DevOps"* sí es un requisito, porque el léxico se prueba antes que la negación.
- Algunas frases niegan por sí mismas (polaridad `niega`): *carga estable*, *pocos usuarios*, *presupuesto amplio*, *sin prisa*.

## Modo Experto (pestañas)

1. **Regla nueva:** id, explicación (obligatoria), condiciones (que deben cumplirse), exclusiones (traducidas a `\+`), efecto (*recomendar* con +1 a +5 o *descartar*) y estilo afectado. Python envía solo esos datos. Prolog valida (id repetido, estilo existente, requisitos existentes, al menos una condición, peso entre 1 y 5, sin solapes) y construye la cláusula `regla_experta/5`, que se inserta con `assertz` y se anexa al archivo. Nunca se ejecuta texto Prolog escrito por el usuario.
2. **Arquitectura nueva:** el formulario de estilos nuevos del entregable 2.
3. **Vocabulario:** frase → requisito (afirma/niega). La caja de texto la entiende de inmediato, sin reiniciar.
4. **Reglas y conocimiento aprendido:** reglas, estilos y sinónimos aprendidos, cada uno con 🗑 y confirmación.

Las reglas disparadas suman su bonus en `puntaje/3` o descartan el estilo en `motivo_descarte/3`. Ranking, candidatos, descartes, *¿Qué falta?* y la sección **¿Por qué? (auditoría)** las muestran sin reiniciar.

## Guion de demostración

1. **Rol Usuario.** Escriba *"somos un equipo de tres personas con poco presupuesto y necesitamos entregar rapido"* y pulse **Interpretar**. Se marcan 3 casillas y arrancan las preguntas guiadas. Abra **Ver análisis sintáctico**.
2. **Rol Experto (PIN `experto2026`).** En **Modo Experto → Regla nueva** cree `mvc_para_equipos_pequenos`:
   - condiciones: *Equipo reducido* y *Separar interfaz de usuario y lógica*
   - exclusión: *Dominio complejo*
   - efecto: recomendar +3, estilo MVC

   Con esas dos casillas, MVC pasa de 5 a 8 puntos y queda primero. En **Resumen → ¿Por qué? (auditoría)** aparece la regla.
3. Cierre la app y vuelva a abrirla: la regla sigue cargada (`conocimiento_aprendido.pl`).
4. Elimine la regla desde **Reglas y conocimiento aprendido**.
