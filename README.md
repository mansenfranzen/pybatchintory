# pybatchintory

`pybatchintory` represents a middleware for generating batches of data items. It enables incremental processing and provides first class support for reprocessing historical data with predictable workloads. 

It consumes only the meta information of data items. It does not read any of the data itself. Instead, it manages an inventory of already processed and unseen data while providing an API to interact with it.

## Reasoning

This package may greatly improve data pipelines by enabling the following four features:

- **Incremental processing**: Only new, unseen data items can be processed, avoiding recomputation of all data items.
- **Backfill scenarios**: Historical data items can be reprocessed in a configurable and automated way.
- **Predictable workloads**: The amount of data to be processed can be defined and is known upfront to adjust compute resources accordingly for best efficiency and cost/performance ratio for both incremental processing and backfill scenarios.
- **Transparency and observability**: Each data item can be enriched with information about when it was processed by what job.

## Preconditions

`pybatchintory` assumes the existence of a metadata table that contains information about the data items, such as their file location and registration timestamps. Importantly, to properly generate ranges of data items constituting a single batch to be processed, `pybatchintory` requires the metadata table to provide a unique auto-increment ID column.

## Examplary usage

### Single batch - incremental/backfill with weight

```python

from pybatchintory import acquire_batch

# incremental
batch = acquire_batch(source_table="meta_data_raw_data", job_identifer="incremental_job", weight=10)
process_func(batch.items)
batch.success()

# backfill
batch = acquire_batch(source_table="meta_data_raw_data", job_identifer="backfill_job", id_start=10, id_end=50, weight=10)
process_func(batch.items)
batch.success()

```

### Multiple batches

```python

from pybatchintory import acquire_batches

batches = acquire_batches(source_table="meta_data_raw_data", job_identifer="incremental_job", weight=10, batch_count=5)
for batch in batches:
   process_func(batch.items)
   batch.success()
```

### Error handling

```python

from pybatchintory import acquire_batch

# version 1 - manual error handling
batch = acquire_batch(source_table="meta_data_raw_data", job_identifer="incremental_job", weight=10)
try:
   process_func(batch.items)
   batch.success()
except Exception as e:
   batch.error(e)
   raise
	
# version 2 - automatic error handling
batch = acquire_batch(source_table="meta_data_raw_data", job_identifer="incremental_job", weight=10)
batch.process(func, args, kwargs)
```

### Requirements (non ordered)

- Allow concurrent batch generation/processing for the same job identifier
	- read/update transactions
	- for secure and reliable functioning, isolation level "serializable" is required however "read committed" should be sufficent in most cases
- Separate database connections for meta data (external) and inventory tables (backend)
	- use sqlalchemy for engine creation and query building (guard against sql injections)
- Credentials to be read via environment variables or dotenv files (pydantic)
- Allow recursive processing of inventory table itself to allow incremental/backfill on already incremental/backfilled jobs
- Provide filter condition for meta data source table to select only relevant subset of data items


### Backend tables

Please provide a markdown representation of the following 2 database tables:

#### Inventory

| Column Name       | Data Type | Constraints                  |
|-------------------|-----------|------------------------------|
| id                | integer   | primary key, auto-increment  |
| job_identifer     | string    |                              |
| processing_start  | timestamp |                              |
| processing_end    | timestamp |                              |
| range_start       | integer   |                              |
| range_end         | integer   |                              |
| weight            | integer   |                              |
| attempt           | integer   |                              |
| status            | enum      | running, succeeded, failed   |

#### Inventory_Logs

| Column Name      | Data Type | Constraints                 |
|------------------|-----------|-----------------------------|
| id               | integer   | primary key                 |
| attempt          | integer   | primary key                 |
| processing_start | timestamp |                             |
| processing_end   | timestamp |                             |
| status           | enum      | running, succeeded, failed  |
| logging          | string    |                             |


## Poem (thanks to chatGPT)

This Python package is a wondrous tool,\
For data processing, it's oh so cool,\
With middleware for batches of data,\
Incremental processing, a much-needed beta.

No more recomputation of all data,\
Only the unseen items, a true data saver,\
Backfill scenarios are now a breeze,\
With historical data, we can reprocess with ease.

Predictable workloads, we can define,\
Adjusting resources, a task that's benign,\
For cost and performance, it's the way to go,\
Efficient processing, with no overflow.

Transparency and observability in tow,\
Each data item enriched, as we know,\
When and how it was processed, we see,\
A Python package that's just meant to be.
