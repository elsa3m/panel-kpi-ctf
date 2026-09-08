"""
Componentes visuales (HTML + CSS) del panel. Todo se renderiza con
st.markdown(..., unsafe_allow_html=True) para reproducir el diseño oscuro
con tarjetas del panel original.
"""
from __future__ import annotations

import html

import streamlit as st

from .config import COLORES as C
from .config import SEMAFORO as S

CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Source+Sans+3:wght@400;600;700;800;900&display=swap');

html, body, [data-testid="stAppViewContainer"], .stApp {{
  background: radial-gradient(1200px 600px at 20% -10%, #0b2a52 0%, {C['fondo']} 55%) fixed;
  color: {C['texto']};
  font-family: 'Source Sans 3', 'Segoe UI', sans-serif;
}}
[data-testid="stHeader"] {{ background: transparent; }}
.block-container, [data-testid="stMainBlockContainer"], section.main > div {{ padding-top: .6rem !important; padding-bottom: 2.5rem; max-width: 1600px !important; padding-left:1.4rem !important; padding-right:1.4rem !important; }}

h1.titulo {{
  text-align:center; font-weight:900; letter-spacing:.06em; font-size:clamp(1.5rem, 4vw, 2.4rem);
  color:#fff; margin:.4rem 0 .3rem 0; text-shadow:0 0 18px rgba(34,211,238,.35);
}}
/* placa blanca del logo (el archivo trae fondo blanco y texto oscuro) */
.logo-box {{
  background:#fff; border-radius:14px; padding:.6rem .9rem; display:block;
  width:100%; max-width:310px; box-shadow:0 4px 16px rgba(0,0,0,.35);
  border:1px solid rgba(255,255,255,.6); margin-bottom:.5rem;
}}
.logo-box img {{ display:block; width:100%; height:auto; }}
@media (max-width: 640px) {{ .logo-box {{ max-width:220px; margin:0 auto; }} }}

/* radio de vistas como botones */
div[role="radiogroup"] {{ gap:.5rem; flex-wrap:wrap; }}
div[role="radiogroup"] > label {{
  background:{C['card']}; border:1px solid {C['borde']}; border-radius:12px;
  padding:.55rem 1rem; font-weight:800; text-transform:uppercase; letter-spacing:.03em;
  color:#fff !important;
}}
div[role="radiogroup"] > label[data-checked="true"],
div[role="radiogroup"] > label:has(input:checked) {{
  background:linear-gradient(135deg,#0e5aa7,#0891b2); border-color:{C['cyan']};
  box-shadow:0 0 14px rgba(34,211,238,.45);
}}
div[role="radiogroup"] p {{ color:#fff; font-weight:800; }}

/* selects: fondo blanco y borde cian, para que se vea que son desplegables */
div[data-baseweb="select"] > div {{
  background:#ffffff !important; color:#0f172a !important; border-radius:10px;
  border:2px solid {C['cyan']} !important; box-shadow:0 0 10px rgba(34,211,238,.25);
  font-weight:700; font-size:1rem;
}}
div[data-baseweb="select"] div, div[data-baseweb="select"] span,
div[data-baseweb="select"] svg {{ color:#0f172a !important; fill:#0f172a !important; }}
div[data-baseweb="popover"] li {{ background:#ffffff; color:#0f172a; font-weight:600; }}
div[data-baseweb="popover"] li:hover {{ background:#cffafe; color:#0f172a; }}
label[data-testid="stWidgetLabel"] p {{ color:#fff; font-weight:800; font-size:1.05rem; }}

/* expander y avisos */
details {{ background:{C['card']}; border:1px solid {C['borde']}; border-radius:12px; }}
summary p {{ color:#fff !important; font-weight:800; text-transform:uppercase; font-size:.9rem; }}
[data-testid="stAlert"] {{ background:{C['card']}; border:1px solid {C['borde']}; color:{C['texto']}; border-radius:12px; }}

/* botones */
.stButton > button, .stDownloadButton > button {{
  width:100%; background:linear-gradient(135deg,#06b6d4,#0ea5e9); color:#fff; font-weight:800;
  border:0; border-radius:12px; padding:.6rem 1rem; box-shadow:0 0 14px rgba(34,211,238,.35);
}}
.stButton > button:hover, .stDownloadButton > button:hover {{ filter:brightness(1.1); color:#fff; }}

/* ---------- tarjetas ---------- */
.card {{
  background:linear-gradient(180deg,#0d1b3a 0%, {C['card']} 100%);
  border:1.5px solid {C['borde']}; border-radius:14px; padding:.7rem .85rem; margin-bottom:.55rem;
  box-shadow:0 0 0 1px rgba(30,58,138,.35), 0 6px 18px rgba(0,0,0,.35);
}}
.card.cyan {{ border-color:{C['cyan']}; }}
.card.verde {{ border-color:{C['verde']}; }}
.card.amarillo {{ border-color:{C['amarillo']}; }}
.card.rojo {{ border-color:{C['rojo']}; }}
.card.morado {{ border-color:{C['morado']}; }}
.card.naranjo {{ border-color:{C['naranjo']}; }}
.card.rosa {{ border-color:#f472b6; background:linear-gradient(180deg,#2a0f24 0%, #1a0a18 100%); }}
.card.light {{ background:linear-gradient(180deg,#f8fafc,#e2e8f0); color:#0f172a; border-color:#cbd5e1; }}

.card .h {{ font-size:.92rem; font-weight:800; letter-spacing:.06em; text-transform:uppercase; color:#d3dbe6; text-align:center; }}
.card .big {{ font-size:clamp(1.45rem, 2vw, 2.1rem); font-weight:900; text-align:center; line-height:1.1; margin:.25rem 0; color:#fff; white-space:nowrap; }}
.card .mid {{ font-size:clamp(1.05rem, 1.4vw, 1.45rem); font-weight:900; text-align:center; color:#fff; white-space:nowrap; }}
.card .sub {{ font-size:.85rem; color:#d3dbe6; text-align:center; font-weight:600; line-height:1.4; }}
.card .sec {{ font-size:clamp(1.05rem, 1.6vw, 1.35rem); font-weight:900; color:#fff; letter-spacing:.03em; }}
.card .sec small {{ font-size:.75rem; color:{C['cyan']}; font-weight:800; }}
.t-cyan {{ color:{C['cyan']} !important; }}
.t-verde {{ color:{C['verde']} !important; }}
.t-amarillo {{ color:{C['amarillo']} !important; }}
.t-rojo {{ color:{C['rojo']} !important; }}
.t-morado {{ color:{C['morado']} !important; }}
.t-gris {{ color:{C['texto2']} !important; }}
.hr {{ border-top:1px solid #1f3b6f; margin:.7rem 0; }}

/* grillas internas */
.grid {{ display:grid; gap:.6rem; }}
.g2 {{ grid-template-columns:repeat(2,1fr); }}
.g3 {{ grid-template-columns:repeat(3,1fr); }}
.g4 {{ grid-template-columns:repeat(4,1fr); }}
.g5 {{ grid-template-columns:repeat(5,1fr); }}
.cell {{ text-align:center; padding:.35rem .25rem; border-bottom:1px solid #1f3b6f; }}
.cell .l {{ font-size:.85rem; font-weight:800; letter-spacing:.04em; text-transform:uppercase; color:#d3dbe6; line-height:1.25; }}
.cell .v {{ font-size:1.2rem; font-weight:900; color:#fff; margin-top:.1rem; }}
.cell .v.big {{ font-size:1.6rem; }}
.cell .s {{ font-size:.75rem; color:#d3dbe6; margin-top:.1rem; }}
.mini {{ background:#0a1430; border:1px solid #1f3b6f; border-radius:10px; padding:.45rem .35rem; text-align:center; }}
.mini .l {{ font-size:.85rem; letter-spacing:.04em; font-weight:800; text-transform:uppercase; color:#d3dbe6; }}
.mini .v {{ font-size:1.05rem; font-weight:900; color:#fff; margin-top:.15rem; }}

/* tarjetas de la cabecera: mismo alto y contenido centrado */
.card.igual {{ min-height:230px; display:flex; flex-direction:column; justify-content:center; }}
@media (max-width: 640px) {{ .card.igual {{ min-height:0; }} }}

/* pill */
.pill {{ display:inline-block; border:1.5px solid {C['cyan']}; border-radius:999px; padding:.25rem .8rem;
        font-weight:800; font-size:.85rem; color:#fff; background:#0a1a3a; }}

/* cuadrícula de productos (tarjetas claras, una al lado de otra) */
.prod-grid {{ display:grid; grid-template-columns:repeat(4, 1fr); gap:.7rem; margin:.6rem 0 .9rem; }}
.prod-grid.g7 {{ grid-template-columns:repeat(7, 1fr); }}
@media (max-width: 1200px) {{ .prod-grid, .prod-grid.g7 {{ grid-template-columns:repeat(4, 1fr); }} }}
@media (max-width: 800px) {{ .prod-grid, .prod-grid.g7 {{ grid-template-columns:repeat(2, 1fr); }} }}
@media (max-width: 500px) {{ .prod-grid, .prod-grid.g7 {{ grid-template-columns:repeat(2,1fr); gap:.45rem; }}
  .prod {{ padding:.5rem .55rem; }} .prod .val {{ font-size:1.25rem; }} }}

/* semáforos: color + símbolo, para que se entiendan sin depender del color */
.celda-sem {{ display:block; padding:.2rem .25rem; border-radius:4px; font-weight:800; font-size:.8rem; }}
.sem-v {{ background:{S['v'][0]}; color:{S['v'][1]}; }}
.sem-a {{ background:{S['a'][0]}; color:{S['a'][1]}; }}
.sem-r {{ background:{S['r'][0]}; color:{S['r'][1]}; }}
.sem-t {{ background:{S['t'][0]}; color:{S['t'][1]}; }}
.celda-sem::before {{ font-weight:900; margin-right:.2em; }}
.celda-sem.sem-v::before {{ content:"▲"; }}
.celda-sem.sem-a::before {{ content:"■"; }}
.celda-sem.sem-r::before {{ content:"▼"; }}
.celda-sem.rango::before {{ content:none; }}
.tag {{ display:inline-block; border-radius:999px; padding:.08rem .5rem; font-size:.75rem; font-weight:800; margin-right:.15rem; }}
.g6 {{ grid-template-columns:repeat(6,1fr); }}
.g7 {{ grid-template-columns:repeat(7,1fr); }}

/* chip de variación vs. corte anterior */
.delta {{ display:inline-block; border-radius:999px; padding:.05rem .45rem; font-size:.75rem; font-weight:800;
         border:1px solid transparent; }}
.delta.up {{ background:rgba(74,222,128,.16); border-color:{C['verde']}; color:{C['verde']}; }}
.delta.down {{ background:rgba(251,113,133,.16); border-color:{C['rojo']}; color:{C['rojo']}; }}
.delta.flat {{ background:rgba(168,179,196,.16); border-color:{C['texto2']}; color:{C['texto2']}; }}
.spark {{ display:block; margin:.2rem auto 0; }}

/* barra de producto (tarjeta clara) */
.prod {{ background:linear-gradient(180deg,#f8fafc,#eef2f7); color:#0f172a; border-radius:12px; padding:.6rem .7rem; margin-bottom:0; }}
.prod .n {{ display:inline-block; width:22px; height:22px; border-radius:6px; color:#fff; font-weight:800;
           text-align:center; line-height:22px; margin-right:.4rem; font-size:.78rem; }}
.prod .name {{ font-weight:800; font-size:.82rem; letter-spacing:.02em; text-transform:uppercase; }}
.prod .lleva {{ font-size:.75rem; font-weight:700; margin-top:.3rem; color:#3f4d63; }}
.prod .val {{ font-size:1.45rem; font-weight:900; }}
.prod .de {{ font-size:.95rem; font-weight:800; color:#3f4d63; }}
.bar {{ position:relative; width:100%; height:11px; background:#94a3b8; border-radius:6px; overflow:hidden; margin:.35rem 0; }}
.bar > div {{ height:100%; border-radius:6px; }}
.bar > .marca {{ position:absolute; top:-3px; width:3px; height:17px; background:#0f172a; border-radius:1px; }}
.prod .det {{ font-size:.76rem; color:#3f4d63; line-height:1.5; }}
.prod .det b {{ color:#0f172a; }}

/* prioridades */
.prio {{ border:1.5px solid #f472b6; border-radius:11px; padding:.55rem .7rem; margin-bottom:.45rem; background:#22101f; }}
.prio .k {{ font-size:.75rem; font-weight:800; letter-spacing:.06em; color:#fecdd3; }}
.prio .f {{ font-size:1.05rem; font-weight:900; color:#fff; }}
.prio .d {{ font-size:.82rem; color:#fbd5db; font-weight:600; line-height:1.45; }}

/* tabla: cabecera fija y primera columna fija al hacer scroll lateral */
.tabla-wrap {{ overflow-x:auto; max-height:70vh; overflow-y:auto; -webkit-overflow-scrolling:touch; }}
.tabla {{ width:100%; border-collapse:separate; border-spacing:0; font-size:.82rem; }}
.tabla th {{ position:sticky; top:0; z-index:3; background:#0c1a38; text-align:center; font-size:.82rem;
            letter-spacing:.04em; text-transform:uppercase; color:#d3dbe6; padding:.4rem .3rem; border-bottom:1px solid #1f3b6f; }}
.tabla td {{ text-align:center; padding:.3rem .3rem; border-bottom:1px solid #16294f; color:#fff; font-weight:700; font-size:.8rem; }}
.tabla td.izq, .tabla th.izq {{ text-align:left; }}
.tabla th.fija, .tabla td.fija {{ position:sticky; left:0; z-index:2; background:#0c1a38; }}
.tabla th.fija {{ z-index:4; }}
.tabla tr.total td {{ background:#0e2a5c; }}
.tabla tbody tr:hover td {{ background:#12244a; }}

.foot {{ text-align:center; color:{C['texto2']}; font-size:.78rem; margin-top:.8rem; }}

/* ---------- responsive: tablet ---------- */
@media (max-width: 1100px) {{
  .g5, .g6, .g7 {{ grid-template-columns:repeat(3,1fr); }}
  [data-testid="stHorizontalBlock"] {{ flex-wrap:wrap !important; }}
  [data-testid="stHorizontalBlock"] > [data-testid="column"],
  [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {{
     flex:1 1 46% !important; min-width:46% !important; }}
}}
/* ---------- responsive: celular ---------- */
@media (max-width: 640px) {{
  .block-container, [data-testid="stMainBlockContainer"] {{ padding-left:.6rem !important; padding-right:.6rem !important; }}
  /* dos tarjetas por fila en celular: se ve más de un dato sin desplazarse */
  [data-testid="stHorizontalBlock"] {{ gap:.4rem !important; }}
  [data-testid="stHorizontalBlock"] > [data-testid="column"],
  [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {{
     flex:1 1 44% !important; min-width:44% !important; width:44% !important; }}
  .g3, .g4, .g5, .g6, .g7 {{ grid-template-columns:repeat(2,1fr); }}
  .grid {{ gap:.4rem; }}
  /* una tarjeta marcada con .ancho-total ocupa la fila completa en celular */
  [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:has(.ancho-total),
  [data-testid="stHorizontalBlock"] > [data-testid="column"]:has(.ancho-total) {{
     flex:1 1 100% !important; min-width:100% !important; width:100% !important; }}
  .card {{ padding:.6rem .65rem; margin-bottom:.45rem; }}
  .card .big {{ font-size:1.6rem; white-space:normal; overflow-wrap:anywhere; }}
  .mini .v {{ font-size:.85rem; overflow-wrap:anywhere; }}
  .mini .l {{ letter-spacing:0; }}
  .card .mid {{ font-size:1.1rem; white-space:normal; }}
  .card .sec {{ font-size:1.05rem; }}
  .cell .v {{ font-size:1.1rem; }}
  .cell .v.big {{ font-size:1.4rem; }}
  div[role="radiogroup"] {{ gap:.3rem; }}
  div[role="radiogroup"] > label {{ padding:.4rem .6rem; font-size:.8rem; }}
  .tabla-wrap {{ max-height:60vh; }}
  .tabla th, .tabla td {{ font-size:.75rem; padding:.28rem .25rem; }}
  h1.titulo {{ font-size:1.45rem; }}
}}
/* piso legible: nada por debajo de 12 px (0,75 rem) */
.card [style*="font-size:.75rem"], .card [style*="font-size:.75rem"],
.card [style*="font-size:.75rem"] {{ font-size:.75rem !important; }}
.ref {{ font-size:.75rem; color:{C['texto2']}; text-align:center; line-height:1.4; }}
</style>
"""


def inject_css():
    st.markdown(CSS, unsafe_allow_html=True)


def h(txt) -> str:
    return html.escape(str(txt))


def md(s: str):
    st.markdown(s, unsafe_allow_html=True)


def card(body: str, color: str = "", extra_class: str = ""):
    md(f'<div class="card {color} {extra_class}">{body}</div>')


def kpi(titulo: str, valor: str, sub: str = "", color_valor: str = "", borde: str = "", icono: str = ""):
    cuerpo = f'<div class="h">{icono} {h(titulo)}</div><div class="big {color_valor}">{valor}</div>'
    if sub:
        cuerpo += f'<div class="sub">{sub}</div>'
    card(cuerpo, borde)


def celda(label: str, valor: str, sub: str = "", grande: bool = False, color: str = "") -> str:
    s = f'<div class="s">{sub}</div>' if sub else ""
    return f'<div class="cell"><div class="l">{h(label)}</div><div class="v {"big" if grande else ""} {color}">{valor}</div>{s}</div>'


def mini(label: str, valor: str) -> str:
    return f'<div class="mini"><div class="l">{h(label)}</div><div class="v">{valor}</div></div>'


def grid(celdas: list[str], cols: int = 4) -> str:
    return f'<div class="grid g{cols}">{"".join(celdas)}</div>'


def seccion(icono: str, titulo: str, sub: str = "", color: str = "") -> None:
    md(f'<div class="card {color}" style="padding:.7rem 1.1rem"><div class="sec">{icono} {h(titulo)} <small>{h(sub)}</small></div></div>')


def color_cump(x: float) -> str:
    if x is None:
        return "t-gris"
    if x >= 1.0:
        return "t-verde"
    if x >= 0.8:
        return "t-amarillo"
    return "t-rojo"


def producto(n: int, nombre: str, real, meta, faltan, cump, conv=None, color="#2563eb", extra: str = "",
             corte: float | None = None) -> str:
    """
    Tarjeta de producto. `corte` (0..1) dibuja una marca negra en la barra con el
    avance esperado: de un vistazo se ve si va adelantado o atrasado.
    """
    from .metrics import entero, pct, v
    ancho = max(0.0, min(1.0, v(cump))) * 100
    marca = ""
    if corte is not None and 0 < corte <= 1:
        marca = (f'<div class="marca" style="left:{min(99.5, corte * 100):.1f}%" '
                 f'title="Avance esperado {pct(corte, 1)}"></div>')
    estado = ""
    if corte is not None and corte > 0:
        ok = v(cump) >= corte
        estado = (f'<span class="delta {"up" if ok else "down"}">{"▲ sobre el corte" if ok else "▼ bajo el corte"}</span>')
    det = f"<b>Faltan:</b> {entero(faltan)}<br><b>Cumplimiento:</b> {pct(cump)}"
    if conv is not None:
        det += f"<br><b>Conv.:</b> {pct(conv, 1)}"
    if extra:
        det += f"<br>{extra}"
    return (
        f'<div class="prod"><span class="n" style="background:{color}">{n}</span>'
        f'<span class="name">{h(nombre)}</span>'
        f'<div class="lleva">Lleva:</div>'
        f'<div><span class="val" style="color:{color}">{entero(real)}</span> <span class="de">de {entero(meta)}</span></div>'
        f'<div class="bar"><div style="width:{ancho:.1f}%;background:{color}"></div>{marca}</div>'
        f'<div class="det">{estado}<br>{det}</div></div>'
    )


def delta(dif: float | None, sufijo: str = " pts", dec: int = 1, invertir: bool = False) -> str:
    """Chip '+3,2 pts' / '−1,4 pts' de variación contra el corte anterior."""
    if dif is None:
        return ""
    signo = "+" if dif > 0 else ("−" if dif < 0 else "=")
    bueno = (dif < 0) if invertir else (dif > 0)
    clase = "flat" if abs(dif) < 1e-9 else ("up" if bueno else "down")
    flecha = "▲" if dif > 0 else ("▼" if dif < 0 else "=")
    txt = f"{abs(dif):.{dec}f}".replace(".", ",")
    return f'<span class="delta {clase}">{flecha} {signo if signo != "=" else ""}{txt}{sufijo}</span>'


def sparkline(valores, color: str | None = None, ancho: int = 88, alto: int = 22) -> str:
    """Mini-gráfico SVG de la tendencia de los últimos cortes."""
    vals = [float(x) for x in valores if x is not None and x == x]
    if len(vals) < 2:
        return ""
    color = color or C["cyan"]
    lo, hi = min(vals), max(vals)
    rango = (hi - lo) or 1.0
    paso = ancho / (len(vals) - 1)
    puntos = " ".join(f"{i * paso:.1f},{alto - 2 - (x - lo) / rango * (alto - 4):.1f}" for i, x in enumerate(vals))
    ult = puntos.split()[-1]
    return (f'<svg class="spark" width="{ancho}" height="{alto}" viewBox="0 0 {ancho} {alto}" '
            f'role="img" aria-label="Tendencia de los últimos {len(vals)} cortes">'
            f'<polyline points="{puntos}" fill="none" stroke="{color}" stroke-width="1.8" '
            f'stroke-linejoin="round" stroke-linecap="round"/>'
            f'<circle cx="{ult.split(",")[0]}" cy="{ult.split(",")[1]}" r="2.4" fill="{color}"/></svg>')


def tabla(columnas: list[str], filas: list[list[str]], total: list[str] | None = None, izq: int = 1,
          escapar_cabecera: bool = True, fijar_primera: bool = True) -> str:
    def clases(i):
        c = []
        if i < izq:
            c.append("izq")
        if fijar_primera and i == 0:
            c.append("fija")
        return " ".join(c)

    th = "".join(f'<th class="{clases(i)}">{h(c) if escapar_cabecera else c}</th>' for i, c in enumerate(columnas))
    tr = ""
    for f in filas:
        tr += "<tr>" + "".join(f'<td class="{clases(i)}">{c}</td>' for i, c in enumerate(f)) + "</tr>"
    if total:
        tr += '<tr class="total">' + "".join(f'<td class="{clases(i)}">{c}</td>' for i, c in enumerate(total)) + "</tr>"
    return f'<div class="tabla-wrap"><table class="tabla"><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table></div>'
