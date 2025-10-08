---
tags: [sql, advanced-sql, window-functions, cte, optimization, healthcare, medicaid]
persona: tejuu
---

# Advanced SQL for Business Analysis - Tejuu's Expertise

## Healthcare & Medicaid Analytics SQL

### Claims Analysis at Stryker
**Tejuu's Real-World SQL for Medicaid:**

```sql
-- Medicaid Claims Analysis with Payment Patterns
WITH claim_summary AS (
    SELECT 
        claim_id,
        patient_id,
        provider_id,
        claim_date,
        service_date,
        claim_amount,
        paid_amount,
        denied_amount,
        claim_status,
        denial_reason,
        payer_name,
        DATEDIFF(day, service_date, claim_date) as days_to_submit,
        DATEDIFF(day, claim_date, payment_date) as days_to_payment
    FROM fact_claims
    WHERE payer_type = 'Medicaid'
        AND claim_date >= '2023-01-01'
),
payment_metrics AS (
    SELECT 
        provider_id,
        COUNT(*) as total_claims,
        SUM(claim_amount) as total_billed,
        SUM(paid_amount) as total_paid,
        SUM(denied_amount) as total_denied,
        AVG(paid_amount) as avg_payment,
        AVG(days_to_payment) as avg_days_to_payment,
        SUM(CASE WHEN claim_status = 'Denied' THEN 1 ELSE 0 END) as denied_count,
        SUM(CASE WHEN claim_status = 'Paid' THEN 1 ELSE 0 END) as paid_count
    FROM claim_summary
    GROUP BY provider_id
)
SELECT 
    p.provider_id,
    p.provider_name,
    p.provider_specialty,
    pm.total_claims,
    pm.total_billed,
    pm.total_paid,
    ROUND((pm.total_paid / NULLIF(pm.total_billed, 0)) * 100, 2) as payment_rate_pct,
    pm.denied_count,
    ROUND((pm.denied_count * 100.0 / pm.total_claims), 2) as denial_rate_pct,
    pm.avg_payment,
    pm.avg_days_to_payment,
    CASE 
        WHEN pm.avg_days_to_payment <= 30 THEN 'Fast'
        WHEN pm.avg_days_to_payment <= 60 THEN 'Average'
        ELSE 'Slow'
    END as payment_speed_category
FROM payment_metrics pm
JOIN dim_provider p ON pm.provider_id = p.provider_id
WHERE pm.total_claims >= 10  -- Minimum volume threshold
ORDER BY pm.total_billed DESC;
```

### Patient Readmission Analysis
**30-Day Readmission Tracking:**

```sql
-- Identify 30-Day Hospital Readmissions
WITH patient_visits AS (
    SELECT 
        patient_id,
        visit_id,
        admission_date,
        discharge_date,
        diagnosis_code,
        drg_code,
        facility_id,
        LEAD(admission_date) OVER (
            PARTITION BY patient_id 
            ORDER BY admission_date
        ) as next_admission_date,
        LEAD(visit_id) OVER (
            PARTITION BY patient_id 
            ORDER BY admission_date
        ) as next_visit_id
    FROM fact_patient_visits
    WHERE discharge_date IS NOT NULL
        AND admission_date >= '2023-01-01'
),
readmissions AS (
    SELECT 
        patient_id,
        visit_id as initial_visit_id,
        next_visit_id as readmission_visit_id,
        admission_date as initial_admission,
        discharge_date as initial_discharge,
        next_admission_date as readmission_date,
        DATEDIFF(day, discharge_date, next_admission_date) as days_between_visits,
        diagnosis_code as initial_diagnosis,
        drg_code as initial_drg
    FROM patient_visits
    WHERE next_admission_date IS NOT NULL
        AND DATEDIFF(day, discharge_date, next_admission_date) <= 30
)
SELECT 
    r.patient_id,
    p.patient_name,
    p.age,
    p.gender,
    r.initial_visit_id,
    r.readmission_visit_id,
    r.initial_admission,
    r.initial_discharge,
    r.readmission_date,
    r.days_between_visits,
    r.initial_diagnosis,
    d.diagnosis_description,
    r.initial_drg,
    drg.drg_description,
    f.facility_name,
    CASE 
        WHEN r.days_between_visits <= 7 THEN 'Very High Risk'
        WHEN r.days_between_visits <= 14 THEN 'High Risk'
        WHEN r.days_between_visits <= 21 THEN 'Medium Risk'
        ELSE 'Low Risk'
    END as readmission_risk_category
FROM readmissions r
JOIN dim_patient p ON r.patient_id = p.patient_id
JOIN dim_diagnosis d ON r.initial_diagnosis = d.diagnosis_code
JOIN dim_drg drg ON r.initial_drg = drg.drg_code
JOIN fact_patient_visits v ON r.initial_visit_id = v.visit_id
JOIN dim_facility f ON v.facility_id = f.facility_id
ORDER BY r.days_between_visits, r.readmission_date DESC;

-- Readmission Rate by Diagnosis
SELECT 
    d.diagnosis_code,
    d.diagnosis_description,
    COUNT(DISTINCT v.visit_id) as total_discharges,
    COUNT(DISTINCT r.readmission_visit_id) as readmissions,
    ROUND((COUNT(DISTINCT r.readmission_visit_id) * 100.0 / 
           COUNT(DISTINCT v.visit_id)), 2) as readmission_rate_pct,
    AVG(r.days_between_visits) as avg_days_to_readmission
FROM fact_patient_visits v
JOIN dim_diagnosis d ON v.primary_diagnosis = d.diagnosis_code
LEFT JOIN readmissions r ON v.visit_id = r.initial_visit_id
WHERE v.discharge_date >= '2023-01-01'
GROUP BY d.diagnosis_code, d.diagnosis_description
HAVING COUNT(DISTINCT v.visit_id) >= 20  -- Minimum volume
ORDER BY readmission_rate_pct DESC;
```

## Advanced Window Functions for Business Analytics

### Sales Performance Analysis
**Tejuu's Sales Analytics at CVS Health:**

```sql
-- Comprehensive Sales Performance with Rankings and Trends
WITH daily_sales AS (
    SELECT 
        sale_date,
        product_id,
        store_id,
        region,
        SUM(quantity) as units_sold,
        SUM(sales_amount) as daily_sales,
        SUM(cost_amount) as daily_cost
    FROM fact_sales
    WHERE sale_date >= '2023-01-01'
    GROUP BY sale_date, product_id, store_id, region
),
sales_with_metrics AS (
    SELECT 
        sale_date,
        product_id,
        store_id,
        region,
        daily_sales,
        daily_cost,
        daily_sales - daily_cost as daily_profit,
        
        -- Running totals
        SUM(daily_sales) OVER (
            PARTITION BY product_id, store_id 
            ORDER BY sale_date
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) as running_total_sales,
        
        -- Moving averages
        AVG(daily_sales) OVER (
            PARTITION BY product_id, store_id 
            ORDER BY sale_date
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ) as moving_avg_7day,
        
        AVG(daily_sales) OVER (
            PARTITION BY product_id, store_id 
            ORDER BY sale_date
            ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
        ) as moving_avg_30day,
        
        -- Year-over-year comparison
        LAG(daily_sales, 365) OVER (
            PARTITION BY product_id, store_id 
            ORDER BY sale_date
        ) as sales_last_year,
        
        -- Month-over-month comparison
        LAG(daily_sales, 30) OVER (
            PARTITION BY product_id, store_id 
            ORDER BY sale_date
        ) as sales_last_month,
        
        -- Rankings
        RANK() OVER (
            PARTITION BY sale_date, region 
            ORDER BY daily_sales DESC
        ) as daily_rank_in_region,
        
        DENSE_RANK() OVER (
            PARTITION BY DATE_TRUNC('month', sale_date), region 
            ORDER BY SUM(daily_sales) OVER (
                PARTITION BY product_id, store_id, DATE_TRUNC('month', sale_date)
            ) DESC
        ) as monthly_rank_in_region,
        
        -- Percentiles
        PERCENT_RANK() OVER (
            PARTITION BY region 
            ORDER BY daily_sales
        ) as sales_percentile
        
    FROM daily_sales
)
SELECT 
    sale_date,
    p.product_name,
    s.store_name,
    sm.region,
    sm.daily_sales,
    sm.daily_profit,
    sm.running_total_sales,
    sm.moving_avg_7day,
    sm.moving_avg_30day,
    sm.sales_last_year,
    ROUND(((sm.daily_sales - sm.sales_last_year) / 
           NULLIF(sm.sales_last_year, 0)) * 100, 2) as yoy_growth_pct,
    sm.daily_rank_in_region,
    sm.monthly_rank_in_region,
    ROUND(sm.sales_percentile * 100, 2) as sales_percentile_rank,
    CASE 
        WHEN sm.daily_sales > sm.moving_avg_30day * 1.2 THEN 'High Performance'
        WHEN sm.daily_sales < sm.moving_avg_30day * 0.8 THEN 'Low Performance'
        ELSE 'Normal'
    END as performance_category
FROM sales_with_metrics sm
JOIN dim_product p ON sm.product_id = p.product_id
JOIN dim_store s ON sm.store_id = s.store_id
WHERE sale_date >= '2024-01-01'
ORDER BY sale_date DESC, sm.daily_sales DESC;
```

### Customer Cohort Analysis
**Retention and Lifetime Value:**

```sql
-- Customer Cohort Analysis with Retention Rates
WITH first_purchase AS (
    SELECT 
        customer_id,
        MIN(order_date) as cohort_month,
        MIN(order_id) as first_order_id
    FROM fact_orders
    GROUP BY customer_id
),
customer_orders AS (
    SELECT 
        o.customer_id,
        o.order_date,
        o.order_amount,
        fp.cohort_month,
        DATE_TRUNC('month', o.order_date) as order_month,
        DATEDIFF(month, fp.cohort_month, DATE_TRUNC('month', o.order_date)) as months_since_first
    FROM fact_orders o
    JOIN first_purchase fp ON o.customer_id = fp.customer_id
    WHERE o.order_date >= '2023-01-01'
),
cohort_data AS (
    SELECT 
        cohort_month,
        months_since_first,
        COUNT(DISTINCT customer_id) as customers,
        SUM(order_amount) as total_revenue,
        AVG(order_amount) as avg_order_value
    FROM customer_orders
    GROUP BY cohort_month, months_since_first
),
cohort_size AS (
    SELECT 
        cohort_month,
        COUNT(DISTINCT customer_id) as cohort_size
    FROM first_purchase
    GROUP BY cohort_month
)
SELECT 
    cd.cohort_month,
    cs.cohort_size,
    cd.months_since_first,
    cd.customers,
    ROUND((cd.customers * 100.0 / cs.cohort_size), 2) as retention_rate_pct,
    cd.total_revenue,
    cd.avg_order_value,
    SUM(cd.total_revenue) OVER (
        PARTITION BY cd.cohort_month 
        ORDER BY cd.months_since_first
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) as cumulative_revenue,
    ROUND(SUM(cd.total_revenue) OVER (
        PARTITION BY cd.cohort_month 
        ORDER BY cd.months_since_first
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) / cs.cohort_size, 2) as lifetime_value
FROM cohort_data cd
JOIN cohort_size cs ON cd.cohort_month = cs.cohort_month
ORDER BY cd.cohort_month, cd.months_since_first;
```

## Complex CTEs and Recursive Queries

### Organizational Hierarchy Analysis
**Tejuu's HR Analytics:**

```sql
-- Recursive CTE for Employee Hierarchy
WITH RECURSIVE employee_hierarchy AS (
    -- Base case: Top-level managers (no manager)
    SELECT 
        employee_id,
        employee_name,
        manager_id,
        job_title,
        department,
        salary,
        1 as level,
        CAST(employee_name AS VARCHAR(1000)) as hierarchy_path,
        CAST(employee_id AS VARCHAR(1000)) as id_path
    FROM dim_employee
    WHERE manager_id IS NULL
    
    UNION ALL
    
    -- Recursive case: Employees with managers
    SELECT 
        e.employee_id,
        e.employee_name,
        e.manager_id,
        e.job_title,
        e.department,
        e.salary,
        eh.level + 1,
        CAST(eh.hierarchy_path || ' > ' || e.employee_name AS VARCHAR(1000)),
        CAST(eh.id_path || '>' || e.employee_id AS VARCHAR(1000))
    FROM dim_employee e
    INNER JOIN employee_hierarchy eh ON e.manager_id = eh.employee_id
    WHERE eh.level < 10  -- Prevent infinite recursion
),
team_metrics AS (
    SELECT 
        eh.employee_id,
        eh.employee_name,
        eh.level,
        COUNT(DISTINCT e2.employee_id) as direct_reports,
        COUNT(DISTINCT e3.employee_id) as total_team_size,
        AVG(e3.salary) as avg_team_salary,
        SUM(e3.salary) as total_team_cost
    FROM employee_hierarchy eh
    LEFT JOIN dim_employee e2 ON eh.employee_id = e2.manager_id
    LEFT JOIN employee_hierarchy e3 ON e3.id_path LIKE eh.id_path || '%'
    GROUP BY eh.employee_id, eh.employee_name, eh.level
)
SELECT 
    eh.employee_id,
    eh.employee_name,
    eh.job_title,
    eh.department,
    eh.salary,
    eh.level,
    eh.hierarchy_path,
    tm.direct_reports,
    tm.total_team_size,
    tm.avg_team_salary,
    tm.total_team_cost,
    ROUND((eh.salary / NULLIF(tm.avg_team_salary, 0)), 2) as salary_vs_team_avg
FROM employee_hierarchy eh
JOIN team_metrics tm ON eh.employee_id = tm.employee_id
ORDER BY eh.level, eh.employee_name;
```

### Product Category Hierarchy
**Inventory Analysis with Rollups:**

```sql
-- Product Category Hierarchy with Sales Rollup
WITH RECURSIVE category_hierarchy AS (
    SELECT 
        category_id,
        category_name,
        parent_category_id,
        1 as level,
        CAST(category_name AS VARCHAR(500)) as category_path
    FROM dim_category
    WHERE parent_category_id IS NULL
    
    UNION ALL
    
    SELECT 
        c.category_id,
        c.category_name,
        c.parent_category_id,
        ch.level + 1,
        CAST(ch.category_path || ' > ' || c.category_name AS VARCHAR(500))
    FROM dim_category c
    INNER JOIN category_hierarchy ch ON c.parent_category_id = ch.category_id
),
sales_by_category AS (
    SELECT 
        p.category_id,
        SUM(s.sales_amount) as total_sales,
        SUM(s.quantity) as total_quantity,
        COUNT(DISTINCT s.order_id) as order_count,
        COUNT(DISTINCT s.customer_id) as customer_count
    FROM fact_sales s
    JOIN dim_product p ON s.product_id = p.product_id
    WHERE s.sale_date >= '2024-01-01'
    GROUP BY p.category_id
)
SELECT 
    ch.category_id,
    ch.category_name,
    ch.parent_category_id,
    ch.level,
    ch.category_path,
    COALESCE(sc.total_sales, 0) as direct_sales,
    COALESCE(sc.total_quantity, 0) as direct_quantity,
    SUM(COALESCE(sc2.total_sales, 0)) as total_sales_with_children,
    SUM(COALESCE(sc2.total_quantity, 0)) as total_quantity_with_children
FROM category_hierarchy ch
LEFT JOIN sales_by_category sc ON ch.category_id = sc.category_id
LEFT JOIN category_hierarchy ch2 ON ch2.category_path LIKE ch.category_path || '%'
LEFT JOIN sales_by_category sc2 ON ch2.category_id = sc2.category_id
GROUP BY 
    ch.category_id,
    ch.category_name,
    ch.parent_category_id,
    ch.level,
    ch.category_path,
    sc.total_sales,
    sc.total_quantity
ORDER BY ch.category_path;
```

## Data Quality and Validation SQL

### Comprehensive Data Quality Checks
**Tejuu's Data Validation Framework:**

```sql
-- Data Quality Report
WITH null_checks AS (
    SELECT 
        'fact_sales' as table_name,
        'customer_id' as column_name,
        COUNT(*) as total_records,
        SUM(CASE WHEN customer_id IS NULL THEN 1 ELSE 0 END) as null_count,
        ROUND(SUM(CASE WHEN customer_id IS NULL THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as null_percentage
    FROM fact_sales
    WHERE sale_date >= CURRENT_DATE - INTERVAL '30 days'
    
    UNION ALL
    
    SELECT 
        'fact_sales',
        'sale_date',
        COUNT(*),
        SUM(CASE WHEN sale_date IS NULL THEN 1 ELSE 0 END),
        ROUND(SUM(CASE WHEN sale_date IS NULL THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2)
    FROM fact_sales
    WHERE sale_date >= CURRENT_DATE - INTERVAL '30 days'
    
    UNION ALL
    
    SELECT 
        'fact_sales',
        'sales_amount',
        COUNT(*),
        SUM(CASE WHEN sales_amount IS NULL THEN 1 ELSE 0 END),
        ROUND(SUM(CASE WHEN sales_amount IS NULL THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2)
    FROM fact_sales
    WHERE sale_date >= CURRENT_DATE - INTERVAL '30 days'
),
range_checks AS (
    SELECT 
        'fact_sales' as table_name,
        'sales_amount' as column_name,
        MIN(sales_amount) as min_value,
        MAX(sales_amount) as max_value,
        AVG(sales_amount) as avg_value,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY sales_amount) as median_value,
        SUM(CASE WHEN sales_amount < 0 THEN 1 ELSE 0 END) as negative_count,
        SUM(CASE WHEN sales_amount = 0 THEN 1 ELSE 0 END) as zero_count
    FROM fact_sales
    WHERE sale_date >= CURRENT_DATE - INTERVAL '30 days'
),
duplicate_checks AS (
    SELECT 
        'fact_sales' as table_name,
        'order_id' as key_column,
        COUNT(*) as total_records,
        COUNT(DISTINCT order_id) as unique_records,
        COUNT(*) - COUNT(DISTINCT order_id) as duplicate_count
    FROM fact_sales
    WHERE sale_date >= CURRENT_DATE - INTERVAL '30 days'
),
referential_integrity AS (
    SELECT 
        'fact_sales -> dim_customer' as relationship,
        COUNT(DISTINCT s.customer_id) as fact_keys,
        COUNT(DISTINCT c.customer_id) as dim_keys,
        COUNT(DISTINCT s.customer_id) - COUNT(DISTINCT c.customer_id) as orphaned_records
    FROM fact_sales s
    LEFT JOIN dim_customer c ON s.customer_id = c.customer_id
    WHERE s.sale_date >= CURRENT_DATE - INTERVAL '30 days'
)
SELECT 
    'Null Checks' as check_type,
    table_name,
    column_name,
    null_count as issue_count,
    null_percentage as issue_percentage,
    CASE WHEN null_percentage > 5 THEN 'FAIL' ELSE 'PASS' END as status
FROM null_checks
WHERE null_count > 0

UNION ALL

SELECT 
    'Range Checks',
    table_name,
    column_name,
    negative_count + zero_count,
    ROUND((negative_count + zero_count) * 100.0 / 
          (SELECT COUNT(*) FROM fact_sales WHERE sale_date >= CURRENT_DATE - INTERVAL '30 days'), 2),
    CASE WHEN negative_count > 0 THEN 'FAIL' ELSE 'PASS' END
FROM range_checks

UNION ALL

SELECT 
    'Duplicate Checks',
    table_name,
    key_column,
    duplicate_count,
    ROUND(duplicate_count * 100.0 / total_records, 2),
    CASE WHEN duplicate_count > 0 THEN 'FAIL' ELSE 'PASS' END
FROM duplicate_checks

UNION ALL

SELECT 
    'Referential Integrity',
    relationship,
    '',
    orphaned_records,
    ROUND(orphaned_records * 100.0 / fact_keys, 2),
    CASE WHEN orphaned_records > 0 THEN 'FAIL' ELSE 'PASS' END
FROM referential_integrity;
```

## Interview Talking Points

### Technical Achievements
- Wrote 500+ SQL queries for business analytics
- Optimized slow queries from 5 minutes to 10 seconds
- Built automated data quality checks catching 95% of issues
- Created reusable SQL templates for common analyses
- Trained 15+ analysts on advanced SQL techniques

### Problem-Solving Examples
**Performance Optimization:**
"At Stryker, we had this Medicaid claims query that was taking 5 minutes to run. I analyzed the execution plan and found we were doing a full table scan on a 50 million row table. I added appropriate indexes on claim_date and provider_id, rewrote the query to use CTEs instead of subqueries, and got it down to 10 seconds."

**Complex Business Logic:**
"At Central Bank, finance needed a complex calculation for regulatory reporting that involved multiple date ranges, conditional aggregations, and hierarchical rollups. I broke it down into CTEs, tested each piece separately, and documented the logic. The final query was 200 lines but very maintainable and accurate."

### Tools & Technologies
- **Databases**: SQL Server, Oracle, PostgreSQL, MySQL
- **SQL Skills**: Window functions, CTEs, recursive queries, performance tuning
- **Tools**: SQL Server Management Studio, DBeaver, DataGrip
- **Integration**: Power BI, Tableau, Python, Excel
