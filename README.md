# pybatchintory

`pybatchintory` represents a middleware for batch oriented data pipelines. It enables incremental processing and provides first class support for reprocessing historical data with predictable workloads.

Only meta information of data items is consumed and processed. The actual data is not read. An **inventory** of already processed and unseen data items is managed while providing an API to interact with it.

## Reasoning

This package may greatly improve data pipelines by enabling the following four features:

- **Incremental processing**: Only new, unseen data items can be processed, avoiding recomputation of all data items.
- **Backfill scenarios**: Historical data items can be reprocessed in a configurable and automated way.
- **Predictable workloads**: The amount of data to be processed can be defined and is known upfront to adjust compute resources accordingly for best efficiency and cost/performance ratio for both incremental processing and backfill scenarios.
- **Transparency and observability**: Each data item can be enriched with information about when it was processed by what job.

## Preconditions

`pybatchintory` assumes the existence of a metadata table that contains information about the data items, such as their file location and registration timestamps. Importantly, to properly generate ranges of data items constituting a single batch to be processed, `pybatchintory` requires the metadata table to provide a **unique auto-increment ID column**.

## Assumptions

- Data items are always processed chronologically according to monotonic increasing unique id
- Only continuous ranges of ids can be processed

### Example meta data source table

**Schema**

| Field           | Type         | Key          | Extra         |
|-----------------|--------------|--------------|---------------|
| id              | int(11)      | PRI          | auto_increment|
| file_location   | varchar(255) |              |               |
| size_in_bytes   | int(11)      |              |               |
| imported        | timestamp    |              |               |

**Content**

| id | file_location         | size_in_bytes | imported            |
|----|-----------------------|---------------|---------------------|
| 6  | /path/to/sixth/file    | 32768         | 2021-01-06 00:00:00 |
| 7  | /path/to/seventh/file  | 65536         | 2021-01-07 00:00:00 |
| 8  | /path/to/eighth/file   | 131072        | 2021-01-08 00:00:00 |
| 9  | /path/to/ninth/file    | 262144        | 2021-01-09 00:00:00 |
| 10 | /path/to/tenth/file    | 524288        | 2021-01-10 00:00:00 |

## Examplary usage

### Single batch - incremental/backfill with weight

```python

from pybatchintory import acquire_batch

# incremental
batch = acquire_batch(job="incremental_job", weight=10)
process_func(batch.items)
batch.success()

# backfill
batch = acquire_batch(job="backfill_job", id_start=10, id_end=50, weight=10)
process_func(batch.items)
batch.success()

```

### Multiple batches

**Not yet implemented**

```python

from pybatchintory import acquire_batches

batches = acquire_batches(job="incremental_job", weight=10, iterations=5)
for batch in batches:
   process_func(batch.items)
   batch.success()
```

### Error handling

```python

from pybatchintory import acquire_batch

# version 1 - manual error handling
batch = acquire_batch(job="incremental_job", weight=10)
try:
   process_func(batch.items)
   batch.success()
except Exception as e:
   batch.error(e)
   raise
	
# version 2 - automatic error handling - not yet implemented
batch = acquire_batch(job="incremental_job", weight=10)
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

| Column Name      | Type                                                  | Constraints                              |
|------------------|-------------------------------------------------------|------------------------------------------|
| id               | Integer                                               | primary_key=True, autoincrement=True     |
| meta_table       | String                                                | nullable=False                           |
| job              | String                                                | nullable=False                           |
| job_identifier   | String                                                |                                          |
| job_result       | JSON                                                  |                                          |
| processing_start | DateTime                                              | nullable=False, default=TS               |
| processing_end   | DateTime                                              |                                          |
| meta_id_start    | Integer                                               | nullable=False                           |
| meta_id_end      | Integer                                               | nullable=False                           |
| weight           | Integer                                               |                                          |
| count            | Integer                                               | nullable=False                           |
| attempt          | Integer                                               | nullable=False, default=1                |
| status           | Enum(*cfg.settings.INVENTORY_STATUS_ENUMS)            | nullable=False, default="running"        |
| logging          | String                                                |                                          |
| config           | JSON                                                  | nullable=False                           |


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
