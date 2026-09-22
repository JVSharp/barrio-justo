from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timezone

import config


class BaseScraper(ABC):
    """Guarda avisos en MongoDB, uno por URL.

    - Aviso nuevo: se inserta con `fecha_primera_vista` y un historial de
      precio con un solo punto.
    - Aviso conocido: se actualizan sus datos y `fecha_ultima_vista`. Si el
      precio cambió, se agrega un punto a `historial_precios`; si no, el
      historial no se toca. Así se puede ver qué avisos bajaron de precio y
      cuánto tiempo llevan publicados.
    """

    fuente = "generica"

    def __init__(self, cfg: config.Config | None = None, coleccion=None):
        if coleccion is not None:          # inyectable en tests
            self.col = coleccion
        else:
            from pymongo import ASCENDING, MongoClient

            cfg = cfg or config.cargar()
            self.col = MongoClient(cfg.mongo_uri)[cfg.mongo_db][cfg.mongo_coleccion]
            self.col.create_index([("url", ASCENDING)], unique=True)
        self.nuevos = 0
        self.actualizados = 0
        self.cambios_de_precio = 0

    @abstractmethod
    def scrape(self) -> None: ...

    def guardar(self, aviso: dict) -> None:
        if not aviso.get("url"):
            return
        ahora = datetime.now(timezone.utc).isoformat(timespec="seconds")
        aviso = {**aviso, "fuente": self.fuente, "fecha_ultima_vista": ahora}
        punto = {"fecha": ahora, "precio_uf": aviso.get("precio_uf")}

        previo = self.col.find_one({"url": aviso["url"]},
                                   {"precio_uf": 1, "historial_precios": 1, "fecha_ultima_vista": 1})
        if previo is None:
            self.col.insert_one({**aviso, "fecha_primera_vista": ahora, "historial_precios": [punto]})
            self.nuevos += 1
            return

        cambios: dict = {"$set": aviso}
        historial = previo.get("historial_precios")
        if historial is None:
            # Aviso guardado antes de v3: se siembra el historial con el precio conocido.
            historial = [{"fecha": previo.get("fecha_ultima_vista") or ahora,
                          "precio_uf": previo.get("precio_uf")}]
            cambios["$set"] = {**aviso, "historial_precios": historial}
        if historial and historial[-1].get("precio_uf") != aviso.get("precio_uf"):
            if "historial_precios" in cambios["$set"]:
                cambios["$set"]["historial_precios"] = historial + [punto]
            else:
                cambios["$push"] = {"historial_precios": punto}
            self.cambios_de_precio += 1
        self.col.update_one({"url": aviso["url"]}, cambios)
        self.actualizados += 1
