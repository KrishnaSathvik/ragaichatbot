---
tags: [aws, cloud, data-engineering, s3, glue, lambda, redshift, kinesis, ec2, rds]
persona: de
---

# AWS Data Engineering Services & Krishna's Experience

## Core AWS Services for Data Engineering

### Amazon S3 (Simple Storage Service)
**Krishna's Usage at Walgreens:**
- **Data Lake Storage**: Used S3 as primary data lake for storing 10TB+ monthly data
- **Bronze/Silver/Gold Architecture**: Implemented medallion architecture with S3 buckets
- **Cost Optimization**: Used S3 Intelligent Tiering, reducing storage costs by 25%
- **Data Partitioning**: Organized data by date, region, and business unit for efficient querying

**Key Features Used:**
- S3 Lifecycle policies for automatic data archival
- S3 Cross-Region Replication for disaster recovery
- S3 Event Notifications to trigger Lambda functions
- S3 Select for querying data without full download

### AWS Glue
**Krishna's Implementation:**
- **ETL Jobs**: Built serverless ETL pipelines processing pharmacy and supply chain data
- **Data Catalog**: Created centralized metadata repository for 200+ tables
- **Crawlers**: Automated schema discovery for new data sources
- **Job Monitoring**: Set up CloudWatch alarms for job failures

**Code Example from Krishna's Projects:**
```python
import boto3
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext

# Glue job for processing pharmacy data
glueContext = GlueContext(SparkContext.getOrCreate())
spark = glueContext.spark_session

# Read from S3 Bronze layer
pharmacy_df = glueContext.create_dynamic_frame.from_catalog(
    database="pharmacy_db",
    table_name="bronze_pharmacy_data"
).toDF()

# Transform and clean data
cleaned_df = pharmacy_df.filter(col("status") == "active") \
    .withColumn("processed_date", current_timestamp())

# Write to Silver layer
glueContext.write_dynamic_frame.from_options(
    frame=DynamicFrame.fromDF(cleaned_df, glueContext, "cleaned_pharmacy"),
    connection_type="s3",
    connection_options={
        "path": "s3://walgreens-data-lake/silver/pharmacy/",
        "partitionKeys": ["year", "month", "day"]
    }
)
```

### Amazon Redshift
**Krishna's Data Warehouse Experience:**
- **Data Modeling**: Designed star schema for analytics with fact and dimension tables
- **Performance Tuning**: Optimized queries using distribution keys and sort keys
- **Data Loading**: Implemented COPY commands for bulk data loading from S3
- **Query Optimization**: Reduced average query time from 45 seconds to 8 seconds

**Redshift Best Practices Applied:**
```sql
-- Distribution key optimization
CREATE TABLE fact_sales (
    sale_id BIGINT,
    customer_id BIGINT,
    product_id BIGINT,
    sale_date DATE,
    amount DECIMAL(10,2)
) DISTKEY(customer_id) SORTKEY(sale_date);

-- Query optimization with window functions
SELECT 
    customer_id,
    sale_date,
    amount,
    SUM(amount) OVER (PARTITION BY customer_id ORDER BY sale_date 
                      ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) as rolling_7day_sales
FROM fact_sales
WHERE sale_date >= '2023-01-01';
```

### AWS Lambda
**Krishna's Serverless Implementations:**
- **Data Validation**: Created Lambda functions for real-time data quality checks
- **API Integration**: Built REST APIs for data access using Lambda + API Gateway
- **Event Processing**: Processed S3 events for automated data pipeline triggers
- **Cost Savings**: Replaced EC2 instances with Lambda, reducing compute costs by 40%

**Lambda Function Example:**
```python
import json
import boto3
from datetime import datetime

def lambda_handler(event, context):
    s3 = boto3.client('s3')
    
    # Process S3 event
    for record in event['Records']:
        bucket = record['s3']['bucket']['name']
        key = record['s3']['object']['key']
        
        # Validate file format and size
        response = s3.head_object(Bucket=bucket, Key=key)
        if response['ContentType'] != 'text/csv':
            raise ValueError(f"Invalid file type: {key}")
        
        # Trigger Glue job
        glue = boto3.client('glue')
        glue.start_job_run(
            JobName='pharmacy-etl-job',
            Arguments={
                '--input_path': f's3://{bucket}/{key}',
                '--output_path': 's3://walgreens-data-lake/silver/pharmacy/'
            }
        )
    
    return {'statusCode': 200, 'body': 'Processing started'}
```

### Amazon Kinesis
**Krishna's Real-time Data Processing:**
- **Data Streams**: Processed real-time pharmacy transactions (1000+ events/second)
- **Firehose**: Delivered streaming data to S3 and Redshift
- **Analytics**: Used Kinesis Analytics for real-time aggregations
- **Monitoring**: Set up CloudWatch dashboards for stream health

### AWS EC2 & EMR
**Krishna's Big Data Processing:**
- **EMR Clusters**: Launched transient clusters for large-scale data processing
- **Spot Instances**: Used spot instances for cost optimization (60% savings)
- **Auto Scaling**: Configured cluster auto-scaling based on workload
- **Security**: Implemented VPC, security groups, and IAM roles

## AWS Architecture Patterns

### Data Lake Architecture (Implemented at Walgreens)
```
S3 Data Lake Structure:
├── bronze/           # Raw data ingestion
│   ├── pharmacy/
│   ├── supply_chain/
│   └── customer/
├── silver/           # Cleaned and validated data
│   ├── pharmacy/
│   ├── supply_chain/
│   └── customer/
└── gold/             # Business-ready aggregated data
    ├── analytics/
    ├── reporting/
    └── ml_features/
```

### Event-Driven Architecture
- **S3 Events** → **Lambda** → **Glue Jobs** → **S3/Redshift**
- **CloudWatch Events** → **Step Functions** → **Multiple Services**
- **API Gateway** → **Lambda** → **DynamoDB/Redshift**

## Cost Optimization Strategies

### Krishna's Cost Reduction Achievements:
1. **S3 Intelligent Tiering**: 25% storage cost reduction
2. **Spot Instances**: 60% compute cost savings
3. **Lambda vs EC2**: 40% reduction in serverless workloads
4. **Redshift Query Optimization**: 80% faster queries = lower compute costs
5. **Data Compression**: Used Parquet format, reducing storage by 70%

### Best Practices Applied:
- **Right-sizing**: Regular review and adjustment of instance types
- **Reserved Instances**: Purchased RIs for predictable workloads
- **Auto-scaling**: Implemented for variable workloads
- **Data Lifecycle**: Automated archival and deletion policies

## Security & Compliance

### Security Measures Implemented:
- **IAM Roles**: Least privilege access for all services
- **VPC**: Private subnets for data processing
- **Encryption**: At rest (S3, Redshift) and in transit (TLS)
- **Audit Logging**: CloudTrail for all API calls
- **Data Masking**: PII protection in analytics layer

### Compliance (HIPAA for Healthcare):
- **Data Classification**: Tagged sensitive data appropriately
- **Access Controls**: Role-based access with MFA
- **Audit Trails**: Complete logging for compliance reporting
- **Data Retention**: Automated policies for data lifecycle

## Monitoring & Alerting

### CloudWatch Implementation:
- **Custom Metrics**: Business KPIs and data quality metrics
- **Dashboards**: Real-time monitoring of data pipelines
- **Alarms**: Automated alerts for failures and performance issues
- **Logs**: Centralized logging for troubleshooting

### Key Metrics Tracked:
- Data pipeline success rates (99.5% SLA)
- Query performance (average 8 seconds)
- Cost per GB processed ($0.15/GB)
- Data freshness (95% within 1 hour)

## Migration Experience

### Legacy System Migration:
- **From On-premise**: Migrated 50+ SQL Server databases to AWS
- **Data Migration**: Used AWS DMS for zero-downtime migration
- **Application Migration**: Rehosted applications on EC2
- **Timeline**: 6-month migration with 99.9% uptime

### Challenges Overcome:
- **Data Consistency**: Implemented CDC (Change Data Capture)
- **Performance**: Optimized queries for cloud environment
- **Cost Management**: Right-sized resources post-migration
- **Security**: Enhanced security posture in cloud

## Interview Talking Points

### Technical Achievements:
- "Reduced data processing costs by 40% through AWS optimization"
- "Achieved 99.5% SLA for data pipelines using AWS services"
- "Processed 10TB+ monthly data with 8-second average query time"
- "Implemented zero-downtime migration from on-premise to AWS"

### Problem-Solving Examples:
- **Data Skew**: Used S3 partitioning and Redshift distribution keys
- **Cost Optimization**: Implemented spot instances and intelligent tiering
- **Performance**: Optimized queries and used appropriate instance types
- **Security**: Enhanced compliance with automated audit trails

### Tools & Technologies:
- **AWS Services**: S3, Glue, Lambda, Redshift, Kinesis, EC2, EMR
- **Languages**: Python, SQL, PySpark
- **Monitoring**: CloudWatch, CloudTrail
- **Security**: IAM, VPC, KMS, Secrets Manager
