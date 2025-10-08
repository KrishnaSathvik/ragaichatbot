---
tags: [python, data-engineering, pandas, numpy, apache-airflow, etl, automation]
persona: de
---

# Python for Data Engineering & Krishna's Production Experience

## Core Python Libraries for Data Engineering

### Pandas for Data Processing
**Krishna's Real-World Applications at Walgreens:**

```python
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Data quality validation framework
class DataQualityValidator:
    def __init__(self, df):
        self.df = df
        self.quality_report = {}
    
    def check_null_values(self):
        """Check for null values in critical columns"""
        null_counts = self.df.isnull().sum()
        self.quality_report['null_values'] = null_counts[null_counts > 0].to_dict()
        return self
    
    def check_data_types(self):
        """Validate data types"""
        expected_types = {
            'customer_id': 'int64',
            'order_date': 'datetime64[ns]',
            'amount': 'float64'
        }
        
        type_issues = {}
        for col, expected_type in expected_types.items():
            if col in self.df.columns:
                actual_type = str(self.df[col].dtype)
                if actual_type != expected_type:
                    type_issues[col] = {'expected': expected_type, 'actual': actual_type}
        
        self.quality_report['type_issues'] = type_issues
        return self
    
    def check_business_rules(self):
        """Validate business logic"""
        issues = {}
        
        # Amount should be positive
        negative_amounts = (self.df['amount'] < 0).sum()
        if negative_amounts > 0:
            issues['negative_amounts'] = negative_amounts
        
        # Order date should not be in future
        future_dates = (self.df['order_date'] > datetime.now()).sum()
        if future_dates > 0:
            issues['future_dates'] = future_dates
        
        self.quality_report['business_rule_violations'] = issues
        return self
    
    def generate_report(self):
        """Generate comprehensive quality report"""
        return self.quality_report

# Usage in production pipeline
def process_pharmacy_data(file_path):
    """Process pharmacy transaction data with quality checks"""
    # Read data
    df = pd.read_csv(file_path, parse_dates=['order_date'])
    
    # Data quality validation
    validator = DataQualityValidator(df)
    quality_report = validator.check_null_values() \
                              .check_data_types() \
                              .check_business_rules() \
                              .generate_report()
    
    # Log quality issues
    if quality_report['null_values'] or quality_report['business_rule_violations']:
        logger.warning(f"Data quality issues found: {quality_report}")
    
    # Data cleaning
    df_clean = df.dropna(subset=['customer_id', 'order_date']) \
                 .query('amount > 0') \
                 .query('order_date <= @datetime.now()')
    
    # Feature engineering
    df_clean['day_of_week'] = df_clean['order_date'].dt.day_name()
    df_clean['month'] = df_clean['order_date'].dt.month
    df_clean['is_weekend'] = df_clean['order_date'].dt.weekday >= 5
    
    return df_clean, quality_report
```

### Advanced Pandas Operations
**Krishna's Analytics Pipeline:**

```python
# Customer segmentation using pandas
def customer_segmentation(transactions_df):
    """Segment customers based on RFM analysis"""
    
    # Calculate RFM metrics
    rfm = transactions_df.groupby('customer_id').agg({
        'order_date': lambda x: (datetime.now() - x.max()).days,  # Recency
        'order_id': 'count',  # Frequency
        'amount': 'sum'  # Monetary
    }).rename(columns={
        'order_date': 'recency',
        'order_id': 'frequency',
        'amount': 'monetary'
    })
    
    # Create RFM scores (1-5 scale)
    rfm['r_score'] = pd.qcut(rfm['recency'], 5, labels=[5,4,3,2,1])
    rfm['f_score'] = pd.qcut(rfm['frequency'].rank(method='first'), 5, labels=[1,2,3,4,5])
    rfm['m_score'] = pd.qcut(rfm['monetary'], 5, labels=[1,2,3,4,5])
    
    # Combine scores
    rfm['rfm_score'] = rfm['r_score'].astype(str) + rfm['f_score'].astype(str) + rfm['m_score'].astype(str)
    
    # Customer segments
    segment_map = {
        '555': 'Champions', '554': 'Champions', '544': 'Champions', '545': 'Champions',
        '543': 'Loyal Customers', '444': 'Loyal Customers', '435': 'Loyal Customers',
        '355': 'Potential Loyalists', '354': 'Potential Loyalists', '345': 'Potential Loyalists',
        '111': 'Lost Customers', '112': 'Lost Customers', '121': 'Lost Customers'
    }
    
    rfm['segment'] = rfm['rfm_score'].map(segment_map).fillna('Others')
    
    return rfm

# Time series analysis
def sales_trend_analysis(sales_df):
    """Analyze sales trends and seasonality"""
    
    # Resample to daily frequency
    daily_sales = sales_df.set_index('order_date').resample('D')['amount'].sum()
    
    # Calculate moving averages
    daily_sales['ma_7'] = daily_sales.rolling(window=7).mean()
    daily_sales['ma_30'] = daily_sales.rolling(window=30).mean()
    
    # Seasonal decomposition
    from statsmodels.tsa.seasonal import seasonal_decompose
    decomposition = seasonal_decompose(daily_sales.dropna(), model='additive', period=7)
    
    # Anomaly detection using IQR method
    Q1 = daily_sales.quantile(0.25)
    Q3 = daily_sales.quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    
    anomalies = daily_sales[(daily_sales < lower_bound) | (daily_sales > upper_bound)]
    
    return {
        'daily_sales': daily_sales,
        'decomposition': decomposition,
        'anomalies': anomalies
    }
```

## Apache Airflow for Workflow Orchestration

### DAG Development
**Krishna's Production DAGs:**

```python
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.providers.amazon.aws.operators.s3 import S3FileTransformOperator

# Default arguments
default_args = {
    'owner': 'krishna',
    'depends_on_past': False,
    'start_date': datetime(2023, 1, 1),
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'email': ['krishna@walgreens.com']
}

# DAG definition
dag = DAG(
    'pharmacy_data_pipeline',
    default_args=default_args,
    description='Daily pharmacy data processing pipeline',
    schedule_interval='0 2 * * *',  # Daily at 2 AM
    catchup=False,
    max_active_runs=1,
    tags=['pharmacy', 'etl', 'production']
)

def extract_pharmacy_data(**context):
    """Extract data from source systems"""
    import pandas as pd
    from sqlalchemy import create_engine
    
    # Database connection
    engine = create_engine('postgresql://user:pass@host:5432/pharmacy_db')
    
    # Extract data
    query = """
    SELECT customer_id, order_date, product_id, amount, store_id
    FROM pharmacy_transactions
    WHERE order_date >= CURRENT_DATE - INTERVAL '1 day'
    """
    
    df = pd.read_sql(query, engine)
    
    # Save to staging
    df.to_parquet('/tmp/pharmacy_data.parquet', index=False)
    
    # Log extraction metrics
    context['task_instance'].xcom_push(key='record_count', value=len(df))
    context['task_instance'].xcom_push(key='extraction_time', value=datetime.now().isoformat())
    
    return f"Extracted {len(df)} records"

def transform_data(**context):
    """Transform and clean data"""
    import pandas as pd
    
    # Read data
    df = pd.read_parquet('/tmp/pharmacy_data.parquet')
    
    # Data quality checks
    initial_count = len(df)
    
    # Remove duplicates
    df = df.drop_duplicates()
    
    # Data cleaning
    df = df.dropna(subset=['customer_id', 'order_date'])
    df = df[df['amount'] > 0]
    
    # Feature engineering
    df['day_of_week'] = pd.to_datetime(df['order_date']).dt.day_name()
    df['is_weekend'] = pd.to_datetime(df['order_date']).dt.weekday >= 5
    
    # Data validation
    final_count = len(df)
    data_loss_pct = ((initial_count - final_count) / initial_count) * 100
    
    if data_loss_pct > 5:  # Alert if more than 5% data loss
        raise ValueError(f"High data loss detected: {data_loss_pct:.2f}%")
    
    # Save transformed data
    df.to_parquet('/tmp/pharmacy_data_transformed.parquet', index=False)
    
    # Log transformation metrics
    context['task_instance'].xcom_push(key='final_record_count', value=final_count)
    context['task_instance'].xcom_push(key='data_loss_pct', value=data_loss_pct)
    
    return f"Transformed {final_count} records with {data_loss_pct:.2f}% data loss"

def load_to_warehouse(**context):
    """Load data to data warehouse"""
    import pandas as pd
    from sqlalchemy import create_engine
    
    # Read transformed data
    df = pd.read_parquet('/tmp/pharmacy_data_transformed.parquet')
    
    # Warehouse connection
    engine = create_engine('postgresql://user:pass@warehouse:5432/analytics_db')
    
    # Load to warehouse
    df.to_sql('pharmacy_sales_fact', engine, if_exists='append', index=False)
    
    # Update metadata
    metadata_query = """
    INSERT INTO etl_metadata (table_name, load_date, record_count, status)
    VALUES ('pharmacy_sales_fact', CURRENT_DATE, %s, 'success')
    """
    
    with engine.connect() as conn:
        conn.execute(metadata_query, (len(df),))
    
    return f"Loaded {len(df)} records to warehouse"

# Task definitions
extract_task = PythonOperator(
    task_id='extract_pharmacy_data',
    python_callable=extract_pharmacy_data,
    dag=dag
)

transform_task = PythonOperator(
    task_id='transform_data',
    python_callable=transform_data,
    dag=dag
)

load_task = PythonOperator(
    task_id='load_to_warehouse',
    python_callable=load_to_warehouse,
    dag=dag
)

# Data quality check
quality_check = PostgresOperator(
    task_id='data_quality_check',
    postgres_conn_id='warehouse_conn',
    sql="""
    SELECT 
        COUNT(*) as record_count,
        COUNT(DISTINCT customer_id) as unique_customers,
        SUM(amount) as total_amount
    FROM pharmacy_sales_fact
    WHERE load_date = CURRENT_DATE
    """,
    dag=dag
)

# Notification task
def send_success_notification(**context):
    """Send success notification"""
    record_count = context['task_instance'].xcom_pull(task_ids='extract_pharmacy_data', key='record_count')
    
    message = f"""
    Pharmacy Data Pipeline Completed Successfully!
    
    Records Processed: {record_count}
    Execution Date: {context['ds']}
    Duration: {context['task_instance'].duration}
    """
    
    # Send notification (Slack, email, etc.)
    print(message)

notification_task = PythonOperator(
    task_id='send_notification',
    python_callable=send_success_notification,
    dag=dag
)

# Task dependencies
extract_task >> transform_task >> load_task >> quality_check >> notification_task
```

### Advanced Airflow Patterns
**Krishna's Production Patterns:**

```python
# Dynamic task generation
def create_dynamic_tasks():
    """Create tasks dynamically based on data sources"""
    sources = ['pharmacy', 'supply_chain', 'customer', 'inventory']
    
    for source in sources:
        extract_task = PythonOperator(
            task_id=f'extract_{source}_data',
            python_callable=lambda src=source: extract_data(src),
            dag=dag
        )
        
        transform_task = PythonOperator(
            task_id=f'transform_{source}_data',
            python_callable=lambda src=source: transform_data(src),
            dag=dag
        )
        
        extract_task >> transform_task

# Conditional execution
def check_data_availability(**context):
    """Check if source data is available"""
    # Check if source files exist
    source_files = ['/data/pharmacy.csv', '/data/supply_chain.csv']
    
    available_files = [f for f in source_files if os.path.exists(f)]
    
    if len(available_files) == 0:
        raise AirflowSkipException("No source data available")
    
    return available_files

# Sensor for file availability
file_sensor = FileSensor(
    task_id='wait_for_data',
    filepath='/data/',
    fs_conn_id='data_fs',
    poke_interval=30,
    timeout=3600,
    dag=dag
)

# Branching based on data quality
def data_quality_branch(**context):
    """Branch based on data quality results"""
    quality_score = context['task_instance'].xcom_pull(task_ids='quality_check')
    
    if quality_score > 0.95:
        return 'high_quality_path'
    elif quality_score > 0.85:
        return 'medium_quality_path'
    else:
        return 'low_quality_path'

branch_task = BranchPythonOperator(
    task_id='data_quality_branch',
    python_callable=data_quality_branch,
    dag=dag
)
```

## Data Processing with NumPy

### Performance Optimization
**Krishna's High-Performance Computing:**

```python
import numpy as np
import pandas as pd
from numba import jit, prange

# Vectorized operations for large datasets
def calculate_customer_metrics_vectorized(transactions):
    """Calculate customer metrics using vectorized operations"""
    
    # Convert to numpy arrays for speed
    customer_ids = transactions['customer_id'].values
    amounts = transactions['amount'].values
    dates = pd.to_datetime(transactions['order_date']).values
    
    # Unique customers
    unique_customers = np.unique(customer_ids)
    
    # Initialize result arrays
    n_customers = len(unique_customers)
    total_spent = np.zeros(n_customers)
    order_count = np.zeros(n_customers)
    last_order_date = np.zeros(n_customers, dtype='datetime64[D]')
    
    # Vectorized calculations
    for i, customer_id in enumerate(unique_customers):
        mask = customer_ids == customer_id
        total_spent[i] = np.sum(amounts[mask])
        order_count[i] = np.sum(mask)
        last_order_date[i] = np.max(dates[mask])
    
    # Create result DataFrame
    result = pd.DataFrame({
        'customer_id': unique_customers,
        'total_spent': total_spent,
        'order_count': order_count,
        'last_order_date': last_order_date
    })
    
    return result

# Numba JIT compilation for even faster execution
@jit(nopython=True, parallel=True)
def calculate_rolling_average_numba(values, window_size):
    """Calculate rolling average using Numba JIT"""
    n = len(values)
    result = np.zeros(n)
    
    for i in prange(n):
        start_idx = max(0, i - window_size + 1)
        window_values = values[start_idx:i+1]
        result[i] = np.mean(window_values)
    
    return result

# Memory-efficient processing for large datasets
def process_large_dataset_chunked(file_path, chunk_size=10000):
    """Process large datasets in chunks to manage memory"""
    
    results = []
    
    for chunk in pd.read_csv(file_path, chunksize=chunk_size):
        # Process chunk
        chunk_processed = chunk.groupby('customer_id').agg({
            'amount': ['sum', 'count', 'mean'],
            'order_date': 'max'
        }).reset_index()
        
        # Flatten column names
        chunk_processed.columns = ['customer_id', 'total_spent', 'order_count', 'avg_amount', 'last_order']
        
        results.append(chunk_processed)
    
    # Combine results
    final_result = pd.concat(results, ignore_index=True)
    
    # Final aggregation
    final_result = final_result.groupby('customer_id').agg({
        'total_spent': 'sum',
        'order_count': 'sum',
        'avg_amount': 'mean',
        'last_order': 'max'
    }).reset_index()
    
    return final_result
```

## Error Handling and Logging

### Production-Grade Error Handling
**Krishna's Robust Error Management:**

```python
import logging
import traceback
from functools import wraps
from typing import Optional, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data_pipeline.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def retry_on_failure(max_retries: int = 3, delay: int = 5):
    """Decorator for retrying failed operations"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")
                    if attempt == max_retries - 1:
                        logger.error(f"All {max_retries} attempts failed")
                        raise
                    time.sleep(delay)
            return None
        return wrapper
    return decorator

class DataPipelineError(Exception):
    """Custom exception for data pipeline errors"""
    pass

class DataQualityError(DataPipelineError):
    """Exception for data quality issues"""
    pass

def validate_data_quality(df: pd.DataFrame, rules: Dict[str, Any]) -> bool:
    """Validate data quality against business rules"""
    errors = []
    
    for column, rule in rules.items():
        if column not in df.columns:
            errors.append(f"Missing column: {column}")
            continue
        
        if 'not_null' in rule and df[column].isnull().any():
            errors.append(f"Null values found in {column}")
        
        if 'min_value' in rule and (df[column] < rule['min_value']).any():
            errors.append(f"Values below minimum in {column}")
        
        if 'max_value' in rule and (df[column] > rule['max_value']).any():
            errors.append(f"Values above maximum in {column}")
    
    if errors:
        raise DataQualityError(f"Data quality validation failed: {'; '.join(errors)}")
    
    return True

@retry_on_failure(max_retries=3)
def process_data_with_validation(file_path: str) -> pd.DataFrame:
    """Process data with comprehensive validation and error handling"""
    
    try:
        logger.info(f"Starting data processing for {file_path}")
        
        # Read data
        df = pd.read_csv(file_path)
        logger.info(f"Loaded {len(df)} records")
        
        # Data quality rules
        quality_rules = {
            'customer_id': {'not_null': True, 'min_value': 1},
            'amount': {'not_null': True, 'min_value': 0},
            'order_date': {'not_null': True}
        }
        
        # Validate data quality
        validate_data_quality(df, quality_rules)
        logger.info("Data quality validation passed")
        
        # Process data
        df_processed = df.copy()
        df_processed['processed_date'] = datetime.now()
        
        logger.info(f"Successfully processed {len(df_processed)} records")
        return df_processed
        
    except DataQualityError as e:
        logger.error(f"Data quality error: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        logger.error(traceback.format_exc())
        raise DataPipelineError(f"Data processing failed: {str(e)}")
```

## Krishna's Production Best Practices

### Code Organization and Testing
```python
# Project structure
"""
data_pipeline/
├── src/
│   ├── extractors/
│   ├── transformers/
│   ├── loaders/
│   └── validators/
├── tests/
├── config/
├── logs/
└── requirements.txt
"""

# Configuration management
import yaml
from dataclasses import dataclass
from typing import Dict, List

@dataclass
class PipelineConfig:
    """Configuration class for data pipeline"""
    source_db_url: str
    target_db_url: str
    batch_size: int = 10000
    max_retries: int = 3
    quality_threshold: float = 0.95
    
    @classmethod
    def from_yaml(cls, config_path: str):
        """Load configuration from YAML file"""
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)
        return cls(**config_data)

# Unit testing
import unittest
import pandas as pd
from unittest.mock import patch, MagicMock

class TestDataQualityValidator(unittest.TestCase):
    """Test cases for data quality validator"""
    
    def setUp(self):
        self.sample_data = pd.DataFrame({
            'customer_id': [1, 2, 3, None, 5],
            'amount': [100, 200, -50, 300, 150],
            'order_date': ['2023-01-01', '2023-01-02', '2023-01-03', '2023-01-04', '2023-01-05']
        })
    
    def test_null_value_detection(self):
        """Test null value detection"""
        validator = DataQualityValidator(self.sample_data)
        report = validator.check_null_values().generate_report()
        
        self.assertIn('customer_id', report['null_values'])
        self.assertEqual(report['null_values']['customer_id'], 1)
    
    def test_business_rule_validation(self):
        """Test business rule validation"""
        validator = DataQualityValidator(self.sample_data)
        report = validator.check_business_rules().generate_report()
        
        self.assertIn('negative_amounts', report['business_rule_violations'])
        self.assertEqual(report['business_rule_violations']['negative_amounts'], 1)

# Performance monitoring
import time
import psutil
from contextlib import contextmanager

@contextmanager
def performance_monitor(operation_name: str):
    """Context manager for performance monitoring"""
    start_time = time.time()
    start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
    
    logger.info(f"Starting {operation_name}")
    
    try:
        yield
    finally:
        end_time = time.time()
        end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        duration = end_time - start_time
        memory_used = end_memory - start_memory
        
        logger.info(f"Completed {operation_name} in {duration:.2f}s, used {memory_used:.2f}MB")

# Usage example
with performance_monitor("data_processing"):
    result = process_data_with_validation("data.csv")
```

## Interview-Ready Python Patterns

### Common Data Engineering Interview Questions

**1. Data Deduplication:**
```python
def remove_duplicates_keep_latest(df, key_columns, date_column):
    """Remove duplicates keeping the latest record"""
    return df.sort_values(date_column).drop_duplicates(subset=key_columns, keep='last')

# Usage
df_clean = remove_duplicates_keep_latest(
    df, 
    key_columns=['customer_id', 'product_id'], 
    date_column='order_date'
)
```

**2. Data Aggregation with Custom Functions:**
```python
def custom_aggregation(group):
    """Custom aggregation function"""
    return pd.Series({
        'total_amount': group['amount'].sum(),
        'avg_amount': group['amount'].mean(),
        'order_count': len(group),
        'first_order': group['order_date'].min(),
        'last_order': group['order_date'].max(),
        'unique_products': group['product_id'].nunique()
    })

# Apply custom aggregation
customer_metrics = df.groupby('customer_id').apply(custom_aggregation)
```

**3. Time Series Resampling:**
```python
def resample_time_series(df, freq='D', agg_func='sum'):
    """Resample time series data"""
    df_indexed = df.set_index('order_date')
    return df_indexed.resample(freq)['amount'].agg(agg_func)

# Usage
daily_sales = resample_time_series(df, freq='D', agg_func='sum')
monthly_sales = resample_time_series(df, freq='M', agg_func='mean')
```

## Krishna's Performance Achievements

### Real-World Optimizations:
1. **Pandas Optimization**: Reduced data processing time by 60% using vectorized operations
2. **Memory Management**: Processed 10TB+ datasets using chunked processing
3. **Airflow Orchestration**: Achieved 99.5% pipeline success rate
4. **Error Handling**: Reduced production incidents by 80% with robust error management
5. **Code Quality**: 95% test coverage with comprehensive unit tests

### Tools and Technologies:
- **Python Libraries**: Pandas, NumPy, SQLAlchemy, Airflow, Pytest
- **Data Formats**: Parquet, CSV, JSON, Avro
- **Databases**: PostgreSQL, MySQL, SQL Server
- **Cloud Platforms**: AWS, Azure
- **Monitoring**: Logging, Metrics, Alerting
