# Data Engineering Interview Preparation Guide

## Table of Contents
- [Overview](#overview)
- [Technical Skills](#technical-skills)
- [Interview Scenarios](#interview-scenarios)
- [Key Talking Points](#key-talking-points)
- [Leadership & Communication](#leadership--communication)
- [Project Background](#project-background)

## Overview

This guide contains comprehensive interview preparation materials for Data Engineering positions, with a focus on **PySpark**, **Databricks**, **Azure Data Factory**, and **Microsoft Fabric**. The content is based on real-world experience from large-scale data migration and modernization projects.

## Technical Skills

### Core Technologies
- **PySpark** - Primary development language for data processing
- **Databricks** - Main platform for data engineering workflows
- **Azure Data Factory (ADF)** - Orchestration and pipeline management
- **Delta Lake** - Data lakehouse architecture
- **Azure Synapse** - Data warehousing and analytics
- **Snowflake** - Cloud data platform
- **Microsoft Fabric** - Next-generation data platform

### Key Technical Areas
- Data ingestion and ETL/ELT pipelines
- Schema enforcement and data validation
- Performance tuning and optimization
- Data modeling (Bronze, Silver, Gold architecture)
- CI/CD for data pipelines
- Data governance and security

## Interview Scenarios

### 1. Data Processing & Cleanup

**Q: How do you handle data quality issues in your pipelines?**

**A:** "In my Walgreens migration work, I focused on writing production-ready PySpark code, not just 'it runs'. So beyond the main logic, I always include:

- **Error handling**: try/except around each stage (read → transform → write) with clear messages and exit codes so ADF can retry or fail fast
- **Logging & metrics**: log4j logs at key steps, plus row counts in/out, bad-record counts, and total runtime—helps support & root-cause quickly
- **Comments & structure**: small, named functions with docstrings, inline comments for business rules, and a top README explaining inputs/outputs
- **Config & parameters**: no hardcoding—paths, dates, table names via config/ADF params so the same job runs for multiple sources
- **Data quality checks**: schema validation, null/duplicate checks, referential checks, with a quarantine path for rejects
- **Idempotency & retries**: Delta MERGE/upsert, checkpoint/temp paths, safe overwrite modes—so re-runs don't duplicate data
- **Security**: secrets from Key Vault/Databricks scopes, not in code
- **Review & CI/CD**: PR reviews in Git, basic notebook tests on sample data, and pipeline deploys via ARM templates

That's the standard I follow—so the code is readable, monitored, and safe to operate, not just a basic script."

### 2. Data Deduplication & Cleanup

**Q: How do you handle duplicates and data cleanup?**

**A:** "On Walgreens pipelines I handled cleanup in the PySpark notebook right after landing. First I standardize columns (trim, lower/upper, cast types, date parsing) and run schema + null checks. For duplicates, I either use `dropDuplicates(['business_key1','business_key2'])` when the key is clear, or a window to keep the latest record: `row_number() over the key ordered by last_modified` and keep `rn=1`. I also fix common issues (empty strings → null, `na.fill` for defaults, `na.drop` where mandatory), and send any failed rows to a quarantine path. After that I write clean data to Delta/Parquet partitioned by date, and use Delta MERGE for incremental upserts."

### 3. Large Dataset Processing

**Q: How do you handle large datasets from a processing perspective?**

**A:** "On the Walgreens project we processed 10+ TB/month, so we designed for scale. We landed raw data partitioned in ADLS (by date/source) and used Parquet/Delta so Spark gets column pruning & predicate pushdown. In the notebooks we ran incremental loads (filter by last_modified_date) to avoid full scans, and we partitioned by date/store to keep shuffles small. For joins, we broadcast small dimensions and tuned shuffle partitions; for stability we sized the Databricks cluster properly and let it autoscale.

We also fixed small-file issues by compacting/OPTIMIZE (Delta) and kept the pipeline idempotent with MERGE INTO. Only cached DataFrames we reused; avoided collect() on big data; and used ADF to parallelize safe steps with retries and monitoring. That combination kept large datasets fast and reliable."

### 4. Data Architecture (Bronze-Silver-Gold)

**Q: What's your data structure for ingestion?**

**A:** "In Walgreens we followed a simple Bronze → Silver → Gold structure in ADLS/Databricks.

**Bronze (raw/landing)**: data exactly as received from sources, partitioned by ingest_date/source (e.g., `/bronze/sourceA/ingest_dt=2025-09-26/…`). Formats were CSV/JSON from source; no transforms, just metadata columns like ingest_ts, file_name.

**Silver (clean/curated)**: after PySpark cleanup (schema validation, trims, null/dup handling, business rules). We standardized types and keys, and wrote Delta/Parquet, partitioned by business date or store/region depending on query patterns.

**Gold (serving/analytics)**: aggregated, joined, report-ready tables (KPIs). Mostly Delta for MERGE/upserts, with OPTIMIZE + ZORDER on common filters.

We also had a quarantine/rejects area for bad rows, consistent naming conventions (db.table per domain), and tracked schema/version columns. That structure made ingestion predictable and downstream consumption fast."

### 5. Schema Enforcement

**Q: How do you handle schema enforcement?**

**A:** "On Walgreens pipelines I enforce schema upfront. I never infer — I define an explicit StructType in PySpark and read with that schema. If a file doesn't match, the read runs in FAILFAST/PERMISSIVE and I route bad rows to a quarantine path with the error reason and file name. After read, I cast & standardize types (dates, decimals), check required columns, and run quick DQ checks (null/dup keys).

For Delta targets I rely on Delta schema enforcement and use constraints (NOT NULL/CHECK) so bad data can't land. If there's safe drift (e.g., a new optional column), I allow controlled evolution via mergeSchema (or autoMerge only in the curated job), otherwise the job fails fast and alerts via ADF. This keeps the tables consistent while still letting us onboard additive changes safely."

### 6. Data Modeling & KPIs

**Q: How would you build a sales KPI system from ingestion to consumption?**

**A:** "For a cross-system sales scenario, I'd run a clean Bronze-Silver-Gold flow and a dimensional model so KPIs are reliable and fast.

**Ingestion (Bronze)**: Orchestrate with ADF. Use Copy Activity/Linked Services to land each source (POS, e-comm, ERP) into ADLS Bronze exactly as-is, partitioned by ingest date and source. Capture metadata (ingest_ts, file_name).

**Cleansing & Conformance (Silver in Databricks/PySpark)**: In notebooks I enforce schema (explicit StructType), standardize types/time zones, trim/case, handle nulls/duplicates (`dropDuplicates(keys)` or window `row_number()`), and conform keys (e.g., product IDs, store IDs). Join to reference data, validate row counts, push rejects to a quarantine path. Store Delta/Parquet, partitioned (typically by business date).

**Data Modeling (Gold)**: Build a star schema:
- **FactSales** (grain: one line per transaction line), columns: DateKey, StoreKey, ProductKey, CustomerKey, Qty, NetAmount, Discount, Tax, Cost, Margin, etc.
- **Dimensions**: DimDate, DimStore, DimProduct, DimCustomer. Use SCD Type-2 where history matters (Product, Customer). Generate surrogate keys, maintain natural keys for lineage.

Loads are incremental using Delta MERGE INTO with a watermark (last_modified_date). Apply constraints (NOT NULL/CHECK) to keep quality high.

**Performance & Ops**: Use partitioning (e.g., by SalesDate), OPTIMIZE + Z-ORDER (e.g., on StoreKey/ProductKey), compact small files, tune shuffle partitions, broadcast small dimensions for joins, and cache only reused DFs. Schedule via ADF triggers with retries + alerts (Log Analytics). Secrets via Key Vault/DBX scopes. CI/CD with Git/ARM.

**Consumption (Power BI / Semantic Model)**: Expose Gold tables to Power BI (Import, DirectQuery, or Direct Lake). Create a clean semantic model with relationships (star), measures like:
- Total Sales = SUM(FactSales[NetAmount])
- Gross Margin = SUM(NetAmount) - SUM(Cost)
- GM% = DIVIDE([Gross Margin],[Total Sales])
- Time-intel (MTD/QTD/YTD) on DimDate.

Optionally add aggregate tables for common rollups (daily by store/product) to speed large reports.

**Governance & DQ**: Register assets in Purview for lineage, add DQ checks (schema, nulls, referential integrity) and SLA monitors (row count deltas). Keep run logs/metrics (rows in/out, reject counts) for auditability.

That's the exact pattern I used at Walgreens: ADF to orchestrate, PySpark in Databricks to cleanse/conform, Delta-based star schema in Gold, and BI over the curated layer with strong observability and incremental MERGEs so KPIs stay fresh and trustworthy."

### 7. Databricks Clusters & Cost Management

**Q: How do clusters work in Databricks?**

**A:** "In Databricks, a cluster is basically the compute engine where all PySpark jobs and notebooks run. It's made up of a driver node that coordinates work and multiple worker nodes that process data in parallel. You can set it as interactive for dev/testing or job clusters for scheduled ADF/production runs.

I usually enable autoscaling so executors scale up when load is high and shrink back when idle — which saves cost. On Walgreens pipelines, I tuned clusters by choosing the right VM size, adjusting shuffle partitions, and caching where needed. So the cluster handles distributing the data, executing transformations in parallel, and then bringing results back through the driver."

**Q: How do you manage Databricks costs efficiently?**

**A:** "Right—cost is a big deal. From a FinOps perspective, here's what I've done to keep Databricks/Spark efficient without surprises:

- **Right-size fixed job clusters** (no autoscaling) per workload and use ephemeral job clusters—spin up, run, shut down—to avoid idle DBUs. Cluster pools help cut startup time.
- **Process less data**: design incremental loads (watermark/Delta MERGE) instead of full refreshes; strong partition pruning and predicate pushdown with Parquet/Delta.
- **Faster = cheaper**: compact small files (Delta OPTIMIZE), Z-ORDER on common filters, broadcast small dims, tune spark.sql.shuffle.partitions to match cores, and cache only when reused.
- **Pick the right runtime/sku**: use Photon/modern runtimes where it speeds DF ops, choose VM families that match memory/CPU needs, and consider spot/low-priority where safe for non-critical jobs.
- **Orchestrate wisely in ADF**: parallelize only what the cluster can handle; sequence the rest to avoid over-provisioning; add retries with backoff instead of brute-force reruns.
- **Governance**: tag jobs with cost centers, monitor runtime/DBUs per pipeline, and adjust cluster sizes based on real usage.

That's exactly how I ran the Walgreens pipelines—keep clusters lean, move less data, and make each job finish faster so overall compute spend stays predictable and efficient."

### 8. JSON Processing

**Q: How do you handle JSON structures, especially deeply nested JSONs?**

**A:** "Yes, I've worked quite a bit with JSON, including deeply nested structures. In Walgreens some of our API feeds came in as nested JSON, so the first step was always to define a proper schema using StructType instead of relying on schema inference. Once loaded into a DataFrame, I used functions like `explode`, `from_json`, and `get_json_object` to flatten arrays and nested fields. For example, if a transaction contained multiple line items in an array, I would explode that array so each item became its own row. For deeper nesting, I'd sometimes apply multiple levels of explode and then select the individual attributes into a flattened structure. After flattening, I standardized types, applied business rules, and wrote the results into Delta tables so downstream users didn't have to deal with complex JSON. So I'm very comfortable handling nested JSONs and designing pipelines to make them analytics-ready."

**Q: Why use StructType instead of schema inference?**

**A:** "I usually prefer defining an explicit schema with StructType rather than relying on schema inference. The main reason is consistency and control. With inference, Spark looks at the data sample and guesses the schema, which can easily break if the source adds new columns, changes data types, or has inconsistent null values. For example, a numeric column with occasional nulls might get inferred as a string, and suddenly downstream logic fails. By defining the schema with StructType, I ensure the data always comes in with the correct types, and if the source drifts, the job fails fast so we can catch it. It also improves performance because Spark doesn't have to scan the data first to infer the schema. So the advantage is reliability, predictable data types, and faster ingestion, especially when dealing with large or complex JSON."

### 9. Validation Frameworks

**Q: Can you explain your validation frameworks experience?**

**A:** "Yes, in Walgreens I built validation frameworks mainly inside the Databricks notebooks using PySpark. The idea was to have a reusable set of checks that could run consistently across different datasets. For example, I implemented schema validation where I compared the incoming schema to the expected StructType and failed fast if there was a mismatch. I also added data quality checks like null checks on mandatory fields, duplicate detection using window functions, referential integrity checks against dimension tables, and basic profiling like row counts before and after transformations. The framework was parameterized, so instead of rewriting logic for every dataset, I could pass in the rules and apply them dynamically. Any records that failed were written to a quarantine location with error codes and counts were logged into control tables. Those metrics were then surfaced in Power BI so stakeholders could monitor data quality centrally. This approach made validations systematic and reusable, instead of being scattered one-off checks inside each pipeline."

### 10. Data Governance & Security

**Q: How did you protect PII data in your databases?**

**A:** "At Walgreens protecting PII was a big priority, so we built controls both at the pipeline and storage levels. In Databricks, any PII fields such as customer name, address, phone, or email were masked or tokenized as soon as they landed. For example, we used hashing for identifiers and encryption for sensitive attributes where masking wasn't enough. Access to raw PII data was restricted through role-based access control, and with Unity Catalog we could enforce fine-grained permissions so only authorized users could view certain columns. In the curated Silver and Gold layers, we exposed only the masked or anonymized versions of data, never the raw PII, and for analytics most use cases worked fine with surrogate keys or pseudonyms instead of real values. On top of that, secrets like keys and connection strings were stored in Azure Key Vault and not in notebooks. So the combination of masking, encryption, access control, and secret management gave us a secure approach to handling PII end-to-end."

### 11. Partitioning & Performance

**Q: Can you talk about the partitioning techniques you used?**

**A:** "In Walgreens, partitioning was one of the key techniques I used to handle large volumes efficiently. For landing and raw data in the Bronze layer, we typically partitioned by ingest date so that we could easily trace and reload data if needed. In the Silver and Gold layers, partitioning was driven by the business use case. For example, sales and transaction-level data was partitioned by business date, sometimes also by store or region, because most of the downstream queries and reports were filtered on those columns. That way, Spark could prune partitions and avoid scanning the entire dataset. In some cases, we also combined partitioning with Z-ORDER in Delta to optimize queries that filtered on customer or product IDs. The goal was always to balance partition size—large enough to reduce overhead but small enough to parallelize well—so we targeted file sizes of a few hundred MB per partition after compaction. This approach reduced read times significantly and made incremental loads much faster."

**Q: How do you balance partitioning for different query patterns?**

**A:** "I'd start by picking a single primary partition that matches the dominant access pattern—here that's almost always the business date—so recent and date-filtered queries get strong partition pruning and fast reads. For the merchant, product-centric angle, I wouldn't create a second physical partition on the same table because that explodes small files and hurts writes; instead I'd lean on Delta techniques to make those filters fast: routinely OPTIMIZE the table and Z-ORDER on product keys so the data files are clustered for product filters, which lets the engine skip most files even though the table is date-partitioned. For heavy merchant use cases, I'd add a product-focused Gold table or aggregate (for example daily product performance by store) that's fed incrementally from the same Silver data, so product dashboards hit a compact, purpose-built table while everyone else continues using the date-partitioned fact. Together this gives you the best of both worlds: simple, stable partitioning for the bulk of users, and fast product queries via Z-ORDER and a targeted product mart, without duplicating all the transformation logic."

### 12. Synapse to Databricks Migration

**Q: How would you migrate Synapse notebooks to Databricks?**

**A:** "Yes, I've worked with Synapse too. If I need to migrate a Synapse notebook to Databricks, the main steps are:

- **Language differences**: Synapse notebooks often use T-SQL or Spark (Scala/PySpark). In Databricks I'd convert everything to PySpark APIs or SQL cells. For example, replace `%%sql` T-SQL queries with `spark.sql()` or PySpark DataFrame operations.
- **Library/connector changes**: Synapse may use built-in connectors; in Databricks I'd use Spark's read APIs or Azure connectors (ADLS, JDBC, etc.).
- **Config/secrets**: Replace Synapse linked services with Databricks secrets / Key Vault scopes.
- **Optimization**: Tune for Databricks (broadcast joins, partitions, Delta Lake MERGE) since Databricks has more optimization features.
- **Testing**: Validate outputs row counts, schema, and performance against the Synapse version before fully cutting over.

That's how I'd migrate Synapse notebooks — mainly adjusting SQL to PySpark syntax, connectors, and configs to run smoothly in Databricks."

### 13. CI/CD Experience

**Q: What's your CI/CD experience?**

**A:** "In Walgreens I was involved in setting up CI/CD mainly for our Databricks notebooks and ADF pipelines. For Databricks, we integrated with Git so all notebooks were version-controlled, and we used feature branches and pull requests for code reviews. Deployments were automated through Azure DevOps pipelines, where we packaged notebooks and configuration files and deployed them to different workspaces like dev, test, and prod. For ADF, we stored pipeline JSONs in Git as well, and used DevOps release pipelines to publish from one environment to another, making sure linked services and parameters were environment-specific. We also set up automated validation steps, such as linting code, running unit tests on PySpark functions, and checking schema compatibility before a release. This gave us consistent deployments, reduced manual errors, and allowed us to roll back if needed. It also made collaboration with the offshore team easier because everyone worked off the same repo and process."

### 14. Unity Catalog vs Hive Metastore

**Q: Have you worked on Unity Catalog or Hive Metastore?**

**A:** "Yes, I've worked with both. In Walgreens we initially used the Hive Metastore as the catalog, but later we started moving to Unity Catalog. Hive Metastore worked fine for basic table registrations, but it had limitations when it came to centralized governance and consistent permissions across multiple workspaces. With Unity Catalog, we were able to centrally manage tables, schemas, and permissions, which gave us stronger security and simplified access control. It also helped with lineage tracking, auditing, and data discovery, so users could easily find and trust the right datasets. In practice, I still created and managed Delta tables in notebooks, but Unity Catalog added that extra layer of governance and control that Hive Metastore couldn't provide."

### 15. Data Source Integration

**Q: What sources were you getting data from?**

**A:** "In Walgreens we were pulling data from more than fifteen different sources. Some were structured sources like Oracle and SQL Server databases, some were flat files such as CSV and JSON coming through SFTP, and we also had API-based sources providing incremental feeds. All of these landed first into ADLS using ADF pipelines, and from there I processed them in Databricks with PySpark to standardize formats, validate schemas, and transform them into Delta tables. So it was a mix of databases, files, and APIs coming together into the Azure data lake."

**Q: How do you work with APIs from your notebook?**

**A:** "Yes, I have worked with APIs directly from Databricks notebooks. I usually call the API using Python's requests library inside the notebook, fetch the JSON response, and then load it into a PySpark DataFrame. Once it's in a DataFrame, I apply schema validation, flatten any nested fields, and then write the clean data into Delta tables in ADLS. For larger or recurring feeds, I integrate the API call with ADF so it can trigger the notebook automatically, making the process part of our scheduled pipelines. This way we could combine API data with other sources like databases and flat files in the same data lake."

### 16. Data Modeling Experience

**Q: Can you talk about your modeling experience?**

**A:** "In Walgreens it was a mix. Sometimes we got fairly clear requirements, for example a business team might already know the KPIs they needed and would specify the measures and dimensions they expected. In other cases, the requirements were high level, like 'we want transaction-level data available for analysis,' and it was up to me and the team to shape the model. My role was to take the raw sources from Bronze, clean and conform them in Silver, and then design Gold layer tables in a way that was business-friendly. Typically this meant creating fact tables at the right grain, such as one row per transaction or per line item, and then building supporting dimension tables like product, store, or customer. I applied best practices like surrogate keys, handling slowly changing dimensions when historical tracking was needed, and partitioning facts by business date to keep performance high. So while sometimes I worked off well-defined specs, other times I designed the Delta models myself based on both source system analysis and the reporting needs communicated by stakeholders."

### 17. Multi-System Data Management

**Q: How do Databricks, Synapse, and Snowflake interplay?**

**A:** "Yes, each of them had a specific role in the Walgreens setup. Databricks was really the engine for ingestion and transformation, where we landed the raw data, applied validations, and built the Bronze, Silver, and Gold Delta tables. Synapse was mainly used as a serving layer for Power BI dashboards because the business already had a lot of reporting built on Synapse, so we pushed curated Gold tables there for easy integration. Snowflake came into the picture for certain analytics and partner reporting use cases, since some teams preferred working in Snowflake for ad-hoc analysis and external data sharing. So the flow was: ingest and process in Databricks, curate into Delta tables, then publish subsets into Synapse or Snowflake depending on the consumer. That way Databricks handled the heavy lifting and data quality, while Synapse and Snowflake made it easy to serve the right data to different types of users."

**Q: Did you have issues with multiple copies of data?**

**A:** "Yes, that was definitely one of the challenges. Since the authoritative copy was in the Delta Lake on Databricks, whenever we pushed data into Synapse or Snowflake there was always the risk of drift if the loads weren't aligned perfectly. For example, if a pipeline failed mid-run or if there was a schema change that got applied in Databricks but not updated in the downstream system, the copies could get out of sync. To address that, we built reconciliation checks comparing record counts and hash totals between Delta and Synapse/Snowflake after each load. We also moved away from full refreshes and relied more on incremental MERGE loads, which reduced the window for mismatches. In addition, we logged schema versions and put validation at the pipeline level so any change in Databricks had to be reflected in the mappings before the publish step would succeed. It wasn't perfect, but these controls helped us keep consistency across multiple systems while still meeting the business need of having data available in both Synapse and Snowflake."

## Key Talking Points

### Walgreens Project Summary
- **Role**: Senior Data Engineer on data migration and modernization project
- **Scale**: 15+ sources, 10+ TB monthly processing
- **Technologies**: Azure Data Factory, Databricks, PySpark, Delta Lake
- **Architecture**: Bronze-Silver-Gold medallion architecture
- **Sources**: Oracle, SQL Server, CSV/JSON files, APIs
- **Downstream**: Synapse, Snowflake, Power BI

### Technical Strengths
1. **PySpark Expertise**: Primary development language for data processing
2. **ADF Orchestration**: Parameterized pipelines for ingestion
3. **Schema Enforcement**: Explicit StructType definitions, validation frameworks
4. **Performance Tuning**: Partitioning, broadcasting, incremental loads
5. **Data Quality**: Validation frameworks, error handling, monitoring
6. **CI/CD**: Git integration, automated deployments, code reviews

### Production-Ready Code Standards
- Error handling with try/except blocks
- Comprehensive logging and metrics
- Parameterized configurations (no hardcoding)
- Data quality checks and quarantine paths
- Idempotent operations with Delta MERGE
- Security through Key Vault integration
- Documentation and version control

## Leadership & Communication

### Team Collaboration
- **Onsite-Offshore Coordination**: Daily syncs with offshore team
- **Stakeholder Communication**: Clear explanation of technical solutions to business teams
- **Issue Resolution**: Proactive problem-solving and escalation
- **Knowledge Transfer**: Documentation and training for team members

### Project Leadership Examples
- **Standard Setting**: Established coding standards and best practices
- **Process Improvement**: Added logging, error handling, and reusable components
- **Cross-team Collaboration**: Worked with business SMEs and technical teams
- **Delivery Management**: Ensured on-time delivery through effective coordination

### Communication Style
- **Technical Translation**: Converting business requirements to technical solutions
- **Clear Documentation**: README files, inline comments, and process documentation
- **Regular Updates**: Status reports and issue escalation
- **Training & Mentoring**: Helping team members grow their skills

## Project Background

### Current Role Expectations
- **Hands-on Development**: Deep PySpark and Databricks expertise
- **Data Modeling**: Bronze-Silver-Gold architecture implementation
- **Performance Optimization**: Tuning for large-scale data processing
- **Team Leadership**: Guiding offshore teams and stakeholders
- **Platform Building**: Creating reusable, maintainable data solutions

### Key Success Factors
1. **Technical Depth**: Strong hands-on experience with core technologies
2. **Production Focus**: Building reliable, monitored, scalable solutions
3. **Collaboration**: Effective communication with diverse stakeholders
4. **Continuous Learning**: Adapting to new technologies (Fabric, Unity Catalog)
5. **Quality Standards**: Consistent, well-documented, maintainable code

### Future Opportunities
- **Microsoft Fabric**: Next-generation data platform adoption
- **Advanced Analytics**: Machine learning and AI integration
- **Data Governance**: Enhanced security and compliance
- **Team Scaling**: Building internal expertise and capabilities

---

## Interview Tips

### Preparation Strategy
1. **Review Technical Concepts**: PySpark, Databricks, ADF fundamentals
2. **Practice Scenarios**: Data processing, modeling, optimization
3. **Prepare Examples**: Specific project experiences and outcomes
4. **Leadership Stories**: Team coordination and stakeholder management
5. **Current Trends**: Fabric, Unity Catalog, modern data architecture

### Key Messages to Convey
- **Hands-on Expertise**: Deep technical skills with practical experience
- **Production Focus**: Building reliable, scalable, maintainable solutions
- **Collaboration Skills**: Effective team leadership and communication
- **Continuous Learning**: Adaptability and growth mindset
- **Quality Standards**: Commitment to best practices and excellence

### Questions to Ask
- **Technical Challenges**: What are the current data processing bottlenecks?
- **Architecture Evolution**: How is the platform moving toward Fabric?
- **Team Structure**: What's the collaboration model between onsite and offshore?
- **Growth Opportunities**: What are the learning and advancement paths?
- **Project Scope**: What are the immediate priorities and long-term goals?

---

*This guide serves as a comprehensive reference for data engineering interviews, emphasizing both technical depth and leadership capabilities. Use these talking points to demonstrate expertise while showing how your experience aligns with the role requirements.*
