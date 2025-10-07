---
tags: [interview, preparation, comprehensive, databricks, sql, spark, python]
persona: de
file_name: interview_prep_comprehensive
---

# Comprehensive Data Engineering Interview Preparation

## Latest Interview Questions & Topics

Over the past few months, I've been actively preparing for Data Engineering interviews, and I thought of sharing some of the latest questions I came across. These focus on Spark, SQL, Python, and Databricks, the core skills for most modern data engineering roles.

### 🔹 Spark Questions

**Explain Spark architecture – how do driver, executors, and cluster manager interact?**
- Driver program coordinates the job execution and communicates with cluster manager
- Cluster manager (YARN, Mesos, or standalone) allocates resources across the cluster
- Executors run tasks and store data in memory/disk, report back to driver
- Driver sends tasks to executors, collects results, and manages the overall job

**Difference between narrow vs. wide transformations with examples.**
- Narrow transformations: map(), filter(), union() - no data movement between partitions
- Wide transformations: groupBy(), join(), distinct() - requires shuffling data across partitions
- Wide transformations are expensive and should be minimized for performance

**How do you optimize Spark jobs (partitioning, caching, broadcast joins)?**
- Partition data appropriately based on query patterns (usually date-based)
- Cache frequently accessed DataFrames in memory
- Use broadcast joins for small lookup tables
- Tune spark.sql.shuffle.partitions based on cluster size
- Use coalesce() instead of repartition() when reducing partitions

**What happens when you run df.explain() in Spark?**
- Shows the logical and physical execution plans
- Displays optimization decisions made by Catalyst optimizer
- Helps identify bottlenecks, unnecessary shuffles, or missing optimizations
- Can use df.explain(true) for extended physical plan details

### 🔹 SQL Questions

**Write a query to get the second highest salary without using TOP or LIMIT.**
```sql
-- Using window function
SELECT salary 
FROM (
    SELECT salary, ROW_NUMBER() OVER (ORDER BY salary DESC) as rn
    FROM employees
) ranked
WHERE rn = 2;

-- Using subquery
SELECT MAX(salary) 
FROM employees 
WHERE salary < (SELECT MAX(salary) FROM employees);

-- Using self-join
SELECT DISTINCT e1.salary
FROM employees e1, employees e2
WHERE e1.salary < e2.salary
GROUP BY e1.salary
HAVING COUNT(*) = 1;
```

**Explain QUALIFY with an example.**
```sql
-- QUALIFY filters results of window functions without subquery
SELECT name, salary, department,
       ROW_NUMBER() OVER (PARTITION BY department ORDER BY salary DESC) as rn
FROM employees
QUALIFY rn <= 3;  -- Top 3 earners per department
```

**Difference between INNER JOIN, LEFT JOIN, FULL JOIN, and CROSS JOIN.**
- INNER JOIN: Only matching rows from both tables
- LEFT JOIN: All rows from left table + matching rows from right table
- FULL JOIN: All rows from both tables (union of LEFT and RIGHT)
- CROSS JOIN: Cartesian product of all rows from both tables

**How do you handle incremental loads in SQL?**
- Use watermark columns (modified_date, created_date)
- Implement CDC (Change Data Capture) patterns
- Use MERGE statements for upsert operations
- Track last processed timestamp in control tables

### 🔹 Python Questions

**How would you reverse a string without using built-in functions?**
```python
def reverse_string(s):
    result = ""
    for i in range(len(s) - 1, -1, -1):
        result += s[i]
    return result

# Alternative approach
def reverse_string_slicing(s):
    return s[::-1]
```

**Write code to find duplicates in a list.**
```python
def find_duplicates(lst):
    seen = set()
    duplicates = set()
    for item in lst:
        if item in seen:
            duplicates.add(item)
        else:
            seen.add(item)
    return list(duplicates)

# Using collections.Counter
from collections import Counter
def find_duplicates_counter(lst):
    counts = Counter(lst)
    return [item for item, count in counts.items() if count > 1]
```

**Difference between @staticmethod, @classmethod, and instance methods.**
- Instance methods: Take self, access instance attributes
- Class methods: Take cls, access class attributes, can create new instances
- Static methods: Don't take self or cls, utility functions that don't need class/instance data

**Explain Python's GIL (Global Interpreter Lock).**
- GIL prevents multiple threads from executing Python bytecode simultaneously
- Only one thread can execute Python code at a time
- Affects CPU-bound tasks but not I/O-bound tasks
- Can be bypassed using multiprocessing or C extensions

### 🔹 Databricks Questions

**How do you implement Bronze-Silver-Gold architecture in Databricks?**
- Bronze: Raw ingested data with schema flexibility
- Silver: Cleaned, validated, deduplicated data with enforced schemas
- Gold: Business-ready aggregated and modeled data for analytics
- Use Delta Lake for ACID transactions and schema evolution

**Difference between Delta Lake and traditional parquet tables.**
- Delta Lake: ACID transactions, schema enforcement, time travel, upserts
- Parquet: Immutable, append-only, no built-in transaction support
- Delta Lake provides better reliability and governance capabilities

**How do you manage incremental data load using Delta Lake?**
```python
# Using MERGE for upserts
df.write.format("delta").mode("append").option("mergeSchema", "true").save("/path/to/table")

# Or using merge operation
from delta.tables import DeltaTable
deltaTable = DeltaTable.forPath(spark, "/path/to/table")
deltaTable.alias("target").merge(
    source_df.alias("source"),
    "target.id = source.id"
).whenMatchedUpdateAll().whenNotMatchedInsertAll().execute()
```

**Explain Unity Catalog and its role in governance.**
- Centralized metadata store for data governance
- Provides fine-grained access control at table/column level
- Enables data lineage tracking and discovery
- Supports PII masking and row-level security
- Integrates with external identity providers

## 🔍 Why Most People Struggle in Data Engineering Interviews

I've seen this pattern again and again — candidates know the tools, but the moment the interviewer shifts from "what is Spark?" to "design a pipeline for streaming data," things start to fall apart.

**The truth?** Data Engineering interviews test how you think, not just what you know.

### Mental Framework for Interviews:

1️⃣ **SQL is your foundation** → If you can't join, aggregate, and optimize queries, nothing else will stand.

2️⃣ **Model the data** → Understand when to use star schema vs. snowflake, OLTP vs. OLAP, and how to handle Slowly Changing Dimensions.

3️⃣ **Think scale** → Spark, partitioning, shuffles, streaming late-arrival data — these aren't buzzwords, they're the backbone of real-world DE systems.

4️⃣ **Design pipelines, not scripts** → Batch vs. streaming, orchestration with Airflow, partitioning strategies — show that you can think like an architect.

5️⃣ **Zoom out** → Cloud (S3, Redshift, BigQuery, Synapse), data lake vs. warehouse vs. lakehouse — interviews often end with "how would you design this end-to-end?"

## Databricks-Specific Interview Preparation

Databricks is the home of Apache Spark and the Lakehouse Platform. Engineers here focus on real-time data, ML pipelines, and large-scale analytics.

### 10 Key Databricks Questions:

1️⃣ **Explain how Delta Lake improves reliability over a traditional data lake.**
- ACID transactions ensure data consistency
- Schema enforcement prevents data corruption
- Time travel enables data recovery and auditing
- Upsert capabilities support CDC patterns

2️⃣ **How would you design a streaming pipeline with Structured Streaming in Spark?**
```python
from pyspark.sql import SparkSession
from pyspark.sql.functions import *

spark = SparkSession.builder.appName("StreamingPipeline").getOrCreate()

# Read from Kafka
streaming_df = spark.readStream.format("kafka") \
    .option("kafka.bootstrap.servers", "localhost:9092") \
    .option("subscribe", "events") \
    .load()

# Process and write to Delta Lake
processed_df = streaming_df.select(
    from_json(col("value").cast("string"), schema).alias("data")
).select("data.*")

query = processed_df.writeStream \
    .format("delta") \
    .option("checkpointLocation", "/checkpoint/path") \
    .outputMode("append") \
    .start("/delta/events")
```

3️⃣ **Walk me through optimizing a Spark job handling terabytes of data.**
- Profile with Spark UI to identify bottlenecks
- Optimize partitioning strategy (usually date-based)
- Use broadcast joins for small lookup tables
- Implement salting for skewed joins
- Enable Adaptive Query Execution (AQE)
- Cache frequently accessed DataFrames
- Use columnar formats like Parquet/Delta

4️⃣ **How would you enable ACID transactions in a big data pipeline?**
- Use Delta Lake for ACID compliance
- Implement proper partitioning strategies
- Use MERGE operations for upserts
- Configure appropriate isolation levels
- Handle concurrent writes with optimistic concurrency control

5️⃣ **Explain how you'd manage schema evolution with Delta Lake.**
```python
# Enable schema evolution
df.write.format("delta") \
    .mode("append") \
    .option("mergeSchema", "true") \
    .save("/delta/table")

# Or manually evolve schema
spark.sql("ALTER TABLE delta_table ADD COLUMN new_column STRING")
```

6️⃣ **What's your strategy for scaling ML model training pipelines in Databricks?**
- Use MLflow for experiment tracking and model versioning
- Implement distributed training with Spark MLlib
- Use GPU clusters for deep learning workloads
- Cache feature engineering results
- Implement model serving with MLflow Model Registry

7️⃣ **How would you integrate Databricks with external BI tools like Tableau or Power BI?**
- Create SQL endpoints for direct query access
- Use JDBC/ODBC connectors for BI tools
- Implement data marts with optimized schemas
- Use Delta Lake for consistent data access
- Configure appropriate access controls

8️⃣ **Describe how you'd secure a data lakehouse in a multi-tenant environment.**
- Implement Unity Catalog for centralized governance
- Use workspace-level isolation
- Configure fine-grained access controls
- Implement PII masking and encryption
- Use Azure Active Directory integration

9️⃣ **How do you debug performance bottlenecks in Spark?**
- Use Spark UI to analyze DAG and stage execution
- Check for data skew in shuffle operations
- Monitor memory usage and garbage collection
- Profile with Spark History Server
- Use query plans to identify optimization opportunities

🔟 **Tell me about a time you balanced speed vs. cost in large-scale data jobs.**
- Implemented incremental processing instead of full loads
- Used spot instances for non-critical workloads
- Optimized partitioning to reduce shuffle overhead
- Implemented auto-scaling based on workload patterns
- Used columnar storage formats for better compression

## Advanced Data Engineering Interview Questions

### 20 Comprehensive Questions:

1️⃣ **Write an SQL query to find the second highest salary from an employee table.**
```sql
SELECT MAX(salary) as second_highest_salary
FROM employees 
WHERE salary < (SELECT MAX(salary) FROM employees);
```

2️⃣ **How do you handle NULL values in SQL joins while ensuring data integrity?**
- Use COALESCE() or ISNULL() to provide default values
- Implement proper NULL handling in business logic
- Use INNER JOIN to exclude NULL matches if appropriate
- Consider LEFT JOIN with NULL checks for data validation

3️⃣ **Write an SQL query to calculate customer churn rate over the last 6 months.**
```sql
WITH customer_activity AS (
    SELECT customer_id,
           MAX(order_date) as last_order_date,
           CASE WHEN MAX(order_date) < DATE_SUB(CURRENT_DATE, INTERVAL 6 MONTH) 
                THEN 1 ELSE 0 END as is_churned
    FROM orders
    GROUP BY customer_id
)
SELECT 
    COUNT(*) as total_customers,
    SUM(is_churned) as churned_customers,
    ROUND(SUM(is_churned) * 100.0 / COUNT(*), 2) as churn_rate_percentage
FROM customer_activity;
```

4️⃣ **Design a fact table for an e-commerce platform – what dimensions and measures would you include?**
- **Dimensions**: Date, Customer, Product, Store, Payment Method
- **Measures**: Sales Amount, Quantity, Discount, Tax, Shipping Cost
- **Grain**: One row per transaction line item
- **Design**: Star schema with fact table in center

5️⃣ **Explain the difference between star schema and snowflake schema and when to choose each.**
- **Star Schema**: Single fact table with denormalized dimensions
- **Snowflake Schema**: Normalized dimensions with multiple levels
- **Choose Star**: When query performance is priority, simpler to understand
- **Choose Snowflake**: When storage efficiency matters, complex hierarchies

6️⃣ **Write a Python script to validate data quality and detect anomalies before loading.**
```python
def validate_data_quality(df):
    validation_results = {}
    
    # Check for nulls in critical columns
    critical_columns = ['customer_id', 'order_date', 'amount']
    for col in critical_columns:
        null_count = df.filter(col(col).isNull()).count()
        validation_results[f'{col}_nulls'] = null_count
    
    # Check for duplicates
    duplicate_count = df.count() - df.dropDuplicates().count()
    validation_results['duplicates'] = duplicate_count
    
    # Check for outliers (amount > 3 standard deviations)
    amount_stats = df.select(mean('amount'), stddev('amount')).collect()[0]
    outlier_count = df.filter(col('amount') > (amount_stats[0] + 3 * amount_stats[1])).count()
    validation_results['outliers'] = outlier_count
    
    return validation_results
```

7️⃣ **In PySpark, how would you efficiently join two very large DataFrames to avoid skew?**
```python
# Method 1: Broadcast small DataFrame
from pyspark.sql.functions import broadcast
result = large_df.join(broadcast(small_df), "key")

# Method 2: Salting for skewed keys
def salt_key(df, salt_buckets=10):
    return df.withColumn("salt", (rand() * salt_buckets).cast("int")) \
             .withColumn("salted_key", concat(col("key"), lit("_"), col("salt")))

# Method 3: Repartition before join
df1_repartitioned = df1.repartition(200, "join_key")
df2_repartitioned = df2.repartition(200, "join_key")
result = df1_repartitioned.join(df2_repartitioned, "join_key")
```

8️⃣ **Write PySpark code to find the top 3 customers by revenue per region.**
```python
from pyspark.sql.functions import sum, rank, col
from pyspark.sql.window import Window

window_spec = Window.partitionBy("region").orderBy(col("total_revenue").desc())

top_customers = df.groupBy("customer_id", "region") \
    .agg(sum("revenue").alias("total_revenue")) \
    .withColumn("rank", rank().over(window_spec)) \
    .filter(col("rank") <= 3) \
    .orderBy("region", "rank")
```

9️⃣ **You are processing real-time data from Event Hub into Delta tables. How would you implement this?**
```python
# Structured Streaming from Event Hub
streaming_df = spark.readStream \
    .format("eventhubs") \
    .options(**event_hub_config) \
    .load()

# Process and write to Delta Lake
processed_stream = streaming_df.select(
    from_json(col("body").cast("string"), schema).alias("data")
).select("data.*")

query = processed_stream.writeStream \
    .format("delta") \
    .option("checkpointLocation", "/checkpoint/path") \
    .outputMode("append") \
    .trigger(processingTime='10 seconds') \
    .start("/delta/real_time_data")
```

🔟 **How do you implement schema evolution in Delta Lake without breaking existing jobs?**
- Use `mergeSchema=true` option when writing
- Add new columns with default values
- Use `ALTER TABLE` for explicit schema changes
- Test schema changes in development first
- Use version control for schema definitions

1️⃣1️⃣ **How would you implement Slowly Changing Dimensions (SCD Type 2) in a data warehouse?**
```python
# SCD Type 2 implementation with Delta Lake
def implement_scd_type2(current_df, historical_df, business_key):
    # Add versioning columns
    current_with_version = current_df.withColumn("effective_date", current_date()) \
                                   .withColumn("end_date", lit(None)) \
                                   .withColumn("is_current", lit(True))
    
    # Merge logic
    delta_table = DeltaTable.forPath(spark, historical_table_path)
    delta_table.alias("target").merge(
        current_with_version.alias("source"),
        f"target.{business_key} = source.{business_key}"
    ).whenMatchedUpdate(
        condition="target.is_current = true AND target.hash_key != source.hash_key",
        set={
            "end_date": current_date(),
            "is_current": "false"
        }
    ).whenNotMatchedInsertAll().execute()
```

1️⃣2️⃣ **Late-arriving data is detected in a batch pipeline – how do you ensure correctness of historical reporting?**
- Implement watermarking with configurable retention periods
- Use Delta Lake's time travel for reprocessing
- Design fact tables to handle late-arriving facts
- Implement data quality monitoring for late arrivals
- Use surrogate keys for dimension lookups

1️⃣3️⃣ **How do you design a pipeline that supports both batch and streaming workloads simultaneously?**
- Use Lambda architecture with batch and speed layers
- Implement unified data models in Delta Lake
- Use Structured Streaming for real-time processing
- Batch layer handles historical data and corrections
- Merge both layers for complete analytics

1️⃣4️⃣ **What is your approach to building incremental data loads in Azure Data Factory pipelines?**
- Use watermark columns to track last processed data
- Implement lookup activities to retrieve watermarks
- Use conditional activities for incremental vs. full loads
- Store watermarks in Azure SQL Database or Key Vault
- Implement error handling and retry policies

1️⃣5️⃣ **Your PySpark job is failing due to skewed joins. Walk through your debugging and optimization steps.**
1. Identify skew using Spark UI (look for tasks taking much longer)
2. Analyze data distribution on join keys
3. Apply salting technique for skewed keys
4. Use broadcast joins for small tables
5. Repartition data before joins
6. Enable Adaptive Query Execution (AQE)

1️⃣6️⃣ **Explain the architecture of Azure Databricks integrated with Delta Lake in a production environment.**
- Databricks workspace with Unity Catalog for governance
- Azure Data Lake Storage Gen2 for data persistence
- Azure Key Vault for secrets management
- Azure Active Directory for authentication
- Azure Monitor for logging and monitoring
- CI/CD pipeline with Azure DevOps

1️⃣7️⃣ **How do you optimize query performance and concurrency in a Synapse dedicated SQL pool?**
- Implement proper distribution strategies (hash, round-robin, replicated)
- Use columnstore indexes for analytical workloads
- Optimize statistics and create covering indexes
- Implement workload management with resource classes
- Use result set caching for repeated queries

1️⃣8️⃣ **Your data lake contains sensitive PII data. What best practices do you follow to secure data and manage secrets?**
- Implement encryption at rest and in transit
- Use Azure Key Vault for secret management
- Apply row-level security and column-level encryption
- Implement data masking for non-production environments
- Use Azure Purview for data classification and lineage
- Regular security audits and access reviews

1️⃣9️⃣ **How do you establish end-to-end data lineage and governance using Microsoft Purview?**
- Register data sources (Azure Data Lake, SQL databases, etc.)
- Configure automated scanning for schema discovery
- Set up data classification and sensitivity labels
- Implement access policies and data retention rules
- Create lineage maps showing data flow
- Enable compliance reporting and auditing

2️⃣0️⃣ **Design an end-to-end analytics pipeline that ingests from Event Hub, processes data in Databricks, stores it in Synapse, and powers dashboards in Power BI.**
```
Event Hub → Azure Data Factory → Databricks (Streaming) → Delta Lake → 
Synapse (via PolyBase/Copy) → Power BI → Business Users

Components:
- Event Hub: Real-time data ingestion
- ADF: Orchestration and scheduling
- Databricks: Stream processing and ML
- Delta Lake: ACID transactions and schema evolution
- Synapse: Data warehouse and analytics
- Power BI: Visualization and reporting
- Azure Key Vault: Secrets management
- Azure Monitor: Monitoring and alerting
```

## Key Success Factors for Data Engineering Interviews

1. **Technical Depth**: Understand the "why" behind tools and technologies
2. **System Design**: Think about scalability, reliability, and maintainability
3. **Problem Solving**: Break down complex problems into manageable pieces
4. **Communication**: Explain technical concepts clearly and concisely
5. **Real-world Experience**: Draw from actual project experiences and challenges
6. **Continuous Learning**: Stay updated with latest trends and best practices

Remember: Interviewers want to see how you think through problems, not just memorized answers. Focus on demonstrating your analytical approach and practical experience.
