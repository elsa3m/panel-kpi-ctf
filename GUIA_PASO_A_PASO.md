# Guía paso a paso · Replicar el Panel KPI CTF en Streamlit

Esta guía explica, de principio a fin, cómo levantar en tu PC y publicar en internet la réplica del panel **KPI Ejecutivo | Tiendas CTF** (https://gestion-ctf.streamlit.app/). El proyecto ya está programado en la carpeta `panel-kpi-ctf`; tu trabajo es ejecutarlo, revisarlo, subirlo a GitHub y desplegarlo en Streamlit Community Cloud.

---

## 0. ¿Cómo funciona un panel de este tipo?

Un panel Streamlit tiene tres piezas:

1. **Los datos**: los Excel mensuales (DRIVE TIENDAS, FIBRA DRIVE y ESCUCHAS ENTEL). Se cargan desde la propia app y quedan guardados en la carpeta `data/` del servidor.
2. **El código Python** (`app.py` y la carpeta `kpi/`): lee los Excel con `openpyxl` y `pandas`, calcula los KPI y dibuja las tarjetas con `streamlit`.
3. **El hosting**: el código vive en un repositorio de **GitHub**; **Streamlit Community Cloud** lee ese repositorio y publica la app en una URL `https://<nombre>.streamlit.app`. Cada vez que subes un cambio a GitHub, la app se actualiza sola.

```
Excel (tu PC) ──carga desde la app──▶ data/ (servidor) ──▶ kpi/loader.py ──▶ kpi/metrics.py ──▶ app.py (pantalla)
                                                                     ▲
GitHub (código) ◀── git push ── tu PC                                 │
      │                                                               │
      └──────────── Streamlit Community Cloud lee el repo y ejecuta app.py
```

---

## 1. Estructura del proyecto

```
panel-kpi-ctf/
├── app.py                  ← la aplicación (las 5 vistas)
├── requirements.txt        ← librerías que necesita Python
├── .streamlit/config.toml  ← tema oscuro y tamaño máximo de carga (200 MB)
├── .gitignore              ← evita subir los Excel al repositorio
├── kpi/
│   ├── columns.py          ← MAPA DE COLUMNAS de la hoja MOV-FIBRA (el archivo más importante)
│   ├── config.py           ← reglas de negocio: tramos, montos de bonos, colores, rutas
│   ├── loader.py           ← lectura de los Excel (MOV-FIBRA, METAS, FICHAS, EPA, BASE P EPA, CIERRE BONOS, FIBRA DRIVE, ESCUCHAS)
│   ├── metrics.py          ← cálculos: bonos, alertas, prioridades del corte, resumen de fibra
│   ├── ui.py               ← diseño (CSS) y componentes visuales (tarjetas, grillas, tablas)
│   └── pdf.py              ← "Descargar ficha PDF"
├── data/                   ← aquí se guardan los Excel activos (NO se sube a GitHub)
├── assets/logo.png         ← (opcional) logo CTF que aparece arriba a la izquierda
├── tests/test_replica.py   ← comprueba que los KPI coinciden con el panel original
├── README.md
└── GUIA_PASO_A_PASO.md     ← este documento
```

---

## 2. Probar la app en tu PC

### 2.1 Abrir una terminal en la carpeta del proyecto

**Opción A (recomendada)**

1. Abre la carpeta `panel-kpi-ctf` en el **Explorador de archivos de Windows** (la ventana de carpetas, no el navegador de internet). Adentro debes ver `app.py`, `kpi`, `requirements.txt`, etc.
2. En la parte superior de esa misma ventana hay una franja blanca larga que muestra la ruta: `OneDrive - CTF TECNOLOGIA SPA > CTF MOVIL > … > Streamlit > panel-kpi-ctf`. Esa es la **barra de direcciones**.
3. Haz **un clic** en un espacio vacío de esa franja (a la derecha del texto). La ruta queda seleccionada en azul.
4. Escribe las tres letras `cmd` (reemplazan la ruta seleccionada) y presiona **Enter**.
5. Se abre una ventana negra (la terminal). Su primera línea debe terminar en `\panel-kpi-ctf>`; eso confirma que estás dentro de la carpeta.

**Opción B**

Dentro de la carpeta, haz clic derecho en un espacio vacío (no sobre un archivo) y elige **"Abrir en Terminal"** (Windows 11) o, manteniendo Shift + clic derecho, **"Abrir ventana de PowerShell aquí"**. Si usas PowerShell, el comando de activación del paso 2.2 es `.venv\Scripts\Activate.ps1`.

En la terminal se escribe **un comando por línea**: lo escribes, presionas Enter y esperas a que termine (vuelve a aparecer la ruta con `>`) antes de escribir el siguiente.

### 2.2 Crear un entorno virtual e instalar las librerías (solo la primera vez)

```bat
python -m venv .venv
```
Crea la carpeta `.venv` (tarda unos segundos y no muestra nada).

```bat
.venv\Scripts\activate
```
Al inicio de la línea aparece `(.venv)`: el entorno está activo.

```bat
pip install -r requirements.txt
```
Descarga las librerías (1–3 minutos, muchas líneas). Termina con `Successfully installed…`.

Si `python` no se reconoce, instálalo desde https://www.python.org/downloads/ marcando la casilla **"Add python.exe to PATH"** y vuelve a abrir la terminal.

### 2.3 Ejecutar

```bat
streamlit run app.py
```

Se abre el navegador en `http://localhost:8501`. Deja la ventana negra abierta mientras uses la app; para detenerla presiona **Ctrl + C**. Las próximas veces solo necesitas abrir la terminal en la carpeta (2.1), escribir `.venv\Scripts\activate` y luego `streamlit run app.py`.

### 2.4 Cargar los Excel

1. Abre el desplegable **📁 GESTIÓN DE ARCHIVOS**.
2. En **MOV-FIBRA** sube `DRIVE TIENDAS SEPTIEMBRE 2026 CTF (1RA).xlsx`.
3. En **FIBRA DRIVE** sube `FIBRA DRIVE SEPTIEMBRE 2026 CTF.xlsx`.
4. En **ESCUCHAS ENTEL** sube el export del Power BI `Adherencia KPIs Hogar por PDV - Ejecutivo.xlsx` (opcional).
5. En **COLABORADORES** sube `DOTACIÓN CTF TECNOLOGIA <AÑO> (COMPLETO).xlsx` (opcional): completa la antigüedad y el cumpleaños en la ficha del ejecutivo.

Los archivos quedan copiados dentro de `data/` con nombres fijos (`mov_fibra.xlsx`, `fibra_drive.xlsx`, `escuchas_entel.xlsx`). Para actualizar el mes solo vuelves a subir el archivo nuevo.

### 2.5 Verificar que los números coinciden

```bat
python tests\test_replica.py
```

Debe imprimir `OK: todos los KPI de CMA_EMONTILVA coinciden con el panel original.` La prueba compara 60 valores (24.72 %, 78.04 %, tramo 0, 11 de 91, bonos, equipos, seguros, etc.) con lo que mostraba el panel original al corte 03/09/2026.

---

## 3. Cómo lee la app los Excel (para que puedas mantenerla)

### 3.1 Hoja MOV-FIBRA (archivo DRIVE TIENDAS)

- Los encabezados definitivos están en la **fila 6** y los datos parten en la **fila 7**.
- Cada fila es una **tienda** (cuando la columna D repite el nombre de la tienda) o un **ejecutivo** (columna D = código `CMA_…`). La fila con PDV = `CTF` es el **total**.
- Como hay muchos encabezados repetidos ("META", "REAL", "FALTA"…), la app ubica cada dato **por número de columna** en `kpi/columns.py`. Ejemplo: `"mov_real": (13, "REAL")` significa *columna 13 (M), cuyo encabezado en la fila 6 debe decir REAL*. Si un mes cambian el orden de columnas, la app muestra un aviso amarillo indicando qué columna no coincide: ajusta el número en `columns.py` y listo.
- Celdas sueltas: **B4** = fecha del corte; **B3** = avance esperado (días trabajados / días del mes); **fila 5, columnas 145–151** = pesos de la ficha; **fila 4** = estándares mínimos (conv. 26 %, 24 %, 12 %, attach 32 %, etc.), que alimentan las alertas.
- Un ejecutivo se considera **activo** si tiene META TOTAL MÓVIL > 0 (por eso PDV 5003 muestra 3 ejecutivos y no 4).

### 3.2 Otras hojas del mismo archivo

| Hoja | Para qué la usa la app |
|---|---|
| METAS | Nombre completo del ejecutivo (columna E) |
| CIERRE BONOS. | Jornada FT / PT (columna F) |
| EPA | Tabla "EPA … POR EJECUTIVO" (EPA actual, Q total, actitud) |
| BASE P EPA | Encuestas individuales (conteo y "por recuperar" = notas 0 y −1) |
| FICHAS | Referencia de pesos y reglas de bonos (los valores están copiados en `config.py`) |

### 3.3 Archivo FIBRA DRIVE

| Hoja | Uso |
|---|---|
| AVANCE FIBRAS (encabezado fila 2) | Última solicitud del ejecutivo, solicitudes del periodo, estado de cada solicitud |
| RESUMEN (encabezado fila 2) | Meta / real fibra y TV por tienda y ejecutivo |
| EVOLUTIVO | Solicitudes por día (disponible en `fib.evolutivo` si quieres graficarlo) |

### 3.4 Archivo ESCUCHAS ENTEL

Es el export del informe de Power BI **"Adherencia KPIs Hogar por PDV - Ejecutivo"** (en la visualización: ⋯ → *Exportar datos* → Excel). La app lee la hoja `Export` y clasifica cada fila:

| Fila | Cómo se reconoce | Uso |
|---|---|---|
| Ejecutivo | `agent_id` = `CMA_…` | Tarjetas de escuchas del ejecutivo |
| Tienda | `agent_id` = `Total` y `PDV` = `5245 - Arauco Maipú` | Referencia "Tienda" |
| CTF | `PDV` = `Total` | Referencia "CTF" |

Columnas usadas: *KPI Foco N Auditadas, Starlink % Todas, Latam Pass % Todas, Motivo Hogar %, Fibra Calidad %, Fibra Estabilidad %, Motivo Portabilidad %, Porta Objeciones %, Porta Urgencia %*.

> La referencia **"Canal"** que muestra el panel original no viene en este export porque el informe está filtrado por `socio es CTF TECNOLOGIA SPA`. Para tenerla, exporta el mismo visual quitando ese filtro y agrega esas filas al archivo.

### 3.5 Archivo COLABORADORES (DOTACIÓN)

Completa **antigüedad** y **cumpleaños** en la ficha del ejecutivo. La app lee la hoja `DOTACIÓN` y usa el encabezado de la fila 2.

| Columna del Excel | Uso en el panel |
|---|---|
| IDENTIDAD RED | Código `CMA_…` que enlaza con MOV-FIBRA |
| NOMBRE COMPLETO | Nombre del ejecutivo |
| FECHA INGRESO | Antigüedad ("9 meses", "2 años, 3 meses") |
| FECHA NACIMIENTO | Cumpleaños ("16 de abril · en 12 días") |
| JORNADA | Full-time / Part-time |

> **Importante — datos personales.** La planilla de dotación contiene RUT, direcciones, teléfonos, contactos de emergencia y credenciales. Al subirla, la app **extrae solo las cinco columnas de la tabla anterior y guarda únicamente esa versión reducida**; el archivo original nunca se escribe en el servidor. Además, `data/` está excluido del repositorio por el `.gitignore`, así que estos datos no llegan a GitHub. Aun así, evita dejar copias del archivo completo en carpetas compartidas.

### 3.6 Archivo ESCUCHAS — formato antiguo

No estaba en la carpeta, así que la app espera una hoja con una fila de encabezados que contenga **EJECUTIVO** (o USUARIO) y columnas **LATAM PASS, HOGAR, CALIDAD, ESTABILIDAD, MOTIVO, OBJECIONES, URGENCIA**. Las filas cuyo "ejecutivo" sea `CANAL` o `CTF` se usan como referencias del canal y de CTF, y la fila con el nombre de la tienda como referencia de tienda. Si tu archivo real tiene otro formato, ajusta `ESCUCHAS_ALIAS` en `kpi/loader.py` (o pásamelo y lo adapto).

### 3.5 Reglas de negocio (`kpi/config.py`)

- **Tramos**: ≤79,9 % → 0 · 80–89,99 → 1 · 90–94,99 → 2 · 95–99,99 → 3 · 100–104,99 → 4 · 105–109,99 → 5 · 110–119,99 → 6 · ≥120 → 7.
- **Bono portabilidad**: FULL $60.000 / PT $30.000 al cumplir META BONO PORTA. **Bono winner**: $40.000 / $20.000. **Bono foco**: $100.000 / $80.000 / $40.000 según % (revisa los umbrales de `BONO_FOCO` con Coordinación).
- **Alertas / prioridades**: para cada producto se genera *"bajo corte · debería llevar N"* cuando REAL < DEBEN LLEVAR, y *"bajo estándar · mínimo X %"* cuando una conversión o attach está por debajo de la fila 4. Se agrupan por foco (MOVILIDAD, FIBRA, EQUIPOS, SEGUROS, ACCESORIOS) y se muestran las 3 con más peso.

> Diferencia conocida con el panel original: allí "deben llevar al corte" usa avance = días trabajados / 30 (10,0 %); esta réplica usa la celda B3 del Excel (3/28 = 10,7 %), que es el mismo valor que usa la columna DEBEN LLEVAR de la hoja. Si prefieres el criterio del original, cambia `avance_esperado` en `loader.py` por `dias_trab / 30`.

---

## 4. Subir el proyecto a GitHub

### 4.1 Instalar Git (solo la primera vez)

1. En el navegador entra a https://git-scm.com/download/win y haz clic en **"Click here to download"** (o "64-bit Git for Windows Setup"). Se descarga `Git-2.xx-64-bit.exe` en Descargas.
2. Abre ese archivo con doble clic. Si Windows pregunta si permites cambios, responde **Sí**.
3. El instalador muestra unas 10 pantallas de opciones: **no cambies nada**, presiona **Next** en cada una y al final **Install**. Tarda 1–2 minutos. Presiona **Finish**.
4. **Cierra la terminal** que tenías abierta y vuelve a abrirla (punto 2.1); si no, la terminal no reconoce a Git.
5. Comprueba con `git --version`: debe responder `git version 2.xx…`. Si dice que no se reconoce, reinicia el PC y prueba de nuevo.
6. Configura tu nombre y correo (uno por línea; no muestran nada al terminar, es normal):

```bat
git config --global user.name "Elsa"
git config --global user.email "elsa3m@gmail.com"
```

### 4.2 Crear el repositorio en GitHub

1. Entra a https://github.com/new.
2. **Repository name**: `panel-kpi-ctf`. Visibilidad: **Private** (los datos de la empresa no deben ser públicos; Streamlit Cloud puede leer repos privados).
3. No marques "Add a README" (ya existe). Clic en **Create repository**.

### 4.3 Subir el código desde tu PC

En la terminal, dentro de `panel-kpi-ctf`:

```bat
git init
git add .
git commit -m "Panel KPI CTF - version inicial"
git branch -M main
git remote add origin https://github.com/elsa3m/panel-kpi-ctf.git
git push -u origin main
```

La primera vez GitHub te pedirá iniciar sesión en una ventana del navegador. Gracias al `.gitignore`, los Excel de `data/` **no** se suben.

### 4.4 Actualizar el código más adelante

Cada vez que cambies algo (por ejemplo `columns.py`):

```bat
git add .
git commit -m "Descripcion del cambio"
git push
```

Streamlit Cloud detecta el push y reinicia la app automáticamente.

---

## 5. Publicar en Streamlit Community Cloud

1. Entra a https://share.streamlit.io e inicia sesión con tu cuenta de GitHub (así puede ver tus repositorios).
2. Clic en **Create app** → **Deploy a public app from GitHub** (aunque el repo sea privado, funciona).
3. **Repository**: `elsa3m/panel-kpi-ctf` · **Branch**: `main` · **Main file path**: `app.py`.
4. **App URL**: elige el subdominio, por ejemplo `kpi-ctf` → la app quedará en `https://kpi-ctf.streamlit.app`.
5. (Opcional) En **Advanced settings** deja Python 3.11 o 3.12.
6. Clic en **Deploy**. En 1–3 minutos la app estará en línea.
7. Abre la app, entra a **Gestión de archivos** y sube los tres Excel.

### 5.1 Importante sobre los archivos en Streamlit Cloud

Los archivos subidos quedan en el disco del servidor de Streamlit. **Se pierden cuando la app se reinicia** (nuevo push a GitHub, reboot desde el panel de Streamlit, o si la app estuvo dormida y se vuelve a levantar). Es exactamente el aviso que muestra el panel original: *"Mantén también una copia de respaldo externa"*. Después de cada reinicio vuelve a cargar los Excel. Si en el futuro quieres que persistan de verdad, la alternativa es guardarlos en Google Drive / OneDrive con una cuenta de servicio o en un bucket S3; te lo puedo armar cuando lo necesites.

### 5.2 Controlar quién ve la app

En Streamlit Cloud → tu app → **Settings → Sharing** puedes marcar la app como privada e invitar por correo a las personas que pueden verla (los jefes de tienda, por ejemplo).

---

## 6. Rutina mensual / semanal

1. Guardar el nuevo `DRIVE TIENDAS <MES> <AÑO> CTF.xlsx` y `FIBRA DRIVE <MES> <AÑO> CTF.xlsx` en OneDrive.
2. Abrir la app → Gestión de archivos → subir ambos (y ESCUCHAS si cambió).
3. Revisar el aviso amarillo (si aparece) por columnas desplazadas → corregir `kpi/columns.py` → `git push`.
4. Ejecutar `python tests\test_replica.py` cuando cambies código de cálculo, para asegurarte de que nada se rompió.

---

## 7. Personalizaciones frecuentes

| Quiero… | Dónde |
|---|---|
| Cambiar colores del panel | `kpi/config.py` → `COLORES` y `kpi/ui.py` → CSS |
| Poner el logo de CTF | Guarda `assets/logo.png` |
| Cambiar montos o tramos de bonos | `kpi/config.py` |
| Agregar un KPI nuevo de MOV-FIBRA | 1) agrega la columna en `kpi/columns.py`; 2) muéstralo con `celda(...)` en el bloque correspondiente de `app.py` |
| Cambiar el orden o textos de las prioridades | `kpi/metrics.py` → `alertas()` y `PESO_FOCO` |
| Agregar una sexta vista | crea `def vista_nueva():` en `app.py` y agrégala a `VISTAS` y al diccionario final |

---

## 8. Solución de problemas

- **"streamlit no se reconoce"** → activa el entorno: `.venv\Scripts\activate`.
- **Aviso "MOV-FIBRA col 13 (mov_real): se esperaba 'REAL'…"** → cambió la estructura del Excel; corrige el número de columna en `kpi/columns.py`.
- **La app en Streamlit Cloud dice "Carga el Excel MOV-FIBRA"** → la app se reinició; vuelve a subir los archivos.
- **Error al leer un Excel** → guárdalo desde Excel como `.xlsx` normal (no `.xlsb`) y verifica que las hojas se llamen `MOV-FIBRA`, `METAS`, `AVANCE FIBRAS`, `RESUMEN`.
- **Números distintos al original** → ejecuta `python tests\test_replica.py` y revisa qué KPI difiere.
