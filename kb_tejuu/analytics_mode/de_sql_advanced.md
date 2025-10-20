---
tags: [data-engineer, sql, advanced, optimization, performance, tejuu]
persona: analytics
---

# Advanced SQL for Data Engineering - Tejuu's Experience

## Introduction
**Tejuu's SQL Expertise:**
At Central Bank of Missouri, I write complex SQL queries daily for data processing, analytics, and reporting. I've optimized queries that process millions of records, built sophisticated data models, and created self-service analytics solutions. My SQL skills are essential for my data engineering work, especially when working with Azure Synapse and Power BI. Let me share the advanced SQL patterns and optimization techniques I've mastered.

## Advanced Query Patterns

### 1. Window Functions
**Tejuu's Window Function Patterns:**

```sql
-- Customer analytics with window functions
WITH CustomerMetrics AS (
    SELECT 
        customer_id,
        customer_name,
        transaction_date,
        transaction_amount,
        -- Running totals
        SUM(transaction_amount) OVER (
            PARTITION BY customer_id 
            ORDER BY transaction_date 
            ROWS UNBOUNDED PRECEDING
        ) AS running_total,
        
        -- Customer ranking
        ROW_NUMBER() OVER (
            PARTITION BY customer_id 
            ORDER BY transaction_date DESC
        ) AS transaction_rank,
        
        -- Customer statistics
        COUNT(*) OVER (PARTITION BY customer_id) AS total_transactions,
        AVG(transaction_amount) OVER (PARTITION BY customer_id) AS avg_transaction_amount,
        MAX(transaction_amount) OVER (PARTITION BY customer_id) AS max_transaction_amount,
        MIN(transaction_amount) OVER (PARTITION BY customer_id) AS min_transaction_amount,
        
        -- Rolling calculations
        SUM(transaction_amount) OVER (
            PARTITION BY customer_id 
            ORDER BY transaction_date 
            ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
        ) AS rolling_30d_amount,
        
        -- Percentile calculations
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY transaction_amount) 
            OVER (PARTITION BY customer_id) AS median_transaction_amount,
        PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY transaction_amount) 
            OVER (PARTITION BY customer_id) AS p95_transaction_amount
    FROM fct_customer_transactions
    WHERE transaction_date >= DATEADD(month, -12, GETDATE())
)
SELECT 
    customer_id,
    customer_name,
    total_transactions,
    avg_transaction_amount,
    max_transaction_amount,
    median_transaction_amount,
    p95_transaction_amount,
    rolling_30d_amount
FROM CustomerMetrics
WHERE transaction_rank = 1  -- Latest transaction per customer
ORDER BY rolling_30d_amount DESC;
```

### 2. Common Table Expressions (CTEs)
**Tejuu's CTE Patterns:**

```sql
-- Complex business logic with CTEs
WITH 
-- Customer segmentation
CustomerSegmentation AS (
    SELECT 
        customer_id,
        customer_name,
        total_balance,
        CASE 
            WHEN total_balance >= 100000 THEN 'Premium'
            WHEN total_balance >= 50000 THEN 'Gold'
            WHEN total_balance >= 10000 THEN 'Silver'
            ELSE 'Bronze'
        END AS customer_segment
    FROM dim_customer
    WHERE is_current = 1
),

-- Transaction summary
TransactionSummary AS (
    SELECT 
        customer_id,
        COUNT(*) AS transaction_count,
        SUM(transaction_amount) AS total_amount,
        AVG(transaction_amount) AS avg_amount,
        MAX(transaction_date) AS last_transaction_date,
        MIN(transaction_date) AS first_transaction_date
    FROM fct_customer_transactions
    WHERE transaction_date >= DATEADD(month, -12, GETDATE())
    GROUP BY customer_id
),

-- Risk assessment
RiskAssessment AS (
    SELECT 
        customer_id,
        CASE 
            WHEN total_amount > 500000 THEN 'High'
            WHEN total_amount > 100000 THEN 'Medium'
            ELSE 'Low'
        END AS risk_level,
        CASE 
            WHEN DATEDIFF(day, last_transaction_date, GETDATE()) > 90 THEN 'Inactive'
            WHEN DATEDIFF(day, last_transaction_date, GETDATE()) > 30 THEN 'At Risk'
            ELSE 'Active'
        END AS activity_status
    FROM TransactionSummary
)

-- Final result
SELECT 
    cs.customer_id,
    cs.customer_name,
    cs.customer_segment,
    ts.transaction_count,
    ts.total_amount,
    ts.avg_amount,
    ts.last_transaction_date,
    ra.risk_level,
    ra.activity_status,
    DATEDIFF(day, ts.first_transaction_date, ts.last_transaction_date) AS customer_lifetime_days
FROM CustomerSegmentation cs
INNER JOIN TransactionSummary ts ON cs.customer_id = ts.customer_id
INNER JOIN RiskAssessment ra ON cs.customer_id = ra.customer_id
ORDER BY ts.total_amount DESC;
```

### 3. Recursive CTEs
**Tejuu's Recursive CTE Patterns:**

```sql
-- Hierarchical data processing (e.g., organizational structure)
WITH OrgHierarchy AS (
    -- Base case: top-level managers
    SELECT 
        employee_id,
        employee_name,
        manager_id,
        department,
        1 AS level,
        CAST(employee_name AS VARCHAR(MAX)) AS hierarchy_path
    FROM dim_employee
    WHERE manager_id IS NULL
    
    UNION ALL
    
    -- Recursive case: subordinates
    SELECT 
        e.employee_id,
        e.employee_name,
        e.manager_id,
        e.department,
        oh.level + 1,
        oh.hierarchy_path + ' -> ' + e.employee_name
    FROM dim_employee e
    INNER JOIN OrgHierarchy oh ON e.manager_id = oh.employee_id
    WHERE oh.level < 10  -- Prevent infinite recursion
)
SELECT 
    employee_id,
    employee_name,
    manager_id,
    department,
    level,
    hierarchy_path
FROM OrgHierarchy
ORDER BY level, employee_name;

-- Date range generation
WITH DateRange AS (
    -- Base case: start date
    SELECT CAST('2024-01-01' AS DATE) AS date_value
    
    UNION ALL
    
    -- Recursive case: next date
    SELECT DATEADD(day, 1, date_value)
    FROM DateRange
    WHERE date_value < '2024-12-31'
)
SELECT 
    date_value,
    YEAR(date_value) AS year,
    MONTH(date_value) AS month,
    DAY(date_value) AS day,
    DATENAME(weekday, date_value) AS day_name,
    CASE 
        WHEN DATEPART(weekday, date_value) IN (1, 7) THEN 1 
        ELSE 0 
    END AS is_weekend
FROM DateRange
OPTION (MAXRECURSION 366);  -- Allow up to 366 iterations
```

## Performance Optimization

### 1. Indexing Strategies
**Tejuu's Indexing Patterns:**

```sql
-- Clustered index for fact table
CREATE CLUSTERED INDEX IX_fct_transactions_date
ON fct_customer_transactions (transaction_date)
WITH (
    DATA_COMPRESSION = PAGE,
    FILLFACTOR = 90
);

-- Non-clustered index with included columns
CREATE NONCLUSTERED INDEX IX_fct_transactions_customer_lookup
ON fct_customer_transactions (customer_id)
INCLUDE (transaction_amount, transaction_type, transaction_date)
WITH (
    DATA_COMPRESSION = PAGE,
    FILLFACTOR = 90
);

-- Filtered index for active records
CREATE NONCLUSTERED INDEX IX_customers_active
ON dim_customer (customer_id)
WHERE is_current = 1
WITH (
    DATA_COMPRESSION = PAGE
);

-- Covering index for common queries
CREATE NONCLUSTERED INDEX IX_transactions_covering
ON fct_customer_transactions (customer_id, transaction_date)
INCLUDE (transaction_amount, transaction_type, branch_id)
WITH (
    DATA_COMPRESSION = PAGE
);

-- Index on computed column
ALTER TABLE fct_customer_transactions
ADD transaction_year_month AS (YEAR(transaction_date) * 100 + MONTH(transaction_date)) PERSISTED;

CREATE NONCLUSTERED INDEX IX_transactions_year_month
ON fct_customer_transactions (transaction_year_month)
WITH (DATA_COMPRESSION = PAGE);
```

### 2. Query Optimization Techniques
**Tejuu's Optimization Patterns:**

```sql
-- Optimized query with proper joins
SELECT 
    c.customer_id,
    c.customer_name,
    c.customer_segment,
    COUNT(t.transaction_id) AS transaction_count,
    SUM(t.transaction_amount) AS total_amount,
    AVG(t.transaction_amount) AS avg_amount
FROM dim_customer c
INNER JOIN fct_customer_transactions t ON c.customer_key = t.customer_key
WHERE c.is_current = 1
  AND t.transaction_date >= DATEADD(month, -12, GETDATE())
  AND t.transaction_amount > 0
GROUP BY c.customer_id, c.customer_name, c.customer_segment
HAVING COUNT(t.transaction_id) >= 5  -- Customers with at least 5 transactions
ORDER BY total_amount DESC;

-- Use EXISTS instead of IN for better performance
SELECT c.customer_id, c.customer_name
FROM dim_customer c
WHERE EXISTS (
    SELECT 1 
    FROM fct_customer_transactions t 
    WHERE t.customer_key = c.customer_key 
      AND t.transaction_date >= DATEADD(month, -1, GETDATE())
      AND t.transaction_amount > 10000
);

-- Optimized subquery with window functions
SELECT 
    customer_id,
    transaction_date,
    transaction_amount,
    LAG(transaction_amount) OVER (
        PARTITION BY customer_id 
        ORDER BY transaction_date
    ) AS previous_amount,
    transaction_amount - LAG(transaction_amount) OVER (
        PARTITION BY customer_id 
        ORDER BY transaction_date
    ) AS amount_change
FROM fct_customer_transactions
WHERE transaction_date >= DATEADD(month, -3, GETDATE());
```

### 3. Partitioning Strategies
**Tejuu's Partitioning Patterns:**

```sql
-- Partition function for date-based partitioning
CREATE PARTITION FUNCTION pf_transaction_date (DATE)
AS RANGE RIGHT FOR VALUES (
    '2024-01-01', '2024-02-01', '2024-03-01', '2024-04-01',
    '2024-05-01', '2024-06-01', '2024-07-01', '2024-08-01',
    '2024-09-01', '2024-10-01', '2024-11-01', '2024-12-01'
);

-- Partition scheme
CREATE PARTITION SCHEME ps_transaction_date
AS PARTITION pf_transaction_date
TO (fg_2024_01, fg_2024_02, fg_2024_03, fg_2024_04,
    fg_2024_05, fg_2024_06, fg_2024_07, fg_2024_08,
    fg_2024_09, fg_2024_10, fg_2024_11, fg_2024_12);

-- Partitioned table
CREATE TABLE fct_customer_transactions_partitioned (
    transaction_key INT IDENTITY(1,1),
    customer_key INT,
    transaction_date DATE,
    transaction_amount DECIMAL(18,2),
    transaction_type VARCHAR(50)
) ON ps_transaction_date(transaction_date);

-- Query with partition elimination
SELECT 
    customer_key,
    COUNT(*) AS transaction_count,
    SUM(transaction_amount) AS total_amount
FROM fct_customer_transactions_partitioned
WHERE transaction_date >= '2024-06-01'  -- Uses partition elimination
  AND transaction_date < '2024-07-01'
GROUP BY customer_key;
```

## Advanced Data Processing

### 1. Pivot and Unpivot Operations
**Tejuu's Pivot Patterns:**

```sql
-- Pivot transaction data by month
SELECT 
    customer_id,
    [2024-01] AS Jan_2024,
    [2024-02] AS Feb_2024,
    [2024-03] AS Mar_2024,
    [2024-04] AS Apr_2024,
    [2024-05] AS May_2024,
    [2024-06] AS Jun_2024
FROM (
    SELECT 
        customer_id,
        transaction_amount,
        FORMAT(transaction_date, 'yyyy-MM') AS transaction_month
    FROM fct_customer_transactions
    WHERE transaction_date >= '2024-01-01'
      AND transaction_date < '2024-07-01'
) AS SourceTable
PIVOT (
    SUM(transaction_amount)
    FOR transaction_month IN ([2024-01], [2024-02], [2024-03], [2024-04], [2024-05], [2024-06])
) AS PivotTable;

-- Unpivot monthly data
WITH MonthlyData AS (
    SELECT 
        customer_id,
        [2024-01] AS Jan_2024,
        [2024-02] AS Feb_2024,
        [2024-03] AS Mar_2024
    FROM customer_monthly_summary
)
SELECT 
    customer_id,
    month_name,
    transaction_amount
FROM MonthlyData
UNPIVOT (
    transaction_amount FOR month_name IN (Jan_2024, Feb_2024, Mar_2024)
) AS UnpivotTable;
```

### 2. Advanced Aggregations
**Tejuu's Aggregation Patterns:**

```sql
-- Complex aggregations with multiple grouping sets
SELECT 
    COALESCE(customer_segment, 'All Segments') AS customer_segment,
    COALESCE(transaction_type, 'All Types') AS transaction_type,
    COUNT(*) AS transaction_count,
    SUM(transaction_amount) AS total_amount,
    AVG(transaction_amount) AS avg_amount,
    MIN(transaction_amount) AS min_amount,
    MAX(transaction_amount) AS max_amount,
    STDEV(transaction_amount) AS std_amount
FROM fct_customer_transactions t
INNER JOIN dim_customer c ON t.customer_key = c.customer_key
WHERE t.transaction_date >= DATEADD(month, -12, GETDATE())
GROUP BY 
    GROUPING SETS (
        (c.customer_segment, t.transaction_type),
        (c.customer_segment),
        (t.transaction_type),
        ()
    )
ORDER BY customer_segment, transaction_type;

-- Rolling aggregations
SELECT 
    customer_id,
    transaction_date,
    transaction_amount,
    SUM(transaction_amount) OVER (
        PARTITION BY customer_id 
        ORDER BY transaction_date 
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) AS rolling_7d_amount,
    AVG(transaction_amount) OVER (
        PARTITION BY customer_id 
        ORDER BY transaction_date 
        ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
    ) AS rolling_30d_avg,
    ROW_NUMBER() OVER (
        PARTITION BY customer_id 
        ORDER BY transaction_date DESC
    ) AS transaction_rank
FROM fct_customer_transactions
WHERE transaction_date >= DATEADD(month, -12, GETDATE());
```

### 3. Data Quality Checks
**Tejuu's Data Quality SQL Patterns:**

```sql
-- Comprehensive data quality check
WITH DataQualityChecks AS (
    SELECT 
        'Completeness' AS check_type,
        'customer_id' AS column_name,
        COUNT(*) - COUNT(customer_id) AS error_count,
        CAST(COUNT(customer_id) AS FLOAT) / COUNT(*) * 100 AS quality_score
    FROM fct_customer_transactions
    
    UNION ALL
    
    SELECT 
        'Completeness' AS check_type,
        'transaction_amount' AS column_name,
        COUNT(*) - COUNT(transaction_amount) AS error_count,
        CAST(COUNT(transaction_amount) AS FLOAT) / COUNT(*) * 100 AS quality_score
    FROM fct_customer_transactions
    
    UNION ALL
    
    SELECT 
        'Validity' AS check_type,
        'negative_amounts' AS column_name,
        COUNT(*) AS error_count,
        CAST(COUNT(*) - COUNT(CASE WHEN transaction_amount < 0 THEN 1 END) AS FLOAT) / COUNT(*) * 100 AS quality_score
    FROM fct_customer_transactions
    WHERE transaction_amount < 0
    
    UNION ALL
    
    SELECT 
        'Consistency' AS check_type,
        'duplicate_transactions' AS column_name,
        COUNT(*) - COUNT(DISTINCT transaction_id) AS error_count,
        CAST(COUNT(DISTINCT transaction_id) AS FLOAT) / COUNT(*) * 100 AS quality_score
    FROM fct_customer_transactions
)
SELECT 
    check_type,
    column_name,
    error_count,
    quality_score,
    CASE 
        WHEN quality_score >= 95 THEN 'PASS'
        WHEN quality_score >= 90 THEN 'WARNING'
        ELSE 'FAIL'
    END AS status
FROM DataQualityChecks
ORDER BY check_type, column_name;
```

## Stored Procedures and Functions

### 1. Advanced Stored Procedures
**Tejuu's Stored Procedure Patterns:**

```sql
-- Complex stored procedure for customer analytics
CREATE PROCEDURE usp_customer_analytics
    @customer_id VARCHAR(50) = NULL,
    @start_date DATE = NULL,
    @end_date DATE = NULL,
    @include_inactive BIT = 0
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Set default date range if not provided
    IF @start_date IS NULL
        SET @start_date = DATEADD(month, -12, GETDATE());
    
    IF @end_date IS NULL
        SET @end_date = GETDATE();
    
    -- Validate parameters
    IF @start_date > @end_date
    BEGIN
        RAISERROR('Start date cannot be greater than end date', 16, 1);
        RETURN;
    END
    
    -- Main analytics query
    WITH CustomerAnalytics AS (
        SELECT 
            c.customer_id,
            c.customer_name,
            c.customer_segment,
            c.total_balance,
            COUNT(t.transaction_id) AS transaction_count,
            SUM(t.transaction_amount) AS total_amount,
            AVG(t.transaction_amount) AS avg_amount,
            MIN(t.transaction_date) AS first_transaction_date,
            MAX(t.transaction_date) AS last_transaction_date,
            DATEDIFF(day, MAX(t.transaction_date), GETDATE()) AS days_since_last_transaction,
            -- Risk metrics
            CASE 
                WHEN SUM(t.transaction_amount) > 500000 THEN 'High'
                WHEN SUM(t.transaction_amount) > 100000 THEN 'Medium'
                ELSE 'Low'
            END AS risk_level,
            -- Activity status
            CASE 
                WHEN DATEDIFF(day, MAX(t.transaction_date), GETDATE()) > 90 THEN 'Inactive'
                WHEN DATEDIFF(day, MAX(t.transaction_date), GETDATE()) > 30 THEN 'At Risk'
                ELSE 'Active'
            END AS activity_status
        FROM dim_customer c
        LEFT JOIN fct_customer_transactions t ON c.customer_key = t.customer_key
            AND t.transaction_date >= @start_date
            AND t.transaction_date <= @end_date
        WHERE c.is_current = 1
          AND (@customer_id IS NULL OR c.customer_id = @customer_id)
          AND (@include_inactive = 1 OR c.is_active = 1)
        GROUP BY c.customer_id, c.customer_name, c.customer_segment, c.total_balance
    )
    SELECT 
        customer_id,
        customer_name,
        customer_segment,
        total_balance,
        transaction_count,
        total_amount,
        avg_amount,
        first_transaction_date,
        last_transaction_date,
        days_since_last_transaction,
        risk_level,
        activity_status
    FROM CustomerAnalytics
    ORDER BY total_amount DESC;
    
    -- Return summary statistics
    SELECT 
        COUNT(*) AS total_customers,
        SUM(transaction_count) AS total_transactions,
        SUM(total_amount) AS total_volume,
        AVG(avg_amount) AS overall_avg_amount
    FROM CustomerAnalytics;
END;
```

### 2. User-Defined Functions
**Tejuu's Function Patterns:**

```sql
-- Scalar function for customer categorization
CREATE FUNCTION dbo.fn_categorize_customer(@balance DECIMAL(18,2))
RETURNS VARCHAR(20)
AS
BEGIN
    DECLARE @category VARCHAR(20);
    
    IF @balance >= 100000
        SET @category = 'Premium';
    ELSE IF @balance >= 50000
        SET @category = 'Gold';
    ELSE IF @balance >= 10000
        SET @category = 'Silver';
    ELSE
        SET @category = 'Bronze';
    
    RETURN @category;
END;

-- Table-valued function for customer transactions
CREATE FUNCTION dbo.fn_get_customer_transactions(
    @customer_id VARCHAR(50),
    @start_date DATE,
    @end_date DATE
)
RETURNS TABLE
AS
RETURN
(
    SELECT 
        t.transaction_id,
        t.transaction_date,
        t.transaction_amount,
        t.transaction_type,
        c.customer_name,
        c.customer_segment
    FROM fct_customer_transactions t
    INNER JOIN dim_customer c ON t.customer_key = c.customer_key
    WHERE c.customer_id = @customer_id
      AND t.transaction_date >= @start_date
      AND t.transaction_date <= @end_date
);

-- Usage examples
SELECT 
    customer_id,
    total_balance,
    dbo.fn_categorize_customer(total_balance) AS customer_category
FROM dim_customer
WHERE is_current = 1;

SELECT * FROM dbo.fn_get_customer_transactions('CUST12345678', '2024-01-01', '2024-12-31');
```

## Azure Synapse Specific Patterns

### 1. External Tables
**Tejuu's External Table Patterns:**

```sql
-- Create external data source
CREATE EXTERNAL DATA SOURCE data_lake
WITH (
    LOCATION = 'abfss://silver@storageaccount.dfs.core.windows.net/'
);

-- Create external file format
CREATE EXTERNAL FILE FORMAT parquet_format
WITH (
    FORMAT_TYPE = PARQUET,
    DATA_COMPRESSION = 'org.apache.hadoop.io.compress.SnappyCodec'
);

-- Create external table
CREATE EXTERNAL TABLE ext_customer_transactions (
    transaction_id VARCHAR(50),
    customer_id VARCHAR(50),
    transaction_date DATE,
    transaction_amount DECIMAL(18,2),
    transaction_type VARCHAR(50)
)
WITH (
    LOCATION = '/processed/transactions/',
    DATA_SOURCE = data_lake,
    FILE_FORMAT = parquet_format
);

-- Query external table
SELECT 
    customer_id,
    COUNT(*) AS transaction_count,
    SUM(transaction_amount) AS total_amount
FROM ext_customer_transactions
WHERE transaction_date >= '2024-01-01'
GROUP BY customer_id
ORDER BY total_amount DESC;
```

### 2. Serverless SQL Pool Queries
**Tejuu's Serverless Patterns:**

```sql
-- Query data lake directly with serverless SQL pool
SELECT 
    customer_id,
    transaction_date,
    transaction_amount,
    transaction_type
FROM OPENROWSET(
    BULK 'https://storageaccount.dfs.core.windows.net/silver/transactions/*.parquet',
    FORMAT = 'PARQUET'
) AS transactions
WHERE transaction_date >= '2024-01-01'
  AND transaction_amount > 1000;

-- Create view for Power BI
CREATE VIEW vw_customer_analytics AS
SELECT 
    customer_id,
    YEAR(transaction_date) AS year,
    MONTH(transaction_date) AS month,
    COUNT(*) AS transaction_count,
    SUM(transaction_amount) AS total_amount,
    AVG(transaction_amount) AS avg_amount
FROM OPENROWSET(
    BULK 'https://storageaccount.dfs.core.windows.net/silver/transactions/*.parquet',
    FORMAT = 'PARQUET'
) AS transactions
WHERE transaction_date >= DATEADD(year, -2, GETDATE())
GROUP BY customer_id, YEAR(transaction_date), MONTH(transaction_date);
```

My advanced SQL skills help build high-performance, scalable data solutions that power enterprise analytics and reporting!
