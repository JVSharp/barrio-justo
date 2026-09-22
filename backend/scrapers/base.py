from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timezone

import config


class BaseScraper(ABC):
    """Guarda avisos en MongoDB, uno por URL.

    Si el aviso ya existe se actualizan precio y datos, y se registra la
    fecha en que se vio por última vez. `fecha_primera_vista` no se toca:
    con eso se puede medir cuánto tiempo lleva publicado un aviso.
    """

    fuente = "generica"

    def __init__(self, cfg: config.Config | None = None):
        from pymongo import ASCENDING, MongoClient

        cfg = cfg or config.cargar()
        self.col = MongoClient(cfg.mongo_uri)[cfg.mongo_db][cfg.mongo_coleccion]
        self.col.create_index([("url", ASCENDING)], unique=True)
        self.nuevos = 0
        self.actualizados = 0

    @abstractmethod
    def scrape(self) -> None: ...

    def guardar(self, aviso: dict) -> None:
        if not aviso.get("url"):
            return
        ahora = datetime.now(timezone.utc).isoformat(timespec="seconds")
        aviso = {**aviso, "fuente": self.fuente, "fecha_ultima_vista": ahora}
        r = self.col.update_one(
            {"url": aviso["url"]},
            {"$set": aviso, "$setOnInsert": {"fecha_primera_vista": ahora}},
            upsert=True,
        )
        if r.upserted_id is not None:
            self.nuevos += 1
        else:
            self.actualizados += 1
