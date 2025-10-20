---
tags: [data-engineer, aws, s3, glue, redshift, athena, emr, lambda, tejuu]
persona: analytics
---

# AWS Cloud for Data Engineering - Tejuu's Experience

## Introduction
**Tejuu's AWS Background:**
While my primary platform is Azure, I've worked with AWS data services on several projects, especially during my time at Stryker and CVS Health. Here's what I know about building data platforms on AWS, with a focus on analytics and business intelligence.

## Amazon S3

### Data Lake Organization
**Tejuu's S3 Structure:**
```
s3://centralbank-data-lake/

├── raw/                                # Landing zone
│   ├── legacy_excel/
│   │   └── 2024-01-15/
│   ├── access_databases/
│   │   └── customers/2024-01-15/
│   └── api_data/
│       └── banking_api/2024-01-15/
│
├── processed/                          # Cleaned data
│   ├── customers/
│   │   └── year=2024/month=01/day=15/
│   ├── transactions/
│   └── accounts/
│
├── analytics/                          # Business-ready
│   ├── customer_360/
│   ├── risk_metrics/
│   └── regulatory_reports/
│
└── archive/                            # Historical data
    └── 2023/
```

### S3 Performance Optimization
**Tejuu's Best Practices:**

**1. Partitioning Strategy:**
```python
# Write partitioned data for analytics
df.write \
    .partitionBy("year", "month", "day") \
    .mode("overwrite") \
    .parquet("s3://bucket/processed/transactions/")

# Read specific partition (fast)
df = spark.read.parquet("s3://bucket/processed/transactions/year=2024/month=01/")
```

**2. File Formats for Analytics:**
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
      "Id": "archive-legacy-data",
      "Status": "Enabled",
      "Filter": {
        "Prefix": "raw/legacy_excel/"
      },
      "Transitions": [
        {
          "Days": 30,
          "StorageClass": "STANDARD_IA"
        },
        {
          "Days": 90,
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
**Tejuu's Glue Job Pattern:**

```python
# Glue Job: migrate_legacy_data.py
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
df_raw = spark.read.parquet(f"s3://bucket/raw/legacy_data/date={args['execution_date']}")

# Data validation and cleansing
df_clean = (
    df_raw
    .filter(F.col("customer_id").isNotNull())
    .filter(F.col("amount") > 0)
    .withColumn("amount", F.col("amount").cast("decimal(18,2)"))
    .dropDuplicates(["transaction_id"])
    .withColumn("processed_at", F.current_timestamp())
)

# Data quality checks
row_count = df_clean.count()
if row_count == 0:
    raise Exception("No data processed - validation failed")

# Write to processed
df_clean.write \
    .mode("overwrite") \
    .partitionBy("transaction_date") \
    .parquet(f"s3://bucket/processed/transactions/")

print(f"✅ Processed {row_count:,} transactions")
job.commit()
```

### Glue Data Catalog
**Tejuu's Catalog Management:**

```python
# Create Glue Crawler via boto3
import boto3

glue = boto3.client('glue')

response = glue.create_crawler(
    Name='banking-data-crawler',
    Role='AWSGlueServiceRole',
    DatabaseName='centralbank_data',
    Description='Crawl banking data',
    Targets={
        'S3Targets': [
            {
                'Path': 's3://bucket/processed/transactions/',
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
**Tejuu's Redshift Setup:**

**1. Create Tables with Distribution:**
```sql
-- Fact table with KEY distribution
CREATE TABLE fct_customer_transactions (
    transaction_id VARCHAR(50) NOT NULL,
    customer_id VARCHAR(50) DISTKEY,    -- Distribute by join key
    transaction_date DATE SORTKEY,      -- Sort for date queries
    amount DECIMAL(18,2),
    transaction_type VARCHAR(50),
    branch_id VARCHAR(20),
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
COPY fct_customer_transactions
FROM 's3://bucket/processed/transactions/'
IAM_ROLE 'arn:aws:iam::123456789:role/RedshiftRole'
FORMAT AS PARQUET
COMPUPDATE ON
STATUPDATE ON;
```

**3. Unload Data to S3:**
```sql
-- Export query results to S3
UNLOAD (
    'SELECT * FROM fct_customer_transactions WHERE transaction_date >= ''2024-01-01'''
)
TO 's3://bucket/exports/transactions_'
IAM_ROLE 'arn:aws:iam::123456789:role/RedshiftRole'
FORMAT AS PARQUET
PARALLEL ON
ALLOWOVERWRITE;
```

### Redshift Performance
**Tejuu's Optimization:**

**1. Vacuum and Analyze:**
```sql
-- Reclaim space and resort
VACUUM fct_customer_transactions;

-- Update statistics for query planner
ANALYZE fct_customer_transactions;

-- Vacuum specific table with options
VACUUM DELETE ONLY fct_customer_transactions TO 75 PERCENT;
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
**Tejuu's Athena Patterns:**

**1. Create External Tables:**
```sql
-- Create table on S3 data
CREATE EXTERNAL TABLE IF NOT EXISTS customer_transactions (
    transaction_id STRING,
    customer_id STRING,
    transaction_date DATE,
    amount DECIMAL(18,2),
    transaction_type STRING
)
PARTITIONED BY (year INT, month INT, day INT)
STORED AS PARQUET
LOCATION 's3://bucket/processed/transactions/';

-- Add partitions
MSCK REPAIR TABLE customer_transactions;

-- Or add specific partition
ALTER TABLE customer_transactions ADD IF NOT EXISTS
PARTITION (year=2024, month=1, day=15)
LOCATION 's3://bucket/processed/transactions/year=2024/month=01/day=15/';
```

**2. Query Optimization:**
```sql
-- BAD: Scans entire table
SELECT * FROM customer_transactions WHERE transaction_date = '2024-01-15';

-- GOOD: Uses partitions
SELECT * FROM customer_transactions 
WHERE year = 2024 AND month = 1 AND day = 15;

-- BETTER: Limit columns
SELECT transaction_id, customer_id, amount
FROM customer_transactions
WHERE year = 2024 AND month = 1 AND day = 15;
```

**3. CTAS for Performance:**
```sql
-- Create optimized table from query
CREATE TABLE customer_summary
WITH (
    format = 'PARQUET',
    parquet_compression = 'SNAPPY',
    partitioned_by = ARRAY['year', 'month']
) AS
SELECT
    year,
    month,
    customer_id,
    COUNT(*) as transaction_count,
    SUM(amount) as total_amount
FROM customer_transactions
GROUP BY year, month, customer_id;
```

## AWS Lambda for Data Pipelines

### Event-Driven Processing
**Tejuu's Lambda Functions:**

```python
# Lambda: validate_banking_data.py
import json
import boto3
import pandas as pd
from io import BytesIO

s3 = boto3.client('s3')
sns = boto3.client('sns')

def lambda_handler(event, context):
    """
    Triggered when new file lands in S3
    Validates banking data before processing
    """
    # Get file info from S3 event
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']
    
    print(f"Validating: s3://{bucket}/{key}")
    
    try:
        # Download and read file
        obj = s3.get_object(Bucket=bucket, Key=key)
        df = pd.read_csv(BytesIO(obj['Body'].read()))
        
        # Banking data validation checks
        errors = []
        
        # Check required columns
        required_cols = ['transaction_id', 'customer_id', 'amount', 'transaction_date']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            errors.append(f"Missing columns: {missing_cols}")
        
        # Check for nulls in critical fields
        null_counts = df[required_cols].isnull().sum()
        if null_counts.any():
            errors.append(f"Null values found: {null_counts.to_dict()}")
        
        # Check amount is positive
        if 'amount' in df.columns:
            negative_amounts = df[df['amount'] <= 0].shape[0]
            if negative_amounts > 0:
                errors.append(f"Found {negative_amounts} transactions with non-positive amounts")
        
        # Check transaction date format
        if 'transaction_date' in df.columns:
            try:
                pd.to_datetime(df['transaction_date'])
            except:
                errors.append("Invalid transaction_date format")
        
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
                Subject='Banking Data Validation Failed',
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
**Tejuu's Step Functions Workflow:**

```json
{
  "Comment": "Banking Data ETL Pipeline",
  "StartAt": "ValidateFiles",
  "States": {
    "ValidateFiles": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:us-east-1:123456789:function:validate-banking-data",
      "Next": "RunGlueJob"
    },
    "RunGlueJob": {
      "Type": "Task",
      "Resource": "arn:aws:states:::glue:startJobRun.sync",
      "Parameters": {
        "JobName": "migrate-legacy-data",
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
        "Message": "Banking data pipeline completed successfully"
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

**Tejuu's AWS Cost Strategies:**

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

My AWS experience complements my Azure expertise, making me versatile across cloud platforms for data engineering and analytics!
