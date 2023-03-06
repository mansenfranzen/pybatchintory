import functools

from sqlalchemy import Table, MetaData

from pybatchintory import sql


@functools.lru_cache(maxsize=128)
def autoload_meta_table(name: str) -> Table:
    """Loads schema for meta table from database.

    """

    if "." in name:
        schema, name = name.split(".")
    else:
        schema = None

    engine = sql.db.engine_meta
    return Table(name, MetaData(), schema=schema, autoload_with=engine)
