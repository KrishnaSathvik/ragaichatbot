---
tags: [krishna, data-engineering, cost-optimization, databricks, job-clusters, spot-instances]
persona: de
---

# Cost Optimization Without Auto-scaling - Krishna's Implementation

## Cost Control Strategies

### Job Clusters with Fixed Min Nodes
```python
# Use job clusters with minimum nodes fixed
job_config = {
    "new_cluster": {
        "spark_version": "13.3.x-scala2.12",
        "node_type_id": "i3.xlarge",
        "num_workers": 3,  # Fixed minimum for 10TB+ data
        "max_workers": 6,  # Cap maximum
        "spark_conf": {
            "spark.sql.adaptive.enabled": "true",
            "spark.sql.adaptive.coalescePartitions.enabled": "true"
        }
    }
}

# Schedule off-peak hours
schedule_config = {
    "cron": "0 0 1 * * ?",  # 1 AM daily
    "timezone": "UTC"
}
```

### Spot/Preemptible Instances
```python
# Use spot instances for retry-safe jobs
spot_config = {
    "new_cluster": {
        "node_type_id": "i3.xlarge",
        "num_workers": 3,
        "aws_attributes": {
            "availability": "SPOT_WITH_FALLBACK",
            "spot_bid_price_percent": 50
        }
    }
}

# Implement retry logic for spot interruptions
def run_with_retry(job_func, max_retries=3):
    for attempt in range(max_retries):
        try:
            return job_func()
        except Exception as e:
            if "spot" in str(e).lower() and attempt < max_retries - 1:
                time.sleep(60 * (2 ** attempt))  # Exponential backoff
                continue
            raise
```

### File Optimization
```python
# Weekly OPTIMIZE + ZORDER
def optimize_tables():
    tables = ["bronze.pharmacy_orders", "silver.prescriptions", "gold.fact_prescriptions"]
    
    for table in tables:
        # OPTIMIZE for file compaction
        spark.sql(f"OPTIMIZE {table}")
        
        # ZORDER for query performance
        spark.sql(f"OPTIMIZE {table} ZORDER BY (prescription_id, order_date)")
        
        # Vacuum old files
        spark.sql(f"VACUUM {table} RETAIN 168 HOURS")

# Enable auto-optimize at write time
df.write \
    .format("delta") \
    .option("autoOptimize", "true") \
    .option("optimizeWrite", "true") \
    .mode("append") \
    .save("/path/to/table")
```

### Multi-task Workflows
```python
# Consolidate tasks to avoid cluster spin-ups
workflow_tasks = [
    {
        "task_key": "bronze_ingestion",
        "notebook_task": {
            "notebook_path": "/bronze/ingest_pharmacy"
        }
    },
    {
        "task_key": "silver_processing",
        "notebook_task": {
            "notebook_path": "/silver/process_prescriptions"
        },
        "depends_on": [{"task_key": "bronze_ingestion"}]
    },
    {
        "task_key": "gold_aggregation",
        "notebook_task": {
            "notebook_path": "/gold/aggregate_prescriptions"
        },
        "depends_on": [{"task_key": "silver_processing"}]
    }
]
```

### Tune Shuffle Partitions
```python
# Tune partitions based on data size
data_size_gb = df.rdd.getNumPartitions() * 128 / 1024  # Approximate GB

if data_size_gb < 1:
    spark.conf.set("spark.sql.shuffle.partitions", "200")
elif data_size_gb < 10:
    spark.conf.set("spark.sql.shuffle.partitions", "400")
else:
    spark.conf.set("spark.sql.shuffle.partitions", "800")

# Enable AQE
spark.conf.set("spark.sql.adaptive.enabled", "true")
spark.conf.set("spark.sql.adaptive.coalescePartitions.enabled", "true")
spark.conf.set("spark.sql.adaptive.skewJoin.enabled", "true")
```

## Krishna's Experience

At Walgreens, I implemented these cost optimization strategies for our 10TB+ monthly data processing pipeline. Using job clusters with fixed minimum nodes and spot instances reduced our compute costs by 50% while maintaining performance.

The weekly OPTIMIZE and ZORDER operations kept file sizes optimal, and consolidating tasks into multi-task workflows eliminated unnecessary cluster spin-ups. This approach supported 500+ business users while reducing monthly compute costs from $25K to $12K.
