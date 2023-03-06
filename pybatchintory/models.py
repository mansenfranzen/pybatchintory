from typing import Optional

from pydantic.main import BaseModel


class IdRange(BaseModel):
    """Resembles the computed item id range which
    constitutes a batch of data items.

    """

    id_min: int
    id_max: int
    count: int
    weight: Optional[float]

    class Config:
        orm_mode = True


class BatchConfig(BaseModel):
    """Resembles config with which a batch is acquired.

    """

    meta_table: str
    job: str
    job_identifier: Optional[str]
    id_min: int = 0
    id_max: Optional[int] = None
    batch_weight: Optional[float] = None
    batch_count: Optional[int] = None
    id_inventory_max: int
    id_meta_max: int
