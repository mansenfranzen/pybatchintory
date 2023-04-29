# Requirements specification

This document outlines the requirements specification for a software project named "pybatchintory". It focuses on *what* the software is supposed to accomplish. The problem statement is formulated and the added value is justified. Functional and non-functional requirements are derived. This is primarily intended for developers, architects and stakeholders.

## General description

### Purpose

`pybatchintory` represents a middleware for batch processing data pipelines. It may greatly reduce maintenance efforts, improve performance and enhance observability by enabling following features:

- **Incremental processing**: Process only new, unseen data assets without custom bookmarking logic.
- **Backfilling**: Reprocess historical data assets in a configurable and automated fashion without manual intervention.
- **Configurable workloads**: Define the amount of data assets to be processed for best predictability and efficiency.
- **Transparency**: Enrich processed data assets with job details like timestamp, identifier and configuration.

From a high level perspective, a batch processing application (e.g., Apache Spark or Dask) delegates the responsibility of generating batches of data assets to `pybatchintory` in order to benefit from the aforementioned features.

Conceptionally, `pybatchintory` only consumes metadata about data assets and does not read their actual content.

### Rationale

The following section summarizes the contextual background from which `pybatchintory` originates with its purpose and added value.  

#### Incremental processing

Incremental processing greatly improves pipeline performance by only processing newly arriving data. This prevents costly reprocessing of entire datasets. 

While incremental processing is supported in stream processing frameworks by design (e.g. Spark Streaming or Flink), this functionality is rarely available in batch processing frameworks. Only very few off-the-shelf solutions provide easy-to-use abstractions to handle incremental batch semantics (e.g., [AWS Glue Bookmarks](https://docs.aws.amazon.com/glue/latest/dg/monitor-continuations.html)). More often than not, custom solutions are used in production environments. Interestingly, these rely on timestamp comparisons or offsets which closely resembles what stream processing frameworks offer out-of-the-box.

!!! note

    - [Databricks Autoloader](https://docs.databricks.com/ingestion/auto-loader/index.html) enables incremental processing, too. However, it only integrates with [Spark Streaming](https://spark.apache.org/docs/latest/structured-streaming-programming-guide.html) causes additional [limitations](https://spark.apache.org/docs/latest/structured-streaming-programming-guide.html#unsupported-operations) in contrast to Spark's Batch processing mode.
    - [Apache Hudi's DeltaStreamer](https://hudi.apache.org/docs/hoodie_deltastreamer/).

#### Backfilling

Reprocessing of data is not an uncommon theme. Bugs need to be fixed in production pipelines and new features have to be computed for historical data, too. However, first class support for such backfilling scenarios is currently not available. In production environments, large volumes of data accumulate over time which eventually become costly and error prone to be processed all at once. Hence, manual planning and execution is often required to create processable chunks of work.

#### Configurable Workloads

Data assets are not generated evenly over time. Rather, the data generation process often exhibits seasonality and spikes. If auto-scaling is not available, processing applications may drastically drop in performance (e.g., insufficient memory -> disk spills) or may even fail completely (e.g., out of memory error). Even if auto-scaling is enabled, performance degradation is  likely because ideal parallelization is almost never possible in distributed systems. Currently, batch processing frameworks don't provide native support to limit the amount of data to be processed.

#### Observability

Frequently, doubts arise regarding data integrity and reliabilty. Customers may question results presented in a dashboard such as missing data. Hence, underlying data pipelines need to be easily inspectable to verify that all available data assets have been processed correctly. Moreover, you may need to identify when a certain data asset was processed by a certain processing application. While the former scenario is widely supported, there exist little to no solutions for the latter one.


### Terminiology


### Precondition

In order to generate batches of data assets, the existence of a metadata table is mandatory. At minimum, it needs to contain a reference to the data item (e.g, file location) and a primary key as unique row identifier. Since *pybatchintory* generates chronologically sorted ranges of data items, the primary key needs to chronologically sorted, too.

### Limitation

The batch generation process will only support consecutive data assets in chronologically increasing order. This greatly reduces complextiy and simplifies the implementation. Future versions may loosen this restriction.

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

- Backlog: Describes the remaining amount of unprocessed data assets for a given job.
- Data asset type: Summarizes data assets that semantically belong together such as a directory of parquet files containing IoT data accross various devices and time ranges.
- Batch window: Specifies the range of data assets to be included in the batch generation process. Data assets outside this window are not relevant for the batch generation process. The window is defined by a lower and upper boundary which define the first and last data assets to be included, respectively.
- Batch status: Defines the possible states of a batch of data assets. This includes "processing", "succeeded" and "failed".

### Functional requirements

#### Acquire & Release

Before a job starts processing data assets, it has to acquire them. This marks these data assets as being reserved while preventing other jobs to simultaneously process them. Once the job has finished, it can release the of data assets with a given result status such as being succeeded or failed. 

#### Batch Generation

This subsection represents the functionality that is required to generate a batch of data assets.

##### Data Asset Selection

Allow defining the metadata table that references the relevant data assets.

##### Data Asset Filtering

Allow providing a filter condition to subset data assets from the metadata table. This is crucial in case the metadata table holds references to multiple data asset types.  The filtering method should be as flexible as possible to support a wide range of metadata table models.

##### Incremental processing

Allow fetching non-processed data assets with no upper boundary for the batch window. Hence, newly added data assets will be included from one job run to another. The total amount of relevant data assets is dynamic and changes over time.

##### Backfilling

Allow fetching non-processed data assets with an upper boundary for the batch window. Hence, newly added data assets will be excluded from one job run to another. The total amount of relevant data assets is fixed and remains constant over time.

##### Chronology

Always fetch data assets in chronological order starting with the oldest ones. 

##### Predictable workloads

Allow to specify the maximum workload that a single job processes. This includes two possbile criteria. First, define the maximum number of data assets. Second, define the maximum weight as the total sum of data asset size. 

The weight criteria depends on the existance of a weight attribute being present in the metadata table. If not given, no weight can be computed. 

In case no criteria is specified, all non-processed data is fetched. If both criteria are specified, the one which first exceeds the threshold applies.

##### Retry mechanism

Allow to select failed batches of data assets for retry processing. Store the number of attempts for a batch of data assets. Allow a configurable retry count upon failure.

##### Single job and multiple batches

Allow a single job to process multiple batches consecutively while specifying the total number of iterations. 

#### Concurrent processing

Enable multiple jobs to process disjunct ranges of a single type of data assets simultaneously. This allows to parallize jobs with predictable workloads to quickly process large amounts of backlogs.

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
