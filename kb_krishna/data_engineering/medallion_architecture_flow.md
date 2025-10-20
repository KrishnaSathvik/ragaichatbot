---
tags: [krishna, data-engineering, medallion, bronze, silver, gold, delta-lake, pyspark]
persona: de
---

# Medallion Architecture End-to-End Flow - Krishna's Implementation

## Bronze → Silver → Gold Flow

### Bronze Layer: Raw Data Landing
```python
from pyspark.sql.functions import current_timestamp, input_file_name, monotonically_increasing_id

# Land raw data with metadata
bronze_df = spark.read.json("path/to/raw/pharmacy/") \
    .withColumn("_ingest_ts", current_timestamp()) \
    .withColumn("_source_file", input_file_name()) \
    .withColumn("_batch_id", monotonically_increasing_id())

# Write to Delta with partitioning
bronze_df.write \
    .format("delta") \
    .partitionBy("year", "month", "day") \
    .mode("append") \
    .save("/path/to/bronze/pharmacy_orders")
```

### Silver Layer: Cleaned and Standardized
```python
from pyspark.sql.window import Window
from pyspark.sql.functions import row_number, col, when, coalesce

# Deduplication using window functions
window_spec = Window.partitionBy("prescription_id").orderBy(col("update_ts").desc())

silver_df = bronze_df \
    .withColumn("row_num", row_number().over(window_spec)) \
    .filter(col("row_num") == 1) \
    .drop("row_num") \
    .withColumn("prescription_status", 
        when(col("status").isNull(), "UNKNOWN")
        .otherwise(col("status"))) \
    .withColumn("quantity_standardized", 
        coalesce(col("quantity"), col("qty"), col("amount")))

# SCD2 for dimensions
dim_patient_scd2 = silver_df.select("patient_id", "patient_name", "update_ts") \
    .withColumn("effective_date", col("update_ts")) \
    .withColumn("expiry_date", 
        when(col("update_ts").isNull(), None)
        .otherwise(lead("update_ts").over(Window.partitionBy("patient_id").orderBy("update_ts"))))
```

### Gold Layer: Business-Ready Aggregations
```python
# MERGE INTO fact table
fact_prescriptions = spark.sql("""
    MERGE INTO gold.fact_prescriptions AS target
    USING silver.prescriptions_delta AS source
    ON target.prescription_id = source.prescription_id
    WHEN MATCHED THEN UPDATE SET
        quantity = source.quantity_standardized,
        status = source.prescription_status,
        updated_at = current_timestamp()
    WHEN NOT MATCHED THEN INSERT (
        prescription_id, patient_id, quantity, status, created_at
    ) VALUES (
        source.prescription_id, source.patient_id, 
        source.quantity_standardized, source.prescription_status,
        current_timestamp()
    )
""")

# Build dimension tables
dim_medication = spark.sql("""
    SELECT DISTINCT
        medication_id,
        medication_name,
        drug_class,
        manufacturer,
        current_timestamp() as created_at
    FROM silver.prescriptions_delta
    WHERE medication_id IS NOT NULL
""")

# Expose to Power BI with RLS
spark.sql("""
    CREATE VIEW gold.vw_prescriptions_bi AS
    SELECT 
        f.prescription_id,
        f.quantity,
        f.status,
        p.patient_name,
        m.medication_name,
        s.store_name
    FROM gold.fact_prescriptions f
    LEFT JOIN gold.dim_patient p ON f.patient_id = p.patient_id
    LEFT JOIN gold.dim_medication m ON f.medication_id = m.medication_id
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
    .load("/path/to/bronze/pharmacy_orders")

# Update control table only on success
if incremental_df.count() > 0:
    # Process data...
    
    # Update watermark only after successful processing
    spark.sql(f"""
        UPDATE control.watermark_table 
        SET last_processed = '{watermark_value}'
        WHERE table_name = 'pharmacy_orders'
    """)
```

## Krishna's Experience

At Walgreens, I implemented this exact medallion architecture for processing 10TB+ monthly data across pharmacy, retail, and supply chain systems. The Bronze layer handled raw data ingestion with proper metadata tracking, Silver layer ensured data quality through deduplication and standardization, and Gold layer provided business-ready aggregations.

The incremental processing with watermark control prevented reprocessing of data and ensured failed runs didn't advance the watermark. This architecture reduced processing time by 35% and enabled real-time analytics for 500+ business users at Walgreens.
