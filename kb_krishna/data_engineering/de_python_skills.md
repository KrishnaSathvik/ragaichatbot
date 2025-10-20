---
tags: [data-engineer, python, pandas, automation, data-quality, scripting]
persona: de
---

# Python for Data Engineering - Krishna's Skills

## Introduction
**Krishna's Python Experience:**
Python is my go-to language for data engineering - from pandas transformations to automation scripts. At Walgreens, I use Python for data quality checks, pipeline orchestration, and glue code between systems. Here's everything I use daily.

## Pandas for Data Transformation

### Data Cleaning
**Krishna's Most Common Patterns:**
```python
import pandas as pd
import numpy as np
from datetime import datetime

# Read data
df = pd.read_csv('orders.csv')

# Clean and standardize
df_clean = (
    df
    # Remove duplicates
    .drop_duplicates(subset='order_id', keep='last')
    
    # Handle missing values
    .assign(
        customer_id=lambda x: x['customer_id'].fillna('UNKNOWN'),
        order_amount=lambda x: x['order_amount'].fillna(0)
    )
    
    # Data type conversions
    .astype({
        'order_id': 'str',
        'customer_id': 'str',
        'order_amount': 'float64'
    })
    
    # Parse dates
    .assign(
        order_date=lambda x: pd.to_datetime(x['order_date'], errors='coerce')
    )
    
    # String cleaning
    .assign(
        customer_email=lambda x: x['customer_email'].str.lower().str.strip(),
        product_name=lambda x: x['product_name'].str.title()
    )
)
```

### Complex Transformations
**Krishna's Business Logic:**
```python
# Customer segmentation based on business rules
def calculate_customer_segment(row):
    ltv = row['lifetime_value']
    tenure_days = row['customer_tenure_days']
    order_count = row['order_count']
    
    if ltv > 10000 or (ltv > 5000 and tenure_days > 365):
        return 'Platinum'
    elif ltv > 5000 or (ltv > 2000 and order_count > 10):
        return 'Gold'
    elif ltv > 1000 or order_count > 5:
        return 'Silver'
    else:
        return 'Bronze'

df['customer_segment'] = df.apply(calculate_customer_segment, axis=1)

# Vectorized alternative (faster for large datasets)
df['customer_segment'] = np.select(
    [
        (df['lifetime_value'] > 10000) | ((df['lifetime_value'] > 5000) & (df['customer_tenure_days'] > 365)),
        (df['lifetime_value'] > 5000) | ((df['lifetime_value'] > 2000) & (df['order_count'] > 10)),
        (df['lifetime_value'] > 1000) | (df['order_count'] > 5)
    ],
    ['Platinum', 'Gold', 'Silver'],
    default='Bronze'
)
```

### Aggregations & Grouping
**Krishna's Analytics Patterns:**
```python
# Complex aggregations
customer_summary = (
    df_orders
    .groupby('customer_id')
    .agg({
        'order_id': 'count',
        'order_amount': ['sum', 'mean', 'std'],
        'order_date': ['min', 'max']
    })
    .reset_index()
)

# Flatten multi-level columns
customer_summary.columns = ['_'.join(col).strip('_') for col in customer_summary.columns.values]

# Custom aggregations
def calculate_metrics(group):
    return pd.Series({
        'order_count': len(group),
        'total_spent': group['order_amount'].sum(),
        'avg_order_value': group['order_amount'].mean(),
        'first_order': group['order_date'].min(),
        'last_order': group['order_date'].max(),
        'days_active': (group['order_date'].max() - group['order_date'].min()).days,
        'unique_products': group['product_id'].nunique()
    })

customer_metrics = df_orders.groupby('customer_id').apply(calculate_metrics).reset_index()
```

## Data Quality Framework

### Automated Quality Checks
**Krishna's Production Quality System:**
```python
import logging
from typing import Dict, List, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataQualityChecker:
    """Comprehensive data quality validation"""
    
    def __init__(self, df: pd.DataFrame, table_name: str):
        self.df = df
        self.table_name = table_name
        self.checks = []
        self.errors = []
        self.warnings = []
    
    def check_nulls(self, columns: List[str], threshold: float = 0.05):
        """Check for null values exceeding threshold"""
        for col in columns:
            if col not in self.df.columns:
                continue
            
            null_count = self.df[col].isnull().sum()
            null_pct = null_count / len(self.df)
            
            if null_pct > threshold:
                self.errors.append({
                    'check': 'null_values',
                    'column': col,
                    'null_count': null_count,
                    'null_percentage': round(null_pct * 100, 2)
                })
            elif null_pct > 0:
                self.warnings.append({
                    'check': 'null_values',
                    'column': col,
                    'null_count': null_count
                })
        
        return self
    
    def check_duplicates(self, key_columns: List[str]):
        """Check for duplicate records"""
        dup_count = self.df.duplicated(subset=key_columns).sum()
        
        if dup_count > 0:
            self.errors.append({
                'check': 'duplicates',
                'key_columns': key_columns,
                'duplicate_count': dup_count
            })
        
        return self
    
    def check_data_types(self, expected_types: Dict[str, str]):
        """Validate column data types"""
        for col, expected_type in expected_types.items():
            if col not in self.df.columns:
                self.errors.append({
                    'check': 'missing_column',
                    'column': col
                })
                continue
            
            actual_type = str(self.df[col].dtype)
            if expected_type not in actual_type:
                self.errors.append({
                    'check': 'data_type_mismatch',
                    'column': col,
                    'expected': expected_type,
                    'actual': actual_type
                })
        
        return self
    
    def check_value_range(self, column: str, min_value: Any, max_value: Any):
        """Validate numeric ranges"""
        if column not in self.df.columns:
            return self
        
        out_of_range = (
            (self.df[column] < min_value) | 
            (self.df[column] > max_value)
        ).sum()
        
        if out_of_range > 0:
            self.errors.append({
                'check': 'value_range',
                'column': column,
                'out_of_range_count': out_of_range,
                'expected_range': f'{min_value} to {max_value}'
            })
        
        return self
    
    def check_referential_integrity(self, column: str, reference_df: pd.DataFrame, reference_column: str):
        """Check foreign key integrity"""
        orphaned = ~self.df[column].isin(reference_df[reference_column])
        orphaned_count = orphaned.sum()
        
        if orphaned_count > 0:
            self.errors.append({
                'check': 'referential_integrity',
                'column': column,
                'reference_column': reference_column,
                'orphaned_count': orphaned_count
            })
        
        return self
    
    def generate_report(self) -> Dict:
        """Generate quality report"""
        report = {
            'table_name': self.table_name,
            'timestamp': datetime.now().isoformat(),
            'row_count': len(self.df),
            'column_count': len(self.df.columns),
            'errors': self.errors,
            'warnings': self.warnings,
            'status': 'FAILED' if self.errors else 'PASSED'
        }
        
        # Log report
        if self.errors:
            logger.error(f"❌ Data Quality FAILED for {self.table_name}: {len(self.errors)} errors")
            for error in self.errors:
                logger.error(f"  - {error}")
        else:
            logger.info(f"✅ Data Quality PASSED for {self.table_name}")
        
        return report

# Usage
df_orders = pd.read_csv('orders.csv')

quality_report = (
    DataQualityChecker(df_orders, 'fct_orders')
    .check_nulls(['order_id', 'customer_id'], threshold=0.01)
    .check_duplicates(['order_id'])
    .check_data_types({
        'order_id': 'object',
        'order_amount': 'float',
        'order_date': 'datetime'
    })
    .check_value_range('order_amount', 0, 1000000)
    .generate_report()
)
```

## Azure/Databricks Integration

### Reading from Azure Blob
```python
from azure.storage.blob import BlobServiceClient
import io

def read_blob_to_pandas(account_name: str, container_name: str, blob_name: str, account_key: str) -> pd.DataFrame:
    """Read CSV from Azure Blob Storage"""
    
    connection_string = f"DefaultEndpointsProtocol=https;AccountName={account_name};AccountKey={account_key};EndpointSuffix=core.windows.net"
    
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
    
    # Download blob content
    blob_data = blob_client.download_blob().readall()
    
    # Read into pandas
    df = pd.read_csv(io.BytesIO(blob_data))
    
    return df

# Usage
df = read_blob_to_pandas(
    account_name='walgreensdata',
    container_name='raw',
    blob_name='orders/2024-01-15/orders.csv',
    account_key='your-key-here'
)
```

### Writing to Delta Lake
```python
def pandas_to_delta(df: pd.DataFrame, delta_path: str, mode: str = 'overwrite', partition_cols: List[str] = None):
    """Convert pandas to Delta format via PySpark"""
    from pyspark.sql import SparkSession
    
    spark = SparkSession.builder.getOrCreate()
    
    # Convert pandas to Spark DataFrame
    spark_df = spark.createDataFrame(df)
    
    # Write to Delta
    writer = spark_df.write.format('delta').mode(mode)
    
    if partition_cols:
        writer = writer.partitionBy(*partition_cols)
    
    writer.save(delta_path)
    
    print(f"✅ Wrote {len(df):,} rows to {delta_path}")

# Usage
pandas_to_delta(
    df_orders,
    delta_path='/mnt/silver/orders',
    mode='overwrite',
    partition_cols=['order_date']
)
```

## Automation Scripts

### Pipeline Monitoring Script
**Krishna's Daily Monitoring:**
```python
import requests
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText

class PipelineMonitor:
    """Monitor data pipelines and alert on failures"""
    
    def __init__(self, adf_resource_id: str, subscription_id: str, access_token: str):
        self.adf_resource_id = adf_resource_id
        self.subscription_id = subscription_id
        self.access_token = access_token
        self.base_url = f"https://management.azure.com{adf_resource_id}"
    
    def get_pipeline_runs(self, pipeline_name: str, hours: int = 24) -> List[Dict]:
        """Get recent pipeline runs"""
        url = f"{self.base_url}/queryPipelineRuns?api-version=2018-06-01"
        
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)
        
        payload = {
            "lastUpdatedAfter": start_time.isoformat() + "Z",
            "lastUpdatedBefore": end_time.isoformat() + "Z",
            "filters": [{
                "operand": "PipelineName",
                "operator": "Equals",
                "values": [pipeline_name]
            }]
        }
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        
        return response.json().get('value', [])
    
    def check_pipeline_health(self, pipeline_name: str) -> Dict:
        """Check pipeline health status"""
        runs = self.get_pipeline_runs(pipeline_name, hours=24)
        
        if not runs:
            return {
                'status': 'WARNING',
                'message': f'No runs found for {pipeline_name} in last 24 hours'
            }
        
        latest_run = runs[0]
        status = latest_run.get('status')
        
        if status == 'Failed':
            return {
                'status': 'CRITICAL',
                'message': f'{pipeline_name} FAILED',
                'run_id': latest_run.get('runId'),
                'error': latest_run.get('message')
            }
        elif status == 'Succeeded':
            return {
                'status': 'OK',
                'message': f'{pipeline_name} succeeded',
                'duration': latest_run.get('durationInMs')
            }
        else:
            return {
                'status': 'WARNING',
                'message': f'{pipeline_name} status: {status}'
            }
    
    def send_alert(self, subject: str, body: str, recipients: List[str]):
        """Send email alert"""
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = 'data-pipelines@walgreens.com'
        msg['To'] = ', '.join(recipients)
        
        with smtplib.SMTP('smtp.office365.com', 587) as server:
            server.starttls()
            server.send_message(msg)

# Usage
monitor = PipelineMonitor(
    adf_resource_id='/subscriptions/xxx/resourceGroups/rg-data/providers/Microsoft.DataFactory/factories/adf-walgreens',
    subscription_id='xxx',
    access_token='your-token'
)

# Check critical pipelines
critical_pipelines = ['pl_daily_orders', 'pl_customer_sync', 'pl_inventory_update']

for pipeline in critical_pipelines:
    health = monitor.check_pipeline_health(pipeline)
    
    if health['status'] in ['CRITICAL', 'WARNING']:
        monitor.send_alert(
            subject=f"Pipeline Alert: {pipeline}",
            body=health['message'],
            recipients=['data-team@walgreens.com']
        )
```

### Data Reconciliation Script
**Krishna's Quality Assurance:**
```python
def reconcile_data(source_df: pd.DataFrame, target_df: pd.DataFrame, key_columns: List[str]) -> Dict:
    """Compare source and target data"""
    
    # Record counts
    source_count = len(source_df)
    target_count = len(target_df)
    
    # Find differences
    source_keys = set(source_df[key_columns].apply(tuple, axis=1))
    target_keys = set(target_df[key_columns].apply(tuple, axis=1))
    
    missing_in_target = source_keys - target_keys
    extra_in_target = target_keys - source_keys
    
    # Value differences for common keys
    common_keys = source_keys & target_keys
    
    value_differences = []
    for key in common_keys:
        source_row = source_df[source_df[key_columns].apply(tuple, axis=1) == key].iloc[0]
        target_row = target_df[target_df[key_columns].apply(tuple, axis=1) == key].iloc[0]
        
        for col in source_df.columns:
            if col not in key_columns and col in target_df.columns:
                if source_row[col] != target_row[col]:
                    value_differences.append({
                        'key': key,
                        'column': col,
                        'source_value': source_row[col],
                        'target_value': target_row[col]
                    })
    
    # Generate report
    report = {
        'source_count': source_count,
        'target_count': target_count,
        'count_difference': target_count - source_count,
        'missing_in_target_count': len(missing_in_target),
        'extra_in_target_count': len(extra_in_target),
        'value_differences_count': len(value_differences),
        'status': 'PASSED' if (
            missing_in_target == set() and 
            extra_in_target == set() and 
            len(value_differences) == 0
        ) else 'FAILED'
    }
    
    if report['status'] == 'FAILED':
        logger.error(f"❌ Reconciliation FAILED: {report}")
    else:
        logger.info(f"✅ Reconciliation PASSED")
    
    return report
```

## Performance Optimization

### Efficient DataFrame Operations
**Krishna's Speed Tips:**
```python
import time

# BAD: Iterating over rows
start = time.time()
for idx, row in df.iterrows():
    df.loc[idx, 'new_column'] = row['col1'] + row['col2']
print(f"iterrows: {time.time() - start:.2f}s")  # 10+ seconds

# BETTER: Apply function
start = time.time()
df['new_column'] = df.apply(lambda row: row['col1'] + row['col2'], axis=1)
print(f"apply: {time.time() - start:.2f}s")  # 2-3 seconds

# BEST: Vectorized operations
start = time.time()
df['new_column'] = df['col1'] + df['col2']
print(f"vectorized: {time.time() - start:.2f}s")  # 0.01 seconds
```

### Memory Optimization
```python
# Reduce memory usage
def optimize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Optimize DataFrame memory usage"""
    
    for col in df.columns:
        col_type = df[col].dtype
        
        if col_type != 'object':
            c_min = df[col].min()
            c_max = df[col].max()
            
            if str(col_type)[:3] == 'int':
                if c_min > np.iinfo(np.int8).min and c_max < np.iinfo(np.int8).max:
                    df[col] = df[col].astype(np.int8)
                elif c_min > np.iinfo(np.int16).min and c_max < np.iinfo(np.int16).max:
                    df[col] = df[col].astype(np.int16)
                elif c_min > np.iinfo(np.int32).min and c_max < np.iinfo(np.int32).max:
                    df[col] = df[col].astype(np.int32)
            
            elif str(col_type)[:5] == 'float':
                if c_min > np.finfo(np.float32).min and c_max < np.finfo(np.float32).max:
                    df[col] = df[col].astype(np.float32)
    
    return df

# Before: 1.2GB
# After: 300MB (75% reduction!)
```

These Python skills help me build efficient, reliable data engineering solutions at Walgreens!

