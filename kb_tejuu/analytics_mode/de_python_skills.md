---
tags: [data-engineer, python, pandas, numpy, sql, programming, tejuu]
persona: analytics
---

# Python Skills for Data Engineering - Tejuu's Experience

## Introduction
**Tejuu's Python Journey:**
At Central Bank of Missouri, I use Python extensively for data processing, ETL pipelines, and analytics. I've built automated data migration scripts, data quality validation frameworks, and integration tools using Python. My Python skills complement my SQL and Power BI expertise, making me a well-rounded data engineer. Let me share the Python patterns and best practices I've learned.

## Core Python Libraries

### 1. Pandas for Data Processing
**Tejuu's Pandas Patterns:**

```python
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

# Data processing with pandas
class BankingDataProcessor:
    def __init__(self):
        self.logger = self.setup_logging()
    
    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)
    
    def process_customer_data(self, df):
        """Process customer data with data quality checks"""
        self.logger.info(f"Processing {len(df)} customer records")
        
        # Data type conversions
        df['customer_id'] = df['customer_id'].astype('string')
        df['created_date'] = pd.to_datetime(df['created_date'], errors='coerce')
        df['balance'] = pd.to_numeric(df['balance'], errors='coerce')
        
        # Data cleaning
        df_clean = (
            df
            .dropna(subset=['customer_id', 'customer_name'])
            .drop_duplicates(subset=['customer_id'])
            .reset_index(drop=True)
        )
        
        # Data validation
        validation_results = self.validate_customer_data(df_clean)
        if validation_results['errors']:
            self.logger.warning(f"Found {len(validation_results['errors'])} validation errors")
        
        return df_clean, validation_results
    
    def validate_customer_data(self, df):
        """Validate customer data quality"""
        errors = []
        
        # Check for required fields
        required_fields = ['customer_id', 'customer_name', 'created_date']
        for field in required_fields:
            if field not in df.columns:
                errors.append(f"Missing required field: {field}")
        
        # Check for null values in critical fields
        null_counts = df[required_fields].isnull().sum()
        for field, count in null_counts.items():
            if count > 0:
                errors.append(f"Found {count} null values in {field}")
        
        # Check data formats
        if 'customer_id' in df.columns:
            invalid_ids = df[~df['customer_id'].str.match(r'^CUST\d{8}$', na=False)]
            if len(invalid_ids) > 0:
                errors.append(f"Found {len(invalid_ids)} invalid customer IDs")
        
        return {'errors': errors, 'error_count': len(errors)}
    
    def calculate_customer_metrics(self, df):
        """Calculate customer analytics metrics"""
        metrics = {
            'total_customers': len(df),
            'unique_customers': df['customer_id'].nunique(),
            'avg_balance': df['balance'].mean(),
            'median_balance': df['balance'].median(),
            'balance_std': df['balance'].std(),
            'date_range': {
                'earliest': df['created_date'].min(),
                'latest': df['created_date'].max()
            }
        }
        
        return metrics
```

### 2. NumPy for Numerical Operations
**Tejuu's NumPy Patterns:**

```python
import numpy as np

# Numerical data processing
class NumericalDataProcessor:
    def __init__(self):
        self.nan_threshold = 0.1  # 10% threshold for missing data
    
    def process_financial_data(self, df):
        """Process financial data with numerical operations"""
        # Convert to numpy arrays for performance
        amounts = df['amount'].values
        balances = df['balance'].values
        
        # Statistical calculations
        stats = {
            'mean_amount': np.mean(amounts),
            'median_amount': np.median(amounts),
            'std_amount': np.std(amounts),
            'percentile_95': np.percentile(amounts, 95),
            'percentile_99': np.percentile(amounts, 99)
        }
        
        # Outlier detection using IQR
        Q1 = np.percentile(amounts, 25)
        Q3 = np.percentile(amounts, 75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        outliers = df[(amounts < lower_bound) | (amounts > upper_bound)]
        
        return stats, outliers
    
    def calculate_risk_metrics(self, df):
        """Calculate risk metrics using numpy"""
        amounts = df['amount'].values
        frequencies = df['frequency'].values
        
        # Value at Risk (VaR) calculation
        var_95 = np.percentile(amounts, 5)  # 95% VaR
        var_99 = np.percentile(amounts, 1)  # 99% VaR
        
        # Expected Shortfall (Conditional VaR)
        es_95 = np.mean(amounts[amounts <= var_95])
        es_99 = np.mean(amounts[amounts <= var_99])
        
        # Volatility calculation
        returns = np.diff(amounts) / amounts[:-1]
        volatility = np.std(returns) * np.sqrt(252)  # Annualized
        
        risk_metrics = {
            'var_95': var_95,
            'var_99': var_99,
            'es_95': es_95,
            'es_99': es_99,
            'volatility': volatility
        }
        
        return risk_metrics
```

### 3. SQL Integration with Python
**Tejuu's SQL Integration Patterns:**

```python
import pyodbc
import sqlalchemy
from sqlalchemy import create_engine, text
import pandas as pd

# SQL Server integration
class SQLServerConnector:
    def __init__(self, connection_string):
        self.connection_string = connection_string
        self.engine = create_engine(connection_string)
    
    def execute_query(self, query, params=None):
        """Execute SQL query and return DataFrame"""
        try:
            df = pd.read_sql(query, self.engine, params=params)
            return df
        except Exception as e:
            print(f"Error executing query: {e}")
            return None
    
    def execute_stored_procedure(self, sp_name, params=None):
        """Execute stored procedure"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(f"EXEC {sp_name}"), params or {})
                return result.fetchall()
        except Exception as e:
            print(f"Error executing stored procedure: {e}")
            return None
    
    def bulk_insert(self, df, table_name, if_exists='append'):
        """Bulk insert DataFrame to SQL Server"""
        try:
            df.to_sql(table_name, self.engine, if_exists=if_exists, index=False, method='multi')
            print(f"Successfully inserted {len(df)} records to {table_name}")
        except Exception as e:
            print(f"Error inserting data: {e}")

# Azure SQL Database integration
class AzureSQLConnector:
    def __init__(self, server, database, username, password):
        self.connection_string = (
            f"mssql+pyodbc://{username}:{password}@{server}.database.windows.net/"
            f"{database}?driver=ODBC+Driver+17+for+SQL+Server"
        )
        self.engine = create_engine(self.connection_string)
    
    def get_customer_data(self, customer_id=None):
        """Get customer data with optional filtering"""
        if customer_id:
            query = "SELECT * FROM customers WHERE customer_id = :customer_id"
            params = {'customer_id': customer_id}
        else:
            query = "SELECT * FROM customers"
            params = None
        
        return self.execute_query(query, params)
    
    def update_customer_balance(self, customer_id, new_balance):
        """Update customer balance"""
        query = """
        UPDATE customers 
        SET balance = :new_balance, 
            updated_at = GETDATE()
        WHERE customer_id = :customer_id
        """
        params = {
            'customer_id': customer_id,
            'new_balance': new_balance
        }
        
        with self.engine.connect() as conn:
            result = conn.execute(text(query), params)
            conn.commit()
            return result.rowcount
```

## Data Engineering Patterns

### 1. ETL Pipeline Framework
**Tejuu's ETL Framework:**

```python
from abc import ABC, abstractmethod
import logging
from datetime import datetime
import json

# Abstract ETL pipeline base class
class ETLPipeline(ABC):
    def __init__(self, config_file):
        self.config = self.load_config(config_file)
        self.logger = self.setup_logging()
        self.start_time = datetime.now()
    
    def load_config(self, config_file):
        """Load configuration from JSON file"""
        with open(config_file, 'r') as f:
            return json.load(f)
    
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('etl_pipeline.log'),
                logging.StreamHandler()
            ]
        )
        return logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    def extract(self):
        """Extract data from source"""
        pass
    
    @abstractmethod
    def transform(self, data):
        """Transform data"""
        pass
    
    @abstractmethod
    def load(self, data):
        """Load data to target"""
        pass
    
    def run(self):
        """Run the complete ETL pipeline"""
        try:
            self.logger.info("Starting ETL pipeline")
            
            # Extract
            raw_data = self.extract()
            self.logger.info(f"Extracted {len(raw_data)} records")
            
            # Transform
            transformed_data = self.transform(raw_data)
            self.logger.info(f"Transformed {len(transformed_data)} records")
            
            # Load
            self.load(transformed_data)
            self.logger.info("Data loaded successfully")
            
            # Calculate runtime
            runtime = datetime.now() - self.start_time
            self.logger.info(f"ETL pipeline completed in {runtime}")
            
        except Exception as e:
            self.logger.error(f"ETL pipeline failed: {e}")
            raise

# Concrete implementation for banking data
class BankingETLPipeline(ETLPipeline):
    def __init__(self, config_file):
        super().__init__(config_file)
        self.sql_connector = SQLServerConnector(self.config['source_connection'])
        self.target_connector = AzureSQLConnector(**self.config['target_connection'])
    
    def extract(self):
        """Extract banking data from SQL Server"""
        query = """
        SELECT 
            customer_id,
            customer_name,
            balance,
            created_date,
            updated_date
        FROM customers
        WHERE updated_date >= DATEADD(day, -1, GETDATE())
        """
        
        return self.sql_connector.execute_query(query)
    
    def transform(self, data):
        """Transform banking data"""
        # Data cleaning
        data_clean = data.dropna(subset=['customer_id', 'customer_name'])
        
        # Data type conversions
        data_clean['created_date'] = pd.to_datetime(data_clean['created_date'])
        data_clean['updated_date'] = pd.to_datetime(data_clean['updated_date'])
        data_clean['balance'] = pd.to_numeric(data_clean['balance'], errors='coerce')
        
        # Business logic transformations
        data_clean['customer_segment'] = data_clean['balance'].apply(self.categorize_customer)
        data_clean['risk_score'] = data_clean.apply(self.calculate_risk_score, axis=1)
        data_clean['processed_at'] = datetime.now()
        
        return data_clean
    
    def load(self, data):
        """Load data to Azure SQL Database"""
        self.target_connector.bulk_insert(data, 'customers_processed')
    
    def categorize_customer(self, balance):
        """Categorize customer based on balance"""
        if balance >= 100000:
            return 'Premium'
        elif balance >= 50000:
            return 'Gold'
        elif balance >= 10000:
            return 'Silver'
        else:
            return 'Bronze'
    
    def calculate_risk_score(self, row):
        """Calculate risk score for customer"""
        balance = row['balance']
        if balance < 1000:
            return 'High'
        elif balance < 10000:
            return 'Medium'
        else:
            return 'Low'
```

### 2. Data Quality Framework
**Tejuu's Data Quality Patterns:**

```python
# Data quality validation framework
class DataQualityFramework:
    def __init__(self):
        self.quality_rules = {}
        self.validation_results = {}
    
    def add_quality_rule(self, rule_name, rule_function):
        """Add a data quality rule"""
        self.quality_rules[rule_name] = rule_function
    
    def validate_dataframe(self, df, table_name):
        """Validate DataFrame against all quality rules"""
        validation_results = {
            'table_name': table_name,
            'total_records': len(df),
            'validation_timestamp': datetime.now(),
            'rules': {}
        }
        
        for rule_name, rule_function in self.quality_rules.items():
            try:
                rule_result = rule_function(df)
                validation_results['rules'][rule_name] = rule_result
            except Exception as e:
                validation_results['rules'][rule_name] = {
                    'status': 'ERROR',
                    'error': str(e)
                }
        
        self.validation_results[table_name] = validation_results
        return validation_results
    
    def generate_quality_report(self, table_name):
        """Generate data quality report"""
        if table_name not in self.validation_results:
            return "No validation results found for this table"
        
        results = self.validation_results[table_name]
        report = f"""
        Data Quality Report for {table_name}
        =====================================
        Total Records: {results['total_records']:,}
        Validation Time: {results['validation_timestamp']}
        
        Rule Results:
        """
        
        for rule_name, rule_result in results['rules'].items():
            status = rule_result.get('status', 'UNKNOWN')
            report += f"  {rule_name}: {status}\n"
            
            if 'errors' in rule_result:
                report += f"    Errors: {len(rule_result['errors'])}\n"
            if 'warnings' in rule_result:
                report += f"    Warnings: {len(rule_result['warnings'])}\n"
        
        return report

# Specific quality rules for banking data
class BankingDataQualityRules:
    @staticmethod
    def check_completeness(df):
        """Check data completeness"""
        required_fields = ['customer_id', 'customer_name', 'balance']
        errors = []
        
        for field in required_fields:
            if field in df.columns:
                null_count = df[field].isnull().sum()
                if null_count > 0:
                    errors.append(f"Field {field} has {null_count} null values")
        
        return {
            'status': 'PASS' if not errors else 'FAIL',
            'errors': errors
        }
    
    @staticmethod
    def check_data_types(df):
        """Check data types"""
        errors = []
        
        if 'balance' in df.columns:
            if not pd.api.types.is_numeric_dtype(df['balance']):
                errors.append("Balance field is not numeric")
        
        if 'created_date' in df.columns:
            if not pd.api.types.is_datetime64_any_dtype(df['created_date']):
                errors.append("Created date field is not datetime")
        
        return {
            'status': 'PASS' if not errors else 'FAIL',
            'errors': errors
        }
    
    @staticmethod
    def check_business_rules(df):
        """Check business rules"""
        errors = []
        
        if 'balance' in df.columns:
            # Check for negative balances
            negative_balances = df[df['balance'] < 0]
            if len(negative_balances) > 0:
                errors.append(f"Found {len(negative_balances)} negative balances")
            
            # Check for unrealistic balances
            unrealistic_balances = df[df['balance'] > 10000000]  # 10M threshold
            if len(unrealistic_balances) > 0:
                errors.append(f"Found {len(unrealistic_balances)} unrealistic balances")
        
        return {
            'status': 'PASS' if not errors else 'FAIL',
            'errors': errors
        }
```

### 3. API Integration
**Tejuu's API Integration Patterns:**

```python
import requests
import json
from datetime import datetime
import time

# API integration for external data sources
class BankingAPIClient:
    def __init__(self, base_url, api_key):
        self.base_url = base_url
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        })
    
    def get_customer_data(self, customer_id):
        """Get customer data from API"""
        url = f"{self.base_url}/customers/{customer_id}"
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching customer data: {e}")
            return None
    
    def get_transaction_data(self, start_date, end_date, page=1, limit=1000):
        """Get transaction data with pagination"""
        url = f"{self.base_url}/transactions"
        params = {
            'start_date': start_date,
            'end_date': end_date,
            'page': page,
            'limit': limit
        }
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching transaction data: {e}")
            return None
    
    def get_all_transaction_data(self, start_date, end_date):
        """Get all transaction data with automatic pagination"""
        all_data = []
        page = 1
        
        while True:
            data = self.get_transaction_data(start_date, end_date, page)
            if not data or not data.get('transactions'):
                break
            
            all_data.extend(data['transactions'])
            page += 1
            
            # Rate limiting
            time.sleep(0.1)
        
        return all_data

# Data processing for API data
class APIDataProcessor:
    def __init__(self, api_client):
        self.api_client = api_client
    
    def process_customer_api_data(self, customer_id):
        """Process customer data from API"""
        raw_data = self.api_client.get_customer_data(customer_id)
        if not raw_data:
            return None
        
        # Transform API response to DataFrame
        df = pd.DataFrame([raw_data])
        
        # Data cleaning and transformation
        df_processed = (
            df
            .assign(
                customer_id=df['id'],
                created_date=pd.to_datetime(df['created_at']),
                updated_date=pd.to_datetime(df['updated_at'])
            )
            .drop(columns=['id', 'created_at', 'updated_at'])
        )
        
        return df_processed
    
    def process_transaction_api_data(self, start_date, end_date):
        """Process transaction data from API"""
        raw_data = self.api_client.get_all_transaction_data(start_date, end_date)
        if not raw_data:
            return pd.DataFrame()
        
        # Convert to DataFrame
        df = pd.DataFrame(raw_data)
        
        # Data transformation
        df_processed = (
            df
            .assign(
                transaction_date=pd.to_datetime(df['date']),
                amount=pd.to_numeric(df['amount'], errors='coerce')
            )
            .drop(columns=['date'])
            .dropna(subset=['amount'])
        )
        
        return df_processed
```

## Performance Optimization

### 1. Memory Management
**Tejuu's Memory Optimization Patterns:**

```python
import gc
import psutil
import os

# Memory optimization for large datasets
class MemoryOptimizer:
    def __init__(self):
        self.memory_threshold = 0.8  # 80% memory usage threshold
    
    def check_memory_usage(self):
        """Check current memory usage"""
        memory_percent = psutil.virtual_memory().percent
        return memory_percent
    
    def optimize_dataframe_memory(self, df):
        """Optimize DataFrame memory usage"""
        initial_memory = df.memory_usage(deep=True).sum() / 1024**2  # MB
        
        # Optimize numeric columns
        for col in df.select_dtypes(include=['int64']).columns:
            df[col] = pd.to_numeric(df[col], downcast='integer')
        
        for col in df.select_dtypes(include=['float64']).columns:
            df[col] = pd.to_numeric(df[col], downcast='float')
        
        # Optimize object columns
        for col in df.select_dtypes(include=['object']).columns:
            if df[col].dtype == 'object':
                df[col] = df[col].astype('category')
        
        final_memory = df.memory_usage(deep=True).sum() / 1024**2  # MB
        reduction = (initial_memory - final_memory) / initial_memory * 100
        
        print(f"Memory usage reduced by {reduction:.1f}% ({initial_memory:.1f}MB -> {final_memory:.1f}MB)")
        
        return df
    
    def process_large_file_in_chunks(self, file_path, chunk_size=10000):
        """Process large file in chunks to manage memory"""
        chunk_list = []
        
        for chunk in pd.read_csv(file_path, chunksize=chunk_size):
            # Process chunk
            processed_chunk = self.process_chunk(chunk)
            chunk_list.append(processed_chunk)
            
            # Check memory usage
            if self.check_memory_usage() > self.memory_threshold:
                # Combine chunks and save intermediate result
                combined_df = pd.concat(chunk_list, ignore_index=True)
                self.save_intermediate_result(combined_df)
                chunk_list = []
                gc.collect()
        
        # Combine remaining chunks
        if chunk_list:
            final_df = pd.concat(chunk_list, ignore_index=True)
            return final_df
        
        return None
```

### 2. Parallel Processing
**Tejuu's Parallel Processing Patterns:**

```python
from multiprocessing import Pool, cpu_count
import concurrent.futures
from functools import partial

# Parallel processing for data operations
class ParallelDataProcessor:
    def __init__(self, max_workers=None):
        self.max_workers = max_workers or cpu_count()
    
    def process_data_parallel(self, data_list, process_function):
        """Process data in parallel"""
        with Pool(self.max_workers) as pool:
            results = pool.map(process_function, data_list)
        return results
    
    def process_files_parallel(self, file_paths, process_function):
        """Process multiple files in parallel"""
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [executor.submit(process_function, file_path) for file_path in file_paths]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        return results
    
    def process_dataframe_parallel(self, df, process_function, partition_size=1000):
        """Process DataFrame in parallel partitions"""
        # Split DataFrame into partitions
        partitions = [df.iloc[i:i+partition_size] for i in range(0, len(df), partition_size)]
        
        # Process partitions in parallel
        with Pool(self.max_workers) as pool:
            processed_partitions = pool.map(process_function, partitions)
        
        # Combine results
        return pd.concat(processed_partitions, ignore_index=True)

# Example usage
def process_customer_chunk(chunk_df):
    """Process a chunk of customer data"""
    # Apply transformations
    processed_chunk = (
        chunk_df
        .assign(
            customer_segment=chunk_df['balance'].apply(categorize_customer),
            risk_score=chunk_df.apply(calculate_risk_score, axis=1)
        )
    )
    return processed_chunk

def categorize_customer(balance):
    """Categorize customer based on balance"""
    if balance >= 100000:
        return 'Premium'
    elif balance >= 50000:
        return 'Gold'
    elif balance >= 10000:
        return 'Silver'
    else:
        return 'Bronze'

def calculate_risk_score(row):
    """Calculate risk score for customer"""
    balance = row['balance']
    if balance < 1000:
        return 'High'
    elif balance < 10000:
        return 'Medium'
    else:
        return 'Low'
```

My Python skills help build robust, efficient, and maintainable data engineering solutions that integrate seamlessly with enterprise data platforms!
