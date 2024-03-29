# pybatchintory

`pybatchintory` is a middleware for batch processing data pipelines. It enables incremental processing and provides first class support for reprocessing historical data with predictable workloads.

**Metadata** about **data assests** is leveraged to generate **batches** of work. The actual data is not read. An **inventory** maintains state of already processed data items.


## Rational

`pybatchintory` may greatly improve batch processing data pipelines by enabling the following four features:

- **Incremental processing**: Process only new, unseen data avoiding recomputation of all data items.
- **Backfilling**: Reprocess historical data in a configurable and automated fashion without manual intervention.
- **Predictable workloads**: Define the amount of data to be processed to match compute resources for best efficiency.
- **Transparency and observability**: Enrich processed data with meta information such as processing job, time and result.

## Reasoning

While incremental processing is supported in stream processing frameworks by design, this functionality is rarely available in batch processing frameworks. Only very few off-the-shelf solutions provide easy-to-use abstractions to handle incremental batch semantics (e.g., AWS Glue Job Bookmarks). More often than not, custom non-standard solutions are used in production environments. Interestingly, these rely on timestamp watermarks which closely resemble what stream processing frameworks offer out-of-the-box. 

Support for backfilling is even worse. Reprocessing of data is not an uncommon theme. Bugs need to be fixed in production pipelines and new features have to be computed for historical data, too. In reality, large volumes of data accumulate over time which may become impossible to be processed all at once. Hence, manual planning and execution is required to create processable chunks of work. 

`pybatchintory` solves these issues while providing a thin abstraction layer that can be integrated with any batch processing framework. 

## Preconditions

`pybatchintory` assumes the existence of a metadata table that contains information about the data assets, such as file location and size. To generate ranges of data assets constituting a batch to be processed, `pybatchintory` requires the metadata table to provide a **unique auto-increment identifier column**.

## Concepts & Terminology 

![architecture](docs/material/architecture.svg)

- **Processing application**: Resembles the application that actually reads and processes the content of data assets. It utilizes `pybatchintory` to generate batches of data assets while passing a batch configuration.
- **Batch configuration:** Specifies the characteristics of a batch of data assets. It contains the definition of incremental or backfill semantics with predictable workloads.
- **Jobs:** Represent one or more executions of the processing application. Each instantiation invokes `pybatchintory` to fetch batch of data assets.
- **Batches:** Contain references to one or more data assets.
- **Batch generation:** Resembles the process of generating new batches of data assets. Its result is determined by the batch configuration, the inventory table and the meta table. It embodies the core logic enabling incremental and backfilling semantics with predictable workloads. 
- **Inventory table:** Represents the backend table of `pybatchintory`. It maintains state of historically processed data items. Each row corresponds to a single  job consuming a batch with references to the meta table and a range of processed data assets.
- **Meta table:** Contains meta information about data assets like file location and size. `pybatchintory` leverages it to generate batches of data assets.
- **Data assets:** Represent arbitrary processable units of work. Typically, these are Parquet or JSON files stored in an object store such as AWS S3 or Azure Blob. However, since `pybatchintory` makes no strong assumptions about them, it can be anything consumable by a processing application.

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

## Usage

### Configuration

SqlAlchemy connection strings for inventory and meta table need to be 
provided. These can be provided via environment variables as follows:

#### Environment variables

```bash
export PYBATCHINTORY_INVENTORY_CONN="postgresql+psycopg2://user:password@host:port/dbname"
export PYBATCHINTORY_META_CONN="postgresql+psycopg2://user:password@host:port/dbname"
```

#### Dot-env file
You may also provide a path to a dot-env file via an environment variable:

```bash
export PYBATCHINTORY_ENV_FILE="PATH_TO_DOT_ENV_FILE"
```

#### Programmatically

In addition, you may set a dot-env file and explicit settings programmatically:

```python
from pybatchintory import configure

configure(
    dot_env="PATH_TO_DOT_ENV_FILE", 
    settings=dict(INVENTORY_CONN="CONN_STRING"))
```

### Invocation

#### Incremental with predictable workload

```python
from pybatchintory import acquire_batch

batch = acquire_batch(
    meta_table_name="meta_table", 
    meta_table_cols={
        "uid": "id",
        "item": "file",
        "weight": "size_in_mib"
	},
    job="incremental_job",
    batch_weight=100
)

process_func(batch.items)
batch.succeeded()
```

#### Backfill with predictable workload

```python
from pybatchintory import acquire_batch

batch = acquire_batch(
    meta_table_name="meta_table", 
    meta_table_cols={
        "uid": "id",
        "item": "file",
        "weight": "size_in_mib"
	},
    job="backfill_job", 
    batch_id_min=20,
    batch_id_max=80,
    batch_weight=100
)

process_func(batch.items)
batch.succeeded()
```

#### Multiple batches

**Not yet implemented**

```python
from pybatchintory import acquire_batches

batches = acquire_batches(
	meta_table_name="meta_table",
	job="incremental_job",
	batch_weight=10,
	iterations=5
)

for batch in batches:
	process_func(batch.items)
	batch.succeeded()
```

#### Error handling

```python

from pybatchintory import acquire_batch

# version 1 - manual error handling
batch = acquire_batch(
	meta_table_name="meta_table",
	job="incremental_job",
	batch_weight=10)
try:
	process_func(batch.items)
	batch.succeeded()
except Exception as e:
	batch.failed(e)
	raise

# version 2 - automatic error handling - not yet implemented
batch = acquire_batch(
	meta_table_name="meta_table",
	job="incremental_job",
	batch_weight=10)
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


### Inventory table

| Column Name      | Type                                                  | Constraints                              |
|------------------|-------------------------------------------------------|------------------------------------------|
| id               | Integer                                               | primary_key=True, autoincrement=True     |
| meta_table       | String                                                | nullable=False                           |
| job              | String                                                | nullable=False                           |
| job_identifier   | String                                                |                                          |
| job_result_item  | JSON                                                  |                                          |
| processing_start | DateTime                                              | nullable=False, default=TS               |
| processing_end   | DateTime                                              |                                          |
| batch_id_start   | Integer                                               | nullable=False                           |
| batch_id_end     | Integer                                               | nullable=False                           |
| batch_weight     | Integer                                               |                                          |
| batch_count      | Integer                                               | nullable=False                           |
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
