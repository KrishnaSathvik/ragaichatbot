---
tags: [analytics-engineer, python, pandas, pyspark, data-transformation]
persona: analytics
---

# Python for Analytics Engineers - Tejuu's Skills

## Introduction
**Tejuu's Python Journey:**
As an Analytics Engineer, I use Python daily - primarily for data transformation, testing, and automation. While I'm not a software engineer, my Python skills help me build reliable data pipelines and solve business problems efficiently.

## Pandas for Data Transformation

**Tejuu's Common Use Cases:**
I use pandas for prototyping transformations, data quality checks, and ad-hoc analysis.

**Data Cleaning Example:**
```python
import pandas as pd
import numpy as np
from datetime import datetime

# Read data
df_customers = pd.read_csv('customers.csv')

# Clean and standardize
df_clean = (
    df_customers
    # Remove duplicates
    .drop_duplicates(subset='customer_id', keep='last')
    
    # Clean email addresses
    .assign(email=lambda x: x['email'].str.lower().str.strip())
    
    # Standardize names
    .assign(
        first_name=lambda x: x['first_name'].str.title().str.strip(),
        last_name=lambda x: x['last_name'].str.title().str.strip()
    )
    
    # Handle missing values
    .assign(
        phone=lambda x: x['phone'].fillna('Unknown'),
        city=lambda x: x['city'].fillna('Not Provided')
    )
    
    # Parse dates
    .assign(registration_date=lambda x: pd.to_datetime(x['registration_date']))
    
    # Calculate customer tenure
    .assign(
        customer_tenure_days=lambda x: (datetime.now() - x['registration_date']).dt.days
    )
)

print(df_clean.head())
```

**Business Logic Implementation:**
```python
# Calculate customer segment based on business rules

def calculate_customer_segment(ltv, tenure_days, order_count):
    """
    Business rules from Marketing team:
    - Platinum: LTV > $10,000 OR (LTV > $5,000 AND tenure > 365 days)
    - Gold: LTV > $5,000 OR (LTV > $2,000 AND order_count > 10)
    - Silver: LTV > $1,000 OR order_count > 5
    - Bronze: Everyone else
    """
    if ltv > 10000 or (ltv > 5000 and tenure_days > 365):
        return 'Platinum'
    elif ltv > 5000 or (ltv > 2000 and order_count > 10):
        return 'Gold'
    elif ltv > 1000 or order_count > 5:
        return 'Silver'
    else:
        return 'Bronze'

# Apply business rules
df_clean['customer_segment'] = df_clean.apply(
    lambda row: calculate_customer_segment(
        row['lifetime_value'],
        row['customer_tenure_days'],
        row['order_count']
    ),
    axis=1
)
```

**Data Quality Checks:**
```python
# Comprehensive data quality report

def generate_data_quality_report(df, table_name):
    """Generate data quality report for stakeholders"""
    
    report = {
        'table_name': table_name,
        'timestamp': datetime.now(),
        'row_count': len(df),
        'column_count': len(df.columns),
        'checks': []
    }
    
    # Check 1: Null values
    null_counts = df.isnull().sum()
    null_pct = (null_counts / len(df) * 100).round(2)
    
    for col in df.columns:
        if null_counts[col] > 0:
            report['checks'].append({
                'check': 'null_values',
                'column': col,
                'null_count': int(null_counts[col]),
                'null_percentage': float(null_pct[col]),
                'status': 'WARNING' if null_pct[col] > 5 else 'INFO'
            })
    
    # Check 2: Duplicates
    dup_count = df.duplicated().sum()
    if dup_count > 0:
        report['checks'].append({
            'check': 'duplicates',
            'duplicate_count': int(dup_count),
            'status': 'ERROR'
        })
    
    # Check 3: Data types
    for col in df.columns:
        expected_type = get_expected_type(col)  # From metadata
        actual_type = str(df[col].dtype)
        if expected_type != actual_type:
            report['checks'].append({
                'check': 'data_type_mismatch',
                'column': col,
                'expected': expected_type,
                'actual': actual_type,
                'status': 'ERROR'
            })
    
    # Check 4: Value ranges
    numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns
    for col in numeric_cols:
        if col == 'order_amount':
            invalid_count = ((df[col] < 0) | (df[col] > 1000000)).sum()
            if invalid_count > 0:
                report['checks'].append({
                    'check': 'value_range',
                    'column': col,
                    'invalid_count': int(invalid_count),
                    'status': 'ERROR'
                })
    
    # Generate summary
    error_count = len([c for c in report['checks'] if c['status'] == 'ERROR'])
    warning_count = len([c for c in report['checks'] if c['status'] == 'WARNING'])
    
    report['summary'] = {
        'total_checks': len(report['checks']),
        'errors': error_count,
        'warnings': warning_count,
        'overall_status': 'FAILED' if error_count > 0 else 'PASSED'
    }
    
    return report

# Run quality checks
report = generate_data_quality_report(df_clean, 'dim_customer')
print(f"Data Quality: {report['summary']['overall_status']}")
print(f"Errors: {report['summary']['errors']}, Warnings: {report['summary']['warnings']}")
```

**Business Value:**
Finance CFO asked: "How do I know the customer segments are correct?"
I showed him the data quality report with business rule validation. He was impressed!

## PySpark for Large-Scale Transformations

**Tejuu's PySpark Usage:**
For processing millions of rows, I use PySpark in Databricks.

**Example: Customer LTV Calculation:**
```python
from pyspark.sql import SparkSession, Window
from pyspark.sql import functions as F

spark = SparkSession.builder.appName("CustomerLTV").getOrCreate()

# Read data
df_orders = spark.read.format("delta").load("/mnt/raw/orders")
df_customers = spark.read.format("delta").load("/mnt/raw/customers")

# Calculate customer metrics
df_customer_metrics = (
    df_orders
    .filter(F.col("order_status") == "completed")
    .groupBy("customer_id")
    .agg(
        F.min("order_date").alias("first_order_date"),
        F.max("order_date").alias("last_order_date"),
        F.count("order_id").alias("total_orders"),
        F.sum("order_amount").alias("lifetime_value"),
        F.avg("order_amount").alias("avg_order_value"),
        F.countDistinct(F.col("order_date").cast("date")).alias("active_days")
    )
    .withColumn(
        "customer_tenure_days",
        F.datediff(F.current_date(), F.col("first_order_date"))
    )
    .withColumn(
        "days_since_last_order",
        F.datediff(F.current_date(), F.col("last_order_date"))
    )
    .withColumn(
        "is_active",
        F.when(F.col("days_since_last_order") <= 90, True).otherwise(False)
    )
)

# Join with customer dimensions
df_customer_enriched = (
    df_customer_metrics
    .join(df_customers, "customer_id", "left")
    .select(
        "customer_id",
        "customer_name",
        "email",
        "first_order_date",
        "last_order_date",
        "total_orders",
        "lifetime_value",
        "avg_order_value",
        "customer_tenure_days",
        "days_since_last_order",
        "is_active"
    )
)

# Apply customer segmentation
df_final = (
    df_customer_enriched
    .withColumn(
        "customer_segment",
        F.when(
            (F.col("lifetime_value") > 10000) | 
            ((F.col("lifetime_value") > 5000) & (F.col("customer_tenure_days") > 365)),
            "Platinum"
        )
        .when(
            (F.col("lifetime_value") > 5000) | 
            ((F.col("lifetime_value") > 2000) & (F.col("total_orders") > 10)),
            "Gold"
        )
        .when(
            (F.col("lifetime_value") > 1000) | (F.col("total_orders") > 5),
            "Silver"
        )
        .otherwise("Bronze")
    )
)

# Write to Delta
(
    df_final.write
    .format("delta")
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .save("/mnt/analytics/dim_customer")
)

print(f"✅ Processed {df_final.count():,} customers")
```

**Window Functions for Rankings:**
```python
# Calculate product rankings within each category

from pyspark.sql.window import Window

window_spec = Window.partitionBy("product_category").orderBy(F.desc("total_revenue"))

df_product_rankings = (
    df_sales
    .groupBy("product_category", "product_id", "product_name")
    .agg(
        F.sum("sales_amount").alias("total_revenue"),
        F.sum("quantity").alias("total_quantity"),
        F.count("order_id").alias("order_count")
    )
    .withColumn("category_rank", F.row_number().over(window_spec))
    .withColumn("revenue_pct_of_category", 
        F.col("total_revenue") / F.sum("total_revenue").over(Window.partitionBy("product_category"))
    )
    .filter(F.col("category_rank") <= 10)  # Top 10 per category
    .orderBy("product_category", "category_rank")
)
```

## Python for dbt Integration

**Tejuu's dbt Helper Scripts:**

**Script to Generate dbt Models from Database:**
```python
# generate_dbt_models.py
# Automatically generate dbt staging models from source tables

import psycopg2
import yaml
from pathlib import Path

def get_table_schema(conn, schema, table):
    """Get column information for a table"""
    query = f"""
        SELECT 
            column_name,
            data_type,
            is_nullable
        FROM information_schema.columns
        WHERE table_schema = '{schema}'
          AND table_name = '{table}'
        ORDER BY ordinal_position
    """
    
    cursor = conn.cursor()
    cursor.execute(query)
    columns = cursor.fetchall()
    return columns

def generate_staging_model(schema, table, columns):
    """Generate dbt staging model SQL"""
    
    model_name = f"stg_{schema}_{table}"
    
    # SQL template
    sql = f"""-- models/staging/{schema}/{model_name}.sql

{{{{
    config(
        materialized='view',
        schema='staging'
    )
}}}}

WITH source AS (
    SELECT * FROM {{{{ source('{schema}', '{table}') }}}}
),

renamed AS (
    SELECT
"""
    
    # Add columns
    col_lines = []
    for col_name, data_type, is_nullable in columns:
        # Clean column name
        clean_name = col_name.lower().replace(' ', '_')
        
        # Add type casting if needed
        if data_type in ['varchar', 'text']:
            col_lines.append(f"        TRIM({col_name}) AS {clean_name}")
        elif data_type == 'timestamp':
            col_lines.append(f"        {col_name}::TIMESTAMP AS {clean_name}")
        else:
            col_lines.append(f"        {col_name} AS {clean_name}")
    
    sql += ",\n".join(col_lines)
    sql += "\n    FROM source\n)\n\nSELECT * FROM renamed"
    
    return model_name, sql

def generate_schema_yml(schema, table, columns):
    """Generate dbt schema.yml"""
    
    model_name = f"stg_{schema}_{table}"
    
    schema_dict = {
        'version': 2,
        'models': [{
            'name': model_name,
            'description': f'Staging model for {schema}.{table}',
            'columns': [
                {
                    'name': col[0].lower().replace(' ', '_'),
                    'description': '',
                    'tests': ['not_null'] if col[2] == 'NO' else []
                }
                for col in columns
            ]
        }]
    }
    
    return yaml.dump(schema_dict, default_flow_style=False)

# Connect to database
conn = psycopg2.connect(
    host="your-database.com",
    database="analytics",
    user="readonly",
    password="secret"
)

# Generate models for all tables in raw schema
cursor = conn.cursor()
cursor.execute("""
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = 'raw'
    ORDER BY table_name
""")

tables = cursor.fetchall()

for (table_name,) in tables:
    print(f"Generating model for raw.{table_name}...")
    
    # Get schema
    columns = get_table_schema(conn, 'raw', table_name)
    
    # Generate SQL
    model_name, sql = generate_staging_model('raw', table_name, columns)
    
    # Write SQL file
    sql_path = Path(f"models/staging/raw/{model_name}.sql")
    sql_path.parent.mkdir(parents=True, exist_ok=True)
    sql_path.write_text(sql)
    
    # Generate schema.yml
    schema_yml = generate_schema_yml('raw', table_name, columns)
    yml_path = Path(f"models/staging/raw/schema.yml")
    yml_path.write_text(schema_yml)
    
    print(f"  ✅ Created {sql_path}")

conn.close()
print("\n🎉 All models generated!")
```

**Business Impact:**
Saved 20+ hours manually writing staging models for 50+ source tables!

## Automation Scripts

**Tejuu's Daily Helpers:**

**Script to Check Data Freshness:**
```python
# check_data_freshness.py
# Alert if source data is stale

import boto3
from datetime import datetime, timedelta
import json

def check_s3_freshness(bucket, prefix, max_age_hours=24):
    """Check if files in S3 are recent"""
    
    s3 = boto3.client('s3')
    
    response = s3.list_objects_v2(
        Bucket=bucket,
        Prefix=prefix,
        MaxKeys=1
    )
    
    if 'Contents' not in response:
        return False, f"No files found in {prefix}"
    
    last_modified = response['Contents'][0]['LastModified']
    age_hours = (datetime.now(last_modified.tzinfo) - last_modified).seconds / 3600
    
    is_fresh = age_hours < max_age_hours
    message = f"Data is {age_hours:.1f} hours old (max: {max_age_hours})"
    
    return is_fresh, message

def send_alert(message):
    """Send Slack alert"""
    sns = boto3.client('sns')
    sns.publish(
        TopicArn='arn:aws:sns:us-east-1:123456789:data-freshness-alerts',
        Subject='Data Freshness Alert',
        Message=message
    )

# Check critical data sources
sources_to_check = [
    ('my-bucket', 'raw/salesforce/', 12),
    ('my-bucket', 'raw/database_extracts/', 24),
    ('my-bucket', 'raw/api_data/', 6)
]

alerts = []

for bucket, prefix, max_age in sources_to_check:
    is_fresh, message = check_s3_freshness(bucket, prefix, max_age)
    
    if not is_fresh:
        alerts.append(f"⚠️  {prefix}: {message}")
    else:
        print(f"✅ {prefix}: {message}")

if alerts:
    alert_message = "Data Freshness Issues:\n\n" + "\n".join(alerts)
    send_alert(alert_message)
    print("\n❌ Alerts sent!")
else:
    print("\n✅ All data sources are fresh!")
```

**Script to Compare dbt Runs:**
```python
# compare_dbt_runs.py
# Compare results between dbt runs to catch issues

import json
from pathlib import Path

def load_run_results(file_path):
    """Load dbt run_results.json"""
    with open(file_path) as f:
        return json.load(f)

def compare_runs(baseline_path, current_path):
    """Compare two dbt runs"""
    
    baseline = load_run_results(baseline_path)
    current = load_run_results(current_path)
    
    # Get model results
    baseline_models = {
        r['unique_id']: r 
        for r in baseline['results']
    }
    
    current_models = {
        r['unique_id']: r 
        for r in current['results']
    }
    
    issues = []
    
    # Check for new failures
    for model_id, result in current_models.items():
        if result['status'] == 'error':
            baseline_result = baseline_models.get(model_id, {})
            if baseline_result.get('status') != 'error':
                issues.append(f"❌ NEW FAILURE: {model_id}")
    
    # Check for large row count changes
    for model_id in baseline_models.keys() & current_models.keys():
        baseline_rows = baseline_models[model_id].get('rows_affected', 0)
        current_rows = current_models[model_id].get('rows_affected', 0)
        
        if baseline_rows > 0:
            pct_change = abs(current_rows - baseline_rows) / baseline_rows * 100
            
            if pct_change > 20:  # More than 20% change
                issues.append(
                    f"⚠️  ROW COUNT CHANGE: {model_id} "
                    f"({baseline_rows:,} → {current_rows:,}, {pct_change:.1f}% change)"
                )
    
    # Check for slow models
    for model_id, result in current_models.items():
        execution_time = result.get('execution_time', 0)
        if execution_time > 300:  # More than 5 minutes
            issues.append(f"🐌 SLOW MODEL: {model_id} ({execution_time:.0f}s)")
    
    return issues

# Run comparison
issues = compare_runs(
    'target/baseline_run_results.json',
    'target/run_results.json'
)

if issues:
    print("\n🚨 Issues found:\n")
    for issue in issues:
        print(issue)
else:
    print("\n✅ No issues found!")
```

These Python skills help me build reliable, maintainable analytics pipelines that deliver business value!

