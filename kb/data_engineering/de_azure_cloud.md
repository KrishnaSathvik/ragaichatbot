---
tags: [data-engineer, azure, azure-data-factory, databricks, synapse, adls, cloud, adf]
persona: de
---

# Azure Cloud for Data Engineering - Krishna's Experience

## Introduction
**Krishna's Azure Journey:**
At Walgreens, our entire data platform runs on Azure. I work daily with Azure Data Factory, Databricks, ADLS Gen2, and Synapse. Let me share everything I've learned building production pipelines in Azure.

## Azure Data Factory (ADF)

### Pipeline Architecture
**Krishna's ADF Design Patterns:**

**1. Metadata-Driven Pipelines:**
```json
{
  "name": "pl_metadata_driven_ingestion",
  "description": "Generic pipeline that reads config from control table",
  "activities": [
    {
      "name": "Get Pipeline Metadata",
      "type": "Lookup",
      "inputs": [],
      "outputs": [],
      "typeProperties": {
        "source": {
          "type": "AzureSqlSource",
          "sqlReaderQuery": "SELECT * FROM control.pipeline_config WHERE is_active = 1"
        },
        "firstRowOnly": false
      }
    },
    {
      "name": "For Each Source System",
      "type": "ForEach",
      "dependsOn": [{"activity": "Get Pipeline Metadata", "dependencyConditions": ["Succeeded"]}],
      "typeProperties": {
        "items": {
          "value": "@activity('Get Pipeline Metadata').output.value",
          "type": "Expression"
        },
        "isSequential": false,
        "batchCount": 4,
        "activities": [
          {
            "name": "Copy Data",
            "type": "Copy",
            "inputs": [{
              "referenceName": "ds_generic_source",
              "type": "DatasetReference",
              "parameters": {
                "tableName": "@item().source_table",
                "schemaName": "@item().source_schema"
              }
            }],
            "outputs": [{
              "referenceName": "ds_adls_bronze",
              "type": "DatasetReference",
              "parameters": {
                "filePath": "@concat(item().destination_path, '/', formatDateTime(utcnow(), 'yyyy-MM-dd'))"
              }
            }],
            "typeProperties": {
              "source": {"type": "SqlServerSource"},
              "sink": {
                "type": "ParquetSink",
                "storeSettings": {"type": "AzureBlobFSWriteSettings"}
              }
            }
          }
        ]
      }
    }
  ]
}
```

**Business Impact:**
One metadata-driven pipeline replaced 50+ individual copy pipelines. Changes now take 2 minutes (update config table) vs 2 hours (modify 50 pipelines).

**2. Incremental Load Pattern:**
```json
{
  "name": "pl_incremental_load_with_watermark",
  "activities": [
    {
      "name": "Get Last Watermark",
      "type": "Lookup",
      "typeProperties": {
        "source": {
          "type": "AzureSqlSource",
          "sqlReaderQuery": "SELECT MAX(updated_at) as last_watermark FROM control.watermark WHERE table_name = 'orders'"
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
            "value": "SELECT * FROM orders WHERE updated_at > '@{activity('Get Last Watermark').output.firstRow.last_watermark}' AND updated_at <= GETDATE()",
            "type": "Expression"
          }
        },
        "sink": {
          "type": "ParquetSink"
        }
      }
    },
    {
      "name": "Update Watermark",
      "type": "SqlServerStoredProcedure",
      "dependsOn": [{"activity": "Copy Incremental Data", "dependencyConditions": ["Succeeded"]}],
      "typeProperties": {
        "storedProcedureName": "control.usp_update_watermark",
        "storedProcedureParameters": {
          "table_name": {"value": "orders", "type": "String"},
          "watermark_value": {
            "value": "@activity('Copy Incremental Data').output.executionDetails[0].source.rowsRead",
            "type": "DateTime"
          }
        }
      }
    }
  ]
}
```

**Real Use Case - Pharmacy Orders:**
Full load: 8 hours, 5TB data transfer
Incremental: 15 minutes, 50GB data transfer
Saved: $200/day in data transfer costs

**3. Error Handling & Retry Logic:**
```json
{
  "name": "pl_robust_pipeline",
  "activities": [
    {
      "name": "Execute Databricks Notebook",
      "type": "DatabricksNotebook",
      "policy": {
        "timeout": "0.12:00:00",
        "retry": 3,
        "retryIntervalInSeconds": 300,
        "secureOutput": false,
        "secureInput": false
      },
      "typeProperties": {
        "notebookPath": "/Pipelines/Silver/transform_orders",
        "baseParameters": {
          "execution_date": "@pipeline().parameters.execution_date"
        }
      }
    },
    {
      "name": "Send Success Email",
      "type": "WebActivity",
      "dependsOn": [{"activity": "Execute Databricks Notebook", "dependencyConditions": ["Succeeded"]}],
      "typeProperties": {
        "url": "https://prod-27.eastus.logic.azure.com/workflows/abc123/triggers/manual/paths/invoke",
        "method": "POST",
        "body": {
          "pipeline": "@pipeline().Pipeline",
          "runId": "@pipeline().RunId",
          "status": "Success"
        }
      }
    },
    {
      "name": "Send Failure Alert",
      "type": "WebActivity",
      "dependsOn": [{"activity": "Execute Databricks Notebook", "dependencyConditions": ["Failed"]}],
      "typeProperties": {
        "url": "https://hooks.slack.com/services/YOUR/WEBHOOK/URL",
        "method": "POST",
        "body": {
          "text": "🚨 Pipeline Failed: @{pipeline().Pipeline} - Run ID: @{pipeline().RunId}"
        }
      }
    }
  ]
}
```

### ADF Optimization Strategies
**Krishna's Performance Tips:**

**1. Parallel Execution:**
```json
{
  "name": "For Each with Parallelism",
  "type": "ForEach",
  "typeProperties": {
    "isSequential": false,
    "batchCount": 10,  // Process 10 items in parallel
    "activities": [...]
  }
}
```

**2. Data Integration Units (DIU) Optimization:**
```json
{
  "name": "Copy with Optimal DIU",
  "type": "Copy",
  "typeProperties": {
    "dataIntegrationUnits": 32,  // Auto-scale up to 32 DIUs
    "parallelCopies": 8,          // 8 parallel copy operations
    "enableStaging": true,
    "stagingSettings": {
      "linkedServiceName": {"referenceName": "ls_adls_staging"}
    }
  }
}
```

**3. Partitioned Copy:**
```json
{
  "name": "Partitioned Copy for Large Tables",
  "type": "Copy",
  "typeProperties": {
    "source": {
      "type": "SqlServerSource",
      "partitionOption": "DynamicRange",
      "partitionSettings": {
        "partitionColumnName": "order_id",
        "partitionUpperBound": "10000000",
        "partitionLowerBound": "1"
      }
    }
  }
}
```

## Azure Databricks

### Integration with ADF
**Krishna's Databricks-ADF Workflow:**

**1. Triggered Databricks Jobs:**
```json
{
  "name": "Execute dbt in Databricks",
  "type": "DatabricksNotebook",
  "linkedServiceName": {"referenceName": "ls_databricks"},
  "typeProperties": {
    "notebookPath": "/Shared/dbt/run_dbt_models",
    "baseParameters": {
      "execution_date": "@formatDateTime(pipeline().parameters.date, 'yyyy-MM-dd')",
      "dbt_models": "tag:daily",
      "target": "prod"
    },
    "libraries": [
      {"pypi": {"package": "dbt-databricks==1.6.0"}}
    ]
  },
  "linkedServiceName": {
    "referenceName": "ls_databricks_job_cluster",
    "type": "LinkedServiceReference"
  }
}
```

**2. Databricks Notebook for ADF:**
```python
# Databricks Notebook: transform_orders.py
# This notebook is called from ADF

# Get parameters from ADF
dbutils.widgets.text("execution_date", "")
dbutils.widgets.text("environment", "prod")

execution_date = dbutils.widgets.get("execution_date")
environment = dbutils.widgets.get("environment")

print(f"Processing data for {execution_date} in {environment}")

# Read from Bronze (raw data)
df_orders = spark.read.format("delta") \
    .load(f"/mnt/bronze/orders/date={execution_date}")

# Transform
df_clean = (
    df_orders
    .filter(F.col("order_status").isin(["completed", "shipped"]))
    .withColumn("order_amount", F.col("order_amount").cast("decimal(18,2)"))
    .dropDuplicates(["order_id"])
)

# Write to Silver
df_clean.write.format("delta") \
    .mode("overwrite") \
    .partitionBy("order_date") \
    .save(f"/mnt/silver/orders")

# Data quality check
row_count = df_clean.count()
if row_count == 0:
    dbutils.notebook.exit("FAILED: No data processed")

print(f"✅ Processed {row_count:,} orders")
dbutils.notebook.exit(f"SUCCESS: {row_count}")
```

### Cluster Configuration
**Krishna's Production Cluster Setup:**

**Job Cluster (Cost-Effective):**
```python
{
  "cluster_name": "adf-triggered-etl",
  "spark_version": "13.3.x-scala2.12",
  "node_type_id": "Standard_DS3_v2",
  "autoscale": {
    "min_workers": 2,
    "max_workers": 8
  },
  "auto_termination_minutes": 0,  // Terminate after job
  "spark_conf": {
    "spark.databricks.delta.preview.enabled": "true",
    "spark.sql.adaptive.enabled": "true"
  },
  "azure_attributes": {
    "availability": "SPOT_WITH_FALLBACK_AZURE",
    "spot_bid_max_price": 0.5
  }
}
```

**All-Purpose Cluster (Development):**
```python
{
  "cluster_name": "dev-data-engineering",
  "spark_version": "13.3.x-scala2.12",
  "node_type_id": "Standard_DS3_v2",
  "num_workers": 2,
  "autotermination_minutes": 30,
  "spark_conf": {
    "spark.databricks.delta.preview.enabled": "true"
  }
}
```

**Cost Savings:**
- Using Spot VMs: 60-80% cheaper than on-demand
- Job clusters vs always-on: Saved $30K/month
- Right-sizing: Reduced over-provisioning by 40%

## Azure Data Lake Storage (ADLS) Gen2

### Storage Organization
**Krishna's Data Lake Structure:**
```
adls://walgreensdata@storageaccount.dfs.core.windows.net/

├── raw/                                    # Landing zone
│   ├── salesforce/
│   │   └── 2024-01-15/opportunities.parquet
│   ├── sql_server/
│   │   └── orders/2024-01-15/orders.parquet
│   └── api_data/
│       └── customer_events/2024-01-15/events.json
│
├── bronze/                                 # Raw ingested (Delta format)
│   ├── orders/
│   │   └── date=2024-01-15/
│   ├── customers/
│   │   └── date=2024-01-15/
│   └── products/
│
├── silver/                                 # Cleaned & validated
│   ├── orders/
│   │   └── order_date=2024-01-15/
│   ├── dim_customer/
│   └── dim_product/
│
├── gold/                                   # Business aggregations
│   ├── daily_sales_summary/
│   ├── customer_ltv/
│   └── product_performance/
│
└── archive/                                # Old data
    └── raw/2023/
```

### Access Control & Security
**Krishna's Security Implementation:**

**1. Service Principal Authentication:**
```python
# Mount ADLS using Service Principal
configs = {
  "fs.azure.account.auth.type": "OAuth",
  "fs.azure.account.oauth.provider.type": "org.apache.hadoop.fs.azurebfs.oauth2.ClientCredsTokenProvider",
  "fs.azure.account.oauth2.client.id": dbutils.secrets.get("keyvault", "sp-client-id"),
  "fs.azure.account.oauth2.client.secret": dbutils.secrets.get("keyvault", "sp-client-secret"),
  "fs.azure.account.oauth2.client.endpoint": "https://login.microsoftonline.com/tenant-id/oauth2/token"
}

dbutils.fs.mount(
  source = "abfss://bronze@walgreensdata.dfs.core.windows.net/",
  mount_point = "/mnt/bronze",
  extra_configs = configs
)
```

**2. Azure Key Vault Integration:**
```python
# Store secrets in Key Vault, reference in Databricks
db_password = dbutils.secrets.get(scope="keyvault", key="sql-db-password")
api_key = dbutils.secrets.get(scope="keyvault", key="external-api-key")

# Use in connections
jdbc_url = f"jdbc:sqlserver://server.database.windows.net;database=WalgreensDB;user=admin;password={db_password}"
```

**3. RBAC (Role-Based Access Control):**
```bash
# Azure CLI commands for RBAC
# Grant Data Engineer team read/write to silver layer
az role assignment create \
  --assignee "data-engineers@walgreens.com" \
  --role "Storage Blob Data Contributor" \
  --scope "/subscriptions/{sub-id}/resourceGroups/rg-data/providers/Microsoft.Storage/storageAccounts/walgreensdata/blobServices/default/containers/silver"

# Grant Analytics team read-only to gold layer
az role assignment create \
  --assignee "analytics-team@walgreens.com" \
  --role "Storage Blob Data Reader" \
  --scope "/subscriptions/{sub-id}/resourceGroups/rg-data/providers/Microsoft.Storage/storageAccounts/walgreensdata/blobServices/default/containers/gold"
```

## Azure Synapse Analytics

### SQL Pool for Analytics
**Krishna's Synapse Implementation:**

**1. External Tables on Data Lake:**
```sql
-- Create external data source
CREATE EXTERNAL DATA SOURCE adls_gold
WITH (
    TYPE = HADOOP,
    LOCATION = 'abfss://gold@walgreensdata.dfs.core.windows.net/'
);

-- Create external file format
CREATE EXTERNAL FILE FORMAT parquet_format
WITH (
    FORMAT_TYPE = PARQUET,
    DATA_COMPRESSION = 'org.apache.hadoop.io.compress.SnappyCodec'
);

-- Create external table
CREATE EXTERNAL TABLE ext_daily_sales (
    order_date DATE,
    customer_segment VARCHAR(50),
    product_category VARCHAR(100),
    total_sales DECIMAL(18,2),
    order_count INT
)
WITH (
    LOCATION = '/daily_sales_summary/',
    DATA_SOURCE = adls_gold,
    FILE_FORMAT = parquet_format
);

-- Query it like a normal table
SELECT 
    customer_segment,
    SUM(total_sales) as total_revenue,
    SUM(order_count) as total_orders
FROM ext_daily_sales
WHERE order_date >= '2024-01-01'
GROUP BY customer_segment;
```

**2. Serverless SQL Pool:**
```sql
-- Query Delta tables directly (no import needed!)
SELECT 
    order_id,
    customer_id,
    order_date,
    order_amount
FROM OPENROWSET(
    BULK 'https://walgreensdata.dfs.core.windows.net/silver/orders/',
    FORMAT = 'DELTA'
) AS orders
WHERE order_date >= '2024-01-01';
```

## Azure DevOps CI/CD

### Data Pipeline CI/CD
**Krishna's Deployment Pipeline:**

```yaml
# azure-pipelines.yml
trigger:
  branches:
    include:
      - main
      - develop
  paths:
    include:
      - pipelines/
      - databricks/

pool:
  vmImage: 'ubuntu-latest'

stages:
  - stage: Build
    jobs:
      - job: Validate
        steps:
          - task: UsePythonVersion@0
            inputs:
              versionSpec: '3.10'
          
          - script: |
              pip install databricks-cli pyspark pytest
              pytest tests/
            displayName: 'Run Unit Tests'
          
          - script: |
              # Validate ADF pipelines
              az datafactory pipeline validate \
                --factory-name adf-walgreens \
                --resource-group rg-data \
                --name pl_daily_etl
            displayName: 'Validate ADF Pipelines'

  - stage: Deploy_Dev
    condition: and(succeeded(), eq(variables['Build.SourceBranch'], 'refs/heads/develop'))
    jobs:
      - job: Deploy
        steps:
          - script: |
              # Deploy Databricks notebooks
              databricks workspace import_dir \
                ./databricks/notebooks \
                /Shared/Pipelines \
                --overwrite
            displayName: 'Deploy to Dev Databricks'
          
          - task: AzureResourceManagerTemplateDeployment@3
            inputs:
              deploymentScope: 'Resource Group'
              azureResourceManagerConnection: 'Azure-DevOps-SP'
              subscriptionId: 'subscription-id'
              action: 'Create Or Update Resource Group'
              resourceGroupName: 'rg-data-dev'
              location: 'East US'
              templateLocation: 'Linked artifact'
              csmFile: 'arm-templates/adf-pipelines.json'
            displayName: 'Deploy ADF Pipelines to Dev'

  - stage: Deploy_Prod
    condition: and(succeeded(), eq(variables['Build.SourceBranch'], 'refs/heads/main'))
    jobs:
      - deployment: DeployProd
        environment: 'production'
        strategy:
          runOnce:
            deploy:
              steps:
                - script: |
                    databricks workspace import_dir \
                      ./databricks/notebooks \
                      /Production/Pipelines \
                      --overwrite
                  displayName: 'Deploy to Prod Databricks'
```

## Cost Optimization

### Krishna's Azure Cost Strategies:

**1. Reserved Capacity:**
- Committed to 1-year reserved Databricks: Saved 37%
- Reserved Azure SQL: Saved 40%

**2. Spot VMs for Databricks:**
```python
# Use spot instances for non-critical jobs
"azure_attributes": {
    "availability": "SPOT_WITH_FALLBACK_AZURE",
    "spot_bid_max_price": 0.5  // Max 50% of on-demand price
}
```

**3. Storage Lifecycle Policies:**
```json
{
  "rules": [
    {
      "name": "move-old-raw-to-cool",
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

**4. Auto-Pause & Auto-Terminate:**
- Auto-terminate dev clusters after 30 min idle
- Auto-pause Synapse SQL pools overnight
- Saved: $25K/month

**Total Cost Optimization:**
- Monthly Azure spend: $180K → $115K (36% reduction)
- No performance impact
- CFO was very happy!

My Azure expertise helps Walgreens run cost-effective, scalable, reliable data platforms in the cloud!

