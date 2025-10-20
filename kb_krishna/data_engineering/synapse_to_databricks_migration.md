---
tags: [krishna, data-engineering, migration, synapse, databricks, pyspark, t-sql]
persona: de
---

# Synapse to Databricks Migration - Krishna's Implementation

## Migration Strategy

### Port T-SQL/Scala to PySpark DataFrames
```python
# Original T-SQL in Synapse
# SELECT customer_id, COUNT(*) as order_count, SUM(amount) as total_amount
# FROM orders 
# WHERE order_date >= '2023-01-01'
# GROUP BY customer_id

# Converted to PySpark
from pyspark.sql.functions import col, count, sum as spark_sum, when

df_orders = spark.table("orders")

# PySpark equivalent
result = df_orders \
    .filter(col("order_date") >= "2023-01-01") \
    .groupBy("customer_id") \
    .agg(
        count("*").alias("order_count"),
        spark_sum("amount").alias("total_amount")
    )
```

### Replace Temp Tables with Delta Temp Tables
```python
# Original Synapse temp table
# CREATE TABLE #temp_customers AS
# SELECT customer_id, customer_name, region
# FROM customers WHERE status = 'ACTIVE'

# Converted to Delta temp table
temp_customers = spark.table("customers") \
    .filter(col("status") == "ACTIVE") \
    .select("customer_id", "customer_name", "region")

# Write to Delta temp location
temp_customers.write \
    .format("delta") \
    .mode("overwrite") \
    .option("path", "/tmp/temp_customers") \
    .saveAsTable("temp_customers")

# Use in subsequent operations
result = spark.table("temp_customers") \
    .join(spark.table("orders"), "customer_id")
```

### Validate Parity
```python
# Row count validation
def validate_row_counts():
    synapse_count = spark.sql("SELECT COUNT(*) FROM synapse_orders").collect()[0][0]
    databricks_count = spark.sql("SELECT COUNT(*) FROM databricks_orders").collect()[0][0]
    
    assert synapse_count == databricks_count, f"Row count mismatch: {synapse_count} vs {databricks_count}"
    print("✅ Row counts match")

# Hash validation for data integrity
def validate_data_hashes():
    synapse_hash = spark.sql("""
        SELECT CHECKSUM_AGG(CAST(ORDER_ID AS BIGINT)) as hash_sum
        FROM synapse_orders
    """).collect()[0][0]
    
    databricks_hash = spark.sql("""
        SELECT CHECKSUM_AGG(CAST(ORDER_ID AS BIGINT)) as hash_sum
        FROM databricks_orders
    """).collect()[0][0]
    
    assert synapse_hash == databricks_hash, f"Data hash mismatch: {synapse_hash} vs {databricks_hash}"
    print("✅ Data hashes match")

# KPI validation
def validate_kpis():
    synapse_kpi = spark.sql("""
        SELECT SUM(amount) as total_revenue, COUNT(DISTINCT customer_id) as unique_customers
        FROM synapse_orders
    """).collect()[0]
    
    databricks_kpi = spark.sql("""
        SELECT SUM(amount) as total_revenue, COUNT(DISTINCT customer_id) as unique_customers
        FROM databricks_orders
    """).collect()[0]
    
    revenue_diff = abs(synapse_kpi[0] - databricks_kpi[0])
    customer_diff = abs(synapse_kpi[1] - databricks_kpi[1])
    
    assert revenue_diff < 0.01, f"Revenue KPI mismatch: {revenue_diff}"
    assert customer_diff == 0, f"Customer count mismatch: {customer_diff}"
    print("✅ KPIs match")
```

### Run Both Systems in Parallel
```python
# Parallel validation for one week
def parallel_validation():
    start_date = "2023-01-01"
    end_date = "2023-01-07"
    
    # Run both systems
    synapse_results = run_synapse_pipeline(start_date, end_date)
    databricks_results = run_databricks_pipeline(start_date, end_date)
    
    # Compare results daily
    for date in pd.date_range(start_date, end_date):
        synapse_daily = synapse_results.filter(col("date") == date)
        databricks_daily = databricks_results.filter(col("date") == date)
        
        validate_daily_results(synapse_daily, databricks_daily)
        print(f"✅ {date} validation passed")
```

### Replace Stored Procs with Parameterized Notebooks
```python
# Original stored procedure
# CREATE PROCEDURE sp_ProcessOrders(@start_date DATE, @end_date DATE)
# AS
# BEGIN
#     SELECT * FROM orders WHERE order_date BETWEEN @start_date AND @end_date
# END

# Converted to parameterized notebook
def process_orders_notebook(start_date, end_date):
    # Get parameters from widgets
    start_date = spark.conf.get("start_date", start_date)
    end_date = spark.conf.get("end_date", end_date)
    
    # Process data
    df_orders = spark.table("orders") \
        .filter(col("order_date").between(start_date, end_date))
    
    # Apply business logic
    df_processed = df_orders \
        .withColumn("processed_at", current_timestamp()) \
        .withColumn("status", 
            when(col("amount") > 1000, "HIGH_VALUE")
            .otherwise("STANDARD"))
    
    return df_processed

# Promote via DevOps
def deploy_notebook():
    # Notebook promotion pipeline
    # 1. Validate notebook syntax
    # 2. Run unit tests
    # 3. Deploy to staging
    # 4. Run integration tests
    # 5. Deploy to production
    pass
```

## Krishna's Experience

At Walgreens, I led the migration of 200+ Synapse notebooks to Databricks. The key was systematic conversion of T-SQL to PySpark DataFrames, replacing temp tables with Delta temp tables, and running both systems in parallel for validation.

We validated parity by comparing row counts, data hashes, and KPIs daily for a week. The parameterized notebook approach replaced stored procedures and enabled better version control through DevOps pipelines.

This migration reduced processing time by 35% and enabled better scalability for our 10TB+ monthly data processing at Walgreens. The Delta Lake format also provided better ACID guarantees and time travel capabilities compared to Synapse.
