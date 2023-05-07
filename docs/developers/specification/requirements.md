# Requirements

This document outlines the requirements specification for a software project named `pybatchintory`. It focuses on **what** the software aims to accomplish opposed to *how* it is achieved (see [implementation specification](implementation.md)). 

The problem statement is formulated and the added value is justified. Functional and non-functional requirements are derived. 

The intended audience are primarily developers, engineers and architects.

## General description

### Purpose

`pybatchintory` represents a middleware for batch processing data pipelines. It reduces maintenance efforts, improves performance and enhances observability by providing fist class support for following features:

- **Incremental processing**: Process only new, unseen data assets without custom bookmarking logic.
- **Backfilling**: Reprocess historical data assets in a configurable and automated manner without manual intervention.
- **Configurable workloads**: Define the amount of data assets to be processed for best predictability and efficiency.
- **Transparency**: Enrich processed data assets with job details like timestamp, identifier and parametrization.

Conceptionally, batch processing applications delegate the responsibility of generating batches of data assets to `pybatchintory` to leverage these features. `pybatchintory` provides an API to generate batches of data assets while maintaining state of historically processed data assets. Importantly, `pybatchintory` only consumes metadata about data assets while the actual data is not read.

The primary use case are **file-based batch processing pipelines**. A typical real world example are Parquet or JSON files which are continuously added to a cloud object store like Azure Blob or AWS S3. Periodically, these files require batch processing via a distributed computation framework like Apache Spark or Dask.

However, `pybatchintory` is not limited to any specific type or format because it is data asset agnostic. It is possible to generate batches of work that represent partitioning keys in table formats or distributed databases. 

### Rationale

The following section summarizes the contextual background from which `pybatchintory` originates with its purpose and added value.  

#### Incremental processing

Incremental processing greatly improves data pipeline performance by only processing unseen data assets. This prevents costly reprocessing of entire datasets. 

While incremental processing is supported in stream processing frameworks by design (e.g. Flink or Kafka Streams), this functionality is rarely available in batch processing frameworks. Only very few off-the-shelf solutions provide easy-to-use abstractions to handle incremental batch semantics (e.g., [AWS Glue Bookmarks](https://docs.aws.amazon.com/glue/latest/dg/monitor-continuations.html)). More often than not, custom solutions are used in production environments. Typically, these rely on timestamp comparisons or manually maintained offsets which closely resembles what stream processing frameworks offer out-of-the-box.

??? question "Why not use stream instead of batch processing?"

    For non-time-sensitive tasks, batch processing provides two significant advantages over stream processing:

    1. **Resource efficiency**: Batch processing allows for aggregation of large amounts of data at once, utilizing compute and memory resources more effectively while being more cost-effective overall.
    
    2. **Managing complexity**: Batch processing is easer to reason about because data is bounded and finite. Moreover, implementing complex logic on unbounded, infinite streams of data is very challenging to develop and maintain.

??? question "What other solutions exist for incremental batch processing?"

    The following is a non-exhaustive list of alternative solutions which tend fall short in one regard or the other:

    - **Databrick**'s [Autoloader](https://docs.databricks.com/ingestion/auto-loader/index.html) enables incremental processing of files in cloud objects stores. However, this does not support batch processing but only integrates with [Spark Streaming](https://spark.apache.org/docs/latest/structured-streaming-programming-guide.html) and its associated [limitations](https://spark.apache.org/docs/latest/structured-streaming-programming-guide.html#unsupported-operations).
    - Likewise, **Flink**'s [unbounded file data source](https://nightlies.apache.org/flink/flink-docs-release-1.17/docs/connectors/datastream/filesystem/#bounded-and-unbounded-streams) continously monitors for new files at any given location. However, downstream computations using this data source can only run in unbounded, [streaming execution mode](https://nightlies.apache.org/flink/flink-docs-master/docs/dev/datastream/execution_mode/#when-canshould-i-use-batch-execution-mode) which does not leverage the benefits of batch processing.
    - **Apache Hudi**'s [DeltaStreamer](https://hudi.apache.org/docs/hoodie_deltastreamer/) allows to incrementally ingest data from various sources into Hudi tables while applying custom [transformations](https://hudi.apache.org/docs/next/transforms/) on the raw data. While this approach supports batch processing, it only works for Hudi tables and is mainly intended for less complex ingestion use cases.

#### Backfilling

Data reprocessing is not an uncommon theme. Errors need to be fixed in production pipelines for both past and future data. Likewise, new features such as novel KPIs typically need to be made available for recent years, too.

However, first class support for such scenarios is currently not available. Processing all historical data at once can prove prohibitively expensive and susceptible to errors, as the cumulative data volume may surpass manageable limits. Hence, manual planning and execution is often required to create processable chunks of work.

#### Configurable Workloads

Data assets are generated inconsistently over time, often displaying seasonality and fluctuations that result in varying data volumes per time interval. In the absence of auto-scaling, processing applications may experience significant performance degradation (e.g., due to inadequate memory causing disk spills) or outright failure (e.g., memory exhaustion). Even when auto-scaling is enabled, perfect parallelization through horizontal scaling is rarely achievable in distributed systems, leading to performance issues.

A straightforward yet efficacious solution is in limiting the data volume processed by a single batch job. However, native support for this functionality is only rarely available in batch processing frameworks (e.g., [AWS Glue Workload Partitioning](https://docs.aws.amazon.com/glue/latest/dg/bounded-execution.html)).

#### Observability

Often, concerns emerge about data integrity and reliability. Consumers question results displayed in an end user dashboards. To facilitate troubleshooting, it is imperative that underlying data pipelines remain readily inspectable, ensuring the accurate processing of all available data assets. Furthermore, individual data assets must be traceable concerning the processing application and the specific time at which they were processed.

### Terminiology

This section defines core concepts which are used throughout this document:

![architecture](../../material/architecture.svg)

- **Batch Processing Application**: Refers to the application responsible for processing data assets, encompassing the core business logic. It relies on `pybatchintory` for generating batches of data assets.
- **Batch Generation Configuration:** Dictates the methodology for generating batches of data assets, outlining incremental, backfilling, and configurable workload semantics.
    - **Window**: Determines the scope of data assets incorporated in the batch generation process, excluding data assets outside this range. The window is delimited by lower and upper boundaries, which indicate the first and last data assets to be included, respectively.
    - **Workload**: Describes the amount of data assets to be processed.
- **Batch Generation:** Represents the procedure of creating batches of data assets, determined by the batch generation configuration, inventory table, and meta table. The output is a data asset batch.
- **Batch:** Comprises references to one or more data assets.
- **Batch Status**: Enumerates the potential states of a data asset batch, encompassing *synced*, *processing*, *succeeded*, and *failed*.
- **Data Asset:** Denotes a versatile, processable work unit, commonly a single file, but may also encompass partitions, keys, or rows.
- **Data Asset Type**: Categorizes semantically related data assets, such as a directory of Parquet files containing IoT data or a directory of CSV files containing ERP data.
- **Job:** Characterizes a single execution of the batch processing application, with each instance invoking `pybatchintory` to obtain one or more batches of data assets.
- **Job Identity:** Every job is equipped with an identifier and a reference to a data asset type. Both constitute the job identity. Jobs with the same job identify belong together and share the history of processed data assets. A single batch processing application may exhibit multiple job identities for separate data asset types or even different incremental and backfilling strategies.
- **Job Backlog**: Represents the remaining quantity of unprocessed data assets for a specific job identity.
- **Inventory table:** Serves as the `pybatchintory` backend table, preserving the state of executed jobs and batches of data items.
- **Meta table:** Stores metadata about data assets, such as file location and size, enabling `pybatchintory` to generate data asset batches.

### Precondition

In order to generate batches of data assets, the existence of a metadata table is mandatory. At minimum, it needs to contain a reference to the data item (e.g, file location) and a primary key as unique row identifier. Since *pybatchintory* generates chronologically sorted ranges of data items, the primary key needs to chronologically sorted, too.

### Limitation

The batch generation process will only support consecutive data assets in chronologically increasing order. This greatly reduces complexity and simplifies the implementation. Future versions may loosen this restriction.

### User Stories

- As a developer, I want a dedicated solution to support incremental processing for batch pipelines.
- As a developer, I want a managed solution to reprocess historical data in configurable chunks.
- As a developer, I want to specify the amount of data that is consumed by a single processing application job.
- As a stakeholder/developer, I want predictable run times and best performance/cost-ratio.
- As a user/developer, I want to understand when a given data asset was processed by which job.
- As a user/developer, I want to retrieve the backlog size of unprocessed data assets for a given job.

## Specific requirements

### Terminiology

This section extends the existing terminiology with more detailed concepts which are relevant for the specific requirements.

- **Backlog**: Describes the remaining amount of unprocessed data assets for a given job.
- **Data asset type**: Summarizes data assets that semantically belong together such as a directory of parquet files containing IoT data accross various devices and time ranges.
- **Batch window**: Specifies the range of data assets to be included in the batch generation process. Data assets outside this window are not relevant for the batch generation process. The window is defined by a lower and upper boundary which define the first and last data assets to be included, respectively.
- **Batch status**: Defines the possible states of a batch of data assets. This includes "processing", "succeeded" and "failed".

### Functional requirements

#### Data Asset Selection

Allow defining the metadata table that references the relevant data assets.

#### Data Asset Filtering

Allow providing a filter condition to subset data assets from the metadata table. This is crucial in case the metadata table holds references to multiple data asset types.  The filtering method should be as flexible as possible to support a wide range of metadata table models.

#### Incremental processing

Allow fetching non-processed data assets with no upper boundary for the batch window. Hence, newly added data assets will be included from one job run to another. The total amount of relevant data assets is dynamic and changes over time.

#### Backfilling

Allow fetching non-processed data assets with an upper boundary for the batch window. Hence, newly added data assets will be excluded from one job run to another. The total amount of relevant data assets is fixed and remains constant over time.

#### Chronology

Always fetch data assets in chronological order starting with the oldest ones. 

#### Configure workloads

Allow to specify the maximum workload that a single job processes. This includes two possbile criteria. First, define the maximum number of data assets. Second, define the maximum weight as the total sum of data asset size. 

The weight criteria depends on the existence of a weight attribute being present in the metadata table. If not given, no weight can be computed. 

In case no criteria is specified, all non-processed data is fetched. If both criteria are specified, the one which first exceeds the threshold applies.

#### Retry mechanism

Allow to select failed batches of data assets for retry processing. Store the number of attempts for a batch of data assets. Allow a configurable retry count upon failure.

#### Single job and multiple batches

Allow a single job to process multiple batches consecutively while specifying the total number of iterations. 

#### Recursivity

#### Concurrent processing

Enable multiple jobs to process disjunct ranges of a single type of data assets simultaneously. This allows to parallelize jobs with predictable workloads to quickly process large amounts of backlogs. 

Before a job starts processing data assets, it has to acquire them. This marks these data assets as being reserved while preventing other jobs to simultaneously process them. Once the job has finished, it can release the of data assets with a given result status such as being succeeded or failed. 

#### Observability



### Non-functional requirements

#### Usability

#### Reliability

#### Performance

#### Security

#### Maintainability

### Interfaces

#### Programmatic API

#### Command Line Client CLI
