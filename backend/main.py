"""
API de Comuna Dash.

    uvicorn main:app --reload        (desde backend/)

Documentación interactiva en /docs.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Annotated, Literal

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

import analisis
import config
import repositorio
from repositorio import Repositorio

CFG = config.cargar()

app = FastAPI(
    title="Comuna Dash API",
    description="Avisos de propiedades del Biobío y estadísticas robustas por comuna.",
    version="2.0.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CFG.cors_origins,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@lru_cache(maxsize=1)
def obtener_repo() -> Repositorio:
    return repositorio.crear(CFG)


Repo = Annotated[Repositorio, Depends(obtener_repo)]
Operacion = Literal["venta", "arriendo"]
Inmueble = Literal["casa", "departamento"]


def _filtro(**campos: str | None) -> dict[str, str]:
    return {k: v for k, v in campos.items() if v}


@app.get("/salud", tags=["meta"])
def salud(repo: Repo):
    """Qué fuente de datos está usando la API y cuántos avisos tiene."""
    return {"fuente": repo.fuente, "avisos": repo.contar()}


@app.get("/comunas", tags=["meta"])
def comunas(repo: Repo) -> list[str]:
    return repo.distintos("comuna")


@app.get("/tipos_inmueble", tags=["meta"])
def tipos_inmueble(repo: Repo) -> list[str]:
    return repo.distintos("tipo_inmueble")


@app.get("/tipos_operacion", tags=["meta"])
def tipos_operacion(repo: Repo) -> list[str]:
    return repo.distintos("tipo_operacion")


def refs_de(repo: Repositorio) -> dict:
    """Referencias de UF/m² por grupo. Dependen de todos los avisos (no solo
    de la página pedida), así que se guardan en el repositorio por 60 s."""
    import time

    ahora = time.monotonic()
    guardado = getattr(repo, "_cache_refs", None)
    if guardado and ahora - guardado[0] < 60:
        return guardado[1]
    refs = analisis.referencias(repo.todos({}))
    repo._cache_refs = (ahora, refs)
    return refs


Posicion = Literal["bajo", "en_rango", "sobre", "sin_referencia"]


@app.get("/propiedades", tags=["avisos"])
def propiedades(
    repo: Repo,
    comuna: str | None = None,
    tipo_operacion: Operacion | None = None,
    tipo_inmueble: Inmueble | None = None,
    posicion: Posicion | None = None,
    orden: Literal["reciente", "precio_asc", "precio_desc", "uf_m2_asc", "vs_mediana_asc"] = "reciente",
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 24,
):
    """Avisos filtrados y paginados. Cada aviso trae su UF/m², si quedó fuera
    del análisis (y por qué), dónde cae frente a su comuna (`posicion`) y su
    historial (`dias_publicado`, `cambio_precio_pct`)."""
    refs = refs_de(repo)
    avisos = repo.todos(_filtro(comuna=comuna, tipo_operacion=tipo_operacion,
                                tipo_inmueble=tipo_inmueble))
    avisos = [analisis.enriquecer(a, refs) for a in avisos]
    if posicion:
        avisos = [a for a in avisos if a["posicion"]["codigo"] == posicion]
    avisos = repositorio.ordenar(avisos, orden)
    return {"total": len(avisos), "skip": skip, "limit": limit, "items": avisos[skip: skip + limit]}


@app.get("/rentabilidad", tags=["estadísticas"])
def rentabilidad(repo: Repo):
    """Rentabilidad bruta anual estimada por comuna y tipo:
    (mediana UF/m² de arriendo mensual × 12) / mediana UF/m² de venta.
    No descuenta gastos, contribuciones ni vacancia."""
    return {"minimo_por_lado": analisis.MIN_REFERENCIA, "filas": analisis.rentabilidad(repo.todos({}))}


@app.get("/resumen", tags=["estadísticas"])
def resumen(
    repo: Repo,
    tipo_operacion: Operacion = "venta",
    tipo_inmueble: Inmueble = "departamento",
):
    """Mediana, p25–p75 y UF/m² por comuna para una operación y tipo."""
    avisos = repo.todos(_filtro(tipo_operacion=tipo_operacion, tipo_inmueble=tipo_inmueble))
    filas = analisis.resumen_por(avisos, ("comuna",))
    validos, excluidos = analisis.limpiar(avisos)
    return {
        "tipo_operacion": tipo_operacion,
        "tipo_inmueble": tipo_inmueble,
        "region": analisis.estadisticas(validos),
        "excluidos": len(excluidos),
        "comunas": filas,
    }


@app.get("/resumen/{comuna}", tags=["estadísticas"])
def resumen_comuna(comuna: str, repo: Repo):
    """Todas las combinaciones operación × tipo de una comuna."""
    avisos = repo.todos({"comuna": comuna})
    if not avisos:
        raise HTTPException(404, f"No hay avisos para la comuna {comuna!r}")
    return {
        "comuna": comuna,
        "grupos": analisis.resumen_por(avisos, ("tipo_operacion", "tipo_inmueble")),
    }


@app.get("/calidad", tags=["estadísticas"])
def calidad(repo: Repo):
    """Cuántos avisos quedan fuera del análisis y por qué."""
    return analisis.calidad(repo.todos({}))
