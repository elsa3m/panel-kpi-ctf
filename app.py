"""
PANEL KPI CTF · réplica en Streamlit
=====================================
Punto de entrada de la aplicación.  Ejecutar con:  streamlit run app.py
"""
from __future__ import annotations

import calendar
import datetime as dt

import pandas as pd
import streamlit as st

from kpi import config as cfg
from kpi import loader, metrics as M, ui
from kpi.metrics import entero, fecha_txt, pct, pesos, v
from kpi.ui import celda, grid, h, md, mini

st.set_page_config(page_title="KPI Ejecutivo | Tiendas CTF", page_icon="📊", layout="wide")
ui.inject_css()


# ---------------------------------------------------------------------------
# carga con caché (se invalida cuando cambia el archivo en data/)
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner="Leyendo MOV-FIBRA…")
def _cargar_mov(path: str, mtime: float):
    return loader.cargar_mov_fibra(path)


@st.cache_data(show_spinner="Leyendo FIBRA DRIVE…")
def _cargar_fibra(path: str, mtime: float):
    return loader.cargar_fibra(path)


@st.cache_data(show_spinner="Leyendo ESCUCHAS…")
def _cargar_escuchas(path: str, mtime: float):
    return loader.cargar_escuchas(path)


def cargar(nombre: str):
    p = loader.ruta_fuente(nombre)
    if not p.exists():
        return None
    fn = {"MOV-FIBRA": _cargar_mov, "FIBRA DRIVE": _cargar_fibra, "ESCUCHAS ENTEL": _cargar_escuchas}[nombre]
    try:
        return fn(str(p), p.stat().st_mtime)
    except Exception as ex:  # noqa: BLE001
        st.error(f"No se pudo leer {nombre}: {ex}")
        return None


# ---------------------------------------------------------------------------
# cabecera
# ---------------------------------------------------------------------------
logo = cfg.ASSETS_DIR / "logo.png"
c1, c2, c3 = st.columns([1, 2.4, 1])
with c1:
    if logo.exists():
        st.image(str(logo), width=260)
with c2:
    md('<h1 class="titulo">PANEL KPI CTF</h1>')

VISTAS = ["👤 Vista Ejecutivo", "🏬 Vista Tiendas / CTF", "👔 Jefe de Tienda", "📡 Fibra Tiendas", "👷 Fibra Ejecutivos"]
vista = st.radio("Vista", VISTAS, horizontal=True, label_visibility="collapsed")

st.info("Los Excel activos quedan guardados en el servidor. Mantén también una **copia de respaldo externa**.")

# ---------------------------------------------------------------------------
# gestión de archivos
# ---------------------------------------------------------------------------
with st.expander("📁 GESTIÓN DE ARCHIVOS", expanded=False):
    st.caption("Puedes cargar un archivo nuevo para reemplazar el anterior, o eliminarlo manualmente con el botón correspondiente.")
    for nombre, meta in cfg.FUENTES.items():
        st.subheader(f"{meta['icono']} {meta['titulo']}")
        subido = st.file_uploader(f"Cargar / reemplazar Excel {meta['titulo']}", type=["xlsx", "xlsm"],
                                  key=f"up_{nombre}", help=meta["ayuda"])
        destino = loader.ruta_fuente(nombre)
        if subido is not None:
            destino.write_bytes(subido.getbuffer())
            (destino.with_suffix(".nombre.txt")).write_text(subido.name, encoding="utf-8")
            st.cache_data.clear()
            st.success(f"{subido.name} guardado como {meta['titulo']}.")
        if destino.exists():
            nombre_original = destino.with_suffix(".nombre.txt")
            nombre_original = nombre_original.read_text(encoding="utf-8") if nombre_original.exists() else destino.name
            fecha_mod = dt.datetime.fromtimestamp(destino.stat().st_mtime).strftime("%d/%m/%Y %H:%M")
            st.markdown(f"✅ **Archivo guardado**  \n**{nombre_original}** · {destino.stat().st_size / 1e6:.1f} MB  \n**Actualizado:** {fecha_mod}")
            if st.checkbox(f"Confirmo que deseo eliminar {meta['titulo']}", key=f"chk_{nombre}"):
                if st.button(f"🗑️ Eliminar {meta['titulo']} guardado", key=f"del_{nombre}"):
                    destino.unlink(missing_ok=True)
                    destino.with_suffix(".nombre.txt").unlink(missing_ok=True)
                    st.cache_data.clear()
                    st.rerun()
        else:
            st.warning(f"Sin archivo {meta['titulo']} cargado.")

mov = cargar("MOV-FIBRA")
fib = cargar("FIBRA DRIVE")
esc = cargar("ESCUCHAS ENTEL")

if mov is None:
    st.warning("Carga el Excel **MOV-FIBRA** en *Gestión de archivos* para comenzar.")
    st.stop()

for aviso in mov.avisos:
    st.warning(aviso)

_f1, _slot_pdf = st.columns([2.7, 1])
with _f1:
    md(f'<div class="card cyan" style="padding:.7rem 1rem;margin-bottom:.4rem">📅 <b>DATOS ACTUALIZADOS AL: {fecha_txt(mov.fecha_corte)}</b> '
       f'<span class="t-gris">· Fuente: MOV-FIBRA · L{loader.C.HEADER_ROW}</span></div>')

tiendas = mov.tiendas
ejecutivos = mov.ejecutivos[mov.ejecutivos["activo"]].copy()
nombre_tienda = dict(zip(tiendas["pdv"], tiendas["tienda"]))
etiqueta_tienda = {p: f"{n} · PDV {p}" for p, n in nombre_tienda.items()}
NOMBRE_ARCHIVO = (loader.ruta_fuente("MOV-FIBRA").with_suffix(".nombre.txt"))
NOMBRE_ARCHIVO = NOMBRE_ARCHIVO.read_text(encoding="utf-8") if NOMBRE_ARCHIVO.exists() else mov.archivo


def avance_calendario(row) -> float:
    """Avance esperado como en el panel original: días trabajados / días del mes del corte."""
    dias_mes = calendar.monthrange(mov.fecha_corte.year, mov.fecha_corte.month)[1] if mov.fecha_corte else 30
    return v(row.get("dias_trab")) / dias_mes if dias_mes else 0.0


def avance_dias(row) -> float:
    """Avance del periodo según el propio Excel: días trabajados / (trabajados + restantes).

    Es el criterio que usan las hojas de fibra y coincide con la celda B3 de MOV-FIBRA.
    """
    t, r = v(row.get("dias_trab")), v(row.get("dias_rest"))
    return t / (t + r) if (t + r) else mov.avance_esperado


def deben(row, clave_meta: str, avance: float) -> float:
    return v(row.get(clave_meta)) * avance


# ===========================================================================
# BLOQUES REUTILIZABLES (los usan Vista Ejecutivo y Vista Tiendas)
# ===========================================================================
def bloque_cabecera(row, pdv_txt: str, sub_pdv: str, titulo_peq: str, nombre_grande: str, minis: list[str] | None,
                    lema: str, f: dict, ultima_fibra: dict | None):
    c1, c2, c3, c4 = st.columns([1.1, 3.2, 1, 1])
    with c1:
        ui.card(f'<div class="mid">🏬 {h(pdv_txt)}</div><div class="sub t-cyan" style="font-weight:800;font-size:1rem">{h(sub_pdv)}</div>'
                f'<div class="hr"></div><div class="h t-cyan">📅 CORTE</div><div class="mid">{fecha_txt(mov.fecha_corte)}</div>', "cyan")
    with c2:
        cuerpo = f'<div class="h">{h(titulo_peq)}</div><div class="big t-cyan" style="font-size:2.4rem">{h(nombre_grande)}</div>'
        if minis:
            cuerpo += grid(minis, 4)
        if lema:
            cuerpo += f'<div class="sub" style="font-size:1.4rem;font-style:italic;color:#e5e7eb">{h(lema)}</div>'
        ui.card(cuerpo, "")
        if ultima_fibra is not None:
            if ultima_fibra["ultima"]:
                cuando = "Hoy" if ultima_fibra["hoy"] else (f"Hace {ultima_fibra['dias']} días" if ultima_fibra["dias"] is not None else "")
                ui.card(f'<div class="h t-cyan">ÚLTIMA SOLICITUD DE FIBRA</div><div class="mid t-verde">📅 {fecha_txt(ultima_fibra["ultima"])}</div>'
                        f'<div class="sub">{cuando} · {ultima_fibra["periodo"]} solicitudes en el periodo</div>', "cyan")
            else:
                ui.card('<div class="h t-cyan">ÚLTIMA SOLICITUD DE FIBRA</div><div class="mid t-rojo">Sin solicitudes</div>'
                        '<div class="sub">0 solicitudes en el periodo</div>', "cyan")
    col_real = "t-rojo" if f["cump"] < 0.8 else ("t-amarillo" if f["cump"] < 1 else "t-verde")
    col_proy = "t-rojo" if f["proy"] < 0.8 else ("t-amarillo" if f["proy"] < 1 else "t-verde")
    with c3:
        ui.card(f'<div class="h" style="margin-top:1.2rem">% REAL A LA FECHA</div><div class="big {col_real}" style="margin:1.2rem 0">{pct(f["cump"])}</div>'
                f'<div class="mid {col_real}" style="font-size:1.3rem">TRAMO {f["tramo"]}</div><div class="sub {col_real}" style="margin:1rem 0 .6rem"><b>{f["etiqueta"]}</b></div>',
                "rojo" if col_real == "t-rojo" else ("amarillo" if col_real == "t-amarillo" else "verde"))
    with c4:
        ui.card(f'<div class="h" style="margin-top:1.2rem">% PROYECCIÓN</div><div class="big {col_proy}" style="margin:1.2rem 0">{pct(f["proy"])}</div>'
                f'<div class="mid {col_proy}" style="font-size:1.3rem">TRAMO {f["tramo_proy"]}</div><div class="sub {col_proy}" style="margin:1rem 0 .6rem"><b>{f["etiqueta_proy"] if f["tramo_proy"] == 0 else "TRAMO " + str(f["tramo_proy"])}</b></div>',
                "rojo" if col_proy == "t-rojo" else ("amarillo" if col_proy == "t-amarillo" else "verde"))


def bloque_indicadores(row, f: dict, prom_pares: float | None):
    k1, k2, k3, k4, k5 = st.columns(5)
    with k1:
        sub = ""
        if prom_pares is not None:
            dif = v(row["atenciones"]) - prom_pares
            sub = f"Prom. pares FULL: {entero(prom_pares)} · <b class='{'t-verde' if dif >= 0 else 't-rojo'}'>{'+' if dif >= 0 else ''}{entero(dif)}</b>"
        ui.kpi("Atenciones", entero(row["atenciones"]), sub, "", "", "👤")
    with k2:
        ui.kpi("Días restantes", entero(row["dias_rest"]), "", "", "", "📅")
    with k3:
        ui.kpi("Meta EPA", pct(row["epa_meta"], 0), "", "", "", "🎯")
    with k4:
        ui.kpi("EPA actual", pct(row["epa"], 1), "", ui.color_cump(v(row["epa"]) / v(row["epa_meta"], 1) if v(row["epa_meta"]) else None), "")
    with k5:
        col = "t-rojo" if f["cump"] < 0.8 else ("t-amarillo" if f["cump"] < 1 else "t-verde")
        ui.kpi("Tramo real", str(f["tramo"]), f'<b class="{col}">{f["etiqueta"]}</b>', col, "", "🏅")


def bloque_movilidad(row, avance: float):
    md(f'<div class="card" style="padding:.6rem 1.1rem;display:flex;justify-content:space-between;align-items:center">'
       f'<span class="sec">📱 ENTEL – MOVILIDAD</span><span class="pill">📍 AVANCE ESPERADO: {pct(avance, 1)}</span></div>')
    items = [
        (1, "Total móvil", "mov", "#2563eb", "mov_conv", None),
        (2, "Suscripción", "sus", "#0d9488", "sus_conv", None),
        (3, "Migraciones", "mis", "#a855f7", None, None),
        (4, "1ra línea", "l1", "#ea580c", None, None),
        (5, "2da línea", "l2", "#2563eb", None, None),
        (6, "Portabilidad", "porta", "#16a34a", "porta_conv", "porta_peso"),
        (7, "Fibra", "fib", "#0891b2", "conv_fibra", None),
    ]
    html_items = ""
    for n, nombre, k, color, conv, extra in items:
        extra_txt = f"<b>Peso porta:</b> {pct(row.get(extra), 1)}" if extra else ""
        html_items += ui.producto(n, nombre, row.get(f"{k}_real"), row.get(f"{k}_meta"), row.get(f"{k}_falta"),
                                  row.get(f"{k}_cump"), row.get(conv) if conv else None, color, extra_txt)
    md(f'<div class="prod-grid g7">{html_items}</div>')


def bloque_bonos(row, jornada: str):
    bf, bp, bw = M.bono_foco(row, jornada), M.bono_porta(row, jornada), M.bono_winner(row, jornada)
    tipo = "FULL" if jornada == "FT" else "PT"
    est_bf = '<span class="t-verde">✅ GANA</span>' if bf["gana"] else '<span class="t-rojo">❌ NO GANA</span>'
    est_bw = '<span class="t-verde">✅ GANA</span>' if bw["gana"] else '<span class="t-rojo">❌ NO GANA</span>'
    cuerpo = '<div class="sec t-morado" style="font-size:1.3rem">💰 BONOS DEL EJECUTIVO</div><div class="grid g3" style="margin-top:.5rem">'
    cuerpo += ('<div class="card morado" style="margin:0"><div class="sec" style="font-size:1.1rem">📲 BONO PORTABILIDAD</div>'
               + grid([celda("Meta bono", entero(bp["meta"])), celda("Lleva", entero(bp["real"])),
                       celda("Cumplimiento", pct(bp["cump"], 1)), celda("Bono ganado", pesos(bp["monto"]), color="t-verde")], 4)
               + f'<div class="sub" style="margin-top:.4rem;font-size:.75rem"><b>Tipo:</b> <span class="t-verde">{tipo}</span> · <b>Regla:</b> FULL {pesos(cfg.BONO_PORTA["FULL"])} / PT {pesos(cfg.BONO_PORTA["PT"])} al cumplir meta.</div></div>')
    cuerpo += ('<div class="card morado" style="margin:0"><div class="sec" style="font-size:1.1rem">🎯 BONO FOCO</div>'
               + grid([celda("% Suscripción", pct(bf["cump_sus"], 1)), celda("% Fibra", pct(bf["cump_fib"], 1)),
                       celda("% Bono foco", pct(bf["pct"])), celda("Estado", est_bf)], 4) + '</div>')
    cuerpo += ('<div class="card morado" style="margin:0"><div class="sec" style="font-size:1.1rem">🏆 BONO WINNER</div>'
               + grid([celda("Att seguro", pct(bw["att_seg"], 1)), celda("Att ene./prot.", pct(bw["att_ene_prot"], 1)),
                       celda("Att TV full", pct(bw["att_tv"], 1)), celda("Cumplimiento", pct(bw["cump"], 1))], 4)
               + f'<div class="sub" style="margin-top:.4rem;font-size:.75rem">{est_bw} · <b>Bono:</b> {pesos(bw["monto"])} · <b>Tipo:</b> <span class="t-verde">{tipo}</span></div></div>')
    cuerpo += "</div>"
    ui.card(cuerpo, "morado")
    return {"foco": bf, "porta": bp, "winner": bw}


def bloque_fibra(row):
    fp = v(row.get("factor_prod"))
    cuerpo = '<div class="sec">📶 FIBRA (REAL ENTEL)</div>' + grid([
        celda("Q Validaciones", entero(row.get("q_valid")), f"% Validación {pct(row.get('pct_valid'))}<br>Incorrectas {pct(row.get('valid_inc'))}", True),
        celda("Factibles", entero(row.get("factibles")), f"% Factibles {pct(row.get('pct_fact'))}", True),
        celda("Conv. fibra", pct(row.get("conv_fibra")), "", True),
        celda("Factor de prod.", pct(fp) if fp <= 1 else f"{fp:.2f}", "", True),
        celda("Tasa de instalación", pct(row.get("tasa_inst")), "", True),
        celda("Fibra solicitudes", entero(row.get("fib_sol")), f"Pendientes: {entero(row.get('fib_pend'))}", True),
    ], 6)
    ui.card(cuerpo, "cyan")


def bloque_equipos_seguros_acc(row, avance: float):
    a, b, c = st.columns(3)
    with a:
        ui.card('<div class="sec" style="text-align:center">📱 EQUIPOS</div>' + grid([
            celda("Cumplimiento", pct(row.get("eq_cump"))), celda("Conv. equipos", pct(row.get("eq_conv"), 1)),
            celda("Vendidos / meta", f"{entero(row.get('eq_q'))} / {entero(row.get('eq_meta_q'))}"),
            celda("Q faltan", entero(v(row.get("eq_meta_q")) - v(row.get("eq_q")))),
            celda("Att. eq–línea", pct(row.get("att_eq_linea"), 1)),
        ], 5) + grid([
            celda("Meta ($)", pesos(row.get("eq_meta"))), celda("Real ($)", pesos(row.get("eq_real"))),
            celda("Falta ($)", pesos(row.get("eq_falta"))), celda("Deben llevar al corte ($)", pesos(deben(row, "eq_meta", avance))),
        ], 2), "")
    with b:
        ui.card('<div class="sec" style="text-align:center">🛡️ SEGUROS</div>' + grid([
            celda("Meta (Q)", entero(row.get("seg_meta"))), celda("Real (Q)", entero(row.get("seg_real"))),
            celda("Falta (Q)", entero(row.get("seg_falta"))), celda("Deben llevar", str(M.ceil_pos(deben(row, "seg_meta", avance)))),
        ], 4) + grid([celda("Cumplimiento", pct(row.get("seg_cump"))), celda("Attach", pct(row.get("att_seg"), 1))], 2), "morado")
    with c:
        ui.card('<div class="sec" style="text-align:center">👜 ACCESORIOS</div>' + grid([
            celda("Meta ($)", pesos(row.get("acc_meta"))), celda("Real ($)", pesos(row.get("acc_real"))),
            celda("Falta ($)", pesos(row.get("acc_falta"))), celda("Deben llevar ($)", pesos(deben(row, "acc_meta", avance))),
        ], 2) + grid([
            celda("Cumplimiento", pct(row.get("acc_cump"))), celda("Conv. acc", pct(row.get("acc_conv"), 1)),
            celda("Q vendidos", f"{entero(row.get('acc_q'))}/{entero(row.get('acc_meta_q'))}"),
        ], 3), "naranjo")


def bloque_ene_prot_epa(row):
    a, b, c = st.columns(3)
    with a:
        ui.card('<div class="sec" style="text-align:center">⚡ ENERGÍA</div>' + grid([
            celda("$ Energía", pesos(row.get("ene_usd"))), celda("Q Energía", entero(row.get("ene_q"))),
            celda("Conv.", pct(row.get("ene_conv"))), celda("Attach", pct(row.get("ene_att"))),
        ], 4), "amarillo")
    with b:
        ui.card('<div class="sec" style="text-align:center">🛡️ PROTECCIÓN</div>' + grid([
            celda("$ Protección", pesos(row.get("prot_usd"))), celda("Q Protec.", entero(row.get("prot_q"))),
            celda("Conv.", pct(row.get("prot_conv"))), celda("Attach", pct(row.get("prot_att"))),
        ], 4), "rojo")
    with c:
        ui.card('<div class="sec" style="text-align:center">☑️ EPA <small>(EVALUACIÓN PLAN DE ACCIÓN)</small></div>' + grid([
            celda("Meta EPA", pct(row.get("epa_meta"), 0), grande=True),
            celda("EPA actual", pct(row.get("epa"), 1), grande=True, color=ui.color_cump(v(row.get("epa")) / v(row.get("epa_meta"), 1) if v(row.get("epa_meta")) else None)),
        ], 2), "cyan")


def bloque_escuchas(clave: str, tienda: str, titulo: str = "ESCUCHAS"):
    ui.seccion("🎧", titulo)
    if esc is None or esc.empty:
        st.info("Carga el Excel **ESCUCHAS ENTEL** en *Gestión de archivos* para ver Escuchas auditadas, Starlink, Latam Pass, Hogar, Fibra y Portabilidad.")
        return
    fila = esc[esc["ejecutivo"].str.upper() == clave.upper()]
    if fila.empty:
        st.info("No hay escuchas registradas para esta selección.")
        return
    r = fila.iloc[0]

    def ref(nombre):
        f_ = esc[esc["ejecutivo"].str.upper() == str(nombre).upper()]
        return f_.iloc[0] if not f_.empty else None

    t, canal, ctf = ref(tienda), ref("CANAL"), ref("CTF")

    def refs(col, fmt=lambda x: pct(x, 1)):
        partes = []
        if t is not None and t is not r:
            partes.append(f"Tienda <span class='t-cyan'>{fmt(t[col])}</span>")
        if canal is not None:
            partes.append(f"Canal <span class='t-cyan'>{fmt(canal[col])}</span>")
        if ctf is not None:
            partes.append(f"CTF <span class='t-cyan'>{fmt(ctf[col])}</span>")
        return "<br>".join(partes)

    cols = st.columns(6)
    with cols[0]:
        ui.card(f'<div class="h">🎧 ESCUCHAS AUDITADAS</div><div class="big t-verde">{entero(r["auditadas"])}</div><div class="sub">{refs("auditadas", entero)}</div>', "cyan")
    with cols[1]:
        ui.card(f'<div class="h">🛰️ STARLINK</div><div class="big t-verde">{pct(r["starlink"], 1)}</div><div class="sub">{refs("starlink")}</div>', "cyan")
    with cols[2]:
        ui.card(f'<div class="h">✈️ LATAM PASS</div><div class="big t-verde">{pct(r["latam_pass"], 1)}</div><div class="sub">{refs("latam_pass")}</div>', "cyan")
    with cols[3]:
        ui.card(f'<div class="h">🏠 HOGAR</div><div class="big t-verde">{pct(r["hogar"], 1)}</div><div class="sub">{refs("hogar")}</div>', "cyan")
    with cols[4]:
        ui.card('<div class="h">📡 FIBRA</div>' + grid([celda("Calidad", pct(r["fibra_calidad"], 1), color="t-amarillo"), celda("Estabilidad", pct(r["fibra_estabilidad"], 1), color="t-amarillo")], 2)
                + f'<div class="sub" style="margin-top:.3rem;font-size:.72rem">{refs("fibra_calidad")}</div>', "cyan")
    with cols[5]:
        ui.card('<div class="h">📲 PORTABILIDAD</div>' + grid([celda("Motivo", pct(r["porta_motivo"], 1), color="t-amarillo"), celda("Objeciones", pct(r["porta_objeciones"], 1), color="t-amarillo"), celda("Urgencia", pct(r["porta_urgencia"], 1), color="t-amarillo")], 3)
                + f'<div class="sub" style="margin-top:.3rem;font-size:.72rem">{refs("porta_motivo")}</div>', "cyan")


def bloque_epa_encuestas(codigo: str):
    ui.seccion("🗣️", "EPA Y ENCUESTAS DEL EJECUTIVO")
    epa_row = mov.epa_ejecutivo[mov.epa_ejecutivo["ejecutivo"] == codigo]
    enc = mov.encuestas[mov.encuestas["ejecutivo"] == codigo] if not mov.encuestas.empty else pd.DataFrame()
    epa_val = epa_row.iloc[0]["epa"] if not epa_row.empty else None
    q_total = int(v(epa_row.iloc[0]["q_total"])) if not epa_row.empty else 0
    n_enc = len(enc) if not enc.empty else q_total
    positivas = int((enc["nota"] >= 1).sum()) if not enc.empty else 0
    por_rec = int((enc["nota"] <= 0).sum()) if not enc.empty else 0
    a, b, c, d = st.columns(4)
    with a:
        ui.kpi("EPA actual", pct(epa_val, 1, "—") if q_total else "—", "Fuente: hoja EPA", "t-verde" if q_total else "", "", "🎯")
    with b:
        ui.kpi("Encuestas", str(n_enc), "Respuestas registradas", "", "", "📝")
    with c:
        ui.kpi("Positivas", str(positivas), "Nota igual a 1", "t-verde", "", "✅")
    with d:
        ui.kpi("Por recuperar", str(por_rec), "Notas 0 y -1", "", "", "⚠️")
    if enc.empty:
        st.info("Este ejecutivo no tiene encuestas detalladas registradas en BASE EPA.")
    else:
        cols = [c_ for c_ in ("fecha", "nota", "tipo_atencion", "literal") if c_ in enc.columns]
        st.dataframe(enc[cols].sort_values("fecha", ascending=False), use_container_width=True, hide_index=True)


def bloque_prioridades(row, titulo="3 PRIORIDADES DEL CORTE"):
    lista = M.alertas(row, mov.estandares, mov.avance_esperado)
    prios = M.prioridades(lista, 3)
    focos = len({a["foco"] for a in lista})
    cuerpo = f'<div class="sec">🎯 {titulo}</div><div class="sub" style="text-align:left;color:#fda4af"><b>{len(lista)} alertas consolidadas en {focos} focos. Trabaja primero estas tres prioridades.</b></div>'
    cuerpo += '<div class="grid g3" style="margin-top:.5rem">'
    for i, p in enumerate(prios, 1):
        cuerpo += f'<div class="prio" style="margin:0"><div class="k">PRIORIDAD {i}</div><div class="f">{h(p["foco"])}</div><div class="d">{h(p["texto"])}</div></div>'
    cuerpo += "</div>"
    if not prios:
        cuerpo += '<div class="sub t-verde">Sin alertas: todos los KPI están sobre el corte y el estándar.</div>'
    ui.card(cuerpo, "rosa")
    return prios


# ===========================================================================
# TABLAS DE LA VISTA TIENDAS / CTF
# ===========================================================================
def semaforo(valor, clave: str) -> str:
    u = mov.umbrales.get(clave)
    if u is None:
        return ""
    x = v(valor)
    if x >= u["meta"]:
        return "sem-v"
    if x >= u["amarillo"]:
        return "sem-a"
    return "sem-r"


def tabla_bono_winner(ej: pd.DataFrame):
    ui.seccion("🏆", "CUMPLIMIENTOS DE EJECUTIVOS · BONO WINNER")
    md('<div class="card" style="padding:.5rem 1rem;font-size:.85rem"><b>Metas Winner:</b> Attach Seguro 32% · Energía/Protección 34% · TV Full 45% · Pago según el resultado oficial del Drive.</div>')
    filas = []
    for _, r in ej.sort_values(["tienda", "ejecutivo"]).iterrows():
        j = M.jornada_de(r["ejecutivo"], mov.jornadas)
        bw = M.bono_winner(r, j)
        filas.append([h(r["ejecutivo"]), h(r["tienda"]), "FULL" if j == "FT" else "PT",
                      pct(bw["att_seg"], 1), pct(bw["att_ene_prot"], 1), pct(bw["att_tv"], 1), pct(bw["cump"], 1),
                      f'<span class="{"t-verde" if bw["gana"] else "t-rojo"}">{"GANA" if bw["gana"] else "NO GANA"}</span>',
                      f'<span class="{"t-verde" if bw["gana"] else "t-rojo"}">{pesos(bw["monto"])}</span>'])
    ui.card(ui.tabla(["Ejecutivo", "Tienda", "Tipo", "Att seguro", "Att ene./prot.", "Att TV full", "Cumplimiento", "Estado", "Bono"], filas, izq=2), "cyan")


KPIS_CUMP = [("Total móvil", "mov_cump"), ("Suscripción", "sus_cump"), ("1ra línea", "l1_cump"), ("2da línea", "l2_cump"),
             ("Porta", "porta_cump"), ("Fibra", "fib_cump"), ("Equipos", "eq_cump"), ("Seguros", "seg_cump"), ("Accesorios", "acc_cump")]


def tabla_cumplimientos(ej: pd.DataFrame, avance: float):
    u = mov.umbrales.get("mov_cump", {"meta": mov.avance_esperado, "amarillo": 0.075})
    md(f'<div class="card" style="padding:.6rem 1.1rem;display:flex;justify-content:space-between;align-items:center">'
       f'<span class="sec">👥 CUMPLIMIENTOS DE EJECUTIVOS</span><span class="pill">📍 AVANCE ESPERADO: {pct(avance, 1)}</span></div>')
    md(f'<div class="card" style="padding:.45rem 1rem;font-size:.8rem"><span class="tag sem-v">VERDE ≥ {pct(u["meta"], 1)}</span> '
       f'<span class="tag sem-a">AMARILLO {pct(u["amarillo"], 1)} a {pct(u["meta"], 1)}</span> <span class="tag sem-r">ROJO &lt; {pct(u["amarillo"], 1)}</span>'
       f' · Cada resumen suma exactamente los {len(KPIS_CUMP)} KPI visibles.</div>')
    filas = []
    for _, r in ej.sort_values("ejecutivo").iterrows():
        celdas = []
        cnt = {"sem-v": 0, "sem-a": 0, "sem-r": 0}
        for _, k in KPIS_CUMP:
            cls = semaforo(r.get(k), k)
            cnt[cls] = cnt.get(cls, 0) + 1
            celdas.append(f'<span class="celda-sem {cls}">{pct(r.get(k), 1)}</span>')
        resumen = (f'<span class="tag sem-v">V{cnt["sem-v"]}</span> <span class="tag sem-a">A{cnt["sem-a"]}</span> '
                   f'<span class="tag sem-r">R{cnt["sem-r"]}</span> <span class="tag sem-t">T{len(KPIS_CUMP)}</span>')
        filas.append([h(r["ejecutivo"]), h(mov.nombres.get(r["ejecutivo"], "")), entero(r["atenciones"])] + celdas + [resumen])
    ui.card(ui.tabla(["Ejecutivo", "Nombre", "Atenc."] + [n for n, _ in KPIS_CUMP] + ["Resumen"], filas, izq=2), "cyan")


KPIS_GESTION = [("Conv. móvil", "mov_conv"), ("Conv. sus", "sus_conv"), ("Conv. porta", "porta_conv"), ("Peso porta", "porta_peso"),
                ("CVM 50%", "cvm_50"), ("Conv. fibra", "conv_fibra"), ("Tasa inst.", "tasa_inst"), ("% Validac.", "pct_valid"),
                ("% Fact.", "pct_fact"), ("Conv. equipos", "eq_conv"), ("Att eq-línea", "att_eq_linea"), ("Att seguro", "att_seg"),
                ("Conv. acc", "acc_conv"), ("Att energía", "ene_att"), ("Att protec.", "prot_att"), ("EPA", "epa")]


def tabla_gestion(ej: pd.DataFrame):
    ui.seccion("🎯", "GESTIÓN DE EJECUTIVOS")
    md('<div class="card" style="padding:.45rem 1rem;font-size:.8rem"><span class="tag sem-v">VERDE = META / ESTÁNDAR</span> '
       '<span class="tag sem-a">AMARILLO = RANGO INTERMEDIO</span> <span class="tag sem-r">ROJO = BAJO MÍNIMO</span> · Umbrales tomados directamente de la hoja CONV-CUMP del Excel.</div>')
    cabecera = ["Ejecutivo", "Nombre", "Atenc."]
    for n, k in KPIS_GESTION:
        u = mov.umbrales.get(k)
        cabecera.append(f'{n}<br><span class="t-cyan">META {pct(u["meta"], 1) if u else "—"}</span>')
    filas = []
    for _, r in ej.sort_values("ejecutivo").iterrows():
        celdas = [f'<span class="celda-sem {semaforo(r.get(k), k)}">{pct(r.get(k), 1)}</span>' for _, k in KPIS_GESTION]
        filas.append([h(r["ejecutivo"]), h(mov.nombres.get(r["ejecutivo"], "")), entero(r["atenciones"])] + celdas)
    ui.card(ui.tabla(cabecera, filas, izq=2, escapar_cabecera=False), "cyan")


def tabla_ranking(ej: pd.DataFrame):
    ui.seccion("🏆", "RANKING CTF DE EJECUTIVOS")
    rk = ej.sort_values(["atenciones", "proy_pond"], ascending=[False, False])
    filas = []
    for i, (_, r) in enumerate(rk.iterrows(), 1):
        f = M.ficha(r, mov.pesos)
        col = "t-rojo" if f["proy"] < 0.8 else ("t-amarillo" if f["proy"] < 1 else "t-verde")
        filas.append([str(i), h(r["ejecutivo"]), h(mov.nombres.get(r["ejecutivo"], "")), h(r["tienda"]), entero(r["atenciones"]),
                      f'<span class="{col}">{pct(f["proy"])}</span>', f'<span class="{col}">TRAMO {f["tramo_proy"]}</span>',
                      f'<span class="{col}">{f["etiqueta_proy"]}</span>'])
    ui.card(ui.tabla(["#", "Ejecutivo", "Nombre", "Tienda", "Atenc.", "% Proyección", "Tramo", "Estado"], filas, izq=4), "cyan")


# ===========================================================================
# VISTA 1 · EJECUTIVO
# ===========================================================================
def vista_ejecutivo():
    s1, s2 = st.columns(2)
    with s1:
        pdv = st.selectbox("🏬 Tienda", list(etiqueta_tienda.keys()), format_func=lambda p: etiqueta_tienda[p])
    ej_tienda = ejecutivos[ejecutivos["pdv"] == pdv]
    if ej_tienda.empty:
        st.warning("Esta tienda no tiene ejecutivos activos en MOV-FIBRA.")
        return
    with s2:
        codigo = st.selectbox("👤 Ejecutivo", list(ej_tienda["ejecutivo"]))
    e = ej_tienda[ej_tienda["ejecutivo"] == codigo].iloc[0]
    tienda = nombre_tienda.get(pdv, "")
    nombre = mov.nombres.get(codigo, "")
    jornada = M.jornada_de(codigo, mov.jornadas)
    f = M.ficha(e, mov.pesos)
    avance = avance_calendario(e)

    bonos = {"foco": M.bono_foco(e, jornada), "porta": M.bono_porta(e, jornada), "winner": M.bono_winner(e, jornada)}
    prios = M.prioridades(M.alertas(e, mov.estandares, mov.avance_esperado), 3)
    with _slot_pdf:
        try:
            from kpi.pdf import ficha_pdf
            pdf_bytes = ficha_pdf(e.to_dict(), nombre, tienda, mov.fecha_corte, f, bonos, prios)
            st.download_button("📥 Descargar ficha PDF", pdf_bytes, use_container_width=True,
                               file_name=f"ficha_{codigo}_{fecha_txt(mov.fecha_corte).replace('/', '-')}.pdf", mime="application/pdf")
        except Exception as ex:  # noqa: BLE001
            st.caption(f"PDF no disponible: {ex}")

    md(f'<div class="card" style="padding:.6rem 1rem">Tienda: <b>{h(tienda)}</b> · Ejecutivos en esta tienda: <b>{len(ej_tienda)}</b></div>')

    minis = [mini("👤 Nombre", h(nombre or "Por completar")), mini("⏳ Antigüedad", "Por completar"),
             mini("🕒 Jornada", jornada), mini("🎂 Cumpleaños", "Por completar")]
    rf = M.resumen_fibra_ejecutivo(fib.solicitudes if fib else None, codigo, mov.fecha_corte)
    bloque_cabecera(e, f"PDV {pdv}", tienda, "EJECUTIVO SELECCIONADO", codigo, minis, "", f, rf)

    prom = ej_tienda.loc[ej_tienda["ejecutivo"] != codigo, "atenciones"]
    bloque_indicadores(e, f, prom.mean() if not prom.empty else 0)
    bloque_movilidad(e, avance)
    bloque_bonos(e, jornada)
    bloque_fibra(e)
    bloque_equipos_seguros_acc(e, avance)
    bloque_ene_prot_epa(e)
    bloque_escuchas(codigo, tienda)
    bloque_epa_encuestas(codigo)
    bloque_prioridades(e)
    md(f'<div class="foot">Archivo cargado: {h(NOMBRE_ARCHIVO)} · Vista: Ejecutivo · {h(tienda)} · Ejecutivos: {len(ej_tienda)}</div>')


# ===========================================================================
# VISTA 2 · TIENDAS / CTF
# ===========================================================================
def vista_tiendas():
    opciones = ["CTF"] + list(etiqueta_tienda.keys())
    etiquetas = {"CTF": "CTF EMPRESA TOTAL · CTF TECNOLOGIA SPA", **etiqueta_tienda}
    sel = st.selectbox("🏬 Seleccionar tienda / empresa", opciones, format_func=lambda p: etiquetas[p])

    if sel == "CTF":
        row = pd.Series(mov.total)
        ej = ejecutivos
        titulo, pdv_txt, sub_pdv, nombre_grande = "EMPRESA TOTAL", "PDV CTF", "CTF EMPRESA TOTAL", "CTF EMPRESA TOTAL"
        escucha_clave = "CTF"
    else:
        row = tiendas[tiendas["pdv"] == sel].iloc[0]
        ej = ejecutivos[ejecutivos["pdv"] == sel]
        titulo, pdv_txt, sub_pdv, nombre_grande = "TIENDA", f"PDV {sel}", nombre_tienda[sel], nombre_tienda[sel]
        escucha_clave = nombre_tienda[sel]

    # cumplimiento ponderado de la tienda / empresa = promedio de sus ejecutivos
    f = {
        "cump": ej["cump_ficha"].mean() if not ej.empty else 0.0,
        "proy": ej["proy_pond"].mean() if not ej.empty else 0.0,
    }
    f["tramo"], f["tramo_proy"] = cfg.tramo_de(f["cump"]), cfg.tramo_de(f["proy"])
    f["etiqueta"], f["etiqueta_proy"] = cfg.etiqueta_cumplimiento(f["cump"]), cfg.etiqueta_cumplimiento(f["proy"])
    avance = avance_calendario(row)

    md(f'<div class="card" style="padding:.6rem 1rem">Vista: <b>{h(nombre_grande)}</b> · Ejecutivos: <b>{len(ej)}</b> · Corte: <b>{fecha_txt(mov.fecha_corte)}</b></div>')
    bloque_cabecera(row, pdv_txt, sub_pdv, titulo, nombre_grande, None, "¡Vamos por más! Cada venta cuenta.", f, None)
    bloque_indicadores(row, f, None)
    bloque_movilidad(row, avance)
    bloque_fibra(row)
    bloque_equipos_seguros_acc(row, avance)
    bloque_ene_prot_epa(row)
    tabla_bono_winner(ej)
    tabla_cumplimientos(ej, avance)
    tabla_gestion(ej)
    tabla_ranking(ej)
    bloque_escuchas(escucha_clave, escucha_clave, f"ESCUCHAS · {nombre_grande}")
    md(f'<div class="foot">Archivo cargado: {h(NOMBRE_ARCHIVO)} · Vista: Tiendas / CTF · {h(nombre_grande)}</div>')


# ===========================================================================
# VISTA 3 · JEFE DE TIENDA
# ===========================================================================
def vista_jefe():
    pdv = st.selectbox("🏬 Tienda", list(etiqueta_tienda.keys()), format_func=lambda p: etiqueta_tienda[p])
    t = tiendas[tiendas["pdv"] == pdv].iloc[0]
    ej = ejecutivos[ejecutivos["pdv"] == pdv]
    tienda = t["tienda"]
    avance = avance_calendario(t)

    md(f'<div class="card" style="padding:.6rem 1rem">Tienda: <b>{h(tienda)}</b> · PDV {h(pdv)} · Ejecutivos activos: <b>{len(ej)}</b> · Corte: <b>{fecha_txt(mov.fecha_corte)}</b></div>')
    ui.seccion("👥", "EJECUTIVOS DE LA TIENDA", "semáforo del corte")
    filas = []
    for _, r in ej.sort_values("cump_ficha", ascending=False).iterrows():
        f = M.ficha(r, mov.pesos)
        al = M.alertas(r, mov.estandares, mov.avance_esperado)
        filas.append([h(r["ejecutivo"]), h(mov.nombres.get(r["ejecutivo"], "")), entero(r["atenciones"]),
                      f'<span class="{ui.color_cump(f["cump"])}">{pct(f["cump"])}</span>', str(f["tramo"]),
                      f'<span class="{ui.color_cump(f["proy"])}">{pct(f["proy"])}</span>',
                      f"{entero(r['mov_real'])}/{M.ceil_pos(deben(r, 'mov_meta', avance))}", f"{entero(r['porta_real'])}/{M.ceil_pos(deben(r, 'porta_meta', avance))}",
                      f"{entero(r['fib_real'])}/{M.ceil_pos(deben(r, 'fib_meta', avance))}", f"{entero(r['seg_real'])}/{M.ceil_pos(deben(r, 'seg_meta', avance))}",
                      pct(r["eq_cump"]), pct(r["epa"], 0), f'<span class="{"t-rojo" if len(al) >= 8 else "t-amarillo" if len(al) >= 4 else "t-verde"}">{len(al)}</span>'])
    ui.card(ui.tabla(["Ejecutivo", "Nombre", "Atenc.", "% Real", "Tramo", "% Proy.", "Móvil / corte", "Porta / corte", "Fibra / corte", "Seg. / corte", "Cump. eq.", "EPA", "Alertas"], filas, izq=2), "cyan")

    ui.seccion("🎯", "PRIORIDADES POR EJECUTIVO")
    cols = st.columns(3)
    for i, (_, r) in enumerate(ej.iterrows()):
        with cols[i % 3]:
            prios = M.prioridades(M.alertas(r, mov.estandares, mov.avance_esperado), 3)
            cuerpo = f'<div class="sec" style="font-size:1.1rem">{h(r["ejecutivo"])}</div>'
            for j, p in enumerate(prios, 1):
                cuerpo += f'<div class="prio"><div class="k">PRIORIDAD {j} · {h(p["foco"])}</div><div class="d">{h(p["texto"])}</div></div>'
            if not prios:
                cuerpo += '<div class="sub t-verde">Sin alertas.</div>'
            ui.card(cuerpo, "rosa")

    bloque_movilidad(t, avance)
    bloque_fibra(t)
    bloque_equipos_seguros_acc(t, avance)
    bloque_ene_prot_epa(t)
    md(f'<div class="foot">Archivo cargado: {h(NOMBRE_ARCHIVO)} · Vista: Jefe de tienda · {h(tienda)}</div>')


# ===========================================================================
# VISTAS 4 y 5 · FIBRA
# ===========================================================================
def _sin_fibra():
    st.warning("Carga el Excel **FIBRA DRIVE** en *Gestión de archivos* para ver esta vista.")


ESTATUS_ORDEN = ["AGENDADA", "EN INSTALACIÓN", "INSTALADA", "REPROGRAMADA", "RECONTRATADA", "CANCELADO"]


def _sol_periodo(sol: pd.DataFrame) -> pd.DataFrame:
    """Solicitudes del mes del corte (según la fecha de solicitud)."""
    if sol is None or sol.empty:
        return sol if sol is not None else pd.DataFrame()
    mes = (fib.fecha_actualizacion or mov.fecha_corte)
    return sol[sol["mes"] == mes.month] if mes else sol


def bloque_ordenes(s: pd.DataFrame):
    """5 tarjetas: total órdenes, instaladas, canceladas, en progreso, recontratadas."""
    total = len(s)
    def cuenta(*estatus):
        return int(s["estatus"].isin(estatus).sum()) if total else 0
    inst, canc, recon = cuenta("INSTALADA"), cuenta("CANCELADO"), cuenta("RECONTRATADA")
    prog = cuenta("AGENDADA", "EN INSTALACIÓN", "REPROGRAMADA")
    def p(x):
        return pct(x / total, 1) if total else "0,0%"
    c = st.columns(5)
    datos = [("📋 Total órdenes", total, "100%", "t-cyan", "cyan"),
             ("✅ Instaladas", inst, p(inst), "t-verde", "verde"),
             ("❌ Canceladas", canc, p(canc), "t-rojo", "rojo"),
             ("⏳ En progreso", prog, p(prog), "t-morado", "morado"),
             ("🔁 Recontratadas", recon, p(recon), "t-cyan", "cyan")]
    for col, (t, val, sub, cl, borde) in zip(c, datos):
        with col:
            ui.kpi(t, str(val), sub, cl, borde)


def bloque_reagendamientos(s: pd.DataFrame):
    reag = int((s["reagendamientos"] > 0).sum()) if not s.empty else 0
    total_reag = int(s["reagendamientos"].sum()) if not s.empty else 0
    prom = s["intentos"].mean() if not s.empty else 0
    mx = int(s["intentos"].max()) if not s.empty else 0
    c = st.columns(4)
    for col, (t, val, sub) in zip(c, [("📄 Órdenes reagendadas", str(reag), "Con más de 1 intento"),
                                      ("🔁 Reagendamientos", str(total_reag), "Intentos adicionales"),
                                      ("📊 Prom. intentos", f"{prom:.2f}".replace(".", ","), "Por orden"),
                                      ("⚠️ Máx. intentos", str(mx), "Máximo observado")]):
        with col:
            ui.kpi(t, val, sub, "t-cyan", "")


def bloque_cancelaciones(s: pd.DataFrame, con_tienda: bool = True):
    ui.seccion("❌", "ANÁLISIS DE CANCELACIONES")
    canc = s[s["estatus"] == "CANCELADO"] if not s.empty else pd.DataFrame()
    if canc.empty:
        st.info("Sin cancelaciones registradas en el periodo.")
        return
    a, b = st.columns(2)
    with a:
        st.caption("Principales motivos de cancelación")
        st.bar_chart(canc["motivo"].fillna("Sin motivo").replace("", "Sin motivo").value_counts().head(8), color="#0ea5e9")
    with b:
        st.caption("Tipo de rechazo")
        st.bar_chart(canc["tipo_rechazo"].fillna("Sin tipificación").replace("", "Sin tipificación").value_counts().head(8), color="#0ea5e9")
    cols = ["id", "ejecutivo"] + (["pdv"] if con_tienda else []) + ["tipo_rechazo", "motivo"]
    vis = canc[cols].copy()
    if con_tienda:
        vis["pdv"] = vis["pdv"].map(lambda p: nombre_tienda.get(p, p))
    vis.columns = ["ID", "Nombre ejecutivo"] + (["Tienda"] if con_tienda else []) + ["Tipo de rechazo", "Motivo"]
    st.dataframe(vis.fillna("").astype(str).replace({"None": "", "NaT": "", "nan": ""}), use_container_width=True, hide_index=True)


def vista_fibra_tiendas():
    if fib is None:
        return _sin_fibra()
    md('<div class="card cyan" style="padding:.6rem 1rem;text-align:center"><span class="sec t-cyan">📡 FIBRA TIENDAS</span></div>')
    res, sol = fib.resumen, _sol_periodo(fib.solicitudes)

    opciones = ["CTF"] + list(etiqueta_tienda.keys())
    etiquetas = {"CTF": "CTF EMPRESA TOTAL", **{p: nombre_tienda[p] for p in etiqueta_tienda}}
    sel = st.selectbox("🏬 Tienda / empresa", opciones, format_func=lambda p: etiquetas[p])
    s = sol if sel == "CTF" else sol[sol["pdv"] == sel]
    ej_res = res[res["es_ejecutivo"]] if sel == "CTF" else res[(res["es_ejecutivo"]) & (res["pdv"] == sel)]
    ej_mov = ejecutivos if sel == "CTF" else ejecutivos[ejecutivos["pdv"] == sel]

    md(f'<div class="card" style="padding:.6rem 1rem">Vista seleccionada: <b>{h(etiquetas[sel])}</b> · Órdenes: <b>{len(s)}</b></div>')
    bloque_ordenes(s)

    # --- fila de metas de fibra --------------------------------------------
    meta = ej_res["meta_fibra"].fillna(0).sum()
    real = ej_res["real_fibra"].fillna(0).sum()
    cump = real / meta if meta else 0.0
    fila_ref = pd.Series(mov.total) if sel == "CTF" else tiendas[tiendas["pdv"] == sel].iloc[0]
    avance = avance_dias(fila_ref)
    proy = cump / avance if avance else 0.0
    deben_ = ej_mov["fib_deben"].fillna(0).sum()
    inst = int((s["estatus"] == "INSTALADA").sum()) if not s.empty else 0
    tasa = inst / len(s) if len(s) else 0.0
    c = st.columns(7)
    datos = [("🎯 Meta fibra", entero(meta), "Meta instalación", "t-cyan"),
             ("✅ Real fibra", entero(real), "Instaladas válidas", "t-verde"),
             ("📉 Faltan", entero(meta - real), "Para alcanzar meta", "t-rojo"),
             ("📊 Cumplimiento", pct(cump, 1), "Real / meta", ui.color_cump(cump / max(avance, 1e-9))),
             ("🚀 Proyección", pct(proy, 1), "Proyección de cierre", ui.color_cump(proy)),
             ("🕐 Deben llevar", str(M.ceil_pos(deben_)), "Instaladas al corte", "t-cyan"),
             ("🔧 Tasa instalación", pct(tasa, 1), "Instaladas / órdenes", ui.color_cump(tasa))]
    for col, (t, val, sub, cl) in zip(c, datos):
        with col:
            ui.kpi(t, val, sub, cl, "")

    # --- tabla cumplimiento fibra por ejecutivo -----------------------------
    ui.seccion("👥", "CUMPLIMIENTO FIBRA POR EJECUTIVO")
    filas = []
    for _, r in ej_res.iterrows():
        cod = r["nombre"]
        m_, rn, ra = v(r.get("meta_fibra")), v(r.get("real_no_af")), v(r.get("real_af"))
        tot = rn + ra
        cu = tot / m_ if m_ else 0.0
        pr = cu / avance if avance else 0.0
        mv = ej_mov[ej_mov["ejecutivo"] == cod]
        de = M.ceil_pos(v(mv.iloc[0]["fib_deben"]) if not mv.empty else m_ * avance)
        ti = v(mv.iloc[0]["tasa_inst"]) if not mv.empty else 0.0
        va = v(mv.iloc[0]["pct_valid"]) if not mv.empty else 0.0
        sem_c = "sem-v" if cu >= avance else ("sem-a" if cu >= avance * 0.7 else "sem-r")
        sem_p = "sem-v" if pr >= 1 else ("sem-a" if pr >= 0.8 else "sem-r")
        filas.append([h(cod), h(nombre_tienda.get(r["pdv"], r["pdv"])), entero(m_), entero(rn), entero(ra), entero(tot),
                      f'<span class="celda-sem {sem_c}">{pct(cu, 0)}</span>', f'<span class="celda-sem {sem_p}">{pct(pr, 0)}</span>',
                      str(de), entero(r.get("FIBRA PEND. SEPT")), entero(r.get("PEND. OCT")),
                      f'<span class="celda-sem {"sem-v" if ti >= 0.75 else ("sem-a" if ti >= 0.4 else "sem-r")}">{pct(ti, 1)}</span>',
                      f'<span class="celda-sem {"sem-v" if va >= 0.85 else ("sem-a" if va >= 0.7 else "sem-r")}">{pct(va, 1)}</span>'])
    ui.card(ui.tabla(["Ejecutivo", "Tienda", "Meta", "Real", "Afinidad", "Total", "Cump.", "Proy.", "Deben",
                      "Pend. sept.", "Pend. oct.", "Tasa inst.", "Valid."], filas, izq=2), "cyan")

    # --- evolutivo diario ----------------------------------------------------
    ui.seccion("📅", "EVOLUTIVO DIARIO DE SOLICITUDES")
    ref = fib.fecha_actualizacion or mov.fecha_corte
    if not s.empty and ref:
        dias = [dt.date(ref.year, ref.month, d) for d in range(1, ref.day + 1)]
        filas = []
        for cod in sorted(s["ejecutivo"].unique()):
            ss = s[s["ejecutivo"] == cod]
            fechas = [f_ for f_ in ss["fecha_solicitud"] if isinstance(f_, dt.date) and pd.notna(f_)]
            ultima = max(fechas) if fechas else None
            sin = max(0, (ref - ultima).days) if ultima else None
            por_dia = [int((ss["fecha_solicitud"] == d).sum()) for d in dias]
            celdas = [f'<span class="celda-sem {"sem-v" if n >= 3 else ("sem-a" if n >= 1 else "")}">{n or ""}</span>' for n in por_dia]
            filas.append([h(ss.iloc[0]["pdv"]), h(cod), fecha_txt(ultima), str(sin) if sin is not None else "—", str(sum(por_dia))] + celdas)
        ui.card(ui.tabla(["PDV", "Ejecutivo", "Última solicitud", "Días sin solicitud", "Total"] + [d.strftime("%d/%m") for d in dias], filas, izq=2), "cyan")

    bloque_reagendamientos(s)

    # --- agenda y estado de instalaciones ------------------------------------
    ui.seccion("📆", "AGENDA Y ESTADO DE INSTALACIONES")
    st.caption(f"Tienda seleccionada: {etiquetas[sel]}. Filtra el periodo para revisar qué se instalará y el estado actual de cada solicitud.")
    f1, f2 = st.columns([1, 2])
    with f1:
        campo = st.selectbox("📅 Filtrar según", ["Fecha de instalación", "Fecha de solicitud"], key="fibra_campo")
    col_f = "fecha_instalacion" if campo.startswith("Fecha de inst") else "fecha_solicitud"
    fechas_validas = [f_ for f_ in s[col_f] if isinstance(f_, dt.date) and pd.notna(f_)] if not s.empty else []
    with f2:
        if fechas_validas:
            rango = st.date_input("📆 Rango de fechas", value=(min(fechas_validas), max(fechas_validas)), key="fibra_rango")
        else:
            rango = None
    estados = st.multiselect("📌 Estado de las solicitudes", ESTATUS_ORDEN,
                             default=[e for e in ESTATUS_ORDEN if e in set(s["estatus"].dropna())], key="fibra_estados")
    ss = s[s["estatus"].isin(estados)] if not s.empty else s
    if rango and isinstance(rango, tuple) and len(rango) == 2 and not ss.empty:
        ss = ss[ss[col_f].map(lambda f_: isinstance(f_, dt.date) and pd.notna(f_) and rango[0] <= f_ <= rango[1])]

    n_sol = len(ss)
    n_inst = int((ss["estatus"] == "INSTALADA").sum()) if n_sol else 0
    n_canc = int((ss["estatus"] == "CANCELADO").sum()) if n_sol else 0
    n_reag = int((ss["reagendamientos"] > 0).sum()) if n_sol else 0
    c = st.columns(5)
    for col, (t, val, sub, cl, b) in zip(c, [("📋 Solicitudes", n_sol, "En el periodo", "t-cyan", "cyan"),
                                             ("📦 Por instalar", n_sol - n_inst - n_canc, "Pendientes / en curso", "t-amarillo", "amarillo"),
                                             ("✅ Instaladas", n_inst, "Completadas", "t-verde", "verde"),
                                             ("❌ Canceladas", n_canc, "No se instalarán", "t-rojo", "rojo"),
                                             ("🔁 Reagendadas", n_reag, "Con más de un intento", "t-morado", "morado")]):
        with col:
            ui.kpi(t, str(val), sub, cl, b)

    if not ss.empty:
        g1, g2 = st.columns(2)
        with g1:
            st.caption("Carga de instalaciones por día")
            por_dia = ss.dropna(subset=[col_f]).groupby(col_f).size()
            if not por_dia.empty:
                por_dia.index = [f_.strftime("%d/%m") for f_ in por_dia.index]
                st.bar_chart(por_dia.rename("órdenes"), color="#22d3ee")
        with g2:
            st.caption("Distribución por estado")
            st.bar_chart(ss["estatus"].value_counts(), color="#0ea5e9")

        st.caption("Detalle de solicitudes")
        cols = ["id", "pdv", "ejecutivo", "fecha_solicitud", "fecha_instalacion", "estado", "estatus",
                "intentos", "reagendamientos", "contratista", "comuna", "motivo"]
        vis = ss[[c_ for c_ in cols if c_ in ss.columns]].copy()
        vis["pdv"] = vis["pdv"].map(lambda p: nombre_tienda.get(p, p))
        vis.columns = ["ID", "Tienda", "Nombre ejecutivo", "Fecha solicitud", "Fecha instalación", "Estado", "Estatus",
                       "Intentos", "Reagendamientos", "Contratista", "Comuna", "Motivo"][:len(vis.columns)]
        vis = vis.fillna("").astype(str).replace({"None": "", "NaT": "", "nan": ""})
        st.dataframe(vis, use_container_width=True, hide_index=True)
        st.download_button("📥 Descargar agenda filtrada (CSV)", vis.to_csv(index=False).encode("utf-8-sig"),
                           file_name=f"agenda_fibra_{fecha_txt(mov.fecha_corte).replace('/', '-')}.csv", mime="text/csv")

    bloque_cancelaciones(s)

    # --- comparativo de tiendas ---------------------------------------------
    ui.seccion("🏬", "COMPARATIVO DE TIENDAS")
    filas = []
    for pdv_, nom in nombre_tienda.items():
        sp = sol[sol["pdv"] == pdv_] if not sol.empty else pd.DataFrame()
        er = res[(res["es_ejecutivo"]) & (res["pdv"] == pdv_)]
        m_, r_ = er["meta_fibra"].fillna(0).sum(), er["real_fibra"].fillna(0).sum()
        cu = r_ / m_ if m_ else 0.0
        i_ = int((sp["estatus"] == "INSTALADA").sum()) if len(sp) else 0
        filas.append([h(nom), str(len(sp)), str(i_), str(int((sp["estatus"] == "CANCELADO").sum()) if len(sp) else 0),
                      str(int(sp["estatus"].isin(["AGENDADA", "EN INSTALACIÓN", "REPROGRAMADA"]).sum()) if len(sp) else 0),
                      str(int((sp["estatus"] == "RECONTRATADA").sum()) if len(sp) else 0), entero(m_), entero(r_),
                      f'<span class="{ui.color_cump(cu / max(avance, 1e-9))}">{pct(cu, 1)}</span>',
                      f'<span class="{ui.color_cump(i_ / len(sp) if len(sp) else 0)}">{pct(i_ / len(sp) if len(sp) else 0, 1)}</span>'])
    ui.card(ui.tabla(["Tienda", "Órdenes", "Instaladas", "Canceladas", "En progreso", "Recontratadas", "Meta", "Real", "Cumplimiento", "Tasa instalación"], filas), "cyan")
    md(f'<div class="foot">Excel Fibra activo: {h(fib.archivo)} · Vista: 📡 FIBRA TIENDAS</div>')


def vista_fibra_ejecutivos():
    if fib is None:
        return _sin_fibra()
    md('<div class="card cyan" style="padding:.6rem 1rem;text-align:center"><span class="sec t-cyan">👷 FIBRA EJECUTIVOS</span></div>')
    res, sol = fib.resumen, _sol_periodo(fib.solicitudes)

    s1, s2 = st.columns(2)
    with s1:
        pdv = st.selectbox("🏬 Tienda", list(etiqueta_tienda.keys()), format_func=lambda p: etiqueta_tienda[p])
    ej_tienda = ejecutivos[ejecutivos["pdv"] == pdv]
    if ej_tienda.empty:
        st.warning("Esta tienda no tiene ejecutivos activos.")
        return
    with s2:
        codigo = st.selectbox("👤 Ejecutivo", list(ej_tienda["ejecutivo"]))
    e = ej_tienda[ej_tienda["ejecutivo"] == codigo].iloc[0]
    r = res[(res["es_ejecutivo"]) & (res["nombre"] == codigo)]
    r = r.iloc[0] if not r.empty else pd.Series(dtype=object)
    s = sol[sol["ejecutivo"] == codigo] if not sol.empty else pd.DataFrame()
    avance = avance_dias(e)

    md(f'<div class="card" style="padding:.6rem 1rem"><b>{h(codigo)}</b> · {h(mov.nombres.get(codigo, ""))} · {h(nombre_tienda.get(pdv, ""))}</div>')

    meta, real = v(r.get("meta_fibra")) or v(e.get("fib_meta")), v(r.get("real_fibra"))
    cump = real / meta if meta else 0.0
    proy = cump / avance if avance else 0.0
    c = st.columns(6)
    datos = [("🎯 Meta", entero(meta), "Meta fibra", "t-cyan"),
             ("✅ Lleva", entero(real), "Instaladas válidas", "t-verde"),
             ("📉 Faltan", entero(meta - real), "Para llegar a meta", "t-rojo"),
             ("🕐 Debe llevar", str(M.ceil_pos(e.get("fib_deben"))), "Según el corte", "t-cyan"),
             ("📊 Cumpl.", pct(cump, 1), "Real / meta", ui.color_cump(cump / max(avance, 1e-9))),
             ("🚀 Proyección", pct(proy, 1), "Cierre proyectado", ui.color_cump(proy))]
    for col, (t, val, sub, cl) in zip(c, datos):
        with col:
            ui.kpi(t, val, sub, cl, "")

    bloque_ordenes(s)
    bloque_reagendamientos(s)

    ui.seccion("📌", "SEGUIMIENTO OPERATIVO")
    c = st.columns(5)
    for col, (t, val, sub) in zip(c, [("📋 Solicitudes", entero(r.get("sol_ok")), "Órdenes del ejecutivo"),
                                      ("🟡 Pendientes", entero(r.get("FIBRA PEND. SEPT")), "Pendientes del mes"),
                                      ("🔁 Recontratadas", entero(r.get("recont")), "Resumen"),
                                      ("❌ Rechazos", entero(r.get("rechazo")), "Resumen"),
                                      ("📅 Pend. próx.", entero(r.get("PEND. OCT")), "Próximo mes")]):
        with col:
            ui.kpi(t, val, sub, "t-cyan", "")

    bloque_cancelaciones(s, con_tienda=False)

    ui.seccion("📋", "DETALLE DE ÓRDENES")
    if s.empty:
        st.info("Este ejecutivo no tiene órdenes registradas en el periodo.")
    else:
        cols = ["id", "fecha_solicitud", "fecha_instalacion", "estado", "estatus", "tipo_rechazo", "motivo",
                "intentos", "reagendamientos", "contratista", "comuna"]
        vis = s[[c_ for c_ in cols if c_ in s.columns]].copy()
        vis.columns = ["ID", "Fecha de solicitud", "Fecha de instalación", "Estado", "Estatus", "Tipo de rechazo",
                       "Motivo", "Intentos", "Reagendamientos", "Contratista", "Comuna"][:len(vis.columns)]
        st.dataframe(vis.fillna("").astype(str).replace({"None": "", "NaT": "", "nan": ""}), use_container_width=True, hide_index=True)
    md(f'<div class="foot">Excel Fibra activo: {h(fib.archivo)} · Vista: 👷 FIBRA EJECUTIVOS</div>')


# ===========================================================================
# despacho
# ===========================================================================
{
    VISTAS[0]: vista_ejecutivo,
    VISTAS[1]: vista_tiendas,
    VISTAS[2]: vista_jefe,
    VISTAS[3]: vista_fibra_tiendas,
    VISTAS[4]: vista_fibra_ejecutivos,
}[vista]()
