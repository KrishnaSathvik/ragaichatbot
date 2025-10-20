---
tags: [data-engineer, sql, query-optimization, window-functions, cte, performance-tuning]
persona: de
---

# Advanced SQL - Krishna's Expertise

## Introduction
**Krishna's SQL Background:**
SQL is my daily driver - from complex transformations to performance tuning. At Walgreens, I've optimized queries processing billions of rows, written complex window functions for analytics, and tuned performance for sub-second responses. Here's everything I know about advanced SQL.

## Window Functions

### Ranking Functions
**Krishna's Real Use Cases:**

**1. Customer Ranking by Spend:**
```sql
-- Rank customers within each segment
SELECT
    customer_id,
    customer_name,
    customer_segment,
    lifetime_value,
    ROW_NUMBER() OVER (PARTITION BY customer_segment ORDER BY lifetime_value DESC) as segment_rank,
    RANK() OVER (PARTITION BY customer_segment ORDER BY lifetime_value DESC) as segment_rank_with_ties,
    DENSE_RANK() OVER (PARTITION BY customer_segment ORDER BY lifetime_value DESC) as dense_rank,
    NTILE(4) OVER (PARTITION BY customer_segment ORDER BY lifetime_value DESC) as quartile
FROM dim_customer
WHERE is_active = 1;
```

**Business Question:** "Who are our top 10 customers in each segment?"
```sql
WITH ranked_customers AS (
    SELECT
        customer_id,
        customer_segment,
        lifetime_value,
        ROW_NUMBER() OVER (PARTITION BY customer_segment ORDER BY lifetime_value DESC) as rn
    FROM dim_customer
)
SELECT *
FROM ranked_customers
WHERE rn <= 10
ORDER BY customer_segment, rn;
```

**2. Product Performance Ranking:**
```sql
-- Top 5 products per category with running total
SELECT
    product_category,
    product_name,
    total_sales,
    ROW_NUMBER() OVER (PARTITION BY product_category ORDER BY total_sales DESC) as category_rank,
    SUM(total_sales) OVER (PARTITION BY product_category ORDER BY total_sales DESC) as running_total,
    ROUND(100.0 * total_sales / SUM(total_sales) OVER (PARTITION BY product_category), 2) as pct_of_category
FROM (
    SELECT 
        p.product_category,
        p.product_name,
        SUM(s.sales_amount) as total_sales
    FROM fct_sales s
    JOIN dim_product p ON s.product_key = p.product_key
    WHERE s.order_date >= DATEADD(month, -12, GETDATE())
    GROUP BY p.product_category, p.product_name
) product_sales
WHERE category_rank <= 5;
```

### Aggregation Functions
**Krishna's Analytics Patterns:**

**1. Running Totals & Moving Averages:**
```sql
-- Daily sales with running total and 7-day moving average
SELECT
    order_date,
    daily_sales,
    SUM(daily_sales) OVER (ORDER BY order_date) as running_total,
    AVG(daily_sales) OVER (ORDER BY order_date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) as moving_avg_7day,
    daily_sales - AVG(daily_sales) OVER (ORDER BY order_date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) as variance_from_avg
FROM (
    SELECT 
        order_date,
        SUM(order_amount) as daily_sales
    FROM fct_orders
    WHERE order_date >= '2024-01-01'
    GROUP BY order_date
) daily_summary
ORDER BY order_date;
```

**2. Lead/Lag for Period Comparisons:**
```sql
-- Month-over-month growth analysis
SELECT
    order_month,
    monthly_revenue,
    LAG(monthly_revenue, 1) OVER (ORDER BY order_month) as prev_month_revenue,
    monthly_revenue - LAG(monthly_revenue, 1) OVER (ORDER BY order_month) as mom_growth,
    ROUND(100.0 * (monthly_revenue - LAG(monthly_revenue, 1) OVER (ORDER BY order_month)) / 
          NULLIF(LAG(monthly_revenue, 1) OVER (ORDER BY order_month), 0), 2) as mom_growth_pct,
    LAG(monthly_revenue, 12) OVER (ORDER BY order_month) as same_month_last_year,
    ROUND(100.0 * (monthly_revenue - LAG(monthly_revenue, 12) OVER (ORDER BY order_month)) / 
          NULLIF(LAG(monthly_revenue, 12) OVER (ORDER BY order_month), 0), 2) as yoy_growth_pct
FROM monthly_sales_summary
ORDER BY order_month DESC;
```

**3. First/Last Value:**
```sql
-- Customer first and most recent purchase
SELECT
    customer_id,
    order_id,
    order_date,
    order_amount,
    FIRST_VALUE(order_date) OVER (PARTITION BY customer_id ORDER BY order_date) as first_purchase_date,
    LAST_VALUE(order_date) OVER (PARTITION BY customer_id ORDER BY order_date 
        ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) as last_purchase_date,
    DATEDIFF(day, 
        FIRST_VALUE(order_date) OVER (PARTITION BY customer_id ORDER BY order_date),
        order_date) as days_since_first_purchase
FROM fct_orders;
```

## Common Table Expressions (CTEs)

### Recursive CTEs
**Krishna's Hierarchical Data Queries:**

**1. Organization Hierarchy:**
```sql
-- Build employee reporting chain
WITH RECURSIVE employee_hierarchy AS (
    -- Base case: CEO (no manager)
    SELECT 
        employee_id,
        employee_name,
        manager_id,
        job_title,
        1 as level,
        CAST(employee_name AS VARCHAR(500)) as path
    FROM employees
    WHERE manager_id IS NULL
    
    UNION ALL
    
    -- Recursive case: employees with managers
    SELECT 
        e.employee_id,
        e.employee_name,
        e.manager_id,
        e.job_title,
        eh.level + 1,
        CAST(eh.path || ' > ' || e.employee_name AS VARCHAR(500))
    FROM employees e
    INNER JOIN employee_hierarchy eh ON e.manager_id = eh.employee_id
)
SELECT * FROM employee_hierarchy
ORDER BY path;
```

**2. Date Series Generation:**
```sql
-- Generate all dates for a year
WITH RECURSIVE date_series AS (
    SELECT CAST('2024-01-01' AS DATE) as date
    UNION ALL
    SELECT DATEADD(day, 1, date)
    FROM date_series
    WHERE date < '2024-12-31'
)
SELECT 
    date,
    DATEPART(weekday, date) as day_of_week,
    DATENAME(weekday, date) as day_name,
    CASE WHEN DATEPART(weekday, date) IN (1, 7) THEN 1 ELSE 0 END as is_weekend
FROM date_series;
```

### Complex CTEs for Analytics
**Krishna's Multi-Stage Transformations:**

```sql
-- Customer cohort analysis with multiple CTEs
WITH first_purchases AS (
    SELECT
        customer_id,
        MIN(order_date) as cohort_date,
        DATE_TRUNC('month', MIN(order_date)) as cohort_month
    FROM fct_orders
    GROUP BY customer_id
),
monthly_activity AS (
    SELECT
        o.customer_id,
        DATE_TRUNC('month', o.order_date) as activity_month,
        SUM(o.order_amount) as monthly_spend,
        COUNT(DISTINCT o.order_id) as monthly_orders
    FROM fct_orders o
    GROUP BY o.customer_id, DATE_TRUNC('month', o.order_date)
),
cohort_activity AS (
    SELECT
        f.cohort_month,
        m.activity_month,
        DATEDIFF('month', f.cohort_month, m.activity_month) as months_since_cohort,
        COUNT(DISTINCT m.customer_id) as active_customers,
        SUM(m.monthly_spend) as cohort_revenue
    FROM first_purchases f
    JOIN monthly_activity m ON f.customer_id = m.customer_id
    GROUP BY f.cohort_month, m.activity_month
),
cohort_sizes AS (
    SELECT
        cohort_month,
        COUNT(DISTINCT customer_id) as cohort_size
    FROM first_purchases
    GROUP BY cohort_month
)
SELECT
    ca.cohort_month,
    ca.months_since_cohort,
    ca.active_customers,
    cs.cohort_size,
    ROUND(100.0 * ca.active_customers / cs.cohort_size, 2) as retention_rate,
    ca.cohort_revenue,
    ROUND(ca.cohort_revenue / ca.active_customers, 2) as revenue_per_active_customer
FROM cohort_activity ca
JOIN cohort_sizes cs ON ca.cohort_month = cs.cohort_month
ORDER BY ca.cohort_month, ca.months_since_cohort;
```

## Performance Optimization

### Index Strategies
**Krishna's Indexing Rules:**

**1. Clustered Index (Primary Key):**
```sql
-- Orders table - clustered on order_id
CREATE CLUSTERED INDEX IX_Orders_OrderID 
ON fct_orders (order_id);

-- Dimensions - cluster on surrogate key
CREATE CLUSTERED INDEX IX_Customer_CustomerKey
ON dim_customer (customer_key);
```

**2. Non-Clustered Indexes:**
```sql
-- Index frequently filtered columns
CREATE NONCLUSTERED INDEX IX_Orders_CustomerDate
ON fct_orders (customer_id, order_date)
INCLUDE (order_amount, order_status);

-- Covering index for common query
CREATE NONCLUSTERED INDEX IX_Orders_DateStatus
ON fct_orders (order_date, order_status)
INCLUDE (customer_id, order_amount, product_id);
```

**3. Filtered Indexes:**
```sql
-- Index only active records
CREATE NONCLUSTERED INDEX IX_Customers_Active
ON dim_customer (customer_id, customer_segment)
WHERE is_active = 1;
```

### Query Optimization Techniques
**Krishna's Performance Fixes:**

**BAD Query (Table Scan):**
```sql
-- Slow: No indexes, OR logic, functions on columns
SELECT *
FROM fct_orders
WHERE YEAR(order_date) = 2024
   OR customer_id IS NULL
   OR LOWER(order_status) = 'completed';
```

**GOOD Query (Index Seek):**
```sql
-- Fast: Uses indexes, sargable predicates
SELECT 
    order_id, customer_id, order_date, order_amount
FROM fct_orders WITH (INDEX(IX_Orders_DateStatus))
WHERE order_date >= '2024-01-01'
  AND order_date < '2025-01-01'
  AND order_status = 'completed'
  AND customer_id IS NOT NULL;
```

### Execution Plan Analysis
**Krishna's Debugging Process:**

```sql
-- Enable actual execution plan
SET STATISTICS TIME ON;
SET STATISTICS IO ON;

-- Run query
SELECT 
    c.customer_segment,
    COUNT(*) as customer_count,
    SUM(o.order_amount) as total_revenue
FROM dim_customer c
LEFT JOIN fct_orders o ON c.customer_id = o.customer_id
WHERE c.is_active = 1
  AND o.order_date >= '2024-01-01'
GROUP BY c.customer_segment;

-- Check for:
-- 1. Table scans → Add indexes
-- 2. Hash matches → Consider merge join
-- 3. High logical reads → Add covering index
-- 4. Implicit conversions → Fix data types
```

## Complex Interview Questions

### 1. Second Highest Salary
**Krishna's Approach:**
```sql
-- Method 1: Using ROW_NUMBER
WITH ranked_salaries AS (
    SELECT 
        salary,
        ROW_NUMBER() OVER (ORDER BY salary DESC) as rn
    FROM employees
    GROUP BY salary
)
SELECT salary as second_highest_salary
FROM ranked_salaries
WHERE rn = 2;

-- Method 2: Using OFFSET-FETCH
SELECT DISTINCT salary as second_highest_salary
FROM employees
ORDER BY salary DESC
OFFSET 1 ROW
FETCH NEXT 1 ROW ONLY;
```

### 2. Find Duplicates
```sql
-- Find duplicate customer records
SELECT 
    customer_email,
    COUNT(*) as duplicate_count,
    STRING_AGG(CAST(customer_id AS VARCHAR), ', ') as duplicate_ids
FROM dim_customer
GROUP BY customer_email
HAVING COUNT(*) > 1
ORDER BY duplicate_count DESC;
```

### 3. Running Total with Reset
```sql
-- Daily sales with running total that resets monthly
SELECT
    order_date,
    daily_sales,
    SUM(daily_sales) OVER (
        PARTITION BY YEAR(order_date), MONTH(order_date)
        ORDER BY order_date
    ) as monthly_running_total
FROM daily_sales_summary;
```

### 4. Customer Churn Analysis
```sql
-- Identify churned customers (no order in 90 days)
WITH last_orders AS (
    SELECT
        customer_id,
        MAX(order_date) as last_order_date,
        COUNT(*) as total_orders,
        SUM(order_amount) as lifetime_value
    FROM fct_orders
    GROUP BY customer_id
)
SELECT
    c.customer_id,
    c.customer_name,
    c.customer_segment,
    lo.last_order_date,
    DATEDIFF(day, lo.last_order_date, GETDATE()) as days_since_last_order,
    lo.total_orders,
    lo.lifetime_value,
    CASE
        WHEN DATEDIFF(day, lo.last_order_date, GETDATE()) > 180 THEN 'High Risk'
        WHEN DATEDIFF(day, lo.last_order_date, GETDATE()) > 90 THEN 'At Risk'
        ELSE 'Active'
    END as churn_status
FROM dim_customer c
LEFT JOIN last_orders lo ON c.customer_id = lo.customer_id
WHERE c.is_active = 1
ORDER BY days_since_last_order DESC;
```

### 5. Gap Analysis
```sql
-- Find missing dates in order sequence
WITH date_range AS (
    SELECT CAST('2024-01-01' AS DATE) as date
    UNION ALL
    SELECT DATEADD(day, 1, date)
    FROM date_range
    WHERE date < '2024-12-31'
),
actual_dates AS (
    SELECT DISTINCT order_date
    FROM fct_orders
    WHERE order_date >= '2024-01-01'
)
SELECT dr.date as missing_date
FROM date_range dr
LEFT JOIN actual_dates ad ON dr.date = ad.order_date
WHERE ad.order_date IS NULL
  AND DATEPART(weekday, dr.date) NOT IN (1, 7);  -- Exclude weekends
```

## Business-Focused SQL

### Revenue Analysis
**Krishna's Executive Queries:**

```sql
-- Comprehensive revenue analysis for CFO
SELECT
    DATE_TRUNC('month', order_date) as month,
    
    -- Current month metrics
    SUM(order_amount) as gross_revenue,
    SUM(CASE WHEN order_status = 'returned' THEN order_amount ELSE 0 END) as returns,
    SUM(order_amount) - SUM(CASE WHEN order_status = 'returned' THEN order_amount ELSE 0 END) as net_revenue,
    COUNT(DISTINCT order_id) as order_count,
    COUNT(DISTINCT customer_id) as unique_customers,
    SUM(order_amount) / NULLIF(COUNT(DISTINCT customer_id), 0) as revenue_per_customer,
    
    -- YoY comparison
    LAG(SUM(order_amount), 12) OVER (ORDER BY DATE_TRUNC('month', order_date)) as revenue_same_month_last_year,
    ROUND(100.0 * (SUM(order_amount) - LAG(SUM(order_amount), 12) OVER (ORDER BY DATE_TRUNC('month', order_date))) /
          NULLIF(LAG(SUM(order_amount), 12) OVER (ORDER BY DATE_TRUNC('month', order_date)), 0), 2) as yoy_growth_pct
          
FROM fct_orders
WHERE order_date >= '2023-01-01'
GROUP BY DATE_TRUNC('month', order_date)
ORDER BY month DESC;
```

This SQL expertise helps me solve complex business problems and optimize data pipelines at Walgreens!

