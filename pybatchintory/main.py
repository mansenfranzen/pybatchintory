from typing import Optional, Dict

from pybatchintory.batch import Batch
from pybatchintory.models import BatchConfig, MetaTableSpec
from pybatchintory.sql import crud
from pybatchintory import validate


def acquire_batch(job: str,
                  meta_table_name: str,
                  meta_table_cols: Optional[Dict[str, str]] = None,
                  job_identifier: Optional[str] = None,
                  batch_id_min: Optional[int] = None,
                  batch_id_max: Optional[int] = None,
                  batch_weight: Optional[float] = None,
                  batch_count: Optional[int] = None) -> Optional[Batch]:
    """Factory function to instantiate a `Batch` including validation rules
    to prevent invalid batch configurations.

    Parameters
    ----------
    job: str
        Name of the job that operates on a given `meta_table_name`. This serves
        as an identifier for a specific configuration such as
        `incremental_10gb` or `backfill_2023_50gb`. Subsequent jobs with the
        same name will not reprocess the same data but will continue where the
        former has finished.
    meta_table_name:
        Name of the meta data table containing information about the actual
        data items.
    meta_table_cols: dict, optional
        Specify the relevant columns `uid`, `item` and `weight` of the
        meta data table as an dictionary where keys correspond to the column
        and values to the name of the column.
    job_identifier: str, optional
        Unlike `job`, this is corresponds to a unique job id which even
        separates among tasks of the same job.
    batch_id_min: int, optional
        Define the lower batch boundary by providing the minimum valid id of
        the meta data table.
    batch_id_max: int, optional
        Define the upper batch boundary by providing the maximum valid id of
        the meta data table.
    batch_weight: float, optional
        Define the maximum weight allowed to be included in a batch.
    batch_count: int, optional
        Define the maximum number of items to be included in a batch.

    Returns
    -------
    acquired_batch: Batch

    """

    meta_table_cols = meta_table_cols or {}
    meta_table = MetaTableSpec(name=meta_table_name, cols=meta_table_cols)
    id_user_min = batch_id_min if batch_id_min is not None else float("-inf")

    id_inventory_max = crud.read_max_meta_id_from_inventory(
        meta_table=meta_table,
        job=job
    )
    id_meta_max = crud.read_max_meta_id_from_meta(meta_table=meta_table)

    if validate.acquire_batch_is_invalid(id_user_min=id_user_min,
                                         id_meta_max=id_meta_max,
                                         id_inventory_max=id_inventory_max):
        return

    checked_id_min = max(id_user_min, id_inventory_max + 1)
    batch_id_range = crud.read_meta_id_range_from_meta(
        meta_table=meta_table,
        id_min=checked_id_min,
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
