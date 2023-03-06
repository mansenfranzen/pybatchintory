from typing import Dict

import pandas as pd
import pytest
from packaging import version
from sqlalchemy import create_engine, text
import sqlalchemy as sa

from pybatchintory import configure, sql
from pybatchintory.sql.testing import recreate_inventory_table, \
    recreate_meta_table

from . import test_data

SCHEMA = "test_pybatchintory"
META_TABLE_NAME = "test_meta"
META_TABLE_NAME_SCHEMA = f"{SCHEMA}.{META_TABLE_NAME}"
INVENTORY_TABLE_NAME = "test_inventory"
INVENTORY_LOGS_TABLE_NAME = "test_inventory_logs"

POSTGRESQL_URL = "postgresql+psycopg2://postgres:postgres@localhost:5432/postgres"


def pytest_addoption(parser):
    parser.addoption(
        "--db",
        action="store",
        default="sqlite",
        help="Choose database backend to test against",
        choices=("sqlite", "postgresql"),
    )


@pytest.fixture
def schema(pytestconfig):
    """Using seperate test schema does not work with the combination of sqlite
    and sqlalchemy. Hence, it needs to be handled separately.

    """
    sqlite_used = pytestconfig.getoption("db") == "sqlite"
    incompatible_sa = version.parse(sa.__version__) < version.Version("2.0.0")

    if sqlite_used and incompatible_sa:
        return None
    else:
        return "test_pybatchintory"


@pytest.fixture
def meta_table(schema):
    if schema:
        return META_TABLE_NAME_SCHEMA
    else:
        return META_TABLE_NAME


@pytest.fixture(scope="function")
def conn_inventory(pytestconfig, tmp_path):
    db_param = pytestconfig.getoption("db")
    if db_param == "sqlite":
        filename = tmp_path.joinpath("test_backend.db")
        return f"sqlite:///{filename}"
    elif db_param == "postgresql":
        return POSTGRESQL_URL
    else:
        raise NotImplementedError


@pytest.fixture(scope="function")
def conn_meta(pytestconfig, tmp_path):
    db_param = pytestconfig.getoption("db")
    if db_param == "sqlite":
        filename = tmp_path.joinpath("test_meta.db")
        return f"sqlite:///{filename}"
    elif db_param == "postgresql":
        return POSTGRESQL_URL
    else:
        raise NotImplementedError


@pytest.fixture(scope="function")
def engine_inventory(schema, conn_inventory):
    """Create engine and create schema/tables if not exist.

    """

    engine = create_engine(conn_inventory)

    # support schemas in sqlite
    if engine.dialect.name == "sqlite":
        if schema:
            with engine.begin() as conn:
                stmt = text(f"ATTACH ':memory:' AS {schema};")
                conn.execute(stmt)

    else:
        with engine.begin() as conn:
            if not conn.dialect.has_schema(conn, schema):
                conn.execute(sa.schema.CreateSchema(schema))

    return engine


@pytest.fixture(scope="function")
def engine_meta(schema, conn_meta):
    """Create engine and create schema if not exist.

    """

    engine = create_engine(conn_meta)

    if engine.dialect.name == "sqlite":
        if schema:
            with engine.begin() as conn:
                stmt = text(f"ATTACH ':memory:' AS {schema};")
                conn.execute(stmt)
    else:
        with engine.begin() as conn:
            if not conn.dialect.has_schema(conn, schema):
                conn.execute(sa.schema.CreateSchema(schema))

    return engine


@pytest.fixture
def df_meta(schema, engine_meta):
    table = recreate_meta_table(name=META_TABLE_NAME,
                                engine=engine_meta,
                                schema=schema)

    with engine_meta.begin() as conn:
        conn.execute(sa.insert(table), test_data.META)

    return pd.DataFrame(test_data.META)


@pytest.fixture
def df_inventory(schema, meta_table, engine_inventory):
    table = recreate_inventory_table(name=INVENTORY_TABLE_NAME,
                                     engine=engine_inventory,
                                     schema=schema)
    test_data_inventory = test_data.inventory_data(meta_table)
    with engine_inventory.begin() as conn:
        conn.execute(sa.insert(table), test_data_inventory)

    return pd.DataFrame(test_data_inventory)


@pytest.fixture
def configuration(schema,
                  engine_inventory,
                  engine_meta,
                  conn_inventory,
                  conn_meta):
    configure(
        settings=dict(
            INVENTORY_CONN=conn_inventory,
            INVENTORY_CONN_SCHEMA=schema,
            INVENTORY_TABLE_NAME=INVENTORY_TABLE_NAME,
            META_CONN=conn_meta,
            META_CONN_SCHEMA=schema,
            META_TABLE_NAME=META_TABLE_NAME,
            META_COLS={"uid": "id", "item": "item", "weight": "weight"},
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
