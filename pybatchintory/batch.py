from typing import Dict, Optional, List

from pybatchintory import models, sql, config as cfg
from pybatchintory.sql import crud
from sqlalchemy.engine.base import Connection
import sqlalchemy as sa


class Batch:

    def __init__(self,
                 batch_cfg: models.BatchConfig,
                 id_range: models.IdRange):
        self.batch_cfg = batch_cfg
        self.id_range = id_range

        self.pk: Optional[int] = None
        self.items: Optional[List[str]] = None
        self.success: Optional[bool] = None

    def _is_acquirable(self):
        if self.pk is not None:
            raise ValueError("Batch has already been acquired.")

    def _is_releasable(self):
        if self.success is not None:
            raise ValueError("Batch has already been released.")

    def _check_concurrent_change(self, conn: Connection):
        id_inventory_max = crud.read_max_meta_id_from_inventory(
            job=self.batch_cfg.job,
            conn=conn
        )

        if id_inventory_max != self.batch_cfg.id_inventory_max:
            raise NotImplementedError("Concurrent changes are not supported")

    def _build_acquire_values(self) -> Dict:
        return {"job": self.batch_cfg.job,
                "job_identifier": self.batch_cfg.job_identifier,
                "meta_table": cfg.settings.META_TABLE_NAME,
                "meta_id_start": self.id_range.id_min,
                "meta_id_end": self.id_range.id_max,
                "count": self.id_range.count,
                "weight": self.id_range.weight,
                "config": self.batch_cfg.dict()}

    def _acquire_batch_in_inventory(self, conn: Connection):
        values = self._build_acquire_values()
        self.pk = crud.create_row_in_inventory(conn=conn, values=values)

    def acquire(self):
        self._is_acquirable()

        with sql.db.engine_inventory.begin() as conn:
            self._check_concurrent_change(conn)
            self._acquire_batch_in_inventory(conn)

        self.items = crud.read_files_via_id_range_from_meta(
            id_min=self.id_range.id_min,
            id_max=self.id_range.id_max)

    def release(self,
                success: bool,
                result: Optional[Dict] = None,
                logging: Optional[str] = None):
        self._is_releasable()

        self.success = success

        values = {"status": "succeeded" if success else "failed",
                  "job_result": result,
                  "logging": logging,
                  "processing_end": sa.func.current_timestamp()}

        crud.update_row_in_inventory(primary_key=self.pk, values=values)

    def success(self, **kwargs):
        self.release(success=True, **kwargs)

    def error(self, error: Exception, **kwargs):
        if "logging" in kwargs:
            kwargs["logging"] += str(error)
        else:
            kwargs["logging"] = str(error)
        self.release(success=False, **kwargs)
