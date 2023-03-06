from typing import Optional

from pybatchintory import config as cfg
from sqlalchemy import Table, Column, Integer, String, DateTime, Enum, \
    JSON, MetaData, func, BigInteger
from sqlalchemy.engine.base import Engine

TS = func.current_timestamp()


def generate_inventory_table(name: str,
                             metadata: MetaData,
                             schema: Optional[str] = None) -> Table:
    return Table(
        name,
        metadata,
        Column('id', BigInteger, primary_key=True),
        Column('meta_table', String, nullable=False),
        Column('job', String, nullable=False),
        Column('job_identifier', String),
        Column('job_result', JSON),
        Column('processing_start', DateTime, nullable=False, default=TS),
        Column('processing_end', DateTime),
        Column('meta_id_start', BigInteger, nullable=False),
        Column('meta_id_end', BigInteger, nullable=False),
        Column('weight', Integer),
        Column('count', Integer, nullable=False),
        Column('attempt', Integer, nullable=False, default=1),
        Column('status',
               Enum(*cfg.settings.INVENTORY_STATUS_ENUMS,
                    name="status_enum"),
               nullable=False,
               default="running"),
        Column('logging', String),
        Column('config', JSON, nullable=False),
        schema=schema,
        sqlite_autoincrement=True
    )


def generate_meta_table(engine: Engine, metadata: MetaData) -> Table:
    return Table(cfg.settings.META_TABLE_NAME,
                 metadata,
                 schema=cfg.settings.META_CONN_SCHEMA,
                 autoload_with=engine)
