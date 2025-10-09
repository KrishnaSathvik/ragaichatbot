---
tags: [analytics-engineer, azure, azure-data-factory, synapse, databricks, azure-sql]
persona: ae
---

# Azure Cloud for Analytics Engineers - Tejuu's Experience

## Introduction
**Tejuu's Azure Journey:**
I've been working with Azure data services for 2+ years, primarily focusing on analytics workloads. My role involves orchestrating data pipelines, building transformations in Synapse and Databricks, and ensuring our analytics stack runs smoothly in the cloud.

## Azure Data Factory (ADF)

**Tejuu's ADF Use Cases:**
I use ADF to orchestrate my dbt transformations, copy data from various sources, and trigger downstream processes.

**Example: Daily dbt Orchestration Pipeline**
```json
{
  "name": "pl_daily_analytics_refresh",
  "description": "Orchestrate daily analytics refresh with dbt",
  "activities": [
    {
      "name": "Check Data Freshness",
      "type": "Lookup",
      "inputs": [{
        "referenceName": "ds_synapse_control_table",
        "type": "DatasetReference"
      }],
      "outputs": [],
      "typeProperties": {
        "source": {
          "type": "SqlDWSource",
          "sqlReaderQuery": "SELECT MAX(updated_at) as last_update FROM raw.orders"
        }
      }
    },
    {
      "name": "Run dbt Models",
      "type": "DatabricksNotebook",
      "dependsOn": [{"activity": "Check Data Freshness"}],
      "typeProperties": {
        "notebookPath": "/Shared/dbt/run_dbt_production",
        "baseParameters": {
          "dbt_command": "dbt run --select tag:daily",
          "target": "prod"
        }
      }
    },
    {
      "name": "Run dbt Tests",
      "type": "DatabricksNotebook",
      "dependsOn": [{"activity": "Run dbt Models"}],
      "typeProperties": {
        "notebookPath": "/Shared/dbt/run_dbt_tests",
        "baseParameters": {
          "dbt_command": "dbt test --select tag:daily"
        }
      }
    },
    {
      "name": "Send Success Notification",
      "type": "WebActivity",
      "dependsOn": [{"activity": "Run dbt Tests"}],
      "typeProperties": {
        "url": "https://hooks.slack.com/services/YOUR/WEBHOOK/URL",
        "method": "POST",
        "body": {
          "text": "✅ Daily analytics refresh completed successfully"
        }
      }
    }
  ],
  "parameters": {
    "execution_date": {
      "type": "String",
      "defaultValue": "@formatDateTime(utcnow(), 'yyyy-MM-dd')"
    }
  }
}
```

**Business Impact:**
- Marketing gets fresh campaign metrics by 7 AM daily
- Finance dashboards auto-refresh overnight
- 99.5% pipeline success rate with automated alerting

**Copy Activity for Incremental Loads:**
```json
{
  "name": "copy_salesforce_data",
  "type": "Copy",
  "inputs": [{
    "referenceName": "ds_salesforce_opportunities",
    "type": "DatasetReference"
  }],
  "outputs": [{
    "referenceName": "ds_adls_raw_salesforce",
    "type": "DatasetReference"
  }],
  "typeProperties": {
    "source": {
      "type": "SalesforceSource",
      "query": "SELECT Id, AccountId, Amount, CloseDate, StageName, LastModifiedDate FROM Opportunity WHERE LastModifiedDate > @{formatDateTime(addDays(utcnow(), -1), 'yyyy-MM-ddTHH:mm:ssZ')}"
    },
    "sink": {
      "type": "ParquetSink",
      "storeSettings": {
        "type": "AzureBlobFSWriteSettings",
        "copyBehavior": "PreserveHierarchy"
      },
      "formatSettings": {
        "type": "ParquetWriteSettings",
        "fileExtension": ".parquet"
      }
    }
  }
}
```

## Azure Synapse Analytics

**Tejuu's Synapse Setup:**
We use Synapse as our enterprise data warehouse. I create and maintain the serving layer where business users query data.

**Creating Analytics Tables:**
```sql
-- Create fact table with distribution and indexing

CREATE TABLE analytics.fct_sales
(
    sale_id VARCHAR(50) NOT NULL,
    date_key INT NOT NULL,
    customer_key BIGINT NOT NULL,
    product_key BIGINT NOT NULL,
    store_key BIGINT NOT NULL,
    
    sales_amount DECIMAL(18,2),
    quantity INT,
    discount_amount DECIMAL(18,2),
    net_amount DECIMAL(18,2),
    cost_amount DECIMAL(18,2),
    profit_amount DECIMAL(18,2),
    
    created_at DATETIME2,
    updated_at DATETIME2
)
WITH
(
    DISTRIBUTION = HASH(customer_key),  -- Distribute by commonly joined column
    CLUSTERED COLUMNSTORE INDEX,        -- Best for analytics
    PARTITION (date_key RANGE RIGHT FOR VALUES (20230101, 20230201, 20230301))
);

-- Create dimension table

CREATE TABLE analytics.dim_customer
(
    customer_key BIGINT NOT NULL,
    customer_id VARCHAR(50) NOT NULL,
    customer_name VARCHAR(200),
    customer_segment VARCHAR(50),
    customer_tier VARCHAR(20),
    region VARCHAR(100),
    city VARCHAR(100),
    state VARCHAR(50),
    
    -- SCD Type 2 fields
    effective_date DATE,
    end_date DATE,
    is_current BIT,
    
    created_at DATETIME2,
    updated_at DATETIME2
)
WITH
(
    DISTRIBUTION = REPLICATE,  -- Small dimension tables - replicate to all nodes
    CLUSTERED COLUMNSTORE INDEX
);
```

**Performance Optimization:**
```sql
-- Update statistics for query optimization
CREATE STATISTICS stat_fct_sales_customer_key ON analytics.fct_sales(customer_key);
CREATE STATISTICS stat_fct_sales_date_key ON analytics.fct_sales(date_key);
CREATE STATISTICS stat_fct_sales_amount ON analytics.fct_sales(sales_amount);

-- Create materialized view for common aggregations
CREATE MATERIALIZED VIEW analytics.mv_daily_sales_summary
WITH (DISTRIBUTION = HASH(date_key))
AS
SELECT
    date_key,
    customer_segment,
    product_category,
    region,
    COUNT(DISTINCT sale_id) AS order_count,
    SUM(sales_amount) AS total_sales,
    SUM(quantity) AS total_quantity,
    SUM(profit_amount) AS total_profit
FROM analytics.fct_sales f
JOIN analytics.dim_customer c ON f.customer_key = c.customer_key AND c.is_current = 1
JOIN analytics.dim_product p ON f.product_key = p.product_key
JOIN analytics.dim_store s ON f.store_key = s.store_key
GROUP BY
    date_key,
    customer_segment,
    product_category,
    region;
```

**Business Value:**
Dashboard queries that took 30 seconds now return in 2 seconds. Product managers love the speed improvement!

**Incremental Load Pattern:**
```sql
-- Merge pattern for incremental updates

MERGE INTO analytics.fct_sales AS target
USING staging.stg_sales_incremental AS source
ON target.sale_id = source.sale_id

WHEN MATCHED AND source.updated_at > target.updated_at THEN
    UPDATE SET
        sales_amount = source.sales_amount,
        quantity = source.quantity,
        discount_amount = source.discount_amount,
        net_amount = source.net_amount,
        updated_at = source.updated_at

WHEN NOT MATCHED THEN
    INSERT (
        sale_id, date_key, customer_key, product_key, store_key,
        sales_amount, quantity, discount_amount, net_amount,
        created_at, updated_at
    )
    VALUES (
        source.sale_id, source.date_key, source.customer_key, source.product_key, source.store_key,
        source.sales_amount, source.quantity, source.discount_amount, source.net_amount,
        source.created_at, source.updated_at
    );
```

## Azure Databricks

**Tejuu's Databricks Workflows:**
I run dbt transformations in Databricks for heavy-duty data processing.

**dbt Integration with Databricks:**
```python
# Databricks Notebook: run_dbt_production.py

import os
import subprocess
from datetime import datetime

# Setup
dbt_project_path = "/Workspace/Shared/dbt_project"
os.chdir(dbt_project_path)

# Get parameters
dbt_command = dbutils.widgets.get("dbt_command")  # e.g., "dbt run --select tag:daily"
target = dbutils.widgets.get("target")  # e.g., "prod"

print(f"Running dbt command: {dbt_command}")
print(f"Target environment: {target}")

# Run dbt
try:
    result = subprocess.run(
        dbt_command.split(),
        capture_output=True,
        text=True,
        check=True
    )
    
    print("✅ dbt command succeeded")
    print(result.stdout)
    
    # Log success to control table
    spark.sql(f"""
        INSERT INTO control.dbt_run_log
        VALUES (
            '{datetime.now()}',
            '{dbt_command}',
            'SUCCESS',
            '{result.stdout[:1000]}'  -- Truncate long output
        )
    """)
    
except subprocess.CalledProcessError as e:
    print("❌ dbt command failed")
    print(e.stderr)
    
    # Log failure
    spark.sql(f"""
        INSERT INTO control.dbt_run_log
        VALUES (
            '{datetime.now()}',
            '{dbt_command}',
            'FAILED',
            '{e.stderr[:1000]}'
        )
    """)
    
    # Send alert
    dbutils.notebook.exit("FAILED")
    raise
```

**Delta Lake for Analytics:**
```python
# Create Delta table optimized for analytics

from delta.tables import DeltaTable
from pyspark.sql import functions as F

# Read source data
df_sales = spark.read.format("delta").load("/mnt/raw/sales")

# Transform and aggregate
df_daily_summary = (
    df_sales
    .filter(F.col("order_status") == "completed")
    .groupBy(
        F.to_date("order_date").alias("date"),
        "customer_segment",
        "product_category"
    )
    .agg(
        F.count("order_id").alias("order_count"),
        F.sum("order_amount").alias("total_sales"),
        F.avg("order_amount").alias("avg_order_value"),
        F.countDistinct("customer_id").alias("unique_customers")
    )
)

# Write to Delta with partitioning
(
    df_daily_summary.write
    .format("delta")
    .mode("overwrite")
    .partitionBy("date")
    .option("overwriteSchema", "true")
    .save("/mnt/analytics/fct_daily_sales_summary")
)

# Optimize Delta table
spark.sql("""
    OPTIMIZE delta.`/mnt/analytics/fct_daily_sales_summary`
    ZORDER BY (customer_segment, product_category)
""")
```

**Business Scenario:**
We process 100M+ rows of clickstream data daily. Using Databricks with Delta Lake, processing completes in 15 minutes vs 2 hours with traditional methods.

## Azure Data Lake Storage (ADLS)

**Tejuu's ADLS Organization:**
```
adls://analyticsdata@company.dfs.core.windows.net/

├── raw/                          # Landing zone
│   ├── salesforce/
│   │   └── 2024/01/15/opportunities.parquet
│   ├── erp/
│   │   └── 2024/01/15/orders.parquet
│   └── web_analytics/
│       └── 2024/01/15/clickstream.json
│
├── staging/                      # Cleaned data
│   ├── stg_opportunities/
│   ├── stg_orders/
│   └── stg_clickstream/
│
├── analytics/                    # Business logic applied
│   ├── fct_sales/
│   ├── fct_campaigns/
│   ├── dim_customer/
│   └── dim_product/
│
└── reporting/                    # Aggregated for BI
    ├── daily_revenue_summary/
    ├── customer_ltv/
    └── product_performance/
```

**Lifecycle Management:**
```python
# Python script to manage ADLS lifecycle

from azure.storage.filedatalake import DataLakeServiceClient

# Move old raw files to archive
def archive_old_files(days_old=90):
    """Move files older than 90 days to archive tier"""
    
    service_client = DataLakeServiceClient.from_connection_string(conn_str)
    file_system_client = service_client.get_file_system_client("analyticsdata")
    
    paths = file_system_client.get_paths(path="raw")
    
    for path in paths:
        if is_older_than(path.last_modified, days_old):
            # Move to cool tier or archive
            properties = {'tier': 'Archive'}
            path.set_access_control_recursive(properties)
            print(f"Archived: {path.name}")
```

## Azure Key Vault Integration

**Tejuu's Secret Management:**
```python
# dbt profile with Azure Key Vault

# profiles.yml
my_project:
  target: prod
  outputs:
    prod:
      type: databricks
      host: "{{ env_var('DBX_HOST') }}"
      http_path: "{{ env_var('DBX_HTTP_PATH') }}"
      token: "{{ env_var('DBX_TOKEN') }}"  # Retrieved from Key Vault
      schema: analytics
      threads: 4

# ADF pipeline retrieves secrets
{
  "activities": [
    {
      "name": "Get DB Password",
      "type": "WebActivity",
      "typeProperties": {
        "url": "https://my-keyvault.vault.azure.net/secrets/db-password?api-version=7.0",
        "method": "GET",
        "authentication": {
          "type": "MSI",
          "resource": "https://vault.azure.net"
        }
      }
    }
  ]
}
```

## Cost Optimization

**Tejuu's Cost Management:**
```sql
-- Query to find expensive tables in Synapse

SELECT
    t.name AS table_name,
    SUM(p.rows) AS row_count,
    SUM(a.used_pages) * 8 / 1024 / 1024 AS size_gb,
    t.distribution_policy_desc,
    COUNT(DISTINCT p.partition_number) AS partition_count
FROM sys.tables t
JOIN sys.indexes i ON t.object_id = i.object_id
JOIN sys.partitions p ON i.object_id = p.object_id AND i.index_id = p.index_id
JOIN sys.allocation_units a ON p.partition_id = a.container_id
WHERE t.schema_id = SCHEMA_ID('analytics')
GROUP BY t.name, t.distribution_policy_desc
ORDER BY size_gb DESC;
```

**Databricks Cluster Optimization:**
```json
{
  "cluster_name": "dbt-analytics-cluster",
  "spark_version": "13.3.x-scala2.12",
  "node_type_id": "Standard_DS3_v2",
  "autoscale": {
    "min_workers": 2,
    "max_workers": 8
  },
  "autotermination_minutes": 30,
  "spark_conf": {
    "spark.databricks.delta.preview.enabled": "true",
    "spark.sql.adaptive.enabled": "true",
    "spark.databricks.cluster.profile": "singleNode"
  }
}
```

**Business Impact:**
Reduced Azure costs by 30% by:
- Auto-terminating idle Databricks clusters
- Using materialized views in Synapse
- Implementing data lifecycle policies
- Scheduling pipelines during off-peak hours

## Monitoring and Alerting

**Tejuu's Monitoring Setup:**
```python
# Log Analytics query for pipeline monitoring

# KQL query in Azure Monitor
AzureDiagnostics
| where ResourceProvider == "MICROSOFT.DATAFACTORY"
| where Category == "PipelineRuns"
| where Status == "Failed"
| where TimeGenerated > ago(24h)
| extend PipelineName = tostring(split(resource_name, '/')[2])
| project
    TimeGenerated,
    PipelineName,
    Status,
    ErrorMessage = ActivityError
| summarize FailureCount = count() by PipelineName
| where FailureCount > 0
```

**Alerting Logic:**
```yaml
# Alert rule for failed dbt runs

alert_rule:
  name: "dbt_daily_run_failed"
  description: "Alert when daily dbt run fails"
  severity: "High"
  condition:
    query: |
      AzureDiagnostics
      | where ActivityName contains "Run dbt Models"
      | where Status == "Failed"
      | where TimeGenerated > ago(30m)
  action:
    action_group: "analytics-team-alerts"
    email: ["tejuu@company.com", "data-team@company.com"]
    slack_webhook: "https://hooks.slack.com/services/YOUR/WEBHOOK"
```

My focus in Azure is making analytics reliable, performant, and cost-effective while empowering business users!

