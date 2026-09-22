"""v5: posición solar, horas de sol con edificios y distancias."""

from datetime import date, datetime, timedelta, timezone

import pytest

import geo
import sol

CONCE = (-36.8270, -73.0503)
UTC4 = timezone(timedelta(hours=-4))
UTC3 = timezone(timedelta(hours=-3))


# --- posición solar -----------------------------------------------------------

def test_mediodia_de_invierno_en_concepcion():
    """21 de junio: el sol culmina al norte a ~29,7° (90 − 36,8 − 23,44)."""
    tray = sol.trayectoria(date(2026, 6, 21), *CONCE, utc_offset_h=-4, paso_min=1)
    elev_max, az = max(tray)
    assert elev_max == pytest.approx(29.73, abs=0.3)
    assert az == pytest.approx(0, abs=3) or az == pytest.approx(360, abs=3)   # norte


def test_mediodia_de_verano_en_concepcion():
    tray = sol.trayectoria(date(2026, 12, 21), *CONCE, utc_offset_h=-3, paso_min=1)
    assert max(tray)[0] == pytest.approx(76.6, abs=0.3)


def test_horas_de_luz_del_dia_mas_corto():
    """Día geométrico (centro del sol sobre el horizonte, sin refracción):
    cos H = −tan(φ)·tan(δ) → H ≈ 71°, 2H/15 ≈ 9,47 h. Las tablas civiles dan
    ~9 h 38 min porque suman la refracción y el radio del disco."""
    tray = sol.trayectoria(date(2026, 6, 21), *CONCE, utc_offset_h=-4, paso_min=1)
    assert len(tray) / 60 == pytest.approx(9.47, abs=0.05)


def test_sale_por_el_noreste_en_invierno():
    """Sale ~8:10 (hora de invierno) por el noreste."""
    elev, az = sol.posicion_solar(datetime(2026, 6, 21, 8, 40, tzinfo=UTC4), *CONCE)
    assert 0 < elev < 10 and 45 < az < 75
    antes, _ = sol.posicion_solar(datetime(2026, 6, 21, 8, 0, tzinfo=UTC4), *CONCE)
    assert antes < 0


def test_requiere_zona_horaria():
    with pytest.raises(ValueError):
        sol.posicion_solar(datetime(2026, 6, 21, 12), *CONCE)


# --- horizonte y horas de sol -------------------------------------------------

def caja(x0, y0, ancho, fondo):
    return [(x0, y0), (x0 + ancho, y0), (x0 + ancho, y0 + fondo), (x0, y0 + fondo)]


TRAY = sol.trayectoria(date(2026, 6, 21), *CONCE, utc_offset_h=-4)
LUZ = round(len(TRAY) * 10 / 60, 1)


def test_sin_edificios_hay_sol_todo_el_dia():
    assert sol.horas_de_sol(TRAY, sol.horizonte([], 1.5)) == LUZ


def test_edificio_alto_al_norte_tapa_el_sol_de_invierno():
    """Una torre de 40 m a 20 m al norte: en invierno el sol va bajo y por el norte."""
    torre = [(40.0, caja(-30, 20, 60, 20))]
    calle = sol.horas_de_sol(TRAY, sol.horizonte(torre, 1.5))
    piso10 = sol.horas_de_sol(TRAY, sol.horizonte(torre, 28.5))
    assert calle < LUZ * 0.5
    assert piso10 > calle            # más arriba, menos tapado


def test_edificio_al_sur_no_quita_sol_en_invierno():
    torre_sur = [(40.0, caja(-30, -40, 60, 20))]
    assert sol.horas_de_sol(TRAY, sol.horizonte(torre_sur, 1.5)) == LUZ


def test_edificio_mas_bajo_que_el_observador_no_tapa():
    casa = [(6.0, caja(-10, 10, 20, 10))]
    assert sol.horas_de_sol(TRAY, sol.horizonte(casa, 16.5)) == LUZ


def test_punto_en_poligono():
    assert sol.dentro(0, 0, caja(-5, -5, 10, 10))
    assert not sol.dentro(20, 0, caja(-5, -5, 10, 10))


def a_latlon(x, y, lat0=CONCE[0], lon0=CONCE[1]):
    import math
    return (lat0 + y / 110_540.0, lon0 + x / (111_320.0 * math.cos(math.radians(lat0))))


def edificio(altura, conocida, puntos_xy):
    return [altura, conocida, [list(a_latlon(x, y)) for x, y in puntos_xy]]


def test_sol_en_invierno_excluye_el_propio_edificio_y_mide_calidad():
    propio = edificio(60, 1, caja(-10, -10, 20, 20))       # el aviso está adentro
    norte = edificio(40, 0, caja(-30, 20, 60, 20))          # altura supuesta
    ind = geo.indice_edificios([propio, norte])
    r = geo.sol_en_invierno(*CONCE, ind, TRAY)
    assert r["sol_edificios"] == 1                            # solo el del norte
    assert r["sol_calidad"] == 0.0
    assert r["sol_calle"] < r["sol_p10"] <= r["sol_horas_luz"]


def test_sin_edificios_cerca_calidad_desconocida():
    r = geo.sol_en_invierno(*CONCE, geo.indice_edificios([]), TRAY)
    assert r["sol_calidad"] is None and r["sol_calle"] == r["sol_horas_luz"]


# --- cercanía ---------------------------------------------------------------

def test_distancia_al_mas_cercano():
    pois = {"biotren": [[*a_latlon(0, 300), "Estación A"], [*a_latlon(0, 2000), "Estación B"]],
            "supermercado": []}
    r = geo.cercania(*CONCE, geo.indice_pois(pois))
    assert r["dist_biotren"] == pytest.approx(300, abs=3) and r["cerca_biotren"] == "Estación A"
    assert r["dist_supermercado"] is None


def test_categorias_desconocidas_se_ignoran():
    assert geo.indice_pois({"karaoke": [[0, 0, "x"]]}) == {}


def test_borde_que_cruza_el_norte_exacto_no_se_sale_del_arreglo():
    """Regresión: un borde que pasa justo por azimut 0/360 daba índice 360."""
    borde = [(40.0, [(-1e-13, 10.0), (1e-13, 10.0), (1e-13, 30.0), (-1e-13, 30.0)])]
    h = sol.horizonte(borde, 1.5)
    assert len(h) == 360 and max(h) > 0
