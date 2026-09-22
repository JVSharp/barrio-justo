"""
Horas de sol directo en un punto, considerando los edificios de alrededor.

Método:
1. Posición del sol (elevación y azimut) con las ecuaciones de la NOAA
   (https://gml.noaa.gov/grad/solcalc/calcdetails.html), precisión de
   ~1 minuto de arco: de sobra para contar horas.
2. "Horizonte" del punto: para cada grado de azimut, el ángulo de elevación
   más alto que tapa algún edificio cercano (altura del edificio menos la del
   observador, sobre la distancia).
3. Hay sol directo cuando el sol está sobre el horizonte del cielo *y* sobre
   ese horizonte de edificios.

No considera cerros, árboles ni la orientación de las ventanas. Las
coordenadas se pasan a metros con una proyección local (equirectangular),
suficiente para radios de un par de cientos de metros.
"""

from __future__ import annotations

import math
from datetime import date, datetime, timedelta, timezone
from typing import Iterable, Sequence

Punto = tuple[float, float]  # (lat, lon)


# ---------------------------------------------------------------------------
# Posición solar (NOAA)
# ---------------------------------------------------------------------------

def posicion_solar(momento: datetime, lat: float, lon: float) -> tuple[float, float]:
    """(elevación, azimut) en grados. Azimut desde el norte, en sentido horario."""
    if momento.tzinfo is None:
        raise ValueError("el momento debe tener zona horaria")
    t = momento.astimezone(timezone.utc)
    jd = t.timestamp() / 86400.0 + 2440587.5
    jc = (jd - 2451545.0) / 36525.0

    L0 = (280.46646 + jc * (36000.76983 + jc * 0.0003032)) % 360
    M = 357.52911 + jc * (35999.05029 - 0.0001537 * jc)
    e = 0.016708634 - jc * (0.000042037 + 0.0000001267 * jc)
    Mr = math.radians(M)
    C = (math.sin(Mr) * (1.914602 - jc * (0.004817 + 0.000014 * jc))
         + math.sin(2 * Mr) * (0.019993 - 0.000101 * jc) + math.sin(3 * Mr) * 0.000289)
    omega = math.radians(125.04 - 1934.136 * jc)
    lam = math.radians(L0 + C - 0.00569 - 0.00478 * math.sin(omega))
    eps0 = 23 + (26 + (21.448 - jc * (46.815 + jc * (0.00059 - jc * 0.001813))) / 60) / 60
    eps = math.radians(eps0 + 0.00256 * math.cos(omega))
    decl = math.asin(math.sin(eps) * math.sin(lam))

    y = math.tan(eps / 2) ** 2
    L0r = math.radians(L0)
    eq_time = 4 * math.degrees(
        y * math.sin(2 * L0r) - 2 * e * math.sin(Mr) + 4 * e * y * math.sin(Mr) * math.cos(2 * L0r)
        - 0.5 * y * y * math.sin(4 * L0r) - 1.25 * e * e * math.sin(2 * Mr)
    )
    minutos = t.hour * 60 + t.minute + t.second / 60
    tst = (minutos + eq_time + 4 * lon) % 1440
    ha = math.radians(tst / 4 - 180)

    latr = math.radians(lat)
    cos_z = math.sin(latr) * math.sin(decl) + math.cos(latr) * math.cos(decl) * math.cos(ha)
    zen = math.acos(max(-1.0, min(1.0, cos_z)))
    elev = 90 - math.degrees(zen)

    den = math.cos(latr) * math.sin(zen)
    if abs(den) < 1e-9:
        az = 180.0 if lat > 0 else 0.0
    else:
        c = (math.sin(latr) * math.cos(zen) - math.sin(decl)) / den
        az0 = math.degrees(math.acos(max(-1.0, min(1.0, c))))
        az = (az0 + 180) % 360 if ha > 0 else (540 - az0) % 360
    return elev, az


def trayectoria(dia: date, lat: float, lon: float, utc_offset_h: float, paso_min: int = 10):
    """Posiciones del sol durante el día local, cada `paso_min` minutos.
    Devuelve [(elevación, azimut)] solo para los instantes con sol sobre el horizonte."""
    tz = timezone(timedelta(hours=utc_offset_h))
    inicio = datetime(dia.year, dia.month, dia.day, tzinfo=tz)
    salida = []
    for k in range(0, 24 * 60, paso_min):
        elev, az = posicion_solar(inicio + timedelta(minutes=k), lat, lon)
        if elev > 0:
            salida.append((elev, az))
    return salida


# ---------------------------------------------------------------------------
# Geometría local
# ---------------------------------------------------------------------------

def a_metros(lat0: float, lon0: float, lat: float, lon: float) -> tuple[float, float]:
    """(x hacia el este, y hacia el norte) en metros desde (lat0, lon0)."""
    return ((lon - lon0) * 111_320.0 * math.cos(math.radians(lat0)), (lat - lat0) * 110_540.0)


def dentro(x: float, y: float, poligono: Sequence[tuple[float, float]]) -> bool:
    """Punto en polígono (ray casting)."""
    adentro = False
    n = len(poligono)
    for i in range(n):
        x1, y1 = poligono[i]
        x2, y2 = poligono[(i + 1) % n]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            adentro = not adentro
    return adentro


def _azimut(x: float, y: float) -> float:
    return math.degrees(math.atan2(x, y)) % 360     # 0 = norte, 90 = este


def horizonte(edificios: Iterable[tuple[float, Sequence[tuple[float, float]]]], altura_obs: float,
              paso_m: float = 2.0) -> list[float]:
    """Ángulo de elevación (grados) que tapan los edificios en cada grado de azimut.

    `edificios`: [(altura_m, [(x, y), ...])] en metros relativos al observador.
    Los bordes se recorren cada `paso_m` y, entre dos muestras consecutivas,
    se rellenan todos los grados intermedios con el menor de los dos ángulos
    (conservador: no inventa sombra que no está).
    """
    h = [0.0] * 360
    for altura, poligono in edificios:
        dh = altura - altura_obs
        if dh <= 0 or len(poligono) < 3:
            continue
        muestras: list[tuple[float, float]] = []
        n = len(poligono)
        for i in range(n):
            (x1, y1), (x2, y2) = poligono[i], poligono[(i + 1) % n]
            largo = math.hypot(x2 - x1, y2 - y1)
            pasos = max(1, int(largo / paso_m))
            for k in range(pasos):
                f = k / pasos
                x, y = x1 + (x2 - x1) * f, y1 + (y2 - y1) * f
                d = max(math.hypot(x, y), 0.5)
                muestras.append((_azimut(x, y), math.degrees(math.atan2(dh, d))))
        for j in range(len(muestras)):
            az1, a1 = muestras[j]
            az2, a2 = muestras[(j + 1) % len(muestras)]
            ang = min(a1, a2)
            # recorrer el arco corto entre az1 y az2
            delta = ((az2 - az1 + 540) % 360) - 180
            pasos = max(1, int(abs(delta)) + 1)
            for k in range(pasos + 1):
                b = int((az1 + delta * k / pasos) % 360) % 360   # 359,9999… % 360 puede dar 360.0
                if ang > h[b]:
                    h[b] = ang
    return h


def horas_de_sol(trayecto: Sequence[tuple[float, float]], horiz: Sequence[float], paso_min: int = 10) -> float:
    visibles = sum(1 for elev, az in trayecto if elev > horiz[int(az) % 360])
    return round(visibles * paso_min / 60, 1)
