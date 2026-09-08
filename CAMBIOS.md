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

# Segunda ronda de ajustes

## 9. Acumulados por tienda desde la hoja OT#

La vista **Jefe de Tienda** y la vista **Tiendas / CTF** ahora toman los
acumulados de la pestaña **OT#** del Drive, que es donde están consolidados
oficialmente, en vez de sumar o promediar a los ejecutivos.

Esto resolvió de paso una diferencia que estaba pendiente: el total CTF que yo
calculaba promediando ejecutivos daba 21,78 % / 53,22 %, y el panel original
mostraba 25,74 % / 90,23 %. Esos números salen de OT#. Ahora coinciden.

Cada vista dice de dónde viene el dato. Si algún mes el Excel no trae la hoja
OT#, el panel avisa y usa el consolidado de MOV-FIBRA.

## 10. Bloqueo de la vista Jefe de Tienda

La vista pide contraseña. **No está en el código**: el repositorio es público y
una clave escrita ahí quedaría a la vista de cualquiera. Va en los *secrets* de
Streamlit:

1. **share.streamlit.io** → tu app → **Settings** → **Secrets**
2. Escribe: `clave_jefes = "la-clave-que-elijas"` y guarda
3. La app se reinicia sola

Para probar en tu computador: crea `.streamlit/secrets.toml` en la carpeta del
proyecto con esa misma línea. Ese archivo está en `.gitignore`, así que nunca se
sube a GitHub.

Mientras no la configures, la vista muestra estas mismas instrucciones. Adentro
hay un botón **🔒 Bloquear vista** para cerrarla.

## 11. Ajustes visuales

- **Logo**: se usa el archivo nítido, montado sobre una placa blanca redondeada.
  El PNG trae fondo blanco y el texto "tecnología" casi negro, así que sobre el
  fondo oscuro del panel desaparecería; la placa mantiene los colores de marca.
  Para cambiarlo más adelante basta reemplazar `assets/logo.png`.
- **Casillas de Tienda y Ejecutivo**: fondo blanco, borde cian y letra más
  grande. Ahora se ve que son desplegables.
- **Las cuatro tarjetas de la cabecera** (PDV, ejecutivo, % Real, % Proyección)
  quedaron del mismo alto y ocupando el mismo espacio.
- **Títulos más grandes**: los de las tarjetas de 0,80 a 0,92 rem; los de las
  mini-tarjetas y celdas de 0,75 a 0,85 rem.
- **MOVILIDAD → MOVIL** en todo el panel.
- **PROM. CTF** eliminada de la comparación contra pares. Queda "Puesto en CTF",
  que dice lo mismo de forma más útil.
- **Conv. SUS** agregada a la comparación contra pares (y también Conv. acc).

## 12. Fibra Ejecutivos reorganizada

Ahora se lee como una secuencia, no como un montón de tarjetas sueltas:

1. 🎯 **Meta del mes** — cuánto falta para cerrar, con una línea directa:
   "▼ Va 2 instalaciones bajo el corte"
2. 📦 **Sus órdenes** — en qué estado está cada solicitud
3. 🔎 **Dónde se pierden** — pendientes, rechazos y reagendamientos
4. 📋 **Detalle** — la tabla completa, para quien la necesite

---

# 13. ⚙️ Personalizar panel — para editarlo sin pedírmelo

Al final de cada vista hay un desplegable **⚙️ PERSONALIZAR PANEL** con cuatro
pestañas. Lo que cambies ahí queda guardado y se aplica de inmediato.

### 📑 Secciones
Una tabla con todas las secciones de esa vista. Puedes:

- **Renombrarlas** — escribe encima del nombre (así habrías hecho tú misma el
  cambio de MOVILIDAD a MOVIL)
- **Ocultarlas** — desmarca "Se ve"
- **Abrirlas o cerrarlas por defecto** — la casilla "Abierta"
- **Reordenarlas** — la columna "Orden": 0 va primero

Luego **💾 Guardar secciones**.

### 🎨 Colores y tamaños
Un selector de color por cada color del panel, el tamaño del texto (de 0,85 a
1,30) y qué tan apretadas van las tarjetas (Compacto / Normal / Amplio).

Un aviso: la paleta de fábrica está calculada para que se distinga bien también
en daltonismo. Si cambias el verde o el amarillo, procura que no queden
parecidos entre sí.

### 🚦 Umbrales
Desde qué punto un número se pinta verde, amarillo o rojo. Y, si quieres, puedes
dejar de usar los umbrales de la hoja CONV-CUMP y fijar tus propios mínimos por
KPI (en tanto por uno: 0,26 = 26 %).

### 💾 Respaldo
En Streamlit Cloud la configuración se borra cuando la app reinicia, igual que
el histórico. **Descarga la configuración** cuando la dejes como te gusta, y
vuelve a cargarla si se pierde. También está **♻️ Restaurar todo**, que vuelve
a los valores de fábrica.

**Ojo:** los cambios son para todos los que abran el panel, no solo para ti.

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
