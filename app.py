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

from kpi import ajustes as A
from kpi import config as cfg
from kpi import historia, loader, metrics as M, ui
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


@st.cache_data(show_spinner="Leyendo COLABORADORES…")
def _cargar_colab(path: str, mtime: float):
    return loader.cargar_colaboradores(path)


def cargar(nombre: str):
    p = loader.ruta_fuente(nombre)
    if not p.exists():
        return None
    fn = {"MOV-FIBRA": _cargar_mov, "FIBRA DRIVE": _cargar_fibra,
          "ESCUCHAS ENTEL": _cargar_escuchas, "COLABORADORES": _cargar_colab}[nombre]
    try:
        return fn(str(p), p.stat().st_mtime)
    except Exception as ex:  # noqa: BLE001
        st.error(f"No se pudo leer {nombre}: {ex}")
        return None


# ---------------------------------------------------------------------------
# cabecera
# ---------------------------------------------------------------------------
def buscar_logo():
    """
    Logo de la cabecera. Basta con dejar el archivo en assets/ con cualquiera de
    estos nombres; se usa el primero que exista. Para cambiarlo, reemplaza el
    archivo (idealmente PNG con fondo transparente, de 600 px de ancho o más).
    """
    for nombre in ("logo.png", "logo.jpg", "logo.jpeg", "logo.webp", "logo.svg"):
        p = cfg.ASSETS_DIR / nombre
        if p.exists():
            return p
    return None


def logo_html(p) -> str:
    """
    El logo va sobre una placa blanca redondeada: el archivo trae fondo blanco y
    el texto 'tecnología' es casi negro, así que sobre el fondo oscuro del panel
    desaparecería. La placa mantiene los colores de marca tal como son.
    """
    import base64
    mimes = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
             ".webp": "image/webp", ".svg": "image/svg+xml"}
    b64 = base64.b64encode(p.read_bytes()).decode()
    return (f'<div class="logo-box"><img src="data:{mimes.get(p.suffix.lower(), "image/png")};base64,{b64}" '
            f'alt="CTF Tecnología"></div>')


logo = buscar_logo()
c1, c2, c3 = st.columns([1, 2.4, 1])
with c1:
    if logo:
        md(logo_html(logo))
with c2:
    md('<h1 class="titulo">PANEL KPI CTF</h1>')

VISTAS = ["👤 Vista Ejecutivo", "🏬 Vista Tiendas / CTF", "👔 Jefe de Tienda", "📡 Fibra Tiendas", "👷 Fibra Ejecutivos"]
vista = st.radio("Vista", VISTAS, horizontal=True, label_visibility="collapsed")

# ---------------------------------------------------------------------------
# gestión de archivos
# ---------------------------------------------------------------------------
with st.expander("📁 GESTIÓN DE ARCHIVOS", expanded=False):
    st.caption("Los Excel activos quedan guardados en el servidor. Mantén también una copia de respaldo externa.")
    st.caption("Puedes cargar un archivo nuevo para reemplazar el anterior, o eliminarlo manualmente con el botón correspondiente.")
    for nombre, meta in cfg.FUENTES.items():
        st.subheader(f"{meta['icono']} {meta['titulo']}")
        subido = st.file_uploader(f"Cargar / reemplazar Excel {meta['titulo']}", type=["xlsx", "xlsm"],
                                  key=f"up_{nombre}", help=meta["ayuda"])
        destino = loader.ruta_fuente(nombre)
        if subido is not None:
            if meta.get("reducir"):
                # solo se guardan las columnas que usa el panel; el resto se descarta
                try:
                    n = loader.guardar_colaboradores_reducido(subido.getvalue(), destino)
                    st.success(f"{subido.name}: guardados {n} colaboradores (solo código, nombre, ingreso, nacimiento y jornada).")
                except Exception as ex:  # noqa: BLE001
                    st.error(f"No se pudo procesar {subido.name}: {ex}")
                    destino.unlink(missing_ok=True)
            else:
                destino.write_bytes(subido.getbuffer())
                st.success(f"{subido.name} guardado como {meta['titulo']}.")
            (destino.with_suffix(".nombre.txt")).write_text(subido.name, encoding="utf-8")
            st.cache_data.clear()
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

    # --- histórico de cortes -------------------------------------------------
    st.subheader("🕘 HISTÓRICO DE CORTES")
    st.caption("Cada Excel que cargas queda registrado como un corte. Con dos o más cortes el panel "
               "muestra la tendencia y la variación. **Descarga el histórico de vez en cuando**: si el "
               "servidor reinicia la app, se pierde y lo puedes volver a cargar aquí.")
    st.markdown(f"**{historia.resumen()}**")
    hc1, hc2 = st.columns(2)
    with hc1:
        st.download_button("📥 Descargar histórico (CSV)", historia.exportar_csv(),
                           file_name="historico_kpi_ctf.csv", mime="text/csv", key="dl_hist")
    with hc2:
        hist_up = st.file_uploader("Restaurar histórico guardado", type=["csv"], key="up_hist")
        if hist_up is not None:
            try:
                n = historia.importar_csv(hist_up.getvalue())
                st.success(f"Histórico restaurado: {n} filas.")
            except Exception as ex:  # noqa: BLE001
                st.error(f"No se pudo leer el histórico: {ex}")

mov = cargar("MOV-FIBRA")
fib = cargar("FIBRA DRIVE")
esc = cargar("ESCUCHAS ENTEL")
colab = cargar("COLABORADORES")
COLAB = {} if colab is None or colab.empty else {r["ejecutivo"]: r for _, r in colab.iterrows()}

if mov is None:
    st.warning("Carga el Excel **MOV-FIBRA** en *Gestión de archivos* para comenzar.")
    st.stop()

for aviso in mov.avisos:
    st.warning(aviso)

# el corte cargado se registra en el histórico (si ya estaba, se reemplaza)
try:
    historia.guardar_corte(mov)
except Exception:  # noqa: BLE001  el histórico nunca debe romper el panel
    pass


def tendencia(clave: str, kpi: str, en_puntos: bool = True, invertir: bool = False) -> str:
    """Chip de variación + mini-gráfico de los últimos cortes, si los hay."""
    var = historia.variacion(clave, kpi)
    if var is None:
        return ""
    factor = 100 if en_puntos else 1
    sufijo = " pts" if en_puntos else ""
    chip = ui.delta(var["delta"] * factor, sufijo, invertir=invertir)
    s = historia.serie(clave, kpi, n=12)
    spark = ui.sparkline(list(s.values)) if len(s) > 2 else ""
    desde = var["fecha_anterior"]
    desde = desde.strftime("%d/%m") if hasattr(desde, "strftime") else str(desde)
    return f'<div class="ref">{chip} <span class="t-gris">vs. {desde}</span></div>{spark}'

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
# BLOQUES: cada vista se arma con una lista de bloques que la usuaria puede
# mostrar, ocultar, reordenar, abrir/cerrar y renombrar desde ⚙️ Personalizar.
# ===========================================================================
class Bloque:
    """
    Un trozo de una vista.

    fijo=True  -> siempre visible y en su lugar (la cabecera, por ejemplo);
                  no aparece en la lista de reordenar.
    suelto=True-> se dibuja directo, sin caja desplegable.
    """

    def __init__(self, id_: str, titulo: str, dibujar, abierto: bool = True,
                 fijo: bool = False, suelto: bool = False):
        self.id, self.titulo, self.dibujar = id_, titulo, dibujar
        self.abierto, self.fijo, self.suelto = abierto, fijo, suelto


def render_bloques(vista: str, bloques: list[Bloque]) -> None:
    """Dibuja los bloques de una vista respetando los ajustes guardados."""
    fijos = [b for b in bloques if b.fijo]
    movibles = [b for b in bloques if not b.fijo]
    conf = {b.id: A.seccion(vista, b.id, b.titulo, b.abierto, i)
            for i, b in enumerate(bloques)}

    for b in fijos:
        b.dibujar()

    for b in sorted(movibles, key=lambda x: conf[x.id]["orden"]):
        c = conf[b.id]
        if not c["visible"]:
            continue
        if b.suelto:
            b.dibujar()
        else:
            with st.expander(c["titulo"], expanded=c["abierto"]):
                b.dibujar()


def panel_personalizar(vista: str, bloques: list[Bloque]) -> None:
    """Desplegable ⚙️: secciones, colores, tamaños, textos y umbrales."""
    movibles = [b for b in bloques if not b.fijo]
    with st.expander("⚙️ PERSONALIZAR PANEL", expanded=False):
        st.caption("Los cambios quedan guardados y se aplican a todos. "
                   "Si algo no te gusta, **Restaurar todo** vuelve a dejarlo como estaba de fábrica.")
        t1, t2, t3, t4 = st.tabs(["📑 Secciones", "🎨 Colores y tamaños", "🚦 Umbrales", "💾 Respaldo"])

        # ---- secciones ------------------------------------------------------
        with t1:
            if not movibles:
                st.info("Esta vista no tiene secciones configurables.")
            else:
                st.caption("Marca qué secciones quieres ver, si vienen abiertas, cómo se llaman "
                           "y en qué orden aparecen (1 = primero).")
                filas = []
                for b in movibles:
                    c = A.seccion(vista, b.id, b.titulo, b.abierto, movibles.index(b))
                    filas.append({"Sección": c["titulo"], "Se ve": c["visible"],
                                  "Abierta": c["abierto"], "Orden": c["orden"], "_id": b.id})
                editado = st.data_editor(
                    pd.DataFrame(filas).sort_values("Orden"),
                    column_config={
                        "Sección": st.column_config.TextColumn("Sección", help="Puedes renombrarla"),
                        "Se ve": st.column_config.CheckboxColumn("Se ve"),
                        "Abierta": st.column_config.CheckboxColumn("Abierta"),
                        "Orden": st.column_config.NumberColumn("Orden", min_value=0, max_value=99, step=1),
                        "_id": None,
                    },
                    hide_index=True, use_container_width=True, key=f"ed_sec_{vista}")
                if st.button("💾 Guardar secciones", key=f"gs_{vista}"):
                    a = A.cargar()
                    for _, r in editado.iterrows():
                        a["secciones"][f"{vista}.{r['_id']}"] = {
                            "visible": bool(r["Se ve"]), "abierto": bool(r["Abierta"]),
                            "orden": int(r["Orden"]), "titulo": str(r["Sección"]).strip()}
                    A.guardar(a)
                    st.rerun()

        # ---- colores y tamaños ---------------------------------------------
        with t2:
            a = A.cargar()
            st.caption("Los colores del texto y de los bordes. La paleta de fábrica está pensada "
                       "para que se distinga bien también en daltonismo; si la cambias, procura "
                       "que el verde y el amarillo no queden parecidos.")
            etiquetas = {"cyan": "Cian (destacados)", "verde": "Verde (cumple)",
                         "amarillo": "Amarillo (en riesgo)", "rojo": "Rojo (bajo)",
                         "morado": "Morado (bonos)", "naranjo": "Naranjo (accesorios)",
                         "fondo": "Fondo", "card": "Fondo de tarjeta", "borde": "Borde de tarjeta",
                         "texto": "Texto", "texto2": "Texto secundario"}
            nuevos = {}
            cols = st.columns(4)
            for i, (k, etq) in enumerate(etiquetas.items()):
                with cols[i % 4]:
                    nuevos[k] = st.color_picker(etq, a["colores"].get(k, cfg.COLORES[k]), key=f"col_{k}")
            c1, c2 = st.columns(2)
            with c1:
                esc = st.slider("Tamaño del texto", 0.85, 1.30, float(a.get("escala_texto", 1.0)), 0.05,
                                help="1,00 es el tamaño normal. Sube a 1,15 si cuesta leer en pantallas grandes.")
            with c2:
                den = st.select_slider("Espacio entre tarjetas", list(A.DENSIDADES.keys()),
                                       value=a.get("densidad", "Normal"))
            if st.button("💾 Guardar colores y tamaños", key="gct"):
                a["colores"], a["escala_texto"], a["densidad"] = nuevos, esc, den
                A.guardar(a)
                st.rerun()

        # ---- umbrales -------------------------------------------------------
        with t3:
            a = A.cargar()
            st.caption("Desde qué punto un número se pinta verde, amarillo o rojo.")
            u1, u2 = st.columns(2)
            with u1:
                uv = st.slider("Verde desde", 0.5, 1.5, float(a.get("umbral_verde", 1.0)), 0.05,
                               format="%.2f", help="1,00 = alcanzó lo que debía llevar al corte.")
            with u2:
                ua = st.slider("Amarillo desde", 0.3, 1.2, float(a.get("umbral_amarillo", 0.8)), 0.05,
                               format="%.2f", help="Bajo este valor se pinta rojo.")
            if ua >= uv:
                st.warning("El amarillo debe empezar antes que el verde. Baja el amarillo o sube el verde.")
            usar_excel = st.checkbox(
                "Usar los umbrales de la hoja CONV-CUMP del Excel para las tablas de semáforos",
                value=bool(a.get("usar_umbrales_excel", True)),
                help="Recomendado: así los semáforos siempre siguen la meta oficial del mes. "
                     "Si lo desmarcas, puedes fijar tus propios mínimos abajo.")
            propios = dict(a.get("umbrales_propios") or {})
            if not usar_excel:
                st.caption("Mínimos propios (deja vacío el que quieras seguir tomando del Excel).")
                base = mov.umbrales if mov is not None else {}
                filas = [{"KPI": n, "_k": k,
                          "Meta (verde)": float(propios.get(k, {}).get("meta", base.get(k, {}).get("meta", 0) or 0)),
                          "Amarillo desde": float(propios.get(k, {}).get("amarillo", base.get(k, {}).get("amarillo", 0) or 0))}
                         for n, k in KPIS_GESTION]
                ed = st.data_editor(pd.DataFrame(filas),
                                    column_config={"KPI": st.column_config.TextColumn(disabled=True),
                                                   "Meta (verde)": st.column_config.NumberColumn(format="%.4f"),
                                                   "Amarillo desde": st.column_config.NumberColumn(format="%.4f"),
                                                   "_k": None},
                                    hide_index=True, use_container_width=True, key="ed_umb")
                propios = {r["_k"]: {"meta": float(r["Meta (verde)"]), "amarillo": float(r["Amarillo desde"])}
                           for _, r in ed.iterrows()}
                st.caption("Los valores van en tanto por uno: 0,26 = 26 %.")
            if st.button("💾 Guardar umbrales", key="gu"):
                a["umbral_verde"], a["umbral_amarillo"] = uv, ua
                a["usar_umbrales_excel"] = usar_excel
                a["umbrales_propios"] = {} if usar_excel else propios
                A.guardar(a)
                st.rerun()

        # ---- respaldo -------------------------------------------------------
        with t4:
            st.caption("En Streamlit Cloud la configuración se borra cuando la app reinicia. "
                       "**Descárgala** después de dejarla como te gusta y vuelve a cargarla si se pierde.")
            r1, r2 = st.columns(2)
            with r1:
                st.download_button("📥 Descargar configuración", A.exportar(),
                                   file_name="ajustes_panel_ctf.json", mime="application/json", key="dl_aj")
            with r2:
                sub = st.file_uploader("Cargar configuración guardada", type=["json"], key="up_aj")
                if sub is not None:
                    try:
                        A.importar(sub.getvalue())
                        st.success("Configuración restaurada.")
                        st.rerun()
                    except Exception as ex:  # noqa: BLE001
                        st.error(f"No se pudo leer: {ex}")
            st.divider()
            if st.checkbox("Confirmo que quiero volver a los valores de fábrica", key="chk_rest"):
                if st.button("♻️ Restaurar todo", key="btn_rest"):
                    A.restaurar()
                    st.rerun()


def fila_ot(pdv: str) -> dict | None:
    """
    Acumulado oficial de la hoja OT# para una tienda ('CTF' para la empresa).

    Es la fuente correcta para los totales por tienda: vienen consolidados en la
    planilla, con su propia ficha y su propio tramo. Devuelve None si el Excel
    del mes no trae la hoja OT#, y el panel cae al consolidado de MOV-FIBRA.
    """
    if str(pdv).upper() == "CTF":
        return dict(mov.ot_total) if mov.ot_total else None
    if mov.ot_tiendas is None or mov.ot_tiendas.empty:
        return None
    f_ = mov.ot_tiendas[mov.ot_tiendas["pdv"].astype(str) == str(pdv)]
    return f_.iloc[0].to_dict() if not f_.empty else None


ORIGEN_OT = "Acumulados oficiales de la hoja <b>OT#</b> del Drive."
ORIGEN_MOV = "Acumulados de la hoja <b>MOV-FIBRA</b> (este Excel no trae la hoja OT#)."


# ===========================================================================
# BLOQUES REUTILIZABLES (los usan Vista Ejecutivo y Vista Tiendas)
# ===========================================================================
def bloque_cabecera(row, pdv_txt: str, sub_pdv: str, titulo_peq: str, nombre_grande: str, minis: list[str] | None,
                    lema: str, f: dict, ultima_fibra: dict | None, clave: str = ""):
    c1, c2, c3, c4 = st.columns([1.25, 2.9, 1.25, 1.25])
    with c1:
        ui.card(f'<div class="mid">🏬 {h(pdv_txt)}</div><div class="sub t-cyan" style="font-weight:800;font-size:1rem">{h(sub_pdv)}</div>'
                f'<div class="hr"></div><div class="h t-cyan">📅 CORTE</div><div class="mid">{fecha_txt(mov.fecha_corte)}</div>', "cyan igual")
    with c2:
        cuerpo = (f'<div class="ancho-total"></div><div class="h">{h(titulo_peq)}</div>'
                  f'<div class="big t-cyan" style="font-size:clamp(1.4rem,2.6vw,2.2rem)">{h(nombre_grande)}</div>')
        if minis:
            cuerpo += grid(minis, 4)
        if lema:
            cuerpo += f'<div class="sub" style="font-size:1.4rem;font-style:italic;color:#e5e7eb">{h(lema)}</div>'
        ui.card(cuerpo, "igual")
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
    conf = M.confianza_proyeccion(row.get("dias_trab"))
    with c3:
        ui.card(f'<div class="h">% REAL A LA FECHA</div><div class="big {col_real}" style="margin:.5rem 0">{pct(f["cump"])}</div>'
                f'{tendencia(clave, "cump_ficha") if clave else ""}'
                f'<div class="mid {col_real}" style="font-size:1.15rem;margin-top:.35rem">TRAMO {f["tramo"]}</div>'
                f'<div class="sub {col_real}"><b>{f["etiqueta"]}</b></div>',
                ("rojo" if col_real == "t-rojo" else ("amarillo" if col_real == "t-amarillo" else "verde")) + " igual")
    with c4:
        ui.card(f'<div class="h">% PROYECCIÓN</div>'
                f'<div class="big {col_proy}" style="margin:.5rem 0">{M.pct_topado(f["proy"], cfg.TOPE_PROYECCION_VISUAL, 2)}</div>'
                f'{tendencia(clave, "proy_pond") if clave else ""}'
                f'<div class="mid {col_proy}" style="font-size:1.15rem;margin-top:.35rem">TRAMO {f["tramo_proy"]}</div>'
                f'<div class="sub {col_proy}"><b>{f["etiqueta_proy"] if f["tramo_proy"] == 0 else "TRAMO " + str(f["tramo_proy"])}</b></div>'
                f'<div class="ref"><span class="{conf["clase"]}">{conf["icono"]} confianza {conf["nivel"]}</span> · {h(conf["texto"])}</div>',
                ("rojo" if col_proy == "t-rojo" else ("amarillo" if col_proy == "t-amarillo" else "verde")) + " igual")


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
       f'<span class="sec">📱 ENTEL – MOVIL</span><span class="pill">📍 AVANCE ESPERADO: {pct(avance, 1)}</span></div>')
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
                                  row.get(f"{k}_cump"), row.get(conv) if conv else None, color, extra_txt,
                                  corte=avance)
    md(f'<div class="prod-grid g7">{html_items}</div>')
    md('<div class="ref">La marca negra sobre cada barra es el avance esperado al corte: '
       'si el color la pasa, el producto va adelantado.</div>')


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
    fp, aviso_fp = M.sanear_tasa(row.get("factor_prod"))
    ti, aviso_ti = M.sanear_tasa(row.get("tasa_inst"))
    cuerpo = '<div class="sec">📶 FIBRA (REAL ENTEL)</div>' + grid([
        celda("Q Validaciones", entero(row.get("q_valid")), f"% Validación {pct(row.get('pct_valid'))}<br>Incorrectas {pct(row.get('valid_inc'))}", True),
        celda("Factibles", entero(row.get("factibles")), f"% Factibles {pct(row.get('pct_fact'))}", True),
        celda("Conv. fibra", pct(row.get("conv_fibra")), "", True),
        celda("Factor de prod.", pct(fp) if fp is not None else "—",
              '<span class="t-amarillo">⚠ revisar</span>' if aviso_fp else "", True,
              color="t-amarillo" if aviso_fp else ""),
        celda("Tasa de instalación", pct(ti) if ti is not None else "—",
              '<span class="t-amarillo">⚠ revisar</span>' if aviso_ti else "", True,
              color="t-amarillo" if aviso_ti else ""),
        celda("Fibra solicitudes", entero(row.get("fib_sol")), f"Pendientes: {entero(row.get('fib_pend'))}", True),
    ], 6)
    avisos = [a for a in (aviso_fp, aviso_ti) if a]
    if avisos:
        cuerpo += ('<div class="ref t-amarillo">⚠ Factor de producción y/o tasa de instalación sobre 100 %. '
                   'Suele ser un cálculo con problema en el Excel (fórmulas #REF! o divisiones con base cero), '
                   'no un resultado real.</div>')
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


def bloque_escuchas(clave: str, pdv: str, titulo: str = "ESCUCHAS"):
    """clave = código CMA_ del ejecutivo, código de tienda, o 'CTF'."""
    ui.seccion("🎧", titulo)
    if esc is None or esc.empty:
        st.info("Carga el Excel **ESCUCHAS ENTEL** (export del Power BI) en *Gestión de archivos* "
                "para ver Escuchas auditadas, Starlink, Latam Pass, Hogar, Fibra y Portabilidad.")
        return
    fila = esc[esc["clave"].astype(str).str.upper() == str(clave).upper()]
    if fila.empty:
        st.info("No hay escuchas registradas para esta selección en el export cargado.")
        return
    r = fila.iloc[0]

    def ref(nivel, filtro_pdv=None):
        f_ = esc[esc["nivel"] == nivel]
        if filtro_pdv is not None:
            f_ = f_[f_["pdv"] == filtro_pdv]
        return f_.iloc[0] if not f_.empty else None

    t = ref("tienda", pdv) if r["nivel"] == "ejecutivo" else None
    canal, ctf = ref("canal"), ref("ctf")

    def refs(col, fmt=lambda x: pct(x, 1)):
        partes = []
        if t is not None:
            partes.append(f"Tienda <span class='t-cyan'>{fmt(t[col])}</span>")
        if canal is not None:
            partes.append(f"Canal <span class='t-cyan'>{fmt(canal[col])}</span>")
        if ctf is not None and r["nivel"] != "ctf":
            partes.append(f"CTF <span class='t-cyan'>{fmt(ctf[col])}</span>")
        return " · ".join(partes)

    cols = st.columns(6)
    with cols[0]:
        ui.card(f'<div class="h">🎧 ESCUCHAS AUDITADAS</div><div class="big t-verde">{entero(r["auditadas"])}</div>'
                f'<div class="sub" style="font-size:.75rem">{refs("auditadas", entero)}</div>', "cyan")
    with cols[1]:
        ui.card(f'<div class="h">🛰️ STARLINK</div><div class="big t-verde">{pct(r["starlink"], 1)}</div>'
                f'<div class="sub" style="font-size:.75rem">{refs("starlink")}</div>', "cyan")
    with cols[2]:
        ui.card(f'<div class="h">✈️ LATAM PASS</div><div class="big t-verde">{pct(r["latam_pass"], 1)}</div>'
                f'<div class="sub" style="font-size:.75rem">{refs("latam_pass")}</div>', "cyan")
    with cols[3]:
        ui.card(f'<div class="h">🏠 HOGAR</div><div class="big t-verde">{pct(r["hogar"], 1)}</div>'
                f'<div class="sub" style="font-size:.75rem">{refs("hogar")}</div>', "cyan")
    with cols[4]:
        ui.card('<div class="h">📡 FIBRA</div>'
                + grid([celda("Calidad", pct(r["fibra_calidad"], 1), color="t-amarillo"),
                        celda("Estabilidad", pct(r["fibra_estabilidad"], 1), color="t-amarillo")], 2)
                + f'<div class="sub" style="margin-top:.3rem;font-size:.75rem">{refs("fibra_calidad")}</div>', "cyan")
    with cols[5]:
        ui.card('<div class="h">📲 PORTABILIDAD</div>'
                + grid([celda("Motivo", pct(r["porta_motivo"], 1), color="t-amarillo"),
                        celda("Objeciones", pct(r["porta_objeciones"], 1), color="t-amarillo"),
                        celda("Urgencia", pct(r["porta_urgencia"], 1), color="t-amarillo")], 3)
                + f'<div class="sub" style="margin-top:.3rem;font-size:.75rem">{refs("porta_motivo")}</div>', "cyan")


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


KPIS_PARES = [("% Real ficha", "cump_ficha", 2), ("Atenciones", "atenciones", 0), ("Conv. móvil", "mov_conv", 1),
              ("Conv. sus", "sus_conv", 1), ("Conv. porta", "porta_conv", 1), ("Conv. fibra", "conv_fibra", 1),
              ("Att seguro", "att_seg", 1), ("Conv. equipos", "eq_conv", 1), ("Conv. acc", "acc_conv", 1),
              ("EPA", "epa", 1)]


def comparacion_pares(row, ej_tienda: pd.DataFrame, ej_ctf: pd.DataFrame, codigo: str):
    """Cómo se ve este ejecutivo al lado de su tienda y de toda la empresa."""
    filas = []
    for etiqueta, k, dec in KPIS_PARES:
        val = v(row.get(k))
        m_t = ej_tienda[k].mean() if k in ej_tienda.columns and not ej_tienda.empty else None
        fmt = (lambda x: entero(x)) if k == "atenciones" else (lambda x: pct(x, dec))
        serie_ctf = pd.to_numeric(ej_ctf[k], errors="coerce").dropna() if k in ej_ctf.columns else pd.Series(dtype=float)
        if len(serie_ctf) > 1:
            puesto = int((serie_ctf > val).sum()) + 1
            pos = f"{puesto} de {len(serie_ctf)}"
            cls = "sem-v" if puesto <= len(serie_ctf) / 3 else ("sem-a" if puesto <= 2 * len(serie_ctf) / 3 else "sem-r")
        else:
            pos, cls = "—", ""
        dif_t = (val - m_t) if m_t is not None and pd.notna(m_t) else None
        factor = 1 if k == "atenciones" else 100
        filas.append([h(etiqueta), fmt(val), fmt(m_t) if m_t is not None else "—",
                      ui.delta(dif_t * factor, "" if k == "atenciones" else " pts",
                               0 if k == "atenciones" else 1) if dif_t is not None else "—",
                      f'<span class="celda-sem rango {cls}">{pos}</span>' if cls else pos,
                      tendencia(codigo, k) or "—"])
    ui.card(ui.tabla(["KPI", "Este ejecutivo", "Prom. tienda", "vs. tienda", "Puesto en CTF", "vs. corte anterior"],
                     filas, izq=1), "cyan")


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
def umbral_de(clave: str) -> dict | None:
    """Umbral vigente de un KPI: el del Excel, o el propio si se configuró uno."""
    a = A.cargar()
    if not a.get("usar_umbrales_excel", True):
        propio = (a.get("umbrales_propios") or {}).get(clave)
        if propio and (propio.get("meta") or propio.get("amarillo")):
            return propio
    return mov.umbrales.get(clave)


def semaforo(valor, clave: str) -> str:
    u = umbral_de(clave)
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
    u = umbral_de("mov_cump") or {"meta": mov.avance_esperado, "amarillo": 0.075}
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
        u = umbral_de(k)
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

    c_ = COLAB.get(codigo)
    hoy = mov.fecha_corte or dt.date.today()
    antig = M.antiguedad(c_["fecha_ingreso"], hoy) if c_ is not None else "Por completar"
    cumple, cuando_cumple = M.cumpleanos(c_["fecha_nacimiento"], hoy) if c_ is not None else ("Por completar", "")
    if c_ is not None and c_["nombre"]:
        nombre = nombre or c_["nombre"]
    minis = [mini("👤 Nombre", h(nombre or "Por completar")),
             mini("⏳ Antigüedad", h(antig)),
             mini("🕒 Jornada", jornada),
             mini("🎂 Cumpleaños", h(cumple) + (f'<div class="t-cyan" style="font-size:.75rem">{h(cuando_cumple)}</div>' if cuando_cumple else ""))]
    rf = M.resumen_fibra_ejecutivo(fib.solicitudes if fib else None, codigo, mov.fecha_corte)
    bloque_cabecera(e, f"PDV {pdv}", tienda, "EJECUTIVO SELECCIONADO", codigo, minis, "", f, rf, clave=codigo)

    prom = ej_tienda.loc[ej_tienda["ejecutivo"] != codigo, "atenciones"]

    def resumen_enviar():
        texto = M.resumen_accionable(e, nombre, tienda, mov.fecha_corte, f, mov.estandares, mov.avance_esperado)
        st.code(texto, language=None)
        st.download_button("📥 Descargar resumen (.txt)", texto.encode("utf-8"),
                           file_name=f"resumen_{codigo}_{fecha_txt(mov.fecha_corte).replace('/', '-')}.txt",
                           mime="text/plain", key="dl_resumen_ej")

    bloques = [
        Bloque("indicadores", "Indicadores", lambda: bloque_indicadores(e, f, prom.mean() if not prom.empty else 0), fijo=True),
        Bloque("prioridades", "🎯 3 PRIORIDADES DEL CORTE", lambda: bloque_prioridades(e), suelto=True),
        Bloque("resumen", "📤 RESUMEN PARA ENVIAR AL EJECUTIVO", resumen_enviar, abierto=False),
        Bloque("movilidad", "📱 ENTEL – MOVIL", lambda: bloque_movilidad(e, avance), suelto=True),
        Bloque("pares", "⚖️ CÓMO VA FRENTE A SUS PARES", lambda: comparacion_pares(e, ej_tienda, ejecutivos, codigo)),
        Bloque("fibra", "📶 FIBRA (REAL ENTEL)", lambda: bloque_fibra(e), suelto=True),
        Bloque("equipos", "📱 EQUIPOS · SEGUROS · ACCESORIOS", lambda: bloque_equipos_seguros_acc(e, avance), suelto=True),
        Bloque("bonos", "💰 BONOS DEL EJECUTIVO", lambda: bloque_bonos(e, jornada), abierto=False),
        Bloque("energia", "⚡ ENERGÍA · PROTECCIÓN · EPA", lambda: bloque_ene_prot_epa(e), abierto=False),
        Bloque("escuchas", "🎧 ESCUCHAS", lambda: bloque_escuchas(codigo, pdv), abierto=False),
        Bloque("encuestas", "🗣️ EPA Y ENCUESTAS", lambda: bloque_epa_encuestas(codigo), abierto=False),
    ]
    render_bloques("ejecutivo", bloques)
    panel_personalizar("ejecutivo", bloques)
    md(f'<div class="foot">Archivo cargado: {h(NOMBRE_ARCHIVO)} · Vista: Ejecutivo · {h(tienda)} · Ejecutivos: {len(ej_tienda)}</div>')


# ===========================================================================
# VISTA 2 · TIENDAS / CTF
# ===========================================================================
def vista_tiendas():
    opciones = ["CTF"] + list(etiqueta_tienda.keys())
    etiquetas = {"CTF": "CTF EMPRESA TOTAL · CTF TECNOLOGIA SPA", **etiqueta_tienda}
    sel = st.selectbox("🏬 Seleccionar tienda / empresa", opciones, format_func=lambda p: etiquetas[p])

    if sel == "CTF":
        row = pd.Series(fila_ot("CTF") or mov.total)
        ej = ejecutivos
        titulo, pdv_txt, sub_pdv, nombre_grande = "EMPRESA TOTAL", "PDV CTF", "CTF EMPRESA TOTAL", "CTF EMPRESA TOTAL"
        escucha_clave, escucha_pdv = "CTF", ""
    else:
        row = pd.Series(fila_ot(sel) or tiendas[tiendas["pdv"] == sel].iloc[0].to_dict())
        ej = ejecutivos[ejecutivos["pdv"] == sel]
        titulo, pdv_txt, sub_pdv, nombre_grande = "TIENDA", f"PDV {sel}", nombre_tienda[sel], nombre_tienda[sel]
        escucha_clave, escucha_pdv = sel, sel

    f = M.ficha(row, mov.pesos)
    avance = avance_calendario(row)

    md(f'<div class="card" style="padding:.6rem 1rem">Vista: <b>{h(nombre_grande)}</b> · Ejecutivos: <b>{len(ej)}</b> · '
       f'Corte: <b>{fecha_txt(mov.fecha_corte)}</b> · {ORIGEN_OT if fila_ot(sel) else ORIGEN_MOV}</div>')
    bloque_cabecera(row, pdv_txt, sub_pdv, titulo, nombre_grande, None, "¡Vamos por más! Cada venta cuenta.", f, None,
                    clave="CTF" if sel == "CTF" else sel)
    bloques = [
        Bloque("indicadores", "Indicadores", lambda: bloque_indicadores(row, f, None), fijo=True),
        Bloque("equipo", "🚦 QUIÉN NECESITA APOYO HOY", lambda: tablero_ejecutivos(ej, f), suelto=True),
        Bloque("movilidad", "📱 ENTEL – MOVIL", lambda: bloque_movilidad(row, avance), suelto=True),
        Bloque("fibra", "📶 FIBRA (REAL ENTEL)", lambda: bloque_fibra(row), suelto=True),
        Bloque("equipos", "📱 EQUIPOS · SEGUROS · ACCESORIOS", lambda: bloque_equipos_seguros_acc(row, avance)),
        Bloque("energia", "⚡ ENERGÍA · PROTECCIÓN · EPA", lambda: bloque_ene_prot_epa(row), abierto=False),
        Bloque("cumplimientos", "👥 CUMPLIMIENTOS DE EJECUTIVOS", lambda: tabla_cumplimientos(ej, avance)),
        Bloque("gestion", "🎯 GESTIÓN DE EJECUTIVOS (conversiones y attach)", lambda: tabla_gestion(ej), abierto=False),
        Bloque("ranking", "🏆 RANKING CTF DE EJECUTIVOS", lambda: tabla_ranking(ej), abierto=False),
        Bloque("winner", "🏆 BONO WINNER", lambda: tabla_bono_winner(ej), abierto=False),
        Bloque("escuchas", "🎧 ESCUCHAS", lambda: bloque_escuchas(escucha_clave, escucha_pdv, f"ESCUCHAS · {nombre_grande}"), abierto=False),
    ]
    render_bloques("tiendas", bloques)
    panel_personalizar("tiendas", bloques)
    md(f'<div class="foot">Archivo cargado: {h(NOMBRE_ARCHIVO)} · Vista: Tiendas / CTF · {h(nombre_grande)}</div>')


def tablero_ejecutivos(ej: pd.DataFrame, f: dict):
    """Quién necesita ayuda hoy: el semáforo por persona, en una sola mirada."""
    if ej.empty:
        return
    filas = []
    for _, r in ej.iterrows():
        fe = M.ficha(r, mov.pesos)
        al = M.alertas(r, mov.estandares, mov.avance_esperado)
        filas.append({"cod": r["ejecutivo"], "nombre": mov.nombres.get(r["ejecutivo"], ""),
                      "cump": fe["cump"], "tramo": fe["tramo"], "alertas": len(al),
                      "prio": M.prioridades(al, 1)})
    filas.sort(key=lambda x: x["cump"])
    # "en riesgo" se mide contra el avance esperado del mes, no contra el 100 %:
    # el día 3 nadie lleva 80 % y marcar a todos en rojo no dice nada.
    corte = mov.avance_esperado or 0.0
    en_riesgo = [x for x in filas if x["cump"] < corte]

    def tarjetas(lista):
        out = '<div class="grid g4" style="margin-top:.5rem">'
        for x in lista:
            rel = (x["cump"] / corte) if corte else None
            col = ui.color_cump(rel)
            borde = {"t-rojo": "#fb7185", "t-amarillo": "#fbbf24", "t-verde": "#4ade80"}.get(col, "#1e3a8a")
            foco = x["prio"][0]["foco"] if x["prio"] else "Sin alertas"
            out += (f'<div class="mini" style="border-color:{borde};text-align:left;padding:.5rem .6rem">'
                    f'<div class="l">{h(x["cod"])}</div>'
                    f'<div class="v {col}" style="font-size:1.15rem">{pct(x["cump"], 1)}</div>'
                    f'<div class="ref" style="text-align:left">Tramo {x["tramo"]} · {x["alertas"]} alertas<br>'
                    f'<b>{h(foco)}</b></div></div>')
        return out + "</div>"

    if en_riesgo:
        intro = (f'<b>{len(en_riesgo)} de {len(filas)}</b> ejecutivos van bajo el avance esperado del mes '
                 f'({pct(corte, 1)}). Estos son los que más apoyo necesitan.')
    else:
        intro = (f'Nadie va bajo el avance esperado del mes ({pct(corte, 1)}). '
                 f'Aun así, estos son los cumplimientos más bajos del equipo.')
    cuerpo = (f'<div class="sec">🚦 QUIÉN NECESITA APOYO HOY</div>'
              f'<div class="ref" style="text-align:left">{intro}</div>' + tarjetas(filas[:8]))
    ui.card(cuerpo, "cyan")
    if len(filas) > 8:
        with st.expander(f"Ver los {len(filas)} ejecutivos", expanded=False):
            ui.card(tarjetas(filas[8:]), "cyan")


# ===========================================================================
# VISTA 3 · JEFE DE TIENDA
# ===========================================================================
CLAVE_SESION = "jefe_desbloqueado"


def clave_configurada() -> str:
    """
    Contraseña de la vista Jefe de Tienda.

    Se lee de los *secrets* de Streamlit, nunca del código: el repositorio es
    público, así que una clave escrita aquí quedaría a la vista de cualquiera.
    En Streamlit Cloud: Settings → Secrets → clave_jefes = "loquesea".
    En local: crear .streamlit/secrets.toml con esa misma línea.
    """
    try:
        return str(st.secrets.get("clave_jefes", "") or "")
    except Exception:  # noqa: BLE001  no hay secrets.toml en local
        return ""


def bloqueo_jefe() -> bool:
    """Devuelve True si la vista está desbloqueada."""
    if st.session_state.get(CLAVE_SESION):
        return True
    clave = clave_configurada()
    if not clave:
        ui.card('<div class="sec">🔒 VISTA RESERVADA</div>'
                '<div class="sub" style="text-align:left">Esta vista está protegida y todavía no tiene contraseña configurada.<br><br>'
                '<b>Para activarla:</b><br>'
                '1. Entra a <b>share.streamlit.io</b> → tu app → <b>Settings</b> → <b>Secrets</b>.<br>'
                '2. Escribe una línea: <code>clave_jefes = "la-clave-que-elijas"</code> y guarda.<br>'
                '3. La app se reinicia sola y aquí aparecerá el cuadro para escribirla.<br><br>'
                'Para probar en tu computador, crea el archivo <code>.streamlit/secrets.toml</code> '
                'en la carpeta del proyecto con esa misma línea. Ese archivo está excluido del '
                'repositorio, así que la clave nunca se sube a GitHub.</div>', "amarillo")
        return False

    ui.card('<div class="sec">🔒 VISTA RESERVADA · JEFE DE TIENDA</div>'
            '<div class="sub">Esta vista muestra los acumulados por tienda y el detalle de cada ejecutivo. '
            'Escribe la contraseña para entrar.</div>', "cyan")
    c1, c2 = st.columns([2, 1])
    with c1:
        ingresada = st.text_input("Contraseña", type="password", key="clave_jefe_input",
                                  label_visibility="collapsed", placeholder="Contraseña")
    with c2:
        entrar = st.button("🔓 Entrar", key="btn_jefe")
    if entrar or ingresada:
        if ingresada == clave:
            st.session_state[CLAVE_SESION] = True
            st.rerun()
        elif entrar:
            st.error("Contraseña incorrecta.")
    return False


def vista_jefe():
    if not bloqueo_jefe():
        return
    b1, b2 = st.columns([3, 1])
    with b2:
        if st.button("🔒 Bloquear vista", key="btn_bloquear"):
            st.session_state[CLAVE_SESION] = False
            st.rerun()
    with b1:
        pdv = st.selectbox("🏬 Tienda", list(etiqueta_tienda.keys()), format_func=lambda p: etiqueta_tienda[p])
    ot = fila_ot(pdv)
    t = pd.Series(ot) if ot else tiendas[tiendas["pdv"] == pdv].iloc[0]
    ej = ejecutivos[ejecutivos["pdv"] == pdv]
    tienda = nombre_tienda.get(pdv, "")
    avance = avance_calendario(t)
    ft = M.ficha(t, mov.pesos)

    md(f'<div class="card" style="padding:.6rem 1rem">Tienda: <b>{h(tienda)}</b> · PDV {h(pdv)} · Ejecutivos activos: <b>{len(ej)}</b> · '
       f'Corte: <b>{fecha_txt(mov.fecha_corte)}</b> · {ORIGEN_OT if ot else ORIGEN_MOV}</div>')

    # --- acumulado oficial de la tienda -------------------------------------
    col_r = ui.color_cump(ft["cump"])
    col_p = ui.color_cump(ft["proy"])
    conf = M.confianza_proyeccion(t.get("dias_trab"))
    k = st.columns(6)
    tarjetas = [("📊 % Real tienda", pct(ft["cump"]), f'Tramo {ft["tramo"]} · {ft["etiqueta"]}', col_r),
                ("🚀 % Proyección", M.pct_topado(ft["proy"], cfg.TOPE_PROYECCION_VISUAL, 2),
                 f'{conf["icono"]} confianza {conf["nivel"]}', col_p),
                ("👤 Atenciones", entero(t.get("atenciones")), "Acumulado de la tienda", "t-cyan"),
                ("📅 Días restantes", entero(t.get("dias_rest")), "Del periodo", "t-cyan"),
                ("📱 Cump. móvil", pct(t.get("mov_cump"), 1), f'Conv. {pct(t.get("mov_conv"), 1)}', ui.color_cump(v(t.get("mov_cump")) / max(avance, 1e-9))),
                ("📶 Cump. fibra", pct(t.get("fib_cump"), 1), f'Conv. {pct(t.get("conv_fibra"), 1)}', ui.color_cump(v(t.get("fib_cump")) / max(avance, 1e-9)))]
    for col, (tt, val, sub, cl) in zip(k, tarjetas):
        with col:
            ui.kpi(tt, val, sub, cl, "")
    def tabla_equipo():
        filas = []
        for _, r in ej.sort_values("cump_ficha", ascending=False).iterrows():
            fr = M.ficha(r, mov.pesos)
            al = M.alertas(r, mov.estandares, mov.avance_esperado)
            filas.append([h(r["ejecutivo"]), h(mov.nombres.get(r["ejecutivo"], "")), entero(r["atenciones"]),
                          f'<span class="{ui.color_cump(fr["cump"])}">{pct(fr["cump"])}</span>', str(fr["tramo"]),
                          f'<span class="{ui.color_cump(fr["proy"])}">{M.pct_topado(fr["proy"], cfg.TOPE_PROYECCION_VISUAL, 2)}</span>',
                          f"{entero(r['mov_real'])}/{M.ceil_pos(deben(r, 'mov_meta', avance))}",
                          f"{entero(r['porta_real'])}/{M.ceil_pos(deben(r, 'porta_meta', avance))}",
                          f"{entero(r['fib_real'])}/{M.ceil_pos(deben(r, 'fib_meta', avance))}",
                          f"{entero(r['seg_real'])}/{M.ceil_pos(deben(r, 'seg_meta', avance))}",
                          pct(r["eq_cump"]), pct(r["epa"], 0),
                          f'<span class="{"t-rojo" if len(al) >= 8 else "t-amarillo" if len(al) >= 4 else "t-verde"}">{len(al)}</span>'])
        ui.card(ui.tabla(["Ejecutivo", "Nombre", "Atenc.", "% Real", "Tramo", "% Proy.", "Móvil / corte",
                          "Porta / corte", "Fibra / corte", "Seg. / corte", "Cump. eq.", "EPA", "Alertas"],
                         filas, izq=2), "cyan")

    def prioridades_equipo():
        cols = st.columns(3)
        for i, (_, r) in enumerate(ej.iterrows()):
            with cols[i % 3]:
                prios = M.prioridades(M.alertas(r, mov.estandares, mov.avance_esperado), 3)
                cuerpo = f'<div class="sec" style="font-size:1.1rem">{h(r["ejecutivo"])}</div>'
                for j, pr in enumerate(prios, 1):
                    cuerpo += f'<div class="prio"><div class="k">PRIORIDAD {j} · {h(pr["foco"])}</div><div class="d">{h(pr["texto"])}</div></div>'
                if not prios:
                    cuerpo += '<div class="sub t-verde">Sin alertas.</div>'
                ui.card(cuerpo, "rosa")

    def resumen_tienda():
        partes = []
        for _, r in ej.sort_values("cump_ficha").iterrows():
            fr = M.ficha(r, mov.pesos)
            partes.append(M.resumen_accionable(r, mov.nombres.get(r["ejecutivo"], ""), tienda,
                                               mov.fecha_corte, fr, mov.estandares, mov.avance_esperado))
        texto = ("\n\n" + "-" * 60 + "\n\n").join(partes)
        st.download_button("📥 Descargar resumen de la tienda (.txt)", texto.encode("utf-8"),
                           file_name=f"resumen_{pdv}_{fecha_txt(mov.fecha_corte).replace('/', '-')}.txt",
                           mime="text/plain", key="dl_resumen_tienda")
        st.code(texto[:4000] + ("\n…" if len(texto) > 4000 else ""), language=None)

    bloques = [
        Bloque("equipo", "👥 EJECUTIVOS DE LA TIENDA", tabla_equipo),
        Bloque("prioridades", "🎯 PRIORIDADES POR EJECUTIVO", prioridades_equipo),
        Bloque("resumen", "📤 RESUMEN DE LA TIENDA PARA ENVIAR", resumen_tienda, abierto=False),
        Bloque("movilidad", "📱 ENTEL – MOVIL", lambda: bloque_movilidad(t, avance), suelto=True),
        Bloque("fibra", "📶 FIBRA (REAL ENTEL)", lambda: bloque_fibra(t), suelto=True),
        Bloque("equipos", "📱 EQUIPOS · SEGUROS · ACCESORIOS", lambda: bloque_equipos_seguros_acc(t, avance), abierto=False),
        Bloque("energia", "⚡ ENERGÍA · PROTECCIÓN · EPA", lambda: bloque_ene_prot_epa(t), abierto=False),
    ]
    render_bloques("jefe", bloques)
    panel_personalizar("jefe", bloques)
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
             ("🚀 Proyección", M.pct_topado(proy, cfg.TOPE_PROYECCION_VISUAL), "Proyección de cierre", ui.color_cump(proy)),
             ("🕐 Deben llevar", str(M.ceil_pos(deben_)), "Instaladas al corte", "t-cyan"),
             ("🔧 Tasa instalación", M.pct_topado(tasa, cfg.TOPE_TASA_VISUAL), "Instaladas / órdenes", ui.color_cump(tasa))]
    for col, (t, val, sub, cl) in zip(c, datos):
        with col:
            ui.kpi(t, val, sub, cl, "")

    conf = M.confianza_proyeccion(fila_ref.get("dias_trab"))
    md(f'<div class="ref"><span class="{conf["clase"]}">{conf["icono"]} Confianza {conf["nivel"]}</span> · {h(conf["texto"])} '
       f'Las proyecciones sobre {pct(cfg.TOPE_PROYECCION_VISUAL, 0)} y las tasas sobre 100 % se muestran topadas: '
       f'suelen venir de una base muy chica o de un cálculo con problema en el Excel.</div>')

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
        ti_txt = M.pct_topado(ti, cfg.TOPE_TASA_VISUAL, 1) + (" ⚠" if ti > cfg.TOPE_TASA_VISUAL * 1.05 else "")
        filas.append([h(cod), h(nombre_tienda.get(r["pdv"], r["pdv"])), entero(m_), entero(rn), entero(ra), entero(tot),
                      f'<span class="celda-sem {sem_c}">{pct(cu, 0)}</span>',
                      f'<span class="celda-sem {sem_p}">{M.pct_topado(pr, cfg.TOPE_PROYECCION_VISUAL, 0)}</span>',
                      str(de), entero(r.get("FIBRA PEND. SEPT")), entero(r.get("PEND. OCT")),
                      f'<span class="celda-sem {"sem-v" if 0.75 <= ti <= cfg.TOPE_TASA_VISUAL * 1.05 else ("sem-a" if ti >= 0.4 else "sem-r")}">{ti_txt}</span>',
                      f'<span class="celda-sem {"sem-v" if va >= 0.85 else ("sem-a" if va >= 0.7 else "sem-r")}">{pct(va, 1)}</span>'])
    ui.card(ui.tabla(["Ejecutivo", "Tienda", "Meta", "Real", "Afinidad", "Total", "Cump.", "Proy.", "Deben",
                      "Pend. sept.", "Pend. oct.", "Tasa inst.", "Valid."], filas, izq=2), "cyan")

    def evolutivo():
        ref = fib.fecha_actualizacion or mov.fecha_corte
        if s.empty or not ref:
            st.info("Sin solicitudes en el periodo.")
            return
        dias = [dt.date(ref.year, ref.month, d) for d in range(1, ref.day + 1)]
        filas = []
        for cod in sorted(s["ejecutivo"].unique()):
            ss_ = s[s["ejecutivo"] == cod]
            fechas = [f_ for f_ in ss_["fecha_solicitud"] if isinstance(f_, dt.date) and pd.notna(f_)]
            ultima = max(fechas) if fechas else None
            sin = max(0, (ref - ultima).days) if ultima else None
            por_dia = [int((ss_["fecha_solicitud"] == d).sum()) for d in dias]
            celdas = [f'<span class="celda-sem {"sem-v" if n >= 3 else ("sem-a" if n >= 1 else "")}">{n or ""}</span>' for n in por_dia]
            filas.append([h(ss_.iloc[0]["pdv"]), h(cod), fecha_txt(ultima),
                          str(sin) if sin is not None else "—", str(sum(por_dia))] + celdas)
        ui.card(ui.tabla(["PDV", "Ejecutivo", "Última solicitud", "Días sin solicitud", "Total"]
                         + [d.strftime("%d/%m") for d in dias], filas, izq=2), "cyan")

    def agenda():
        st.caption(f"Tienda seleccionada: {etiquetas[sel]}. Filtra el periodo para revisar qué se instalará "
                   f"y el estado actual de cada solicitud.")
        f1, f2 = st.columns([1, 2])
        with f1:
            campo = st.selectbox("📅 Filtrar según", ["Fecha de instalación", "Fecha de solicitud"], key="fibra_campo")
        col_f = "fecha_instalacion" if campo.startswith("Fecha de inst") else "fecha_solicitud"
        fechas_validas = [f_ for f_ in s[col_f] if isinstance(f_, dt.date) and pd.notna(f_)] if not s.empty else []
        with f2:
            rango = st.date_input("📆 Rango de fechas", value=(min(fechas_validas), max(fechas_validas)),
                                  key="fibra_rango") if fechas_validas else None
        estados = st.multiselect("📌 Estado de las solicitudes", ESTATUS_ORDEN,
                                 default=[e_ for e_ in ESTATUS_ORDEN if e_ in set(s["estatus"].dropna())],
                                 key="fibra_estados")
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
        if ss.empty:
            return
        g1, g2 = st.columns(2)
        with g1:
            st.caption("Carga de instalaciones por día")
            por_dia = ss.dropna(subset=[col_f]).groupby(col_f).size()
            if not por_dia.empty:
                por_dia.index = [f_.strftime("%d/%m") for f_ in por_dia.index]
                st.bar_chart(por_dia.rename("órdenes"), color=A.colores()["cyan"])
        with g2:
            st.caption("Distribución por estado")
            st.bar_chart(ss["estatus"].value_counts(), color=A.colores()["cyan"])
        st.caption("Detalle de solicitudes")
        cols = ["id", "pdv", "ejecutivo", "fecha_solicitud", "fecha_instalacion", "estado", "estatus",
                "intentos", "reagendamientos", "contratista", "comuna", "motivo"]
        vis = ss[[c_ for c_ in cols if c_ in ss.columns]].copy()
        vis["pdv"] = vis["pdv"].map(lambda pp: nombre_tienda.get(pp, pp))
        vis.columns = ["ID", "Tienda", "Nombre ejecutivo", "Fecha solicitud", "Fecha instalación", "Estado", "Estatus",
                       "Intentos", "Reagendamientos", "Contratista", "Comuna", "Motivo"][:len(vis.columns)]
        vis = vis.fillna("").astype(str).replace({"None": "", "NaT": "", "nan": ""})
        st.dataframe(vis, use_container_width=True, hide_index=True)
        st.download_button("📥 Descargar agenda filtrada (CSV)", vis.to_csv(index=False).encode("utf-8-sig"),
                           file_name=f"agenda_fibra_{fecha_txt(mov.fecha_corte).replace('/', '-')}.csv", mime="text/csv")

    def comparativo():
        filas = []
        for pdv_, nom in nombre_tienda.items():
            sp = sol[sol["pdv"] == pdv_] if not sol.empty else pd.DataFrame()
            er = res[(res["es_ejecutivo"]) & (res["pdv"] == pdv_)]
            m_, r_ = er["meta_fibra"].fillna(0).sum(), er["real_fibra"].fillna(0).sum()
            cu = r_ / m_ if m_ else 0.0
            i_ = int((sp["estatus"] == "INSTALADA").sum()) if len(sp) else 0
            filas.append([h(nom), str(len(sp)), str(i_),
                          str(int((sp["estatus"] == "CANCELADO").sum()) if len(sp) else 0),
                          str(int(sp["estatus"].isin(["AGENDADA", "EN INSTALACIÓN", "REPROGRAMADA"]).sum()) if len(sp) else 0),
                          str(int((sp["estatus"] == "RECONTRATADA").sum()) if len(sp) else 0), entero(m_), entero(r_),
                          f'<span class="{ui.color_cump(cu / max(avance, 1e-9))}">{pct(cu, 1)}</span>',
                          f'<span class="{ui.color_cump(i_ / len(sp) if len(sp) else 0)}">{pct(i_ / len(sp) if len(sp) else 0, 1)}</span>'])
        ui.card(ui.tabla(["Tienda", "Órdenes", "Instaladas", "Canceladas", "En progreso", "Recontratadas",
                          "Meta", "Real", "Cumplimiento", "Tasa instalación"], filas), "cyan")

    bloques = [
        Bloque("evolutivo", "📅 EVOLUTIVO DIARIO DE SOLICITUDES", evolutivo, abierto=False),
        Bloque("reagenda", "🔁 REAGENDAMIENTOS", lambda: bloque_reagendamientos(s), abierto=False),
        Bloque("agenda", "📆 AGENDA Y ESTADO DE INSTALACIONES", agenda),
        Bloque("cancelaciones", "❌ ANÁLISIS DE CANCELACIONES", lambda: bloque_cancelaciones(s), abierto=False),
        Bloque("comparativo", "🏬 COMPARATIVO DE TIENDAS", comparativo),
    ]
    render_bloques("fibra_tiendas", bloques)
    panel_personalizar("fibra_tiendas", bloques)
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
    conf = M.confianza_proyeccion(e.get("dias_trab"))

    # ---- 1. ¿Va bien con la meta? ------------------------------------------
    ui.seccion("🎯", "META DEL MES", "cuánto falta para cerrar")
    c = st.columns(6)
    datos = [("🎯 Meta", entero(meta), "Instalaciones del mes", "t-cyan"),
             ("✅ Lleva", entero(real), "Instaladas válidas", "t-verde"),
             ("📉 Faltan", entero(max(0, meta - real)), "Para llegar a meta", "t-rojo"),
             ("🕐 Debe llevar hoy", str(M.ceil_pos(e.get("fib_deben"))), "Según el avance del corte", "t-cyan"),
             ("📊 Cumplimiento", pct(cump, 1), "Real / meta", ui.color_cump(cump / max(avance, 1e-9))),
             ("🚀 Proyección", M.pct_topado(proy, cfg.TOPE_PROYECCION_VISUAL),
              f'{conf["icono"]} confianza {conf["nivel"]}', ui.color_cump(proy))]
    for col, (t, val, sub, cl) in zip(c, datos):
        with col:
            ui.kpi(t, val, sub, cl, "")
    atraso = M.ceil_pos(e.get("fib_deben")) - real
    if atraso > 0:
        md(f'<div class="card rojo" style="padding:.55rem 1rem"><b class="t-rojo">▼ Va {M.entero(atraso)} instalación(es) '
           f'bajo el corte.</b> <span class="t-gris">Al ritmo de hoy cierra el mes en '
           f'{M.pct_topado(proy, cfg.TOPE_PROYECCION_VISUAL)} de la meta.</span></div>')
    else:
        md('<div class="card verde" style="padding:.55rem 1rem"><b class="t-verde">▲ Va al día o por sobre el corte.</b></div>')

    def donde_se_pierden():
        c_ = st.columns(5)
        for col, (t, val, sub) in zip(c_, [("📋 Solicitudes", entero(r.get("sol_ok")), "Órdenes ingresadas"),
                                           ("🟡 Pendientes", entero(r.get("FIBRA PEND. SEPT")), "Del mes en curso"),
                                           ("❌ Rechazos", entero(r.get("rechazo")), "No siguieron"),
                                           ("🔁 Recontratadas", entero(r.get("recont")), "Volvieron a contratar"),
                                           ("📅 Pend. próx. mes", entero(r.get("PEND. OCT")), "Quedan para después")]):
            with col:
                ui.kpi(t, val, sub, "t-cyan", "")

    def detalle():
        if s.empty:
            st.info("Este ejecutivo no tiene órdenes registradas en el periodo.")
            return
        cols = ["id", "fecha_solicitud", "fecha_instalacion", "estado", "estatus", "tipo_rechazo", "motivo",
                "intentos", "reagendamientos", "contratista", "comuna"]
        vis = s[[c_ for c_ in cols if c_ in s.columns]].copy()
        vis.columns = ["ID", "Fecha de solicitud", "Fecha de instalación", "Estado", "Estatus", "Tipo de rechazo",
                       "Motivo", "Intentos", "Reagendamientos", "Contratista", "Comuna"][:len(vis.columns)]
        st.dataframe(vis.fillna("").astype(str).replace({"None": "", "NaT": "", "nan": ""}),
                     use_container_width=True, hide_index=True)

    bloques = [
        Bloque("ordenes", "📦 SUS ÓRDENES", lambda: bloque_ordenes(s)),
        Bloque("perdidas", "🔎 DÓNDE SE PIERDEN", donde_se_pierden),
        Bloque("reagenda", "🔁 REAGENDAMIENTOS", lambda: bloque_reagendamientos(s), abierto=False),
        Bloque("cancelaciones", "❌ ANÁLISIS DE CANCELACIONES", lambda: bloque_cancelaciones(s, con_tienda=False), abierto=False),
        Bloque("detalle", "📋 DETALLE DE ÓRDENES", detalle, abierto=False),
    ]
    render_bloques("fibra_ejecutivos", bloques)
    panel_personalizar("fibra_ejecutivos", bloques)
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
