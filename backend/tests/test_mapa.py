"""v4: celdas del mapa."""

import csv

import analisis as a
from repositorio import DemoRepositorio


def av(uf, lat, lon, m2=100, url=None, **kw):
    return {"precio_uf": uf, "superficie_m2": f"{m2} m²", "tipo_operacion": "venta",
            "tipo_inmueble": "departamento", "comuna": "Concepción", "latitud": lat, "longitud": lon,
            "url": url or f"{uf}{lat}{lon}{kw}", **kw}


def test_agrupa_por_celda_con_mediana():
    avisos = [av(4000, -36.8201, -73.0401, url="1"), av(5000, -36.8202, -73.0402, url="2"),
              av(9000, -36.8203, -73.0403, url="3")]
    c = a.celdas(avisos)["celdas"]
    assert len(c) == 1
    assert c[0]["n"] == 3 and c[0]["mediana_uf_m2"] == 50.0          # no el promedio (60)


def test_no_dibuja_celdas_chicas():
    avisos = [av(4000, -36.8201, -73.0401, url="1"), av(5000, -36.8202, -73.0402, url="2")]
    assert a.celdas(avisos)["celdas"] == []


def test_descarta_sin_coordenadas_fuera_de_region_y_excluidos():
    base = [av(4000 + i, -36.8201, -73.0401, url=str(i)) for i in range(3)]
    ruido = [av(4000, None, None, url="sin"), av(4000, 0.0, 0.0, url="cero"),
             av(4000, -33.45, -70.66, url="stgo"), av(10, -36.8201, -73.0401, url="malo")]
    r = a.celdas(base + ruido)
    assert r["avisos_con_coordenadas"] == 3
    assert r["celdas"][0]["n"] == 3


def test_celdas_distintas_no_se_mezclan():
    lejos = [av(4000, -36.80, -73.00, url=f"a{i}") for i in range(3)] + \
            [av(8000, -36.90, -73.10, url=f"b{i}") for i in range(3)]
    assert len(a.celdas(lejos)["celdas"]) == 2


def test_demo_lee_coordenadas_negativas(tmp_path):
    p = tmp_path / "d.csv"
    with p.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["url", "precio_uf", "latitud", "longitud"])
        w.writerow(["x", "1", "-36.8201", "-73.0401"])
        w.writerow(["y", "1", "", ""])
    avisos = DemoRepositorio(p).todos({})
    assert avisos[0]["latitud"] == -36.8201 and avisos[0]["longitud"] == -73.0401
    assert avisos[1]["latitud"] is None


def test_demo_une_metricas_geo_por_url(tmp_path):
    p = tmp_path / "avisos.csv"
    p.write_text("url,precio_uf,latitud,longitud\nx,1,-36.8,-73.0\ny,1,-36.8,-73.0\n", encoding="utf-8")
    (tmp_path / "geo.csv").write_text(
        "url,dist_biotren,cerca_biotren,sol_calle,sol_calidad\nx,350,Estación A,4.5,\n", encoding="utf-8")
    x, y = DemoRepositorio(p).todos({})
    assert x["dist_biotren"] == 350.0 and x["cerca_biotren"] == "Estación A"
    assert x["sol_calle"] == 4.5 and x["sol_calidad"] is None
    assert "dist_biotren" not in y
