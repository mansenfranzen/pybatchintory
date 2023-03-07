from typing import Optional, Dict, List

import sqlalchemy as sa
from sqlalchemy.engine.base import Connection
from sqlalchemy.sql.selectable import CTE

from pybatchintory import sql
from pybatchintory.sql import helper
from pybatchintory.logging import logger
from pybatchintory.models import BatchIdRange, MetaTableSpec
from pybatchintory.sql.reflection import autoload_meta_table


def read_max_meta_id_from_inventory(meta_table: MetaTableSpec,
                                    job: str,
                                    conn: Optional[Connection] = None) -> int:
    """Given a job, retrieve the highest item id that has been previously
    processed.

    """

    inventory = sql.db.table_inventory

    # select
    max_val = sa.func.max(inventory.c.batch_id_end)
    value_or_zero = sa.func.coalesce(max_val, 0)

    # where
    where = sa.and_(inventory.c.meta_table == meta_table.name,
                    inventory.c.job == job)

    # query
    stmt = sa.select(value_or_zero).where(where)

    # support as part of transaction or separate transaction
    if conn:
        max_meta_id = conn.execute(stmt).scalar()
    else:
        with sql.db.engine_inventory.begin() as conn:
            max_meta_id = conn.execute(stmt).scalar()

    logger.info(f"max_meta_id_from_inventory: {max_meta_id}")
    return max_meta_id


def read_max_meta_id_from_meta(meta_table: MetaTableSpec) -> int:
    """Retrieve the highest item id from meta table.

    """

    t_meta = autoload_meta_table(meta_table.name)
    c_id = t_meta.c[meta_table.cols.uid]

    # select
    max_val = sa.func.max(c_id)
    value_or_zero = sa.func.coalesce(max_val, 0)

    # query
    stmt = sa.select(value_or_zero)

    with sql.db.engine_meta.begin() as conn:
        max_meta_id = conn.execute(stmt).scalar()

    logger.info(f"max_meta_id_from_meta: {max_meta_id}")
    return max_meta_id


def _build_meta_id_base_cte(meta_table: MetaTableSpec,
                            id_min: int,
                            id_max: Optional[int] = None) -> CTE:
    """Build CTE for meta ia base information regarding rank and cumulative
    sum for weight.

    """
    # get table/column objects for meta table
    t_meta = autoload_meta_table(meta_table.name)
    c_id = t_meta.c[meta_table.cols.uid]
    weight_col = meta_table.cols.weight

    # select
    select = [c_id.label("id"),
              sa.func.rank().over(order_by=c_id).label("count")]

    if weight_col:
        c_wei = t_meta.c[weight_col]
        select.append(sa.func.sum(c_wei).over(order_by=c_id).label("weight"))
    else:
        select.append(sa.null().label("weight"))

    # where
    where = [c_id >= id_min]
    if id_max:
        where.append(c_id <= id_max)

    # common table expression / subquery
    return sa.select(*select).where(sa.and_(*where)).order_by(c_id).cte("cte")


def read_meta_id_range_from_meta(
        meta_table: MetaTableSpec,
        id_min: int,
        id_max: Optional[int] = None,
        weight: Optional[float] = None,
        count: Optional[int] = None
) -> BatchIdRange:
    """Retrieve a range of meta ids.

    """

    # common table expression / subquery
    cte = _build_meta_id_base_cte(meta_table=meta_table,
                                  id_min=id_min,
                                  id_max=id_max)

    # cte where
    cte_where = []
    if weight and meta_table.cols.weight:
        cte_where.append(cte.c.weight <= weight)
    if count:
        cte_where.append(cte.c.count <= count)

    cte_query = (
        sa.select(
            sa.func.min(cte.c.id).label("id_min"),
            sa.func.max(cte.c.id).label("id_max"),
            sa.func.max(cte.c.count).label("count"),
            sa.func.max(cte.c.weight).label("weight")
        )
        .where(sa.and_(*cte_where))
        .select_from(cte)
    )

    with sql.db.engine_meta.begin() as conn:
        result = conn.execute(cte_query).fetchone()

    # check for edge case of empty result set
    if any(result):
        return BatchIdRange(**result._asdict())
    else:
        return _read_single_next_id_from_meta(meta_table, id_min)


def _read_single_next_id_from_meta(meta_table: MetaTableSpec,
                                   id_min: int) -> BatchIdRange:
    """Fallback if weight constraint does not even allow a single data item
    to be returned.

    """

    t_meta = autoload_meta_table(meta_table.name)
    c_id = t_meta.c[meta_table.cols.uid]
    weight_col = meta_table.cols.weight

    filter_subquery = sa.select(sa.func.min(c_id)).where(c_id >= id_min)

    select = [c_id.label("id_min"),
              c_id.label("id_max"),
              sa.literal(1).label("count")]
    if weight_col:
        select.append(t_meta.c[weight_col].label("weight"))
    else:
        select.append(sa.null().label("weight"))

    query = sa.select(*select).where(c_id.in_(filter_subquery))
    with sql.db.engine_meta.begin() as conn:
        result = conn.execute(query).fetchone()
        return BatchIdRange(**result._asdict())


def create_row_in_inventory(values: Dict, conn: Connection) -> int:
    """Inserts new row in inventory table while returning the resulting primary
    key.

    """

    stmt = sa.insert(sql.db.table_inventory).values(values)
    result = conn.execute(stmt)
    return result.inserted_primary_key[0]


def update_row_in_inventory(primary_key: int, values: Dict):
    """Updates row in inventory table given primary key.

    """

    t_inventory = sql.db.table_inventory
    c_id = t_inventory.c.id

    stmt = sa.update(t_inventory).where(c_id == primary_key).values(values)
    with sql.db.engine_inventory.begin() as conn:
        conn.execute(stmt)


def read_items_via_id_range_from_meta(meta_table: MetaTableSpec,
                                      id_min: int,
                                      id_max: int) -> List[str]:
    """Loads items from meta table for given id range.

    """

    t_meta = autoload_meta_table(meta_table.name)
    c_id = t_meta.c[meta_table.cols.uid]
    c_item = t_meta.c[meta_table.cols.item]

    where = sa.and_(c_id >= id_min, c_id <= id_max)
    stmt = sa.select(c_item).where(where)
    with sql.db.engine_meta.begin() as conn:
        result = conn.execute(stmt).fetchall()
        return helper.single_column_result_to_list(result)
