from typing import Optional, Dict

from pybatchintory.batch import Batch
from pybatchintory.models import BatchConfig, MetaTableSpec
from pybatchintory.sql import crud
from pybatchintory import validate


def acquire_batch(job: str,
                  meta_table_name: str,
                  meta_table_cols: Optional[Dict[str, str]] = None,
                  job_identifier: Optional[str] = None,
                  batch_id_min: int = 0,
                  batch_id_max: Optional[int] = None,
                  batch_weight: Optional[float] = None,
                  batch_count: Optional[int] = None) -> Optional[Batch]:

    meta_table_cols = meta_table_cols or {}
    meta_table = MetaTableSpec(name=meta_table_name, cols=meta_table_cols)

    id_inventory_max = crud.read_max_meta_id_from_inventory(
        meta_table=meta_table,
        job=job
    )
    id_meta_max = crud.read_max_meta_id_from_meta(meta_table=meta_table)

    checks = [
        validate.id_min_greater_equals_max_meta_id(
            id_user_min=batch_id_min,
            id_meta_max=id_meta_max),
        validate.max_inventory_id_greater_equals_max_meta_id(
            id_inventory_max=id_inventory_max,
            id_meta_max=id_meta_max)
    ]

    if any(checks):
        return

    batch_id_min = max(batch_id_min, id_inventory_max + 1)
    batch_id_range = crud.read_meta_id_range_from_meta(
        meta_table=meta_table,
        id_min=batch_id_min,
        id_max=batch_id_max,
        count=batch_count,
        weight=batch_weight
    )

    batch_cfg = BatchConfig(
        meta_table=meta_table,
        job=job,
        job_identifier=job_identifier,
        id_min=batch_id_min,
        id_max=batch_id_max,
        batch_weight=batch_weight,
        batch_count=batch_count,
        id_inventory_max=id_inventory_max,
        id_meta_max=id_meta_max
    )

    batch = Batch(id_range=batch_id_range, batch_cfg=batch_cfg)
    batch.acquire()
    return batch
