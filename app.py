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
# VISTA 4 · FIBRA TIENDAS
# ===========================================================================
def _sin_fibra():
    st.warning("Carga el Excel **FIBRA DRIVE** en *Gestión de archivos* para ver esta vista.")


def vista_fibra_tiendas():
    if fib is None:
        return _sin_fibra()
    res, sol = fib.resumen, fib.solicitudes
    md(f'<div class="card cyan" style="padding:.6rem 1rem">📡 <b>FIBRA DRIVE</b> · última solicitud registrada: <b>{fecha_txt(fib.fecha_actualizacion)}</b></div>')

    tiendas_res = res[~res["es_ejecutivo"]].copy()
    tiendas_res = tiendas_res[tiendas_res["pdv"].isin(nombre_tienda.keys()) | tiendas_res["nombre"].str.contains("CTF", na=False)]
    tiendas_res = tiendas_res[(tiendas_res["meta_fibra"].fillna(0) > 0) | (tiendas_res["sol_ok"].fillna(0) > 0)]
    tiendas_res = tiendas_res.drop_duplicates(subset=["pdv"], keep="first")
    filas = []
    for _, r in tiendas_res.iterrows():
        nombre = nombre_tienda.get(r["pdv"], r["nombre"])
        filas.append([h(nombre), entero(r.get("meta_sol")), entero(r.get("sol_ok")), entero(r.get("rechazo")),
                      entero(r.get("meta_fibra")), entero(r.get("real_fibra")), f'<span class="{ui.color_cump(v(r.get("cump")) / max(mov.avance_esperado, 1e-9))}">{pct(r.get("cump"))}</span>',
                      entero(r.get("meta_tv")), entero(r.get("real_tv")), pct(r.get("att_tv"), 1)])
    ui.seccion("🏬", "RESUMEN FIBRA POR TIENDA", "hoja RESUMEN")
    ui.card(ui.tabla(["Tienda", "Meta solic.", "Solic. OK", "Rechazos", "Meta fibra", "Real fibra", "% Cump.", "Meta TV", "Real TV", "Att TV"], filas), "cyan")

    if not sol.empty:
        ui.seccion("📋", "ESTADO DE LAS SOLICITUDES", "hoja AVANCE FIBRAS")
        mes = mov.fecha_corte.month if mov.fecha_corte else None
        sol_mes = sol[sol["mes"] == mes] if mes else sol
        piv = sol_mes.pivot_table(index="pdv", columns="estatus", values="ejecutivo", aggfunc="count", fill_value=0)
        piv = piv.reindex([p for p in nombre_tienda if p in piv.index])
        estatus_cols = list(piv.columns)
        filas = [[h(nombre_tienda.get(p, p))] + [entero(piv.loc[p, c]) for c in estatus_cols] + [entero(piv.loc[p].sum())] for p in piv.index]
        total = ["TOTAL"] + [entero(piv[c].sum()) for c in estatus_cols] + [entero(piv.values.sum())]
        ui.card(ui.tabla(["Tienda"] + [c.title() for c in estatus_cols] + ["Total"], filas, total), "cyan")

        ui.seccion("📈", "SOLICITUDES POR DÍA", f"mes {mes or ''}")
        por_dia = sol_mes.dropna(subset=["fecha_solicitud"]).groupby("fecha_solicitud").size()
        if not por_dia.empty:
            por_dia.index = [f_.strftime("%d/%m") for f_ in por_dia.index]
            st.bar_chart(por_dia.rename("solicitudes"), color="#22d3ee")
    md('<div class="foot">Vista: Fibra tiendas</div>')


# ===========================================================================
# VISTA 5 · FIBRA EJECUTIVOS
# ===========================================================================
def vista_fibra_ejecutivos():
    if fib is None:
        return _sin_fibra()
    res, sol = fib.resumen, fib.solicitudes
    pdv = st.selectbox("🏬 Tienda", list(etiqueta_tienda.keys()), format_func=lambda p: etiqueta_tienda[p])
    ej_res = res[(res["es_ejecutivo"]) & (res["pdv"] == pdv)]
    ui.seccion("👷", f"FIBRA POR EJECUTIVO · {nombre_tienda.get(pdv, pdv)}", "hoja RESUMEN")
    filas = []
    for _, r in ej_res.iterrows():
        rf = M.resumen_fibra_ejecutivo(sol, r["nombre"], mov.fecha_corte)
        filas.append([h(r["nombre"]), entero(r.get("sol_ok")), entero(r.get("rechazo")), entero(r.get("meta_fibra")),
                      entero(r.get("real_fibra")), f'<span class="{ui.color_cump(v(r.get("cump")) / max(mov.avance_esperado, 1e-9))}">{pct(r.get("cump"))}</span>',
                      entero(r.get("meta_tv")), entero(r.get("real_tv")), pct(r.get("att_tv"), 1),
                      fecha_txt(rf["ultima"]), str(rf["periodo"])])
    ui.card(ui.tabla(["Ejecutivo", "Solic. OK", "Rechazos", "Meta fibra", "Real fibra", "% Cump.", "Meta TV", "Real TV", "Att TV", "Última solicitud", "Solic. periodo"], filas), "cyan")

    codigo = st.selectbox("👤 Ejecutivo", list(ej_res["nombre"]) if not ej_res.empty else [])
    if codigo and not sol.empty:
        s = sol[sol["ejecutivo"] == codigo].copy()
        conteo = s["estatus"].fillna("(sin estatus)").value_counts()
        cols = st.columns(max(1, min(6, len(conteo))))
        for i, (k, n) in enumerate(conteo.items()):
            with cols[i % len(cols)]:
                ui.kpi(str(k), str(int(n)), "", "t-cyan", "cyan")
        ui.seccion("📋", "DETALLE DE SOLICITUDES", codigo)
        vis = s[["fecha_solicitud", "fecha_instalacion", "estado", "estatus", "incluye_tv", "tipo_rechazo", "motivo"]].sort_values("fecha_solicitud", ascending=False)
        vis.columns = ["Fecha solicitud", "Fecha instalación", "Estado", "Estatus", "TV", "Tipo rechazo", "Motivo"]
        vis = vis.fillna("").astype(str).replace({"None": "", "NaT": ""})
        st.dataframe(vis, use_container_width=True, hide_index=True)
    md('<div class="foot">Vista: Fibra ejecutivos</div>')


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
