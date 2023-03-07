from typing import Optional

from pybatchintory import config as cfg
from sqlalchemy import Table, Column, Integer, String, DateTime, Enum, \
    JSON, MetaData, func, BigInteger, Float

from pybatchintory.models import MetaTableColumns

TS = func.current_timestamp()


def generate_inventory_table(name: str,
                             metadata: MetaData,
                             schema: Optional[str] = None) -> Table:
    return Table(
        name,
        metadata,
        Column('id',
               BigInteger().with_variant(Integer, "sqlite"),
               primary_key=True),
        Column('meta_table', String, nullable=False),
        Column('job', String, nullable=False),
        Column('job_identifier', String),
        Column('job_result_item', JSON),
        Column('processing_start', DateTime, nullable=False, default=TS),
        Column('processing_end', DateTime),
        Column('batch_id_start', BigInteger, nullable=False),
        Column('batch_id_end', BigInteger, nullable=False),
        Column('batch_weight', Integer),
        Column('batch_count', Integer, nullable=False),
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

def generate_meta_table(name: str,
                        metadata: MetaData,
                        schema: Optional[str] = None) -> Table:

    default_cols = MetaTableColumns()

    return Table(name,
                 metadata,
                 Column(default_cols.uid,
                        BigInteger().with_variant(Integer, "sqlite"),
                        primary_key=True),
                 Column(default_cols.item, String, nullable=False),
                 Column(default_cols.weight, Float),
                 schema=schema,
                 sqlite_autoincrement=True)
