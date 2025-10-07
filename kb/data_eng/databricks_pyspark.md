---
tags: [databricks, pyspark, delta-lake, big-data]
---

# Databricks and PySpark Optimization

## Overview
Databricks provides a unified analytics platform built on Apache Spark, offering optimized performance for big data processing with Delta Lake for ACID transactions and data versioning.

## PySpark Performance Optimization

### 1. Data Partitioning Strategies
```python
# Partition by date for time-series data
df.write.partitionBy("date").mode("overwrite").parquet("path/to/data")

# Partition by business key for joins
df.write.partitionBy("customer_id").mode("overwrite").parquet("path/to/data")

# Coalesce to reduce number of files
df.coalesce(10).write.mode("overwrite").parquet("path/to/data")
```

### 2. Caching and Persistence
```python
# Cache frequently accessed DataFrames
df.cache()

# Persist with different storage levels
df.persist(StorageLevel.MEMORY_AND_DISK_SER)

# Unpersist when done
df.unpersist()
```

### 3. Broadcast Joins
```python
# Broadcast small tables for joins
from pyspark.sql.functions import broadcast

large_df.join(broadcast(small_df), "key", "inner")
```

## Delta Lake Best Practices

### 1. Delta Table Management
```python
# Create Delta table with partitioning
df.write.format("delta").partitionBy("date").saveAsTable("sales_data")

# Optimize Delta table
spark.sql("OPTIMIZE sales_data ZORDER BY (customer_id, product_id)")

# Vacuum old files
spark.sql("VACUUM sales_data RETAIN 168 HOURS")
```

### 2. Time Travel and Versioning
```python
# Read from specific version
df = spark.read.format("delta").option("versionAsOf", 5).table("sales_data")

# Read from specific timestamp
df = spark.read.format("delta").option("timestampAsOf", "2023-01-01").table("sales_data")

# Show table history
spark.sql("DESCRIBE HISTORY sales_data").show()
```

### 3. Merge Operations
```python
# Upsert data using merge
from delta.tables import DeltaTable

delta_table = DeltaTable.forName(spark, "sales_data")

delta_table.alias("target").merge(
    updates_df.alias("source"),
    "target.id = source.id"
).whenMatchedUpdateAll().whenNotMatchedInsertAll().execute()
```

## Cluster Configuration

### 1. Cluster Sizing
- **Driver Node**: 2-4 cores, 8-16GB RAM for small to medium workloads
- **Worker Nodes**: 4-8 cores, 16-32GB RAM per node
- **Storage**: Use instance stores for temporary data, EBS for persistent data
- **Network**: Enable enhanced networking for better performance

### 2. Spark Configuration
```python
# Optimize for large datasets
spark.conf.set("spark.sql.adaptive.enabled", "true")
spark.conf.set("spark.sql.adaptive.coalescePartitions.enabled", "true")
spark.conf.set("spark.sql.adaptive.skewJoin.enabled", "true")

# Optimize for joins
spark.conf.set("spark.sql.join.preferSortMergeJoin", "true")
spark.conf.set("spark.sql.adaptive.localShuffleReader.enabled", "true")
```

### 3. Dynamic Allocation
```python
# Enable dynamic allocation
spark.conf.set("spark.dynamicAllocation.enabled", "true")
spark.conf.set("spark.dynamicAllocation.minExecutors", "2")
spark.conf.set("spark.dynamicAllocation.maxExecutors", "20")
spark.conf.set("spark.dynamicAllocation.initialExecutors", "5")
```

## Data Processing Patterns

### 1. Streaming Data Processing
```python
# Read from Kafka
df = spark.readStream.format("kafka").option("kafka.bootstrap.servers", "localhost:9092").load()

# Process streaming data
processed_df = df.select(
    col("value").cast("string").alias("json"),
    col("timestamp")
).select(
    from_json(col("json"), schema).alias("data"),
    col("timestamp")
).select("data.*", "timestamp")

# Write to Delta Lake
processed_df.writeStream.format("delta").option("checkpointLocation", "/path/to/checkpoint").start()
```

### 2. Batch Processing with Window Functions
```python
from pyspark.sql.window import Window
from pyspark.sql.functions import row_number, rank, lag, lead

# Define window specification
window_spec = Window.partitionBy("customer_id").orderBy("order_date")

# Apply window functions
df.withColumn("row_num", row_number().over(window_spec)) \
  .withColumn("prev_order_date", lag("order_date").over(window_spec)) \
  .withColumn("order_rank", rank().over(window_spec))
```

### 3. Data Quality Checks
```python
# Define data quality rules
quality_rules = [
    col("customer_id").isNotNull(),
    col("order_date").isNotNull(),
    col("amount") > 0,
    col("amount") < 10000
]

# Apply quality checks
valid_df = df.filter(reduce(lambda a, b: a & b, quality_rules))
invalid_df = df.filter(~reduce(lambda a, b: a & b, quality_rules))

# Log quality issues
invalid_df.write.mode("append").saveAsTable("data_quality_issues")
```

## Monitoring and Observability

### 1. Spark UI Monitoring
- **Jobs Tab**: Monitor job execution and stages
- **Stages Tab**: Analyze stage performance and bottlenecks
- **Storage Tab**: Check DataFrame caching and persistence
- **Environment Tab**: Review Spark configuration

### 2. Custom Metrics
```python
# Track custom metrics
from pyspark.sql.functions import count, sum

# Record processing metrics
metrics = df.agg(
    count("*").alias("total_records"),
    sum("amount").alias("total_amount")
).collect()[0]

# Log metrics to external system
log_metrics({
    "total_records": metrics["total_records"],
    "total_amount": metrics["total_amount"],
    "timestamp": datetime.now()
})
```

### 3. Error Handling
```python
# Implement robust error handling
try:
    result_df = process_data(input_df)
    result_df.write.mode("overwrite").saveAsTable("processed_data")
except Exception as e:
    # Log error details
    error_details = {
        "error": str(e),
        "timestamp": datetime.now(),
        "input_record_count": input_df.count()
    }
    
    # Write error to error table
    error_df = spark.createDataFrame([error_details])
    error_df.write.mode("append").saveAsTable("processing_errors")
    
    # Re-raise exception
    raise e
```

## Data Lakehouse Architecture

### 1. Bronze Layer (Raw Data)
```python
# Ingest raw data
raw_df = spark.read.format("json").load("path/to/raw/data")

# Store in Bronze layer
raw_df.write.format("delta").mode("append").saveAsTable("bronze.raw_events")
```

### 2. Silver Layer (Cleaned Data)
```python
# Clean and validate data
cleaned_df = raw_df.filter(
    col("event_id").isNotNull() &
    col("timestamp").isNotNull() &
    col("user_id").isNotNull()
).withColumn("processed_date", current_timestamp())

# Store in Silver layer
cleaned_df.write.format("delta").mode("append").saveAsTable("silver.cleaned_events")
```

### 3. Gold Layer (Business Logic)
```python
# Apply business logic and aggregations
gold_df = cleaned_df.groupBy("user_id", "date").agg(
    count("*").alias("event_count"),
    sum("value").alias("total_value"),
    avg("value").alias("avg_value")
)

# Store in Gold layer
gold_df.write.format("delta").mode("overwrite").saveAsTable("gold.user_daily_metrics")
```

## Cost Optimization

### 1. Cluster Management
- **Auto-scaling**: Use Databricks auto-scaling for variable workloads
- **Spot Instances**: Use spot instances for non-critical workloads
- **Cluster Pools**: Pre-allocate clusters for faster startup
- **Termination Policies**: Auto-terminate idle clusters

### 2. Storage Optimization
- **Compression**: Use Parquet with Snappy compression
- **Partitioning**: Partition large tables by date or key columns
- **File Sizing**: Optimize file sizes (128MB-1GB per file)
- **Delta Optimization**: Regular OPTIMIZE and VACUUM operations

### 3. Query Optimization
- **Predicate Pushdown**: Use filters early in the query
- **Column Pruning**: Select only needed columns
- **Join Optimization**: Use broadcast joins for small tables
- **Caching**: Cache frequently accessed DataFrames

## Security and Governance

### 1. Access Control
- **Unity Catalog**: Centralized data governance
- **Table ACLs**: Fine-grained access control
- **Column-level Security**: Mask sensitive columns
- **Row-level Security**: Filter data based on user context

### 2. Data Lineage
- **Lineage Tracking**: Track data transformations
- **Metadata Management**: Document table schemas and business logic
- **Impact Analysis**: Understand downstream dependencies
- **Compliance**: Meet regulatory requirements

### 3. Audit and Monitoring
- **Query Logging**: Log all data access
- **Performance Monitoring**: Track query performance
- **Resource Usage**: Monitor compute and storage usage
- **Cost Tracking**: Track costs by user and project
