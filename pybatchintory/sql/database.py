from typing import Optional

from pydantic.main import BaseModel
from sqlalchemy.engine.base import Engine
from sqlalchemy import create_engine, MetaData, Table

from pybatchintory import config as cfg
from pybatchintory.sql.models import generate_inventory_table


class DatabaseConfiguration(BaseModel):
    engine_inventory: Engine
    engine_meta: Engine
    metadata_inventory: MetaData
    metadata_meta: MetaData
    table_inventory: Table

    def initialize_metadata_backend(self):
        self.metadata_inventory.create_all(bind=self.engine_inventory,
                                           checkfirst=True)

    class Config:
        arbitrary_types_allowed = True


def initialize(engine_inventory: Optional[Engine] = None,
               engine_meta: Optional[Engine] = None) -> DatabaseConfiguration:
    metadata_inventory = MetaData()
    metadata_meta = MetaData()

    engine_inventory = engine_inventory or get_engine_inventory()
    engine_meta = engine_meta or get_engine_meta()

    table_inventory = generate_inventory_table(
        name=cfg.settings.INVENTORY_TABLE_NAME,
        metadata=metadata_inventory,
        schema=cfg.settings.INVENTORY_CONN_SCHEMA
    )

    return DatabaseConfiguration(
        engine_inventory=engine_inventory,
        engine_meta=engine_meta,
        metadata_inventory=metadata_inventory,
        metadata_meta=metadata_meta,
        table_inventory=table_inventory,
    )


def get_engine_inventory() -> Engine:
    """Provides SQLAlchemy engine for inventory table.

    """

    return create_engine(url=cfg.settings.INVENTORY_CONN.get_secret_value(),
                         echo=cfg.settings.DEBUG)


def get_engine_meta() -> Engine:
    """Provides SQLAlchemy engine for meta table.

    Uses inventory engine as fallback if not `CONN_META` is not set.
    """

    if cfg.settings.META_CONN:
        return create_engine(url=cfg.settings.META_CONN.get_secret_value(),
                             echo=cfg.settings.DEBUG)

    return get_engine_inventory()
