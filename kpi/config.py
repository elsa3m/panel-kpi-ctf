"""
Reglas de negocio configurables del Panel KPI CTF.

Todo lo que NO se puede deducir del Excel vive aquí, para que se pueda ajustar
sin tocar el resto del código.
"""
from pathlib import Path

# ---------------------------------------------------------------------------
# Rutas
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"          # aquí se guardan los Excel "activos"
DATA_DIR.mkdir(exist_ok=True)
ASSETS_DIR = BASE_DIR / "assets"

# Nombre lógico -> (archivo guardado en data/, descripción, hojas requeridas)
FUENTES = {
    "MOV-FIBRA": {
        "archivo": "mov_fibra.xlsx",
        "titulo": "MOV-FIBRA",
        "icono": "📊",
        "ayuda": "Excel DRIVE TIENDAS <MES> <AÑO> CTF (hoja MOV-FIBRA, METAS, FICHAS, EPA, BASE P EPA, CIERRE BONOS).",
        "hojas": ["MOV-FIBRA", "METAS"],
    },
    "FIBRA DRIVE": {
        "archivo": "fibra_drive.xlsx",
        "titulo": "FIBRA DRIVE",
        "icono": "📡",
        "ayuda": "Excel FIBRA DRIVE <MES> <AÑO> CTF (hojas AVANCE FIBRAS, RESUMEN, EVOLUTIVO, ESTATUS).",
        "hojas": ["AVANCE FIBRAS", "RESUMEN"],
    },
    "ESCUCHAS ENTEL": {
        "archivo": "escuchas_entel.xlsx",
        "titulo": "ESCUCHAS ENTEL",
        "icono": "🎧",
        "ayuda": "Export del Power BI 'Adherencia KPIs Hogar por PDV - Ejecutivo' (hoja Export).",
        "hojas": [],
    },
    "COLABORADORES": {
        "archivo": "colaboradores.xlsx",
        "titulo": "COLABORADORES",
        "icono": "👥",
        "ayuda": "Excel DOTACIÓN CTF. Solo se guardan código, nombre, fecha de ingreso, fecha de nacimiento y jornada; el resto de los datos personales se descarta al cargar.",
        "hojas": ["DOTACIÓN"],
        "reducir": True,
    },
}

# ---------------------------------------------------------------------------
# Tramos de cumplimiento de la ficha (hoja CIERRE BONOS, columnas Y:AA).
# Lista de (límite inferior, tramo). Se evalúa de mayor a menor.
# Tabla confirmada por Coordinación CTF (septiembre 2026).
# ---------------------------------------------------------------------------
TRAMOS = [
    (1.20, 7),   # >= 120 %
    (1.10, 6),   # 110 % - 119,99 %
    (1.05, 5),   # 105 % - 109,99 %
    (1.00, 4),   # 100 % - 104,99 %
    (0.95, 3),   #  95 % -  99,99 %
    (0.90, 2),   #  90 % -  94,99 %
    (0.80, 1),   #  80 % -  89,99 %
    (0.00, 0),   # <= 79,9 %
]

def tramo_de(cumplimiento: float) -> int:
    """Devuelve el tramo (0..7) según el % de cumplimiento ponderado de la ficha."""
    if cumplimiento is None:
        return 0
    for limite, tramo in TRAMOS:
        if cumplimiento >= limite:
            return tramo
    return 0

def etiqueta_cumplimiento(cumplimiento: float) -> str:
    if cumplimiento is None:
        return "SIN DATO"
    if cumplimiento >= 1.0:
        return "CUMPLE"
    if cumplimiento >= 0.8:
        return "EN TRAMO"
    return "BAJO CUMPLIMIENTO"

# ---------------------------------------------------------------------------
# Bonos (hoja FICHAS). Montos en pesos chilenos.
# ---------------------------------------------------------------------------
BONO_PORTA = {"FULL": 60_000, "PT": 30_000}            # al cumplir META BONO PORTA
BONO_WINNER = {"FULL": 40_000, "PT": 20_000}           # al cumplir 100 % acumulado (tope 120 % c/u)
BONO_FOCO = [                                           # (mínimo de % bono foco, monto FULL, monto PT)
    (1.00, 100_000, 50_000),
    (0.90,  80_000, 40_000),
    (0.80,  40_000, 20_000),
]
TOPE_KPI_FICHA = 1.30        # MAX 130 % en cada KPI de la ficha
TOPE_FIBRA_FICHA = 1.50      # FIBRA MAX 150 %
FIBRA_MINIMO_FICHA = 0.50    # REAL FIBRA (<50 % CUMP = 0 %)

# ---------------------------------------------------------------------------
# Alertas / prioridades del corte
# ---------------------------------------------------------------------------
FOCOS = ["MOVIL", "FIBRA", "EQUIPOS", "SEGUROS", "ACCESORIOS"]

# Umbrales fijos de fibra que no vienen en la fila 4
ESTANDAR_TASA_INSTALACION = 0.75
ESTANDAR_PCT_FACTIBLES = 0.50

# ---------------------------------------------------------------------------
# Proyecciones honestas
# ---------------------------------------------------------------------------
DIAS_MIN_PROYECCION = 5      # con menos días trabajados la proyección es poco confiable
TOPE_PROYECCION_VISUAL = 1.50  # no se muestran proyecciones sobre 150 % (se marcan como "> 150 %")
TOPE_TASA_VISUAL = 1.00      # tasas / factores sobre 100 % indican un dato con problema

# ---------------------------------------------------------------------------
# Apariencia
# ---------------------------------------------------------------------------
# Paleta revisada para daltonismo (protanopia / deuteranopia / tritanopia) y
# contraste AA sobre el fondo oscuro. El verde pasó de lima (#84cc16) a
# #4ade80 porque el lima y el amarillo se confundían en visión protán.
COLORES = {
    "fondo": "#050b1a",
    "card": "#0b1631",
    "borde": "#1e3a8a",
    "cyan": "#22d3ee",
    "verde": "#4ade80",
    "amarillo": "#fbbf24",
    "rojo": "#fb7185",
    "morado": "#c4b5fd",
    "naranjo": "#fdba74",
    "texto": "#e5e7eb",
    "texto2": "#a8b3c4",
}

# Colores de relleno de los semáforos (texto oscuro encima) y de las barras.
SEMAFORO = {
    "v": ("#22c55e", "#04240f"),
    "a": ("#facc15", "#3a2900"),
    "r": ("#f87171", "#3f0708"),
    "t": ("#0369a1", "#ffffff"),
}
