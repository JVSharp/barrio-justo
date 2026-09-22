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
    a = s.procesar({"price": {"amount": 2000, "currency_id": "CLF"}}, comuna, "venta", "casa", uf=None)
    assert a["precio_uf"] == 2000 and a["precio_clp"] is None
