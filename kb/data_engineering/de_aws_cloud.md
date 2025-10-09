---
tags: [data-engineer, aws, s3, glue, redshift, athena, emr, lambda]
persona: de
---

# AWS Cloud for Data Engineering - Krishna's Experience

## Introduction
**Krishna's AWS Background:**
While my primary platform is Azure, I've worked with AWS data services on several projects. Here's what I know about building data pipelines on AWS.

## Amazon S3

### Data Lake Organization
**Krishna's S3 Structure:**
```
s3://walgreens-data-lake/

├── raw/                                # Landing zone
│   ├── salesforce/
│   │   └── 2024-01-15/
│   ├── database_extracts/
│   │   └── orders/2024-01-15/
│   └── api_data/
│
├── processed/                          # Cleaned data
│   ├── customers/
│   │   └── year=2024/month=01/day=15/
│   ├── orders/
│   └── products/
│
├── analytics/                          # Business-ready
│   ├── daily_sales/
│   ├── customer_metrics/
│   └── product_performance/
│
└── archive/                            # Historical data
    └── 2023/
```

### S3 Performance Optimization
**Krishna's Best Practices:**

**1. Partitioning Strategy:**
```python
# Write partitioned data
df.write \
    .partitionBy("year", "month", "day") \
    .mode("overwrite") \
    .parquet("s3://bucket/processed/orders/")

# Read specific partition (fast)
df = spark.read.parquet("s3://bucket/processed/orders/year=2024/month=01/")
```

**2. File Formats:**
```python
# Parquet (columnar, compressed) - BEST for analytics
df.write.mode("overwrite").parquet("s3://bucket/data.parquet")

# ORC (columnar) - Good for Hive/Spark
df.write.mode("overwrite").orc("s3://bucket/data.orc")

# CSV (human-readable) - Use only for raw data
df.write.mode("overwrite").csv("s3://bucket/data.csv")
```

**3. Lifecycle Policies:**
```json
{
  "Rules": [
    {
      "Id": "archive-old-raw-data",
      "Status": "Enabled",
      "Filter": {
        "Prefix": "raw/"
      },
      "Transitions": [
        {
          "Days": 90,
          "StorageClass": "STANDARD_IA"
        },
        {
          "Days": 365,
          "StorageClass": "GLACIER"
        }
      ]
    },
    {
      "Id": "delete-temp-data",
      "Status": "Enabled",
      "Filter": {
        "Prefix": "temp/"
      },
      "Expiration": {
        "Days": 7
      }
    }
  ]
}
```

## AWS Glue

### Glue ETL Jobs
**Krishna's Glue Job Pattern:**

```python
# Glue Job: transform_orders.py
import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql import functions as F

# Initialize
args = getResolvedOptions(sys.argv, ['JOB_NAME', 'execution_date'])
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

# Read from S3
df_raw = spark.read.parquet(f"s3://bucket/raw/orders/date={args['execution_date']}")

# Transform
df_clean = (
    df_raw
    .filter(F.col("order_status") == "completed")
    .withColumn("order_amount", F.col("order_amount").cast("decimal(18,2)"))
    .dropDuplicates(["order_id"])
    .withColumn("processed_at", F.current_timestamp())
)

# Write to processed
df_clean.write \
    .mode("overwrite") \
    .partitionBy("order_date") \
    .parquet(f"s3://bucket/processed/orders/")

job.commit()
```

### Glue Data Catalog
**Krishna's Catalog Management:**

```python
# Create Glue Crawler via boto3
import boto3

glue = boto3.client('glue')

response = glue.create_crawler(
    Name='orders-crawler',
    Role='AWSGlueServiceRole',
    DatabaseName='walgreens_data',
    Description='Crawl orders data',
    Targets={
        'S3Targets': [
            {
                'Path': 's3://bucket/processed/orders/',
                'Exclusions': ['*.tmp', '*.log']
            }
        ]
    },
    Schedule='cron(0 8 * * ? *)',  # Daily at 8 AM
    SchemaChangePolicy={
        'UpdateBehavior': 'UPDATE_IN_DATABASE',
        'DeleteBehavior': 'LOG'
    }
)
```

## Amazon Redshift

### Redshift Architecture
**Krishna's Redshift Setup:**

**1. Create Tables with Distribution:**
```sql
-- Fact table with KEY distribution
CREATE TABLE fct_orders (
    order_id VARCHAR(50) NOT NULL,
    customer_id VARCHAR(50) DISTKEY,    -- Distribute by join key
    order_date DATE SORTKEY,             -- Sort for date queries
    order_amount DECIMAL(18,2),
    product_id VARCHAR(50),
    created_at TIMESTAMP
);

-- Dimension with ALL distribution
CREATE TABLE dim_customer (
    customer_id VARCHAR(50) NOT NULL SORTKEY,
    customer_name VARCHAR(200),
    customer_segment VARCHAR(50),
    city VARCHAR(100),
    state VARCHAR(50)
)
DISTSTYLE ALL;  -- Replicate to all nodes
```

**2. Load Data from S3:**
```sql
-- COPY command (fastest way to load)
COPY fct_orders
FROM 's3://bucket/processed/orders/'
IAM_ROLE 'arn:aws:iam::123456789:role/RedshiftRole'
FORMAT AS PARQUET
COMPUPDATE ON
STATUPDATE ON;
```

**3. Unload Data to S3:**
```sql
-- Export query results to S3
UNLOAD (
    'SELECT * FROM fct_orders WHERE order_date >= \'2024-01-01\''
)
TO 's3://bucket/exports/orders_'
IAM_ROLE 'arn:aws:iam::123456789:role/RedshiftRole'
FORMAT AS PARQUET
PARALLEL ON
ALLOWOVERWRITE;
```

### Redshift Performance
**Krishna's Optimization:**

**1. Vacuum and Analyze:**
```sql
-- Reclaim space and resort
VACUUM fct_orders;

-- Update statistics for query planner
ANALYZE fct_orders;

-- Vacuum specific table with options
VACUUM DELETE ONLY fct_orders TO 75 PERCENT;
```

**2. Workload Management (WLM):**
```json
{
  "query_concurrency": 5,
  "query_group": [
    {
      "name": "etl",
      "query_group_wildcard": "etl_*",
      "memory_percent": 40,
      "query_concurrency": 2
    },
    {
      "name": "reporting",
      "query_group_wildcard": "report_*",
      "memory_percent": 40,
      "query_concurrency": 3
    }
  ]
}
```

## Amazon Athena

### Querying S3 with Athena
**Krishna's Athena Patterns:**

**1. Create External Tables:**
```sql
-- Create table on S3 data
CREATE EXTERNAL TABLE IF NOT EXISTS orders (
    order_id STRING,
    customer_id STRING,
    order_date DATE,
    order_amount DECIMAL(18,2),
    product_id STRING
)
PARTITIONED BY (year INT, month INT, day INT)
STORED AS PARQUET
LOCATION 's3://bucket/processed/orders/';

-- Add partitions
MSCK REPAIR TABLE orders;

-- Or add specific partition
ALTER TABLE orders ADD IF NOT EXISTS
PARTITION (year=2024, month=1, day=15)
LOCATION 's3://bucket/processed/orders/year=2024/month=01/day=15/';
```

**2. Query Optimization:**
```sql
-- BAD: Scans entire table
SELECT * FROM orders WHERE order_date = '2024-01-15';

-- GOOD: Uses partitions
SELECT * FROM orders 
WHERE year = 2024 AND month = 1 AND day = 15;

-- BETTER: Limit columns
SELECT order_id, customer_id, order_amount
FROM orders
WHERE year = 2024 AND month = 1 AND day = 15;
```

**3. CTAS for Performance:**
```sql
-- Create optimized table from query
CREATE TABLE orders_summary
WITH (
    format = 'PARQUET',
    parquet_compression = 'SNAPPY',
    partitioned_by = ARRAY['year', 'month']
) AS
SELECT
    year,
    month,
    customer_id,
    COUNT(*) as order_count,
    SUM(order_amount) as total_spent
FROM orders
GROUP BY year, month, customer_id;
```

## AWS Lambda for Data Pipelines

### Event-Driven Processing
**Krishna's Lambda Functions:**

```python
# Lambda: validate_new_file.py
import json
import boto3
import pandas as pd
from io import BytesIO

s3 = boto3.client('s3')
sns = boto3.client('sns')

def lambda_handler(event, context):
    """
    Triggered when new file lands in S3
    Validates data before processing
    """
    # Get file info from S3 event
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']
    
    print(f"Validating: s3://{bucket}/{key}")
    
    try:
        # Download and read file
        obj = s3.get_object(Bucket=bucket, Key=key)
        df = pd.read_csv(BytesIO(obj['Body'].read()))
        
        # Validation checks
        errors = []
        
        # Check required columns
        required_cols = ['order_id', 'customer_id', 'order_date', 'order_amount']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            errors.append(f"Missing columns: {missing_cols}")
        
        # Check for nulls
        null_counts = df[required_cols].isnull().sum()
        if null_counts.any():
            errors.append(f"Null values found: {null_counts.to_dict()}")
        
        # Check data types
        if not pd.api.types.is_numeric_dtype(df['order_amount']):
            errors.append("order_amount must be numeric")
        
        if errors:
            # Move to error folder
            error_key = key.replace('raw/', 'errors/')
            s3.copy_object(
                Bucket=bucket,
                CopySource={'Bucket': bucket, 'Key': key},
                Key=error_key
            )
            
            # Send alert
            sns.publish(
                TopicArn='arn:aws:sns:us-east-1:123456789:data-validation-alerts',
                Subject='Data Validation Failed',
                Message=f"File: {key}\nErrors: {errors}"
            )
            
            return {'statusCode': 400, 'body': json.dumps({'errors': errors})}
        
        else:
            # Move to validated folder
            validated_key = key.replace('raw/', 'validated/')
            s3.copy_object(
                Bucket=bucket,
                CopySource={'Bucket': bucket, 'Key': key},
                Key=validated_key
            )
            s3.delete_object(Bucket=bucket, Key=key)
            
            return {'statusCode': 200, 'body': json.dumps({'status': 'validated'})}
            
    except Exception as e:
        print(f"Error: {str(e)}")
        raise
```

## AWS Step Functions

### Orchestrating Data Pipelines
**Krishna's Step Functions Workflow:**

```json
{
  "Comment": "Daily ETL Pipeline",
  "StartAt": "ValidateFiles",
  "States": {
    "ValidateFiles": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:us-east-1:123456789:function:validate-files",
      "Next": "RunGlueJob"
    },
    "RunGlueJob": {
      "Type": "Task",
      "Resource": "arn:aws:states:::glue:startJobRun.sync",
      "Parameters": {
        "JobName": "transform-orders",
        "Arguments": {
          "--execution_date.$": "$.execution_date"
        }
      },
      "Next": "LoadToRedshift"
    },
    "LoadToRedshift": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:us-east-1:123456789:function:load-redshift",
      "Next": "RefreshViews"
    },
    "RefreshViews": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:us-east-1:123456789:function:refresh-views",
      "Next": "SendNotification",
      "Catch": [{
        "ErrorEquals": ["States.ALL"],
        "Next": "HandleError"
      }]
    },
    "SendNotification": {
      "Type": "Task",
      "Resource": "arn:aws:states:::sns:publish",
      "Parameters": {
        "TopicArn": "arn:aws:sns:us-east-1:123456789:pipeline-success",
        "Message": "Pipeline completed successfully"
      },
      "End": true
    },
    "HandleError": {
      "Type": "Task",
      "Resource": "arn:aws:states:::sns:publish",
      "Parameters": {
        "TopicArn": "arn:aws:sns:us-east-1:123456789:pipeline-failure",
        "Message.$": "$.Error"
      },
      "End": true
    }
  }
}
```

## Cost Optimization

**Krishna's AWS Cost Strategies:**

**1. S3 Storage Classes:**
- Standard: Frequently accessed data
- Intelligent-Tiering: Unknown access patterns (auto-optimize)
- Standard-IA: Infrequent access (30+ days)
- Glacier: Archive (90+ days)

**2. Glue Job Optimization:**
```python
# Use Glue job bookmarks (avoid reprocessing)
job.init(args['JOB_NAME'], args)
job.commit()

# Use Glue Flex for non-urgent jobs (50% cheaper)
glue.start_job_run(
    JobName='my-job',
    Arguments={
        '--job-bookmark-option': 'job-bookmark-enable',
        '--enable-glue-datacatalog': 'true'
    }
)
```

**3. Redshift Reserved Nodes:**
- 1-year commitment: 40% savings
- 3-year commitment: 65% savings

**4. Athena Query Optimization:**
```sql
-- Partition pruning saves money
-- BAD: Scans 1TB, costs $5
SELECT * FROM large_table WHERE date = '2024-01-15';

-- GOOD: Scans 10GB, costs $0.05
SELECT * FROM large_table 
WHERE year = 2024 AND month = 1 AND day = 15;
```

My AWS experience complements my Azure expertise, making me versatile across cloud platforms!

