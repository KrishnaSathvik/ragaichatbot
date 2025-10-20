---
tags: [data-engineer, pyspark, databricks, spark, big-data, tejuu]
persona: analytics
---

# PySpark & Databricks - Tejuu's Experience

## Introduction
**Tejuu's PySpark Journey:**
While my primary focus is on Azure Synapse and Power BI, I've worked extensively with PySpark and Databricks during my time at Stryker and CVS Health. I've built data processing pipelines that handle millions of records and integrated PySpark with Azure services. Let me share the patterns and best practices I've learned working with big data processing.

## PySpark Fundamentals

### 1. DataFrame Operations
**Tejuu's DataFrame Patterns:**

```python
# Basic DataFrame operations
from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *

# Initialize Spark session
spark = SparkSession.builder \
    .appName("BankingDataProcessing") \
    .config("spark.sql.adaptive.enabled", "true") \
    .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
    .getOrCreate()

# Read data from multiple sources
def read_banking_data():
    # Read from Azure Data Lake
    df_transactions = spark.read.format("parquet") \
        .load("abfss://bronze@storageaccount.dfs.core.windows.net/transactions/")
    
    # Read from SQL Server
    df_customers = spark.read.format("jdbc") \
        .option("url", "jdbc:sqlserver://server.database.windows.net:1433;database=BankDB") \
        .option("dbtable", "customers") \
        .option("user", "username") \
        .option("password", "password") \
        .load()
    
    return df_transactions, df_customers

# Data transformation pipeline
def transform_banking_data(df_transactions, df_customers):
    # Join transactions with customer data
    df_joined = df_transactions.join(
        df_customers, 
        df_transactions.customer_id == df_customers.customer_id, 
        "inner"
    )
    
    # Apply business transformations
    df_transformed = (
        df_joined
        .filter(col("transaction_status") == "completed")
        .withColumn("transaction_amount", col("transaction_amount").cast("decimal(18,2)"))
        .withColumn("transaction_date", to_date(col("transaction_date"), "yyyy-MM-dd"))
        .withColumn("customer_segment", 
                   when(col("total_balance") >= 100000, "Premium")
                   .when(col("total_balance") >= 50000, "Gold")
                   .when(col("total_balance") >= 10000, "Silver")
                   .otherwise("Bronze"))
        .withColumn("processing_timestamp", current_timestamp())
        .dropDuplicates(["transaction_id"])
    )
    
    return df_transformed
```

### 2. Data Quality Validation
**Tejuu's Data Quality Patterns:**

```python
# Comprehensive data quality validation
class BankingDataQualityValidator:
    def __init__(self):
        self.quality_rules = {
            'completeness': self.check_completeness,
            'accuracy': self.check_accuracy,
            'consistency': self.check_consistency,
            'validity': self.check_validity
        }
    
    def validate_dataframe(self, df, table_name):
        validation_results = {
            'table_name': table_name,
            'total_records': df.count(),
            'quality_score': 0.0,
            'validation_errors': []
        }
        
        for rule_name, rule_function in self.quality_rules.items():
            rule_results = rule_function(df)
            validation_results['validation_errors'].extend(rule_results['errors'])
        
        # Calculate overall quality score
        total_checks = len(validation_results['validation_errors'])
        passed_checks = validation_results['total_records'] - total_checks
        validation_results['quality_score'] = (passed_checks / validation_results['total_records']) * 100
        
        return validation_results
    
    def check_completeness(self, df):
        errors = []
        required_columns = ['transaction_id', 'customer_id', 'amount', 'transaction_date']
        
        for column in required_columns:
            if column in df.columns:
                null_count = df.filter(col(column).isNull()).count()
                if null_count > 0:
                    errors.append({
                        'column': column,
                        'error_type': 'completeness',
                        'error_count': null_count,
                        'message': f'Found {null_count} null values in {column}'
                    })
        
        return {'errors': errors}
    
    def check_accuracy(self, df):
        errors = []
        
        # Check for negative amounts
        if 'amount' in df.columns:
            negative_amounts = df.filter(col("amount") < 0).count()
            if negative_amounts > 0:
                errors.append({
                    'column': 'amount',
                    'error_type': 'accuracy',
                    'error_count': negative_amounts,
                    'message': f'Found {negative_amounts} negative amounts'
                })
        
        # Check for future dates
        if 'transaction_date' in df.columns:
            future_dates = df.filter(col("transaction_date") > current_date()).count()
            if future_dates > 0:
                errors.append({
                    'column': 'transaction_date',
                    'error_type': 'accuracy',
                    'error_count': future_dates,
                    'message': f'Found {future_dates} future dates'
                })
        
        return {'errors': errors}
    
    def check_consistency(self, df):
        errors = []
        
        # Check for duplicate transaction IDs
        if 'transaction_id' in df.columns:
            duplicate_count = df.count() - df.select("transaction_id").distinct().count()
            if duplicate_count > 0:
                errors.append({
                    'column': 'transaction_id',
                    'error_type': 'consistency',
                    'error_count': duplicate_count,
                    'message': f'Found {duplicate_count} duplicate transaction IDs'
                })
        
        return {'errors': errors}
    
    def check_validity(self, df):
        errors = []
        
        # Check transaction amount range
        if 'amount' in df.columns:
            invalid_amounts = df.filter(
                (col("amount") < 0.01) | (col("amount") > 1000000)
            ).count()
            if invalid_amounts > 0:
                errors.append({
                    'column': 'amount',
                    'error_type': 'validity',
                    'error_count': invalid_amounts,
                    'message': f'Found {invalid_amounts} amounts outside valid range'
                })
        
        return {'errors': errors}
```

### 3. Performance Optimization
**Tejuu's Performance Patterns:**

```python
# PySpark performance optimization
class PySparkOptimizer:
    def __init__(self):
        self.optimization_configs = {
            'adaptive_query_execution': True,
            'coalesce_partitions': True,
            'broadcast_join_threshold': '10MB',
            'auto_broadcast_join_threshold': '10MB'
        }
    
    def optimize_dataframe(self, df):
        # Apply optimizations
        df_optimized = df
        
        # Cache frequently used DataFrames
        df_optimized = df_optimized.cache()
        
        # Repartition for better parallelism
        df_optimized = df_optimized.repartition(200)
        
        return df_optimized
    
    def optimize_joins(self, df1, df2, join_key):
        # Broadcast smaller DataFrame
        if df2.count() < 1000000:  # 1M records threshold
            df2_broadcast = broadcast(df2)
            return df1.join(df2_broadcast, join_key, "inner")
        else:
            return df1.join(df2, join_key, "inner")
    
    def optimize_aggregations(self, df, group_columns, agg_columns):
        # Use approximate functions for large datasets
        if df.count() > 10000000:  # 10M records threshold
            return df.groupBy(group_columns).agg(
                approx_count_distinct("customer_id").alias("unique_customers"),
                sum("amount").alias("total_amount"),
                avg("amount").alias("avg_amount")
            )
        else:
            return df.groupBy(group_columns).agg(
                countDistinct("customer_id").alias("unique_customers"),
                sum("amount").alias("total_amount"),
                avg("amount").alias("avg_amount")
            )
```

## Databricks Integration

### 1. Databricks Workspace Setup
**Tejuu's Databricks Patterns:**

```python
# Databricks workspace configuration
class DatabricksWorkspace:
    def __init__(self):
        self.workspace_config = {
            'workspace_url': 'https://adb-1234567890123456.7.azuredatabricks.net',
            'access_token': dbutils.secrets.get("keyvault", "databricks-token"),
            'cluster_id': '1234-567890-abcdef'
        }
    
    def setup_workspace(self):
        # Mount Azure Data Lake Storage
        self.mount_adls()
        
        # Set up libraries
        self.install_libraries()
        
        # Configure Spark settings
        self.configure_spark_settings()
    
    def mount_adls(self):
        # Mount Bronze layer
        dbutils.fs.mount(
            source="abfss://bronze@storageaccount.dfs.core.windows.net/",
            mount_point="/mnt/bronze",
            extra_configs={
                "fs.azure.account.auth.type": "OAuth",
                "fs.azure.account.oauth.provider.type": "org.apache.hadoop.fs.azurebfs.oauth2.ClientCredsTokenProvider",
                "fs.azure.account.oauth2.client.id": dbutils.secrets.get("keyvault", "sp-client-id"),
                "fs.azure.account.oauth2.client.secret": dbutils.secrets.get("keyvault", "sp-client-secret"),
                "fs.azure.account.oauth2.client.endpoint": "https://login.microsoftonline.com/tenant-id/oauth2/token"
            }
        )
        
        # Mount Silver layer
        dbutils.fs.mount(
            source="abfss://silver@storageaccount.dfs.core.windows.net/",
            mount_point="/mnt/silver",
            extra_configs={
                "fs.azure.account.auth.type": "OAuth",
                "fs.azure.account.oauth.provider.type": "org.apache.hadoop.fs.azurebfs.oauth2.ClientCredsTokenProvider",
                "fs.azure.account.oauth2.client.id": dbutils.secrets.get("keyvault", "sp-client-id"),
                "fs.azure.account.oauth2.client.secret": dbutils.secrets.get("keyvault", "sp-client-secret"),
                "fs.azure.account.oauth2.client.endpoint": "https://login.microsoftonline.com/tenant-id/oauth2/token"
            }
        )
    
    def install_libraries(self):
        # Install required Python libraries
        dbutils.library.installPyPI("pandas", "1.5.3")
        dbutils.library.installPyPI("numpy", "1.24.3")
        dbutils.library.installPyPI("pyodbc", "4.0.39")
        
        # Restart Python to load libraries
        dbutils.library.restartPython()
    
    def configure_spark_settings(self):
        # Configure Spark for optimal performance
        spark.conf.set("spark.sql.adaptive.enabled", "true")
        spark.conf.set("spark.sql.adaptive.coalescePartitions.enabled", "true")
        spark.conf.set("spark.sql.adaptive.skewJoin.enabled", "true")
        spark.conf.set("spark.serializer", "org.apache.spark.serializer.KryoSerializer")
```

### 2. Databricks Notebooks
**Tejuu's Notebook Patterns:**

```python
# Databricks notebook for data processing
# This notebook processes banking transactions

# Get parameters from widgets
dbutils.widgets.text("execution_date", "")
dbutils.widgets.text("environment", "prod")

execution_date = dbutils.widgets.get("execution_date")
environment = dbutils.widgets.get("environment")

print(f"Processing banking data for {execution_date} in {environment}")

# Read data from mounted storage
df_transactions = spark.read.format("delta") \
    .load(f"/mnt/bronze/transactions/date={execution_date}")

df_customers = spark.read.format("delta") \
    .load("/mnt/silver/customers")

# Data quality validation
validator = BankingDataQualityValidator()
quality_results = validator.validate_dataframe(df_transactions, "transactions")

if quality_results['quality_score'] < 95:
    print(f"⚠️ Data quality below threshold: {quality_results['quality_score']}%")
    for error in quality_results['validation_errors']:
        print(f"  - {error['message']}")
else:
    print(f"✅ Data quality acceptable: {quality_results['quality_score']}%")

# Transform data
df_processed = transform_banking_data(df_transactions, df_customers)

# Write to Silver layer
df_processed.write \
    .format("delta") \
    .mode("overwrite") \
    .partitionBy("transaction_date") \
    .save(f"/mnt/silver/processed_transactions")

# Create summary statistics
summary_stats = df_processed.groupBy("customer_segment").agg(
    count("*").alias("transaction_count"),
    sum("transaction_amount").alias("total_amount"),
    avg("transaction_amount").alias("avg_amount")
).collect()

print("📊 Transaction Summary by Customer Segment:")
for row in summary_stats:
    print(f"  {row['customer_segment']}: {row['transaction_count']:,} transactions, ${row['total_amount']:,.2f} total")

# Log completion
dbutils.notebook.exit(f"SUCCESS: Processed {df_processed.count():,} transactions")
```

### 3. Databricks Jobs
**Tejuu's Job Patterns:**

```python
# Databricks job configuration
job_config = {
    "name": "banking-data-processing",
    "new_cluster": {
        "spark_version": "13.3.x-scala2.12",
        "node_type_id": "Standard_DS3_v2",
        "num_workers": 2,
        "autoscale": {
            "min_workers": 1,
            "max_workers": 4
        },
        "spark_conf": {
            "spark.databricks.delta.preview.enabled": "true",
            "spark.sql.adaptive.enabled": "true"
        }
    },
    "notebook_task": {
        "notebook_path": "/Shared/banking-data-processing",
        "base_parameters": {
            "execution_date": "{{ds}}",
            "environment": "prod"
        }
    },
    "timeout_seconds": 3600,
    "max_retries": 2,
    "retry_on_timeout": True
}

# Create job
def create_databricks_job(job_config):
    import requests
    
    headers = {
        'Authorization': f'Bearer {dbutils.secrets.get("keyvault", "databricks-token")}',
        'Content-Type': 'application/json'
    }
    
    response = requests.post(
        f"{workspace_config['workspace_url']}/api/2.0/jobs/create",
        headers=headers,
        json=job_config
    )
    
    if response.status_code == 200:
        job_id = response.json()['job_id']
        print(f"✅ Job created successfully with ID: {job_id}")
        return job_id
    else:
        print(f"❌ Failed to create job: {response.text}")
        return None
```

## Advanced PySpark Patterns

### 1. Window Functions
**Tejuu's Window Function Patterns:**

```python
# Advanced window functions for banking analytics
from pyspark.sql.window import Window

def calculate_customer_metrics(df):
    # Define window specifications
    customer_window = Window.partitionBy("customer_id").orderBy("transaction_date")
    customer_window_unbounded = Window.partitionBy("customer_id")
    
    # Calculate customer metrics
    df_with_metrics = (
        df
        .withColumn("transaction_rank", rank().over(customer_window))
        .withColumn("transaction_count", count("*").over(customer_window_unbounded))
        .withColumn("total_amount", sum("transaction_amount").over(customer_window_unbounded))
        .withColumn("avg_amount", avg("transaction_amount").over(customer_window_unbounded))
        .withColumn("max_amount", max("transaction_amount").over(customer_window_unbounded))
        .withColumn("min_amount", min("transaction_amount").over(customer_window_unbounded))
        .withColumn("first_transaction_date", min("transaction_date").over(customer_window_unbounded))
        .withColumn("last_transaction_date", max("transaction_date").over(customer_window_unbounded))
        .withColumn("days_since_last_transaction", 
                   datediff(current_date(), max("transaction_date").over(customer_window_unbounded)))
    )
    
    return df_with_metrics

# Rolling window calculations
def calculate_rolling_metrics(df, window_days=30):
    rolling_window = Window.partitionBy("customer_id") \
                          .orderBy("transaction_date") \
                          .rangeBetween(-window_days, 0)
    
    df_rolling = (
        df
        .withColumn("rolling_30d_count", count("*").over(rolling_window))
        .withColumn("rolling_30d_amount", sum("transaction_amount").over(rolling_window))
        .withColumn("rolling_30d_avg", avg("transaction_amount").over(rolling_window))
    )
    
    return df_rolling
```

### 2. UDFs and Custom Functions
**Tejuu's UDF Patterns:**

```python
# User-defined functions for banking calculations
from pyspark.sql.types import StringType, DecimalType
from pyspark.sql.functions import udf

# Calculate risk score
def calculate_risk_score(amount, frequency, balance):
    if amount > 50000 or frequency > 100 or balance < 1000:
        return "High"
    elif amount > 10000 or frequency > 50 or balance < 5000:
        return "Medium"
    else:
        return "Low"

risk_score_udf = udf(calculate_risk_score, StringType())

# Calculate customer lifetime value
def calculate_clv(avg_amount, frequency, months_active):
    return avg_amount * frequency * months_active

clv_udf = udf(calculate_clv, DecimalType(18, 2))

# Apply UDFs to DataFrame
def apply_banking_udfs(df):
    df_with_udfs = (
        df
        .withColumn("risk_score", risk_score_udf(col("transaction_amount"), col("frequency"), col("balance")))
        .withColumn("customer_lifetime_value", clv_udf(col("avg_amount"), col("frequency"), col("months_active")))
    )
    
    return df_with_udfs
```

### 3. Streaming Data Processing
**Tejuu's Streaming Patterns:**

```python
# Real-time transaction processing
def setup_streaming_pipeline():
    # Read streaming data from Kafka
    df_stream = spark \
        .readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", "localhost:9092") \
        .option("subscribe", "banking-transactions") \
        .option("startingOffsets", "latest") \
        .load()
    
    # Parse JSON data
    from pyspark.sql.types import StructType, StructField, StringType, DecimalType, TimestampType
    
    transaction_schema = StructType([
        StructField("transaction_id", StringType(), True),
        StructField("customer_id", StringType(), True),
        StructField("amount", DecimalType(18, 2), True),
        StructField("transaction_date", TimestampType(), True),
        StructField("transaction_type", StringType(), True)
    ])
    
    df_parsed = df_stream \
        .select(from_json(col("value").cast("string"), transaction_schema).alias("data")) \
        .select("data.*")
    
    # Process streaming data
    df_processed = (
        df_parsed
        .filter(col("amount") > 0)
        .withColumn("processed_at", current_timestamp())
        .withColumn("risk_score", risk_score_udf(col("amount"), lit(1), lit(10000)))
    )
    
    # Write to Delta table
    query = df_processed \
        .writeStream \
        .format("delta") \
        .option("checkpointLocation", "/checkpoint/transactions") \
        .outputMode("append") \
        .trigger(processingTime='10 seconds') \
        .start()
    
    return query
```

## Integration with Azure Services

### 1. Azure Data Factory Integration
**Tejuu's ADF Integration:**

```python
# Databricks notebook for ADF integration
# This notebook is called from Azure Data Factory

# Get parameters from ADF
execution_date = dbutils.widgets.get("execution_date")
source_system = dbutils.widgets.get("source_system")

print(f"Processing data from {source_system} for {execution_date}")

# Read data based on source system
if source_system == "sql_server":
    df = read_from_sql_server(execution_date)
elif source_system == "api":
    df = read_from_api(execution_date)
elif source_system == "file":
    df = read_from_file(execution_date)

# Process data
df_processed = process_banking_data(df)

# Write to target
write_to_target(df_processed, execution_date)

# Return status to ADF
dbutils.notebook.exit("SUCCESS")
```

### 2. Power BI Integration
**Tejuu's Power BI Patterns:**

```python
# Create Power BI optimized views
def create_power_bi_views(df):
    # Create customer summary view
    customer_summary = df.groupBy("customer_id", "customer_segment") \
        .agg(
            count("*").alias("transaction_count"),
            sum("transaction_amount").alias("total_amount"),
            avg("transaction_amount").alias("avg_amount"),
            max("transaction_date").alias("last_transaction_date")
        )
    
    # Create daily summary view
    daily_summary = df.groupBy("transaction_date", "customer_segment") \
        .agg(
            count("*").alias("transaction_count"),
            sum("transaction_amount").alias("total_amount"),
            countDistinct("customer_id").alias("unique_customers")
        )
    
    return customer_summary, daily_summary

# Write to Power BI accessible location
def write_for_power_bi(df, view_name):
    df.write \
        .format("delta") \
        .mode("overwrite") \
        .option("path", f"/mnt/silver/powerbi/{view_name}") \
        .saveAsTable(f"powerbi.{view_name}")
```

My PySpark and Databricks experience helps build scalable, high-performance data processing pipelines that integrate seamlessly with Azure services!
