from typing import Optional

from sqlalchemy.engine.base import Engine
from sqlalchemy import Table, MetaData

from pybatchintory.sql.models import generate_inventory_table, \
    generate_meta_table


def _recreate_table(func, engine, name, schema) -> Table:
    metadata = MetaData()

    table = func(
        name=name,
        metadata=metadata,
        schema=schema
    )

    table.drop(bind=engine, checkfirst=True)
    table.create(bind=engine, checkfirst=True)

    return table


def recreate_inventory_table(engine: Engine,
                             name: str,
                             schema: Optional[str]) -> Table:
    """Removes existing table and creates new inventory table.

    """

    return _recreate_table(func=generate_inventory_table,
                           engine=engine,
                           name=name,
                           schema=schema)


def recreate_meta_table(engine: Engine,
                        name: str,
                        schema: Optional[str]) -> Table:
    """Removes existing table and creates new inventory table.

    """

    return _recreate_table(func=generate_meta_table,
                           engine=engine,
                           name=name,
                           schema=schema)
