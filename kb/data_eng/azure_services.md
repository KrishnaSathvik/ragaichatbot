---
tags: [azure, cloud, data-engineering, data-factory, databricks, synapse, storage, key-vault]
persona: de
---

# Azure Data Engineering Services & Krishna's Experience

## Core Azure Services for Data Engineering

### Azure Data Factory (ADF)
**Krishna's Primary Experience at Walgreens:**
- **Orchestration**: Orchestrated 50+ data pipelines processing 10TB+ monthly data
- **Data Movement**: Built copy activities for 200+ data sources
- **Transformation**: Implemented data flows for complex ETL operations
- **Monitoring**: Set up comprehensive monitoring with 99.5% SLA achievement

**ADF Pipeline Architecture:**
```json
{
  "name": "PharmacyDataPipeline",
  "properties": {
    "activities": [
      {
        "name": "CopyPharmacyData",
        "type": "Copy",
        "inputs": [
          {
            "referenceName": "PharmacySourceDataset",
            "type": "DatasetReference"
          }
        ],
        "outputs": [
          {
            "referenceName": "PharmacySinkDataset", 
            "type": "DatasetReference"
          }
        ],
        "typeProperties": {
          "source": {
            "type": "SqlSource",
            "sqlReaderQuery": "SELECT * FROM pharmacy_transactions WHERE updated_date >= '@{pipeline().parameters.WindowStart}'"
          },
          "sink": {
            "type": "ParquetSink",
            "storeSettings": {
              "type": "AzureBlobFSWriteSettings"
            }
          }
        }
      },
      {
        "name": "TransformData",
        "type": "ExecuteDataFlow",
        "dependsOn": [
          {
            "activity": "CopyPharmacyData",
            "dependencyConditions": ["Succeeded"]
          }
        ],
        "typeProperties": {
          "dataflow": {
            "referenceName": "PharmacyDataFlow",
            "type": "DataFlowReference"
          }
        }
      }
    ]
  }
}
```

### Azure Databricks
**Krishna's Advanced Implementation:**
- **Cluster Management**: Optimized cluster configurations reducing costs by 30%
- **Notebook Development**: Created 100+ notebooks for data processing
- **Delta Lake**: Implemented ACID transactions and time travel
- **Unity Catalog**: Set up data governance and lineage tracking

**Databricks Performance Optimization:**
```python
# Cluster optimization configuration
spark.conf.set("spark.sql.adaptive.enabled", "true")
spark.conf.set("spark.sql.adaptive.coalescePartitions.enabled", "true")
spark.conf.set("spark.sql.adaptive.skewJoin.enabled", "true")
spark.conf.set("spark.serializer", "org.apache.spark.serializer.KryoSerializer")

# Delta Lake optimization
from delta.tables import DeltaTable

# Optimize Delta table
delta_table = DeltaTable.forPath(spark, "/mnt/data/pharmacy_silver")
delta_table.optimize().executeCompaction()

# Z-order optimization for query performance
delta_table.optimize().executeZOrderBy("customer_id", "transaction_date")

# Vacuum old files
delta_table.vacuum(retentionHours=168)  # 7 days
```

### Azure Synapse Analytics
**Krishna's Data Warehouse Implementation:**
- **Dedicated SQL Pools**: Designed for high-performance analytics
- **Serverless SQL**: Used for ad-hoc queries and data exploration
- **Spark Pools**: Integrated with Databricks for big data processing
- **Data Integration**: Built comprehensive data integration pipelines

**Synapse SQL Optimization:**
```sql
-- Distribution strategy for large tables
CREATE TABLE fact_pharmacy_sales (
    sale_id BIGINT,
    customer_id BIGINT,
    product_id BIGINT,
    sale_date DATE,
    amount DECIMAL(10,2),
    store_id INT
)
WITH (
    DISTRIBUTION = HASH(customer_id),  -- Hash distribution for joins
    CLUSTERED COLUMNSTORE INDEX,
    PARTITION (sale_date RANGE RIGHT FOR VALUES 
        ('2023-01-01', '2023-02-01', '2023-03-01', '2023-04-01'))
);

-- Optimized query with proper statistics
UPDATE STATISTICS fact_pharmacy_sales;

-- Window function optimization
SELECT 
    customer_id,
    sale_date,
    amount,
    SUM(amount) OVER (
        PARTITION BY customer_id 
        ORDER BY sale_date 
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) as rolling_7day_sales,
    ROW_NUMBER() OVER (
        PARTITION BY customer_id 
        ORDER BY sale_date DESC
    ) as recency_rank
FROM fact_pharmacy_sales
WHERE sale_date >= '2023-01-01';
```

### Azure Storage
**Krishna's Data Lake Implementation:**
- **Blob Storage**: Primary data lake storage for 10TB+ data
- **Data Lake Gen2**: Hierarchical namespace for better performance
- **Lifecycle Management**: Automated tiering reducing costs by 25%
- **Security**: Implemented RBAC and encryption at rest

**Storage Architecture:**
```
Data Lake Structure:
├── bronze/                    # Raw data ingestion
│   ├── pharmacy/
│   │   ├── year=2023/
│   │   │   ├── month=01/
│   │   │   └── month=02/
│   │   └── year=2024/
│   ├── supply_chain/
│   └── customer/
├── silver/                    # Cleaned and validated data
│   ├── pharmacy/
│   ├── supply_chain/
│   └── customer/
└── gold/                      # Business-ready aggregated data
    ├── analytics/
    ├── reporting/
    └── ml_features/
```

### Azure Key Vault
**Krishna's Security Implementation:**
- **Secret Management**: Stored database credentials and API keys
- **Certificate Management**: Managed SSL certificates for applications
- **Access Policies**: Implemented least privilege access
- **Integration**: Connected with ADF, Databricks, and Synapse

**Key Vault Integration:**
```python
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential

# Initialize Key Vault client
credential = DefaultAzureCredential()
client = SecretClient(vault_url="https://walgreens-kv.vault.azure.net/", credential=credential)

# Retrieve secrets in Databricks
database_password = client.get_secret("database-password").value
api_key = client.get_secret("external-api-key").value

# Use in data processing
spark.conf.set("fs.azure.account.key.walgreensdatalake.dfs.core.windows.net", 
               client.get_secret("storage-account-key").value)
```

## Advanced Azure Patterns

### Medallion Architecture Implementation
**Krishna's Bronze-Silver-Gold Pattern:**

```python
# Bronze Layer - Raw data ingestion
def ingest_bronze_data(source_path, target_path):
    df = spark.read.format("json").load(source_path)
    df.write \
        .format("delta") \
        .mode("append") \
        .option("mergeSchema", "true") \
        .partitionBy("year", "month", "day") \
        .save(target_path)

# Silver Layer - Cleaned and validated data
def process_silver_data(bronze_path, silver_path):
    df = spark.read.format("delta").load(bronze_path)
    
    # Data quality checks
    cleaned_df = df.filter(col("customer_id").isNotNull()) \
        .filter(col("amount") > 0) \
        .withColumn("processed_timestamp", current_timestamp()) \
        .withColumn("data_quality_score", 
                   when(col("amount") > 1000, "high_quality")
                   .otherwise("standard_quality"))
    
    cleaned_df.write \
        .format("delta") \
        .mode("overwrite") \
        .option("overwriteSchema", "true") \
        .partitionBy("year", "month") \
        .save(silver_path)

# Gold Layer - Business-ready aggregated data
def create_gold_aggregates(silver_path, gold_path):
    df = spark.read.format("delta").load(silver_path)
    
    # Business aggregations
    gold_df = df.groupBy("customer_id", "year", "month") \
        .agg(
            sum("amount").alias("total_spent"),
            count("*").alias("transaction_count"),
            avg("amount").alias("avg_transaction_value"),
            max("transaction_date").alias("last_transaction_date")
        ) \
        .withColumn("customer_segment",
                   when(col("total_spent") > 1000, "premium")
                   .when(col("total_spent") > 500, "standard")
                   .otherwise("basic"))
    
    gold_df.write \
        .format("delta") \
        .mode("overwrite") \
        .partitionBy("year", "month") \
        .save(gold_path)
```

### Data Factory Monitoring & Alerting
**Krishna's Comprehensive Monitoring:**

```json
{
  "name": "PipelineMonitoring",
  "properties": {
    "activities": [
      {
        "name": "CheckPipelineHealth",
        "type": "WebActivity",
        "typeProperties": {
          "url": "https://management.azure.com/subscriptions/{subscription-id}/resourceGroups/{rg}/providers/Microsoft.DataFactory/factories/{factory}/pipelineruns?api-version=2018-06-01",
          "method": "GET",
          "headers": {
            "Authorization": "@{concat('Bearer ', activity('GetAccessToken').output.access_token)}"
          }
        }
      },
      {
        "name": "SendAlert",
        "type": "WebActivity",
        "dependsOn": [
          {
            "activity": "CheckPipelineHealth",
            "dependencyConditions": ["Failed"]
          }
        ],
        "typeProperties": {
          "url": "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK",
          "method": "POST",
          "body": {
            "text": "Pipeline failed: @{activity('CheckPipelineHealth').output.value[0].pipelineName}"
          }
        }
      }
    ]
  }
}
```

## Performance Optimization

### Krishna's Optimization Achievements:
1. **Query Performance**: Reduced average query time from 45 seconds to 8 seconds
2. **Cost Reduction**: 30% reduction through cluster optimization
3. **Data Processing**: 2+ hour jobs reduced to 40 minutes
4. **Storage Costs**: 25% reduction through lifecycle management

### Optimization Techniques Applied:

**Databricks Optimization:**
```python
# Adaptive Query Execution
spark.conf.set("spark.sql.adaptive.enabled", "true")
spark.conf.set("spark.sql.adaptive.coalescePartitions.enabled", "true")
spark.conf.set("spark.sql.adaptive.skewJoin.enabled", "true")

# Memory optimization
spark.conf.set("spark.sql.adaptive.advisoryPartitionSizeInBytes", "128MB")
spark.conf.set("spark.sql.adaptive.skewJoin.skewedPartitionFactor", "5")

# Broadcast join optimization
spark.conf.set("spark.sql.autoBroadcastJoinThreshold", "50MB")
```

**Synapse Optimization:**
```sql
-- Table statistics for query optimization
CREATE STATISTICS customer_stats ON fact_pharmacy_sales(customer_id);
CREATE STATISTICS date_stats ON fact_pharmacy_sales(sale_date);

-- Index optimization
CREATE CLUSTERED COLUMNSTORE INDEX CCI_fact_pharmacy_sales 
ON fact_pharmacy_sales;

-- Query hints for performance
SELECT /*+ USE_HINT('ENABLE_PARALLEL_PLAN_PREFERENCE') */
    customer_id,
    SUM(amount) as total_spent
FROM fact_pharmacy_sales
WHERE sale_date >= '2023-01-01'
GROUP BY customer_id;
```

## Security & Compliance

### Security Implementation:
- **Azure AD Integration**: Single sign-on for all services
- **RBAC**: Role-based access control for data access
- **Encryption**: At rest and in transit encryption
- **Network Security**: VNet integration and private endpoints
- **Audit Logging**: Comprehensive logging with Azure Monitor

### Compliance (HIPAA for Healthcare):
```python
# PII masking in Databricks
from pyspark.sql.functions import regexp_replace, when

def mask_pii(df):
    return df.withColumn("email", 
                        regexp_replace(col("email"), 
                                     r"(\w{2})\w*@(\w{2})\w*\.(\w{2})", 
                                     "$1***@$2***.$3")) \
             .withColumn("phone", 
                        regexp_replace(col("phone"), 
                                     r"(\d{3})\d{3}(\d{4})", 
                                     "$1***$2")) \
             .withColumn("ssn", 
                        regexp_replace(col("ssn"), 
                                     r"(\d{3})\d{2}(\d{4})", 
                                     "$1**$2"))
```

## Cost Management

### Cost Optimization Strategies:
1. **Auto-scaling**: Implemented for variable workloads
2. **Reserved Capacity**: Purchased for predictable workloads
3. **Spot Instances**: Used for non-critical processing
4. **Data Lifecycle**: Automated archival and deletion
5. **Query Optimization**: Reduced compute requirements

### Cost Monitoring:
```python
# Cost tracking in Databricks
import requests
from datetime import datetime, timedelta

def get_databricks_cost():
    headers = {
        "Authorization": f"Bearer {dbutils.secrets.get('keyvault', 'databricks-token')}"
    }
    
    # Get cluster usage
    response = requests.get(
        "https://{workspace}.azuredatabricks.net/api/2.0/clusters/list",
        headers=headers
    )
    
    # Calculate costs based on usage
    total_cost = 0
    for cluster in response.json().get('clusters', []):
        if cluster['state'] == 'RUNNING':
            # Calculate cost based on node type and runtime
            cost = calculate_cluster_cost(cluster)
            total_cost += cost
    
    return total_cost
```

## Interview Talking Points

### Technical Achievements:
- "Orchestrated 50+ data pipelines with 99.5% SLA using Azure Data Factory"
- "Reduced data processing costs by 30% through Databricks optimization"
- "Implemented medallion architecture processing 10TB+ monthly data"
- "Achieved 8-second average query time in Synapse Analytics"

### Problem-Solving Examples:
- **Data Skew**: Used Delta Lake Z-ordering and adaptive query execution
- **Cost Optimization**: Implemented auto-scaling and spot instances
- **Performance**: Optimized queries with proper distribution and statistics
- **Security**: Enhanced compliance with automated PII masking

### Tools & Technologies:
- **Azure Services**: Data Factory, Databricks, Synapse, Storage, Key Vault
- **Languages**: Python, SQL, PySpark, Scala
- **Data Formats**: Delta Lake, Parquet, JSON
- **Monitoring**: Azure Monitor, Log Analytics, Application Insights
