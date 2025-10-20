---
tags: [analytics-engineer, coding, interview, python, sql, pandas, dbt]
persona: analytics
---

# Analytics Engineering Coding Interview Guide - Tejuu's Approach

## Introduction
**Tejuu's Coding Interview Philosophy:**
Having solved hundreds of data problems and built analytics pipelines, I approach coding interviews by focusing on clean, efficient solutions with clear business context. My experience with Python, SQL, and dbt gives me practical insights into solving problems that mirror real-world analytics challenges.

## Core Python Skills for Analytics

### 1. Data Manipulation with Pandas
**Tejuu's Essential Patterns:**

#### Data Cleaning & Transformation
```python
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def clean_customer_data(df):
    """Clean and standardize customer data"""
    return (df
        # Remove duplicates
        .drop_duplicates(subset='customer_id', keep='last')
        
        # Clean text fields
        .assign(
            email=lambda x: x['email'].str.lower().str.strip(),
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
        
        # Create derived fields
        .assign(
            full_name=lambda x: x['first_name'] + ' ' + x['last_name'],
            customer_tenure_days=lambda x: (datetime.now() - x['registration_date']).dt.days
        )
    )

# Example usage
customers_df = pd.read_csv('customers.csv')
clean_customers = clean_customer_data(customers_df)
```

#### Aggregation & Grouping
```python
def calculate_customer_metrics(df):
    """Calculate customer-level metrics"""
    return (df
        .groupby('customer_id')
        .agg({
            'order_id': 'count',           # Total orders
            'order_amount': ['sum', 'mean', 'std'],  # Revenue metrics
            'order_date': ['min', 'max']   # First and last order
        })
        .round(2)
        .reset_index()
    )

def calculate_cohort_analysis(df):
    """Calculate customer cohort metrics"""
    # Get first order date for each customer
    first_orders = df.groupby('customer_id')['order_date'].min().reset_index()
    first_orders.columns = ['customer_id', 'first_order_date']
    
    # Merge with original data
    df_with_cohort = df.merge(first_orders, on='customer_id')
    
    # Calculate cohort month
    df_with_cohort['cohort_month'] = df_with_cohort['first_order_date'].dt.to_period('M')
    df_with_cohort['order_month'] = df_with_cohort['order_date'].dt.to_period('M')
    
    # Calculate period number
    df_with_cohort['period_number'] = (
        df_with_cohort['order_month'] - df_with_cohort['cohort_month']
    ).apply(attrgetter('n'))
    
    # Group by cohort and period
    cohort_data = (df_with_cohort
        .groupby(['cohort_month', 'period_number'])
        .agg({
            'customer_id': 'nunique',
            'order_amount': 'sum'
        })
        .reset_index()
    )
    
    return cohort_data
```

### 2. SQL for Analytics
**Tejuu's SQL Patterns:**

#### Window Functions
```sql
-- Customer lifetime value calculation
WITH customer_orders AS (
    SELECT 
        customer_id,
        order_date,
        order_amount,
        ROW_NUMBER() OVER (
            PARTITION BY customer_id 
            ORDER BY order_date
        ) AS order_number,
        SUM(order_amount) OVER (
            PARTITION BY customer_id 
            ORDER BY order_date
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) AS running_total
    FROM orders
    WHERE order_status = 'completed'
)
SELECT 
    customer_id,
    order_date,
    order_amount,
    order_number,
    running_total AS customer_lifetime_value
FROM customer_orders;
```

#### Advanced Analytics
```sql
-- RFM Analysis
WITH customer_metrics AS (
    SELECT 
        customer_id,
        MAX(order_date) AS last_order_date,
        COUNT(DISTINCT order_id) AS frequency,
        SUM(order_amount) AS monetary_value,
        DATEDIFF(CURRENT_DATE, MAX(order_date)) AS recency_days
    FROM orders
    WHERE order_date >= DATEADD(month, -12, CURRENT_DATE)
    GROUP BY customer_id
),
rfm_scores AS (
    SELECT 
        customer_id,
        recency_days,
        frequency,
        monetary_value,
        NTILE(5) OVER (ORDER BY recency_days DESC) AS recency_score,
        NTILE(5) OVER (ORDER BY frequency) AS frequency_score,
        NTILE(5) OVER (ORDER BY monetary_value) AS monetary_score
    FROM customer_metrics
)
SELECT 
    customer_id,
    recency_days,
    frequency,
    monetary_value,
    recency_score,
    frequency_score,
    monetary_score,
    CASE 
        WHEN recency_score >= 4 AND frequency_score >= 4 THEN 'Champions'
        WHEN recency_score >= 3 AND frequency_score >= 3 THEN 'Loyal Customers'
        WHEN recency_score >= 4 AND frequency_score <= 2 THEN 'Promising'
        WHEN recency_score <= 2 AND frequency_score >= 3 THEN 'At Risk'
        WHEN recency_score <= 2 AND frequency_score <= 2 THEN 'Lost'
        ELSE 'Others'
    END AS customer_segment
FROM rfm_scores;
```

### 3. dbt Modeling Patterns
**Tejuu's dbt Examples:**

#### Staging Model
```sql
-- models/staging/stg_orders.sql
{{
    config(
        materialized='view',
        schema='staging'
    )
}}

WITH source AS (
    SELECT * FROM {{ source('raw', 'orders') }}
),

renamed AS (
    SELECT
        order_id,
        customer_id,
        product_id,
        order_date,
        order_amount,
        order_status,
        created_at,
        updated_at
    FROM source
    WHERE order_id IS NOT NULL
)

SELECT * FROM renamed
```

#### Intermediate Model
```sql
-- models/intermediate/int_customer_orders.sql
{{
    config(
        materialized='ephemeral'
    )
}}

WITH customers AS (
    SELECT * FROM {{ ref('stg_customers') }}
),

orders AS (
    SELECT * FROM {{ ref('stg_orders') }}
),

customer_orders AS (
    SELECT
        c.customer_id,
        c.customer_name,
        c.customer_segment,
        o.order_id,
        o.order_date,
        o.order_amount,
        o.order_status
    FROM customers c
    LEFT JOIN orders o ON c.customer_id = o.customer_id
)

SELECT * FROM customer_orders
```

#### Mart Model
```sql
-- models/marts/finance/fct_revenue.sql
{{
    config(
        materialized='incremental',
        unique_key='order_id',
        schema='finance'
    )
}}

WITH customer_orders AS (
    SELECT * FROM {{ ref('int_customer_orders') }}
),

revenue_metrics AS (
    SELECT
        order_id,
        customer_id,
        order_date,
        order_amount,
        
        -- Time dimensions
        DATE_TRUNC('month', order_date) AS order_month,
        DATE_TRUNC('quarter', order_date) AS order_quarter,
        DATE_TRUNC('year', order_date) AS order_year,
        
        -- Customer metrics
        ROW_NUMBER() OVER (
            PARTITION BY customer_id 
            ORDER BY order_date
        ) AS customer_order_number,
        
        -- Revenue metrics
        SUM(order_amount) OVER (
            PARTITION BY customer_id 
            ORDER BY order_date
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) AS customer_lifetime_value,
        
        CURRENT_TIMESTAMP AS dbt_updated_at
        
    FROM customer_orders
    WHERE order_status = 'completed'
    
    {% if is_incremental() %}
        AND order_date > (SELECT MAX(order_date) FROM {{ this }})
    {% endif %}
)

SELECT * FROM revenue_metrics
```

## Common Analytics Coding Problems

### Problem 1: Build a Customer Segmentation Model
```python
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

def create_customer_segments(df):
    """Create customer segments using RFM analysis and clustering"""
    
    # Calculate RFM metrics
    rfm_data = (df
        .groupby('customer_id')
        .agg({
            'order_date': 'max',           # Recency
            'order_id': 'count',           # Frequency
            'order_amount': 'sum'          # Monetary
        })
        .reset_index()
    )
    
    # Calculate recency in days
    rfm_data['recency_days'] = (
        pd.Timestamp.now() - rfm_data['order_date']
    ).dt.days
    
    # Rename columns
    rfm_data.columns = ['customer_id', 'last_order_date', 'frequency', 'monetary', 'recency_days']
    
    # Prepare data for clustering
    clustering_data = rfm_data[['recency_days', 'frequency', 'monetary']].copy()
    
    # Handle outliers
    for column in clustering_data.columns:
        Q1 = clustering_data[column].quantile(0.25)
        Q3 = clustering_data[column].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        clustering_data[column] = clustering_data[column].clip(lower_bound, upper_bound)
    
    # Standardize features
    scaler = StandardScaler()
    scaled_data = scaler.fit_transform(clustering_data)
    
    # Apply K-means clustering
    kmeans = KMeans(n_clusters=4, random_state=42)
    clusters = kmeans.fit_predict(scaled_data)
    
    # Add clusters to data
    rfm_data['cluster'] = clusters
    
    # Define segment names based on cluster characteristics
    segment_mapping = {
        0: 'Champions',      # High recency, frequency, monetary
        1: 'At Risk',        # Low recency, high frequency, monetary
        2: 'New Customers',  # High recency, low frequency, low monetary
        3: 'Lost Customers'  # Low recency, frequency, monetary
    }
    
    rfm_data['segment'] = rfm_data['cluster'].map(segment_mapping)
    
    return rfm_data[['customer_id', 'recency_days', 'frequency', 'monetary', 'segment']]

# Example usage
orders_df = pd.read_csv('orders.csv')
segments = create_customer_segments(orders_df)
print(segments['segment'].value_counts())
```

### Problem 2: Build a Data Quality Framework
```python
import pandas as pd
import numpy as np
from typing import Dict, List, Any

class DataQualityChecker:
    def __init__(self):
        self.checks = []
        self.results = {}
    
    def add_check(self, name: str, check_func, threshold: float = 0.95):
        """Add a data quality check"""
        self.checks.append({
            'name': name,
            'function': check_func,
            'threshold': threshold
        })
        return self
    
    def run_checks(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Run all data quality checks"""
        results = {}
        
        for check in self.checks:
            try:
                score = check['function'](df)
                passed = score >= check['threshold']
                
                results[check['name']] = {
                    'score': score,
                    'passed': passed,
                    'threshold': check['threshold']
                }
                
                status = "✓ PASS" if passed else "✗ FAIL"
                print(f"{status} {check['name']}: {score:.2%} (threshold: {check['threshold']:.2%})")
                
            except Exception as e:
                results[check['name']] = {
                    'score': 0,
                    'passed': False,
                    'error': str(e)
                }
                print(f"✗ ERROR {check['name']}: {e}")
        
        self.results = results
        return results
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of all checks"""
        if not self.results:
            return {}
        
        total_checks = len(self.results)
        passed_checks = sum(1 for r in self.results.values() if r.get('passed', False))
        
        return {
            'total_checks': total_checks,
            'passed_checks': passed_checks,
            'failed_checks': total_checks - passed_checks,
            'pass_rate': passed_checks / total_checks if total_checks > 0 else 0
        }

# Define quality check functions
def completeness_check(df):
    """Check data completeness"""
    return 1 - (df.isnull().sum().sum() / (df.shape[0] * df.shape[1]))

def uniqueness_check(df, key_columns):
    """Check uniqueness of key columns"""
    return 1 - (df.duplicated(subset=key_columns).sum() / len(df))

def validity_check(df, column, valid_values):
    """Check if values are in valid set"""
    if column not in df.columns:
        return 0
    return (df[column].isin(valid_values).sum() / len(df))

def range_check(df, column, min_val, max_val):
    """Check if values are within range"""
    if column not in df.columns:
        return 0
    return ((df[column] >= min_val) & (df[column] <= max_val)).sum() / len(df)

# Example usage
def create_quality_checker():
    """Create a data quality checker for customer data"""
    checker = DataQualityChecker()
    
    checker.add_check(
        "Completeness",
        completeness_check,
        threshold=0.95
    )
    
    checker.add_check(
        "Uniqueness",
        lambda df: uniqueness_check(df, ['customer_id']),
        threshold=1.0
    )
    
    checker.add_check(
        "Email Validity",
        lambda df: validity_check(df, 'email', df['email'].dropna()),
        threshold=0.9
    )
    
    checker.add_check(
        "Age Range",
        lambda df: range_check(df, 'age', 0, 120),
        threshold=0.95
    )
    
    return checker

# Use the checker
checker = create_quality_checker()
results = checker.run_checks(customers_df)
summary = checker.get_summary()
print(f"Overall pass rate: {summary['pass_rate']:.2%}")
```

### Problem 3: Build a Metrics Calculation Engine
```python
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any

class MetricsCalculator:
    def __init__(self):
        self.metrics = {}
    
    def add_metric(self, name: str, calculation_func, description: str = ""):
        """Add a metric calculation"""
        self.metrics[name] = {
            'function': calculation_func,
            'description': description
        }
        return self
    
    def calculate_all(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate all metrics"""
        results = {}
        
        for name, metric in self.metrics.items():
            try:
                value = metric['function'](df)
                results[name] = {
                    'value': value,
                    'description': metric['description']
                }
            except Exception as e:
                results[name] = {
                    'value': None,
                    'error': str(e)
                }
        
        return results

# Define metric calculation functions
def total_revenue(df):
    """Calculate total revenue"""
    return df['order_amount'].sum()

def average_order_value(df):
    """Calculate average order value"""
    return df['order_amount'].mean()

def customer_count(df):
    """Calculate unique customer count"""
    return df['customer_id'].nunique()

def order_count(df):
    """Calculate total order count"""
    return len(df)

def monthly_revenue_growth(df):
    """Calculate month-over-month revenue growth"""
    monthly_revenue = df.groupby(df['order_date'].dt.to_period('M'))['order_amount'].sum()
    growth = monthly_revenue.pct_change().iloc[-1]
    return growth if not pd.isna(growth) else 0

def customer_retention_rate(df, period_days=30):
    """Calculate customer retention rate"""
    cutoff_date = df['order_date'].max() - timedelta(days=period_days)
    
    # Customers who ordered in the last period
    recent_customers = set(df[df['order_date'] >= cutoff_date]['customer_id'])
    
    # Customers who ordered in the period before that
    previous_customers = set(df[df['order_date'] < cutoff_date]['customer_id'])
    
    if not previous_customers:
        return 0
    
    retained_customers = recent_customers.intersection(previous_customers)
    return len(retained_customers) / len(previous_customers)

# Example usage
def create_metrics_calculator():
    """Create a metrics calculator for e-commerce data"""
    calculator = MetricsCalculator()
    
    calculator.add_metric(
        "Total Revenue",
        total_revenue,
        "Sum of all order amounts"
    )
    
    calculator.add_metric(
        "Average Order Value",
        average_order_value,
        "Mean order amount"
    )
    
    calculator.add_metric(
        "Customer Count",
        customer_count,
        "Number of unique customers"
    )
    
    calculator.add_metric(
        "Order Count",
        order_count,
        "Total number of orders"
    )
    
    calculator.add_metric(
        "Monthly Revenue Growth",
        monthly_revenue_growth,
        "Month-over-month revenue growth percentage"
    )
    
    calculator.add_metric(
        "Customer Retention Rate",
        customer_retention_rate,
        "Percentage of customers who made repeat purchases"
    )
    
    return calculator

# Use the calculator
calculator = create_metrics_calculator()
results = calculator.calculate_all(orders_df)

for metric_name, result in results.items():
    if 'error' in result:
        print(f"{metric_name}: ERROR - {result['error']}")
    else:
        print(f"{metric_name}: {result['value']:.2f} - {result['description']}")
```

## Tejuu's Coding Interview Tips

### 1. Problem-Solving Approach
- **Understand the business context**: Ask about the use case
- **Think about data quality**: Consider missing values, duplicates
- **Plan your approach**: Outline steps before coding
- **Test with sample data**: Use small datasets first

### 2. Code Quality
- **Clean and readable**: Use meaningful variable names
- **Handle edge cases**: Empty dataframes, null values
- **Add comments**: Explain business logic
- **Optimize for performance**: Use vectorized operations

### 3. Communication
- **Explain your approach**: Before coding
- **Discuss trade-offs**: Performance vs. readability
- **Ask clarifying questions**: About data and requirements
- **Think about scale**: How would this work with large datasets?

### 4. Common Patterns
- **Groupby operations**: For aggregations
- **Window functions**: For running calculations
- **Data validation**: Check data quality
- **Incremental processing**: For large datasets

This coding approach has helped me successfully solve technical challenges in analytics interviews and build reliable data pipelines at Central Bank and Stryker.
