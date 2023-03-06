from pybatchintory.sql.crud import read_meta_id_range_from_meta
from ..conftest import META_TABLE_NAME_SCHEMA as META_TABLE

def test_get_meta_id_range_from_meta_bounded_backfill_no_constraints(
        default_setup):
    id_range = read_meta_id_range_from_meta(
        meta_table=META_TABLE,
        id_min=2,
        id_max=4
    )

    assert id_range.id_min == 2
    assert id_range.id_max == 4
    assert id_range.count == 3
    assert id_range.weight == 18


def test_get_meta_id_range_from_meta_unbounded_backfill_no_constraints(
        default_setup):
    id_range = read_meta_id_range_from_meta(
        meta_table=META_TABLE,
        id_min=0,
        id_max=4
    )

    assert id_range.id_min == 0
    assert id_range.id_max == 4
    assert id_range.count == 5
    assert id_range.weight == 20


def test_get_meta_id_range_from_meta_bounded_incremental_no_constraints(
        default_setup):
    id_range = read_meta_id_range_from_meta(
        meta_table=META_TABLE,
        id_min=8,
    )

    assert id_range.id_min == 8
    assert id_range.id_max == 9
    assert id_range.count == 2
    assert id_range.weight == 34


def test_get_meta_id_range_from_meta_unbounded_incremental_no_constraints(
        default_setup):
    id_range = read_meta_id_range_from_meta(
        meta_table=META_TABLE,
        id_min=0,
    )

    assert id_range.id_min == 0
    assert id_range.id_max == 9
    assert id_range.count == 10
    assert id_range.weight == 90


def test_get_meta_id_range_from_meta_weight_constraint_without_remainder(
        default_setup):
    id_range = read_meta_id_range_from_meta(
        meta_table=META_TABLE,
        id_min=0,
        weight=12
    )

    assert id_range.id_min == 0
    assert id_range.id_max == 3
    assert id_range.count == 4
    assert id_range.weight == 12


def test_get_meta_id_range_from_meta_weight_constraint_with_remainder(
        default_setup):
    id_range = read_meta_id_range_from_meta(
        meta_table=META_TABLE,
        id_min=0,
        weight=7
    )

    assert id_range.id_min == 0
    assert id_range.id_max == 2
    assert id_range.count == 3
    assert id_range.weight == 6


def test_get_meta_id_range_from_meta_count_constraint(default_setup):
    id_range = read_meta_id_range_from_meta(
        meta_table=META_TABLE,
        id_min=0,
        count=2
    )

    assert id_range.id_min == 0
    assert id_range.id_max == 1
    assert id_range.count == 2
    assert id_range.weight == 2


def test_get_meta_id_range_from_meta_count_overrules_weight_constraint(
        default_setup):
    id_range = read_meta_id_range_from_meta(
        meta_table=META_TABLE,
        id_min=0,
        count=2,
        weight=20
    )

    assert id_range.id_min == 0
    assert id_range.id_max == 1
    assert id_range.count == 2
    assert id_range.weight == 2


def test_get_meta_id_range_from_meta_weight_overrules_count_constraint(
        default_setup):
    id_range = read_meta_id_range_from_meta(
        meta_table=META_TABLE,
        id_min=0,
        count=10,
        weight=30
    )

    assert id_range.id_min == 0
    assert id_range.id_max == 5
    assert id_range.count == 6
    assert id_range.weight == 30


def test_get_meta_id_range_from_meta_weight_constraint_not_realizable(
        default_setup):
    id_range = read_meta_id_range_from_meta(
        meta_table=META_TABLE,
        id_min=5,
        weight=5
    )

    assert id_range.id_min == 5
    assert id_range.id_max == 5
    assert id_range.count == 1
    assert id_range.weight == 10
