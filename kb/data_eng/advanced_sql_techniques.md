---
tags: [sql, advanced, window-functions, cte, optimization, performance, interview]
persona: de
---

# Advanced SQL Techniques & Krishna's Real-World Applications

## Window Functions Mastery

### ROW_NUMBER, RANK, DENSE_RANK
**Krishna's Usage at Walgreens:**
```sql
-- Find top 3 customers by spending in each region
WITH customer_rankings AS (
    SELECT 
        customer_id,
        region,
        total_spent,
        ROW_NUMBER() OVER (PARTITION BY region ORDER BY total_spent DESC) as rn,
        RANK() OVER (PARTITION BY region ORDER BY total_spent DESC) as rank,
        DENSE_RANK() OVER (PARTITION BY region ORDER BY total_spent DESC) as dense_rank
    FROM customer_analytics
)
SELECT customer_id, region, total_spent, rank
FROM customer_rankings 
WHERE rank <= 3;

-- Practical application: Customer segmentation
SELECT 
    customer_id,
    total_spent,
    CASE 
        WHEN DENSE_RANK() OVER (ORDER BY total_spent DESC) <= 100 THEN 'VIP'
        WHEN DENSE_RANK() OVER (ORDER BY total_spent DESC) <= 1000 THEN 'Premium'
        ELSE 'Standard'
    END as customer_tier
FROM customer_analytics;
```

### LAG, LEAD for Time Series Analysis
**Krishna's Pharmacy Analytics:**
```sql
-- Calculate month-over-month growth in pharmacy sales
WITH monthly_sales AS (
    SELECT 
        DATE_TRUNC('month', sale_date) as month,
        SUM(amount) as total_sales
    FROM pharmacy_transactions
    GROUP BY DATE_TRUNC('month', sale_date)
),
sales_with_lag AS (
    SELECT 
        month,
        total_sales,
        LAG(total_sales, 1) OVER (ORDER BY month) as prev_month_sales,
        LAG(total_sales, 12) OVER (ORDER BY month) as prev_year_sales
    FROM monthly_sales
)
SELECT 
    month,
    total_sales,
    ROUND(((total_sales - prev_month_sales) / prev_month_sales) * 100, 2) as mom_growth,
    ROUND(((total_sales - prev_year_sales) / prev_year_sales) * 100, 2) as yoy_growth
FROM sales_with_lag
ORDER BY month;
```

### Running Totals and Moving Averages
**Krishna's Supply Chain Analytics:**
```sql
-- Calculate 7-day moving average for inventory levels
SELECT 
    product_id,
    date,
    inventory_level,
    AVG(inventory_level) OVER (
        PARTITION BY product_id 
        ORDER BY date 
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) as moving_avg_7day,
    SUM(inventory_level) OVER (
        PARTITION BY product_id 
        ORDER BY date 
        ROWS UNBOUNDED PRECEDING
    ) as running_total
FROM daily_inventory
WHERE date >= '2023-01-01';
```

## Common Table Expressions (CTEs)

### Recursive CTEs for Hierarchical Data
**Krishna's Organizational Structure Analysis:**
```sql
-- Find all employees under a manager (recursive hierarchy)
WITH RECURSIVE employee_hierarchy AS (
    -- Base case: top-level managers
    SELECT 
        employee_id,
        employee_name,
        manager_id,
        1 as level,
        CAST(employee_name AS VARCHAR(1000)) as hierarchy_path
    FROM employees
    WHERE manager_id IS NULL
    
    UNION ALL
    
    -- Recursive case: employees under managers
    SELECT 
        e.employee_id,
        e.employee_name,
        e.manager_id,
        eh.level + 1,
        CAST(eh.hierarchy_path || ' -> ' || e.employee_name AS VARCHAR(1000))
    FROM employees e
    INNER JOIN employee_hierarchy eh ON e.manager_id = eh.employee_id
    WHERE eh.level < 10  -- Prevent infinite recursion
)
SELECT employee_id, employee_name, level, hierarchy_path
FROM employee_hierarchy
ORDER BY level, employee_name;
```

### Multiple CTEs for Complex Analytics
**Krishna's Customer Churn Analysis:**
```sql
WITH customer_activity AS (
    SELECT 
        customer_id,
        MAX(order_date) as last_order_date,
        COUNT(*) as total_orders,
        SUM(amount) as total_spent
    FROM orders
    GROUP BY customer_id
),
churn_classification AS (
    SELECT 
        customer_id,
        last_order_date,
        total_orders,
        total_spent,
        CASE 
            WHEN last_order_date < CURRENT_DATE - INTERVAL '90 days' THEN 'Churned'
            WHEN last_order_date < CURRENT_DATE - INTERVAL '30 days' THEN 'At Risk'
            ELSE 'Active'
        END as churn_status
    FROM customer_activity
),
churn_metrics AS (
    SELECT 
        churn_status,
        COUNT(*) as customer_count,
        AVG(total_spent) as avg_spent,
        AVG(total_orders) as avg_orders
    FROM churn_classification
    GROUP BY churn_status
)
SELECT 
    churn_status,
    customer_count,
    ROUND(avg_spent, 2) as avg_spent,
    ROUND(avg_orders, 1) as avg_orders,
    ROUND((customer_count * 100.0 / SUM(customer_count) OVER()), 2) as percentage
FROM churn_metrics
ORDER BY customer_count DESC;
```

## Advanced Joins and Set Operations

### Self Joins for Complex Relationships
**Krishna's Product Recommendation Analysis:**
```sql
-- Find customers who bought similar products
SELECT DISTINCT
    c1.customer_id as customer_1,
    c2.customer_id as customer_2,
    COUNT(*) as common_products
FROM customer_products c1
INNER JOIN customer_products c2 ON c1.product_id = c2.product_id
WHERE c1.customer_id < c2.customer_id  -- Avoid duplicates
GROUP BY c1.customer_id, c2.customer_id
HAVING COUNT(*) >= 3  -- At least 3 common products
ORDER BY common_products DESC;
```

### Lateral Joins for Correlated Subqueries
**Krishna's Top-N Analysis:**
```sql
-- Find top 3 products for each category
SELECT 
    c.category_name,
    p.product_name,
    p.sales_amount,
    p.rank
FROM categories c
CROSS JOIN LATERAL (
    SELECT 
        product_name,
        sales_amount,
        ROW_NUMBER() OVER (ORDER BY sales_amount DESC) as rank
    FROM products p2
    WHERE p2.category_id = c.category_id
    ORDER BY sales_amount DESC
    LIMIT 3
) p
ORDER BY c.category_name, p.rank;
```

## Performance Optimization Techniques

### Indexing Strategies
**Krishna's Query Optimization:**
```sql
-- Composite index for multi-column queries
CREATE INDEX idx_orders_customer_date ON orders(customer_id, order_date);

-- Partial index for frequently queried subset
CREATE INDEX idx_active_orders ON orders(order_date) 
WHERE status = 'active';

-- Covering index to avoid table lookups
CREATE INDEX idx_customer_covering ON orders(customer_id, order_date, amount, status)
INCLUDE (order_id, product_id);

-- Query using the covering index
SELECT customer_id, order_date, amount
FROM orders
WHERE customer_id = 12345 
  AND order_date >= '2023-01-01';
```

### Query Rewriting for Performance
**Krishna's Optimization Examples:**

**Before (Slow):**
```sql
SELECT customer_id, COUNT(*)
FROM orders
WHERE order_date >= '2023-01-01'
  AND customer_id IN (
    SELECT customer_id 
    FROM customers 
    WHERE region = 'West'
  )
GROUP BY customer_id;
```

**After (Optimized):**
```sql
SELECT o.customer_id, COUNT(*)
FROM orders o
INNER JOIN customers c ON o.customer_id = c.customer_id
WHERE o.order_date >= '2023-01-01'
  AND c.region = 'West'
GROUP BY o.customer_id;
```

## Advanced Aggregation Techniques

### PIVOT and UNPIVOT
**Krishna's Sales Analysis:**
```sql
-- Pivot: Convert rows to columns
SELECT 
    product_category,
    SUM(CASE WHEN region = 'North' THEN sales_amount ELSE 0 END) as north_sales,
    SUM(CASE WHEN region = 'South' THEN sales_amount ELSE 0 END) as south_sales,
    SUM(CASE WHEN region = 'East' THEN sales_amount ELSE 0 END) as east_sales,
    SUM(CASE WHEN region = 'West' THEN sales_amount ELSE 0 END) as west_sales
FROM sales_data
GROUP BY product_category;

-- Unpivot: Convert columns to rows
WITH pivoted_data AS (
    SELECT product_category, north_sales, south_sales, east_sales, west_sales
    FROM sales_summary
)
SELECT 
    product_category,
    region,
    sales_amount
FROM pivoted_data
UNPIVOT (
    sales_amount FOR region IN (north_sales, south_sales, east_sales, west_sales)
) AS unpvt;
```

### GROUPING SETS and ROLLUP
**Krishna's Multi-Dimensional Analysis:**
```sql
-- Multi-level aggregation
SELECT 
    COALESCE(region, 'ALL REGIONS') as region,
    COALESCE(product_category, 'ALL CATEGORIES') as category,
    COUNT(*) as order_count,
    SUM(amount) as total_amount
FROM orders
GROUP BY GROUPING SETS (
    (region, product_category),
    (region),
    (product_category),
    ()
)
ORDER BY region, category;
```

## Data Quality and Validation

### Data Quality Checks
**Krishna's Data Validation Framework:**
```sql
-- Comprehensive data quality report
WITH data_quality_checks AS (
    SELECT 
        'orders' as table_name,
        COUNT(*) as total_records,
        COUNT(CASE WHEN order_id IS NULL THEN 1 END) as null_order_ids,
        COUNT(CASE WHEN customer_id IS NULL THEN 1 END) as null_customer_ids,
        COUNT(CASE WHEN order_date IS NULL THEN 1 END) as null_dates,
        COUNT(CASE WHEN amount <= 0 THEN 1 END) as invalid_amounts,
        COUNT(CASE WHEN order_date > CURRENT_DATE THEN 1 END) as future_dates
    FROM orders
    UNION ALL
    SELECT 
        'customers' as table_name,
        COUNT(*) as total_records,
        COUNT(CASE WHEN customer_id IS NULL THEN 1 END) as null_customer_ids,
        COUNT(CASE WHEN email IS NULL THEN 1 END) as null_emails,
        COUNT(CASE WHEN email NOT LIKE '%@%' THEN 1 END) as invalid_emails,
        COUNT(CASE WHEN phone IS NULL THEN 1 END) as null_phones,
        COUNT(CASE WHEN created_date > CURRENT_DATE THEN 1 END) as future_dates
    FROM customers
)
SELECT 
    table_name,
    total_records,
    ROUND((null_order_ids * 100.0 / total_records), 2) as null_order_id_pct,
    ROUND((null_customer_ids * 100.0 / total_records), 2) as null_customer_id_pct,
    ROUND((invalid_amounts * 100.0 / total_records), 2) as invalid_amount_pct
FROM data_quality_checks;
```

## Interview-Ready SQL Patterns

### Common Interview Questions with Krishna's Solutions

**1. Find Second Highest Salary:**
```sql
-- Method 1: Using ROW_NUMBER
SELECT salary
FROM (
    SELECT salary, ROW_NUMBER() OVER (ORDER BY salary DESC) as rn
    FROM employees
) ranked
WHERE rn = 2;

-- Method 2: Using MAX with subquery
SELECT MAX(salary)
FROM employees
WHERE salary < (SELECT MAX(salary) FROM employees);

-- Method 3: Using DENSE_RANK (handles ties)
SELECT salary
FROM (
    SELECT salary, DENSE_RANK() OVER (ORDER BY salary DESC) as dr
    FROM employees
) ranked
WHERE dr = 2;
```

**2. Find Duplicates:**
```sql
-- Find duplicate records
SELECT email, COUNT(*) as duplicate_count
FROM customers
GROUP BY email
HAVING COUNT(*) > 1;

-- Delete duplicates (keep one)
DELETE FROM customers
WHERE customer_id NOT IN (
    SELECT MIN(customer_id)
    FROM customers
    GROUP BY email
);
```

**3. Calculate Running Totals:**
```sql
SELECT 
    order_date,
    amount,
    SUM(amount) OVER (ORDER BY order_date) as running_total,
    AVG(amount) OVER (ORDER BY order_date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) as moving_avg_7day
FROM orders
ORDER BY order_date;
```

## Krishna's Performance Tips

### Query Optimization Best Practices:
1. **Use EXPLAIN ANALYZE** to understand query execution plans
2. **Avoid SELECT *** - specify only needed columns
3. **Use appropriate JOIN types** - INNER vs LEFT vs RIGHT
4. **Leverage indexes** - create composite indexes for multi-column queries
5. **Use LIMIT** for large result sets
6. **Consider materialized views** for complex aggregations
7. **Use window functions** instead of correlated subqueries when possible

### Real-World Performance Gains:
- **Query optimization**: Reduced average query time from 45 seconds to 8 seconds
- **Index strategy**: Improved join performance by 60%
- **Window functions**: Replaced complex subqueries, reducing execution time by 40%
- **Data partitioning**: Enabled parallel processing, improving throughput by 3x

## Advanced SQL Interview Scenarios

### Scenario 1: E-commerce Analytics
**Question**: "How would you analyze customer purchase patterns?"

**Krishna's Solution**:
```sql
WITH customer_metrics AS (
    SELECT 
        customer_id,
        COUNT(DISTINCT order_date) as active_days,
        COUNT(*) as total_orders,
        SUM(amount) as total_spent,
        AVG(amount) as avg_order_value,
        MIN(order_date) as first_order,
        MAX(order_date) as last_order,
        DATEDIFF(MAX(order_date), MIN(order_date)) as customer_lifespan_days
    FROM orders
    GROUP BY customer_id
),
customer_segments AS (
    SELECT 
        customer_id,
        total_spent,
        avg_order_value,
        CASE 
            WHEN total_spent > 1000 AND avg_order_value > 100 THEN 'High Value'
            WHEN total_spent > 500 THEN 'Medium Value'
            ELSE 'Low Value'
        END as customer_segment,
        CASE 
            WHEN DATEDIFF(CURRENT_DATE, last_order) <= 30 THEN 'Active'
            WHEN DATEDIFF(CURRENT_DATE, last_order) <= 90 THEN 'At Risk'
            ELSE 'Inactive'
        END as customer_status
    FROM customer_metrics
)
SELECT 
    customer_segment,
    customer_status,
    COUNT(*) as customer_count,
    AVG(total_spent) as avg_spent,
    AVG(avg_order_value) as avg_order_value
FROM customer_segments
GROUP BY customer_segment, customer_status
ORDER BY customer_segment, customer_status;
```

### Scenario 2: Time Series Analysis
**Question**: "How would you detect anomalies in daily sales?"

**Krishna's Solution**:
```sql
WITH daily_sales AS (
    SELECT 
        sale_date,
        SUM(amount) as daily_total
    FROM sales
    GROUP BY sale_date
),
sales_with_stats AS (
    SELECT 
        sale_date,
        daily_total,
        AVG(daily_total) OVER (ORDER BY sale_date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) as moving_avg,
        STDDEV(daily_total) OVER (ORDER BY sale_date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) as moving_stddev
    FROM daily_sales
)
SELECT 
    sale_date,
    daily_total,
    moving_avg,
    moving_stddev,
    CASE 
        WHEN ABS(daily_total - moving_avg) > 2 * moving_stddev THEN 'Anomaly'
        ELSE 'Normal'
    END as anomaly_flag
FROM sales_with_stats
WHERE ABS(daily_total - moving_avg) > 2 * moving_stddev
ORDER BY sale_date;
```
