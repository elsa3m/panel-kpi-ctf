"""Ficha PDF del ejecutivo (reportlab)."""
from __future__ import annotations

import io

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .metrics import entero, fecha_txt, pct, pesos, v


def ficha_pdf(e: dict, nombre: str, tienda: str, fecha_corte, f: dict, bonos: dict, prios: list[dict]) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=14 * mm, rightMargin=14 * mm, topMargin=12 * mm, bottomMargin=12 * mm)
    st = getSampleStyleSheet()
    H = ParagraphStyle("H", parent=st["Title"], fontSize=18, spaceAfter=4)
    S = ParagraphStyle("S", parent=st["Normal"], fontSize=9, textColor=colors.HexColor("#334155"))
    B = ParagraphStyle("B", parent=st["Heading3"], fontSize=11, spaceBefore=8, spaceAfter=3, textColor=colors.HexColor("#0e5aa7"))

    def tabla(datos, anchos=None):
        t = Table(datos, colWidths=anchos)
        t.setStyle(TableStyle([
            ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 8.5),
            ("FONT", (0, 1), (-1, -1), "Helvetica", 8.5),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#dbeafe")),
            ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#94a3b8")),
            ("ALIGN", (1, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        return t

    el = [Paragraph("FICHA KPI EJECUTIVO · CTF", H),
          Paragraph(f"<b>{e.get('ejecutivo','')}</b> · {nombre} · {tienda} (PDV {e.get('pdv','')}) · Corte: {fecha_txt(fecha_corte)}", S),
          Spacer(1, 6)]

    el.append(Paragraph("Resumen ficha", B))
    el.append(tabla([
        ["% Real a la fecha", "Tramo", "% Proyección", "Tramo proy.", "Atenciones", "Días restantes"],
        [pct(f["cump"]), str(f["tramo"]), pct(f["proy"]), str(f["tramo_proy"]), entero(e.get("atenciones")), entero(e.get("dias_rest"))],
    ]))

    el.append(Paragraph("Entel – Movilidad", B))
    filas = [["Producto", "Meta", "Real", "Faltan", "Cumplimiento", "Conv."]]
    for nom, m, r, fa, c, cv in [
        ("Total móvil", "mov_meta", "mov_real", "mov_falta", "mov_cump", "mov_conv"),
        ("Suscripción", "sus_meta", "sus_real", "sus_falta", "sus_cump", "sus_conv"),
        ("Migraciones", "mis_meta", "mis_real", "mis_falta", "mis_cump", None),
        ("1ra línea", "l1_meta", "l1_real", "l1_falta", "l1_cump", None),
        ("2da línea", "l2_meta", "l2_real", "l2_falta", "l2_cump", None),
        ("Portabilidad", "porta_meta", "porta_real", "porta_falta", "porta_cump", "porta_conv"),
        ("Fibra", "fib_meta", "fib_real", "fib_falta", "fib_cump", "conv_fibra"),
    ]:
        filas.append([nom, entero(e.get(m)), entero(e.get(r)), entero(e.get(fa)), pct(e.get(c)), pct(e.get(cv), 1) if cv else "—"])
    el.append(tabla(filas))

    el.append(Paragraph("Equipos · Seguros · Accesorios", B))
    el.append(tabla([
        ["", "Meta", "Real", "Falta", "Cumplimiento", "Conv. / Attach"],
        ["$ Equipos", pesos(e.get("eq_meta")), pesos(e.get("eq_real")), pesos(e.get("eq_falta")), pct(e.get("eq_cump")), pct(e.get("eq_conv"), 1)],
        ["Seguros (Q)", entero(e.get("seg_meta")), entero(e.get("seg_real")), entero(e.get("seg_falta")), pct(e.get("seg_cump")), pct(e.get("att_seg"), 1)],
        ["$ Accesorios", pesos(e.get("acc_meta")), pesos(e.get("acc_real")), pesos(e.get("acc_falta")), pct(e.get("acc_cump")), pct(e.get("acc_conv"), 1)],
        ["Energía", "—", pesos(e.get("ene_usd")), "—", "—", pct(e.get("ene_att"), 1)],
        ["Protección", "—", pesos(e.get("prot_usd")), "—", "—", pct(e.get("prot_att"), 1)],
        ["EPA", pct(e.get("epa_meta"), 0), pct(e.get("epa"), 1), "—", "—", "—"],
    ]))

    el.append(Paragraph("Bonos", B))
    bf, bp, bw = bonos["foco"], bonos["porta"], bonos["winner"]
    el.append(tabla([
        ["Bono", "Meta / Regla", "Lleva", "Cumplimiento", "Estado", "Monto"],
        ["Portabilidad", entero(bp["meta"]), entero(bp["real"]), pct(bp["cump"], 1), "GANA" if bp["gana"] else "NO GANA", pesos(bp["monto"])],
        ["Foco", "50 % susc. + 50 % fibra", "—", pct(bf["pct"]), bf["estado"], pesos(bf["monto"])],
        ["Winner", "Att seguro / ene-prot / TV", "—", pct(bw["cump"], 1), "GANA" if bw["gana"] else "NO GANA", pesos(bw["monto"])],
    ]))

    if prios:
        el.append(Paragraph("Prioridades del corte", B))
        for i, p in enumerate(prios, 1):
            el.append(Paragraph(f"<b>{i}. {p['foco']}</b> — {p['texto']}", S))

    doc.build(el)
    return buf.getvalue()
