# ArquiSelect — Entregable 2

Sistema experto de **caja blanca** que recomienda un estilo de arquitectura de software (monolito en capas, monolito modular, microservicios, serverless u orientada a eventos). Explica paso a paso por qué llegó al dictamen y, cuando la evidencia no alcanza, sugiere qué dato preguntar para desempatar.

- **Capa simbólica (Prolog):** `base_conocimiento.pl`. Aquí está toda la inferencia, la traza de auditoría y el cálculo del desempate.
- **Capa imperativa (Python):** `main.py`. Contiene la aplicación de escritorio en Tkinter y el controlador PySwip. Solo captura y limpia las entradas, consulta y muestra.

## Archivos

| Archivo | Contenido |
|---|---|
| `main.py` | Aplicación de escritorio multi-vista (Tkinter), persistencia de evaluaciones en JSON (`GestorHistorial`) y clase `PuenteProlog`, que hace todas las consultas a SWI-Prolog. |
| `base_conocimiento.pl` | Hechos y reglas del Entregable 1, más las secciones 5 (explicabilidad), 6 (recomendación) y 7 (apoyo a la interfaz). |
| `motor.py` | Versión por consola del Entregable 1. Sigue funcionando igual. |
| `historial_evaluaciones.json` | Registro de consultas anteriores guardadas en disco. |
| `DICCIONARIO_PREDICADOS.md` / `.pdf` | Documentación de los predicados nuevos. |

## Requisitos

1. **Python 3.9 o superior.**
2. **SWI-Prolog 9.x**, desde https://www.swi-prolog.org/download/stable
   - En Windows, durante la instalación marque la opción **"Add swipl to the system PATH"**.
   - SWI-Prolog y Python deben ser de la misma arquitectura (los dos de 64 bits).
3. Librería de Python (Tkinter ya viene incluido con Python en Windows):

```bash
pip install pyswip
```

## Ejecución

Desde la carpeta del proyecto:

```bash
python main.py
```

Se abre la ventana de ArquiSelect.

### Problemas comunes

| Síntoma | Solución |
|---|---|
| `SwiPrologNotFoundError` o `libswipl not found` | SWI-Prolog no está en el PATH. Reinstálelo marcando la opción del PATH, o defina la variable `SWI_HOME_DIR` con la carpeta de instalación (por ejemplo `C:\Program Files\swipl`). |
| La app no refleja un cambio en el `.pl` | Use el botón **Recargar .pl** del panel izquierdo. Vuelve a consultar el archivo sin reiniciar. |
| `No module named 'tkinter'` | Reinstale Python desde python.org dejando marcada la opción "tcl/tk and IDLE". |

## Cómo se usa la interfaz

- **Vista Inicio:** Menú principal con accesos rápidos a *Nueva Evaluación de Arquitectura*, *Historial de Evaluaciones* y *Recargar Base de Conocimiento*.
- **Vista Evaluación:**
  - **Panel izquierdo:** casillas de requisitos agrupadas por categoría (salen dinámicamente de `requisitos_disponibles/1`), botones de ejemplos rápidos (*Startup*, *Alta Demanda*, *Empresarial*), campo de texto libre con limpieza automática, y botón para guardar en historial.
  - **Tarjetas superiores:** estilo arquitectónico recomendado, descripción detallada, chips de prioridad (severidad), riesgo y confianza, junto con la tarjeta interactiva de desempate (*¿Qué falta?*).
  - **Pestaña "Resumen & Ranking":** gráfico comparativo de barras con las puntuaciones de cada estilo y explicación clara en lenguaje natural (atributos a favor, penalizaciones y alternativas descartadas).
  - **Pestaña "¿Por qué?":** traza exacta de inferencia devuelta por Prolog (reglas disparadas por nivel en árbol, hechos comprobados y alternativas descartadas).
  - **Pestaña "¿Qué falta?":** estado del dictamen, hipótesis en competencia y listado completo de preguntas con poder de desempate calculado por Prolog.
  - **Pestaña "Consulta a Prolog":** metas exactas enviadas y respuesta cruda en formato Prolog para auditoría técnica.
- **Vista Historial:** Tabla con las evaluaciones generadas, fecha, requisitos ingresados, estilo dictaminado, prioridad y estado, persistido en `historial_evaluaciones.json`.

## Decisiones técnicas

- **Sin bloqueos.** Prolog nunca usa `read/1`: los datos llegan como argumentos de la consulta y la respuesta vuelve completa, así que la ventana no se queda esperando una entrada. Cada cambio en una casilla dispara la consulta y la ventana se actualiza al instante.
- **Entradas seguras.** Python envía cada requisito como átomo entre comillas simples, de modo que nunca puede llegar como variable libre. Además, Prolog vuelve a validar con `validar_entrada/2` (`is_list/1`, `ground/1`, `atom/1`, `downcase_atom/2`).
- **Textos sin tildes en el `.pl`.** Las etiquetas y preguntas de la base no llevan tildes para evitar problemas de codificación al pasar por pyswip en Windows. Las tildes se ponen en la capa de presentación.

## División de roles

- **Integrante A (Ingeniero del Conocimiento y Motor Simbólico):** secciones 5 a 7 de `base_conocimiento.pl`, es decir, la traza (`regla_disparada/3`), las hipótesis descartadas (`hipotesis_descartada/3`) y el desempate (`que_falta/5`, `poder_desempate/5`).
- **Integrante B (Ingeniero de Integración y Explicabilidad):** `main.py`, con el puente `PuenteProlog`, la ventana en Tkinter y los paneles "¿Por qué?" y "¿Qué falta?".

## Guion para el video (3 a 5 minutos)

**Caso 1 — Inferencia completa y "¿Por qué?"**

1. Marque *Equipo reducido*, *Presupuesto bajo* y *Hay que entregar en poco tiempo*.
2. Muestre el dictamen: **Monolito en capas**, prioridad **alta**, riesgo bajo, confianza alta, dictamen definitivo.
3. Abra **¿Por qué?** y recorra los niveles 1, 2 y 3. Señale la regla `estilo_viable/2 (\+)` y el cálculo `puntaje de monolito_capas = 9 - 0 = 9`.
4. Muestre las hipótesis descartadas: **Microservicios** por condición excluyente (`equipo_pequeno`) y **Orientada a eventos** sin evidencia (−2).

**Caso 2 — Datos incompletos y "¿Qué falta?"**

1. Pulse **Limpiar** y marque solo *Muchos usuarios concurrentes* y *Carga variable o impredecible*.
2. Aparece **empate técnico**: Serverless con 6 puntos contra Microservicios con 5, confianza media.
3. Abra **¿Qué falta?**. Compiten Serverless y Microservicios, y la primera pregunta es *"¿El equipo de desarrollo tiene menos de 5 personas?"* con poder 7: Serverless sube 2 puntos y Microservicios se descarta.
4. Pulse **"Sí, aplica: agregar este dato"**. Ahora el dictamen es **Serverless** con 8 puntos, prioridad alta y dictamen definitivo, y Microservicios aparece en descartadas.
5. Como cierre opcional, pruebe con un solo requisito (*Muchos usuarios*) para mostrar el estado de evidencia insuficiente.
