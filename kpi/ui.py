"""
Componentes visuales (HTML + CSS) del panel. Todo se renderiza con
st.markdown(..., unsafe_allow_html=True) para reproducir el diseño oscuro
con tarjetas del panel original.
"""
from __future__ import annotations

import html

import streamlit as st

from .config import COLORES as C

CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Source+Sans+3:wght@400;600;700;800;900&display=swap');

html, body, [data-testid="stAppViewContainer"], .stApp {{
  background: radial-gradient(1200px 600px at 20% -10%, #0b2a52 0%, {C['fondo']} 55%) fixed;
  color: {C['texto']};
  font-family: 'Source Sans 3', 'Segoe UI', sans-serif;
}}
[data-testid="stHeader"] {{ background: transparent; }}
.block-container, [data-testid="stMainBlockContainer"], section.main > div {{ padding-top: 1rem !important; padding-bottom: 3rem; max-width: 1600px !important; padding-left:2rem !important; padding-right:2rem !important; }}

h1.titulo {{
  text-align:center; font-weight:900; letter-spacing:.06em; font-size:2.6rem;
  color:#fff; margin:.6rem 0 .4rem 0; text-shadow:0 0 18px rgba(34,211,238,.35);
}}
.logo-box {{ background:#fff; border-radius:10px; padding:.3rem .6rem; display:inline-block; }}

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

/* selects */
div[data-baseweb="select"] > div {{ background:#e5e7eb; color:#111; border-radius:10px; }}
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
  border:1.5px solid {C['borde']}; border-radius:16px; padding:1rem 1.1rem; margin-bottom:.8rem;
  box-shadow:0 0 0 1px rgba(30,58,138,.35), 0 8px 24px rgba(0,0,0,.35);
}}
.card.cyan {{ border-color:{C['cyan']}; }}
.card.verde {{ border-color:{C['verde']}; }}
.card.amarillo {{ border-color:{C['amarillo']}; }}
.card.rojo {{ border-color:{C['rojo']}; }}
.card.morado {{ border-color:{C['morado']}; }}
.card.naranjo {{ border-color:{C['naranjo']}; }}
.card.rosa {{ border-color:#f472b6; background:linear-gradient(180deg,#2a0f24 0%, #1a0a18 100%); }}
.card.light {{ background:linear-gradient(180deg,#f8fafc,#e2e8f0); color:#0f172a; border-color:#cbd5e1; }}

.card .h {{ font-size:.78rem; font-weight:800; letter-spacing:.08em; text-transform:uppercase; color:#cbd5e1; text-align:center; }}
.card .big {{ font-size:clamp(1.3rem, 2vw, 2.3rem); font-weight:900; text-align:center; line-height:1.1; margin:.35rem 0; color:#fff; white-space:nowrap; }}
.card .mid {{ font-size:clamp(1.1rem, 1.5vw, 1.6rem); font-weight:900; text-align:center; color:#fff; white-space:nowrap; }}
.card .sub {{ font-size:.85rem; color:#cbd5e1; text-align:center; font-weight:600; }}
.card .sec {{ font-size:1.55rem; font-weight:900; color:#fff; letter-spacing:.03em; }}
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
.cell {{ text-align:center; padding:.45rem .3rem; border-bottom:1px solid #1f3b6f; }}
.cell .l {{ font-size:.72rem; font-weight:800; letter-spacing:.06em; text-transform:uppercase; color:#cbd5e1; }}
.cell .v {{ font-size:1.35rem; font-weight:900; color:#fff; margin-top:.15rem; }}
.cell .v.big {{ font-size:1.9rem; }}
.cell .s {{ font-size:.78rem; color:#cbd5e1; margin-top:.15rem; }}
.mini {{ background:#0a1430; border:1px solid #1f3b6f; border-radius:12px; padding:.6rem .4rem; text-align:center; }}
.mini .l {{ font-size:.7rem; letter-spacing:.08em; font-weight:800; text-transform:uppercase; color:#cbd5e1; }}
.mini .v {{ font-size:1rem; font-weight:900; color:#fff; margin-top:.2rem; }}

/* pill */
.pill {{ display:inline-block; border:1.5px solid {C['cyan']}; border-radius:999px; padding:.25rem .8rem;
        font-weight:800; font-size:.85rem; color:#fff; background:#0a1a3a; }}

/* cuadrícula de productos (tarjetas claras, una al lado de otra) */
.prod-grid {{ display:grid; grid-template-columns:repeat(4, 1fr); gap:.7rem; margin:.6rem 0 .9rem; }}
.prod-grid.g7 {{ grid-template-columns:repeat(7, 1fr); }}
@media (max-width: 1200px) {{ .prod-grid, .prod-grid.g7 {{ grid-template-columns:repeat(4, 1fr); }} }}
@media (max-width: 800px) {{ .prod-grid, .prod-grid.g7 {{ grid-template-columns:repeat(2, 1fr); }} }}
@media (max-width: 500px) {{ .prod-grid, .prod-grid.g7 {{ grid-template-columns:1fr; }} }}

/* semáforos (tablas de cumplimiento y gestión) */
.celda-sem {{ display:block; padding:.25rem .3rem; border-radius:4px; font-weight:800; color:#111; }}
.sem-v {{ background:#22c55e; color:#052e16; }}
.sem-a {{ background:#facc15; color:#3f2d00; }}
.sem-r {{ background:#f87171; color:#450a0a; }}
.sem-t {{ background:#0ea5e9; color:#fff; }}
.tag {{ display:inline-block; border-radius:999px; padding:.05rem .5rem; font-size:.7rem; font-weight:800; margin-right:.15rem; }}
.g6 {{ grid-template-columns:repeat(6,1fr); }}
.g7 {{ grid-template-columns:repeat(7,1fr); }}
/* barra de producto (tarjeta clara) */
.prod {{ background:linear-gradient(180deg,#f8fafc,#eef2f7); color:#0f172a; border-radius:14px; padding:.9rem 1rem; margin-bottom:0; }}
.prod .n {{ display:inline-block; width:26px; height:26px; border-radius:7px; color:#fff; font-weight:800;
           text-align:center; line-height:26px; margin-right:.5rem; font-size:.85rem; }}
.prod .name {{ font-weight:800; font-size:.85rem; letter-spacing:.03em; text-transform:uppercase; }}
.prod .lleva {{ font-size:.8rem; font-weight:700; margin-top:.4rem; color:#334155; }}
.prod .val {{ font-size:1.7rem; font-weight:900; }}
.prod .de {{ font-size:1rem; font-weight:800; color:#334155; }}
.bar {{ width:100%; height:10px; background:#cbd5e1; border-radius:6px; overflow:hidden; margin:.45rem 0; }}
.bar > div {{ height:100%; border-radius:6px; }}
.prod .det {{ font-size:.78rem; color:#334155; line-height:1.55; }}
.prod .det b {{ color:#0f172a; }}

/* prioridades */
.prio {{ border:1.5px solid #f472b6; border-radius:12px; padding:.7rem .9rem; margin-bottom:.6rem; background:#22101f; }}
.prio .k {{ font-size:.72rem; font-weight:800; letter-spacing:.08em; color:#fda4af; }}
.prio .f {{ font-size:1.2rem; font-weight:900; color:#fff; }}
.prio .d {{ font-size:.85rem; color:#fecdd3; font-weight:600; }}

/* tabla */
.tabla {{ width:100%; border-collapse:collapse; font-size:.85rem; }}
.tabla th {{ text-align:center; font-size:.7rem; letter-spacing:.06em; text-transform:uppercase; color:#cbd5e1; padding:.45rem .3rem; border-bottom:1px solid #1f3b6f; }}
.tabla td {{ text-align:center; padding:.35rem .3rem; border-bottom:1px solid #16294f; color:#fff; font-weight:700; font-size:.8rem; }}
.tabla td.izq, .tabla th.izq {{ text-align:left; }}
.tabla tr.total td {{ background:#0e2a5c; }}

.foot {{ text-align:center; color:#94a3b8; font-size:.8rem; margin-top:1rem; }}
@media (max-width: 760px) {{
  .g4, .g5 {{ grid-template-columns:repeat(2,1fr); }}
  .card .big {{ font-size:1.7rem; }}
}}
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


def producto(n: int, nombre: str, real, meta, faltan, cump, conv=None, color="#2563eb", extra: str = "") -> str:
    from .metrics import entero, pct, v
    ancho = max(0.0, min(1.0, v(cump))) * 100
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
        f'<div class="bar"><div style="width:{ancho:.1f}%;background:{color}"></div></div>'
        f'<div class="det">{det}</div></div>'
    )


def tabla(columnas: list[str], filas: list[list[str]], total: list[str] | None = None, izq: int = 1,
          escapar_cabecera: bool = True) -> str:
    th = "".join(f'<th class="{"izq" if i < izq else ""}">{h(c) if escapar_cabecera else c}</th>' for i, c in enumerate(columnas))
    tr = ""
    for f in filas:
        tr += "<tr>" + "".join(f'<td class="{"izq" if i < izq else ""}">{c}</td>' for i, c in enumerate(f)) + "</tr>"
    if total:
        tr += '<tr class="total">' + "".join(f'<td class="{"izq" if i < izq else ""}">{c}</td>' for i, c in enumerate(total)) + "</tr>"
    return f'<div style="overflow-x:auto"><table class="tabla"><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table></div>'
