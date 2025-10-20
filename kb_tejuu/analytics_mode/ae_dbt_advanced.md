---
tags: [analytics-engineer, dbt, transformation, testing, macros, jinja, incremental-models]
persona: analytics
---

# Advanced dbt Techniques - Tejuu's Expertise

## Introduction
**Tejuu's dbt Journey:**
I've been working with dbt for 3+ years, and it's completely transformed how I build analytics. What started as simple SQL transformations evolved into a sophisticated data transformation pipeline with testing, documentation, and CI/CD. Let me share the advanced techniques I use daily.

## Incremental Models

**Tejuu's Use Case:**
Our sales fact table has 50+ million rows and grows by 500K daily. Rebuilding the entire table takes 2 hours. Using incremental models, we process only new data in 5 minutes.

**Basic Incremental Model:**
```sql
-- models/marts/sales/fct_orders.sql

{{
    config(
        materialized='incremental',
        unique_key='order_id',
        on_schema_change='fail'
    )
}}

SELECT
    order_id,
    customer_id,
    order_date,
    order_amount,
    created_at,
    updated_at
FROM {{ source('raw', 'orders') }}

{% if is_incremental() %}
    -- Only process new or updated records
    WHERE updated_at > (SELECT MAX(updated_at) FROM {{ this }})
{% endif %}
```

**Advanced Incremental with Late-Arriving Data:**
```sql
-- models/marts/sales/fct_orders_late_arriving.sql

{{
    config(
        materialized='incremental',
        unique_key='order_id',
        on_schema_change='sync_all_columns'
    )
}}

WITH source_data AS (
    SELECT
        order_id,
        customer_id,
        order_date,
        order_amount,
        order_status,
        updated_at
    FROM {{ source('raw', 'orders') }}
    
    {% if is_incremental() %}
        -- Look back 7 days to catch late-arriving updates
        WHERE updated_at > (SELECT DATEADD(day, -7, MAX(updated_at)) FROM {{ this }})
    {% endif %}
),

deduplicated AS (
    -- Keep only the latest version of each order
    SELECT *
    FROM (
        SELECT *,
               ROW_NUMBER() OVER (PARTITION BY order_id ORDER BY updated_at DESC) AS rn
        FROM source_data
    )
    WHERE rn = 1
)

SELECT
    order_id,
    customer_id,
    order_date,
    order_amount,
    order_status,
    updated_at
FROM deduplicated
```

**Business Impact:**
Finance can see yesterday's revenue by 6 AM instead of 9 AM. That 3-hour difference means CFO gets numbers before his 7 AM standup with the CEO.

## Snapshots (Slowly Changing Dimensions)

**Tejuu's SCD Implementation:**
Tracking customer segments over time was crucial for marketing analytics.

**Timestamp Strategy:**
```sql
-- snapshots/snap_customers.sql

{% snapshot snap_customers %}

{{
    config(
      target_schema='snapshots',
      unique_key='customer_id',
      strategy='timestamp',
      updated_at='updated_at',
      invalidate_hard_deletes=True
    )
}}

SELECT
    customer_id,
    customer_name,
    customer_segment,    -- Changes from Bronze → Silver → Gold
    customer_tier,
    customer_status,
    region,
    updated_at
FROM {{ source('raw', 'customers') }}

{% endsnapshot %}
```

**Check Strategy (for sources without updated_at):**
```sql
-- snapshots/snap_product_prices.sql

{% snapshot snap_product_prices %}

{{
    config(
      target_schema='snapshots',
      unique_key='product_id',
      strategy='check',
      check_cols=['unit_price', 'list_price']  -- Track price changes
    )
}}

SELECT
    product_id,
    product_name,
    unit_price,
    list_price,
    category,
    brand
FROM {{ source('raw', 'products') }}

{% endsnapshot %}
```

**Using Snapshot in Analysis:**
```sql
-- How much revenue came from customers who were "Gold" tier in Q1 2023?

WITH gold_customers_q1 AS (
    SELECT DISTINCT customer_id
    FROM {{ ref('snap_customers') }}
    WHERE customer_segment = 'Gold'
      AND dbt_valid_from <= '2023-03-31'
      AND (dbt_valid_to > '2023-01-01' OR dbt_valid_to IS NULL)
)

SELECT
    SUM(o.order_amount) AS total_revenue
FROM {{ ref('fct_orders') }} o
JOIN gold_customers_q1 g ON o.customer_id = g.customer_id
WHERE o.order_date BETWEEN '2023-01-01' AND '2023-03-31'
```

## Macros

**Tejuu's Custom Macros:**

**1. Generate Date Spine:**
```sql
-- macros/generate_date_spine.sql

{% macro generate_date_spine(start_date, end_date) %}

WITH date_spine AS (
    {{ dbt_utils.date_spine(
        datepart="day",
        start_date="TO_DATE('" ~ start_date ~ "', 'YYYY-MM-DD')",
        end_date="TO_DATE('" ~ end_date ~ "', 'YYYY-MM-DD')"
    )}}
)

SELECT
    date_day,
    DAYOFWEEK(date_day) AS day_of_week,
    DAYNAME(date_day) AS day_name,
    WEEKOFYEAR(date_day) AS week_of_year,
    MONTH(date_day) AS month_number,
    MONTHNAME(date_day) AS month_name,
    QUARTER(date_day) AS quarter,
    YEAR(date_day) AS year,
    CASE WHEN DAYOFWEEK(date_day) IN (6, 7) THEN TRUE ELSE FALSE END AS is_weekend
FROM date_spine

{% endmacro %}
```

**Usage:**
```sql
-- models/staging/stg_date_spine.sql

{{ generate_date_spine('2020-01-01', '2025-12-31') }}
```

**2. Pivot Table Macro:**
```sql
-- macros/pivot_table.sql

{% macro pivot_table(source_table, row_key, column_key, value_column, agg_function='SUM') %}

WITH source_data AS (
    SELECT * FROM {{ source_table }}
),

pivoted AS (
    SELECT
        {{ row_key }},
        {% for col_value in get_column_values(source_table, column_key) %}
        {{ agg_function }}(
            CASE WHEN {{ column_key }} = '{{ col_value }}' 
            THEN {{ value_column }} 
            ELSE 0 END
        ) AS {{ col_value | replace(' ', '_') | lower }}
        {% if not loop.last %},{% endif %}
        {% endfor %}
    FROM source_data
    GROUP BY {{ row_key }}
)

SELECT * FROM pivoted

{% endmacro %}
```

**Usage:**
```sql
-- models/marts/sales/revenue_by_product_category.sql

{{ pivot_table(
    source_table=ref('fct_sales'),
    row_key='date_key',
    column_key='product_category',
    value_column='sales_amount',
    agg_function='SUM'
) }}
```

**3. Surrogate Key Generation:**
```sql
-- macros/generate_surrogate_key.sql

{% macro generate_surrogate_key(columns) %}
    MD5(CAST(CONCAT(
        {% for col in columns %}
        COALESCE(CAST({{ col }} AS VARCHAR), '')
        {% if not loop.last %}, '|', {% endif %}
        {% endfor %}
    ) AS VARCHAR))
{% endmacro %}
```

**Usage:**
```sql
SELECT
    {{ generate_surrogate_key(['customer_id', 'order_date']) }} AS order_key,
    customer_id,
    order_date,
    order_amount
FROM {{ source('raw', 'orders') }}
```

## Tests

**Tejuu's Testing Strategy:**

**1. Generic Tests:**
```yaml
# models/marts/sales/fct_orders.yml

version: 2

models:
  - name: fct_orders
    tests:
      - dbt_utils.equal_rowcount:
          compare_model: source('raw', 'orders')
          
    columns:
      - name: order_id
        tests:
          - unique
          - not_null
          
      - name: customer_id
        tests:
          - not_null
          - relationships:
              to: ref('dim_customer')
              field: customer_id
              
      - name: order_amount
        tests:
          - not_null
          - dbt_expectations.expect_column_values_to_be_between:
              min_value: 0
              max_value: 1000000
```

**2. Singular Tests:**
```sql
-- tests/assert_daily_revenue_positive.sql

SELECT
    order_date,
    SUM(order_amount) AS daily_revenue
FROM {{ ref('fct_orders') }}
GROUP BY order_date
HAVING SUM(order_amount) < 0
```

**3. Custom Generic Test:**
```sql
-- macros/tests/test_revenue_reconciliation.sql

{% test revenue_reconciliation(model, revenue_column, source_table, source_column, tolerance=100) %}

WITH model_total AS (
    SELECT SUM({{ revenue_column }}) AS model_revenue
    FROM {{ model }}
),

source_total AS (
    SELECT SUM({{ source_column }}) AS source_revenue
    FROM {{ source_table }}
)

SELECT
    model_revenue,
    source_revenue,
    ABS(model_revenue - source_revenue) AS difference
FROM model_total
CROSS JOIN source_total
WHERE ABS(model_revenue - source_revenue) > {{ tolerance }}

{% endtest %}
```

**Usage:**
```yaml
models:
  - name: fct_revenue_daily
    tests:
      - revenue_reconciliation:
          revenue_column: net_revenue
          source_table: source('raw', 'orders')
          source_column: order_amount
          tolerance: 50
```

**Business Value:**
Our CFO once asked: "How do I know these numbers are right?"
I showed him our 100+ automated tests running daily. He was impressed and now trusts the data.

## Jinja Templating

**Tejuu's Advanced Jinja:**

**1. Dynamic Column Generation:**
```sql
-- models/marts/sales/sales_metrics_monthly.sql

WITH monthly_sales AS (
    SELECT
        customer_id,
        DATE_TRUNC('month', order_date) AS order_month,
        SUM(order_amount) AS total_sales
    FROM {{ ref('fct_orders') }}
    GROUP BY 1, 2
)

SELECT
    customer_id,
    {% for month_offset in range(0, 12) %}
    SUM(CASE 
        WHEN order_month = DATEADD('month', -{{ month_offset }}, DATE_TRUNC('month', CURRENT_DATE))
        THEN total_sales 
        ELSE 0 
    END) AS sales_m{{ month_offset }}{% if not loop.last %},{% endif %}
    {% endfor %}
FROM monthly_sales
GROUP BY customer_id
```

**2. Environment-Specific Logic:**
```sql
-- models/staging/stg_orders.sql

SELECT
    order_id,
    customer_id,
    order_date,
    order_amount
FROM {{ source('raw', 'orders') }}

{% if target.name == 'dev' %}
    -- In dev, only process last 30 days for speed
    WHERE order_date >= DATEADD('day', -30, CURRENT_DATE)
{% elif target.name == 'prod' %}
    -- In prod, process all data
    WHERE order_date >= '2020-01-01'
{% endif %}
```

**3. Dynamic Schema Generation:**
```sql
-- macros/generate_schema_name.sql

{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- set default_schema = target.schema -%}
    
    {%- if target.name == 'prod' -%}
        {%- if custom_schema_name is not none -%}
            {{ custom_schema_name | trim }}
        {%- else -%}
            {{ default_schema }}
        {%- endif -%}
    {%- else -%}
        {{ default_schema }}_{{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
```

## Packages

**Tejuu's Essential dbt Packages:**

```yaml
# packages.yml

packages:
  - package: dbt-labs/dbt_utils
    version: 1.1.1
    
  - package: calogica/dbt_expectations
    version: 0.10.0
    
  - package: dbt-labs/metrics
    version: 1.6.0
    
  - package: dbt-labs/codegen
    version: 0.11.0
    
  - package: dbt-labs/audit_helper
    version: 0.9.0
```

**Using dbt_utils:**
```sql
-- models/staging/stg_customers.sql

WITH source AS (
    SELECT * FROM {{ source('raw', 'customers') }}
),

deduplicated AS (
    SELECT *
    FROM source
    {{ dbt_utils.deduplicate(
        partition_by='customer_id',
        order_by='updated_at DESC'
    ) }}
)

SELECT
    {{ dbt_utils.generate_surrogate_key(['customer_id', 'email']) }} AS customer_key,
    customer_id,
    email,
    first_name,
    last_name,
    {{ dbt_utils.get_url_parameter('utm_source', 'registration_url') }} AS acquisition_source,
    created_at,
    updated_at
FROM deduplicated
```

**Using dbt_expectations:**
```yaml
models:
  - name: fct_orders
    tests:
      - dbt_expectations.expect_table_row_count_to_be_between:
          min_value: 1000
          max_value: 10000000
          
      - dbt_expectations.expect_table_columns_to_match_ordered_list:
          column_list: ["order_id", "customer_id", "order_date", "order_amount"]
          
    columns:
      - name: order_date
        tests:
          - dbt_expectations.expect_column_values_to_be_between:
              min_value: "'2020-01-01'"
              max_value: "current_date"
```

## Exposures

**Tejuu's Exposure Tracking:**
I track all downstream dashboards and reports that use my dbt models.

```yaml
# models/exposures.yml

version: 2

exposures:
  - name: executive_revenue_dashboard
    type: dashboard
    maturity: high
    url: https://powerbi.com/reports/executive-revenue
    description: |
      Daily revenue dashboard used by CFO and executive team for morning standup.
      Shows revenue by region, product, and customer segment with YoY comparisons.
    
    depends_on:
      - ref('fct_revenue_daily')
      - ref('dim_date')
      - ref('dim_customer')
      - ref('dim_product')
    
    owner:
      name: Tejuu
      email: tejuu@company.com
    
  - name: marketing_campaign_report
    type: dashboard
    maturity: medium
    url: https://tableau.com/workbooks/marketing-campaigns
    description: |
      Weekly marketing campaign performance report.
      Used by CMO and marketing managers to optimize spend.
    
    depends_on:
      - ref('fct_campaign_performance')
      - ref('dim_campaign')
      - ref('dim_channel')
```

**Business Value:**
When I need to make breaking changes, I know exactly which dashboards will be affected and can notify the right stakeholders.

## CI/CD Integration

**Tejuu's dbt CI/CD Pipeline:**

```yaml
# .github/workflows/dbt_ci.yml

name: dbt CI

on:
  pull_request:
    branches: [main]

jobs:
  dbt-test:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
        
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
          
      - name: Install dbt
        run: |
          pip install dbt-snowflake==1.6.0
          dbt deps
          
      - name: Run dbt models on sample data
        run: |
          dbt run --select state:modified+ --defer --state ./prod_manifest
          
      - name: Run dbt tests
        run: |
          dbt test --select state:modified+
          
      - name: Generate and upload docs
        run: |
          dbt docs generate
          # Upload to S3 or cloud storage
```

**Business Impact:**
- Pull requests automatically run tests before merge
- No more "oops, I broke production"
- Code reviews include test results
- Junior analysts can contribute confidently

## Performance Optimization

**Tejuu's Optimization Techniques:**

**1. Query Performance:**
```sql
-- BEFORE: Slow query with multiple CTEs

WITH raw_orders AS (
    SELECT * FROM {{ source('raw', 'orders') }}
),

raw_customers AS (
    SELECT * FROM {{ source('raw', 'customers') }}
),

raw_products AS (
    SELECT * FROM {{ source('raw', 'products') }}
)

SELECT
    o.order_id,
    c.customer_name,
    p.product_name,
    o.order_amount
FROM raw_orders o
LEFT JOIN raw_customers c ON o.customer_id = c.customer_id
LEFT JOIN raw_products p ON o.product_id = p.product_id


-- AFTER: Optimized with pre-filtered CTEs

WITH recent_orders AS (
    SELECT
        order_id,
        customer_id,
        product_id,
        order_amount
    FROM {{ source('raw', 'orders') }}
    WHERE order_date >= DATEADD('month', -3, CURRENT_DATE)  -- Filter early
),

relevant_customers AS (
    SELECT
        customer_id,
        customer_name
    FROM {{ source('raw', 'customers') }}
    WHERE customer_id IN (SELECT DISTINCT customer_id FROM recent_orders)  -- Only needed customers
),

relevant_products AS (
    SELECT
        product_id,
        product_name
    FROM {{ source('raw', 'products') }}
    WHERE product_id IN (SELECT DISTINCT product_id FROM recent_orders)  -- Only needed products
)

SELECT
    o.order_id,
    c.customer_name,
    p.product_name,
    o.order_amount
FROM recent_orders o
LEFT JOIN relevant_customers c ON o.customer_id = c.customer_id
LEFT JOIN relevant_products p ON o.product_id = p.product_id
```

**2. Incremental Processing:**
```sql
-- models/marts/sales/fct_orders_aggregated.sql

{{
    config(
        materialized='incremental',
        unique_key=['customer_id', 'order_month'],
        on_schema_change='append_new_columns'
    )
}}

WITH monthly_orders AS (
    SELECT
        customer_id,
        DATE_TRUNC('month', order_date) AS order_month,
        COUNT(DISTINCT order_id) AS order_count,
        SUM(order_amount) AS total_spent,
        AVG(order_amount) AS avg_order_value
    FROM {{ ref('fct_orders') }}
    
    {% if is_incremental() %}
    WHERE order_date >= (
        SELECT DATEADD('month', -1, MAX(order_month))
        FROM {{ this }}
    )
    {% endif %}
    
    GROUP BY 1, 2
)

SELECT * FROM monthly_orders
```

These advanced dbt techniques have helped me build reliable, performant analytics pipelines that stakeholders trust!

