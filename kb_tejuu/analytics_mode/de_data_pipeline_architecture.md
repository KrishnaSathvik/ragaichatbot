---
tags: [data-engineer, architecture, etl, elt, pipeline, design, tejuu]
persona: analytics
---

# Data Pipeline Architecture - Tejuu's Experience

## Introduction
**Tejuu's Architecture Philosophy:**
At Central Bank of Missouri, I've designed and built enterprise-scale data pipelines that process millions of records daily. My approach focuses on scalability, reliability, and business value. Let me share the architectural patterns and principles I've learned building production data platforms.

## Data Architecture Patterns

### Medallion Architecture
**Tejuu's Implementation:**

**1. Bronze Layer (Raw Data):**
```sql
-- Bronze layer stores raw, unprocessed data
CREATE TABLE bronze.customer_transactions_raw (
    transaction_id VARCHAR(50),
    customer_id VARCHAR(50),
    transaction_date VARCHAR(20),
    amount VARCHAR(20),
    transaction_type VARCHAR(50),
    raw_data JSON,
    ingested_at TIMESTAMP,
    source_system VARCHAR(50)
)
WITH (
    DISTRIBUTION = ROUND_ROBIN,
    CLUSTERED COLUMNSTORE INDEX
);
```

**2. Silver Layer (Cleaned Data):**
```sql
-- Silver layer with cleaned, validated data
CREATE TABLE silver.customer_transactions (
    transaction_id VARCHAR(50) NOT NULL,
    customer_id VARCHAR(50) NOT NULL,
    transaction_date DATE NOT NULL,
    amount DECIMAL(18,2) NOT NULL,
    transaction_type VARCHAR(50) NOT NULL,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    data_quality_score DECIMAL(5,2)
)
WITH (
    DISTRIBUTION = HASH(customer_id),
    CLUSTERED COLUMNSTORE INDEX
);
```

**3. Gold Layer (Business Aggregations):**
```sql
-- Gold layer with business-ready aggregations
CREATE TABLE gold.daily_customer_summary (
    customer_id VARCHAR(50) NOT NULL,
    transaction_date DATE NOT NULL,
    total_transactions INT,
    total_amount DECIMAL(18,2),
    avg_transaction_amount DECIMAL(18,2),
    transaction_types VARCHAR(500),
    created_at TIMESTAMP
)
WITH (
    DISTRIBUTION = HASH(customer_id),
    CLUSTERED COLUMNSTORE INDEX
);
```

### ETL vs ELT Patterns
**Tejuu's Approach:**

**1. ETL Pattern (Legacy Systems):**
```python
# ETL: Extract, Transform, Load
def etl_legacy_data():
    # Extract from legacy Excel/Access
    df_raw = extract_from_legacy_systems()
    
    # Transform in memory
    df_clean = (
        df_raw
        .filter(col("customer_id").isNotNull())
        .withColumn("amount", col("amount").cast("decimal(18,2)"))
        .withColumn("transaction_date", to_date(col("transaction_date")))
        .dropDuplicates(["transaction_id"])
    )
    
    # Load to target database
    df_clean.write.mode("overwrite").saveAsTable("silver.customer_transactions")
```

**2. ELT Pattern (Modern Cloud):**
```sql
-- ELT: Extract, Load, Transform
-- Extract and Load raw data first
COPY INTO bronze.customer_transactions_raw
FROM 's3://bucket/raw/transactions/'
FILE_FORMAT = (TYPE = 'PARQUET');

-- Transform using SQL (leverage cloud compute)
INSERT INTO silver.customer_transactions
SELECT 
    transaction_id,
    customer_id,
    CAST(transaction_date AS DATE) as transaction_date,
    CAST(amount AS DECIMAL(18,2)) as amount,
    transaction_type,
    CURRENT_TIMESTAMP as created_at,
    CURRENT_TIMESTAMP as updated_at,
    100.0 as data_quality_score
FROM bronze.customer_transactions_raw
WHERE transaction_id IS NOT NULL
  AND customer_id IS NOT NULL
  AND amount IS NOT NULL;
```

## Pipeline Design Principles

### 1. Idempotency
**Tejuu's Idempotent Patterns:**

```python
# Idempotent pipeline - can be run multiple times safely
def process_daily_transactions(execution_date):
    # Check if already processed
    if is_already_processed(execution_date):
        print(f"Data for {execution_date} already processed")
        return
    
    # Process data
    df = extract_transactions(execution_date)
    df_clean = transform_transactions(df)
    load_transactions(df_clean, execution_date)
    
    # Mark as processed
    mark_as_processed(execution_date)
```

### 2. Fault Tolerance
**Tejuu's Error Handling:**

```python
# Robust error handling with retries
import time
from functools import wraps

def retry_on_failure(max_retries=3, delay=60):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise e
                    print(f"Attempt {attempt + 1} failed: {e}")
                    time.sleep(delay)
            return None
        return wrapper
    return decorator

@retry_on_failure(max_retries=3, delay=60)
def load_data_to_warehouse(df, table_name):
    df.write.mode("overwrite").saveAsTable(table_name)
```

### 3. Monitoring & Observability
**Tejuu's Monitoring Setup:**

```python
# Comprehensive pipeline monitoring
def monitor_pipeline_health():
    metrics = {
        'pipeline_start_time': datetime.now(),
        'source_record_count': 0,
        'processed_record_count': 0,
        'error_count': 0,
        'data_quality_score': 0.0
    }
    
    try:
        # Extract
        df_source = extract_data()
        metrics['source_record_count'] = df_source.count()
        
        # Transform
        df_processed = transform_data(df_source)
        metrics['processed_record_count'] = df_processed.count()
        
        # Data quality check
        quality_score = calculate_data_quality(df_processed)
        metrics['data_quality_score'] = quality_score
        
        # Load
        load_data(df_processed)
        
        # Send success metrics
        send_metrics_to_monitoring(metrics)
        
    except Exception as e:
        metrics['error_count'] = 1
        metrics['error_message'] = str(e)
        send_alert_to_team(metrics)
        raise
```

## Data Quality Framework

### 1. Validation Rules
**Tejuu's Data Quality Patterns:**

```python
# Comprehensive data validation
class DataQualityValidator:
    def __init__(self):
        self.rules = {
            'customer_id': {
                'required': True,
                'format': r'^CUST\d{8}$',
                'unique': True
            },
            'amount': {
                'required': True,
                'min_value': 0.01,
                'max_value': 1000000.00,
                'data_type': 'decimal'
            },
            'transaction_date': {
                'required': True,
                'format': 'YYYY-MM-DD',
                'not_future': True
            }
        }
    
    def validate_dataframe(self, df):
        errors = []
        
        for column, rules in self.rules.items():
            if rules.get('required') and df[column].isnull().any():
                errors.append(f"Null values found in {column}")
            
            if 'format' in rules:
                pattern = rules['format']
                invalid_format = df[~df[column].str.match(pattern, na=False)]
                if not invalid_format.empty:
                    errors.append(f"Invalid format in {column}: {len(invalid_format)} records")
            
            if rules.get('unique') and df[column].duplicated().any():
                errors.append(f"Duplicate values found in {column}")
        
        return errors
```

### 2. Data Lineage Tracking
**Tejuu's Lineage Implementation:**

```python
# Track data lineage through pipeline
class DataLineageTracker:
    def __init__(self):
        self.lineage = {}
    
    def track_transformation(self, source_table, target_table, transformation_logic):
        self.lineage[target_table] = {
            'source': source_table,
            'transformation': transformation_logic,
            'timestamp': datetime.now(),
            'record_count': self.get_record_count(target_table)
        }
    
    def get_lineage_report(self, table_name):
        if table_name in self.lineage:
            return self.lineage[table_name]
        return None
```

## Performance Optimization

### 1. Partitioning Strategies
**Tejuu's Partitioning Patterns:**

```sql
-- Partition by date for time-series data
CREATE TABLE fct_transactions (
    transaction_id VARCHAR(50),
    customer_id VARCHAR(50),
    transaction_date DATE,
    amount DECIMAL(18,2)
)
PARTITIONED BY (year INT, month INT, day INT);

-- Partition by customer segment for analytical queries
CREATE TABLE customer_analytics (
    customer_id VARCHAR(50),
    segment VARCHAR(50),
    metrics JSON
)
PARTITIONED BY (segment);
```

### 2. Caching Strategies
**Tejuu's Caching Implementation:**

```python
# Intelligent caching for frequently accessed data
class DataCache:
    def __init__(self, cache_duration=3600):  # 1 hour
        self.cache = {}
        self.cache_duration = cache_duration
    
    def get_cached_data(self, key):
        if key in self.cache:
            data, timestamp = self.cache[key]
            if datetime.now() - timestamp < timedelta(seconds=self.cache_duration):
                return data
        return None
    
    def cache_data(self, key, data):
        self.cache[key] = (data, datetime.now())
```

### 3. Parallel Processing
**Tejuu's Parallel Patterns:**

```python
# Parallel processing for large datasets
from multiprocessing import Pool
import pandas as pd

def process_partition(partition_data):
    # Process individual partition
    df = pd.DataFrame(partition_data)
    return transform_data(df)

def parallel_processing(df, num_processes=4):
    # Split data into partitions
    partitions = [df.iloc[i::num_processes] for i in range(num_processes)]
    
    # Process in parallel
    with Pool(num_processes) as pool:
        results = pool.map(process_partition, partitions)
    
    # Combine results
    return pd.concat(results, ignore_index=True)
```

## Real-Time Data Processing

### 1. Streaming Architecture
**Tejuu's Streaming Patterns:**

```python
# Real-time transaction processing
from pyspark.sql import SparkSession
from pyspark.sql.functions import *

def setup_streaming_pipeline():
    spark = SparkSession.builder \
        .appName("RealTimeTransactions") \
        .getOrCreate()
    
    # Read from Kafka
    df_stream = spark \
        .readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", "localhost:9092") \
        .option("subscribe", "transactions") \
        .load()
    
    # Parse JSON data
    df_parsed = df_stream \
        .select(from_json(col("value").cast("string"), schema).alias("data")) \
        .select("data.*")
    
    # Process in real-time
    df_processed = df_parsed \
        .filter(col("amount") > 0) \
        .withColumn("processed_at", current_timestamp())
    
    # Write to sink
    query = df_processed \
        .writeStream \
        .format("delta") \
        .option("checkpointLocation", "/checkpoint/transactions") \
        .outputMode("append") \
        .start()
    
    return query
```

### 2. Micro-Batch Processing
**Tejuu's Micro-Batch Patterns:**

```python
# Micro-batch processing for near real-time
def micro_batch_processing():
    # Process data in small batches every 5 minutes
    df = extract_recent_data(minutes=5)
    
    # Quick transformations
    df_processed = (
        df
        .filter(col("status") == "completed")
        .withColumn("batch_id", current_timestamp())
    )
    
    # Load to staging
    df_processed.write.mode("append").saveAsTable("staging.recent_transactions")
    
    # Trigger downstream processing
    trigger_analytics_pipeline()
```

## Data Governance

### 1. Access Control
**Tejuu's Security Patterns:**

```sql
-- Row-level security for sensitive data
CREATE FUNCTION dbo.fn_customer_access(@customer_id VARCHAR(50))
RETURNS TABLE
WITH SCHEMABINDING
AS
RETURN SELECT 1 AS fn_customer_access
WHERE @customer_id IN (
    SELECT customer_id 
    FROM user_customer_access 
    WHERE user_name = USER_NAME()
);

-- Apply security policy
CREATE SECURITY POLICY customer_security_policy
ADD FILTER PREDICATE dbo.fn_customer_access(customer_id)
ON fct_transactions
WITH (STATE = ON);
```

### 2. Data Classification
**Tejuu's Classification Framework:**

```python
# Automated data classification
class DataClassifier:
    def __init__(self):
        self.classification_rules = {
            'PII': ['customer_id', 'ssn', 'email', 'phone'],
            'Financial': ['amount', 'balance', 'credit_score'],
            'Public': ['product_name', 'category', 'region']
        }
    
    def classify_column(self, column_name):
        for classification, patterns in self.classification_rules.items():
            if any(pattern in column_name.lower() for pattern in patterns):
                return classification
        return 'Internal'
```

## Cost Optimization

### 1. Resource Right-Sizing
**Tejuu's Cost Strategies:**

```python
# Dynamic resource allocation based on data volume
def calculate_required_resources(data_size_gb):
    if data_size_gb < 10:
        return {'nodes': 2, 'cores': 4, 'memory': '8GB'}
    elif data_size_gb < 100:
        return {'nodes': 4, 'cores': 8, 'memory': '16GB'}
    else:
        return {'nodes': 8, 'cores': 16, 'memory': '32GB'}
```

### 2. Data Lifecycle Management
**Tejuu's Lifecycle Patterns:**

```python
# Automated data archiving
def archive_old_data():
    # Archive data older than 2 years
    cutoff_date = datetime.now() - timedelta(days=730)
    
    # Move to archive storage
    df_old = spark.sql(f"""
        SELECT * FROM fct_transactions 
        WHERE transaction_date < '{cutoff_date.strftime('%Y-%m-%d')}'
    """)
    
    df_old.write.mode("overwrite").parquet("s3://archive/transactions/")
    
    # Delete from main table
    spark.sql(f"""
        DELETE FROM fct_transactions 
        WHERE transaction_date < '{cutoff_date.strftime('%Y-%m-%d')}'
    """)
```

My data pipeline architecture experience helps build robust, scalable, and cost-effective data platforms that deliver real business value!
