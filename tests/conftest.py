from typing import Dict

import pandas as pd
import pytest as pytest
from sqlalchemy import create_engine, MetaData, text
import sqlalchemy as sa

from pybatchintory import configure, sql
from pybatchintory.sql.models import generate_inventory_table

META_TABLE_NAME = "test_meta"
META_CONN_SCHEMA = "test_pybatchintory"
INVENTORY_TABLE_NAME = "test_inventory"
INVENTORY_LOGS_TABLE_NAME = "test_inventory_logs"
INVENTORY_CONN_SCHEMA = "test_pybatchintory"


def pytest_addoption(parser):
    parser.addoption(
        "--db",
        action="store",
        default="sqlite",
        help="Choose database backend to test against",
        choices=("sqlite", "postgresql"),
    )


@pytest.fixture(scope="function")
def conn_inventory(pytestconfig, tmp_path):
    if pytestconfig.getoption("db") == "sqlite":
        filename = tmp_path.joinpath("test_backend.db")
        return f"sqlite:///{filename}"
    else:
        raise NotImplementedError


@pytest.fixture(scope="function")
def conn_meta(pytestconfig, tmp_path):
    if pytestconfig.getoption("db") == "sqlite":
        filename = tmp_path.joinpath("test_meta.db")
        return f"sqlite:///{filename}"
    else:
        raise NotImplementedError


@pytest.fixture(scope="function")
def engine_inventory(conn_inventory):
    engine = create_engine(conn_inventory)

    # support schemas in sqlite
    if engine.dialect.name == "sqlite":
        with engine.connect() as conn:
            stmt = text(f"ATTACH ':memory:' AS {INVENTORY_CONN_SCHEMA};")
            conn.execute(stmt)

    return engine


@pytest.fixture(scope="function")
def engine_meta(conn_meta):
    engine = create_engine(conn_meta)

    # support schemas in sqlite
    if engine.dialect.name == "sqlite":
        with engine.begin() as conn:
            stmt = text(f"ATTACH ':memory:' AS {META_CONN_SCHEMA};")
            conn.execute(stmt)

    return engine


@pytest.fixture(scope="function")
def create_inventory_tables_schema(engine_inventory):
    metadata = MetaData()

    generate_inventory_table(
        name=INVENTORY_TABLE_NAME,
        metadata=metadata,
        schema=INVENTORY_CONN_SCHEMA
    )

    metadata.create_all(bind=engine_inventory, checkfirst=True)

    return engine_inventory


@pytest.fixture
def df_meta(engine_meta):
    df_meta = pd.DataFrame({
        "id": range(10),
        "file": [f"f{x}" for x in range(10)],
        "size": range(0, 20, 2)
    })

    df_meta.to_sql(META_TABLE_NAME,
                   con=engine_meta,
                   if_exists="replace",
                   schema=META_CONN_SCHEMA,
                   index=False)
    return df_meta


@pytest.fixture
def df_inventory(create_inventory_tables_schema):
    df_inventory = pd.DataFrame({
        "id": [1, 2],
        "meta_table": ["test_meta", "test_meta"],
        "job": ["j1", "j2"],
        "job_identifier": ["j1_1", "j2_1"],
        "job_result": ["{file: 1}", "{file: 2}"],
        "processing_start": [pd.Timestamp("2023-01-01 10:00:00"),
                             pd.Timestamp("2023-01-01 12:00:00")],
        "processing_end": [pd.Timestamp("2023-01-01 11:00:00"),
                           pd.Timestamp("2023-01-01 13:00:00")],
        "meta_id_start": [0, 5],
        "meta_id_end": [4, 8],
        "weight": [8, 23],
        "count": [5, 4],
        "attempt": [1, 1],
        "status": ["succeeded", "running"],
        "config": ['{"foo": "bar"}', '{"bar": "foo"}'],
        "logging": ["log1", "log2"]
    })

    df_inventory.to_sql(INVENTORY_TABLE_NAME,
                        schema=INVENTORY_CONN_SCHEMA,
                        con=create_inventory_tables_schema,
                        if_exists="append",
                        index=False)

    return df_inventory


@pytest.fixture
def configuration(engine_inventory, engine_meta, conn_inventory, conn_meta):
    configure(
        settings=dict(
            INVENTORY_CONN=conn_inventory,
            INVENTORY_CONN_SCHEMA=INVENTORY_CONN_SCHEMA,
            INVENTORY_TABLE_NAME=INVENTORY_TABLE_NAME,
            META_CONN=conn_meta,
            META_CONN_SCHEMA=META_CONN_SCHEMA,
            META_TABLE_NAME=META_TABLE_NAME,
            META_COLS={"uid": "id", "file": "file", "weight": "size"},
        ),
        initialize_db=False
    )

    sql.db = sql.initialize(engine_inventory=engine_inventory,
                            engine_meta=engine_meta)


@pytest.fixture
def default_setup(df_meta, df_inventory, configuration):
    """Helper fixture to invoke parent fixtures in correct order to provide
    proper test setup."""
    pass


@pytest.fixture
def inventory_inspect(engine_inventory):
    """Helper function to retrieve values from inventory table.

    """

    def read(primary_key: int) -> Dict:
        t_inventory = sql.db.table_inventory
        c_id = t_inventory.c["id"]
        stmt = sa.select(sql.db.table_inventory).where(c_id == primary_key)
        with engine_inventory.begin() as conn:
            return conn.execute(stmt).fetchone()._asdict()

    return read
