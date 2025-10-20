---
tags: [data-engineer, pipeline-architecture, medallion-architecture, etl, elt, data-lake]
persona: de
---

# Data Pipeline Architecture - Krishna's Design Patterns

## Introduction
**Krishna's Architecture Philosophy:**
At Walgreens, I've designed and implemented modern data architectures processing 10TB+ monthly. Good architecture isn't just about technology - it's about reliability, scalability, and making data accessible to business users.

## Medallion Architecture

### Overview
**Krishna's Implementation:**
Medallion architecture is the foundation of our Walgreens data platform - Bronze (raw), Silver (cleaned), Gold (business).

**Benefits I've Seen:**
- Clear data lineage and quality progression
- Separation of concerns (ingestion vs transformation)
- Easy rollback and recovery
- Scalable and maintainable

### Bronze Layer (Raw/Landing)
**Purpose:** Ingest data as-is, no transformation

```python
# Bronze Layer - Raw Ingestion
def bronze_ingestion(source_path: str, bronze_path: str, execution_date: str):
    """
    Ingest raw data with minimal transformation
    - Schema-on-read (no enforcement)
    - Keep all source columns
    - Add ingestion metadata
    """
    from pyspark.sql import functions as F
    
    df_raw = (
        spark.read
        .format("csv")
        .option("header", "true")
        .option("inferSchema", "true")
        .load(f"{source_path}/date={execution_date}")
        
        # Add metadata only
        .withColumn("_ingestion_timestamp", F.current_timestamp())
        .withColumn("_ingestion_date", F.lit(execution_date))
        .withColumn("_source_file", F.input_file_name())
    )
    
    # Write to Bronze (append mode)
    df_raw.write \
        .format("delta") \
        .mode("append") \
        .partitionBy("_ingestion_date") \
        .save(bronze_path)
```

### Silver Layer (Cleaned/Standardized)
**Purpose:** Clean, validate, standardize data

```python
# Silver Layer - Data Quality & Standardization
def silver_transformation(bronze_path: str, silver_path: str, execution_date: str):
    """
    Apply data quality rules and standardization
    - Schema enforcement
    - Data type conversions
    - Deduplication
    - Validation
    - Business rules
    """
    from pyspark.sql import functions as F, Window
    
    df_bronze = spark.read.format("delta").load(f"{bronze_path}/_ingestion_date={execution_date}")
    
    # Data quality transformation
    df_silver = (
        df_bronze
        
        # Schema enforcement & type casting
        .select(
            F.col("order_id").cast("string"),
            F.col("customer_id").cast("string"),
            F.to_date("order_date", "yyyy-MM-dd").alias("order_date"),
            F.col("order_amount").cast("decimal(18,2)"),
            F.col("order_status").cast("string")
        )
        
        # Data cleaning
        .filter(F.col("order_id").isNotNull())
        .filter(F.col("order_amount") >= 0)
        .withColumn("order_status", F.upper(F.trim(F.col("order_status"))))
        
        # Deduplication (keep latest record)
        .withColumn(
            "row_num",
            F.row_number().over(
                Window.partitionBy("order_id")
                .orderBy(F.desc("_ingestion_timestamp"))
            )
        )
        .filter(F.col("row_num") == 1)
        .drop("row_num")
        
        # Add quality metadata
        .withColumn("_silver_processed_timestamp", F.current_timestamp())
        .withColumn("_data_quality_score", F.lit(100))  # Could be calculated
    )
    
    # Write to Silver (overwrite by partition)
    df_silver.write \
        .format("delta") \
        .mode("overwrite") \
        .partitionBy("order_date") \
        .option("overwriteSchema", "true") \
        .save(silver_path)
```

### Gold Layer (Business/Aggregated)
**Purpose:** Business-ready data models

```python
# Gold Layer - Business Logic & Aggregations
def gold_aggregation(silver_path: str, gold_path: str):
    """
    Create business-ready aggregations
    - Fact and dimension tables
    - Business metrics
    - Optimized for analytics
    """
    from pyspark.sql import functions as F
    
    df_silver = spark.read.format("delta").load(silver_path)
    
    # Daily sales summary (Gold fact table)
    df_gold = (
        df_silver
        .filter(F.col("order_status") == "COMPLETED")
        .groupBy(
            F.col("order_date"),
            F.col("customer_segment"),
            F.col("product_category")
        )
        .agg(
            F.count("order_id").alias("order_count"),
            F.sum("order_amount").alias("total_sales"),
            F.avg("order_amount").alias("avg_order_value"),
            F.countDistinct("customer_id").alias("unique_customers"),
            F.min("order_amount").alias("min_order"),
            F.max("order_amount").alias("max_order")
        )
        .withColumn("_gold_created_timestamp", F.current_timestamp())
    )
    
    # Write to Gold (overwrite)
    df_gold.write \
        .format("delta") \
        .mode("overwrite") \
        .partitionBy("order_date") \
        .save(gold_path)
```

## Incremental Processing Patterns

### Change Data Capture (CDC)
**Krishna's CDC Implementation:**

```python
# CDC Pattern with Merge
from delta.tables import DeltaTable

def incremental_upsert(source_path: str, target_path: str, key_column: str):
    """
    Apply incremental changes using merge (upsert)
    """
    # Read incremental data
    df_incremental = spark.read.format("delta").load(source_path)
    
    # Get target Delta table
    delta_table = DeltaTable.forPath(spark, target_path)
    
    # Merge (upsert) logic
    (
        delta_table.alias("target")
        .merge(
            df_incremental.alias("source"),
            f"target.{key_column} = source.{key_column}"
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

### Watermark-Based Incremental
**Krishna's Watermark Pattern:**

```python
# Watermark tracking for incremental loads
def get_last_watermark(table_name: str) -> str:
    """Get last successfully processed watermark"""
    watermark_df = spark.sql(f"""
        SELECT MAX(watermark_value) as last_watermark
        FROM control.watermarks
        WHERE table_name = '{table_name}'
          AND status = 'SUCCESS'
    """)
    
    return watermark_df.first()['last_watermark'] or '1900-01-01'

def update_watermark(table_name: str, watermark_value: str, status: str):
    """Update watermark after processing"""
    spark.sql(f"""
        INSERT INTO control.watermarks
        VALUES ('{table_name}', '{watermark_value}', '{status}', CURRENT_TIMESTAMP())
    """)

# Incremental processing with watermark
def incremental_load(source_table: str, target_path: str):
    """Process only new/changed records"""
    last_watermark = get_last_watermark(source_table)
    
    df_incremental = spark.read \
        .format("delta") \
        .load(f"/mnt/raw/{source_table}") \
        .filter(F.col("updated_at") > last_watermark)
    
    if df_incremental.count() == 0:
        print("No new data to process")
        return
    
    # Process and write
    df_clean = transform_data(df_incremental)
    df_clean.write.format("delta").mode("append").save(target_path)
    
    # Update watermark
    new_watermark = df_incremental.agg(F.max("updated_at")).first()[0]
    update_watermark(source_table, str(new_watermark), 'SUCCESS')
```

## ETL vs ELT

### ETL (Extract-Transform-Load)
**When Krishna Uses ETL:**
```python
# ETL: Transform before loading
def etl_pattern(source_path: str, target_path: str):
    """
    Transform data BEFORE loading to target
    Good for: Complex transformations, data reduction, legacy systems
    """
    # Extract
    df_raw = spark.read.csv(source_path)
    
    # Transform (heavy transformation)
    df_transformed = (
        df_raw
        .filter(F.col("status") == "active")
        .join(reference_data, "id")
        .groupBy("category").agg(F.sum("amount"))
        .filter(F.col("sum(amount)") > 1000)
    )
    
    # Load (small, transformed data)
    df_transformed.write.mode("overwrite").save(target_path)
```

### ELT (Extract-Load-Transform)
**When Krishna Uses ELT:**
```python
# ELT: Load raw, then transform
def elt_pattern(source_path: str, raw_path: str, transformed_path: str):
    """
    Load raw data THEN transform
    Good for: Data lakes, cloud platforms, flexibility
    """
    # Extract and Load (minimal transformation)
    df_raw = spark.read.csv(source_path)
    df_raw.write.mode("append").save(raw_path)
    
    # Transform later (on demand or scheduled)
    df_raw_stored = spark.read.parquet(raw_path)
    df_transformed = transform_complex_logic(df_raw_stored)
    df_transformed.write.mode("overwrite").save(transformed_path)
```

**Krishna's Decision Matrix:**
- **ETL:** Legacy source systems, complex transformations, small result sets
- **ELT:** Cloud data lakes, large data volumes, need for flexibility

## Batch vs Streaming

### Batch Processing
**Krishna's Batch Pattern:**
```python
# Daily batch processing
def daily_batch_pipeline(execution_date: str):
    """
    Process full day of data in batch
    Latency: Hours, Throughput: High, Cost: Low
    """
    # Read full partition
    df = spark.read.format("delta") \
        .load(f"/mnt/raw/orders/date={execution_date}")
    
    # Process entire partition
    df_processed = transform_batch(df)
    
    # Write results
    df_processed.write.format("delta") \
        .mode("overwrite") \
        .save(f"/mnt/silver/orders/date={execution_date}")
```

### Streaming Processing
**Krishna's Streaming Pattern:**
```python
# Real-time streaming
def realtime_streaming_pipeline():
    """
    Process data as it arrives
    Latency: Seconds, Throughput: Medium, Cost: High
    """
    from pyspark.sql import functions as F
    
    # Read stream from Event Hub
    df_stream = (
        spark.readStream
        .format("kafka")
        .option("kafka.bootstrap.servers", "eventhub:9093")
        .option("subscribe", "orders")
        .load()
    )
    
    # Parse and transform
    df_parsed = (
        df_stream
        .select(F.from_json(F.col("value").cast("string"), schema).alias("data"))
        .select("data.*")
        .withColumn("processing_time", F.current_timestamp())
    )
    
    # Write stream to Delta
    query = (
        df_parsed.writeStream
        .format("delta")
        .outputMode("append")
        .option("checkpointLocation", "/mnt/checkpoints/orders")
        .trigger(processingTime="1 minute")
        .start("/mnt/silver/orders_realtime")
    )
    
    query.awaitTermination()
```

## Error Handling & Monitoring

### Robust Error Handling
**Krishna's Pattern:**
```python
def robust_pipeline(source_path: str, target_path: str):
    """Pipeline with comprehensive error handling"""
    import traceback
    
    try:
        # Pre-checks
        if not path_exists(source_path):
            raise ValueError(f"Source path not found: {source_path}")
        
        # Process
        df = spark.read.format("delta").load(source_path)
        
        if df.count() == 0:
            logger.warning("No data to process")
            return {"status": "NO_DATA", "rows_processed": 0}
        
        df_transformed = transform_with_quality_checks(df)
        
        # Validate output
        assert df_transformed.count() > 0, "Transformation resulted in no data"
        
        # Write with retry
        for attempt in range(3):
            try:
                df_transformed.write.format("delta").mode("overwrite").save(target_path)
                break
            except Exception as e:
                if attempt == 2:
                    raise
                logger.warning(f"Write attempt {attempt + 1} failed, retrying...")
                time.sleep(60)
        
        return {
            "status": "SUCCESS",
            "rows_processed": df_transformed.count()
        }
        
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Write to error table
        error_record = {
            "pipeline_name": "my_pipeline",
            "error_message": str(e),
            "error_traceback": traceback.format_exc(),
            "timestamp": datetime.now()
        }
        log_error_to_table(error_record)
        
        # Send alert
        send_slack_alert(f"Pipeline failed: {str(e)}")
        
        raise
```

These architecture patterns ensure our Walgreens pipelines are reliable, scalable, and maintainable!

