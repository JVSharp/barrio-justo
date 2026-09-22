"""v3: posición de precio, rentabilidad bruta e historial."""

import pytest

import analisis as a
from scrapers.base import BaseScraper


def av(uf, m2=100, comuna="Lota", op="venta", tipo="departamento", url=None, **extra):
    return {"precio_uf": uf, "superficie_m2": f"{m2} m²", "comuna": comuna, "tipo_operacion": op,
            "tipo_inmueble": tipo, "url": url or f"{comuna}{op}{tipo}{uf}{m2}{extra}", **extra}


def grupo(n=20, base=40, **kw):
    """n avisos con UF/m² = base, base+1, …  (100 m² cada uno)."""
    return [av((base + i) * 100, **kw) for i in range(n)]


# --- referencias y posición -------------------------------------------------

def test_referencia_solo_con_muestra_suficiente():
    refs = a.referencias(grupo(9) + grupo(12, comuna="Penco"))
    assert ("Lota", "venta", "departamento") not in refs          # 9 < 10
    assert refs[("Penco", "venta", "departamento")]["n"] == 12


@pytest.mark.parametrize("uf_m2, codigo", [(30, "bajo"), (50, "en_rango"), (70, "sobre")])
def test_posicion_por_cuartiles(uf_m2, codigo):
    refs = a.referencias(grupo(21))            # 40..60 → p25=45, mediana=50, p75=55
    p = a.posicion(av(uf_m2 * 100), refs)
    assert p["codigo"] == codigo


def test_vs_mediana_pct():
    refs = a.referencias(grupo(21))
    assert a.posicion(av(4500), refs)["vs_mediana_pct"] == -10   # 45 vs 50


def test_sin_referencia_si_no_hay_m2_o_esta_excluido():
    refs = a.referencias(grupo(21))
    assert a.posicion(av(5000, m2=""), refs)["codigo"] == "sin_referencia"
    assert a.posicion(av(10), refs)["codigo"] == "sin_referencia"       # venta < 300 UF
    assert a.posicion(av(5000, comuna="Narnia"), refs)["codigo"] == "sin_referencia"


def test_los_excluidos_no_mueven_la_referencia():
    limpio = a.referencias(grupo(21))
    sucio = a.referencias(grupo(21) + [av(10, url="malo1"), av(99_999_999, url="malo2")])
    assert limpio == sucio


# --- rentabilidad -----------------------------------------------------------

def test_rentabilidad_bruta():
    venta = [av(5000, url=f"v{i}") for i in range(10)]                     # 50 UF/m²
    arriendo = [av(20, op="arriendo", url=f"a{i}") for i in range(10)]     # 0,2 UF/m²/mes
    fila = a.rentabilidad(venta + arriendo)[0]
    assert fila["rentabilidad_bruta_pct"] == pytest.approx(4.8)            # 0,2×12/50
    assert fila["n_venta"] == 10 and fila["n_arriendo"] == 10


def test_rentabilidad_requiere_ambos_lados():
    venta = [av(5000, url=f"v{i}") for i in range(10)]
    arriendo = [av(20, op="arriendo", url=f"a{i}") for i in range(9)]       # 9 < 10
    assert a.rentabilidad(venta + arriendo) == []


# --- historial ----------------------------------------------------------------

def test_historial_desde_lista_y_desde_texto():
    lista = {"precio_uf": 3000, "fecha_primera_vista": "2026-06-01", "fecha_ultima_vista": "2026-07-01",
             "historial_precios": [{"fecha": "2026-06-01", "precio_uf": 3200}, {"fecha": "2026-06-15", "precio_uf": 3000}]}
    texto = {**lista, "historial_precios": "2026-06-01:3200|2026-06-15:3000"}
    for aviso in (lista, texto):
        h = a.historial(aviso)
        assert h == {"dias_publicado": 30, "cambio_precio_pct": -6.2, "cambios_de_precio": 1}


def test_historial_sin_datos():
    assert a.historial({}) == {"dias_publicado": None, "cambio_precio_pct": None, "cambios_de_precio": 0}


class ColeccionFalsa:
    def __init__(self):
        self.docs = {}

    def find_one(self, filtro, proyeccion=None):
        d = self.docs.get(filtro["url"])
        return dict(d) if d else None

    def insert_one(self, doc):
        self.docs[doc["url"]] = dict(doc)

    def update_one(self, filtro, cambios):
        d = self.docs[filtro["url"]]
        d.update(cambios.get("$set", {}))
        for k, v in cambios.get("$push", {}).items():
            d.setdefault(k, []).append(v)


class Scraper(BaseScraper):
    def scrape(self):
        pass


def test_guardar_agrega_historial_solo_si_cambia_el_precio():
    col = ColeccionFalsa()
    s = Scraper(coleccion=col)
    s.guardar({"url": "x", "precio_uf": 3200})
    s.guardar({"url": "x", "precio_uf": 3200})          # mismo precio: no agrega
    s.guardar({"url": "x", "precio_uf": 3000})          # bajó: agrega
    h = col.docs["x"]["historial_precios"]
    assert [p["precio_uf"] for p in h] == [3200, 3000]
    assert s.nuevos == 1 and s.actualizados == 2 and s.cambios_de_precio == 1
    assert "fecha_primera_vista" in col.docs["x"]


def test_guardar_siembra_historial_en_avisos_anteriores_a_v3():
    col = ColeccionFalsa()
    col.docs["y"] = {"url": "y", "precio_uf": 5000, "fecha_ultima_vista": "2026-01-01"}   # sin historial
    s = Scraper(coleccion=col)
    s.guardar({"url": "y", "precio_uf": 4800})
    assert [p["precio_uf"] for p in col.docs["y"]["historial_precios"]] == [5000, 4800]
