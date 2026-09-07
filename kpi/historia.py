"""
Histórico de cortes: convierte el panel de una foto en una película.

Cada vez que se carga un MOV-FIBRA nuevo se guarda una fila por ejecutivo (y por
tienda) con las cifras clave de ese corte. Con eso el panel puede mostrar:

  * la tendencia de los últimos cortes (mini-gráfico),
  * la variación respecto del corte anterior ("+3,2 pts").

El archivo vive en data/historia.csv. En Streamlit Cloud la carpeta data/ se
vacía cuando la app se reinicia, por eso la app ofrece descargar el histórico y
volver a cargarlo (ver "Gestión de archivos").
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import pandas as pd

from .config import DATA_DIR

RUTA = DATA_DIR / "historia.csv"

# columnas que se guardan en cada corte (clave interna del panel)
KPIS_HISTORIA = [
    "cump_ficha", "proy_pond", "tramo", "atenciones",
    "mov_real", "mov_cump", "mov_conv",
    "sus_real", "sus_cump", "sus_conv",
    "porta_real", "porta_cump", "porta_conv",
    "fib_real", "fib_cump", "conv_fibra",
    "eq_real", "eq_cump", "eq_conv",
    "seg_real", "seg_cump", "att_seg",
    "acc_real", "acc_cump", "acc_conv",
    "epa", "dias_trab", "dias_rest",
]

COLUMNAS = ["fecha", "nivel", "clave", "pdv"] + KPIS_HISTORIA


def _leer() -> pd.DataFrame:
    if not RUTA.exists():
        return pd.DataFrame(columns=COLUMNAS)
    try:
        df = pd.read_csv(RUTA, parse_dates=["fecha"])
        df["fecha"] = pd.to_datetime(df["fecha"]).dt.date
        return df
    except Exception:                                   # archivo corrupto o vacío
        return pd.DataFrame(columns=COLUMNAS)


def cargar() -> pd.DataFrame:
    """Histórico completo (una fila por corte y por ejecutivo/tienda)."""
    return _leer()


def _filas(df: pd.DataFrame, nivel: str, fecha: dt.date) -> list[dict]:
    out = []
    for _, r in df.iterrows():
        fila = {"fecha": fecha, "nivel": nivel,
                "clave": r.get("ejecutivo", ""), "pdv": r.get("pdv", "")}
        for k in KPIS_HISTORIA:
            fila[k] = r.get(k)
        out.append(fila)
    return out


def guardar_corte(datos) -> int:
    """
    Agrega (o reemplaza) el corte de `datos` en el histórico.

    Devuelve cuántas filas quedaron guardadas para esa fecha. Si el corte ya
    existía se sobrescribe, así volver a subir el mismo Excel no duplica datos.
    """
    if not datos.fecha_corte:
        return 0
    fecha = datos.fecha_corte

    nuevas = _filas(datos.ejecutivos[datos.ejecutivos["activo"]], "ejecutivo", fecha)
    nuevas += _filas(datos.tiendas, "tienda", fecha)
    if datos.total:
        fila = {"fecha": fecha, "nivel": "ctf", "clave": "CTF", "pdv": "CTF"}
        for k in KPIS_HISTORIA:
            fila[k] = datos.total.get(k)
        nuevas.append(fila)

    df_nuevo = pd.DataFrame(nuevas, columns=COLUMNAS)
    viejo = _leer()
    if not viejo.empty:
        viejo = viejo[viejo["fecha"] != fecha]           # reemplaza el mismo corte
    df = pd.concat([viejo, df_nuevo], ignore_index=True)
    df = df.sort_values(["fecha", "nivel", "clave"])
    RUTA.parent.mkdir(exist_ok=True)
    df.to_csv(RUTA, index=False)
    return len(df_nuevo)


def serie(clave: str, kpi: str, n: int = 30) -> pd.Series:
    """Serie temporal de un KPI para un ejecutivo / tienda / CTF."""
    df = _leer()
    if df.empty or kpi not in df.columns:
        return pd.Series(dtype=float)
    s = df[df["clave"].astype(str).str.upper() == str(clave).upper()]
    if s.empty:
        return pd.Series(dtype=float)
    s = s.sort_values("fecha").tail(n)
    return pd.Series(pd.to_numeric(s[kpi], errors="coerce").values, index=s["fecha"].values)


def variacion(clave: str, kpi: str) -> dict | None:
    """
    Variación del KPI respecto del corte anterior.

    Devuelve {'actual', 'anterior', 'delta', 'fecha_anterior'} o None si aún no
    hay dos cortes guardados para esa clave.
    """
    s = serie(clave, kpi, n=2)
    if len(s) < 2:
        return None
    actual, anterior = s.iloc[-1], s.iloc[-2]
    if pd.isna(actual) or pd.isna(anterior):
        return None
    return {"actual": float(actual), "anterior": float(anterior),
            "delta": float(actual) - float(anterior), "fecha_anterior": s.index[-2]}


def cortes_guardados() -> list[dt.date]:
    df = _leer()
    if df.empty:
        return []
    return sorted({f for f in df["fecha"]})


def resumen() -> str:
    fechas = cortes_guardados()
    if not fechas:
        return "Sin cortes guardados todavía."
    if len(fechas) == 1:
        return f"1 corte guardado ({fechas[0].strftime('%d/%m/%Y')}). Con el próximo ya verás tendencias."
    return (f"{len(fechas)} cortes guardados · desde {fechas[0].strftime('%d/%m/%Y')} "
            f"hasta {fechas[-1].strftime('%d/%m/%Y')}")


def exportar_csv() -> bytes:
    df = _leer()
    return df.to_csv(index=False).encode("utf-8-sig")


def importar_csv(contenido: bytes) -> int:
    """Restaura un histórico descargado previamente. Devuelve las filas cargadas."""
    import io
    df = pd.read_csv(io.BytesIO(contenido), parse_dates=["fecha"])
    df["fecha"] = pd.to_datetime(df["fecha"]).dt.date
    for c in COLUMNAS:
        if c not in df.columns:
            df[c] = None
    df = df[COLUMNAS]
    viejo = _leer()
    df = pd.concat([viejo, df], ignore_index=True).drop_duplicates(
        subset=["fecha", "nivel", "clave"], keep="last").sort_values(["fecha", "nivel", "clave"])
    RUTA.parent.mkdir(exist_ok=True)
    df.to_csv(RUTA, index=False)
    return len(df)
