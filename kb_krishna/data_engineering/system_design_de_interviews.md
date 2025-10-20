---
tags: [data-engineering, system-design, interview, architecture, etl, data-lake, data-warehouse]
persona: de
---

# Data Engineering System Design Interview Guide - Krishna's Approach

## Introduction
**Krishna's Data Engineering Philosophy:**
Having built enterprise data platforms at Walgreens processing 10TB+ daily, I approach data engineering system design by focusing on scalability, reliability, and data quality. My experience with Databricks, Azure Data Factory, and Delta Lake gives me practical insights into building data systems that handle real-world complexity.

## Core Data Engineering Design Principles

### 1. Data Architecture Patterns
**Krishna's Architecture Approach:**
- **Medallion Architecture**: Bronze (raw) → Silver (cleaned) → Gold (business-ready)
- **Lambda Architecture**: Batch + streaming processing
- **Data Mesh**: Domain-oriented data ownership
- **Event-driven**: Real-time data processing with event streaming

**Example Medallion Implementation:**
```
Raw Data Sources → Bronze Layer → Silver Layer → Gold Layer → Analytics
     ↓               ↓            ↓            ↓           ↓
  APIs/DBs/      Raw Storage   Cleaned      Business     Power BI/
  Files/         (ADLS)        Data         Models       Tableau
  Streams        (Parquet)     (Delta)      (Star Schema)
```

### 2. Scalability & Performance
**Krishna's Scalability Patterns:**
- **Partitioning**: Date-based partitioning for time-series data
- **Clustering**: Z-order indexing for query performance
- **Caching**: Materialized views and query result caching
- **Auto-scaling**: Dynamic resource allocation based on workload

## Common Data Engineering System Design Questions

### Question 1: Design a Real-Time Data Pipeline

**Krishna's Approach:**

**Requirements:**
- Process 1M events per second
- <5 second end-to-end latency
- 99.9% data accuracy
- Support for late-arriving data

**Architecture:**
```
Data Sources → Message Queue → Stream Processing → Data Lake → Analytics
     ↓             ↓              ↓                ↓          ↓
  IoT/APIs/    Kafka/Event    Spark Streaming   Delta Lake  Real-time
  Databases    Hubs/          /Flink/           /Iceberg    Dashboards
  Files        Kinesis        Kafka Streams     /Hudi       /Alerts
```

**Detailed Components:**

1. **Data Ingestion:**
   - **Message Queue**: Kafka with 3 replicas for durability
   - **Schema Registry**: Confluent Schema Registry for schema evolution
   - **Dead Letter Queue**: Handle failed messages for reprocessing
   - **Monitoring**: Lag monitoring and alerting

2. **Stream Processing:**
   - **Processing Engine**: Apache Spark Streaming or Flink
   - **Windowing**: Tumbling windows for aggregations
   - **Watermarking**: Handle late-arriving data
   - **Checkpointing**: Ensure exactly-once processing

3. **Storage Layer:**
   - **Data Lake**: Delta Lake for ACID transactions
   - **Partitioning**: By date and hour for efficient querying
   - **Compaction**: Regular compaction to optimize file sizes
   - **Retention**: Automated data lifecycle management

4. **Analytics Layer:**
   - **Real-time Dashboards**: Power BI with DirectQuery
   - **Alerting**: Real-time anomaly detection
   - **API Layer**: REST APIs for data access
   - **Caching**: Redis for frequently accessed data

**Code Example - Spark Streaming:**
```python
from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *

# Create Spark session
spark = SparkSession.builder \
    .appName("RealTimeDataPipeline") \
    .config("spark.sql.adaptive.enabled", "true") \
    .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
    .getOrCreate()

# Read from Kafka
df = spark \
    .readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "localhost:9092") \
    .option("subscribe", "events") \
    .load()

# Parse JSON and add watermark
parsed_df = df \
    .select(from_json(col("value").cast("string"), schema).alias("data")) \
    .select("data.*") \
    .withWatermark("timestamp", "10 minutes")

# Process and aggregate
aggregated_df = parsed_df \
    .groupBy(window(col("timestamp"), "5 minutes"), col("device_id")) \
    .agg(
        count("*").alias("event_count"),
        avg("temperature").alias("avg_temperature"),
        max("timestamp").alias("last_seen")
    )

# Write to Delta Lake
query = aggregated_df \
    .writeStream \
    .format("delta") \
    .option("checkpointLocation", "/path/to/checkpoint") \
    .option("path", "/path/to/delta/table") \
    .trigger(processingTime="1 minute") \
    .start()
```

### Question 2: Design a Data Lakehouse Architecture

**Krishna's Approach:**

**Requirements:**
- Store 100TB+ of data
- Support both batch and streaming workloads
- ACID transactions for data consistency
- Schema evolution support

**Architecture:**
```
Data Sources → Ingestion Layer → Storage Layer → Processing Layer → Serving Layer
     ↓             ↓                ↓              ↓               ↓
  Multiple      ADF/Spark        Delta Lake     Databricks      Power BI/
  Sources       Streaming        /Iceberg/      /Spark/         Tableau/
                /Kafka          Hudi           Presto          APIs
```

**Key Components:**

1. **Storage Layer (Delta Lake):**
   - **ACID Transactions**: Ensure data consistency
   - **Schema Evolution**: Add columns without breaking existing queries
   - **Time Travel**: Query historical versions of data
   - **VACUUM**: Clean up old files automatically

2. **Processing Layer:**
   - **Batch Processing**: Daily ETL jobs for large datasets
   - **Stream Processing**: Real-time data processing
   - **Interactive Queries**: Ad-hoc analysis with Presto/Trino
   - **ML Workloads**: Feature engineering and model training

3. **Data Organization:**
   - **Bronze Layer**: Raw data as-is from sources
   - **Silver Layer**: Cleaned and validated data
   - **Gold Layer**: Business-ready aggregated data
   - **Feature Store**: ML features for model training

**Delta Lake Implementation:**
```python
# Create Delta table
df.write.format("delta").mode("overwrite").save("/path/to/delta/table")

# Read with time travel
df_v1 = spark.read.format("delta").option("versionAsOf", 1).load("/path/to/delta/table")

# Merge operation for upserts
from delta.tables import DeltaTable

delta_table = DeltaTable.forPath(spark, "/path/to/delta/table")

delta_table.alias("target").merge(
    updates_df.alias("source"),
    "target.id = source.id"
).whenMatchedUpdateAll().whenNotMatchedInsertAll().execute()

# Optimize table
delta_table.optimize().executeZOrderBy("date", "customer_id")
```

### Question 3: Design a Data Quality Framework

**Krishna's Approach:**

**Requirements:**
- Automated data quality checks
- Real-time monitoring and alerting
- Data lineage tracking
- SLA compliance monitoring

**Architecture:**
```
Data Pipeline → Quality Checks → Monitoring → Alerting → Remediation
     ↓              ↓             ↓          ↓          ↓
  ETL/ELT       Great          Grafana    PagerDuty   Auto-fix/
  Processes     Expectations   /DataDog   /Slack      Manual
                /dbt tests     Dashboards Notifications Review
```

**Quality Framework Components:**

1. **Data Quality Rules:**
   - **Completeness**: Check for null values
   - **Accuracy**: Validate data ranges and formats
   - **Consistency**: Cross-field validation
   - **Timeliness**: Data freshness checks
   - **Uniqueness**: Duplicate detection

2. **Implementation with Great Expectations:**
```python
import great_expectations as ge

# Create expectation suite
suite = context.create_expectation_suite("data_quality_suite")

# Add expectations
validator.expect_column_values_to_not_be_null("customer_id")
validator.expect_column_values_to_be_between("age", min_value=0, max_value=120)
validator.expect_column_values_to_match_regex("email", r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
validator.expect_table_row_count_to_be_between(min_value=1000, max_value=1000000)

# Run validation
results = validator.validate()
```

3. **Monitoring & Alerting:**
   - **Metrics**: Data quality scores, failure rates, SLA compliance
   - **Dashboards**: Real-time quality monitoring
   - **Alerting**: Immediate notification on quality failures
   - **Reporting**: Daily/weekly quality reports

## Performance Optimization Strategies

### 1. Query Optimization
**Krishna's Optimization Techniques:**
- **Partitioning**: Partition by date for time-series queries
- **Clustering**: Z-order by frequently filtered columns
- **Indexing**: Create indexes on join keys and filter columns
- **Caching**: Cache frequently accessed data

### 2. Storage Optimization
**Krishna's Storage Strategies:**
- **File Format**: Use Parquet for columnar storage
- **Compression**: Snappy or Zstd compression
- **File Size**: Optimize file sizes (128MB-1GB)
- **Compaction**: Regular compaction to merge small files

### 3. Processing Optimization
**Krishna's Processing Techniques:**
- **Parallel Processing**: Use multiple cores and nodes
- **Memory Management**: Optimize executor memory settings
- **Broadcast Joins**: Use broadcast for small tables
- **Predicate Pushdown**: Push filters to storage layer

## Data Governance & Security

### 1. Data Lineage
**Krishna's Lineage Approach:**
- **Automatic Tracking**: Use tools like Apache Atlas or Purview
- **Manual Documentation**: Document critical data flows
- **Impact Analysis**: Understand downstream dependencies
- **Change Management**: Track schema and logic changes

### 2. Access Control
**Krishna's Security Model:**
- **Role-Based Access**: Different access levels for different roles
- **Data Classification**: Classify data by sensitivity level
- **Encryption**: Encrypt data at rest and in transit
- **Audit Logging**: Log all data access and modifications

### 3. Compliance
**Krishna's Compliance Strategy:**
- **Data Retention**: Implement retention policies
- **Right to be Forgotten**: Support data deletion requests
- **Privacy**: Implement PII masking and anonymization
- **Regulatory**: Meet GDPR, HIPAA, SOX requirements

## Monitoring & Observability

### 1. Key Metrics
**Krishna's Monitoring Strategy:**
- **Data Quality**: Completeness, accuracy, consistency scores
- **Performance**: Query latency, throughput, resource utilization
- **Reliability**: Pipeline success rate, error rate, MTTR
- **Cost**: Storage costs, compute costs, data transfer costs

### 2. Alerting Strategy
**Krishna's Alerting Approach:**
- **Critical**: Pipeline failures, data quality breaches
- **Warning**: Performance degradation, resource constraints
- **Info**: Successful deployments, performance improvements

## Common Follow-up Questions

### Technical Deep Dives
- "How would you handle a 100x increase in data volume?"
- "What if the data lake becomes corrupted?"
- "How do you ensure data consistency across multiple regions?"
- "How would you implement real-time data quality monitoring?"

### Business Considerations
- "How do you measure the ROI of data quality improvements?"
- "What's your strategy for handling data privacy regulations?"
- "How do you balance data freshness vs. processing cost?"
- "What's your plan for data archiving and lifecycle management?"

## Krishna's Interview Tips

### 1. Start with Business Context
- Understand the business use case and requirements
- Ask about data volume, velocity, and variety
- Clarify compliance and security requirements

### 2. Think in Layers
- Start with high-level architecture, then drill down
- Consider data flow, storage, processing, and serving layers
- Think about monitoring, security, and operational concerns

### 3. Use Real Examples
- Reference actual systems I've built at Walgreens
- Share specific metrics and performance improvements
- Discuss real challenges and how I solved them

### 4. Consider Trade-offs
- Always discuss trade-offs between different approaches
- Explain why I chose specific technologies or patterns
- Be honest about limitations and potential improvements

This system design approach has helped me successfully design and deploy data platforms that process petabytes of data while maintaining high reliability and performance.
