---
tags: [data-engineer, pyspark, databricks, delta-lake, spark, big-data, performance-optimization]
persona: de
---

# PySpark & Databricks - Krishna's Comprehensive Guide

## Introduction
**Krishna's PySpark Journey:**
I use PySpark daily at Walgreens to process 10TB+ monthly data. What started with simple transformations evolved into building complex pipelines with performance optimization, Delta Lake management, and real-time streaming. Let me share everything I've learned.

## PySpark Fundamentals

### DataFrame API
**Krishna's Most-Used Operations:**
```python
from pyspark.sql import SparkSession, functions as F, Window

# Initialize Spark
spark = SparkSession.builder \
    .appName("Walgreens Data Pipeline") \
    .config("spark.sql.adaptive.enabled", "true") \
    .getOrCreate()

# Read data
df_orders = spark.read.format("delta").load("/mnt/raw/orders")

# Common transformations
df_clean = (
    df_orders
    # Filter
    .filter(F.col("order_status") == "completed")
    .filter(F.col("order_date") >= "2023-01-01")
    
    # Select and rename
    .select(
        F.col("order_id"),
        F.col("customer_id"),
        F.col("order_date").cast("date"),
        F.col("order_amount").cast("decimal(18,2)").alias("amount")
    )
    
    # Add derived columns
    .withColumn("order_year", F.year("order_date"))
    .withColumn("order_month", F.month("order_date"))
    .withColumn("is_high_value", F.when(F.col("amount") > 1000, True).otherwise(False))
    
    # Remove duplicates
    .dropDuplicates(["order_id"])
    
    # Handle nulls
    .fillna({"amount": 0, "customer_id": "UNKNOWN"})
)

# Aggregations
df_summary = (
    df_clean
    .groupBy("customer_id", "order_year", "order_month")
    .agg(
        F.count("order_id").alias("order_count"),
        F.sum("amount").alias("total_spent"),
        F.avg("amount").alias("avg_order_value"),
        F.min("order_date").alias("first_order"),
        F.max("order_date").alias("last_order")
    )
)
```

### Window Functions
**Krishna's Real Use Case - Customer Rankings:**
```python
from pyspark.sql.window import Window

# Calculate customer lifetime value rankings
window_spec = Window.partitionBy("customer_segment").orderBy(F.desc("lifetime_value"))

df_customer_analysis = (
    df_customers
    .withColumn("segment_rank", F.row_number().over(window_spec))
    .withColumn("segment_percentile", F.percent_rank().over(window_spec))
    .withColumn(
        "cumulative_value", 
        F.sum("lifetime_value").over(window_spec.rowsBetween(Window.unboundedPreceding, Window.currentRow))
    )
    .withColumn(
        "moving_avg_3months",
        F.avg("monthly_spend").over(Window.partitionBy("customer_id").orderBy("month").rowsBetween(-2, 0))
    )
)

# Lead/Lag for time-series analysis
df_retention = (
    df_orders
    .groupBy("customer_id", F.date_trunc("month", "order_date").alias("order_month"))
    .agg(F.sum("order_amount").alias("monthly_revenue"))
    .withColumn(
        "prev_month_revenue",
        F.lag("monthly_revenue", 1).over(Window.partitionBy("customer_id").orderBy("order_month"))
    )
    .withColumn(
        "next_month_revenue",
        F.lag("monthly_revenue", -1).over(Window.partitionBy("customer_id").orderBy("order_month"))
    )
    .withColumn(
        "revenue_change_pct",
        ((F.col("monthly_revenue") - F.col("prev_month_revenue")) / F.col("prev_month_revenue") * 100)
    )
)
```

## Performance Optimization

### 1. Partitioning Strategies
**Krishna's Lessons Learned:**
```python
# BAD: No partitioning - slow queries
df.write.format("delta").mode("overwrite").save("/mnt/data/orders")

# GOOD: Partition by date - fast time-based queries
df.write.format("delta") \
    .partitionBy("order_date") \
    .mode("overwrite") \
    .save("/mnt/data/orders")

# BETTER: Multi-level partitioning for complex queries
df.write.format("delta") \
    .partitionBy("order_year", "order_month") \
    .mode("overwrite") \
    .save("/mnt/data/orders")

# Optimal file sizes (128MB - 1GB per file)
df.repartition(100).write.format("delta") \
    .partitionBy("order_date") \
    .mode("overwrite") \
    .save("/mnt/data/orders")
```

**Business Impact at Walgreens:**
- Pharmacy queries on daily partitions: 4 hours → 15 minutes
- Supply chain monthly reports: 2 hours → 10 minutes
- Cost savings: $15K/month in compute costs

### 2. Broadcast Joins
**Krishna's Join Optimization:**
```python
# BAD: Shuffle join for small dimension table
large_sales.join(small_products, "product_id")

# GOOD: Broadcast small table (< 10MB)
large_sales.join(F.broadcast(small_products), "product_id")

# Automatic broadcast (configure threshold)
spark.conf.set("spark.sql.autoBroadcastJoinThreshold", 10485760)  # 10MB

# Example: Customer loyalty pipeline
df_transactions = spark.read.format("delta").load("/mnt/raw/transactions")  # 50M rows
df_stores = spark.read.format("delta").load("/mnt/dim/stores")  # 9K rows

# Broadcast stores dimension
df_enriched = df_transactions.join(
    F.broadcast(df_stores),
    "store_id",
    "left"
)
```

### 3. Caching & Persistence
**When Krishna Uses Caching:**
```python
# Cache frequently accessed data
df_customers = spark.read.format("delta").load("/mnt/dim/customers")
df_customers.cache()

# Use in multiple operations
high_value = df_customers.filter(F.col("ltv") > 10000).count()
churn_risk = df_customers.filter(F.col("days_since_order") > 90).count()

# Different persistence levels
from pyspark import StorageLevel

# Memory only - fastest but risky
df.persist(StorageLevel.MEMORY_ONLY)

# Memory + Disk - safer
df.persist(StorageLevel.MEMORY_AND_DISK)

# Serialized - more efficient memory usage
df.persist(StorageLevel.MEMORY_AND_DISK_SER)

# Always unpersist when done!
df.unpersist()
```

**Business Scenario:**
Pharmacy dashboard queries the same customer dimension 50 times. Caching reduced query time from 2 minutes to 5 seconds.

### 4. Adaptive Query Execution (AQE)
**Krishna's AQE Configuration:**
```python
# Enable AQE (Spark 3.0+)
spark.conf.set("spark.sql.adaptive.enabled", "true")

# Coalesce partitions after shuffle
spark.conf.set("spark.sql.adaptive.coalescePartitions.enabled", "true")
spark.conf.set("spark.sql.adaptive.coalescePartitions.initialPartitionNum", 200)

# Handle skewed joins automatically
spark.conf.set("spark.sql.adaptive.skewJoin.enabled", "true")
spark.conf.set("spark.sql.adaptive.skewJoin.skewedPartitionFactor", 5)
spark.conf.set("spark.sql.adaptive.skewJoin.skewedPartitionThresholdInBytes", "256MB")

# Optimize join strategies
spark.conf.set("spark.sql.adaptive.localShuffleReader.enabled", "true")
```

**Real Impact:**
Skewed customer data (80% orders from 20% customers) caused 3-hour jobs. AQE detected skew and reoptimized → 45 minutes.

## Delta Lake

### 1. ACID Transactions
**Krishna's Reliable Pipelines:**
```python
from delta.tables import DeltaTable

# Write with transactions
df_new_orders.write.format("delta") \
    .mode("append") \
    .save("/mnt/silver/orders")

# Concurrent writes are safe - Delta handles it!
# Multiple jobs can write simultaneously

# Read consistent snapshots
df = spark.read.format("delta").load("/mnt/silver/orders")
# Always sees consistent state, never partial writes
```

### 2. Merge (Upsert) Operations
**Krishna's Most Common Pattern:**
```python
# Load incremental data
df_updates = spark.read.format("delta").load("/mnt/bronze/orders_incremental")

# Get existing Delta table
delta_table = DeltaTable.forPath(spark, "/mnt/silver/orders")

# Upsert with merge
(
    delta_table.alias("target")
    .merge(
        df_updates.alias("source"),
        "target.order_id = source.order_id"
    )
    .whenMatchedUpdate(
        condition="source.updated_at > target.updated_at",
        set={
            "order_status": "source.order_status",
            "order_amount": "source.order_amount",
            "updated_at": "source.updated_at"
        }
    )
    .whenNotMatchedInsertAll()
    .execute()
)
```

**Business Use Case - Customer SCD Type 2:**
```python
# Slowly Changing Dimension for customer segments
from pyspark.sql import functions as F

# Read new customer data
df_new = spark.read.format("delta").load("/mnt/bronze/customers_daily")

# Read existing dimension
delta_table = DeltaTable.forPath(spark, "/mnt/silver/dim_customer")

# Prepare SCD Type 2 merge
(
    delta_table.alias("target")
    .merge(
        df_new.alias("source"),
        "target.customer_id = source.customer_id AND target.is_current = true"
    )
    .whenMatchedUpdate(
        condition="target.customer_segment != source.customer_segment",
        set={
            "is_current": "false",
            "end_date": F.current_date()
        }
    )
    .execute()
)

# Insert new records for changed customers
df_changed = df_new.join(
    delta_table.toDF().filter("is_current = false"),
    "customer_id"
).select(
    "customer_id",
    "customer_segment",
    F.current_date().alias("start_date"),
    F.lit("9999-12-31").cast("date").alias("end_date"),
    F.lit(True).alias("is_current")
)

df_changed.write.format("delta").mode("append").save("/mnt/silver/dim_customer")
```

### 3. Time Travel
**Krishna's Debugging & Recovery:**
```python
# Read historical version
df_yesterday = spark.read.format("delta") \
    .option("versionAsOf", 10) \
    .load("/mnt/silver/orders")

# Read by timestamp
df_last_week = spark.read.format("delta") \
    .option("timestampAsOf", "2024-01-01 00:00:00") \
    .load("/mnt/silver/orders")

# Show table history
history_df = spark.sql("DESCRIBE HISTORY delta.`/mnt/silver/orders`")
history_df.select("version", "timestamp", "operation", "operationMetrics").show(20, False)

# Restore to previous version
spark.sql("RESTORE TABLE delta.`/mnt/silver/orders` TO VERSION AS OF 10")
```

**Real Scenario:**
Bad data got loaded on Friday night. Monday morning, I used time travel to compare Friday vs Monday, identified the issue, and restored Friday's version. Business users were happy!

### 4. Optimize & Vacuum
**Krishna's Maintenance Schedule:**
```python
# Optimize - compact small files
spark.sql("OPTIMIZE delta.`/mnt/silver/orders`")

# Z-Order for faster queries
spark.sql("""
    OPTIMIZE delta.`/mnt/silver/orders`
    ZORDER BY (customer_id, order_date)
""")

# Vacuum - remove old files (run weekly)
spark.sql("""
    VACUUM delta.`/mnt/silver/orders` RETAIN 168 HOURS
""")

# Check table statistics
spark.sql("DESCRIBE DETAIL delta.`/mnt/silver/orders`").show(False)
```

**Business Impact:**
- Pre-optimize: 100K small files, 5-minute queries
- Post-optimize: 1K optimized files, 30-second queries
- Storage: Reduced 2TB to 1.5TB after vacuum

## Structured Streaming

### Real-Time Pipelines
**Krishna's Streaming Use Case - Click Events:**
```python
# Read from Kafka/Event Hub
df_stream = (
    spark.readStream
    .format("kafka")
    .option("kafka.bootstrap.servers", "eventhub.servicebus.windows.net:9093")
    .option("subscribe", "clickstream-events")
    .load()
)

# Parse JSON
from pyspark.sql.types import StructType, StructField, StringType, TimestampType, IntegerType

schema = StructType([
    StructField("user_id", StringType()),
    StructField("event_type", StringType()),
    StructField("product_id", StringType()),
    StructField("timestamp", TimestampType()),
    StructField("session_id", StringType())
])

df_parsed = (
    df_stream
    .select(F.from_json(F.col("value").cast("string"), schema).alias("data"))
    .select("data.*")
)

# Windowed aggregations
df_aggregated = (
    df_parsed
    .withWatermark("timestamp", "10 minutes")
    .groupBy(
        F.window("timestamp", "5 minutes", "1 minute"),
        "product_id"
    )
    .agg(
        F.count("*").alias("view_count"),
        F.countDistinct("user_id").alias("unique_users")
    )
)

# Write to Delta
query = (
    df_aggregated.writeStream
    .format("delta")
    .outputMode("append")
    .option("checkpointLocation", "/mnt/checkpoints/product_views")
    .trigger(processingTime="1 minute")
    .start("/mnt/silver/product_view_metrics")
)
```

## Databricks Platform

### 1. Cluster Configuration
**Krishna's Production Clusters:**
```json
{
  "cluster_name": "production-etl-cluster",
  "spark_version": "13.3.x-scala2.12",
  "node_type_id": "Standard_DS4_v2",
  "driver_node_type_id": "Standard_DS4_v2",
  "autoscale": {
    "min_workers": 2,
    "max_workers": 8
  },
  "autotermination_minutes": 30,
  "spark_conf": {
    "spark.sql.adaptive.enabled": "true",
    "spark.databricks.delta.preview.enabled": "true",
    "spark.sql.adaptive.coalescePartitions.enabled": "true"
  },
  "spark_env_vars": {
    "PYSPARK_PYTHON": "/databricks/python3/bin/python3"
  }
}
```

### 2. Notebook Best Practices
**Krishna's Notebook Structure:**
```python
# Cell 1: Imports & Setup
from pyspark.sql import functions as F, Window
from pyspark.sql.types import *
from delta.tables import DeltaTable
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cell 2: Parameters (use Databricks widgets)
dbutils.widgets.text("execution_date", "2024-01-01")
dbutils.widgets.dropdown("environment", "prod", ["dev", "staging", "prod"])

execution_date = dbutils.widgets.get("execution_date")
environment = dbutils.widgets.get("environment")

logger.info(f"Running pipeline for {execution_date} in {environment}")

# Cell 3: Functions
def read_source_data(path, date):
    """Read source data with error handling"""
    try:
        return spark.read.format("delta").load(f"{path}/date={date}")
    except Exception as e:
        logger.error(f"Failed to read {path}: {e}")
        raise

# Cell 4: Main Pipeline Logic
df_orders = read_source_data("/mnt/raw/orders", execution_date)
df_clean = transform_orders(df_orders)
write_to_silver(df_clean, "/mnt/silver/orders")

# Cell 5: Quality Checks
row_count = df_clean.count()
assert row_count > 0, "No data processed!"
logger.info(f"Processed {row_count:,} orders")
```

### 3. Job Orchestration
**Krishna's Job Configuration:**
```python
# Using Databricks Jobs API
job_config = {
    "name": "Daily Orders ETL",
    "tasks": [
        {
            "task_key": "bronze_ingestion",
            "notebook_task": {
                "notebook_path": "/Pipelines/Bronze/ingest_orders",
                "base_parameters": {
                    "execution_date": "{{job.trigger_date}}"
                }
            },
            "new_cluster": {
                "spark_version": "13.3.x-scala2.12",
                "node_type_id": "Standard_DS3_v2",
                "num_workers": 4
            }
        },
        {
            "task_key": "silver_transformation",
            "depends_on": [{"task_key": "bronze_ingestion"}],
            "notebook_task": {
                "notebook_path": "/Pipelines/Silver/transform_orders",
                "base_parameters": {
                    "execution_date": "{{job.trigger_date}}"
                }
            },
            "existing_cluster_id": "1234-567890-abc123"
        },
        {
            "task_key": "gold_aggregation",
            "depends_on": [{"task_key": "silver_transformation"}],
            "notebook_task": {
                "notebook_path": "/Pipelines/Gold/aggregate_metrics",
                "base_parameters": {
                    "execution_date": "{{job.trigger_date}}"
                }
            },
            "existing_cluster_id": "1234-567890-abc123"
        }
    ],
    "schedule": {
        "quartz_cron_expression": "0 0 2 * * ?",  # 2 AM daily
        "timezone_id": "America/Chicago"
    },
    "email_notifications": {
        "on_failure": ["data-team@walgreens.com"]
    },
    "max_concurrent_runs": 1
}
```

## Unity Catalog

### Data Governance
**Krishna's UC Implementation:**
```python
# Create catalog and schemas
spark.sql("CREATE CATALOG IF NOT EXISTS walgreens_prod")
spark.sql("CREATE SCHEMA IF NOT EXISTS walgreens_prod.raw")
spark.sql("CREATE SCHEMA IF NOT EXISTS walgreens_prod.silver")
spark.sql("CREATE SCHEMA IF NOT EXISTS walgreens_prod.gold")

# Create managed table
spark.sql("""
    CREATE TABLE IF NOT EXISTS walgreens_prod.silver.orders (
        order_id STRING,
        customer_id STRING,
        order_date DATE,
        order_amount DECIMAL(18,2),
        created_at TIMESTAMP
    )
    USING DELTA
    PARTITIONED BY (order_date)
    LOCATION '/mnt/silver/orders'
""")

# Grant permissions
spark.sql("GRANT SELECT ON TABLE walgreens_prod.silver.orders TO `analytics-team@walgreens.com`")
spark.sql("GRANT ALL PRIVILEGES ON SCHEMA walgreens_prod.gold TO `data-engineers@walgreens.com`")

# Row-level security
spark.sql("""
    CREATE FUNCTION walgreens_prod.mask_customer_id(customer_id STRING, user_role STRING)
    RETURNS STRING
    RETURN CASE 
        WHEN user_role = 'admin' THEN customer_id
        ELSE CONCAT('***', RIGHT(customer_id, 4))
    END
""")
```

This comprehensive guide covers everything I use daily at Walgreens to build reliable, performant data pipelines with PySpark and Databricks!

