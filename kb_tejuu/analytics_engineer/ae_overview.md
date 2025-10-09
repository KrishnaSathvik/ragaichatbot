---
tags: [analytics-engineer, dbt, data-modeling, sql, data-warehouse, metrics]
persona: ae
---

# Analytics Engineer & Tejuu's Experience

## Modern Data Stack and Analytics Engineering

### What is an Analytics Engineer?
**Tejuu's Role:**
So as an Analytics Engineer, I'm kind of the bridge between data engineering and business intelligence. I take raw data from data warehouses and transform it into clean, well-modeled datasets that business users can easily understand and use for analysis.

The key difference from a traditional BI developer is that I write code (mostly SQL and Python) to build data models, use version control, write tests, and follow software engineering best practices. It's like being a data engineer but focused on the analytics layer rather than data pipelines.

**My Responsibilities:**
```
1. Data Modeling
   - Design dimensional models (star/snowflake schemas)
   - Create reusable data marts
   - Define metrics and KPIs
   - Document data lineage

2. Transformation Development
   - Write SQL transformations
   - Build dbt models
   - Create staging, intermediate, and mart layers
   - Implement business logic

3. Data Quality & Testing
   - Write data quality tests
   - Implement validation rules
   - Monitor data freshness
   - Alert on anomalies

4. Documentation & Governance
   - Document data models
   - Define metrics definitions
   - Create data dictionaries
   - Maintain data catalog

5. Collaboration
   - Work with data engineers on data pipelines
   - Partner with analysts on requirements
   - Support BI developers with data models
   - Train business users on data usage
```

## dbt (Data Build Tool)

### Building Transformation Pipelines with dbt
**Tejuu's dbt Experience:**
I use dbt daily to transform raw data into analytics-ready datasets. It's become the standard tool for analytics engineering, and I love how it brings software engineering practices to data transformation.

**My dbt Project Structure:**
```
my_dbt_project/
├── models/
│   ├── staging/          # Raw data cleaning
│   │   ├── stg_customers.sql
│   │   ├── stg_orders.sql
│   │   └── stg_products.sql
│   ├── intermediate/     # Business logic
│   │   ├── int_customer_orders.sql
│   │   └── int_order_items.sql
│   └── marts/           # Final analytics tables
│       ├── finance/
│       │   ├── fct_revenue.sql
│       │   └── dim_customers.sql
│       └── marketing/
│           ├── fct_campaigns.sql
│           └── dim_customer_segments.sql
├── tests/
│   └── assert_positive_revenue.sql
├── macros/
│   └── generate_schema_name.sql
└── dbt_project.yml
```

**Staging Layer Example:**
```sql
-- models/staging/stg_customers.sql
{{
    config(
        materialized='view',
        schema='staging'
    )
}}

WITH source AS (
    SELECT * FROM {{ source('raw', 'customers') }}
),

renamed AS (
    SELECT
        customer_id,
        TRIM(LOWER(email)) AS email,
        TRIM(first_name) AS first_name,
        TRIM(last_name) AS last_name,
        CONCAT(first_name, ' ', last_name) AS full_name,
        phone,
        address,
        city,
        state,
        zip_code,
        country,
        created_at,
        updated_at
    FROM source
    WHERE customer_id IS NOT NULL
)

SELECT * FROM renamed
```

**Intermediate Layer Example:**
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
        c.full_name,
        c.email,
        c.city,
        c.state,
        o.order_id,
        o.order_date,
        o.order_amount,
        o.order_status
    FROM customers c
    LEFT JOIN orders o ON c.customer_id = o.customer_id
)

SELECT * FROM customer_orders
```

**Marts Layer Example:**
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

### dbt Tests and Data Quality
**My Testing Strategy:**
```yaml
# models/staging/schema.yml
version: 2

models:
  - name: stg_customers
    description: Cleaned and standardized customer data
    columns:
      - name: customer_id
        description: Primary key for customers
        tests:
          - unique
          - not_null
      
      - name: email
        description: Customer email address
        tests:
          - not_null
          - unique
          - dbt_utils.email
      
      - name: created_at
        description: Timestamp when customer was created
        tests:
          - not_null
          - dbt_utils.expression_is_true:
              expression: ">= '2020-01-01'"

  - name: stg_orders
    description: Cleaned and standardized order data
    columns:
      - name: order_id
        tests:
          - unique
          - not_null
      
      - name: customer_id
        tests:
          - not_null
          - relationships:
              to: ref('stg_customers')
              field: customer_id
      
      - name: order_amount
        tests:
          - not_null
          - dbt_utils.expression_is_true:
              expression: "> 0"
```

**Custom Tests:**
```sql
-- tests/assert_revenue_positive.sql
SELECT
    order_id,
    order_amount
FROM {{ ref('fct_revenue') }}
WHERE order_amount <= 0
```

### dbt Macros for Reusability
**My Commonly Used Macros:**
```sql
-- macros/cents_to_dollars.sql
{% macro cents_to_dollars(column_name, precision=2) %}
    ROUND({{ column_name }} / 100.0, {{ precision }})
{% endmacro %}

-- Usage in model:
SELECT
    order_id,
    {{ cents_to_dollars('amount_cents') }} AS amount_dollars
FROM orders

-- macros/generate_surrogate_key.sql
{% macro generate_surrogate_key(field_list) %}
    MD5(CONCAT(
        {% for field in field_list %}
            COALESCE(CAST({{ field }} AS VARCHAR), '')
            {% if not loop.last %} || '|' || {% endif %}
        {% endfor %}
    ))
{% endmacro %}

-- Usage:
SELECT
    {{ generate_surrogate_key(['customer_id', 'order_date']) }} AS order_key,
    *
FROM orders

-- macros/pivot_metric.sql
{% macro pivot_metric(column, values, metric, agg_function='SUM') %}
    {% for value in values %}
        {{ agg_function }}(
            CASE WHEN {{ column }} = '{{ value }}' 
            THEN {{ metric }} 
            ELSE 0 END
        ) AS {{ value | replace(' ', '_') | lower }}
        {% if not loop.last %}, {% endif %}
    {% endfor %}
{% endmacro %}
```

## Metrics Layer and Semantic Modeling

### Defining Business Metrics
**Tejuu's Metrics Framework:**
```yaml
# metrics/revenue_metrics.yml
version: 2

metrics:
  - name: total_revenue
    label: Total Revenue
    model: ref('fct_revenue')
    description: Sum of all completed order amounts
    
    calculation_method: sum
    expression: order_amount
    
    timestamp: order_date
    time_grains: [day, week, month, quarter, year]
    
    dimensions:
      - customer_segment
      - product_category
      - region
    
    filters:
      - field: order_status
        operator: '='
        value: "'completed'"

  - name: average_order_value
    label: Average Order Value
    model: ref('fct_revenue')
    description: Average amount per order
    
    calculation_method: average
    expression: order_amount
    
    timestamp: order_date
    time_grains: [day, week, month, quarter, year]

  - name: customer_lifetime_value
    label: Customer Lifetime Value
    model: ref('dim_customers')
    description: Total revenue per customer
    
    calculation_method: sum
    expression: total_spent
    
    dimensions:
      - customer_segment
      - acquisition_channel
```

## SQL Optimization for Analytics

### Query Performance Optimization
**Tejuu's SQL Optimization Techniques:**
```sql
-- BEFORE: Slow query with subqueries
SELECT 
    c.customer_id,
    c.customer_name,
    (SELECT COUNT(*) FROM orders o WHERE o.customer_id = c.customer_id) as order_count,
    (SELECT SUM(amount) FROM orders o WHERE o.customer_id = c.customer_id) as total_spent
FROM customers c;

-- AFTER: Optimized with JOIN
SELECT 
    c.customer_id,
    c.customer_name,
    COUNT(o.order_id) as order_count,
    SUM(o.amount) as total_spent
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id
GROUP BY c.customer_id, c.customer_name;

-- BEFORE: Multiple passes over data
SELECT customer_id, SUM(amount) FROM orders GROUP BY customer_id;
SELECT customer_id, COUNT(*) FROM orders GROUP BY customer_id;
SELECT customer_id, AVG(amount) FROM orders GROUP BY customer_id;

-- AFTER: Single pass with multiple aggregations
SELECT 
    customer_id,
    SUM(amount) as total_amount,
    COUNT(*) as order_count,
    AVG(amount) as avg_amount
FROM orders
GROUP BY customer_id;

-- Using CTEs for readability and performance
WITH monthly_sales AS (
    SELECT 
        DATE_TRUNC('month', order_date) as month,
        SUM(amount) as total_sales
    FROM orders
    WHERE order_date >= '2023-01-01'
    GROUP BY DATE_TRUNC('month', order_date)
),
sales_with_growth AS (
    SELECT 
        month,
        total_sales,
        LAG(total_sales) OVER (ORDER BY month) as prev_month_sales,
        (total_sales - LAG(total_sales) OVER (ORDER BY month)) / 
        LAG(total_sales) OVER (ORDER BY month) * 100 as growth_rate
    FROM monthly_sales
)
SELECT * FROM sales_with_growth
WHERE growth_rate IS NOT NULL
ORDER BY month;
```

## Data Warehouse Modeling

### Dimensional Modeling
**Tejuu's Dimensional Model Design:**
```sql
-- Dimension Table: Customers
CREATE TABLE dim_customers (
    customer_key INT PRIMARY KEY,  -- Surrogate key
    customer_id VARCHAR(50),        -- Natural key
    customer_name VARCHAR(200),
    email VARCHAR(200),
    segment VARCHAR(50),
    city VARCHAR(100),
    state VARCHAR(50),
    country VARCHAR(50),
    first_order_date DATE,
    customer_since_days INT,
    is_active BOOLEAN,
    effective_date DATE,            -- SCD Type 2
    expiration_date DATE,           -- SCD Type 2
    is_current BOOLEAN,             -- SCD Type 2
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- Fact Table: Sales
CREATE TABLE fct_sales (
    sale_key BIGINT PRIMARY KEY,
    order_id VARCHAR(50),
    customer_key INT REFERENCES dim_customers(customer_key),
    product_key INT REFERENCES dim_products(product_key),
    date_key INT REFERENCES dim_date(date_key),
    employee_key INT REFERENCES dim_employees(employee_key),
    
    -- Measures
    quantity INT,
    unit_price DECIMAL(10,2),
    discount_amount DECIMAL(10,2),
    tax_amount DECIMAL(10,2),
    total_amount DECIMAL(10,2),
    cost_amount DECIMAL(10,2),
    profit_amount DECIMAL(10,2),
    
    -- Degenerate dimensions
    order_number VARCHAR(50),
    invoice_number VARCHAR(50),
    
    created_at TIMESTAMP
);

-- Date Dimension (very important for analytics)
CREATE TABLE dim_date (
    date_key INT PRIMARY KEY,
    date DATE,
    day_of_week VARCHAR(10),
    day_of_month INT,
    day_of_year INT,
    week_of_year INT,
    month_number INT,
    month_name VARCHAR(10),
    quarter INT,
    year INT,
    is_weekend BOOLEAN,
    is_holiday BOOLEAN,
    holiday_name VARCHAR(100),
    fiscal_year INT,
    fiscal_quarter INT,
    fiscal_month INT
);
```

## Data Governance and Documentation

### Data Catalog and Lineage
**My Documentation Approach:**
```markdown
# Data Model: Customer Analytics

## Purpose
Provides a comprehensive view of customer behavior, segmentation, and lifetime value for marketing and sales teams.

## Source Systems
- Salesforce CRM (customer data)
- Shopify (order data)
- Google Analytics (web behavior)

## Refresh Schedule
- Staging: Every 1 hour
- Intermediate: Every 2 hours
- Marts: Daily at 6 AM EST

## Data Lineage
```
raw.salesforce.accounts 
  → staging.stg_customers 
    → intermediate.int_customer_orders 
      → marts.dim_customers
```

## Key Metrics
| Metric | Definition | Formula |
|--------|-----------|---------|
| Customer Lifetime Value | Total revenue from customer | SUM(order_amount) |
| Average Order Value | Average amount per order | SUM(order_amount) / COUNT(orders) |
| Purchase Frequency | Orders per customer per year | COUNT(orders) / customer_tenure_years |

## Data Quality Rules
- customer_id must be unique and not null
- email must be valid format
- total_spent must be >= 0
- first_order_date must be <= last_order_date

## Access Control
- Finance team: Full access
- Marketing team: Read access (excluding PII)
- Sales team: Read access (own region only)
```

## Interview Talking Points

### Technical Skills:
- dbt development and testing
- SQL optimization and performance tuning
- Dimensional modeling (star/snowflake schemas)
- Data quality and validation
- Metrics definition and semantic modeling
- Version control (Git) for data transformations

### Tools & Technologies:
- **Transformation**: dbt, SQL, Python
- **Data Warehouses**: Snowflake, BigQuery, Redshift
- **Version Control**: Git, GitHub, GitLab
- **Orchestration**: Airflow, Dagster, Prefect
- **BI Tools**: Power BI, Tableau, Looker
- **Data Quality**: Great Expectations, dbt tests

### Achievements:
- Built 100+ dbt models serving 50+ analysts
- Reduced data transformation time from 6 hours to 1 hour
- Implemented data quality tests catching 95% of issues
- Created reusable metrics layer used across 20+ dashboards
- Documented 200+ data models improving data discovery
- Trained 15+ analysts on dbt and SQL best practices

### Project Examples:
- Customer 360 data mart (unified customer view)
- Financial reporting data warehouse (P&L, balance sheet)
- Marketing analytics platform (campaign performance, attribution)
- Product analytics (usage, engagement, retention)
- Operational metrics (efficiency, productivity, quality)
