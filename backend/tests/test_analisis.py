import pytest

import analisis as a


def aviso(uf, op="venta", m2="80 m²", url=None, **extra):
    return {"precio_uf": uf, "tipo_operacion": op, "superficie_m2": m2,
            "url": url or f"u{uf}{op}{m2}", **extra}


@pytest.mark.parametrize("entrada, esperado", [
    ("120 m²", 120.0), ("45,5 m2", 45.5), (3, 3.0), ("", None), (None, None), ("n/a", None),
    ("1.200 m² totales", 1200.0), ("12.5", 12.5), ("65 m² útiles", 65.0),
])
def test_numero(entrada, esperado):
    assert a.numero(entrada) == esperado


@pytest.mark.parametrize("av, motivo", [
    (aviso(0), "sin_precio"),
    (aviso(None), "sin_precio"),
    (aviso(40), "venta_baja"),
    (aviso(250_000), "venta_alta"),
    (aviso(4_000, op="arriendo"), "arriendo_alto"),
    (aviso(1, op="arriendo"), "arriendo_bajo"),
    (aviso(3_500), None),
    (aviso(15, op="arriendo"), None),
    (aviso(3_500, es_proyecto=True), "proyecto"),
    (aviso(3_500, es_proyecto="False"), None),
])
def test_motivo_exclusion(av, motivo):
    assert a.motivo_exclusion(av) == motivo


def test_limpiar_separa_duplicados_y_malos():
    avisos = [aviso(3000, url="x"), aviso(3000, url="x"), aviso(10), aviso(4000)]
    validos, excluidos = a.limpiar(avisos)
    assert len(validos) == 2
    assert sorted(e["motivo"] for e in excluidos) == ["duplicado", "venta_baja"]


def test_mediana_no_se_mueve_con_un_outlier():
    """El caso que motivó el cambio: un valor absurdo no arrastra el resultado."""
    normales = [aviso(p, url=str(i)) for i, p in enumerate([3000, 3200, 3400, 3600, 3800])]
    con_outlier = normales + [aviso(95_000, url="raro")]
    assert a.estadisticas(normales)["mediana_uf"] == 3400
    assert a.estadisticas(con_outlier)["mediana_uf"] == 3500   # promedio sería ~18.700


def test_uf_m2_ignora_superficies_absurdas():
    avisos = [aviso(4000, m2="80 m²", url="a"), aviso(4000, m2="2 m²", url="b"),
              aviso(4000, m2="", url="c")]
    s = a.estadisticas(avisos)
    assert s["con_superficie"] == 1
    assert s["mediana_uf_m2"] == 50.0


def test_percentil_coincide_con_numpy():
    assert a.percentil([1, 2, 3, 4], 0.25) == pytest.approx(1.75)
    assert a.percentil([10], 0.75) == 10


def test_resumen_por_cuenta_excluidos_por_grupo():
    avisos = [aviso(3000, comuna="Lota", url="1"), aviso(10, comuna="Lota", url="2"),
              aviso(5000, comuna="Penco", url="3")]
    filas = {f["comuna"]: f for f in a.resumen_por(avisos, ("comuna",))}
    assert filas["Lota"]["cantidad"] == 1 and filas["Lota"]["excluidos"] == 1
    assert filas["Penco"]["excluidos"] == 0
