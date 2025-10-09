---
tags: [analytics-engineer, aws, redshift, glue, s3, lambda, athena]
persona: ae
---

# AWS Cloud for Analytics Engineers - Tejuu's Experience

## Introduction
**Tejuu's AWS Background:**
I've worked with AWS data services on several projects, building scalable analytics solutions using Redshift, Glue, S3, and Athena. My focus is always on creating business-friendly data models that stakeholders can trust.

## Amazon Redshift

**Tejuu's Redshift Architecture:**
Redshift is our data warehouse where business users run analytics queries. I design and maintain the serving layer.

**Creating Analytics Tables:**
```sql
-- Fact table with distribution and sort keys

CREATE TABLE analytics.fct_orders
(
    order_id VARCHAR(50) NOT NULL,
    order_date DATE NOT NULL SORTKEY,  -- Frequent filter column
    customer_id VARCHAR(50) NOT NULL DISTKEY,  -- Join column
    product_id VARCHAR(50) NOT NULL,
    
    order_amount DECIMAL(18,2),
    quantity INTEGER,
    discount_amount DECIMAL(18,2),
    tax_amount DECIMAL(18,2),
    net_amount DECIMAL(18,2),
    
    created_at TIMESTAMP,
    updated_at TIMESTAMP
)
DISTSTYLE KEY;

-- Dimension table with ALL distribution

CREATE TABLE analytics.dim_customer
(
    customer_id VARCHAR(50) NOT NULL SORTKEY,
    customer_name VARCHAR(200),
    customer_email VARCHAR(200),
    customer_segment VARCHAR(50),
    customer_tier VARCHAR(20),
    
    -- Address
    street VARCHAR(200),
    city VARCHAR(100),
    state VARCHAR(50),
    zip_code VARCHAR(20),
    country VARCHAR(50),
    
    -- SCD Type 2
    effective_date DATE,
    expiration_date DATE,
    is_current BOOLEAN,
    
    created_at TIMESTAMP,
    updated_at TIMESTAMP
)
DISTSTYLE ALL;  -- Small table replicated to all nodes
```

**Business Scenario:**
Marketing wanted customer lifetime value by segment. This star schema made it simple:

```sql
-- Customer LTV by Segment - runs in 3 seconds

SELECT
    c.customer_segment,
    COUNT(DISTINCT c.customer_id) AS customer_count,
    SUM(f.net_amount) AS total_revenue,
    AVG(f.net_amount) AS avg_order_value,
    SUM(f.net_amount) / NULLIF(COUNT(DISTINCT c.customer_id), 0) AS ltv_per_customer
FROM analytics.fct_orders f
JOIN analytics.dim_customer c 
    ON f.customer_id = c.customer_id 
    AND c.is_current = TRUE
WHERE f.order_date >= DATEADD(year, -2, CURRENT_DATE)
GROUP BY c.customer_segment
ORDER BY ltv_per_customer DESC;
```

**Incremental Load Pattern:**
```sql
-- Upsert pattern using staging table

BEGIN TRANSACTION;

-- Step 1: Delete updated records from target
DELETE FROM analytics.fct_orders
USING staging.stg_orders_incremental
WHERE analytics.fct_orders.order_id = staging.stg_orders_incremental.order_id;

-- Step 2: Insert all records from staging
INSERT INTO analytics.fct_orders
SELECT * FROM staging.stg_orders_incremental;

-- Step 3: Commit
END TRANSACTION;

-- Vacuum to reclaim space
VACUUM analytics.fct_orders;

-- Analyze for query optimizer
ANALYZE analytics.fct_orders;
```

**Redshift Materialized Views:**
```sql
-- Create materialized view for common aggregation

CREATE MATERIALIZED VIEW analytics.mv_daily_revenue_summary
SORTKEY(order_date)
AS
SELECT
    d.order_date,
    d.year,
    d.quarter,
    d.month,
    c.customer_segment,
    p.product_category,
    
    COUNT(DISTINCT f.order_id) AS order_count,
    COUNT(DISTINCT f.customer_id) AS unique_customers,
    SUM(f.order_amount) AS gross_revenue,
    SUM(f.discount_amount) AS total_discounts,
    SUM(f.net_amount) AS net_revenue,
    AVG(f.net_amount) AS avg_order_value
FROM analytics.fct_orders f
JOIN analytics.dim_date d ON f.order_date = d.order_date
JOIN analytics.dim_customer c ON f.customer_id = c.customer_id AND c.is_current = TRUE
JOIN analytics.dim_product p ON f.product_id = p.product_id
GROUP BY 1, 2, 3, 4, 5, 6;

-- Refresh materialized view (scheduled daily)
REFRESH MATERIALIZED VIEW analytics.mv_daily_revenue_summary;
```

**Business Value:**
CFO's daily revenue dashboard loads in 2 seconds instead of 45 seconds!

## AWS Glue

**Tejuu's Glue ETL Jobs:**
I use Glue for data ingestion and transformation before loading into Redshift.

**PySpark Job for Data Transformation:**
```python
# Glue Job: transform_customer_data.py

import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql import functions as F
from pyspark.sql.window import Window

args = getResolvedOptions(sys.argv, ['JOB_NAME', 'execution_date'])
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

# Read source data from S3
df_customers = spark.read.parquet("s3://my-bucket/raw/customers/")

# Transform data
df_transformed = (
    df_customers
    
    # Clean and standardize
    .withColumn("email", F.lower(F.trim(F.col("email"))))
    .withColumn("customer_name", F.trim(F.col("customer_name")))
    .withColumn("phone", F.regexp_replace("phone", "[^0-9]", ""))
    
    # Derive columns
    .withColumn("full_address", 
        F.concat_ws(", ", "street", "city", "state", "zip_code"))
    
    # Calculate customer tenure
    .withColumn("customer_tenure_days",
        F.datediff(F.current_date(), "registration_date"))
    
    # Assign customer segment based on business rules
    .withColumn("customer_segment",
        F.when(F.col("lifetime_value") > 10000, "Platinum")
         .when(F.col("lifetime_value") > 5000, "Gold")
         .when(F.col("lifetime_value") > 1000, "Silver")
         .otherwise("Bronze"))
    
    # Handle SCD Type 2
    .withColumn("effective_date", F.col("updated_date"))
    .withColumn("expiration_date", F.lit("2099-12-31").cast("date"))
    .withColumn("is_current", F.lit(True))
)

# Remove duplicates - keep latest record
window = Window.partitionBy("customer_id").orderBy(F.desc("updated_date"))
df_deduped = (
    df_transformed
    .withColumn("row_num", F.row_number().over(window))
    .filter(F.col("row_num") == 1)
    .drop("row_num")
)

# Write to S3 in staging area
(
    df_deduped.write
    .mode("overwrite")
    .partitionBy("effective_date")
    .parquet("s3://my-bucket/staging/customers/")
)

# Load into Redshift
glueContext.write_dynamic_frame.from_options(
    frame=DynamicFrame.fromDF(df_deduped, glueContext, "df_deduped"),
    connection_type="redshift",
    connection_options={
        "url": "jdbc:redshift://my-cluster.redshift.amazonaws.com:5439/analytics",
        "dbtable": "staging.stg_customers",
        "user": "admin",
        "password": "{{resolve:secretsmanager:redshift-password}}",
        "redshiftTmpDir": "s3://my-bucket/temp/"
    }
)

job.commit()
```

**Glue Crawler for Schema Discovery:**
```python
# Create Glue Crawler using boto3

import boto3

glue = boto3.client('glue')

response = glue.create_crawler(
    Name='crawler-raw-data',
    Role='AWSGlueServiceRole',
    DatabaseName='raw_data_catalog',
    Description='Discover schema for raw data files',
    Targets={
        'S3Targets': [
            {
                'Path': 's3://my-bucket/raw/salesforce/',
                'Exclusions': ['*.tmp', '*.log']
            },
            {
                'Path': 's3://my-bucket/raw/google_analytics/'
            }
        ]
    },
    Schedule='cron(0 8 * * ? *)',  # Daily at 8 AM
    SchemaChangePolicy={
        'UpdateBehavior': 'UPDATE_IN_DATABASE',
        'DeleteBehavior': 'DEPRECATE_IN_DATABASE'
    },
    RecrawlPolicy={
        'RecrawlBehavior': 'CRAWL_NEW_FOLDERS_ONLY'
    }
)
```

**Business Impact:**
Automated schema discovery saves 5 hours/week of manual catalog updates!

## Amazon S3

**Tejuu's S3 Data Lake Structure:**
```
s3://my-analytics-bucket/

├── raw/                          # Landing zone
│   ├── salesforce/
│   │   └── 2024-01-15/
│   │       └── opportunities.json
│   ├── database_extracts/
│   │   └── 2024-01-15/
│   │       └── orders.csv
│   └── api_data/
│       └── 2024-01-15/
│           └── marketing_campaigns.json
│
├── staging/                      # Cleaned & transformed
│   ├── customers/
│   │   └── effective_date=2024-01-15/
│   ├── orders/
│   │   └── order_date=2024-01-15/
│   └── products/
│
├── analytics/                    # Business logic
│   ├── fct_sales/
│   ├── fct_campaigns/
│   ├── dim_customer/
│   └── dim_product/
│
└── logs/                         # Pipeline logs
    └── glue_jobs/
        └── 2024-01-15/
```

**S3 Lifecycle Policies:**
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
          "StorageClass": "INTELLIGENT_TIERING"
        },
        {
          "Days": 365,
          "StorageClass": "GLACIER"
        }
      ]
    },
    {
      "Id": "delete-staging-data",
      "Status": "Enabled",
      "Filter": {
        "Prefix": "staging/"
      },
      "Expiration": {
        "Days": 30
      }
    }
  ]
}
```

**Business Value:**
Reduced S3 storage costs by 40% with lifecycle policies!

## AWS Lambda

**Tejuu's Lambda Use Cases:**
I use Lambda for lightweight data processing and pipeline orchestration.

**Lambda Function for Data Validation:**
```python
# lambda_validate_data.py

import json
import boto3
import pandas as pd
from datetime import datetime

s3 = boto3.client('s3')
sns = boto3.client('sns')

def lambda_handler(event, context):
    """
    Validate incoming data files before processing
    """
    
    # Get file info from S3 event
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']
    
    print(f"Validating file: s3://{bucket}/{key}")
    
    # Read file
    obj = s3.get_object(Bucket=bucket, Key=key)
    df = pd.read_csv(obj['Body'])
    
    # Validation rules
    errors = []
    
    # 1. Check required columns
    required_cols = ['order_id', 'customer_id', 'order_date', 'order_amount']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        errors.append(f"Missing required columns: {missing_cols}")
    
    # 2. Check for nulls in key columns
    null_counts = df[required_cols].isnull().sum()
    if null_counts.any():
        errors.append(f"Null values found: {null_counts[null_counts > 0].to_dict()}")
    
    # 3. Check date format
    try:
        pd.to_datetime(df['order_date'])
    except:
        errors.append("Invalid date format in order_date column")
    
    # 4. Check numeric columns
    if df['order_amount'].dtype not in ['int64', 'float64']:
        errors.append("order_amount must be numeric")
    
    # 5. Check for duplicates
    dup_count = df['order_id'].duplicated().sum()
    if dup_count > 0:
        errors.append(f"Found {dup_count} duplicate order_ids")
    
    # Send results
    if errors:
        # Validation failed - send alert
        message = f"""
        ❌ Data validation FAILED
        
        File: s3://{bucket}/{key}
        Timestamp: {datetime.now()}
        
        Errors:
        {chr(10).join(errors)}
        """
        
        sns.publish(
            TopicArn='arn:aws:sns:us-east-1:123456789:data-validation-alerts',
            Subject='Data Validation Failed',
            Message=message
        )
        
        # Move file to error folder
        error_key = key.replace('raw/', 'errors/')
        s3.copy_object(
            Bucket=bucket,
            CopySource={'Bucket': bucket, 'Key': key},
            Key=error_key
        )
        s3.delete_object(Bucket=bucket, Key=key)
        
        return {'statusCode': 400, 'body': json.dumps(errors)}
    
    else:
        # Validation passed
        print(f"✅ Validation passed for {key}")
        
        # Move file to validated folder
        validated_key = key.replace('raw/', 'validated/')
        s3.copy_object(
            Bucket=bucket,
            CopySource={'Bucket': bucket, 'Key': key},
            Key=validated_key
        )
        s3.delete_object(Bucket=bucket, Key=key)
        
        return {'statusCode': 200, 'body': 'Validation successful'}
```

**Business Impact:**
Catches data quality issues before they hit production. Saves 10+ hours/month of firefighting!

## Amazon Athena

**Tejuu's Athena Queries:**
I use Athena for ad-hoc analysis on S3 data lake.

**Create External Table:**
```sql
-- Create external table on S3 data

CREATE EXTERNAL TABLE IF NOT EXISTS raw.orders (
    order_id STRING,
    customer_id STRING,
    order_date DATE,
    order_amount DECIMAL(18,2),
    product_id STRING,
    quantity INT,
    status STRING
)
PARTITIONED BY (order_year INT, order_month INT)
ROW FORMAT SERDE 'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe'
STORED AS PARQUET
LOCATION 's3://my-bucket/raw/orders/'
TBLPROPERTIES ('parquet.compression'='SNAPPY');

-- Add partitions
MSCK REPAIR TABLE raw.orders;
```

**Complex Analytics Query:**
```sql
-- Customer cohort analysis

WITH first_purchase AS (
    SELECT
        customer_id,
        MIN(order_date) AS cohort_date,
        DATE_FORMAT(MIN(order_date), '%Y-%m') AS cohort_month
    FROM raw.orders
    WHERE status = 'completed'
    GROUP BY customer_id
),

monthly_orders AS (
    SELECT
        o.customer_id,
        f.cohort_month,
        DATE_FORMAT(o.order_date, '%Y-%m') AS order_month,
        SUM(o.order_amount) AS revenue
    FROM raw.orders o
    JOIN first_purchase f ON o.customer_id = f.customer_id
    WHERE o.status = 'completed'
    GROUP BY 1, 2, 3
),

cohort_size AS (
    SELECT
        cohort_month,
        COUNT(DISTINCT customer_id) AS cohort_size
    FROM first_purchase
    GROUP BY cohort_month
)

SELECT
    m.cohort_month,
    m.order_month,
    DATE_DIFF('month', 
        DATE_PARSE(m.cohort_month, '%Y-%m'),
        DATE_PARSE(m.order_month, '%Y-%m')
    ) AS months_since_first_purchase,
    COUNT(DISTINCT m.customer_id) AS active_customers,
    c.cohort_size,
    CAST(COUNT(DISTINCT m.customer_id) AS DOUBLE) / c.cohort_size AS retention_rate,
    SUM(m.revenue) AS total_revenue,
    SUM(m.revenue) / COUNT(DISTINCT m.customer_id) AS revenue_per_customer
FROM monthly_orders m
JOIN cohort_size c ON m.cohort_month = c.cohort_month
GROUP BY 1, 2, c.cohort_size
ORDER BY 1, 2;
```

**Business Use:**
Marketing uses this cohort analysis to measure retention and optimize customer lifecycle campaigns.

## AWS Step Functions

**Tejuu's ETL Orchestration:**
```json
{
  "Comment": "Daily Analytics Refresh Pipeline",
  "StartAt": "Validate Source Data",
  "States": {
    "Validate Source Data": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:us-east-1:123456789:function:validate-data",
      "Next": "Run Glue ETL Job"
    },
    "Run Glue ETL Job": {
      "Type": "Task",
      "Resource": "arn:aws:states:::glue:startJobRun.sync",
      "Parameters": {
        "JobName": "transform-customer-data",
        "Arguments": {
          "--execution_date.$": "$.execution_date"
        }
      },
      "Next": "Load to Redshift"
    },
    "Load to Redshift": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:us-east-1:123456789:function:load-redshift",
      "Next": "Run dbt Transformations"
    },
    "Run dbt Transformations": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:us-east-1:123456789:function:run-dbt",
      "Parameters": {
        "dbt_command": "dbt run --select tag:daily"
      },
      "Next": "Refresh Materialized Views"
    },
    "Refresh Materialized Views": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:us-east-1:123456789:function:refresh-mv",
      "Next": "Send Success Notification",
      "Catch": [{
        "ErrorEquals": ["States.ALL"],
        "Next": "Send Failure Notification"
      }]
    },
    "Send Success Notification": {
      "Type": "Task",
      "Resource": "arn:aws:states:::sns:publish",
      "Parameters": {
        "TopicArn": "arn:aws:sns:us-east-1:123456789:analytics-success",
        "Message": "✅ Daily analytics refresh completed successfully"
      },
      "End": true
    },
    "Send Failure Notification": {
      "Type": "Task",
      "Resource": "arn:aws:states:::sns:publish",
      "Parameters": {
        "TopicArn": "arn:aws:sns:us-east-1:123456789:analytics-failure",
        "Message.$": "$.Error"
      },
      "End": true
    }
  }
}
```

## Cost Optimization

**Tejuu's AWS Cost Strategies:**

**1. Redshift Reserved Capacity:**
- Committed to 1-year reserved instances
- Saved 40% on compute costs

**2. S3 Intelligent Tiering:**
- Automatically moves infrequently accessed data to cheaper tiers
- Reduced S3 costs by 30%

**3. Athena Query Optimization:**
```sql
-- Partition pruning saves money

-- BAD: Scans entire table ($$$)
SELECT *
FROM raw.orders
WHERE order_date = '2024-01-15';

-- GOOD: Uses partitions ($$)
SELECT *
FROM raw.orders
WHERE order_year = 2024
  AND order_month = 1
  AND order_date = '2024-01-15';
```

**4. Glue Job Optimization:**
- Use Glue Flex for non-urgent jobs (50% cheaper)
- Enable job bookmarks to avoid reprocessing
- Right-size DPUs based on data volume

My AWS expertise helps deliver fast, reliable, cost-effective analytics that drive business decisions!

