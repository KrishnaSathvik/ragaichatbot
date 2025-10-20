---
tags: [data-engineer, data-warehouse, dimensional-modeling, star-schema, tejuu]
persona: analytics
---

# Data Warehousing - Tejuu's Experience

## Introduction
**Tejuu's Data Warehousing Philosophy:**
At Central Bank of Missouri, I've designed and implemented enterprise data warehouses that serve 1K+ users across different business functions. My approach focuses on dimensional modeling, performance optimization, and self-service analytics. Let me share the patterns and best practices I've learned building production data warehouses.

## Dimensional Modeling

### Star Schema Design
**Tejuu's Star Schema Patterns:**

**1. Fact Table Design:**
```sql
-- Central fact table for customer transactions
CREATE TABLE fct_customer_transactions (
    -- Surrogate keys
    transaction_key INT IDENTITY(1,1) PRIMARY KEY,
    customer_key INT NOT NULL,
    product_key INT NOT NULL,
    branch_key INT NOT NULL,
    date_key INT NOT NULL,
    
    -- Measures
    transaction_amount DECIMAL(18,2) NOT NULL,
    transaction_fee DECIMAL(18,2),
    net_amount DECIMAL(18,2),
    transaction_count INT DEFAULT 1,
    
    -- Degenerate dimensions
    transaction_id VARCHAR(50) NOT NULL,
    reference_number VARCHAR(100),
    
    -- Audit fields
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
WITH (
    DISTRIBUTION = HASH(customer_key),
    CLUSTERED COLUMNSTORE INDEX
);
```

**2. Dimension Tables:**
```sql
-- Customer dimension with SCD Type 2
CREATE TABLE dim_customer (
    customer_key INT IDENTITY(1,1) PRIMARY KEY,
    customer_id VARCHAR(50) NOT NULL,
    customer_name VARCHAR(200) NOT NULL,
    customer_type VARCHAR(50),
    customer_segment VARCHAR(50),
    city VARCHAR(100),
    state VARCHAR(50),
    zip_code VARCHAR(10),
    phone VARCHAR(20),
    email VARCHAR(100),
    
    -- SCD Type 2 fields
    effective_date DATE NOT NULL,
    expiry_date DATE,
    is_current BIT DEFAULT 1,
    
    -- Audit fields
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
WITH (
    DISTRIBUTION = REPLICATE,
    CLUSTERED COLUMNSTORE INDEX
);

-- Product dimension
CREATE TABLE dim_product (
    product_key INT IDENTITY(1,1) PRIMARY KEY,
    product_id VARCHAR(50) NOT NULL,
    product_name VARCHAR(200) NOT NULL,
    product_category VARCHAR(100),
    product_subcategory VARCHAR(100),
    product_type VARCHAR(50),
    interest_rate DECIMAL(5,4),
    minimum_balance DECIMAL(18,2),
    
    -- Audit fields
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
WITH (
    DISTRIBUTION = REPLICATE,
    CLUSTERED COLUMNSTORE INDEX
);

-- Date dimension
CREATE TABLE dim_date (
    date_key INT PRIMARY KEY,
    full_date DATE NOT NULL,
    year INT NOT NULL,
    quarter INT NOT NULL,
    month INT NOT NULL,
    month_name VARCHAR(20) NOT NULL,
    day_of_year INT NOT NULL,
    day_of_week INT NOT NULL,
    day_name VARCHAR(20) NOT NULL,
    is_weekend BIT NOT NULL,
    is_holiday BIT NOT NULL,
    fiscal_year INT,
    fiscal_quarter INT
)
WITH (
    DISTRIBUTION = REPLICATE,
    CLUSTERED COLUMNSTORE INDEX
);
```

### Slowly Changing Dimensions (SCD)
**Tejuu's SCD Implementation:**

**1. SCD Type 1 (Overwrite):**
```sql
-- SCD Type 1 for non-critical changes
CREATE PROCEDURE usp_update_customer_scd1
    @customer_id VARCHAR(50),
    @customer_name VARCHAR(200),
    @city VARCHAR(100),
    @state VARCHAR(50)
AS
BEGIN
    UPDATE dim_customer
    SET 
        customer_name = @customer_name,
        city = @city,
        state = @state,
        updated_at = CURRENT_TIMESTAMP
    WHERE customer_id = @customer_id
      AND is_current = 1;
END
```

**2. SCD Type 2 (Historical):**
```sql
-- SCD Type 2 for critical changes
CREATE PROCEDURE usp_update_customer_scd2
    @customer_id VARCHAR(50),
    @customer_name VARCHAR(200),
    @customer_segment VARCHAR(50),
    @effective_date DATE
AS
BEGIN
    -- Expire current record
    UPDATE dim_customer
    SET 
        expiry_date = DATEADD(day, -1, @effective_date),
        is_current = 0,
        updated_at = CURRENT_TIMESTAMP
    WHERE customer_id = @customer_id
      AND is_current = 1;
    
    -- Insert new record
    INSERT INTO dim_customer (
        customer_id, customer_name, customer_segment,
        effective_date, expiry_date, is_current
    )
    VALUES (
        @customer_id, @customer_name, @customer_segment,
        @effective_date, NULL, 1
    );
END
```

## Data Warehouse Architecture

### 1. Staging Layer
**Tejuu's Staging Patterns:**

```sql
-- Staging table for raw data
CREATE TABLE stg_customer_transactions (
    transaction_id VARCHAR(50),
    customer_id VARCHAR(50),
    product_id VARCHAR(50),
    branch_id VARCHAR(20),
    transaction_date VARCHAR(20),
    amount VARCHAR(20),
    transaction_type VARCHAR(50),
    raw_data JSON,
    file_name VARCHAR(200),
    loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
WITH (
    DISTRIBUTION = ROUND_ROBIN,
    HEAP
);

-- Staging table for data quality checks
CREATE TABLE stg_data_quality_log (
    table_name VARCHAR(100),
    column_name VARCHAR(100),
    check_type VARCHAR(50),
    check_result VARCHAR(20),
    error_count INT,
    error_details VARCHAR(MAX),
    check_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
WITH (
    DISTRIBUTION = ROUND_ROBIN,
    HEAP
);
```

### 2. Data Marts
**Tejuu's Data Mart Design:**

```sql
-- Customer analytics data mart
CREATE TABLE dm_customer_analytics (
    customer_key INT,
    customer_id VARCHAR(50),
    customer_name VARCHAR(200),
    customer_segment VARCHAR(50),
    total_transactions INT,
    total_amount DECIMAL(18,2),
    avg_transaction_amount DECIMAL(18,2),
    last_transaction_date DATE,
    days_since_last_transaction INT,
    customer_lifetime_value DECIMAL(18,2),
    risk_score DECIMAL(5,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
WITH (
    DISTRIBUTION = HASH(customer_key),
    CLUSTERED COLUMNSTORE INDEX
);

-- Product performance data mart
CREATE TABLE dm_product_performance (
    product_key INT,
    product_id VARCHAR(50),
    product_name VARCHAR(200),
    product_category VARCHAR(100),
    total_transactions INT,
    total_volume DECIMAL(18,2),
    avg_transaction_amount DECIMAL(18,2),
    unique_customers INT,
    market_share DECIMAL(5,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
WITH (
    DISTRIBUTION = HASH(product_key),
    CLUSTERED COLUMNSTORE INDEX
);
```

## ETL/ELT Processes

### 1. Extract Process
**Tejuu's Extract Patterns:**

```python
# Extract from multiple sources
class DataExtractor:
    def __init__(self):
        self.connections = {
            'sql_server': self.get_sql_server_connection(),
            'oracle': self.get_oracle_connection(),
            'api': self.get_api_connection()
        }
    
    def extract_customer_data(self, source_system):
        if source_system == 'sql_server':
            return self.extract_from_sql_server()
        elif source_system == 'oracle':
            return self.extract_from_oracle()
        elif source_system == 'api':
            return self.extract_from_api()
    
    def extract_from_sql_server(self):
        query = """
        SELECT 
            customer_id,
            customer_name,
            customer_type,
            city,
            state,
            zip_code,
            created_date,
            updated_date
        FROM customers
        WHERE updated_date >= ?
        """
        return self.connections['sql_server'].execute(query, [self.get_last_extract_date()])
```

### 2. Transform Process
**Tejuu's Transform Patterns:**

```python
# Data transformation pipeline
class DataTransformer:
    def __init__(self):
        self.data_quality_rules = DataQualityRules()
        self.business_rules = BusinessRules()
    
    def transform_customer_data(self, df):
        # Data cleansing
        df_clean = (
            df
            .filter(col("customer_id").isNotNull())
            .filter(col("customer_name").isNotNull())
            .withColumn("customer_name", trim(upper(col("customer_name"))))
            .withColumn("zip_code", regexp_replace(col("zip_code"), "[^0-9]", ""))
        )
        
        # Data quality validation
        quality_issues = self.data_quality_rules.validate(df_clean)
        if quality_issues:
            self.log_quality_issues(quality_issues)
        
        # Business rule application
        df_business = self.business_rules.apply_customer_rules(df_clean)
        
        # SCD Type 2 processing
        df_scd = self.apply_scd_type2(df_business)
        
        return df_scd
    
    def apply_scd_type2(self, df):
        # Check for changes and create new records
        existing_customers = self.get_existing_customers()
        
        # Identify changes
        changes = df.join(existing_customers, "customer_id", "left") \
                   .filter(self.has_changes())
        
        # Create new records for changes
        new_records = changes.withColumn("effective_date", current_date()) \
                           .withColumn("is_current", lit(1))
        
        return new_records
```

### 3. Load Process
**Tejuu's Load Patterns:**

```python
# Data loading with error handling
class DataLoader:
    def __init__(self):
        self.target_connection = self.get_target_connection()
    
    def load_to_warehouse(self, df, table_name, load_type="upsert"):
        try:
            if load_type == "upsert":
                self.upsert_data(df, table_name)
            elif load_type == "append":
                self.append_data(df, table_name)
            elif load_type == "replace":
                self.replace_data(df, table_name)
            
            self.log_load_success(table_name, df.count())
            
        except Exception as e:
            self.log_load_error(table_name, str(e))
            raise
    
    def upsert_data(self, df, table_name):
        # Create staging table
        staging_table = f"{table_name}_staging"
        df.write.mode("overwrite").saveAsTable(staging_table)
        
        # Perform upsert using MERGE
        merge_sql = f"""
        MERGE {table_name} AS target
        USING {staging_table} AS source
        ON target.customer_id = source.customer_id
        WHEN MATCHED THEN
            UPDATE SET 
                customer_name = source.customer_name,
                updated_at = CURRENT_TIMESTAMP
        WHEN NOT MATCHED THEN
            INSERT (customer_id, customer_name, created_at)
            VALUES (source.customer_id, source.customer_name, CURRENT_TIMESTAMP);
        """
        
        self.target_connection.execute(merge_sql)
```

## Performance Optimization

### 1. Indexing Strategy
**Tejuu's Indexing Patterns:**

```sql
-- Clustered indexes for fact tables
CREATE CLUSTERED INDEX IX_fct_transactions_date
ON fct_customer_transactions (date_key)
WITH (DATA_COMPRESSION = PAGE);

-- Non-clustered indexes for lookups
CREATE NONCLUSTERED INDEX IX_fct_transactions_customer
ON fct_customer_transactions (customer_key)
INCLUDE (transaction_amount, transaction_type)
WITH (DATA_COMPRESSION = PAGE);

-- Filtered indexes for active records
CREATE NONCLUSTERED INDEX IX_customers_current
ON dim_customer (customer_id)
WHERE is_current = 1
WITH (DATA_COMPRESSION = PAGE);
```

### 2. Partitioning Strategy
**Tejuu's Partitioning Patterns:**

```sql
-- Partition fact table by date
CREATE TABLE fct_customer_transactions_partitioned (
    transaction_key INT,
    customer_key INT,
    date_key INT,
    transaction_amount DECIMAL(18,2)
)
WITH (
    DISTRIBUTION = HASH(customer_key),
    CLUSTERED COLUMNSTORE INDEX
)
PARTITIONED BY (date_key);

-- Create partition function
CREATE PARTITION FUNCTION pf_date (INT)
AS RANGE LEFT FOR VALUES (
    20240101, 20240201, 20240301, 20240401,
    20240501, 20240601, 20240701, 20240801,
    20240901, 20241001, 20241101, 20241201
);

-- Create partition scheme
CREATE PARTITION SCHEME ps_date
AS PARTITION pf_date
TO (fg_2024_01, fg_2024_02, fg_2024_03, fg_2024_04,
    fg_2024_05, fg_2024_06, fg_2024_07, fg_2024_08,
    fg_2024_09, fg_2024_10, fg_2024_11, fg_2024_12);
```

### 3. Query Optimization
**Tejuu's Query Patterns:**

```sql
-- Optimized star schema query
SELECT 
    c.customer_segment,
    p.product_category,
    d.year,
    d.quarter,
    COUNT(*) as transaction_count,
    SUM(t.transaction_amount) as total_amount,
    AVG(t.transaction_amount) as avg_amount
FROM fct_customer_transactions t
INNER JOIN dim_customer c ON t.customer_key = c.customer_key
INNER JOIN dim_product p ON t.product_key = p.product_key
INNER JOIN dim_date d ON t.date_key = d.date_key
WHERE d.year = 2024
  AND c.is_current = 1
GROUP BY c.customer_segment, p.product_category, d.year, d.quarter
ORDER BY total_amount DESC;

-- Use of covering indexes
CREATE NONCLUSTERED INDEX IX_customer_analytics_covering
ON fct_customer_transactions (customer_key, date_key)
INCLUDE (transaction_amount, transaction_type, transaction_fee)
WITH (DATA_COMPRESSION = PAGE);
```

## Data Quality Management

### 1. Data Profiling
**Tejuu's Profiling Patterns:**

```python
# Automated data profiling
class DataProfiler:
    def __init__(self):
        self.profiling_rules = {
            'completeness': self.check_completeness,
            'uniqueness': self.check_uniqueness,
            'validity': self.check_validity,
            'consistency': self.check_consistency
        }
    
    def profile_table(self, table_name, df):
        profile_results = {}
        
        for rule_name, rule_function in self.profiling_rules.items():
            profile_results[rule_name] = rule_function(df)
        
        return profile_results
    
    def check_completeness(self, df):
        total_rows = df.count()
        completeness = {}
        
        for column in df.columns:
            non_null_count = df.filter(col(column).isNotNull()).count()
            completeness[column] = (non_null_count / total_rows) * 100
        
        return completeness
```

### 2. Data Lineage
**Tejuu's Lineage Tracking:**

```python
# Track data lineage through warehouse
class DataLineageTracker:
    def __init__(self):
        self.lineage_graph = {}
    
    def track_transformation(self, source, target, transformation):
        self.lineage_graph[target] = {
            'source': source,
            'transformation': transformation,
            'timestamp': datetime.now(),
            'record_count': self.get_record_count(target)
        }
    
    def get_lineage_path(self, table_name):
        path = []
        current = table_name
        
        while current in self.lineage_graph:
            path.append(current)
            current = self.lineage_graph[current]['source']
        
        return path
```

## Self-Service Analytics

### 1. Semantic Layer
**Tejuu's Semantic Patterns:**

```sql
-- Create business-friendly views
CREATE VIEW vw_customer_transactions AS
SELECT 
    t.transaction_id,
    c.customer_name,
    c.customer_segment,
    p.product_name,
    p.product_category,
    d.full_date as transaction_date,
    d.year,
    d.quarter,
    d.month_name,
    t.transaction_amount,
    t.transaction_fee,
    t.net_amount
FROM fct_customer_transactions t
INNER JOIN dim_customer c ON t.customer_key = c.customer_key
INNER JOIN dim_product p ON t.product_key = p.product_key
INNER JOIN dim_date d ON t.date_key = d.date_key
WHERE c.is_current = 1;

-- Create aggregated views for common queries
CREATE VIEW vw_monthly_customer_summary AS
SELECT 
    customer_id,
    customer_name,
    customer_segment,
    year,
    month_name,
    COUNT(*) as transaction_count,
    SUM(transaction_amount) as total_amount,
    AVG(transaction_amount) as avg_amount
FROM vw_customer_transactions
GROUP BY customer_id, customer_name, customer_segment, year, month_name;
```

### 2. Data Dictionary
**Tejuu's Dictionary Management:**

```python
# Automated data dictionary generation
class DataDictionaryGenerator:
    def __init__(self):
        self.dictionary = {}
    
    def generate_dictionary(self, table_name, df):
        dictionary_entry = {
            'table_name': table_name,
            'columns': {},
            'business_description': self.get_business_description(table_name),
            'data_owner': self.get_data_owner(table_name),
            'last_updated': datetime.now()
        }
        
        for column in df.columns:
            dictionary_entry['columns'][column] = {
                'data_type': str(df.schema[column].dataType),
                'nullable': df.schema[column].nullable,
                'business_meaning': self.get_column_meaning(table_name, column),
                'sample_values': df.select(column).distinct().limit(5).collect()
            }
        
        return dictionary_entry
```

My data warehousing experience helps build robust, scalable, and user-friendly data platforms that deliver real business value!
