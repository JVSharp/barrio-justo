"""Tests del scraper sin red ni MongoDB."""

import comunas
from scrapers.portalinmobiliario import PortalInmobiliarioScraper


def scraper():
    return object.__new__(PortalInmobiliarioScraper)   # sin conectar a Mongo


def test_la_paginacion_cambia_la_url_que_llega_al_servidor():
    """Regresión de la v1: agregaba '#2', que nunca sale del navegador."""
    s = scraper()
    p1 = s.url("venta", "casa", "lota")
    p2 = s.url("venta", "casa", "lota", desde=49)
    assert "#" not in p2
    assert p1 != p2
    assert "_Desde_49_" in p2
    assert p1.endswith("/lota-biobio/_DisplayType_M")


def test_hay_33_comunas_y_los_slugs_son_minusculas():
    todas = comunas.cargar()
    assert len(todas) == 33
    assert all(c.slug == c.slug.lower() for c in todas)
    assert {"concepcion", "chiguayante", "nacimiento"} <= {c.slug for c in todas}


def test_procesar_precio_en_uf_y_en_pesos():
    s = scraper()
    comuna = comunas.Comuna("lota", "Lota", "Concepción")
    en_uf = s.procesar({"price": {"amount": 2000, "currency_id": "CLF"}, "permalink": "x"},
                       comuna, "venta", "casa", uf=40_000)
    assert en_uf["precio_uf"] == 2000 and en_uf["precio_clp"] == 80_000_000

    en_pesos = s.procesar({"price": {"amount": 400_000, "currency_id": "CLP"}, "permalink": "y"},
                          comuna, "arriendo", "casa", uf=40_000)
    assert en_pesos["precio_uf"] == 10.0 and en_pesos["comuna"] == "Lota"


def test_sin_uf_no_inventa_el_precio_en_pesos():
    s = scraper()
    comuna = comunas.Comuna("lota", "Lota", "Concepción")
    a = s.procesar({"price": {"amount": 2000, "currency_id": "CLF"}, "permalink": "z"}, comuna, "venta", "casa", uf=None)
    assert a["precio_uf"] == 2000 and a["precio_clp"] is None


def polycard(id_, precio=3200, moneda="CLF", textos=("2 dormitorios", "2 baños", "65 m² útiles"),
             pill=None, prefijo=""):
    """Tarjeta con la forma real del portal (2026) y valores inventados."""
    comps = [{"type": "title", "id": "title", "title": {"text": "Departamento en venta"}},
             {"type": "price", "id": "price",
              "price": {"current_price": {"value": precio, "currency": moneda}, "prefix": {"text": prefijo}}},
             {"type": "attributes_list", "id": "attributes_list",
              "attributes_list": {"texts": list(textos)}}]
    if pill:
        comps.insert(0, {"type": "pill", "id": pill, "pill": {"text": "Proyecto"}})
    return {"id": "POLYCARD", "state": "VISIBLE",
            "polycard": {"metadata": {"id": id_, "url": f"www.portal.example/{id_}",
                                      "latitude": "-36.82", "longitude": "-73.04"},
                         "components": comps}}


def test_lee_el_formato_polycard():
    s = scraper()
    comuna = comunas.Comuna("concepcion", "Concepción", "Concepción")
    a = s.procesar(polycard("MLC1"), comuna, "venta", "departamento", uf=40_000,
                   url_prefix="https://")
    assert a["id_aviso"] == "MLC1"                      # no 'POLYCARD'
    assert a["url"] == "https://www.portal.example/MLC1"
    assert a["precio_uf"] == 3200 and a["precio_clp"] == 128_000_000
    assert a["dormitorios"] == 2 and a["banos"] == 2 and a["superficie_m2"] == "65 m² útiles"
    assert a["es_proyecto"] is False and a["latitud"] == -36.82


def test_marca_proyectos_nuevos():
    s = scraper()
    comuna = comunas.Comuna("concepcion", "Concepción", "Concepción")
    for card in (polycard("MLC2", pill="project"), polycard("MLC3", prefijo="Desde")):
        assert s.procesar(card, comuna, "venta", "departamento", uf=None)["es_proyecto"] is True


def test_tarjeta_sin_metadata_no_se_guarda():
    s = scraper()
    comuna = comunas.Comuna("lota", "Lota", "Concepción")
    assert s.procesar({"id": "POLYCARD", "polycard": {}}, comuna, "venta", "casa", uf=None) is None


class _Resp:
    def __init__(self, data):
        self._d = data

    def raise_for_status(self):
        pass

    def json(self):
        return self._d


def test_combinacion_pagina_y_para_cuando_se_repite(monkeypatch):
    """100 tarjetas por página: la 2ª pide _Desde_101 y la 3ª repite → fin."""
    import scrapers.portalinmobiliario as mod
    monkeypatch.setattr(mod.time, "sleep", lambda s: None)
    s = scraper()
    guardados, pedidas = [], []
    s.guardar = guardados.append
    pag1 = [polycard(f"MLC{i}") for i in range(100)]
    pag2 = [polycard(f"MLC{i}") for i in range(100, 130)]

    class Http:
        def get(self, url, timeout):
            pedidas.append(url)
            if "_Desde_101_" in url:
                return _Resp({"results": pag2})
            if "_Desde_" in url:
                return _Resp({"results": pag2})        # repetido: debe cortar
            return _Resp({"results": pag1, "polycard_context": {"url_prefix": "https://"}})

    s.http = Http()
    s._combinacion(comunas.Comuna("concepcion", "Concepción", "Concepción"), "venta", "departamento", None)
    assert len(guardados) == 130
    assert "_Desde_101_" in pedidas[1] and len(pedidas) == 3
