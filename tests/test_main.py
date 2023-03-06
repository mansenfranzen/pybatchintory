from pybatchintory.main import acquire_batch
from .conftest import META_TABLE_NAME_SCHEMA as META_TABLE


def test_acquire_batch_plain(default_setup, inventory_inspect):
    batch = acquire_batch(meta_table=META_TABLE, job="j1")

    assert batch.id_range.id_min == 5
    assert batch.id_range.id_max == 9
    assert batch.id_range.count == 5
    assert batch.pk == 3
    assert batch.items == [f"f{x}" for x in range(5, 10)]

    row = inventory_inspect(primary_key=3)
    assert row["id"] == 3
    assert row["status"] == "running"
    assert row["attempt"] == 1
    assert row["processing_end"] is None


def test_acquire_batch_release_success(default_setup, inventory_inspect):
    batch = acquire_batch(meta_table=META_TABLE, job="j1")
    batch.release(success=True, logging="FooBar", result={"Foo": "Bar"})

    row = inventory_inspect(primary_key=3)
    assert row["id"] == 3
    assert row["status"] == "succeeded"
    assert row["attempt"] == 1
    assert row["processing_end"] is not None
    assert row["logging"] == "FooBar"
    assert row["job_result_item"] == {"Foo": "Bar"}


def test_acquire_batch_release_failed(default_setup, inventory_inspect):
    batch = acquire_batch(meta_table=META_TABLE, job="j1")
    batch.release(success=False, logging="FooBar", result={"Foo": "Bar"})

    row = inventory_inspect(primary_key=3)
    assert row["id"] == 3
    assert row["status"] == "failed"
    assert row["attempt"] == 1
    assert row["processing_end"] is not None
    assert row["logging"] == "FooBar"
    assert row["job_result_item"] == {"Foo": "Bar"}
