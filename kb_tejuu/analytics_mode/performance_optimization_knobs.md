---
tags: [tejuu, analytics, performance, pyspark, optimization, aqe, broadcast-joins]
persona: analytics
---

# Performance Optimization Knobs - Tejuu's Implementation

## Performance Tuning Strategies

### AQE and Partition Management
```python
# Enable AQE
spark.conf.set("spark.sql.adaptive.enabled", "true")
spark.conf.set("spark.sql.adaptive.coalescePartitions.enabled", "true")
spark.conf.set("spark.sql.adaptive.skewJoin.enabled", "true")
spark.conf.set("spark.sql.adaptive.localShuffleReader.enabled", "true")

# Coalesce partitions post-filter
df_filtered = df.filter(col("status") == "ACTIVE") \
    .coalesce(200)  # Reduce partitions after filtering

# Repartition for time series data
df_time_series = df.repartitionByRange(200, col("order_date"))
```

### Broadcast Joins
```python
from pyspark.sql.functions import broadcast

# Broadcast small tables (< 10-50MB)
small_dim = spark.table("dim_customer")  # 5MB
large_fact = spark.table("fact_sales")   # 1GB

# Force broadcast join
result = large_fact.join(
    broadcast(small_dim), 
    "customer_id", 
    "left"
)

# Check if broadcast is happening
result.explain()  # Look for "BroadcastHashJoin"
```

### Handle Skewed Data
```python
# Salt skewed join keys
from pyspark.sql.functions import concat, lit, rand

# Add salt to skewed key
df_salted = df.withColumn(
    "salted_key", 
    concat(col("skewed_key"), lit("_"), (rand() * 10).cast("int"))
)

# Join with salted key
result = df_salted.join(
    dim_table.withColumn("salted_key", concat(col("key"), lit("_"), lit(0))),
    "salted_key"
).drop("salted_key")
```

### Caching Strategy
```python
# Cache only if reused 2+ times
df_cached = df.cache()

# Use the cached DataFrame multiple times
result1 = df_cached.filter(col("status") == "ACTIVE").count()
result2 = df_cached.groupBy("category").count().collect()

# Unpersist when done
df_cached.unpersist()
```

### Monitor Performance
```python
# Monitor Spark UI metrics
def analyze_performance(df):
    # Check execution plan
    df.explain(True)
    
    # Get stage metrics
    stages = spark.sparkContext.statusTracker().getJobInfo(0).stageIds
    
    # Check for wide vs narrow dependencies
    # Wide: shuffles, narrow: map operations
    
    # Look for skew indicators
    # - Uneven partition sizes
    # - Long-running tasks
    # - High shuffle read/write ratios

# Example monitoring
df_with_metrics = df.withColumn("partition_id", spark_partition_id())
partition_counts = df_with_metrics.groupBy("partition_id").count().collect()
print("Partition size distribution:", partition_counts)
```

## Tejuu's Experience

At Stryker, I used these performance optimization techniques to reduce our 15M+ transaction processing time from 2-3 hours to 1 hour. The key was enabling AQE, using broadcast joins for small dimension tables, and salting skewed customer keys.

Monitoring the Spark UI helped identify bottlenecks - we found that 80% of processing time was spent on skewed joins. After implementing salting and broadcast joins, we achieved 45% performance improvement while supporting 1,000+ users globally.

The caching strategy was crucial - we only cached DataFrames that were reused 3+ times, and always unpersisted them to free memory. This prevented OOM errors and improved overall cluster utilization.
