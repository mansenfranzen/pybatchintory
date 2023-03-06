from typing import Dict

import pandas as pd
import pytest
from sqlalchemy import create_engine, MetaData, text, schema, Table
import sqlalchemy as sa

from pybatchintory import configure, sql
from pybatchintory.sql.models import generate_inventory_table

from . import test_data

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
    db_param = pytestconfig.getoption("db")
    if db_param == "sqlite":
        filename = tmp_path.joinpath("test_backend.db")
        return f"sqlite:///{filename}"
    elif db_param == "postgresql":
        return "postgresql+psycopg2://postgres:postgres@localhost:5432/postgres"
    else:
        raise NotImplementedError


@pytest.fixture(scope="function")
def conn_meta(pytestconfig, tmp_path):
    db_param = pytestconfig.getoption("db")
    if db_param == "sqlite":
        filename = tmp_path.joinpath("test_meta.db")
        return f"sqlite:///{filename}"
    elif db_param == "postgresql":
        return "postgresql+psycopg2://docker:docker@localhost:5432/docker"
    else:
        raise NotImplementedError


def recreate_inventory_table(engine_inventory):
    """Removes existing table and creates new inventory table.

    """

    metadata = MetaData()

    generate_inventory_table(
        name=INVENTORY_TABLE_NAME,
        metadata=metadata,
        schema=INVENTORY_CONN_SCHEMA
    )

    metadata.drop_all(bind=engine_inventory)
    metadata.create_all(bind=engine_inventory, checkfirst=True)


@pytest.fixture(scope="function")
def engine_inventory(conn_inventory):
    """Create engine and create schema/tables if not exist.

    """

    engine = create_engine(conn_inventory)

    # support schemas in sqlite
    if engine.dialect.name == "sqlite":
        with engine.connect() as conn:
            stmt = text(f"ATTACH ':memory:' AS {INVENTORY_CONN_SCHEMA};")
            conn.execute(stmt)

    else:
        with engine.begin() as conn:
            if not conn.dialect.has_schema(conn, INVENTORY_CONN_SCHEMA):
                conn.execute(schema.CreateSchema(INVENTORY_CONN_SCHEMA))

    recreate_inventory_table(engine)

    return engine


@pytest.fixture(scope="function")
def engine_meta(conn_meta):
    """Create engine and create schema if not exist.

    """

    engine = create_engine(conn_meta)

    if engine.dialect.name == "sqlite":
        with engine.begin() as conn:
            stmt = text(f"ATTACH ':memory:' AS {META_CONN_SCHEMA};")
            conn.execute(stmt)
    else:
        with engine.begin() as conn:
            if not conn.dialect.has_schema(conn, META_CONN_SCHEMA):
                conn.execute(schema.CreateSchema(META_CONN_SCHEMA))

    return engine


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
def df_inventory(engine_inventory):
    table = Table(INVENTORY_TABLE_NAME,
                  MetaData(),
                  schema=INVENTORY_CONN_SCHEMA,
                  autoload_with=engine_inventory)

    with engine_inventory.begin() as conn:
        conn.execute(sa.insert(table), test_data.INVENTORY)

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
