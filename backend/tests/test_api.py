import csv

import pytest
from fastapi.testclient import TestClient

import main
from repositorio import DemoRepositorio

COLUMNAS = ["tipo_operacion", "tipo_inmueble", "precio_uf", "precio_clp", "comuna",
            "superficie_m2", "url", "fecha_ultima_vista"]
FILAS = [
    ("venta", "departamento", 3000, 1, "Lota", "60 m²", "a", "2026-01-03"),
    ("venta", "departamento", 5500, 1, "Lota", "100 m²", "b", "2026-01-02"),
    ("venta", "departamento", 12, 1, "Lota", "", "c", "2026-01-01"),        # excluido
    ("arriendo", "casa", 15, 1, "Penco", "90 m²", "d", "2026-01-04"),
    ("arriendo", "casa", 4200, 1, "Penco", "90 m²", "e", "2026-01-05"),     # excluido
]


@pytest.fixture
def cliente(tmp_path):
    p = tmp_path / "avisos.csv"
    with p.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(COLUMNAS)
        w.writerows(FILAS)
    main.app.dependency_overrides[main.obtener_repo] = lambda: DemoRepositorio(p)
    yield TestClient(main.app)
    main.app.dependency_overrides.clear()


def test_salud(cliente):
    assert cliente.get("/salud").json() == {"fuente": "demo", "avisos": 5}


def test_propiedades_filtra_pagina_y_marca_excluidos(cliente):
    r = cliente.get("/propiedades", params={"comuna": "Lota", "limit": 2}).json()
    assert r["total"] == 3 and len(r["items"]) == 2
    assert r["items"][0]["url"] == "a"                     # orden 'reciente'
    todos = cliente.get("/propiedades", params={"comuna": "Lota"}).json()["items"]
    assert [i["motivo_exclusion"] is not None for i in todos] == [False, False, True]


def test_orden_por_uf_m2(cliente):
    items = cliente.get("/propiedades", params={"comuna": "Lota", "orden": "uf_m2_asc"}).json()["items"]
    assert [i["url"] for i in items][:2] == ["a", "b"]     # 50 UF/m² < 55 UF/m²
    assert items[0]["uf_m2"] == 50.0


def test_resumen_usa_mediana_y_cuenta_excluidos(cliente):
    r = cliente.get("/resumen", params={"tipo_operacion": "venta",
                                        "tipo_inmueble": "departamento"}).json()
    lota = r["comunas"][0]
    assert lota["comuna"] == "Lota"
    assert lota["mediana_uf"] == 4250 and lota["excluidos"] == 1
    assert r["excluidos"] == 1


def test_resumen_comuna_404(cliente):
    assert cliente.get("/resumen/Narnia").status_code == 404


def test_valida_parametros(cliente):
    assert cliente.get("/propiedades", params={"tipo_operacion": "permuta"}).status_code == 422
    assert cliente.get("/propiedades", params={"limit": 500}).status_code == 422


def test_calidad(cliente):
    c = cliente.get("/calidad").json()
    assert c["total"] == 5 and c["excluidos"] == 2
    assert {m["motivo"] for m in c["por_motivo"]} == {"venta_baja", "arriendo_alto"}


def test_propiedades_trae_posicion_e_historial(cliente):
    item = cliente.get("/propiedades", params={"comuna": "Lota"}).json()["items"][0]
    assert {"posicion", "dias_publicado", "cambio_precio_pct"} <= item.keys()
    # 2 avisos válidos con m² en Lota: bajo el mínimo de 10 → sin referencia
    assert item["posicion"]["codigo"] == "sin_referencia"


def test_filtro_por_posicion(cliente):
    r = cliente.get("/propiedades", params={"posicion": "sin_referencia"}).json()
    assert r["total"] == 5
    assert cliente.get("/propiedades", params={"posicion": "bajo"}).json()["total"] == 0
    assert cliente.get("/propiedades", params={"posicion": "otra"}).status_code == 422


def test_rentabilidad_endpoint(cliente):
    r = cliente.get("/rentabilidad").json()
    assert r["minimo_por_lado"] == 10 and r["filas"] == []     # muestra chica: no inventa
