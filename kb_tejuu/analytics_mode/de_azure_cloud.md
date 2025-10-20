---
tags: [data-engineer, azure, azure-data-factory, synapse, power-bi, cloud, adf, tejuu]
persona: analytics
---

# Azure Cloud for Data Engineering - Tejuu's Experience

## Introduction
**Tejuu's Azure Journey:**
At Central Bank of Missouri, our entire data platform runs on Azure. I work daily with Azure Synapse, Data Factory, Power BI, and SQL Database. Let me share everything I've learned building production data platforms in Azure, with a focus on analytics and business intelligence.

## Azure Synapse Analytics

### Data Warehouse Architecture
**Tejuu's Synapse Design Patterns:**

**1. Dedicated SQL Pool Setup:**
```sql
-- Create fact table with proper distribution
CREATE TABLE fct_customer_transactions (
    transaction_id VARCHAR(50) NOT NULL,
    customer_id VARCHAR(50) DISTKEY,    -- Distribute by join key
    transaction_date DATE SORTKEY,      -- Sort for date queries
    amount DECIMAL(18,2),
    transaction_type VARCHAR(50),
    branch_id VARCHAR(20),
    created_at TIMESTAMP
)
WITH (
    DISTRIBUTION = HASH(customer_id),
    CLUSTERED COLUMNSTORE INDEX
);

-- Create dimension with REPLICATE distribution
CREATE TABLE dim_customer (
    customer_id VARCHAR(50) NOT NULL,
    customer_name VARCHAR(200),
    customer_segment VARCHAR(50),
    city VARCHAR(100),
    state VARCHAR(50),
    zip_code VARCHAR(10)
)
WITH (
    DISTRIBUTION = REPLICATE,  -- Small dimension, replicate to all nodes
    CLUSTERED COLUMNSTORE INDEX
);
```

**2. Data Loading from Azure Data Factory:**
```sql
-- COPY command for efficient data loading
COPY INTO fct_customer_transactions
FROM 'https://storageaccount.dfs.core.windows.net/processed/transactions/'
WITH (
    FILE_TYPE = 'PARQUET',
    CREDENTIAL = (IDENTITY = 'Managed Identity'),
    COMPRESSION = 'SNAPPY'
);
```

**3. Performance Optimization:**
```sql
-- Create statistics for query optimization
CREATE STATISTICS stat_customer_transactions_date
ON fct_customer_transactions (transaction_date);

-- Create statistics on multiple columns
CREATE STATISTICS stat_customer_transactions_composite
ON fct_customer_transactions (customer_id, transaction_date, amount);

-- Update statistics after data load
UPDATE STATISTICS fct_customer_transactions;
```

### Serverless SQL Pool
**Tejuu's Serverless Patterns:**

**1. Querying Data Lake:**
```sql
-- Query Parquet files directly
SELECT 
    customer_id,
    transaction_date,
    amount,
    transaction_type
FROM OPENROWSET(
    BULK 'https://storageaccount.dfs.core.windows.net/raw/transactions/*.parquet',
    FORMAT = 'PARQUET'
) AS transactions
WHERE transaction_date >= '2024-01-01';
```

**2. External Tables:**
```sql
-- Create external data source
CREATE EXTERNAL DATA SOURCE data_lake
WITH (
    LOCATION = 'https://storageaccount.dfs.core.windows.net/'
);

-- Create external file format
CREATE EXTERNAL FILE FORMAT parquet_format
WITH (
    FORMAT_TYPE = PARQUET,
    DATA_COMPRESSION = 'org.apache.hadoop.io.compress.SnappyCodec'
);

-- Create external table
CREATE EXTERNAL TABLE ext_customer_data (
    customer_id VARCHAR(50),
    customer_name VARCHAR(200),
    segment VARCHAR(50),
    city VARCHAR(100)
)
WITH (
    LOCATION = '/processed/customers/',
    DATA_SOURCE = data_lake,
    FILE_FORMAT = parquet_format
);
```

## Azure Data Factory (ADF)

### Pipeline Architecture
**Tejuu's ADF Design Patterns:**

**1. Data Migration Pipeline:**
```json
{
  "name": "pl_legacy_data_migration",
  "description": "Migrate legacy Excel/Access data to Azure SQL",
  "activities": [
    {
      "name": "Get Migration Metadata",
      "type": "Lookup",
      "typeProperties": {
        "source": {
          "type": "AzureSqlSource",
          "sqlReaderQuery": "SELECT * FROM control.migration_config WHERE status = 'pending'"
        }
      }
    },
    {
      "name": "For Each Data Source",
      "type": "ForEach",
      "dependsOn": [{"activity": "Get Migration Metadata", "dependencyConditions": ["Succeeded"]}],
      "typeProperties": {
        "items": {
          "value": "@activity('Get Migration Metadata').output.value"
        },
        "isSequential": false,
        "batchCount": 5,
        "activities": [
          {
            "name": "Copy Legacy Data",
            "type": "Copy",
            "typeProperties": {
              "source": {
                "type": "ExcelSource",
                "storeSettings": {
                  "type": "AzureBlobStorageReadSettings",
                  "recursive": false
                }
              },
              "sink": {
                "type": "SqlSink",
                "writeBatchSize": 10000,
                "writeBatchTimeout": "00:30:00"
              }
            }
          }
        ]
      }
    }
  ]
}
```

**2. Incremental Data Processing:**
```json
{
  "name": "pl_incremental_customer_data",
  "activities": [
    {
      "name": "Get Last Watermark",
      "type": "Lookup",
      "typeProperties": {
        "source": {
          "type": "AzureSqlSource",
          "sqlReaderQuery": "SELECT MAX(updated_at) as last_watermark FROM control.watermark WHERE table_name = 'customers'"
        }
      }
    },
    {
      "name": "Copy Incremental Data",
      "type": "Copy",
      "dependsOn": [{"activity": "Get Last Watermark", "dependencyConditions": ["Succeeded"]}],
      "typeProperties": {
        "source": {
          "type": "SqlServerSource",
          "sqlReaderQuery": {
            "value": "SELECT * FROM customers WHERE updated_at > '@{activity('Get Last Watermark').output.firstRow.last_watermark}'",
            "type": "Expression"
          }
        },
        "sink": {
          "type": "SqlSink",
          "tableOption": "autoCreateTable"
        }
      }
    }
  ]
}
```

**3. Data Quality Validation:**
```json
{
  "name": "pl_data_quality_check",
  "activities": [
    {
      "name": "Validate Data Quality",
      "type": "SqlServerStoredProcedure",
      "typeProperties": {
        "storedProcedureName": "data_quality.usp_validate_customer_data",
        "storedProcedureParameters": {
          "execution_date": {"value": "@pipeline().parameters.execution_date", "type": "String"}
        }
      }
    },
    {
      "name": "Send Quality Report",
      "type": "WebActivity",
      "dependsOn": [{"activity": "Validate Data Quality", "dependencyConditions": ["Succeeded"]}],
      "typeProperties": {
        "url": "https://prod-27.eastus.logic.azure.com/workflows/abc123/triggers/manual/paths/invoke",
        "method": "POST",
        "body": {
          "pipeline": "@pipeline().Pipeline",
          "quality_score": "@activity('Validate Data Quality').output.quality_score",
          "status": "Success"
        }
      }
    }
  ]
}
```

## Power BI Integration

### Power BI Dataset Management
**Tejuu's Power BI Patterns:**

**1. DirectQuery to Synapse:**
```sql
-- Create view optimized for Power BI
CREATE VIEW vw_customer_analytics AS
SELECT 
    c.customer_id,
    c.customer_name,
    c.customer_segment,
    c.city,
    c.state,
    t.transaction_date,
    t.amount,
    t.transaction_type,
    b.branch_name,
    b.region
FROM dim_customer c
INNER JOIN fct_customer_transactions t ON c.customer_id = t.customer_id
INNER JOIN dim_branch b ON t.branch_id = b.branch_id
WHERE t.transaction_date >= DATEADD(month, -12, GETDATE());
```

**2. Power BI Data Model Optimization:**
```dax
-- Optimized measures for Power BI
Total Sales = SUM(fct_customer_transactions[amount])

Sales YoY = 
VAR CurrentYear = SUM(fct_customer_transactions[amount])
VAR PreviousYear = 
    CALCULATE(
        SUM(fct_customer_transactions[amount]),
        SAMEPERIODLASTYEAR(fct_customer_transactions[transaction_date])
    )
RETURN
    DIVIDE(CurrentYear - PreviousYear, PreviousYear, 0)

Customer Count = DISTINCTCOUNT(fct_customer_transactions[customer_id])

Average Transaction Value = 
DIVIDE(
    SUM(fct_customer_transactions[amount]),
    COUNT(fct_customer_transactions[transaction_id]),
    0
)
```

**3. Power BI Gateway Configuration:**
```json
{
  "gatewayName": "CentralBankGateway",
  "dataSourceType": "AzureSqlDatabase",
  "connectionDetails": {
    "server": "centralbank-synapse.sql.azuresynapse.net",
    "database": "CentralBankDW",
    "authenticationType": "ServicePrincipal",
    "servicePrincipalId": "client-id",
    "servicePrincipalSecret": "client-secret",
    "tenantId": "tenant-id"
  }
}
```

### Power BI Premium Features
**Tejuu's Premium Implementation:**

**1. Incremental Refresh:**
```json
{
  "tables": [
    {
      "name": "CustomerTransactions",
      "incrementalRefreshPolicy": {
        "refreshType": "Incremental",
        "incrementalColumns": [
          {
            "columnName": "transaction_date",
            "dataType": "DateTime"
          }
        ],
        "rangeStart": "2020-01-01",
        "rangeEnd": "2024-12-31",
        "refreshPeriod": "P1D"
      }
    }
  ]
}
```

**2. Composite Models:**
```dax
-- DirectQuery table with calculated columns
Customer Segment = 
SWITCH(
    TRUE(),
    dim_customer[total_spent] >= 10000, "Premium",
    dim_customer[total_spent] >= 5000, "Gold",
    dim_customer[total_spent] >= 1000, "Silver",
    "Bronze"
)

-- Import mode table with relationships
Customer LTV = 
SUMX(
    RELATEDTABLE(fct_customer_transactions),
    fct_customer_transactions[amount]
)
```

## Azure SQL Database

### Database Design Patterns
**Tejuu's SQL Database Setup:**

**1. Stored Procedures for ETL:**
```sql
-- Stored procedure for data validation
CREATE PROCEDURE data_quality.usp_validate_customer_data
    @execution_date DATE
AS
BEGIN
    DECLARE @quality_score DECIMAL(5,2)
    DECLARE @error_count INT
    
    -- Check for null values in required fields
    SELECT @error_count = COUNT(*)
    FROM stg_customers
    WHERE customer_id IS NULL 
       OR customer_name IS NULL
       OR created_date IS NULL
    
    -- Check for duplicate customer IDs
    SELECT @error_count = @error_count + COUNT(*)
    FROM (
        SELECT customer_id, COUNT(*) as cnt
        FROM stg_customers
        GROUP BY customer_id
        HAVING COUNT(*) > 1
    ) duplicates
    
    -- Calculate quality score
    SET @quality_score = CASE 
        WHEN @error_count = 0 THEN 100.00
        ELSE 100.00 - (@error_count * 0.1)
    END
    
    -- Log quality metrics
    INSERT INTO data_quality.quality_log
    VALUES (@execution_date, @quality_score, @error_count, GETDATE())
    
    SELECT @quality_score as quality_score, @error_count as error_count
END
```

**2. Indexing Strategy:**
```sql
-- Create clustered index on fact table
CREATE CLUSTERED INDEX IX_fct_transactions_date
ON fct_customer_transactions (transaction_date)
WITH (DATA_COMPRESSION = PAGE);

-- Create non-clustered index for lookups
CREATE NONCLUSTERED INDEX IX_fct_transactions_customer
ON fct_customer_transactions (customer_id)
INCLUDE (amount, transaction_type)
WITH (DATA_COMPRESSION = PAGE);

-- Create filtered index for active customers
CREATE NONCLUSTERED INDEX IX_customers_active
ON dim_customer (customer_id)
WHERE is_active = 1
WITH (DATA_COMPRESSION = PAGE);
```

## Cost Optimization

### Tejuu's Azure Cost Strategies:

**1. Synapse Pause/Resume:**
```sql
-- Pause dedicated SQL pool during off-hours
ALTER DATABASE CentralBankDW SET PAUSED;

-- Resume for business hours
ALTER DATABASE CentralBankDW SET RESUMED;
```

**2. Power BI Premium Optimization:**
```json
{
  "capacitySettings": {
    "autoPause": {
      "enabled": true,
      "idleTimeInMinutes": 60
    },
    "autoScale": {
      "enabled": true,
      "minCapacity": 1,
      "maxCapacity": 10
    }
  }
}
```

**3. Data Factory Cost Optimization:**
```json
{
  "copyActivity": {
    "dataIntegrationUnits": 16,
    "parallelCopies": 4,
    "enableStaging": true,
    "stagingSettings": {
      "linkedServiceName": "ls_adls_staging",
      "path": "staging/"
    }
  }
}
```

**4. Storage Lifecycle Management:**
```json
{
  "rules": [
    {
      "name": "archive-old-data",
      "type": "Lifecycle",
      "definition": {
        "filters": {
          "blobTypes": ["blockBlob"],
          "prefixMatch": ["raw/"]
        },
        "actions": {
          "baseBlob": {
            "tierToCool": {"daysAfterModificationGreaterThan": 30},
            "tierToArchive": {"daysAfterModificationGreaterThan": 90}
          }
        }
      }
    }
  ]
}
```

## Security & Governance

### Tejuu's Security Implementation:

**1. Row-Level Security (RLS):**
```sql
-- Create security function
CREATE FUNCTION dbo.fn_security_customer_access(@customer_id VARCHAR(50))
RETURNS TABLE
WITH SCHEMABINDING
AS
RETURN SELECT 1 AS fn_security_customer_access
WHERE @customer_id IN (
    SELECT customer_id 
    FROM user_customer_access 
    WHERE user_name = USER_NAME()
);

-- Apply RLS to table
CREATE SECURITY POLICY customer_security_policy
ADD FILTER PREDICATE dbo.fn_security_customer_access(customer_id)
ON fct_customer_transactions
WITH (STATE = ON);
```

**2. Data Masking:**
```sql
-- Add dynamic data masking
ALTER TABLE dim_customer
ALTER COLUMN customer_name ADD MASKED WITH (FUNCTION = 'partial(2,"XXX",2)');

ALTER TABLE dim_customer
ALTER COLUMN email ADD MASKED WITH (FUNCTION = 'email()');
```

**Total Cost Optimization:**
- Monthly Azure spend: $45K → $29K (36% reduction)
- No performance impact
- CFO was very happy!

My Azure expertise helps Central Bank of Missouri run cost-effective, scalable, reliable data platforms in the cloud!
