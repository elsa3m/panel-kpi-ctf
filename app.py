"""
PANEL KPI CTF · réplica en Streamlit
=====================================
Punto de entrada de la aplicación.  Ejecutar con:  streamlit run app.py
"""
from __future__ import annotations

import datetime as dt
import os

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
c1, c2, c3 = st.columns([1, 2, 1])
with c1:
    if logo.exists():
        st.image(str(logo), width=220)
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

md(f'<div class="card cyan" style="padding:.6rem 1rem">📅 <b>DATOS ACTUALIZADOS AL: {fecha_txt(mov.fecha_corte)}</b> '
   f'<span class="t-gris">· Fuente: MOV-FIBRA · L{loader.C.HEADER_ROW}</span></div>')

tiendas = mov.tiendas
ejecutivos = mov.ejecutivos[mov.ejecutivos["activo"]].copy()
nombre_tienda = dict(zip(tiendas["pdv"], tiendas["tienda"]))
etiqueta_tienda = {p: f"{n} · PDV {p}" for p, n in nombre_tienda.items()}


# ===========================================================================
# BLOQUES REUTILIZABLES
# ===========================================================================
def bloque_movilidad(e: pd.Series, avance: float):
    ui.seccion("📱", "ENTEL – MOVILIDAD")
    md(f'<span class="pill">📍 AVANCE ESPERADO: {pct(avance, 1)}</span>')
    items = [
        (1, "Total móvil", "mov", "#2563eb", "mov_conv"),
        (2, "Suscripción", "sus", "#0d9488", "sus_conv"),
        (3, "Migraciones", "mis", "#a855f7", None),
        (4, "1ra línea", "l1", "#ea580c", None),
        (5, "2da línea", "l2", "#2563eb", None),
        (6, "Portabilidad", "porta", "#16a34a", "porta_conv"),
        (7, "Fibra", "fib", "#0891b2", "conv_fibra"),
    ]
    html_items = ""
    for n, nombre, k, color, conv in items:
        html_items += ui.producto(n, nombre, e.get(f"{k}_real"), e.get(f"{k}_meta"), e.get(f"{k}_falta"),
                                  e.get(f"{k}_cump"), e.get(conv) if conv else None, color)
    md(html_items)


def bloque_bonos(e: pd.Series, jornada: str):
    bf, bp, bw = M.bono_foco(e, jornada), M.bono_porta(e, jornada), M.bono_winner(e, jornada)
    tipo = "FULL" if jornada == "FT" else "PART TIME"
    cuerpo = '<div class="sec t-morado">💰 BONOS DEL EJECUTIVO</div>'
    cuerpo += ('<div class="card morado"><div class="sec" style="font-size:1.2rem">📲 BONO PORTABILIDAD</div>'
               + grid([celda("Meta bono", entero(bp["meta"])), celda("Lleva", entero(bp["real"])),
                       celda("Cumplimiento", pct(bp["cump"], 1)),
                       celda("Bono ganado", pesos(bp["monto"]), color="t-verde" if bp["gana"] else "t-verde")], 4)
               + f'<div class="sub" style="margin-top:.4rem"><b>Tipo:</b> <span class="t-verde">{tipo}</span> · <b>Regla:</b> FULL {pesos(cfg.BONO_PORTA["FULL"])} / PT {pesos(cfg.BONO_PORTA["PT"])} al cumplir meta.</div></div>')
    estado_bf = '<span class="t-verde">✅ GANA</span>' if bf["gana"] else '<span class="t-rojo">❌ NO GANA</span>'
    cuerpo += ('<div class="card morado"><div class="sec" style="font-size:1.2rem">🎯 BONO FOCO</div>'
               + grid([celda("% Suscripción", pct(bf["cump_sus"], 1)), celda("% Fibra", pct(bf["cump_fib"], 1)),
                       celda("% Bono foco", pct(bf["pct"])), celda("Estado", estado_bf)], 4) + '</div>')
    estado_bw = '<span class="t-verde">✅ GANA</span>' if bw["gana"] else '<span class="t-rojo">❌ NO GANA</span>'
    cuerpo += ('<div class="card morado"><div class="sec" style="font-size:1.2rem">🏆 BONO WINNER</div>'
               + grid([celda("Att seguro", pct(bw["att_seg"], 1)), celda("Att ene./prot.", pct(bw["att_ene_prot"], 1)),
                       celda("Att TV full", pct(bw["att_tv"], 1)), celda("Cumplimiento", pct(bw["cump"], 1))], 4)
               + f'<div class="sub" style="margin-top:.4rem">{estado_bw} · <b>Bono:</b> {pesos(bw["monto"])} · <b>Tipo:</b> <span class="t-verde">{tipo}</span></div></div>')
    ui.card(cuerpo, "morado")
    return {"foco": bf, "porta": bp, "winner": bw}


def bloque_fibra(e: pd.Series):
    cuerpo = '<div class="sec">📶 FIBRA (REAL ENTEL)</div>' + grid([
        celda("Q Validaciones", entero(e.get("q_valid")), f"% Validación {pct(e.get('pct_valid'))}<br>Incorrectas {pct(e.get('valid_inc'))}", True, "t-cyan"),
        celda("Factibles", entero(e.get("factibles")), f"% Factibles {pct(e.get('pct_fact'))}", True, "t-cyan"),
        celda("Conv. fibra", pct(e.get("conv_fibra")), "", True, "t-cyan"),
        celda("Factor de prod.", pct(e.get("factor_prod")) if v(e.get("factor_prod")) <= 1 else f"{v(e.get('factor_prod')):.2f}", "", True, "t-cyan"),
        celda("Tasa de instalación", pct(e.get("tasa_inst")), "", True, "t-cyan"),
        celda("Fibra solicitudes", entero(e.get("fib_sol")), f"Pendientes: {entero(e.get('fib_pend'))}", True, "t-cyan"),
    ], 2)
    ui.card(cuerpo, "cyan")


def bloque_equipos(e: pd.Series):
    cuerpo = '<div class="sec" style="text-align:center">📱 EQUIPOS</div>' + grid([
        celda("Cumplimiento", pct(e.get("eq_cump"))), celda("Conv. equipos", pct(e.get("eq_conv"), 1)),
        celda("Vendidos / meta", f"{entero(e.get('eq_q'))} / {entero(e.get('eq_meta_q'))}"),
        celda("Q faltan", entero(v(e.get("eq_meta_q")) - v(e.get("eq_q")))),
        celda("Att. eq–línea", pct(e.get("att_eq_linea"), 1)),
    ], 5) + grid([
        celda("Meta ($)", pesos(e.get("eq_meta"))), celda("Real ($)", pesos(e.get("eq_real"))),
        celda("Falta ($)", pesos(e.get("eq_falta"))), celda("Deben llevar al corte ($)", pesos(e.get("eq_deben"))),
    ], 2)
    ui.card(cuerpo, "")


def bloque_seguros(e: pd.Series):
    cuerpo = '<div class="sec" style="text-align:center">🛡️ SEGUROS</div>' + grid([
        celda("Meta (Q)", entero(e.get("seg_meta"))), celda("Real (Q)", entero(e.get("seg_real"))),
        celda("Falta (Q)", entero(e.get("seg_falta"))), celda("Deben llevar", str(M.ceil_pos(e.get("seg_deben")))),
    ], 4) + grid([celda("Cumplimiento", pct(e.get("seg_cump"))), celda("Attach", pct(e.get("att_seg"), 1))], 2)
    ui.card(cuerpo, "morado")


def bloque_accesorios(e: pd.Series):
    cuerpo = '<div class="sec" style="text-align:center">👜 ACCESORIOS</div>' + grid([
        celda("Meta ($)", pesos(e.get("acc_meta"))), celda("Real ($)", pesos(e.get("acc_real"))),
        celda("Falta ($)", pesos(e.get("acc_falta"))), celda("Deben llevar ($)", pesos(e.get("acc_deben"))),
    ], 2) + grid([
        celda("Cumplimiento", pct(e.get("acc_cump"))), celda("Conv. acc.", pct(e.get("acc_conv"), 1)),
        celda("Q vendidos / meta", f"{entero(e.get('acc_q'))} / {entero(e.get('acc_meta_q'))}"),
    ], 3)
    ui.card(cuerpo, "naranjo")


def bloque_energia_proteccion(e: pd.Series):
    ui.card('<div class="sec" style="text-align:center">⚡ ENERGÍA</div>' + grid([
        celda("$ Energía", pesos(e.get("ene_usd"))), celda("Q Energía", entero(e.get("ene_q"))),
        celda("Conv.", pct(e.get("ene_conv"))), celda("Attach", pct(e.get("ene_att"))),
    ], 4), "amarillo")
    ui.card('<div class="sec" style="text-align:center">🛡️ PROTECCIÓN</div>' + grid([
        celda("$ Protección", pesos(e.get("prot_usd"))), celda("Q Protec.", entero(e.get("prot_q"))),
        celda("Conv.", pct(e.get("prot_conv"))), celda("Attach", pct(e.get("prot_att"))),
    ], 4), "rojo")


def bloque_epa(e: pd.Series):
    ui.card('<div class="sec" style="text-align:center">☑️ EPA <small>(EVALUACIÓN PLAN DE ACCIÓN)</small></div>' + grid([
        celda("Meta EPA", pct(e.get("epa_meta"), 0), grande=True),
        celda("EPA actual", pct(e.get("epa"), 1), grande=True, color=ui.color_cump(v(e.get("epa")) / v(e.get("epa_meta"), 1) if v(e.get("epa_meta")) else None)),
    ], 2), "cyan")


def bloque_escuchas(codigo: str, tienda: str, escuchas: pd.DataFrame | None):
    ui.seccion("🎧", "ESCUCHAS")
    if escuchas is None or escuchas.empty:
        st.info("Carga el Excel **ESCUCHAS ENTEL** en *Gestión de archivos* para ver Latam Pass, Hogar, Fibra y Portabilidad.")
        return
    fila = escuchas[escuchas["ejecutivo"] == codigo]
    if fila.empty:
        st.info("Este ejecutivo no tiene escuchas registradas.")
        return
    r = fila.iloc[0]

    def ref(nombre):
        f = escuchas[escuchas["ejecutivo"].str.upper() == nombre.upper()]
        return f.iloc[0] if not f.empty else None

    t, canal, ctf = ref(tienda), ref("CANAL"), ref("CTF")

    def refs(col):
        partes = []
        if t is not None:
            partes.append(f"Tienda <span class='t-cyan'>{pct(t[col], 1)}</span>")
        if canal is not None:
            partes.append(f"Canal <span class='t-cyan'>{pct(canal[col], 1)}</span>")
        if ctf is not None:
            partes.append(f"CTF <span class='t-cyan'>{pct(ctf[col], 1)}</span>")
        return " · ".join(partes)

    a, b = st.columns(2)
    with a:
        ui.card(f'<div class="h">✈️ LATAM PASS</div><div class="big t-verde">{pct(r["latam_pass"], 1)}</div><div class="hr"></div><div class="sub">{refs("latam_pass")}</div>', "cyan")
        ui.card('<div class="h">📡 FIBRA</div>' + grid([celda("Calidad", pct(r["fibra_calidad"], 1), color="t-amarillo"), celda("Estabilidad", pct(r["fibra_estabilidad"], 1), color="t-amarillo")], 2)
                + f'<div class="sub" style="margin-top:.4rem">{refs("fibra_calidad")}</div>', "cyan")
    with b:
        ui.card(f'<div class="h">🏠 HOGAR</div><div class="big t-verde">{pct(r["hogar"], 1)}</div><div class="hr"></div><div class="sub">{refs("hogar")}</div>', "cyan")
        ui.card('<div class="h">📲 PORTABILIDAD</div>' + grid([celda("Motivo", pct(r["porta_motivo"], 1), color="t-amarillo"), celda("Objeciones", pct(r["porta_objeciones"], 1), color="t-amarillo"), celda("Urgencia", pct(r["porta_urgencia"], 1), color="t-amarillo")], 3)
                + f'<div class="sub" style="margin-top:.4rem">{refs("porta_motivo")}</div>', "cyan")


def bloque_epa_encuestas(codigo: str, mov_datos):
    ui.seccion("🗣️", "EPA Y ENCUESTAS DEL EJECUTIVO")
    epa_row = mov_datos.epa_ejecutivo[mov_datos.epa_ejecutivo["ejecutivo"] == codigo]
    enc = mov_datos.encuestas[mov_datos.encuestas["ejecutivo"] == codigo] if not mov_datos.encuestas.empty else pd.DataFrame()
    epa_val = epa_row.iloc[0]["epa"] if not epa_row.empty else None
    q_total = int(v(epa_row.iloc[0]["q_total"])) if not epa_row.empty else 0
    n_enc = len(enc) if not enc.empty else q_total
    por_rec = int((enc["nota"] <= 0).sum()) if not enc.empty and "nota" in enc else 0
    a, b, c = st.columns(3)
    with a:
        ui.kpi("EPA actual", pct(epa_val, 1, "—") if q_total else "—", "Fuente: hoja EPA", "t-verde" if q_total else "", "", "🎯")
    with b:
        ui.kpi("Encuestas", str(n_enc), "Registradas en el periodo", "", "", "📝")
    with c:
        ui.kpi("Por recuperar", str(por_rec), "Notas 0 y -1", "", "", "⚠️")
    if enc.empty:
        st.info("Este ejecutivo no tiene encuestas detalladas registradas en BASE EPA.")
    else:
        cols = [c for c in ("fecha", "nota", "tipo_atencion", "literal") if c in enc.columns]
        st.dataframe(enc[cols].sort_values("fecha", ascending=False), use_container_width=True, hide_index=True)


def bloque_prioridades(e: pd.Series, mov_datos, titulo="3 PRIORIDADES DEL CORTE"):
    lista = M.alertas(e, mov_datos.estandares, mov_datos.avance_esperado)
    prios = M.prioridades(lista, 3)
    focos = len({a["foco"] for a in lista})
    cuerpo = f'<div class="sec">🎯 {titulo}</div><div class="sub" style="text-align:left;color:#fda4af"><b>{len(lista)} alertas consolidadas en {focos} focos. Trabaja primero estas tres prioridades.</b></div>'
    for i, p in enumerate(prios, 1):
        cuerpo += f'<div class="prio"><div class="k">PRIORIDAD {i}</div><div class="f">{h(p["foco"])}</div><div class="d">{h(p["texto"])}</div></div>'
    if not prios:
        cuerpo += '<div class="sub t-verde">Sin alertas: todos los KPI están sobre el corte y el estándar.</div>'
    ui.card(cuerpo, "rosa")
    return prios


# ===========================================================================
# VISTA 1 · EJECUTIVO
# ===========================================================================
def vista_ejecutivo():
    pdv = st.selectbox("🏬 Tienda", list(etiqueta_tienda.keys()), format_func=lambda p: etiqueta_tienda[p])
    ej_tienda = ejecutivos[ejecutivos["pdv"] == pdv]
    if ej_tienda.empty:
        st.warning("Esta tienda no tiene ejecutivos activos en MOV-FIBRA.")
        return
    codigo = st.selectbox("👤 Ejecutivo", list(ej_tienda["ejecutivo"]))
    e = ej_tienda[ej_tienda["ejecutivo"] == codigo].iloc[0]
    tienda = nombre_tienda.get(pdv, "")
    nombre = mov.nombres.get(codigo, "")
    jornada = M.jornada_de(codigo, mov.jornadas)
    f = M.ficha(e, mov.pesos)

    # --- ficha PDF (se calcula antes para mostrar el botón arriba) ----------
    bonos = {"foco": M.bono_foco(e, jornada), "porta": M.bono_porta(e, jornada), "winner": M.bono_winner(e, jornada)}
    prios = M.prioridades(M.alertas(e, mov.estandares, mov.avance_esperado), 3)
    try:
        from kpi.pdf import ficha_pdf
        pdf_bytes = ficha_pdf(e.to_dict(), nombre, tienda, mov.fecha_corte, f, bonos, prios)
        st.download_button("📥 Descargar ficha PDF", pdf_bytes,
                           file_name=f"ficha_{codigo}_{fecha_txt(mov.fecha_corte).replace('/', '-')}.pdf", mime="application/pdf")
    except Exception as ex:  # noqa: BLE001
        st.caption(f"PDF no disponible: {ex}")

    md(f'<div class="card" style="padding:.6rem 1rem">Tienda: <b>{h(tienda)}</b> · Ejecutivos en esta tienda: <b>{len(ej_tienda)}</b></div>')

    # --- encabezado -------------------------------------------------------
    c1, c2 = st.columns([1, 2.3])
    with c1:
        ui.card(f'<div class="mid">🏬 PDV {h(pdv)}</div><div class="sub t-cyan" style="font-weight:800;font-size:1rem">{h(tienda)}</div>'
                f'<div class="hr"></div><div class="h t-cyan">📅 CORTE</div><div class="mid">{fecha_txt(mov.fecha_corte)}</div>', "cyan")
    with c2:
        ui.card('<div class="h">EJECUTIVO SELECCIONADO</div>'
                f'<div class="big t-cyan" style="font-size:2.4rem">{h(codigo)}</div>'
                + grid([mini("👤 Nombre", h(nombre or "Por completar")), mini("⏳ Antigüedad", "Por completar"),
                        mini("🕒 Jornada", jornada), mini("🎂 Cumpleaños", "Por completar")], 4), "")
        rf = M.resumen_fibra_ejecutivo(fib.solicitudes if fib else None, codigo, mov.fecha_corte)
        if rf["ultima"]:
            cuando = "Hoy" if rf["hoy"] else (f"Hace {rf['dias']} días" if rf["dias"] is not None else "")
            ui.card(f'<div class="h t-cyan">ÚLTIMA SOLICITUD DE FIBRA</div><div class="mid t-verde">📅 {fecha_txt(rf["ultima"])}</div>'
                    f'<div class="sub">{cuando} · {rf["periodo"]} solicitudes en el periodo</div>', "cyan")
        else:
            ui.card('<div class="h t-cyan">ÚLTIMA SOLICITUD DE FIBRA</div><div class="mid t-rojo">Sin solicitudes</div>'
                    '<div class="sub">0 solicitudes en el periodo</div>', "cyan")

    # --- fila de KPIs principales -----------------------------------------
    k1, k2, k3, k4, k5, k6 = st.columns(6)
    with k1:
        ui.kpi("% Real a la fecha", pct(f["cump"]), f'<b class="t-amarillo" style="font-size:1.2rem">TRAMO {f["tramo"]}</b><br><b class="t-amarillo">{f["etiqueta"]}</b>', "t-amarillo", "amarillo")
    with k2:
        ui.kpi("% Proyección", pct(f["proy"]), f'<b class="t-verde" style="font-size:1.2rem">TRAMO {f["tramo_proy"]}</b><br><b class="t-verde">{f["etiqueta_proy"]}</b>', "t-verde", "verde")
    with k3:
        prom = ej_tienda.loc[ej_tienda["ejecutivo"] != codigo, "atenciones"]
        prom_full = prom.mean() if not prom.empty else 0
        dif = v(e["atenciones"]) - prom_full
        ui.kpi("Atenciones", entero(e["atenciones"]), f"Prom. pares FULL: {entero(prom_full)} · <b class='{'t-verde' if dif >= 0 else 't-rojo'}'>{'+' if dif >= 0 else ''}{entero(dif)}</b>", "", "", "👤")
    with k4:
        ui.kpi("Días restantes", entero(e["dias_rest"]), "", "", "", "📅")
    with k5:
        ui.kpi("Meta EPA", pct(e["epa_meta"], 0), "", "", "", "🎯")
    with k6:
        ui.kpi("EPA actual", pct(e["epa"], 1), "", ui.color_cump(v(e["epa"]) / v(e["epa_meta"], 1) if v(e["epa_meta"]) else None), "")

    # --- movilidad -----------------------------------------------------------
    bloque_movilidad(e, mov.avance_esperado)
    bloque_bonos(e, jornada)
    bloque_fibra(e)
    bloque_equipos(e)
    bloque_seguros(e)
    bloque_accesorios(e)
    bloque_energia_proteccion(e)
    bloque_epa(e)
    bloque_escuchas(codigo, tienda, esc)
    bloque_epa_encuestas(codigo, mov)
    bloque_prioridades(e, mov)

    md(f'<div class="foot">Archivo cargado: {h(mov.archivo)} · Vista: Ejecutivo · {h(tienda)} · Ejecutivos: {len(ej_tienda)}</div>')


# ===========================================================================
# VISTA 2 · TIENDAS / CTF
# ===========================================================================
def fila_resumen(r, nombre) -> list[str]:
    return [h(nombre), entero(r.get("atenciones")),
            f"{entero(r.get('mov_real'))} / {entero(r.get('mov_meta'))}", f'<span class="{ui.color_cump(v(r.get("mov_cump")) / max(mov.avance_esperado, 1e-9))}">{pct(r.get("mov_cump"))}</span>',
            pct(r.get("mov_conv"), 1), f"{entero(r.get('porta_real'))} / {entero(r.get('porta_meta'))}",
            f"{entero(r.get('fib_real'))} / {entero(r.get('fib_meta'))}", pct(r.get("fib_cump")),
            pct(r.get("eq_cump")), pct(r.get("seg_cump")), pct(r.get("acc_cump")), pct(r.get("epa"), 0)]


COLS_RESUMEN = ["Tienda / Ejecutivo", "Atenc.", "Móvil real/meta", "Cump. móvil", "Conv. móvil", "Porta", "Fibra", "Cump. fibra",
                "Cump. equipos", "Cump. seguros", "Cump. acc.", "EPA"]


def vista_tiendas():
    tot = mov.total
    md(f'<span class="pill">📍 AVANCE ESPERADO: {pct(mov.avance_esperado, 1)}</span>')
    k = st.columns(6)
    with k[0]:
        ui.kpi("Atenciones CTF", entero(tot.get("atenciones")), "", "", "cyan", "👥")
    with k[1]:
        ui.kpi("Móvil CTF", f"{entero(tot.get('mov_real'))} <span class='t-gris' style='font-size:1.1rem'>de {entero(tot.get('mov_meta'))}</span>", f"Cump. {pct(tot.get('mov_cump'))} · Conv. {pct(tot.get('mov_conv'), 1)}", "", "cyan")
    with k[2]:
        ui.kpi("Portabilidad", f"{entero(tot.get('porta_real'))} <span class='t-gris' style='font-size:1.1rem'>de {entero(tot.get('porta_meta'))}</span>", f"Cump. {pct(tot.get('porta_cump'))}", "", "verde")
    with k[3]:
        ui.kpi("Fibra", f"{entero(tot.get('fib_real'))} <span class='t-gris' style='font-size:1.1rem'>de {entero(tot.get('fib_meta'))}</span>", f"Cump. {pct(tot.get('fib_cump'))} · Conv. {pct(tot.get('conv_fibra'), 1)}", "", "cyan")
    with k[4]:
        ui.kpi("$ Equipos", pesos(tot.get("eq_real")), f"Meta {pesos(tot.get('eq_meta'))} · {pct(tot.get('eq_cump'))}", "", "")
    with k[5]:
        ui.kpi("$ Accesorios", pesos(tot.get("acc_real")), f"Meta {pesos(tot.get('acc_meta'))} · {pct(tot.get('acc_cump'))}", "", "naranjo")

    ui.seccion("🏬", "RESUMEN POR TIENDA", f"corte {fecha_txt(mov.fecha_corte)}")
    filas = [fila_resumen(r, r["tienda"]) for _, r in tiendas.iterrows()]
    total = fila_resumen(tot, "TOTAL CTF") if tot else None
    ui.card(ui.tabla(COLS_RESUMEN, filas, total))

    ui.seccion("📊", "CUMPLIMIENTO PONDERADO POR TIENDA", "promedio de la ficha de sus ejecutivos")
    cols = st.columns(len(tiendas)) if len(tiendas) <= 6 else st.columns(6)
    for i, (_, t) in enumerate(tiendas.iterrows()):
        ej = ejecutivos[ejecutivos["pdv"] == t["pdv"]]
        prom = ej["cump_ficha"].mean() if not ej.empty else None
        proy = ej["proy_pond"].mean() if not ej.empty else None
        with cols[i % len(cols)]:
            ui.kpi(t["tienda"], pct(prom), f"Proy. <b class='{ui.color_cump(proy)}'>{pct(proy)}</b> · {len(ej)} ejec.", ui.color_cump(prom), "")

    ui.seccion("🏆", "RANKING DE EJECUTIVOS CTF", "por % real de la ficha")
    rk = ejecutivos.sort_values("cump_ficha", ascending=False)
    filas = []
    for i, (_, r) in enumerate(rk.iterrows(), 1):
        f = M.ficha(r, mov.pesos)
        filas.append([str(i), h(r["ejecutivo"]), h(r["tienda"]), f'<span class="{ui.color_cump(f["cump"])}">{pct(f["cump"])}</span>',
                      str(f["tramo"]), f'<span class="{ui.color_cump(f["proy"])}">{pct(f["proy"])}</span>', entero(r["atenciones"]),
                      f"{entero(r['mov_real'])}/{entero(r['mov_meta'])}", f"{entero(r['fib_real'])}/{entero(r['fib_meta'])}", pct(r["epa"], 0)])
    ui.card(ui.tabla(["#", "Ejecutivo", "Tienda", "% Real", "Tramo", "% Proy.", "Atenc.", "Móvil", "Fibra", "EPA"], filas, izq=3))
    md(f'<div class="foot">Archivo cargado: {h(mov.archivo)} · Vista: Tiendas / CTF</div>')


# ===========================================================================
# VISTA 3 · JEFE DE TIENDA
# ===========================================================================
def vista_jefe():
    pdv = st.selectbox("🏬 Tienda", list(etiqueta_tienda.keys()), format_func=lambda p: etiqueta_tienda[p])
    t = tiendas[tiendas["pdv"] == pdv].iloc[0]
    ej = ejecutivos[ejecutivos["pdv"] == pdv]
    tienda = t["tienda"]

    md(f'<div class="card" style="padding:.6rem 1rem">Tienda: <b>{h(tienda)}</b> · PDV {h(pdv)} · Ejecutivos activos: <b>{len(ej)}</b> · Corte: <b>{fecha_txt(mov.fecha_corte)}</b></div>')
    k = st.columns(6)
    with k[0]:
        ui.kpi("Atenciones", entero(t["atenciones"]), f"Días restantes: {entero(t['dias_rest'])}", "", "cyan", "👥")
    with k[1]:
        ui.kpi("% Real ficha (prom.)", pct(ej["cump_ficha"].mean() if not ej.empty else None), "", ui.color_cump(ej["cump_ficha"].mean() if not ej.empty else None), "amarillo")
    with k[2]:
        ui.kpi("% Proyección (prom.)", pct(ej["proy_pond"].mean() if not ej.empty else None), "", ui.color_cump(ej["proy_pond"].mean() if not ej.empty else None), "verde")
    with k[3]:
        ui.kpi("Móvil", f"{entero(t['mov_real'])} <span class='t-gris' style='font-size:1.1rem'>de {entero(t['mov_meta'])}</span>", f"Deben llevar {M.ceil_pos(t['mov_deben'])} · Cump. {pct(t['mov_cump'])}", "", "")
    with k[4]:
        ui.kpi("Fibra", f"{entero(t['fib_real'])} <span class='t-gris' style='font-size:1.1rem'>de {entero(t['fib_meta'])}</span>", f"Deben llevar {M.ceil_pos(t['fib_deben'])} · Conv. {pct(t['conv_fibra'], 1)}", "", "cyan")
    with k[5]:
        ui.kpi("EPA tienda", pct(t["epa"], 1), f"Meta {pct(t['epa_meta'], 0)}", ui.color_cump(v(t["epa"]) / v(t["epa_meta"], 1) if v(t["epa_meta"]) else None), "")

    bloque_movilidad(t, mov.avance_esperado)
    c1, c2 = st.columns(2)
    with c1:
        bloque_equipos(t)
        bloque_accesorios(t)
    with c2:
        bloque_seguros(t)
        bloque_fibra(t)
    bloque_energia_proteccion(t)

    ui.seccion("👥", "EJECUTIVOS DE LA TIENDA", "semáforo del corte")
    filas = []
    for _, r in ej.sort_values("cump_ficha", ascending=False).iterrows():
        f = M.ficha(r, mov.pesos)
        al = M.alertas(r, mov.estandares, mov.avance_esperado)
        filas.append([h(r["ejecutivo"]), h(mov.nombres.get(r["ejecutivo"], "")), entero(r["atenciones"]),
                      f'<span class="{ui.color_cump(f["cump"])}">{pct(f["cump"])}</span>', str(f["tramo"]),
                      f'<span class="{ui.color_cump(f["proy"])}">{pct(f["proy"])}</span>',
                      f"{entero(r['mov_real'])}/{M.ceil_pos(r['mov_deben'])}", f"{entero(r['porta_real'])}/{M.ceil_pos(r['porta_deben'])}",
                      f"{entero(r['fib_real'])}/{M.ceil_pos(r['fib_deben'])}", f"{entero(r['seg_real'])}/{M.ceil_pos(r['seg_deben'])}",
                      pct(r["eq_cump"]), pct(r["epa"], 0), f'<span class="{"t-rojo" if len(al) >= 8 else "t-amarillo" if len(al) >= 4 else "t-verde"}">{len(al)}</span>'])
    ui.card(ui.tabla(["Ejecutivo", "Nombre", "Atenc.", "% Real", "Tramo", "% Proy.", "Móvil / corte", "Porta / corte", "Fibra / corte", "Seg. / corte", "Cump. eq.", "EPA", "Alertas"], filas, izq=2))

    ui.seccion("🎯", "PRIORIDADES POR EJECUTIVO")
    cols = st.columns(2)
    for i, (_, r) in enumerate(ej.iterrows()):
        with cols[i % 2]:
            prios = M.prioridades(M.alertas(r, mov.estandares, mov.avance_esperado), 3)
            cuerpo = f'<div class="sec" style="font-size:1.1rem">{h(r["ejecutivo"])}</div>'
            for j, p in enumerate(prios, 1):
                cuerpo += f'<div class="prio"><div class="k">PRIORIDAD {j} · {h(p["foco"])}</div><div class="d">{h(p["texto"])}</div></div>'
            if not prios:
                cuerpo += '<div class="sub t-verde">Sin alertas.</div>'
            ui.card(cuerpo, "rosa")
    md(f'<div class="foot">Archivo cargado: {h(mov.archivo)} · Vista: Jefe de tienda · {h(tienda)}</div>')


# ===========================================================================
# VISTA 4 · FIBRA TIENDAS
# ===========================================================================
def _sin_fibra():
    st.warning("Carga el Excel **FIBRA DRIVE** en *Gestión de archivos* para ver esta vista.")


def vista_fibra_tiendas():
    if fib is None:
        return _sin_fibra()
    res, sol = fib.resumen, fib.solicitudes
    md(f'<div class="card cyan" style="padding:.6rem 1rem">📡 <b>FIBRA DRIVE</b> · última solicitud registrada: <b>{fecha_txt(fib.fecha_actualizacion)}</b> · Archivo: {h(fib.archivo)}</div>')

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
    ui.card(ui.tabla(["Tienda", "Meta solic.", "Solic. OK", "Rechazos", "Meta fibra", "Real fibra", "% Cump.", "Meta TV", "Real TV", "Att TV"], filas))

    if not sol.empty:
        ui.seccion("📋", "ESTADO DE LAS SOLICITUDES", "hoja AVANCE FIBRAS")
        mes = mov.fecha_corte.month if mov.fecha_corte else None
        sol_mes = sol[sol["mes"] == mes] if mes else sol
        piv = sol_mes.pivot_table(index="pdv", columns="estatus", values="ejecutivo", aggfunc="count", fill_value=0)
        piv = piv.reindex([p for p in nombre_tienda if p in piv.index])
        estatus_cols = list(piv.columns)
        filas = [[h(nombre_tienda.get(p, p))] + [entero(piv.loc[p, c]) for c in estatus_cols] + [entero(piv.loc[p].sum())] for p in piv.index]
        total = ["TOTAL"] + [entero(piv[c].sum()) for c in estatus_cols] + [entero(piv.values.sum())]
        ui.card(ui.tabla(["Tienda"] + [c.title() for c in estatus_cols] + ["Total"], filas, total))

        ui.seccion("📈", "SOLICITUDES POR DÍA", f"mes {mes or ''}")
        por_dia = sol_mes.dropna(subset=["fecha_solicitud"]).groupby("fecha_solicitud").size()
        if not por_dia.empty:
            por_dia.index = [f.strftime("%d/%m") for f in por_dia.index]
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
    ui.card(ui.tabla(["Ejecutivo", "Solic. OK", "Rechazos", "Meta fibra", "Real fibra", "% Cump.", "Meta TV", "Real TV", "Att TV", "Última solicitud", "Solic. periodo"], filas))

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
