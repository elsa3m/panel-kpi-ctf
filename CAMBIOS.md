# Qué cambió en esta versión

Resumen de las mejoras, para que puedas revisarlas una por una antes de hacer
commit. Si algo no te gusta, se puede volver atrás sin perder el resto.

---

## 1. Histórico de cortes (antes el panel era una foto; ahora es una película)

Cada vez que cargas un MOV-FIBRA nuevo, el panel guarda ese corte. Con dos o más
cortes vas a ver, bajo el **% Real** y el **% Proyección**:

- un chip con la variación: `▲ +3,2 pts vs. 30/08`
- un mini-gráfico con la tendencia de los últimos cortes

También aparece en la tabla **Cómo va frente a sus pares**, columna
*vs. corte anterior*.

**Importante:** Streamlit Cloud borra la carpeta `data/` cada vez que la app
reinicia. En *Gestión de archivos* hay un botón **📥 Descargar histórico (CSV)** y
otro para volver a cargarlo. Descárgalo después de cada corte y guárdalo en el
Drive: es el respaldo de la memoria del panel.

## 2. Proyecciones honestas

Antes el panel mostraba proyecciones de 267 %, 363 % o tasas de instalación de
3.400 %. Eso no es un logro, es un dato con problema o una base muy chica.

Ahora:

- las proyecciones sobre **150 %** se muestran como `> 150%`
- las tasas y factores sobre **100 %** se muestran topados y con una marca `⚠`
- cada proyección lleva un **nivel de confianza** según los días trabajados:
  con menos de 5 días dice explícitamente que es referencial
- el bloque de Fibra avisa cuando el factor de producción o la tasa de
  instalación vienen sobre 100 % (suele ser `#REF!` o una división con base cero
  en el Excel)

Los números originales no se tocaron: solo se muestra de otra forma lo que ya
estaba mal calculado en la planilla, para que no te lleve a una conclusión falsa.

## 3. Colores, tamaños y contrastes

- **Verde**: pasó de lima (`#84cc16`) a `#4ade80`. El lima y el amarillo se
  confundían en visión protán (daltonismo rojo-verde), que afecta a
  ~1 de cada 12 hombres. Con el cambio la diferencia pasa el umbral.
- **Etiqueta "T9"** de los resúmenes: el celeste con texto blanco daba 2,77:1 de
  contraste (el mínimo legible es 4,5:1). Ahora usa un azul más oscuro: 5,9:1.
- **Barra de los productos**: el riel gris claro casi no se distinguía del fondo
  blanco de la tarjeta (1,42:1). Ahora es más oscuro y se ve.
- **Tamaños**: nada baja de 12 px. Antes había textos de 11 px.
- **Semáforos con forma además de color**: ▲ verde, ■ amarillo, ▼ rojo. Así se
  entienden aunque la persona no distinga los colores o imprima en blanco y negro.

## 4. Diseño más compacto y con desplegables

- Tarjetas y espacios más apretados: entra bastante más en la misma pantalla.
- Lo urgente quedó **arriba**: en Vista Ejecutivo las *3 prioridades del corte*
  subieron justo debajo de los indicadores.
- Lo de consulta quedó en **desplegables** cerrados: bonos, energía/protección/EPA,
  escuchas, encuestas, ranking, bono winner, gestión de ejecutivos.
- Las tablas grandes ahora tienen **cabecera fija** y **primera columna fija** al
  desplazarse: ya no se pierde de vista quién es cada fila.

## 5. Comparación contra pares

Nueva tabla **⚖️ Cómo va frente a sus pares** en Vista Ejecutivo: para cada KPI
muestra el valor del ejecutivo, el promedio de su tienda, el promedio de CTF, la
diferencia y **en qué puesto va de los 31**. Un 26 % de conversión no dice nada
solo; saber que es el puesto 11 de 31 sí.

## 6. Quién necesita apoyo hoy

En Vista Tiendas / CTF, un tablero con el equipo ordenado del que más apoyo
necesita al que menos, con su tramo, cantidad de alertas y su foco principal.
Se muestran los 8 primeros y el resto queda en un desplegable.

Importante: el "en riesgo" se mide contra el **avance esperado del mes**, no
contra el 100 %. El día 3 nadie lleva 80 % y pintar a todos de rojo no informa.

## 7. Resumen accionable para enviar

En Vista Ejecutivo y en Jefe de Tienda hay un desplegable **📤 Resumen para
enviar**: texto plano con el corte, el cumplimiento, las 3 prioridades y lo que
falta por producto. Se copia y se pega en un WhatsApp o un correo, o se descarga
como `.txt`.

## 8. Vista para celular

- En celular las tarjetas se acomodan **de a dos por fila** en vez de una sola:
  se ve más sin desplazarse tanto.
- Los nombres largos ya no se cortan.
- Las tablas se desplazan de lado con la primera columna fija.
- Los botones de vista se ajustan al ancho de la pantalla.

Probado en 390 px (tamaño de un teléfono) y en 1.560 px (notebook), en las cinco
vistas, sin errores.

---

## Qué NO cambió

- Ningún cálculo de negocio: tramos, bonos, ficha ponderada, alertas.
- La prueba de regresión (`python tests/test_replica.py`) sigue comparando 60
  valores de CMA_EMONTILVA contra el panel original y pasa.
- La única diferencia de formato: los porcentajes ahora usan **coma** decimal en
  todo el panel (formato chileno). Antes convivían `24.72%` y `26,2%`.

## Cómo volver atrás

```bash
git log --oneline          # ver los commits
git reset --hard <commit>  # volver a ese punto
```

Si ya habías creado la etiqueta de respaldo:

```bash
git reset --hard version-ok-07sep
```
