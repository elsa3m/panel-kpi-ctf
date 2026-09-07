# Panel KPI CTF

Réplica en Streamlit del panel **KPI Ejecutivo | Tiendas CTF**: cinco vistas (Vista Ejecutivo, Vista Tiendas / CTF, Jefe de Tienda, Fibra Tiendas, Fibra Ejecutivos) alimentadas por los Excel mensuales DRIVE TIENDAS, FIBRA DRIVE y ESCUCHAS ENTEL.

## Ejecutar en local

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows   (source .venv/bin/activate en Mac/Linux)
pip install -r requirements.txt
streamlit run app.py
```

Luego, en la app, abre **Gestión de archivos** y sube los Excel. Quedan guardados en `data/` (carpeta excluida del repositorio).

## Verificar

```bash
python tests/test_replica.py
```

## Despliegue

Repositorio en GitHub → https://share.streamlit.io → *Create app* → `app.py`. Detalles en **GUIA_PASO_A_PASO.md**.

## Estructura

- `app.py` — vistas y componentes.
- `kpi/columns.py` — mapa de columnas de la hoja MOV-FIBRA (ajustar si cambia el Excel).
- `kpi/config.py` — tramos, bonos, colores.
- `kpi/loader.py` — lectura de los Excel.
- `kpi/metrics.py` — bonos, alertas, prioridades del corte.
- `kpi/ui.py` — CSS y tarjetas.
- `kpi/historia.py` — histórico de cortes (tendencias y variación vs. corte anterior).
- `kpi/pdf.py` — ficha PDF.

## Histórico de cortes

Cada Excel MOV-FIBRA que se carga queda registrado en `data/historia.csv` (una fila
por ejecutivo y por corte). Con dos o más cortes el panel muestra la variación
("+3,2 pts vs. 30/08") y un mini-gráfico de tendencia.

En Streamlit Cloud la carpeta `data/` se borra cuando la app reinicia. Por eso en
*Gestión de archivos* hay un botón para **descargar el histórico** y otro para
**volver a cargarlo**. Conviene descargarlo después de cada corte.

## Después de tocar `kpi/`

Streamlit Cloud recarga `app.py` solo, pero mantiene en memoria los módulos de
`kpi/`. Después de subir cambios en esa carpeta hay que usar **Reboot app** en
share.streamlit.io.

Fuentes de datos (todas se cargan desde la app): **MOV-FIBRA** (DRIVE TIENDAS), **FIBRA DRIVE**, **ESCUCHAS ENTEL** (export de Power BI) y **COLABORADORES** (dotación; solo se guardan código, nombre, ingreso, nacimiento y jornada).
