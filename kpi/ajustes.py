"""
Ajustes que la usuaria puede cambiar desde el propio panel, sin tocar código.

Todo lo que se elige en el desplegable "⚙️ PERSONALIZAR PANEL" se guarda aquí,
en data/ajustes.json. Como en Streamlit Cloud la carpeta data/ se vacía cuando
la app reinicia, el panel ofrece descargar y volver a cargar este archivo.

Qué se puede cambiar:
  * secciones — cuáles se ven, en qué orden, abiertas o cerradas, y su título
  * colores   — la paleta del panel
  * tamaños   — escala del texto y qué tan apretadas van las tarjetas
  * umbrales  — desde qué porcentaje algo se pinta verde, amarillo o rojo
"""
from __future__ import annotations

import copy
import json

from .config import DATA_DIR, COLORES

RUTA = DATA_DIR / "ajustes.json"

# ---------------------------------------------------------------------------
# valores de fábrica
# ---------------------------------------------------------------------------
DENSIDADES = {
    "Compacto": {"card_pad": ".5rem .65rem", "card_gap": ".4rem", "grid_gap": ".45rem"},
    "Normal": {"card_pad": ".7rem .85rem", "card_gap": ".55rem", "grid_gap": ".6rem"},
    "Amplio": {"card_pad": "1rem 1.2rem", "card_gap": ".9rem", "grid_gap": ".85rem"},
}

DEFECTO = {
    "colores": dict(COLORES),
    "escala_texto": 1.0,          # 0.85 a 1.30
    "densidad": "Normal",
    "umbral_verde": 1.00,         # cumplimiento relativo desde el que se pinta verde
    "umbral_amarillo": 0.80,      # y desde el que se pinta amarillo
    "usar_umbrales_excel": True,  # semáforos de las tablas: hoja CONV-CUMP
    "umbrales_propios": {},       # clave KPI -> {"meta": x, "amarillo": y}
    "secciones": {},              # "vista.bloque" -> {"visible","abierto","orden","titulo"}
}


def _leer() -> dict:
    if not RUTA.exists():
        return copy.deepcopy(DEFECTO)
    try:
        guardado = json.loads(RUTA.read_text(encoding="utf-8"))
    except Exception:                       # noqa: BLE001  archivo corrupto
        return copy.deepcopy(DEFECTO)
    base = copy.deepcopy(DEFECTO)
    for k, val in guardado.items():
        if k in base and isinstance(base[k], dict) and isinstance(val, dict):
            base[k].update(val)
        elif k in base:
            base[k] = val
    return base


_cache: dict | None = None


def cargar() -> dict:
    """Ajustes actuales (se leen una vez por ejecución)."""
    global _cache
    if _cache is None:
        _cache = _leer()
    return _cache


def guardar(nuevos: dict) -> None:
    global _cache
    _cache = nuevos
    RUTA.parent.mkdir(exist_ok=True)
    RUTA.write_text(json.dumps(nuevos, indent=2, ensure_ascii=False), encoding="utf-8")


def restaurar() -> dict:
    """Vuelve a los valores de fábrica."""
    global _cache
    _cache = copy.deepcopy(DEFECTO)
    RUTA.unlink(missing_ok=True)
    return _cache


def exportar() -> bytes:
    return json.dumps(cargar(), indent=2, ensure_ascii=False).encode("utf-8")


def importar(contenido: bytes) -> None:
    datos = json.loads(contenido.decode("utf-8"))
    if not isinstance(datos, dict):
        raise ValueError("El archivo no tiene el formato esperado.")
    base = copy.deepcopy(DEFECTO)
    for k, val in datos.items():
        if k in base and isinstance(base[k], dict) and isinstance(val, dict):
            base[k].update(val)
        elif k in base:
            base[k] = val
    guardar(base)


def hay_cambios() -> bool:
    return RUTA.exists()


# ---------------------------------------------------------------------------
# secciones
# ---------------------------------------------------------------------------
def seccion(vista: str, bloque: str, titulo: str, abierto: bool, orden: int) -> dict:
    """Configuración guardada de un bloque, con los valores de fábrica de respaldo."""
    guardadas = cargar()["secciones"]
    s = guardadas.get(f"{vista}.{bloque}", {})
    return {
        "visible": bool(s.get("visible", True)),
        "abierto": bool(s.get("abierto", abierto)),
        "orden": int(s.get("orden", orden)),
        "titulo": str(s.get("titulo") or titulo),
    }


def set_seccion(vista: str, bloque: str, **campos) -> None:
    a = cargar()
    a["secciones"].setdefault(f"{vista}.{bloque}", {}).update(campos)
    guardar(a)


def colores() -> dict:
    c = dict(COLORES)
    c.update(cargar().get("colores") or {})
    return c


def densidad() -> dict:
    return DENSIDADES.get(cargar().get("densidad", "Normal"), DENSIDADES["Normal"])


def escala() -> float:
    try:
        return max(0.85, min(1.30, float(cargar().get("escala_texto", 1.0))))
    except (TypeError, ValueError):
        return 1.0
