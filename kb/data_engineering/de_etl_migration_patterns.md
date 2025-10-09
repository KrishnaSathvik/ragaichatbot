---
tags: [data-engineer, etl-migration, informatica, pyspark, modernization, legacy-migration]
persona: de
---

# ETL Migration Patterns - Krishna's Experience

## Introduction
**Krishna's Migration Background:**
At Walgreens, I led the migration of 200+ Informatica workflows to Databricks PySpark. This transformation reduced processing time from 20 hours to 6 hours and cut costs by 40%. Here's everything I learned.

## Why Migrate from Informatica

### Challenges with Informatica
**Krishna's Pain Points:**
- **Cost:** Expensive licensing ($500K+ annually)
- **Scalability:** Limited horizontal scaling
- **Development:** GUI-based, hard to version control
- **Maintenance:** Complex dependency management
- **Performance:** Long processing times on large datasets
- **Cloud:** Not cloud-native, requires VMs

### Benefits of PySpark/Databricks
**Krishna's Wins:**
- **Cost:** 40-60% cheaper with cloud elasticity
- **Scalability:** Auto-scaling clusters
- **Development:** Code-based, Git-friendly
- **Performance:** Distributed processing, 3-5x faster
- **Cloud-Native:** Serverless, managed platform
- **Skills:** Python/SQL easier to hire

## Migration Patterns

### Pattern 1: Source Qualifier → DataFrame Read
**Informatica:**
```
Source Qualifier: ORDERS table
Filter: ORDER_DATE >= $LastRunDate
Columns: ORDER_ID, CUSTOMER_ID, ORDER_DATE, AMOUNT
```

**PySpark Equivalent:**
```python
from pyspark.sql import functions as F

# Read from source
df_orders = (
    spark.read
    .format("jdbc")
    .option("url", "jdbc:oracle:thin:@//hostname:1521/service")
    .option("dbtable", "ORDERS")
    .option("user", dbutils.secrets.get("scope", "db-user"))
    .option("password", dbutils.secrets.get("scope", "db-password"))
    .option("driver", "oracle.jdbc.driver.OracleDriver")
    .load()
    
    # Apply filter (pushdown to source)
    .filter(F.col("ORDER_DATE") >= last_run_date)
    
    # Select columns
    .select("ORDER_ID", "CUSTOMER_ID", "ORDER_DATE", "AMOUNT")
)
```

### Pattern 2: Expression Transformation → withColumn
**Informatica:**
```
Expression Transformation:
- FULL_NAME = FIRST_NAME || ' ' || LAST_NAME
- ORDER_YEAR = TO_CHAR(ORDER_DATE, 'YYYY')
- DISCOUNT_PCT = (DISCOUNT_AMOUNT / ORDER_AMOUNT) * 100
- IS_HIGH_VALUE = IIF(ORDER_AMOUNT > 1000, 'Y', 'N')
```

**PySpark Equivalent:**
```python
df_transformed = (
    df_orders
    .withColumn("FULL_NAME", F.concat(F.col("FIRST_NAME"), F.lit(" "), F.col("LAST_NAME")))
    .withColumn("ORDER_YEAR", F.year("ORDER_DATE"))
    .withColumn("DISCOUNT_PCT", (F.col("DISCOUNT_AMOUNT") / F.col("ORDER_AMOUNT")) * 100)
    .withColumn("IS_HIGH_VALUE", F.when(F.col("ORDER_AMOUNT") > 1000, "Y").otherwise("N"))
)
```

### Pattern 3: Aggregator → groupBy + agg
**Informatica:**
```
Aggregator Transformation:
Group By: CUSTOMER_ID, ORDER_MONTH
Aggregations:
- ORDER_COUNT = COUNT(ORDER_ID)
- TOTAL_AMOUNT = SUM(ORDER_AMOUNT)
- AVG_AMOUNT = AVG(ORDER_AMOUNT)
```

**PySpark Equivalent:**
```python
df_aggregated = (
    df_orders
    .groupBy("CUSTOMER_ID", F.date_trunc("month", "ORDER_DATE").alias("ORDER_MONTH"))
    .agg(
        F.count("ORDER_ID").alias("ORDER_COUNT"),
        F.sum("ORDER_AMOUNT").alias("TOTAL_AMOUNT"),
        F.avg("ORDER_AMOUNT").alias("AVG_AMOUNT")
    )
)
```

### Pattern 4: Joiner → join
**Informatica:**
```
Joiner Transformation:
Master: CUSTOMERS
Detail: ORDERS
Join Type: INNER JOIN
Condition: CUSTOMERS.CUSTOMER_ID = ORDERS.CUSTOMER_ID
```

**PySpark Equivalent:**
```python
# Read customers
df_customers = spark.read.format("delta").load("/mnt/dim/customers")

# Join
df_joined = (
    df_orders.alias("o")
    .join(
        df_customers.alias("c"),
        on=F.col("o.CUSTOMER_ID") == F.col("c.CUSTOMER_ID"),
        how="inner"
    )
    .select(
        "o.ORDER_ID",
        "o.ORDER_DATE",
        "o.ORDER_AMOUNT",
        "c.CUSTOMER_NAME",
        "c.CUSTOMER_SEGMENT"
    )
)
```

### Pattern 5: Lookup → broadcast join
**Informatica:**
```
Lookup Transformation:
Lookup Table: PRODUCT_DIM (small)
Lookup Condition: SOURCE.PRODUCT_ID = LOOKUP.PRODUCT_ID
Return: PRODUCT_NAME, PRODUCT_CATEGORY
Cache: Yes
```

**PySpark Equivalent:**
```python
# Read small lookup table
df_products = spark.read.format("delta").load("/mnt/dim/products")

# Broadcast join (efficient for small tables)
df_enriched = (
    df_orders
    .join(
        F.broadcast(df_products),
        "PRODUCT_ID",
        "left"
    )
    .select(
        "ORDER_ID",
        "ORDER_AMOUNT",
        "PRODUCT_NAME",
        "PRODUCT_CATEGORY"
    )
)
```

### Pattern 6: Router → filter + union
**Informatica:**
```
Router Transformation:
Group 1 (HIGH_VALUE): ORDER_AMOUNT > 1000
Group 2 (MEDIUM_VALUE): ORDER_AMOUNT BETWEEN 100 AND 1000
Group 3 (LOW_VALUE): ORDER_AMOUNT < 100
Default: Reject
```

**PySpark Equivalent:**
```python
# Split data into groups
df_high = df_orders.filter(F.col("ORDER_AMOUNT") > 1000).withColumn("VALUE_TIER", F.lit("HIGH"))
df_medium = df_orders.filter((F.col("ORDER_AMOUNT") >= 100) & (F.col("ORDER_AMOUNT") <= 1000)).withColumn("VALUE_TIER", F.lit("MEDIUM"))
df_low = df_orders.filter(F.col("ORDER_AMOUNT") < 100).withColumn("VALUE_TIER", F.lit("LOW"))

# Union back if needed
df_categorized = df_high.union(df_medium).union(df_low)

# Or use single when/otherwise (more efficient)
df_categorized = (
    df_orders
    .withColumn(
        "VALUE_TIER",
        F.when(F.col("ORDER_AMOUNT") > 1000, "HIGH")
         .when(F.col("ORDER_AMOUNT") >= 100, "MEDIUM")
         .otherwise("LOW")
    )
)
```

### Pattern 7: Sorter → orderBy
**Informatica:**
```
Sorter Transformation:
Sort Keys: CUSTOMER_ID (ASC), ORDER_DATE (DESC)
```

**PySpark Equivalent:**
```python
df_sorted = (
    df_orders
    .orderBy(
        F.col("CUSTOMER_ID").asc(),
        F.col("ORDER_DATE").desc()
    )
)
```

### Pattern 8: Rank → window functions
**Informatica:**
```
Rank Transformation:
Group By: CUSTOMER_ID
Order By: ORDER_AMOUNT DESC
Rank Type: DENSE_RANK
```

**PySpark Equivalent:**
```python
from pyspark.sql.window import Window

window_spec = Window.partitionBy("CUSTOMER_ID").orderBy(F.desc("ORDER_AMOUNT"))

df_ranked = (
    df_orders
    .withColumn("RANK", F.dense_rank().over(window_spec))
    .withColumn("ROW_NUMBER", F.row_number().over(window_spec))
)
```

### Pattern 9: Update Strategy → Merge/Upsert
**Informatica:**
```
Update Strategy Transformation:
Insert: FLAG_INSERT = 1
Update: FLAG_UPDATE = 1
Delete: FLAG_DELETE = 1
```

**PySpark Equivalent:**
```python
from delta.tables import DeltaTable

# Read target table
delta_table = DeltaTable.forPath(spark, "/mnt/silver/customers")

# Merge (upsert)
(
    delta_table.alias("target")
    .merge(
        df_source.alias("source"),
        "target.CUSTOMER_ID = source.CUSTOMER_ID"
    )
    .whenMatchedUpdate(
        condition="source.UPDATED_AT > target.UPDATED_AT",
        set={
            "CUSTOMER_NAME": "source.CUSTOMER_NAME",
            "CUSTOMER_SEGMENT": "source.CUSTOMER_SEGMENT",
            "UPDATED_AT": "source.UPDATED_AT"
        }
    )
    .whenNotMatchedInsert(
        values={
            "CUSTOMER_ID": "source.CUSTOMER_ID",
            "CUSTOMER_NAME": "source.CUSTOMER_NAME",
            "CUSTOMER_SEGMENT": "source.CUSTOMER_SEGMENT",
            "CREATED_AT": "source.CREATED_AT",
            "UPDATED_AT": "source.UPDATED_AT"
        }
    )
    .execute()
)
```

## Real Migration Example

### Informatica Workflow (Before)
**Complex Customer Data Pipeline:**
```
Workflow: WF_CUSTOMER_DAILY
├── Session: SQ_CUSTOMERS (Source Qualifier)
├── Transformation: EXP_CLEAN (Expression - clean data)
├── Transformation: LKP_SEGMENT (Lookup - get segment)
├── Transformation: AGG_METRICS (Aggregator - calculate metrics)
├── Transformation: JNR_ORDERS (Joiner - join with orders)
├── Transformation: RTR_SPLIT (Router - split by segment)
├── Session: TGT_GOLD_CUSTOMERS (Target - Gold table)
└── Session: TGT_SILVER_CUSTOMERS (Target - Silver table)

Runtime: 4 hours
```

### PySpark Equivalent (After)
**Modernized Pipeline:**
```python
# Complete pipeline in PySpark
from pyspark.sql import functions as F, Window
from delta.tables import DeltaTable

def customer_daily_pipeline(execution_date: str):
    """
    Migrated customer pipeline
    Runtime: 45 minutes (5x faster!)
    """
    
    # 1. Source Qualifier - Read customers
    df_customers = (
        spark.read
        .format("jdbc")
        .option("url", jdbc_url)
        .option("dbtable", "CUSTOMERS")
        .option("fetchsize", "10000")
        .load()
        .filter(F.col("UPDATED_DATE") >= execution_date)
    )
    
    # 2. Expression - Clean data
    df_clean = (
        df_customers
        .withColumn("CUSTOMER_NAME", F.trim(F.upper(F.col("CUSTOMER_NAME"))))
        .withColumn("EMAIL", F.lower(F.trim(F.col("EMAIL"))))
        .withColumn("PHONE", F.regexp_replace("PHONE", "[^0-9]", ""))
        .dropDuplicates(["CUSTOMER_ID"])
    )
    
    # 3. Lookup - Get segment (broadcast join for small table)
    df_segments = spark.read.format("delta").load("/mnt/dim/segments")
    
    df_with_segment = (
        df_clean
        .join(F.broadcast(df_segments), "SEGMENT_CODE", "left")
        .select("df_clean.*", "df_segments.SEGMENT_NAME")
    )
    
    # 4. Aggregator - Calculate metrics
    df_orders = spark.read.format("delta").load("/mnt/silver/orders")
    
    df_metrics = (
        df_orders
        .groupBy("CUSTOMER_ID")
        .agg(
            F.count("ORDER_ID").alias("ORDER_COUNT"),
            F.sum("ORDER_AMOUNT").alias("LIFETIME_VALUE"),
            F.max("ORDER_DATE").alias("LAST_ORDER_DATE")
        )
    )
    
    # 5. Joiner - Join with orders metrics
    df_enriched = (
        df_with_segment.alias("c")
        .join(df_metrics.alias("m"), "CUSTOMER_ID", "left")
        .select(
            "c.*",
            "m.ORDER_COUNT",
            "m.LIFETIME_VALUE",
            "m.LAST_ORDER_DATE"
        )
    )
    
    # 6. Router - Split by segment (filter + write separately)
    # Gold customers (high value)
    df_gold = df_enriched.filter(F.col("LIFETIME_VALUE") > 10000)
    df_gold.write.format("delta").mode("overwrite").save("/mnt/gold/customers_premium")
    
    # Silver customers (all customers)
    df_enriched.write.format("delta").mode("overwrite").save("/mnt/silver/customers")
    
    print(f"✅ Processed {df_enriched.count():,} customers in {execution_date}")

# Run pipeline
customer_daily_pipeline("2024-01-15")
```

**Results:**
- Runtime: 4 hours → 45 minutes (5.3x faster)
- Cost: $500/month → $150/month (70% reduction)
- Maintainability: 10 transformations → 1 Python script
- Version Control: GUI changes → Git commits

## Migration Best Practices

### 1. Assess & Prioritize
**Krishna's Assessment Framework:**
```
Priority Matrix:
High Priority:
- Critical business processes
- Long-running workflows (>2 hours)
- Frequently modified workflows
- Simple logic (easier to migrate)

Low Priority:
- Infrequently run jobs
- Complex custom transformations
- Legacy workflows with unclear business logic
```

### 2. Test Thoroughly
**Krishna's Testing Strategy:**
```python
def validate_migration(informatica_output_path, pyspark_output_path):
    """
    Compare Informatica vs PySpark output
    """
    # Read both outputs
    df_infa = spark.read.csv(informatica_output_path)
    df_pyspark = spark.read.csv(pyspark_output_path)
    
    # Compare record counts
    infa_count = df_infa.count()
    pyspark_count = df_pyspark.count()
    assert infa_count == pyspark_count, f"Count mismatch: {infa_count} vs {pyspark_count}"
    
    # Compare checksums
    infa_checksum = df_infa.select(F.sum("AMOUNT")).first()[0]
    pyspark_checksum = df_pyspark.select(F.sum("AMOUNT")).first()[0]
    assert infa_checksum == pyspark_checksum, f"Sum mismatch: {infa_checksum} vs {pyspark_checksum}"
    
    # Sample row comparison
    df_diff = df_infa.exceptAll(df_pyspark)
    diff_count = df_diff.count()
    
    if diff_count > 0:
        print(f"⚠️  Found {diff_count} different rows")
        df_diff.show(20, False)
        return False
    
    print("✅ Validation passed!")
    return True
```

### 3. Parallel Run Period
**Krishna's Cutover Strategy:**
```
Week 1-2: Run both Informatica and PySpark, compare outputs daily
Week 3-4: PySpark primary, Informatica backup
Week 5: Decommission Informatica
```

### 4. Documentation
**Krishna's Migration Documentation:**
```markdown
# Migration: WF_CUSTOMER_DAILY

## Source Workflow
- **Informatica Folder:** PROD/CUSTOMER
- **Workflow Name:** WF_CUSTOMER_DAILY
- **Schedule:** Daily at 2 AM
- **Dependencies:** WF_ORDERS_LOAD (must complete first)
- **Runtime:** 4 hours
- **Transformations:** 12

## Target Pipeline
- **Databricks Notebook:** /Pipelines/Customer/daily_load
- **Cluster:** production-etl
- **Schedule:** ADF trigger, daily at 3 AM
- **Dependencies:** pl_orders_load (ADF)
- **Runtime:** 45 minutes
- **Logic:** Single PySpark script (150 lines)

## Key Changes
1. Source Qualifier → JDBC read with pushdown predicates
2. 5 Expression transforms → chained withColumn operations
3. Lookup → broadcast join (10x faster)
4. Aggregator → groupBy + agg
5. Update Strategy → Delta Lake merge

## Validation Results
- Record count match: ✅
- Sum validation: ✅
- Sample comparison: ✅
- Business user sign-off: ✅ (Jane Doe, 2024-01-20)

## Rollback Plan
If issues found:
1. Disable ADF pipeline
2. Re-enable Informatica workflow
3. Investigate PySpark issues
4. Fix and retest

## Sign-off
- Data Engineer: Krishna (2024-01-15)
- Business Owner: Jane Doe (2024-01-20)
- Production Cutover: 2024-01-25
```

This migration expertise helped Walgreens modernize their data platform and achieve 40% cost savings!

