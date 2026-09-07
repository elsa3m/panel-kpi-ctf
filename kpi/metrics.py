"""
Cálculos derivados: bonos, alertas / prioridades del corte, resumen de fibra,
proyecciones. Reciben la fila del ejecutivo (dict o Series) y los parámetros.
"""
from __future__ import annotations

import datetime as dt
import math

import pandas as pd

from . import config as cfg


# ---------------------------------------------------------------------------
# formato
# ---------------------------------------------------------------------------
def v(x, default=0.0):
    """Valor numérico seguro (NaN / None -> default)."""
    try:
        if x is None or (isinstance(x, float) and math.isnan(x)):
            return default
        return float(x)
    except (TypeError, ValueError):
        return default


def pct(x, dec=2, default="—"):
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return default
    return f"{x * 100:.{dec}f}%".replace(".", ",") if dec == 1 else f"{x * 100:.{dec}f}%"


def pesos(x, default="$0"):
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return default
    return "$" + f"{int(round(x)):,}".replace(",", ".")


def entero(x, default="0"):
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return default
    return f"{int(round(x)):,}".replace(",", ".")


def fecha_txt(f: dt.date | None) -> str:
    return f.strftime("%d/%m/%Y") if f else "—"


MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio",
         "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]


def antiguedad(ingreso: dt.date | None, hoy: dt.date | None = None) -> str:
    """'2 años, 3 meses' a partir de la fecha de ingreso."""
    if not isinstance(ingreso, dt.date):
        return "Por completar"
    hoy = hoy or dt.date.today()
    anios = hoy.year - ingreso.year
    meses = hoy.month - ingreso.month
    if hoy.day < ingreso.day:
        meses -= 1
    if meses < 0:
        anios, meses = anios - 1, meses + 12
    if anios < 0:
        return "Por completar"
    partes = []
    if anios:
        partes.append(f"{anios} año" + ("s" if anios != 1 else ""))
    partes.append(f"{meses} mes" + ("es" if meses != 1 else ""))
    return ", ".join(partes)


def cumpleanos(nacimiento: dt.date | None, hoy: dt.date | None = None) -> tuple[str, str]:
    """Devuelve ('4 de junio', 'Hoy 🎉' / 'en 12 días' / 'hace 5 días')."""
    if not isinstance(nacimiento, dt.date):
        return "Por completar", ""
    hoy = hoy or dt.date.today()
    fecha = f"{nacimiento.day} de {MESES[nacimiento.month - 1]}"
    try:
        prox = nacimiento.replace(year=hoy.year)
    except ValueError:                      # 29 de febrero
        prox = nacimiento.replace(year=hoy.year, day=28)
    dias = (prox - hoy).days
    if dias == 0:
        return fecha, "¡Hoy! 🎉"
    if dias > 0:
        return fecha, f"en {dias} día" + ("s" if dias != 1 else "")
    return fecha, f"hace {-dias} día" + ("s" if dias != -1 else "")


def ceil_pos(x) -> int:
    return max(0, int(math.ceil(v(x) - 1e-9)))


# ---------------------------------------------------------------------------
# bonos
# ---------------------------------------------------------------------------
def bono_foco(e, jornada: str = "FULL") -> dict:
    """Bono foco: 50 % cumplimiento suscripción + 50 % cumplimiento fibra."""
    porcentaje = v(e.get("bf_pct"))
    estado = str(e.get("bf_estado") or "").upper()
    monto = 0
    for minimo, full, pt in cfg.BONO_FOCO:
        if porcentaje >= minimo:
            monto = full if jornada == "FULL" else pt
            break
    gana = estado == "OK" or (estado == "" and monto > 0)
    return {
        "cump_sus": v(e.get("bf_cump_sus")),
        "cump_fib": v(e.get("bf_cump_fib")),
        "pct": porcentaje,
        "gana": gana,
        "monto": monto if gana else 0,
        "estado": "GANA" if gana else "NO GANA",
    }


def bono_porta(e, jornada: str = "FULL") -> dict:
    meta, real, cump = v(e.get("bp_meta")), v(e.get("bp_real")), v(e.get("bp_cump"))
    monto_regla = cfg.BONO_PORTA["FULL" if jornada == "FULL" else "PT"]
    monto_excel = v(e.get("bp_bono"))
    monto = monto_excel if monto_excel > 0 else (monto_regla if cump >= 1 else 0)
    return {"meta": meta, "real": real, "cump": cump, "monto": monto, "gana": monto > 0}


def bono_winner(e, jornada: str = "FULL") -> dict:
    cump = v(e.get("bw_cump"))
    monto_regla = cfg.BONO_WINNER["FULL" if jornada == "FULL" else "PT"]
    monto_excel = v(e.get("bw_bono"))
    monto = monto_excel if monto_excel > 0 else (monto_regla if cump >= 1 else 0)
    return {
        "att_seg": v(e.get("bw_att_seg")),
        "att_ene_prot": v(e.get("bw_att_ene_prot")),
        "att_tv": v(e.get("bw_att_tv")),
        "cump": cump,
        "monto": monto,
        "gana": monto > 0,
    }


def jornada_de(codigo: str, jornadas: dict) -> str:
    j = (jornadas.get(codigo) or "FT").upper()
    return "PT" if j.startswith("P") else "FT"


# ---------------------------------------------------------------------------
# ficha: cumplimiento ponderado y tramo
# ---------------------------------------------------------------------------
def ficha(e, pesos_ficha: dict) -> dict:
    """Detalle del cumplimiento ponderado por KPI de la ficha."""
    detalle = []
    total = 0.0
    for clave, etiqueta in [("ficha_mis", "MIS"), ("ficha_l12", "1ra + 2da"), ("ficha_port", "Portado"),
                            ("ficha_fibra", "Fibra"), ("ficha_epa", "EPA"), ("ficha_eq", "$ Equipos"),
                            ("ficha_acc", "$ Accesorios")]:
        aporte = v(e.get(clave))
        peso = pesos_ficha.get(clave, 0.0)
        detalle.append({"kpi": etiqueta, "peso": peso, "aporte": aporte,
                        "cump": (aporte / peso) if peso else 0.0})
        total += aporte
    cump = v(e.get("cump_ficha"), total)
    tramo_excel = e.get("tramo")
    tramo = int(v(tramo_excel, -1)) if v(tramo_excel, -1) >= 0 else cfg.tramo_de(cump)
    proy = v(e.get("proy_pond"))
    return {
        "cump": cump, "tramo": tramo, "proy": proy,
        "tramo_proy": cfg.tramo_de(proy),
        "etiqueta": cfg.etiqueta_cumplimiento(cump),
        "etiqueta_proy": cfg.etiqueta_cumplimiento(proy),
        "detalle": detalle,
    }


# ---------------------------------------------------------------------------
# alertas y prioridades del corte
# ---------------------------------------------------------------------------
def alertas(e, estandares: dict, avance_esperado: float) -> list[dict]:
    """
    Genera la lista de alertas del ejecutivo. Cada alerta tiene:
    foco (MOVILIDAD/FIBRA/EQUIPOS/SEGUROS/ACCESORIOS), texto, severidad (1..3).
    """
    out = []

    def bajo_corte(foco, etiqueta, real, deben, sev=3, fmt=entero):
        real, deben = v(real), v(deben)
        if deben > 0 and real < deben:
            out.append({"foco": foco, "sev": sev,
                        "texto": f"{etiqueta} bajo corte · debería llevar {fmt(deben) if fmt is not entero else ceil_pos(deben)}"})

    def bajo_estandar(foco, etiqueta, valor, clave, sev=2):
        std = estandares.get(clave)
        if std is None:
            return
        if v(valor) < std:
            out.append({"foco": foco, "sev": sev, "texto": f"{etiqueta} bajo estándar · mínimo {pct(std, 0)}"})

    # MOVILIDAD
    bajo_corte("MOVILIDAD", "Total móvil", e.get("mov_real"), e.get("mov_deben"))
    bajo_corte("MOVILIDAD", "Suscripción", e.get("sus_real"), e.get("sus_deben"))
    bajo_corte("MOVILIDAD", "Portabilidad", e.get("porta_real"), e.get("porta_deben"))
    bajo_estandar("MOVILIDAD", "Conversión móvil", e.get("mov_conv"), "mov_conv")
    bajo_estandar("MOVILIDAD", "Conversión suscripción", e.get("sus_conv"), "sus_conv")
    bajo_estandar("MOVILIDAD", "Conversión portabilidad", e.get("porta_conv"), "porta_conv")
    bajo_estandar("MOVILIDAD", "Peso portabilidad", e.get("porta_peso"), "porta_peso", sev=1)
    # FIBRA
    bajo_corte("FIBRA", "Fibra", e.get("fib_real"), e.get("fib_deben"))
    bajo_estandar("FIBRA", "Conversión fibra", e.get("conv_fibra"), "conv_fibra")
    bajo_estandar("FIBRA", "% validación", e.get("pct_valid"), "pct_valid", sev=1)
    if v(e.get("fib_sol")) > 0 and v(e.get("tasa_inst")) < cfg.ESTANDAR_TASA_INSTALACION:
        out.append({"foco": "FIBRA", "sev": 1,
                    "texto": f"Tasa de instalación baja · mínimo {pct(cfg.ESTANDAR_TASA_INSTALACION, 0)}"})
    # EQUIPOS
    bajo_corte("EQUIPOS", "$ Equipos", e.get("eq_real"), e.get("eq_deben"), fmt=pesos)
    bajo_estandar("EQUIPOS", "Conversión equipos", e.get("eq_conv"), "eq_conv")
    bajo_estandar("EQUIPOS", "Attach equipo-línea", e.get("att_eq_linea"), "att_eq_linea", sev=1)
    # SEGUROS
    bajo_corte("SEGUROS", "Seguros", e.get("seg_real"), e.get("seg_deben"))
    bajo_estandar("SEGUROS", "Attach seguro", e.get("att_seg"), "att_seg")
    # ACCESORIOS
    bajo_corte("ACCESORIOS", "$ Accesorios", e.get("acc_real"), e.get("acc_deben"), fmt=pesos)
    bajo_estandar("ACCESORIOS", "Conversión accesorios", e.get("acc_conv"), "acc_conv")
    bajo_estandar("ACCESORIOS", "Attach energía", e.get("ene_att"), "ene_att", sev=1)
    bajo_estandar("ACCESORIOS", "Attach protección", e.get("prot_att"), "prot_att", sev=1)
    return out


PESO_FOCO = {"MOVILIDAD": 0.42, "FIBRA": 0.18, "EQUIPOS": 0.12, "SEGUROS": 0.10, "ACCESORIOS": 0.10}


def prioridades(lista_alertas: list[dict], n: int = 3) -> list[dict]:
    """Consolida las alertas por foco y devuelve las n prioridades ordenadas."""
    focos = {}
    for a in lista_alertas:
        f = focos.setdefault(a["foco"], {"foco": a["foco"], "alertas": [], "score": 0.0})
        f["alertas"].append(a)
        f["score"] += a["sev"] * PESO_FOCO.get(a["foco"], 0.1)
    orden = sorted(focos.values(), key=lambda f: (-f["score"], cfg.FOCOS.index(f["foco"]) if f["foco"] in cfg.FOCOS else 99))
    out = []
    for f in orden[:n]:
        principales = sorted(f["alertas"], key=lambda a: -a["sev"])[:2]
        extra = len(f["alertas"]) - len(principales)
        texto = " · ".join(a["texto"] for a in principales)
        if extra > 0:
            texto += f" · +{extra} señal(es) relacionada(s)"
        out.append({"foco": f["foco"], "texto": texto, "n": len(f["alertas"])})
    return out


# ---------------------------------------------------------------------------
# fibra
# ---------------------------------------------------------------------------
def resumen_fibra_ejecutivo(solicitudes: pd.DataFrame, codigo: str, fecha_corte: dt.date | None) -> dict:
    """Última solicitud y cantidad de solicitudes del periodo (mes del corte)."""
    if solicitudes is None or solicitudes.empty:
        return {"ultima": None, "hoy": False, "periodo": 0, "dias": None}
    s = solicitudes[solicitudes["ejecutivo"] == codigo]
    fechas = [f for f in s["fecha_solicitud"] if isinstance(f, dt.date) and pd.notna(f)]
    if fecha_corte:
        fechas_periodo = [f for f in fechas if f.year == fecha_corte.year and f.month == fecha_corte.month and f <= fecha_corte]
    else:
        fechas_periodo = fechas
    ultima = max(fechas_periodo) if fechas_periodo else (max(fechas) if fechas else None)
    dias = (fecha_corte - ultima).days if (ultima and fecha_corte) else None
    return {"ultima": ultima, "hoy": dias == 0, "periodo": len(fechas_periodo), "dias": dias}


def estado_solicitudes(solicitudes: pd.DataFrame, filtro: dict | None = None) -> pd.Series:
    s = solicitudes
    if filtro:
        for k, val in filtro.items():
            s = s[s[k] == val]
    return s["estatus"].fillna("(sin estatus)").value_counts()


# ---------------------------------------------------------------------------
# proyección simple
# ---------------------------------------------------------------------------
def proyeccion(real, avance_esperado: float):
    """Proyección lineal al cierre del mes (real / avance esperado)."""
    if not avance_esperado:
        return None
    return v(real) / avance_esperado
