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
- `kpi/pdf.py` — ficha PDF.
