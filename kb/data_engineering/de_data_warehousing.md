---
tags: [data-engineer, data-warehousing, snowflake, dimensional-modeling, star-schema, scd]
persona: de
---

# Data Warehousing - Krishna's Expertise

## Introduction
**Krishna's Warehousing Background:**
I've designed and implemented data warehouse solutions at Walgreens and previous companies. From dimensional modeling to Snowflake optimization, here's what I've learned about building enterprise warehouses.

## Dimensional Modeling

### Star Schema Design
**Krishna's Approach:**
Star schema is my go-to for most analytics use cases - it's simple for users and performs well.

**Example: Sales Data Warehouse**
```sql
-- Fact Table: fct_sales
CREATE TABLE fct_sales (
    sale_id BIGINT PRIMARY KEY,
    date_key INT NOT NULL,              -- FK to dim_date
    customer_key BIGINT NOT NULL,       -- FK to dim_customer
    product_key BIGINT NOT NULL,        -- FK to dim_product
    store_key BIGINT NOT NULL,          -- FK to dim_store
    
    -- Measures (additive)
    quantity INT,
    unit_price DECIMAL(18,2),
    discount_amount DECIMAL(18,2),
    tax_amount DECIMAL(18,2),
    total_amount DECIMAL(18,2),
    cost_amount DECIMAL(18,2),
    profit_amount DECIMAL(18,2),
    
    -- Audit columns
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Dimension Table: dim_customer
CREATE TABLE dim_customer (
    customer_key BIGINT PRIMARY KEY,    -- Surrogate key
    customer_id VARCHAR(50) NOT NULL,   -- Natural key
    
    -- Attributes
    customer_name VARCHAR(200),
    customer_email VARCHAR(200),
    customer_segment VARCHAR(50),
    customer_tier VARCHAR(20),
    
    -- Address
    street VARCHAR(200),
    city VARCHAR(100),
    state VARCHAR(50),
    zip_code VARCHAR(20),
    country VARCHAR(50),
    
    -- SCD Type 2 fields
    effective_date DATE NOT NULL,
    end_date DATE,
    is_current BOOLEAN DEFAULT TRUE,
    
    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Dimension Table: dim_date
CREATE TABLE dim_date (
    date_key INT PRIMARY KEY,           -- YYYYMMDD format
    date DATE NOT NULL,
    
    -- Day attributes
    day_of_week INT,
    day_name VARCHAR(10),
    day_of_month INT,
    day_of_year INT,
    
    -- Week attributes
    week_of_year INT,
    week_start_date DATE,
    week_end_date DATE,
    
    -- Month attributes
    month_number INT,
    month_name VARCHAR(10),
    month_abbr VARCHAR(3),
    quarter INT,
    
    -- Year attributes
    year INT,
    fiscal_year INT,
    fiscal_quarter INT,
    
    -- Flags
    is_weekend BOOLEAN,
    is_holiday BOOLEAN,
    holiday_name VARCHAR(100),
    is_business_day BOOLEAN
);
```

### Slowly Changing Dimensions (SCD)

**SCD Type 1 (Overwrite):**
```sql
-- Update customer segment (no history)
UPDATE dim_customer
SET customer_segment = 'Gold',
    updated_at = CURRENT_TIMESTAMP
WHERE customer_id = 'CUST001';
```

**SCD Type 2 (Historical Tracking):**
```python
# Krishna's SCD Type 2 Implementation
def apply_scd_type2(new_df, target_table, natural_key, change_columns):
    """
    Implement SCD Type 2 for dimension table
    """
    from pyspark.sql import functions as F
    from delta.tables import DeltaTable
    
    # Read current dimension
    current_df = spark.table(target_table).filter("is_current = true")
    
    # Find changed records
    changed_df = (
        new_df.alias("new")
        .join(
            current_df.alias("current"),
            natural_key,
            "inner"
        )
        .where(
            # Check if any change column differs
            " OR ".join([f"new.{col} != current.{col}" for col in change_columns])
        )
        .select("new.*")
    )
    
    # Step 1: Expire old records
    delta_table = DeltaTable.forName(spark, target_table)
    
    (
        delta_table.alias("target")
        .merge(
            changed_df.alias("updates"),
            f"target.{natural_key} = updates.{natural_key} AND target.is_current = true"
        )
        .whenMatchedUpdate(
            set={
                "end_date": F.current_date(),
                "is_current": F.lit(False),
                "updated_at": F.current_timestamp()
            }
        )
        .execute()
    )
    
    # Step 2: Insert new versions
    new_versions = (
        changed_df
        .withColumn("effective_date", F.current_date())
        .withColumn("end_date", F.lit(None).cast("date"))
        .withColumn("is_current", F.lit(True))
        .withColumn("created_at", F.current_timestamp())
        .withColumn("updated_at", F.current_timestamp())
    )
    
    new_versions.write.format("delta").mode("append").saveAsTable(target_table)
    
    # Step 3: Insert truly new customers
    new_customers = (
        new_df.alias("new")
        .join(
            current_df.alias("current"),
            natural_key,
            "left_anti"
        )
        .withColumn("effective_date", F.current_date())
        .withColumn("end_date", F.lit(None).cast("date"))
        .withColumn("is_current", F.lit(True))
    )
    
    new_customers.write.format("delta").mode("append").saveAsTable(target_table)

# Usage
apply_scd_type2(
    new_df=df_new_customers,
    target_table="dim_customer",
    natural_key="customer_id",
    change_columns=["customer_segment", "customer_tier", "city", "state"]
)
```

**SCD Type 3 (Limited History):**
```sql
-- Track previous value only
ALTER TABLE dim_customer
ADD COLUMN previous_segment VARCHAR(50),
ADD COLUMN segment_change_date DATE;

UPDATE dim_customer
SET previous_segment = customer_segment,
    segment_change_date = CURRENT_DATE,
    customer_segment = 'Platinum'
WHERE customer_id = 'CUST001';
```

## Snowflake Platform

### Snowflake Architecture
**Krishna's Snowflake Setup:**

**1. Virtual Warehouse Configuration:**
```sql
-- Create warehouses for different workloads
CREATE WAREHOUSE etl_warehouse
    WAREHOUSE_SIZE = 'LARGE'
    AUTO_SUSPEND = 300          -- 5 minutes
    AUTO_RESUME = TRUE
    INITIALLY_SUSPENDED = TRUE
    COMMENT = 'ETL and data loading';

CREATE WAREHOUSE analytics_warehouse
    WAREHOUSE_SIZE = 'MEDIUM'
    AUTO_SUSPEND = 120          -- 2 minutes
    AUTO_RESUME = TRUE
    MIN_CLUSTER_COUNT = 1
    MAX_CLUSTER_COUNT = 3
    SCALING_POLICY = 'STANDARD'
    COMMENT = 'Ad-hoc analytics queries';

CREATE WAREHOUSE reporting_warehouse
    WAREHOUSE_SIZE = 'SMALL'
    AUTO_SUSPEND = 60
    AUTO_RESUME = TRUE
    COMMENT = 'Scheduled reports and dashboards';
```

**2. Database & Schema Structure:**
```sql
-- Create database hierarchy
CREATE DATABASE walgreens_dwh;

USE DATABASE walgreens_dwh;

CREATE SCHEMA raw COMMENT = 'Raw landing data';
CREATE SCHEMA staging COMMENT = 'Staging transformations';
CREATE SCHEMA dwh COMMENT = 'Production data warehouse';
CREATE SCHEMA analytics COMMENT = 'Analytics views and aggregations';
```

### Snowflake Load Patterns

**1. COPY INTO (Bulk Load):**
```sql
-- Load from S3/Azure Blob
COPY INTO raw.orders
FROM @raw_stage/orders/2024-01-15/
FILE_FORMAT = (
    TYPE = 'CSV'
    FIELD_DELIMITER = ','
    SKIP_HEADER = 1
    NULL_IF = ('NULL', 'null', '')
    EMPTY_FIELD_AS_NULL = TRUE
)
ON_ERROR = 'CONTINUE'
PURGE = TRUE;  -- Delete files after successful load
```

**2. Snowpipe (Continuous Loading):**
```sql
-- Create pipe for auto-ingestion
CREATE PIPE raw.orders_pipe
    AUTO_INGEST = TRUE
    AS
    COPY INTO raw.orders
    FROM @raw_stage/orders/
    FILE_FORMAT = (TYPE = 'CSV' SKIP_HEADER = 1);

-- Show pipe status
SELECT SYSTEM$PIPE_STATUS('raw.orders_pipe');
```

**3. External Tables:**
```sql
-- Query data without loading
CREATE EXTERNAL TABLE raw.ext_orders
WITH LOCATION = @raw_stage/orders/
FILE_FORMAT = (TYPE = 'PARQUET')
AUTO_REFRESH = TRUE;

-- Query like a normal table
SELECT * FROM raw.ext_orders WHERE order_date = '2024-01-15';
```

### Snowflake Performance Optimization

**1. Clustering Keys:**
```sql
-- Add clustering for frequently filtered columns
ALTER TABLE fct_sales
CLUSTER BY (order_date, customer_id);

-- Check clustering quality
SELECT SYSTEM$CLUSTERING_INFORMATION('fct_sales');

-- Reclustering (automatic by default)
ALTER TABLE fct_sales RESUME RECLUSTER;
```

**2. Materialized Views:**
```sql
-- Pre-aggregate for faster queries
CREATE MATERIALIZED VIEW mv_daily_sales AS
SELECT
    order_date,
    customer_segment,
    product_category,
    COUNT(*) as order_count,
    SUM(total_amount) as total_sales,
    AVG(total_amount) as avg_order_value
FROM fct_sales s
JOIN dim_customer c ON s.customer_key = c.customer_key
JOIN dim_product p ON s.product_key = p.product_key
WHERE c.is_current = TRUE
GROUP BY order_date, customer_segment, product_category;

-- Queries use materialized view automatically
```

**3. Search Optimization:**
```sql
-- Optimize for point lookups
ALTER TABLE dim_customer
ADD SEARCH OPTIMIZATION ON EQUALITY(customer_id, customer_email);

-- Check optimization status
SELECT * FROM TABLE(SYSTEM$SEARCH_OPTIMIZATION_HISTORY('dim_customer'));
```

### Snowflake Cost Optimization

**Krishna's Cost-Saving Strategies:**

**1. Warehouse Auto-Suspend:**
```sql
-- Aggressive auto-suspend for development
ALTER WAREHOUSE dev_warehouse SET AUTO_SUSPEND = 60;  -- 1 minute

-- Moderate for production
ALTER WAREHOUSE prod_warehouse SET AUTO_SUSPEND = 300;  -- 5 minutes
```

**2. Result Caching:**
```sql
-- Queries return cached results (24 hours) - FREE!
-- No code change needed, automatic

-- Check if query used cache
SELECT * FROM TABLE(INFORMATION_SCHEMA.QUERY_HISTORY())
WHERE QUERY_ID = 'xxx'
  AND BYTES_SCANNED = 0;  -- Indicates cache hit
```

**3. Query Optimization:**
```sql
-- BAD: Full table scan
SELECT * FROM fct_sales
WHERE YEAR(order_date) = 2024;

-- GOOD: Uses clustering/partitioning
SELECT * FROM fct_sales
WHERE order_date >= '2024-01-01'
  AND order_date < '2025-01-01';

-- BETTER: Limit columns
SELECT order_id, customer_id, total_amount
FROM fct_sales
WHERE order_date >= '2024-01-01'
  AND order_date < '2025-01-01';
```

**4. Table Type Selection:**
```sql
-- Transient tables (no fail-safe, cheaper)
CREATE TRANSIENT TABLE staging.temp_data AS
SELECT * FROM raw.orders;

-- Temporary tables (session-scoped, cheapest)
CREATE TEMPORARY TABLE temp_calc AS
SELECT customer_id, SUM(total_amount) as total
FROM fct_sales
GROUP BY customer_id;
```

## Data Warehouse Best Practices

### Surrogate Keys
**Krishna's Key Generation:**
```sql
-- Generate surrogate keys with sequence
CREATE SEQUENCE customer_key_seq START = 1 INCREMENT = 1;

INSERT INTO dim_customer (
    customer_key,
    customer_id,
    customer_name,
    effective_date,
    is_current
)
SELECT
    customer_key_seq.NEXTVAL,
    customer_id,
    customer_name,
    CURRENT_DATE,
    TRUE
FROM staging.stg_customers;
```

### Fact Table Granularity
**Krishna's Granularity Decisions:**

**Transaction Grain (Most Detailed):**
```sql
-- One row per order line item
CREATE TABLE fct_order_lines (
    order_line_id BIGINT PRIMARY KEY,
    order_id VARCHAR(50),
    date_key INT,
    customer_key BIGINT,
    product_key BIGINT,
    quantity INT,
    line_amount DECIMAL(18,2)
);
```

**Daily Grain (Aggregated):**
```sql
-- One row per customer per product per day
CREATE TABLE fct_daily_sales (
    date_key INT,
    customer_key BIGINT,
    product_key BIGINT,
    order_count INT,
    total_quantity INT,
    total_amount DECIMAL(18,2),
    PRIMARY KEY (date_key, customer_key, product_key)
);
```

### Conformed Dimensions
**Krishna's Shared Dimensions:**
```sql
-- dim_date used by ALL fact tables
-- dim_customer used by sales, service, marketing
-- dim_product used by sales, inventory, procurement

-- This enables cross-functional analysis:
SELECT
    d.month_name,
    SUM(s.total_amount) as sales_revenue,
    SUM(i.inventory_value) as avg_inventory,
    SUM(s.total_amount) / NULLIF(SUM(i.inventory_value), 0) as inventory_turnover
FROM fct_sales s
FULL OUTER JOIN fct_inventory i 
    ON s.date_key = i.date_key 
    AND s.product_key = i.product_key
JOIN dim_date d ON COALESCE(s.date_key, i.date_key) = d.date_key
WHERE d.year = 2024
GROUP BY d.month_name;
```

## ETL to Data Warehouse

### Incremental Load Pattern
**Krishna's Production Pattern:**
```python
def incremental_load_dimension(source_table, target_table, natural_key):
    """
    Incremental load with upsert
    """
    from pyspark.sql import functions as F
    
    # Read incremental data
    df_new = spark.table(f"staging.{source_table}")
    
    # Read current dimension
    df_current = spark.table(f"dwh.{target_table}").filter("is_current = true")
    
    # Identify new, changed, and unchanged records
    df_joined = df_new.alias("new").join(
        df_current.alias("current"),
        natural_key,
        "left"
    )
    
    # New records (insert)
    df_inserts = (
        df_joined
        .where("current.customer_key IS NULL")
        .select("new.*")
        .withColumn("customer_key", F.expr("uuid()"))
        .withColumn("effective_date", F.current_date())
        .withColumn("is_current", F.lit(True))
    )
    
    # Changed records (SCD Type 2)
    df_updates = (
        df_joined
        .where(
            "current.customer_key IS NOT NULL AND "
            "(new.customer_segment != current.customer_segment OR "
            " new.city != current.city)"
        )
        .select("new.*", "current.customer_key")
    )
    
    # Apply updates
    apply_scd_type2(df_updates, target_table, natural_key, ["customer_segment", "city"])
    
    # Insert new records
    df_inserts.write.mode("append").saveAsTable(f"dwh.{target_table}")
```

### Data Quality in DWH
**Krishna's Quality Framework:**
```sql
-- Quality checks before loading to warehouse
CREATE OR REPLACE PROCEDURE validate_data_quality(table_name VARCHAR)
RETURNS VARCHAR
LANGUAGE SQL
AS
$$
BEGIN
    -- Check 1: No duplicates on natural key
    LET dup_count INT := (
        SELECT COUNT(*) FROM (
            SELECT customer_id, COUNT(*)
            FROM staging.stg_customers
            GROUP BY customer_id
            HAVING COUNT(*) > 1
        )
    );
    
    IF (dup_count > 0) THEN
        RETURN 'FAILED: Found ' || dup_count || ' duplicate customer_ids';
    END IF;
    
    -- Check 2: Required fields not null
    LET null_count INT := (
        SELECT COUNT(*)
        FROM staging.stg_customers
        WHERE customer_id IS NULL OR customer_name IS NULL
    );
    
    IF (null_count > 0) THEN
        RETURN 'FAILED: Found ' || null_count || ' records with null required fields';
    END IF;
    
    -- Check 3: Valid values
    LET invalid_segment INT := (
        SELECT COUNT(*)
        FROM staging.stg_customers
        WHERE customer_segment NOT IN ('Bronze', 'Silver', 'Gold', 'Platinum')
    );
    
    IF (invalid_segment > 0) THEN
        RETURN 'FAILED: Found ' || invalid_segment || ' invalid customer segments';
    END IF;
    
    RETURN 'PASSED';
END;
$$;

-- Run quality checks
CALL validate_data_quality('stg_customers');
```

These warehousing patterns ensure our analytics are reliable, performant, and scalable at Walgreens!

