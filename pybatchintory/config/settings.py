from typing import Optional, List

from pydantic import BaseSettings
from pydantic.main import BaseModel
from pydantic.types import SecretStr


class MetaTableColumns(BaseModel):
    """Stores the relevant column names of the meta data table.

    """

    uid: str = "uid"
    item: str = "item"
    weight: Optional[str] = None


class Settings(BaseSettings):
    """Defines all package wide configurations.

    """

    INVENTORY_CONN: SecretStr
    """Represents SqlAlchemy connection string for the inventory backend 
    tables used by `pybatchintory` with read/write access."""

    INVENTORY_CONN_SCHEMA: Optional[str]
    """Provide schema for backend table."""

    INVENTORY_TABLE_NAME: str = "inventory"
    """Name of the inventory table."""

    INVENTORY_STATUS_ENUMS: List[str] = ['running', 'succeeded', 'failed']
    """Possible states of an inventory row."""

    META_CONN: Optional[SecretStr] = None
    """Represents SqlAlchemy connection string for the meta tables which
    are external to `pybatchintory` with read only access. If not given, is 
    assumes it has the same connection string as `CONN_BACKEND`."""

    META_CONN_SCHEMA: Optional[str]
    """Provide schema for meta table."""

    META_TABLE_NAME: str
    """Name of meta data table."""

    META_COLS: MetaTableColumns = MetaTableColumns()
    """Define the column name mappings for the meta data table."""

    DEBUG: bool = False
    """Enable debug mode to see more information such as generated SQL strings.
    """


