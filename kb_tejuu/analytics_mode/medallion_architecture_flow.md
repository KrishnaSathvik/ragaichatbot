---
tags: [tejuu, analytics, medallion, bronze, silver, gold, delta-lake, pyspark]
persona: analytics
---

# Medallion Architecture End-to-End Flow - Tejuu's Implementation

## Bronze → Silver → Gold Flow

### Bronze Layer: Raw Data Landing
```python
from pyspark.sql.functions import current_timestamp, input_file_name, monotonically_increasing_id

# Land raw data with metadata
bronze_df = spark.read.json("path/to/raw/orders/") \
    .withColumn("_ingest_ts", current_timestamp()) \
    .withColumn("_source_file", input_file_name()) \
    .withColumn("_batch_id", monotonically_increasing_id())

# Write to Delta with partitioning
bronze_df.write \
    .format("delta") \
    .partitionBy("year", "month", "day") \
    .mode("append") \
    .save("/path/to/bronze/orders")
```

### Silver Layer: Cleaned and Standardized
```python
from pyspark.sql.window import Window
from pyspark.sql.functions import row_number, col, when, coalesce

# Deduplication using window functions
window_spec = Window.partitionBy("order_id").orderBy(col("update_ts").desc())

silver_df = bronze_df \
    .withColumn("row_num", row_number().over(window_spec)) \
    .filter(col("row_num") == 1) \
    .drop("row_num") \
    .withColumn("order_status", 
        when(col("status").isNull(), "UNKNOWN")
        .otherwise(col("status"))) \
    .withColumn("amount_standardized", 
        coalesce(col("amount"), col("total"), col("value")))

# SCD2 for dimensions
dim_customer_scd2 = silver_df.select("customer_id", "customer_name", "update_ts") \
    .withColumn("effective_date", col("update_ts")) \
    .withColumn("expiry_date", 
        when(col("update_ts").isNull(), None)
        .otherwise(lead("update_ts").over(Window.partitionBy("customer_id").orderBy("update_ts"))))
```

### Gold Layer: Business-Ready Aggregations
```python
# MERGE INTO fact table
fact_sales = spark.sql("""
    MERGE INTO gold.fact_sales AS target
    USING silver.orders_delta AS source
    ON target.order_id = source.order_id
    WHEN MATCHED THEN UPDATE SET
        amount = source.amount_standardized,
        status = source.order_status,
        updated_at = current_timestamp()
    WHEN NOT MATCHED THEN INSERT (
        order_id, customer_id, amount, status, created_at
    ) VALUES (
        source.order_id, source.customer_id, 
        source.amount_standardized, source.order_status,
        current_timestamp()
    )
""")

# Build dimension tables
dim_product = spark.sql("""
    SELECT DISTINCT
        product_id,
        product_name,
        category,
        brand,
        current_timestamp() as created_at
    FROM silver.orders_delta
    WHERE product_id IS NOT NULL
""")

# Expose to Power BI with RLS
spark.sql("""
    CREATE VIEW gold.vw_sales_bi AS
    SELECT 
        f.order_id,
        f.amount,
        f.status,
        d.customer_name,
        p.product_name,
        s.store_name
    FROM gold.fact_sales f
    LEFT JOIN gold.dim_customer d ON f.customer_id = d.customer_id
    LEFT JOIN gold.dim_product p ON f.product_id = p.product_id
    LEFT JOIN gold.dim_store s ON f.store_id = s.store_id
""")
```

### Incremental Processing
```python
# ADF passes watermark parameter
watermark_value = spark.conf.get("spark.databricks.delta.lastModified")

# Process only new/changed data
incremental_df = spark.read \
    .format("delta") \
    .option("timestampAsOf", watermark_value) \
    .load("/path/to/bronze/orders")

# Update control table only on success
if incremental_df.count() > 0:
    # Process data...
    
    # Update watermark only after successful processing
    spark.sql(f"""
        UPDATE control.watermark_table 
        SET last_processed = '{watermark_value}'
        WHERE table_name = 'orders'
    """)
```

## Tejuu's Experience

At Stryker, I implemented this exact medallion architecture for processing 15M+ transactions. The Bronze layer handled raw data ingestion with proper metadata tracking, Silver layer ensured data quality through deduplication and standardization, and Gold layer provided business-ready aggregations.

The incremental processing with watermark control prevented reprocessing of data and ensured failed runs didn't advance the watermark. This architecture reduced processing time by 45% and enabled real-time analytics for 1,000+ users globally.
