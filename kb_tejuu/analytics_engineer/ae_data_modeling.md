---
tags: [analytics-engineer, data-modeling, dimensional-modeling, star-schema, snowflake-schema, kimball]
persona: ae
---

# Data Modeling for Analytics Engineers - Tejuu's Approach

## Introduction
**Tejuu's Philosophy:**
As an Analytics Engineer, I believe good data modeling is the foundation of reliable analytics. My approach combines business understanding with technical design - I always start by understanding what decisions stakeholders need to make, then design models that make those decisions easy.

## Dimensional Modeling Fundamentals

### Star Schema Design
**Tejuu's Experience:**
Star schemas are my go-to for most business analytics. They're simple for business users to understand and perform well in modern data warehouses. I've built dozens of star schemas across finance, sales, marketing, and operations.

**Example: Sales Analytics Star Schema**
```
Fact Table: fct_sales
- sale_id (PK)
- date_key (FK)
- customer_key (FK)
- product_key (FK)
- store_key (FK)
- sales_amount
- quantity
- discount_amount
- net_amount
- cost_amount
- profit_amount

Dimension Tables:
- dim_date (date_key, date, month, quarter, year, day_of_week, is_holiday)
- dim_customer (customer_key, customer_id, name, segment, region, acquisition_date)
- dim_product (product_key, product_id, name, category, subcategory, brand, unit_cost)
- dim_store (store_key, store_id, name, city, state, region, size, type)
```

**Business Benefits I Emphasize:**
- Executives can easily understand "What are my sales by region?"
- Analysts can slice and dice by any dimension without complex joins
- BI tools like Power BI and Tableau work great with star schemas
- Query performance is predictable and fast

### Slowly Changing Dimensions (SCD)

**Tejuu's Real-World Scenario:**
Let me share a challenge I faced: tracking customer segments over time. Customers move from "Silver" to "Gold" tier, but we needed to report on both historical and current segments.

**SCD Type 2 Implementation:**
```sql
-- dim_customer with SCD Type 2
CREATE TABLE dim_customer (
    customer_key BIGINT PRIMARY KEY,        -- Surrogate key
    customer_id VARCHAR(50),                -- Natural key
    customer_name VARCHAR(200),
    customer_segment VARCHAR(50),           -- Changes over time
    region VARCHAR(50),
    
    -- SCD Type 2 fields
    effective_date DATE,
    end_date DATE,
    is_current BOOLEAN,
    
    -- Audit fields
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- When segment changes, we insert a new row
INSERT INTO dim_customer VALUES
(1001, 'CUST001', 'John Smith', 'Silver', 'West', '2023-01-01', '2023-06-30', FALSE, NOW(), NOW()),
(1002, 'CUST001', 'John Smith', 'Gold', 'West', '2023-07-01', '9999-12-31', TRUE, NOW(), NOW());
```

**Business Value:**
- Marketing can analyze "What campaigns worked to upgrade customers from Silver to Gold?"
- Finance can report "Revenue by customer segment as it was in Q1 2023"
- Stakeholders get accurate historical analysis

### Fact Table Design Patterns

**Tejuu's Fact Table Types:**

**1. Transaction Fact Table**
```sql
-- fct_orders: One row per order
CREATE TABLE fct_orders (
    order_key BIGINT PRIMARY KEY,
    order_id VARCHAR(50),
    date_key INT,
    customer_key BIGINT,
    product_key BIGINT,
    
    -- Additive measures (can sum across all dimensions)
    order_amount DECIMAL(18,2),
    quantity INT,
    discount_amount DECIMAL(18,2),
    tax_amount DECIMAL(18,2),
    
    -- Semi-additive measures (can sum across some dimensions)
    inventory_level INT,  -- Additive across products, not across time
    
    -- Non-additive measures (cannot sum)
    unit_price DECIMAL(18,2),  -- Average or calculated, not summed
    discount_percentage DECIMAL(5,2)
);
```

**2. Periodic Snapshot Fact Table**
```sql
-- fct_daily_inventory: One row per product per day
CREATE TABLE fct_daily_inventory (
    snapshot_key BIGINT PRIMARY KEY,
    date_key INT,
    product_key BIGINT,
    warehouse_key BIGINT,
    
    -- Point-in-time measures
    beginning_inventory INT,
    ending_inventory INT,
    units_received INT,
    units_shipped INT,
    units_returned INT,
    
    -- Calculated measures
    inventory_value DECIMAL(18,2),
    days_of_supply DECIMAL(10,2)
);
```

**3. Accumulating Snapshot Fact Table**
```sql
-- fct_order_fulfillment: One row per order, updated as it progresses
CREATE TABLE fct_order_fulfillment (
    order_key BIGINT PRIMARY KEY,
    order_id VARCHAR(50),
    customer_key BIGINT,
    
    -- Multiple date foreign keys for different stages
    order_date_key INT,
    payment_date_key INT,
    shipped_date_key INT,
    delivered_date_key INT,
    
    -- Elapsed time measures
    order_to_payment_hours INT,
    payment_to_ship_hours INT,
    ship_to_delivery_hours INT,
    total_fulfillment_hours INT,
    
    -- Amounts
    order_amount DECIMAL(18,2),
    shipping_cost DECIMAL(18,2)
);
```

**Business Scenario:**
Operations wanted to track order fulfillment performance. Using an accumulating snapshot, we could answer:
- "What's our average time from order to delivery?"
- "Where are the bottlenecks in fulfillment?"
- "Which orders are stuck in payment processing?"

## Conformed Dimensions

**Tejuu's Cross-Functional Design:**
One of my biggest wins was creating conformed dimensions that work across multiple business functions.

**Example: Conformed Date Dimension**
```sql
-- dim_date: Used by Sales, Finance, Marketing, Operations
CREATE TABLE dim_date (
    date_key INT PRIMARY KEY,
    date DATE,
    
    -- Calendar attributes
    day_of_week VARCHAR(10),
    day_name VARCHAR(10),
    day_of_month INT,
    day_of_year INT,
    
    -- Week attributes
    week_of_year INT,
    iso_week INT,
    week_start_date DATE,
    week_end_date DATE,
    
    -- Month attributes
    month_number INT,
    month_name VARCHAR(10),
    month_abbr VARCHAR(3),
    month_start_date DATE,
    month_end_date DATE,
    
    -- Quarter attributes
    quarter_number INT,
    quarter_name VARCHAR(10),
    quarter_start_date DATE,
    quarter_end_date DATE,
    
    -- Year attributes
    year INT,
    fiscal_year INT,
    fiscal_quarter INT,
    fiscal_month INT,
    
    -- Business attributes
    is_weekend BOOLEAN,
    is_holiday BOOLEAN,
    holiday_name VARCHAR(100),
    is_business_day BOOLEAN,
    
    -- Comparison attributes
    prior_year_date DATE,
    prior_year_date_key INT
);
```

**Business Benefits:**
- Finance reports fiscal quarters consistently
- Marketing aligns campaigns with calendar and fiscal periods
- Operations excludes weekends/holidays from SLA calculations
- Everyone speaks the same language about time

## Data Mart Design

**Tejuu's Approach to Marts:**
I organize data marts by business function. Each mart has its own fact and dimension tables, optimized for that team's specific questions.

**Finance Mart Example:**
```sql
-- Finance wants: Revenue, Profit, Budget vs Actual

-- fct_revenue_daily
CREATE TABLE finance.fct_revenue_daily (
    date_key INT,
    customer_key BIGINT,
    product_key BIGINT,
    region_key BIGINT,
    
    -- Actual metrics
    gross_revenue DECIMAL(18,2),
    discounts DECIMAL(18,2),
    returns DECIMAL(18,2),
    net_revenue DECIMAL(18,2),
    cost_of_goods DECIMAL(18,2),
    gross_profit DECIMAL(18,2),
    
    -- Budget metrics
    budgeted_revenue DECIMAL(18,2),
    revenue_variance DECIMAL(18,2),
    revenue_variance_pct DECIMAL(5,2)
);

-- dim_account_hierarchy
CREATE TABLE finance.dim_account_hierarchy (
    account_key BIGINT PRIMARY KEY,
    account_code VARCHAR(50),
    account_name VARCHAR(200),
    account_type VARCHAR(50),
    
    -- Hierarchy
    level_1_name VARCHAR(100),
    level_2_name VARCHAR(100),
    level_3_name VARCHAR(100),
    level_4_name VARCHAR(100),
    
    -- Business attributes
    is_active BOOLEAN,
    requires_approval BOOLEAN
);
```

**Marketing Mart Example:**
```sql
-- Marketing wants: Campaign Performance, Customer Acquisition, LTV

-- fct_campaign_performance
CREATE TABLE marketing.fct_campaign_performance (
    date_key INT,
    campaign_key BIGINT,
    channel_key BIGINT,
    segment_key BIGINT,
    
    -- Metrics
    impressions INT,
    clicks INT,
    conversions INT,
    spend_amount DECIMAL(18,2),
    revenue_generated DECIMAL(18,2),
    
    -- Calculated metrics
    click_through_rate DECIMAL(5,4),
    conversion_rate DECIMAL(5,4),
    cost_per_click DECIMAL(10,2),
    cost_per_acquisition DECIMAL(10,2),
    return_on_ad_spend DECIMAL(10,2)
);

-- dim_campaign
CREATE TABLE marketing.dim_campaign (
    campaign_key BIGINT PRIMARY KEY,
    campaign_id VARCHAR(50),
    campaign_name VARCHAR(200),
    campaign_type VARCHAR(50),
    
    -- Campaign attributes
    start_date DATE,
    end_date DATE,
    target_segment VARCHAR(100),
    objective VARCHAR(100),
    budget_amount DECIMAL(18,2)
);
```

## Metric Layer

**Tejuu's Metric Definitions:**
One of my key responsibilities is defining metrics consistently across the organization.

**Example: Customer Metrics**
```yaml
# metrics.yml - I use YAML to document metrics

metrics:
  - name: customer_lifetime_value
    description: Total revenue from a customer over their lifetime
    calculation: SUM(fct_sales.net_amount) WHERE customer_key = X
    owner: Marketing
    business_definition: |
      Expected total revenue from a customer from first purchase to churn.
      Used for customer acquisition cost justification and segment analysis.
    
  - name: customer_acquisition_cost
    description: Cost to acquire a new customer
    calculation: marketing_spend / new_customers_acquired
    owner: Marketing
    business_definition: |
      Total marketing and sales spend divided by number of new customers.
      Target is to keep CAC below 30% of LTV.
    
  - name: monthly_recurring_revenue
    description: Predictable revenue per month
    calculation: SUM(subscription_amount) WHERE status = 'active'
    owner: Finance
    business_definition: |
      Monthly revenue from all active subscriptions.
      Key metric for SaaS business health and forecasting.
```

**Business Value:**
- No more "Why do Finance and Marketing have different revenue numbers?"
- New analysts can look up metric definitions
- BI dashboards use consistent calculations
- Stakeholders trust the numbers

## Data Quality in Models

**Tejuu's Testing Strategy:**
I implement tests at every layer to catch data quality issues before stakeholders see them.

**dbt Tests Example:**
```yaml
# models/marts/finance/fct_revenue_daily.yml

version: 2

models:
  - name: fct_revenue_daily
    description: Daily revenue fact table
    
    tests:
      - dbt_utils.recency:
          datepart: day
          field: date_key
          interval: 1
          
    columns:
      - name: date_key
        tests:
          - not_null
          - relationships:
              to: ref('dim_date')
              field: date_key
              
      - name: customer_key
        tests:
          - not_null
          - relationships:
              to: ref('dim_customer')
              field: customer_key
              
      - name: net_revenue
        tests:
          - not_null
          - dbt_expectations.expect_column_values_to_be_between:
              min_value: 0
              max_value: 1000000
              
      - name: gross_profit
        tests:
          - not_null
          
      - name: revenue_variance_pct
        tests:
          - dbt_expectations.expect_column_values_to_be_between:
              min_value: -100
              max_value: 100
```

**Custom Tests:**
```sql
-- tests/assert_revenue_matches_source.sql
-- Make sure our aggregated revenue matches the source system

WITH source_revenue AS (
    SELECT
        DATE(order_date) AS order_date,
        SUM(order_amount) AS total_revenue
    FROM {{ source('raw', 'orders') }}
    WHERE order_status = 'completed'
    GROUP BY 1
),

dbt_revenue AS (
    SELECT
        d.date,
        SUM(f.net_revenue) AS total_revenue
    FROM {{ ref('fct_revenue_daily') }} f
    JOIN {{ ref('dim_date') }} d ON f.date_key = d.date_key
    GROUP BY 1
)

SELECT
    s.order_date,
    s.total_revenue AS source_total,
    d.total_revenue AS dbt_total,
    ABS(s.total_revenue - d.total_revenue) AS difference
FROM source_revenue s
LEFT JOIN dbt_revenue d ON s.order_date = d.date
WHERE ABS(s.total_revenue - d.total_revenue) > 0.01
```

**Business Impact:**
Finance CFO asked: "Can I trust these numbers for the board meeting?"
My answer: "Yes - we have 50+ automated tests running daily, and I get alerted immediately if anything fails."

## Performance Optimization

**Tejuu's Optimization Strategies:**

**1. Materialization Strategy**
```sql
-- Staging: Views (lightweight, always fresh)
{{ config(materialized='view') }}

-- Intermediate: Ephemeral or Views (no storage)
{{ config(materialized='ephemeral') }}

-- Marts: Tables or Incremental (fast queries)
{{ config(materialized='table') }}

-- Large Facts: Incremental (only process new data)
{{ config(
    materialized='incremental',
    unique_key='order_id',
    on_schema_change='fail'
) }}
```

**2. Partitioning and Clustering**
```sql
-- Snowflake example
{{ config(
    materialized='incremental',
    unique_key='order_id',
    cluster_by=['order_date', 'customer_id']
) }}

-- BigQuery example
{{ config(
    materialized='incremental',
    unique_key='order_id',
    partition_by={
        'field': 'order_date',
        'data_type': 'date',
        'granularity': 'day'
    },
    cluster_by=['customer_id', 'product_id']
) }}
```

**Business Scenario:**
Dashboard was taking 2 minutes to load. After adding clustering by date and customer, it dropped to 5 seconds. Product manager was thrilled!

## Documentation

**Tejuu's Documentation Approach:**
I treat documentation as code - it lives with the models and is version controlled.

**Example:**
```yaml
# models/marts/finance/fct_revenue_daily.yml

version: 2

models:
  - name: fct_revenue_daily
    description: |
      ## Purpose
      Daily revenue fact table for financial reporting and analysis.
      
      ## Business Logic
      - Revenue is recognized on order completion date
      - Returns are subtracted from gross revenue
      - Budget data comes from finance.budget_monthly table
      
      ## Refresh Schedule
      - Runs daily at 6 AM UTC
      - Data is available for previous day by 7 AM
      
      ## Data Quality
      - Revenue reconciles to source within $100
      - All dates have corresponding budget records
      - No negative net revenue allowed
      
      ## Key Stakeholders
      - Owner: Finance team
      - Primary users: CFO, FP&A team, Regional managers
      - SLA: 99.5% uptime
      
    columns:
      - name: date_key
        description: |
          Foreign key to dim_date.
          Use this to filter by any date attribute (month, quarter, fiscal period).
          
      - name: net_revenue
        description: |
          **Business Definition:** Gross revenue minus discounts and returns.
          **Formula:** gross_revenue - discounts - returns
          **Example:** $1000 order with $50 discount and $20 return = $930 net revenue
          **Use for:** Revenue reporting, variance analysis, forecasting
```

This detailed documentation helps new team members, auditors, and future me understand the models!

