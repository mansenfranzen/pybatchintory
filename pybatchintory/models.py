from typing import Optional

from pydantic.main import BaseModel


class BatchIdRange(BaseModel):
    """Resembles the computed item id range which constitutes a batch of
    data items.

    """

    id_min: int
    id_max: int
    count: int
    weight: Optional[float]

    class Config:
        orm_mode = True


class MetaTableColumns(BaseModel):
    """Stores the relevant column names of the meta data table.

    """

    uid: str = "uid"
    item: str = "item"
    weight: Optional[str] = "weight"


class MetaTableSpec(BaseModel):
    """Represents the configuration for the meta data table.

    """

    name: str
    cols: MetaTableColumns = MetaTableColumns()


class BatchConfig(BaseModel):
    """Resembles config with which a batch is acquired.

    """

    meta_table: MetaTableSpec
    job: str
    job_identifier: Optional[str]
    batch_id_min: int = 0
    batch_id_max: Optional[int] = None
    batch_weight: Optional[float] = None
    batch_count: Optional[int] = None
    id_inventory_max: int
    id_meta_max: int
