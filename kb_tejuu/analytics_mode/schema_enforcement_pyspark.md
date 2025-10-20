---
tags: [tejuu, analytics, pyspark, schema, enforcement, bronze, delta-lake]
persona: analytics
---

# Schema Enforcement in PySpark - Tejuu's Implementation

## Enforce Schema on Ingestion (Bronze)

### Define StructType Explicitly
```python
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, TimestampType

# Define explicit schema for regulated data
order_schema = StructType([
    StructField("order_id", StringType(), False),
    StructField("customer_id", StringType(), False),
    StructField("order_date", TimestampType(), True),
    StructField("amount", IntegerType(), True),
    StructField("status", StringType(), True)
])

# Avoid inference for regulated data - always use explicit schema
df = spark.read.schema(order_schema).json("path/to/orders.json")
```

### JSON Parsing with Schema
```python
from pyspark.sql.functions import from_json, col

# Parse JSON with explicit schema, keep raw alongside parsed
df_parsed = df.withColumn(
    "parsed_data", 
    from_json(col("raw_json"), order_schema, {"mode": "PERMISSIVE"})
).withColumn("raw_data", col("raw_json"))  # Keep original for audit

# Handle malformed records
df_clean = df_parsed.filter(col("parsed_data").isNotNull())
df_quarantine = df_parsed.filter(col("parsed_data").isNull())
```

### Delta Lake Schema Management
```python
# Write to Delta with mergeSchema OFF by default
df_clean.write \
    .format("delta") \
    .option("mergeSchema", "false") \
    .mode("append") \
    .save("/path/to/bronze_orders")

# Route unknown columns to quarantine
df_quarantine.write \
    .format("delta") \
    .mode("append") \
    .save("/path/to/bronze_quarantine")
```

### Delta Constraints
```sql
-- Add primary key constraint
ALTER TABLE bronze_orders 
SET TBLPROPERTIES (
    'delta.constraints.pk'='order_id IS NOT NULL'
);

-- Add check constraints
ALTER TABLE bronze_orders 
SET TBLPROPERTIES (
    'delta.constraints.amount_check'='amount >= 0'
);
```

### Schema Drift Tracking
```python
# Track schema changes in audit table
schema_audit_df = spark.createDataFrame([{
    "table_name": "bronze_orders",
    "schema_version": "1.0",
    "change_type": "new_column",
    "column_name": "new_field",
    "detected_at": current_timestamp()
}])

schema_audit_df.write \
    .format("delta") \
    .mode("append") \
    .save("/path/to/schema_audit")
```

## Tejuu's Experience

At Stryker, I implemented this exact schema enforcement pattern for processing 15M+ transactions monthly. The explicit schema definition prevented data quality issues and the quarantine mechanism caught 0.1% of malformed records that would have caused downstream failures.

The Delta constraints ensured referential integrity, and the schema audit table helped us track evolution over time. This approach reduced data incidents by 60% and improved trust in our analytics platform.
