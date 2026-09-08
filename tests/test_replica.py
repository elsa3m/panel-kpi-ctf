"""
Prueba de regresión: compara los KPI calculados por la app con los valores que
mostraba el panel original (gestion-ctf.streamlit.app) para CMA_EMONTILVA al
corte 03/09/2026.

Ejecutar:  python -m pytest tests/ -q      (o simplemente  python tests/test_replica.py)
Requiere data/mov_fibra.xlsx (DRIVE TIENDAS SEPTIEMBRE 2026 CTF (1RA).xlsx).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from kpi import metrics as M  # noqa: E402
from kpi.loader import cargar_mov_fibra  # noqa: E402

DATA = Path(__file__).resolve().parent.parent / "data" / "mov_fibra.xlsx"

# valor esperado (leído del panel original) -> (clave, tolerancia)
ESPERADO = {
    "atenciones": (42, 0), "dias_rest": (21, 0),
    "cump_ficha": (0.2472, 0.0001), "proy_pond": (0.7804, 0.0001), "tramo": (0, 0),
    "mov_real": (11, 0), "mov_meta": (91.14, 0.5), "mov_cump": (0.1207, 0.0001), "mov_conv": (0.262, 0.001),
    "sus_real": (8, 0), "sus_meta": (76.44, 0.5), "sus_cump": (0.1047, 0.0001), "sus_conv": (0.190, 0.001),
    "l1_real": (2, 0), "l1_cump": (0.1152, 0.0001), "l2_real": (5, 0), "l2_cump": (0.1483, 0.0001),
    "porta_real": (1, 0), "fib_real": (0, 0), "fib_meta": (14, 0), "conv_fibra": (0.056, 0.001),
    "bp_meta": (36, 0), "bp_real": (1, 0), "bp_cump": (0.028, 0.001), "bp_bono": (0, 0),
    "bf_pct": (0.052, 0.0005), "bw_att_seg": (0.182, 0.001), "bw_att_ene_prot": (0.192, 0.001), "bw_cump": (0.378, 0.001),
    "q_valid": (35, 0), "pct_valid": (0.8333, 0.0001), "factibles": (18, 0), "fib_sol": (1, 0), "fib_pend": (0, 0),
    "eq_cump": (0.2171, 0.0001), "eq_conv": (0.310, 0.001), "eq_q": (13, 0), "eq_meta_q": (63, 0.5), "att_eq_linea": (0.375, 0.001),
    "eq_meta": (29956961, 1), "eq_real": (6504093, 1), "eq_falta": (23452868, 1),
    "seg_meta": (22, 0), "seg_real": (2, 0), "seg_falta": (20, 0), "seg_cump": (0.0909, 0.0001), "att_seg": (0.182, 0.001),
    "acc_meta": (3059013, 1), "acc_real": (431882, 1),
    "ene_usd": (86521, 1), "ene_q": (4, 0), "ene_conv": (0.0952, 0.0001), "ene_att": (0.3077, 0.0001),
    "prot_usd": (9235, 1), "prot_q": (1, 0), "prot_conv": (0.0238, 0.0001), "prot_att": (0.0769, 0.0001),
    "epa_meta": (0.86, 0), "epa": (1.0, 0.001),
}


def test_emontilva():
    d = cargar_mov_fibra(DATA)
    e = d.ejecutivos[d.ejecutivos["ejecutivo"] == "CMA_EMONTILVA"].iloc[0]
    errores = []
    for k, (esp, tol) in ESPERADO.items():
        real = M.v(e[k])
        if abs(real - esp) > tol + 1e-9:
            errores.append(f"{k}: esperado {esp}, obtenido {real}")
    assert not errores, "\n".join(errores)
    f = M.ficha(e, d.pesos)
    assert f["tramo"] == 0 and f["etiqueta"] == "BAJO CUMPLIMIENTO"
    prios = M.prioridades(M.alertas(e, d.estandares, d.avance_esperado))
    assert [p["foco"] for p in prios] == ["MOVIL", "FIBRA", "SEGUROS"]
    assert len(d.ejecutivos[(d.ejecutivos["pdv"] == "5003") & d.ejecutivos["activo"]]) == 3


if __name__ == "__main__":
    test_emontilva()
    print("OK: todos los KPI de CMA_EMONTILVA coinciden con el panel original.")
