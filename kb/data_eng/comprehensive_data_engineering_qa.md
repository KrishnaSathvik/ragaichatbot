---
tags: [data-engineering, pyspark, databricks, azure-data-factory, delta-lake, optimization, governance, walgreens, interview-prep, scenarios]
---

# Comprehensive Data Engineering Q&A - 120 Questions

## Section A: Core PySpark + Databricks (20 Questions)

### Q1. What is your experience with PySpark in your current project?
**A:** In my Walgreens project, I built end-to-end PySpark pipelines in Databricks that processed over 10TB monthly. I handled ingestion of raw data into Bronze, applied transformations and schema validation in Silver, and modeled fact/dimension tables in Gold for reporting. I frequently used PySpark DataFrame APIs, window functions, UDFs, and joins. For example, I implemented deduplication logic using `dropDuplicates()` and window functions, ensuring the most recent transaction record is retained.

### Q2. How do you handle large datasets in PySpark efficiently?
**A:** First, I design partitioning strategies at ingestion (date-based partitions). Second, I tune Spark configurations like `spark.sql.shuffle.partitions` and executor memory. Third, I use optimizations such as broadcast joins for small lookup tables and salting for skewed keys. For large jobs, I enable Adaptive Query Execution. In one case, these changes reduced a pipeline runtime from 2+ hours to 40 minutes.

### Q3. How do you debug PySpark jobs when they fail?
**A:** I start with Spark UI to analyze DAGs, stages, and tasks. I check for skew (few tasks taking much longer) or memory errors. Then I check logs in Databricks for stack traces. I usually replay the job with a smaller dataset to isolate the failing transformation. For example, when a job failed due to a corrupt record, I added `_corrupt_record` handling and moved bad rows into a quarantine table.

### Q4. How do you handle nested JSON in PySpark?
**A:** I define a StructType schema, use `from_json` to parse the string column, and `explode` for arrays. Then I flatten with `withColumn` to extract nested attributes. For deeply nested JSON, I use recursive functions to normalize. Finally, I store it as a clean Delta table in Silver for downstream consumption.

### Q5. How do you handle duplicates in PySpark?
**A:** For simple duplicates, I use `dropDuplicates()`. For business-specific deduplication, I use window functions with `row_number()` ordered by timestamp, keeping only the latest row. In Walgreens, this was used for handling multiple prescription updates from pharmacy systems.

### Q6. How do you handle schema drift in PySpark pipelines?
**A:** In Bronze, I ingest with permissive mode to avoid job failure. In Silver, I enforce strict schema. If new columns appear, I add them with defaults in Silver after business validation. For Delta tables, I use `mergeSchema` in controlled deployments, never blindly. This allows flexibility but avoids breaking downstream queries.

### Q7. How do you design incremental loads in PySpark?
**A:** I use watermarking (modified_date column) or surrogate keys. ADF passes parameters to notebooks for last processed date. In PySpark, I filter only incremental rows and apply Delta `merge` to update/inserts. This reduced daily runs from processing 10TB full to ~300GB delta, saving cost and runtime.

### Q8. Can you explain time travel in Delta Lake? How have you used it?
**A:** Time travel lets me query data at a specific version or timestamp. At Walgreens, one job overwrote 2 days of data. Using `VERSION AS OF` in Delta, I restored the table to its previous state in minutes without reloading raw files.

### Q9. How do you handle slowly changing dimensions (SCD) in Databricks?
**A:** I used Delta `merge` for Type 2. Old record is closed with an end_date, new record inserted with active_flag = 1. This keeps historical changes. For example, when product pricing changed, our dimension table kept both old and new versions for accurate reporting.

### Q10. How do you monitor PySpark jobs?
**A:** I log metadata like job ID, start/end time, row counts, and error counts into monitoring tables. ADF sends failure alerts. Additionally, I surface monitoring dashboards in Power BI so IT and business both see pipeline health.

### Q11. How do you implement joins in PySpark for performance?
**A:** For large-large joins, I repartition on join keys to avoid skew. For small-large joins, I use `broadcast()`. For very skewed joins, I salt keys. I always monitor shuffle size in Spark UI.

### Q12. How do you handle corrupt records in ingestion?
**A:** I use `PERMISSIVE` mode in PySpark read, which places bad records in `_corrupt_record`. I redirect them into a quarantine Delta table for manual review, while valid data continues processing.

### Q13. How do you test PySpark pipelines?
**A:** Unit tests validate transformations with small sample data. Row count reconciliation checks ingestion completeness. Schema validation checks enforce consistency. We automated these checks in CI/CD pipelines.

### Q14. How do you manage dependencies across notebooks in Databricks?
**A:** I modularize common logic (like validations, schema enforcement) in utility notebooks or .py files stored in repos. Then I import them into main notebooks. This avoids code duplication and keeps pipelines maintainable.

### Q15. How do you handle late arriving data?
**A:** I use watermarking in Delta tables, so late data is still merged if within X days. If outside retention, we load them manually after business approval.

### Q16. How do you handle large joins across multiple datasets?
**A:** First, partition both datasets on the join key. If one is small, broadcast it. If skew occurs, apply salting. If still heavy, break into smaller joins and cache intermediate results.

### Q17. How do you manage PySpark code for reusability?
**A:** I follow modular design: separate ingestion, transformation, validation, and load functions. I store configs in parameter files, not hardcoded. Reusable frameworks allowed offshore to easily plug in new sources with minimal code.

### Q18. How do you optimize PySpark DataFrame transformations?
**A:** Avoid wide transformations until necessary, use `select` instead of `*`, cache intermediate results when reused, and avoid UDFs unless unavoidable. Vectorized operations (pandas UDFs) are faster than row-wise ones.

### Q19. How do you manage error handling in PySpark?
**A:** I wrap critical transformations with try/except. Failures are logged into error tables. In ADF, we configure retries and failure alerts. This ensures job doesn't fail silently.

### Q20. What's the biggest challenge you solved with PySpark at Walgreens?
**A:** Optimizing a 10TB sales fact pipeline that originally took 2+ hours. By tuning partitioning, salting skewed joins, and compacting files, I reduced runtime to 40 minutes. This improved SLA compliance and cut costs by 30%.

## Section B: Azure Data Factory (ADF) & Orchestration (20 Questions)

### Q21. How did you use ADF in your Walgreens project?
**A:** I used ADF mainly for orchestration and scheduling of Databricks notebooks. ADF pipelines triggered ingestion of raw files into ADLS, parameterized notebook runs with date filters, and coordinated dependencies across multiple jobs. For example, when pharmacy and sales data needed to be processed together, ADF ensured ingestion → transformation → validation were executed in sequence with retries on failure.

### Q22. How do you parameterize ADF pipelines?
**A:** I use ADF global parameters and dataset parameters to make pipelines dynamic. For example, the source file path is parameterized with date and source name, so the same pipeline ingests multiple sources. Databricks notebook activities accept parameters for start_date and end_date, allowing incremental processing without hardcoding.

### Q23. How do you handle scheduling in ADF?
**A:** I use triggers — primarily tumbling window triggers for periodic jobs like daily loads, and event triggers for file arrival. For critical pipelines, we used tumbling window with retry policies. Business-critical reports were scheduled nightly at 2am, ensuring that Silver/Gold tables were refreshed before business started.

### Q24. How do you handle failure in ADF pipelines?
**A:** I configure retry policies on activities and failure paths to send alerts. Failed activities log errors in monitoring tables. For example, if a Databricks notebook failed due to schema mismatch, ADF retried once, and on repeated failure, triggered a Logic App alert to teams.

### Q25. How do you design ADF pipelines for scalability?
**A:** I avoid building one massive pipeline. Instead, I create modular pipelines — ingestion, transformations, validations — and link them with pipeline chaining. I also parameterize everything, so the same pipeline works across multiple sources. This reduced maintenance and improved reusability for offshore team.

### Q26. How do you handle dependencies between ADF pipelines?
**A:** I use dependency triggers and pipeline chaining. For example, Silver pipeline starts only after Bronze ingestion completes successfully. If multiple datasets must be ready before Gold processing, I use "Wait on Activity" or success/failure dependencies.

### Q27. How do you integrate ADF with Databricks?
**A:** ADF has a "Databricks Notebook" activity. I configured linked services with Key Vault for secrets, so credentials aren't hardcoded. Each notebook call passes parameters like file_date, source system, or load_type. This ensured pipelines remained dynamic and secure.

### Q28. How do you handle incremental data loads with ADF?
**A:** I store last run watermark in a metadata table. ADF fetches this value, passes it to Databricks as parameter. Databricks then queries only new/updated data and merges it into Delta. After successful load, ADF updates the watermark. This ensured daily loads were efficient.

### Q29. How do you monitor ADF pipelines?
**A:** I use ADF monitoring dashboard for real-time status. In addition, I log metadata like run_id, row counts, and errors into custom Delta tables. Failures are reported via email alerts. Power BI dashboards show historical success/failure trends, which helped management track SLA adherence.

### Q30. How do you secure ADF pipelines?
**A:** Secrets like database passwords and storage keys are stored in Azure Key Vault. ADF uses managed identities to connect to ADLS and Databricks. This eliminated hardcoding sensitive info.

### Q31. How do you design ADF for reusability?
**A:** I use parameterized datasets and pipeline templates. For example, one generic ingestion pipeline handled all CSV sources by passing schema, file_path, and delimiter as parameters. Offshore team just configured metadata, no code changes.

### Q32. How do you handle event-driven ingestion in ADF?
**A:** For real-time scenarios, I set up Event Grid triggers so ADF pipelines started as soon as new files landed in ADLS. This reduced latency from hours to minutes for near-real-time data availability.

### Q33. How do you integrate ADF with CI/CD?
**A:** ADF JSON definition files are stored in Git. Azure DevOps pipelines deploy these JSONs across dev, test, and prod environments. Parameters like connection strings are environment-specific and replaced during deployment using ARM templates.

### Q34. How do you deal with long-running pipelines?
**A:** For long pipelines, I break them into smaller pipelines with checkpoints. This ensures partial success is saved and we don't restart everything on failure. For example, ingestion pipeline completed successfully even if transformation pipeline failed, allowing us to restart only transformations.

### Q35. How do you manage data validation with ADF?
**A:** After ingestion, I run validation notebooks triggered by ADF. These check row counts, null ratios, and duplicates. ADF logs validation status into Delta tables. Alerts are raised if thresholds are violated.

### Q36. How do you manage metadata in ADF pipelines?
**A:** I store pipeline configs (file paths, schema, business rules) in metadata tables. ADF reads metadata at runtime and applies ingestion accordingly. This approach made pipelines completely dynamic — new sources onboarded without code changes.

### Q37. How do you optimize ADF performance?
**A:** I configure parallel copy in copy activities, use staging in ADLS/Blob, and partition large files. For example, one large file was split into multiple blocks and ingested in parallel, reducing ingestion time from 40 minutes to under 10.

### Q38. How do you orchestrate multiple technologies with ADF?
**A:** ADF orchestrated ADLS, Databricks, Synapse, and Snowflake in my project. For example, ingestion from APIs landed in ADLS, processed in Databricks, exported to Snowflake, and then visualized in Power BI. ADF coordinated the entire workflow end-to-end.

### Q39. How do you handle SLA in ADF pipelines?
**A:** I tracked expected runtime and row counts. If pipelines exceeded thresholds, alerts triggered. For pharmacy data, SLA was 6am reporting availability — ADF was scheduled at 2am with monitoring, so if job failed, support team had time to re-run before SLA breach.

### Q40. What challenges did you face with ADF and how did you solve them?
**A:** One challenge was schema drift causing failures in ingestion. I solved it by using schema drift-tolerant ingestion at Bronze and enforcing strict schema at Silver. Another was long ingestion times, solved with parallel copy and partitioning. I also improved security by integrating Key Vault and managed identities, removing all hardcoded secrets.

## Section C: Delta Lake, Schema, Data Modeling (20 Questions)

### Q41. How did you design the medallion architecture in Walgreens?
**A:** I followed the medallion architecture — Bronze, Silver, and Gold layers. Bronze captured raw ingested data exactly as it arrived from sources, tolerant to schema drift. Silver applied schema enforcement, deduplication, and standardization, making the data clean and query-ready. Gold was modeled into fact and dimension tables optimized for reporting. This layered approach made pipelines robust, reusable, and easy for business teams to consume.

### Q42. How do you enforce schema in Delta Lake?
**A:** I applied explicit schemas during ingestion, not relying on inference in production. For schema evolution, I used `mergeSchema` in controlled updates. For example, when a new column was introduced in sales data, I validated it in dev, updated downstream logic, and then enabled schema merge. This prevented silent failures.

### Q43. How do you handle schema drift?
**A:** Bronze is flexible — it accepts extra columns and quarantines bad rows. Silver enforces schema strictly. Any new column is validated in dev first. If valid, I add it with defaults and update documentation. This two-layer enforcement avoids unexpected breakages.

### Q44. How do you design fact and dimension tables in Gold?
**A:** I model fact tables to capture transactional data like sales, and dimension tables to capture master data like product, store, and customer. Facts include foreign keys to dimensions. I also denormalize selectively for performance. KPIs like revenue per store were modeled in Gold for Power BI dashboards.

### Q45. How do you design SCD (Slowly Changing Dimensions)?
**A:** I implemented Type 2 SCD with Delta merge. When a dimension attribute changes, I close the old record with an end_date and insert a new record with active_flag = 1. This preserved historical accuracy. Example: product price changes required Type 2 so reports showed past sales at old prices.

### Q46. How do you manage historical versions of data?
**A:** Delta Lake's time travel feature allowed querying older versions of tables. For example, when an accidental overwrite occurred, I restored previous version using `VERSION AS OF`. This was faster than reprocessing from raw files.

### Q47. How do you deal with null values in schema enforcement?
**A:** I use PySpark `fillna` or business rules to assign defaults. In Silver, nulls in critical columns are flagged in validation tables. Business-approved defaults like "Unknown" for missing store_id ensure pipelines don't break.

### Q48. How do you validate transformations across layers?
**A:** I reconcile row counts and key distributions from Bronze → Silver → Gold. I log validation results into Delta monitoring tables. For example, I checked that deduplication didn't drop more records than expected.

### Q49. How do you design partitioning in Delta tables?
**A:** I usually partition large datasets by date, as most queries are time-based. For multi-dimensional queries, I use ZORDER indexing. Example: sales fact was partitioned by transaction_date, with ZORDER on store_id and product_id for efficient pruning.

### Q50. How do you manage small file problems in Delta?
**A:** I use `OPTIMIZE` in Databricks to compact small Parquet files into larger ones. I also control batch size during ingestion in ADF to avoid excessive tiny files. For Gold, I scheduled weekly compaction jobs to keep query performance high.

### Q51. How do you design data models for reporting?
**A:** I followed Kimball principles: fact tables for metrics, dimension tables for descriptive attributes, and star schema design. I ensured measures like sales_amount were additive and dimensions like date, product, and store enabled slice-and-dice in Power BI.

### Q52. How do you manage data lineage?
**A:** Unity Catalog and Purview tracked lineage across layers. For example, lineage view showed pharmacy source files → Silver clean table → Gold fact → Power BI dashboard. This transparency helped in audits and troubleshooting.

### Q53. How do you handle late-arriving facts in modeling?
**A:** I used Delta merge to insert or update late-arriving facts. If fact arrived after dimension change, I ensured it still mapped correctly using surrogate keys. For example, late prescription transactions still mapped to the correct product dimension.

### Q54. How do you manage surrogate keys in dimensions?
**A:** I generated surrogate keys in Silver using hash functions on natural keys. These surrogate keys became dimension table primary keys. Fact tables stored foreign keys referencing them. This approach ensured consistency even if natural keys changed.

### Q55. How do you validate fact/dimension consistency?
**A:** I ran referential integrity checks — ensuring every fact foreign key matched a valid dimension key. Invalid records were flagged in a quarantine table for review.

### Q56. How do you manage incremental loads into Gold models?
**A:** I used Delta `merge` for upserts. Facts were loaded incrementally based on modified_date. Dimensions were updated using SCD logic. This kept models fresh without reprocessing full history.

### Q57. How do you optimize Gold layer models for BI?
**A:** I pre-aggregated summary tables for common KPIs, reduced joins by denormalizing small dimensions, and compacted files. This ensured Power BI dashboards loaded in seconds instead of minutes.

### Q58. How do you handle multi-source integration in modeling?
**A:** I standardized schemas across sources in Silver. Then I conformed them into unified dimensions. Example: pharmacy and sales sources had different store codes. I standardized codes and built a single store dimension in Gold.

### Q59. How do you document data models?
**A:** I maintained data dictionaries in Confluence, showing column definitions, lineage, and business rules. Unity Catalog also stored schema metadata. This documentation helped both developers and business users.

### Q60. What challenges did you face in data modeling and how did you solve them?
**A:** One challenge was aligning different source systems with inconsistent schemas. I solved it by applying conformance rules in Silver and building standardized dimensions. Another challenge was query slowness in Power BI; I solved it by pre-aggregating summary tables and optimizing partitioning.

## Section D: Optimization, Performance & Troubleshooting (20 Questions)

### Q61. How did you optimize Spark jobs for large data volumes?
**A:** First, I ensured partitioning strategy matched query patterns, usually date-based. Then, I tuned shuffle partitions (`spark.sql.shuffle.partitions`) based on cluster size, avoiding both too few (skew) and too many (overhead). For joins, I used broadcast for small tables, salting for skew, and AQE (Adaptive Query Execution) to rebalance tasks. I also compacted small files using `OPTIMIZE`. One sales pipeline dropped from 2+ hours to 40 mins with these steps.

### Q62. How do you identify bottlenecks in a Spark job?
**A:** I use Spark UI to analyze DAG stages, tasks, and shuffle read/write sizes. If some tasks run much longer, it usually signals skew. If GC overhead is high, executors need memory tuning. If there's high shuffle volume, I check if joins/aggregations are causing unnecessary repartitions.

### Q63. How do you resolve skew in Spark joins?
**A:** If skew is caused by a few heavy keys, I apply salting — appending a random suffix to distribute skewed keys across partitions. For small lookup joins, I use `broadcast()`. AQE also automatically splits skewed partitions at runtime in Databricks.

### Q64. How do you optimize Delta Lake performance?
**A:** I regularly run `OPTIMIZE` with ZORDER on frequently filtered columns. I compact small files into larger Parquet files, improving metadata handling. I also vacuum old versions to reduce storage overhead. For query pruning, I carefully partition on high-cardinality columns like date, not on low-cardinality ones.

### Q65. How do you handle small file problems?
**A:** I control ingestion batch size in ADF to avoid generating thousands of tiny files. After ingestion, I use `OPTIMIZE` in Delta to compact them. For streaming, I use auto-compaction. This reduces metadata load and speeds up queries.

### Q66. How do you handle long-running jobs?
**A:** First, I profile the job in Spark UI to identify slow stages. Then, I repartition or broadcast joins as needed. If the job processes full data daily, I redesign it to incremental load. For one job that ran for 5+ hours, converting to incremental reduced it to under 1 hour.

### Q67. How do you tune Spark cluster configurations?
**A:** I tune driver/executor memory based on data size. I increase executor cores for parallelism but avoid too many to prevent GC pressure. I use autoscaling for heavy workloads, but for cost control, I size clusters to match partitioning. I also enable cache for reused datasets.

### Q68. How do you optimize joins in PySpark?
**A:** I decide based on size: Small table + large table → broadcast join; Large tables with skew → repartition + salting; Balanced large tables → hash partition on join keys. I always avoid Cartesian joins and prune unnecessary columns before joining.

### Q69. How do you handle out-of-memory issues in Spark jobs?
**A:** I check if wide transformations (e.g., groupBy) are blowing up. Then, I increase executor memory or repartition data to spread load. I persist intermediate results on disk instead of memory if needed. In Walgreens, this fixed a memory issue with 1B+ row aggregation.

### Q70. How do you optimize aggregations in PySpark?
**A:** I partition data on aggregation keys, cache intermediate results if reused, and pre-filter unnecessary rows early. For distinct counts, I used approx algorithms like HyperLogLog when exact wasn't needed, saving resources.

### Q71. How do you debug frequent job failures?
**A:** I check Databricks logs for stack traces, isolate failing transformation, and test with sample data. If schema mismatch, I enforce schema in Bronze. If bad records, I redirect to quarantine. If infrastructure, I scale cluster or tune configs.

### Q72. How do you tune pipeline latency?
**A:** I parallelize independent tasks in ADF, use event triggers for real-time ingestion, and optimize Spark transformations for early filtering. For dashboards, I pre-aggregate Gold tables so BI loads in seconds.

### Q73. How do you troubleshoot data quality issues raised by business?
**A:** First, I trace lineage in Unity Catalog or Purview to identify which layer/data caused it. Then, I check validations in Silver logs. If caused by schema drift, I fix mapping and reprocess. Communication is key — I keep business updated on issue status and fix ETA.

### Q74. How do you deal with high shuffle volume in Spark jobs?
**A:** I reduce unnecessary shuffles by avoiding multiple repartitions, pruning columns early, and reusing partitioning. For unavoidable large shuffles, I increase shuffle partitions and enable AQE.

### Q75. How do you handle slow dashboards due to data issues?
**A:** I optimize Gold tables by compacting files, pre-aggregating metrics, and using summary tables. I also partition models so Power BI queries can prune efficiently. One KPI dashboard load time went from 90s to 15s after introducing summary tables.

### Q76. How do you debug performance issues across layers (Bronze → Silver → Gold)?
**A:** I compare row counts and timings logged at each layer. If Bronze is fine but Silver is slow, I check schema enforcement and dedup logic. If Gold is slow, I check joins and aggregations. Logging at each step helps isolate bottlenecks.

### Q77. How do you optimize pipelines for cost?
**A:** I use job clusters with auto-termination instead of always-on clusters. I right-size clusters based on workload. I compact files to reduce storage and metadata cost. For non-critical jobs, I use spot instances.

### Q78. How do you approach troubleshooting late data arrival?
**A:** I check if ingestion trigger failed in ADF. If source delayed, I escalate to source team. If files arrived but schema mismatched, I fix schema mapping and re-run partial load. I log SLA misses to ensure business visibility.

### Q79. How do you ensure optimized queries in BI tools?
**A:** I pre-aggregate Gold data, reduce table joins by denormalizing small dimensions, and ensure partition pruning. I also monitor Power BI query logs to tune backend models accordingly.

### Q80. What's the toughest optimization challenge you solved?
**A:** A sales fact pipeline processing 10TB+ daily was breaching SLA. Spark jobs had heavy shuffles and skewed joins. I applied salting, ZORDER, and partition tuning, and compacted files weekly. This reduced runtime from 2 hours to 40 minutes, restored SLA compliance, and saved 25% compute cost.

## Section E: Governance, CI/CD, Validation, Offshore & Stakeholder Collaboration (20 Questions)

### Q81. How did you implement data governance in Walgreens?
**A:** We used Unity Catalog as the central governance layer. It controlled table- and column-level access, enforced policies like masking PII, and provided lineage. For example, DOB and SSN columns were masked for analysts while full access was limited to compliance teams. Purview was also integrated to show lineage across ADF, Databricks, and Power BI.

### Q82. How do you protect PII data in Databricks?
**A:** I masked PII columns in Unity Catalog, enforced row-level security policies, and ensured encryption at rest in ADLS. Keys and secrets were stored in Key Vault, never in code. For reporting, Power BI consumed masked views, ensuring compliance while still supporting analysis.

### Q83. How do you ensure role-based access?
**A:** Unity Catalog roles were mapped to business roles. Developers had write access in dev, read-only in test/prod. Analysts had read-only access to Gold tables only. Access was granted at schema/table/column levels, following the principle of least privilege.

### Q84. How do you manage data lineage?
**A:** Unity Catalog and Purview automatically captured lineage from ingestion → transformation → Gold → dashboards. This made it easy to trace an issue in a dashboard back to the source system. Business teams used lineage views during audits to verify compliance.

### Q85. How do you integrate Databricks with Azure DevOps CI/CD?
**A:** We stored all notebooks and ADF pipelines in Git repos. Azure DevOps pipelines deployed them to different environments. Databricks CLI automated notebook deployment, and ADF JSONs were deployed with ARM templates. Environment variables replaced connection strings dynamically.

### Q86. How do you test pipelines before deployment?
**A:** I implemented unit tests on sample datasets, row count reconciliations, and schema validations in lower environments. Each PR triggered DevOps tests to ensure correctness before merging to main. Only validated pipelines were deployed to higher environments.

### Q87. How do you handle rollback in CI/CD if deployment fails?
**A:** Each deployment version was tagged in Git. If a pipeline failed in prod, I rolled back to the last stable version quickly using Git tags and redeployment. Delta Lake time travel also supported rolling back data changes.

### Q88. How do you validate data quality automatically?
**A:** I built a PySpark validation framework that ran checks like duplicates, nulls, referential integrity, and business rules. Results were logged into validation Delta tables. Any violations triggered ADF failure path alerts and were visible in Power BI dashboards.

### Q89. How do you report data quality to business?
**A:** Business users accessed a Power BI dashboard that showed row counts, duplicates, null % by table, and rule violations. This gave real-time transparency into data health. Business could drill down to see which rules failed.

### Q90. How do you monitor SLA compliance?
**A:** I logged pipeline run durations and compared them to SLA thresholds. If a pipeline breached SLA, ADF triggered alerts. Weekly SLA adherence reports were shared with stakeholders to ensure trust in data delivery.

### Q91. How do you collaborate with offshore teams?
**A:** I led daily standups with offshore, reviewing backlog and helping unblock them. I also created reusable PySpark frameworks (ingestion, validation) so offshore could onboard new sources with minimal coding. Code reviews and knowledge-sharing sessions ensured they ramped up quickly.

### Q92. How do you mentor offshore developers?
**A:** I reviewed their PySpark scripts, explained optimization techniques like partitioning and salting, and walked them through Spark UI. I also created runbooks for common errors so they could resolve issues without escalation.

### Q93. How do you handle production incidents with offshore?
**A:** Offshore raised tickets during their shift. I joined morning calls, reviewed logs, and guided them in root cause analysis. If it was schema drift, I advised schema mapping. If infrastructure, I helped with cluster tuning. Communication with business ensured transparency on resolution ETA.

### Q94. How do you communicate with stakeholders?
**A:** I tailored communication: technical details for developers, impact and ETA for business stakeholders. For example, when a pipeline failed due to schema drift, I told business: "Data will be delayed by 1 hour while we patch schema. No data loss." This maintained confidence.

### Q95. How do you balance technical delivery with business priorities?
**A:** I aligned backlog with business SLA commitments. Critical sales reports were prioritized for early-morning refresh. Less critical pipelines (like historical reloads) were scheduled during off-peak. This kept business impact minimal.

### Q96. How do you approach handling unexpected requests?
**A:** I first clarify urgency with the business, then estimate technical impact. If it's quick (like adding a column), I handle same day. If bigger (like new dataset), I put it in sprint backlog. For example, adding a new KPI to Power BI was prioritized within 24h because executives needed it.

### Q97. How do you ensure compliance in pipelines?
**A:** I ensured encryption at rest (ADLS), masking in Unity Catalog, and logging of all access requests. Data quality dashboards ensured transparency. For audits, Purview lineage reports showed full data flows, proving compliance.

### Q98. How do you track pipeline metrics over time?
**A:** I logged row counts, runtime, and errors into Delta monitoring tables. A Power BI dashboard visualized historical pipeline performance, showing trends in failures or runtimes. This helped proactively optimize before SLAs broke.

### Q99. How do you ensure knowledge transfer across teams?
**A:** I maintained detailed documentation in Confluence, covering pipeline design, schema definitions, and troubleshooting steps. I also held KT sessions with offshore, walking through real examples in Databricks notebooks.

### Q100. What's your biggest governance or collaboration achievement?
**A:** My biggest achievement was implementing Unity Catalog + validation framework end-to-end. It ensured PII was masked, data lineage was transparent, and business saw data quality dashboards. Combined with mentoring offshore, it built trust in the system. Stakeholders appreciated that pipelines were compliant, optimized, and reliable — all while I led a distributed team.

## Section F: Scenario-Based Questions (20 Questions)

### S1. Scenario: A downstream Power BI dashboard shows wrong sales numbers. How do you handle it?
**A:** First, I'd trace lineage in Unity Catalog to identify which Gold table feeds that report. Then, I'd check Silver → Gold transformations for logic errors. I'd validate row counts and business rules in validation logs. If the issue came from source schema drift (like a new column added in pharmacy data), I'd patch mapping in Silver, reprocess affected partitions, and communicate with stakeholders immediately, explaining ETA for fix. This keeps business confidence while resolving the root cause.

### S2. Scenario: Your pipeline starts failing at 2am due to corrupt input files. What's your approach?
**A:** I'd configure ingestion with `PERMISSIVE` mode so corrupt rows are flagged into `_corrupt_record`. These rows would be redirected into a quarantine Delta table. The main pipeline would continue for good rows, avoiding SLA breach. Later, I'd review the bad records, escalate to source teams, and patch schema validation if needed. This way, business dashboards still refresh on time.

### S3. Scenario: You need to migrate Synapse notebooks into Databricks. How would you do it?
**A:** Synapse transformations are SQL-based. I'd first review existing T-SQL scripts, then rewrite them into PySpark DataFrame transformations in Databricks. I'd leverage Delta Lake features like ACID and time travel for consistency. To validate migration, I'd reconcile row counts, run sample KPI checks, and parallel-run old Synapse vs new Databricks for a cycle before cutover.

### S4. Scenario: A job that usually runs in 30 minutes suddenly takes 2 hours. How do you troubleshoot?
**A:** I'd check Spark UI to see if shuffle partitions increased, or if skew developed. I'd check recent data volume spikes. If caused by skew, I'd apply salting or broadcast joins. If due to small file explosion, I'd run compaction (`OPTIMIZE`). If it's cluster issue, I'd tune executors or restart with right sizing. Documentation of findings ensures root cause is understood.

### S5. Scenario: Two sets of users need different partitioning (state-based vs product-based). How do you solve it?
**A:** Instead of duplicating datasets, I'd partition primarily on date (common for both) and apply ZORDER indexing on state and product columns. This ensures pruning for both user groups. If certain queries are very heavy, I'd create summary tables (by state or product) in Gold for faster BI performance.

### S6. Scenario: A new data source is onboarded. How do you make your pipeline flexible?
**A:** I'd store ingestion configs in metadata tables (path, schema, delimiter, rules). ADF would read configs and trigger the generic ingestion pipeline. In Silver, reusable PySpark validation functions enforce schema and rules. Offshore team only needs to add metadata entries, no code changes. This accelerates onboarding.

### S7. Scenario: Business complains KPIs don't match finance reports. What's your action plan?
**A:** First, I'd meet with finance team to understand calculation logic. Then, I'd trace current KPI logic in Gold models. If discrepancy is due to business rule misalignment (e.g., revenue net of returns), I'd adjust logic and document it. If due to data lag, I'd reschedule refresh. Clear documentation + governance ensures future alignment.

### S8. Scenario: Pipeline fails due to schema drift — new column added in source. What's your fix?
**A:** Bronze ingests flexibly. In Silver, I'd add the new column with default or nulls, update schema enforcement, and test in dev. After validating downstream transformations, I'd push change to prod. I'd also update schema documentation and inform business about the new attribute.

### S9. Scenario: Offshore reports jobs failed overnight, but you're onsite. How do you handle?
**A:** I'd quickly check logs to identify root cause. If it's schema mismatch, I'd patch mapping. If volume spike, I'd rescale cluster. I'd communicate to business with ETA ("Data delayed by 1 hour, fix in progress"). Meanwhile, I'd guide offshore via call so they learn the resolution. This builds trust and team capability.

### S10. Scenario: Data load is complete but dashboards are very slow. What's your fix?
**A:** I'd review Gold models. If queries scan too many rows, I'd pre-aggregate summary tables. I'd compact files (`OPTIMIZE`) and ensure partitioning matches query filters. For Power BI, I'd use DirectQuery with RLS and reduce joins by denormalizing smaller dimensions.

### S11. Scenario: You need to handle late-arriving sales transactions. How do you design this?
**A:** I'd use Delta `merge` with watermarking. Late rows within X days are merged automatically. If outside retention, I'd reprocess specific partitions after business approval. For analytics, SCD ensures late facts still map to correct dimension versions.

### S12. Scenario: Business requests PII masking for compliance. What's your approach?
**A:** I'd configure Unity Catalog to mask sensitive columns like SSN or DOB. Only compliance teams would see full values. Analysts would see masked/nulls. Access logs would track queries. This balanced compliance and usability.

### S13. Scenario: API source throttles requests, but you must ingest daily. How do you manage?
**A:** In ADF, I'd configure pagination and retries. In Databricks, I'd implement rate-limiting logic with exponential backoff. If needed, I'd parallelize calls with controlled concurrency. Failures are logged and retried separately, so ingestion completes within SLA without breaching API limits.

### S14. Scenario: You find too many small files in ADLS. How do you handle this?
**A:** I'd batch ingestion in ADF to reduce small files. In Delta, I'd run weekly compaction jobs (`OPTIMIZE`) and ZORDER for query columns. This reduced file count, improved performance, and lowered metadata overhead.

### S15. Scenario: A regulatory audit requires proof of lineage. How do you provide it?
**A:** I'd use Purview/Unity Catalog lineage reports to show flow from source → Bronze → Silver → Gold → dashboard. This visual lineage, plus validation logs, provided end-to-end transparency. During audit, we demonstrated compliance with role-based access and PII masking.

### S16. Scenario: Pipeline processing jumps from 1TB/day to 5TB/day. How do you scale?
**A:** I'd scale clusters with more executors temporarily. Then, I'd review partitioning to ensure balanced distribution. I'd switch from full loads to incremental using modified_date. I'd also optimize joins and ZORDER on high-cardinality columns. This allowed scaling without uncontrolled cost.

### S17. Scenario: Business wants new KPI "avg sales per customer" in dashboards. How do you deliver?
**A:** I'd update Gold model by joining sales fact with customer dimension, compute metric in PySpark, and store in summary table. I'd validate numbers with business team, deploy changes via CI/CD, and update Power BI to expose the new KPI.

### S18. Scenario: Data quality check flags 5% null store_id in Silver. What's your action?
**A:** I'd first confirm if nulls are due to source issues. If yes, escalate to source team. Meanwhile, I'd assign default store "Unknown" for analysis continuity. I'd document rule and flag these records in data quality dashboard so business is aware.

### S19. Scenario: Offshore wants to add a new pipeline but lacks guidance. How do you help?
**A:** I'd ask them to define source and target configs in metadata. Then, I'd guide them on plugging configs into our reusable ingestion framework. I'd review their PySpark script and provide optimization tips. Over time, this made them independent and efficient.

### S20. Scenario: Customer interview asks: 'What's your biggest achievement?'
**A:** I'd highlight optimizing a 10TB sales pipeline from 2+ hours to 40 mins using partition tuning, salting, ZORDER, and compaction. This improvement ensured SLA compliance and cut costs by 25%. I'd also mention building validation dashboards for data quality, which gave business confidence in our platform.

---

## Key Takeaways

- **Performance**: Proper partitioning, broadcast joins, and adaptive query execution are crucial
- **Data Quality**: Implement comprehensive error handling and data validation
- **Monitoring**: Log metrics and create dashboards for pipeline health
- **Testing**: Unit tests and automated validation ensure pipeline reliability
- **Code Organization**: Modular design improves maintainability and reusability
- **Delta Lake**: Leverage time travel and merge capabilities for data management
- **Governance**: Unity Catalog and Purview provide comprehensive data governance
- **Collaboration**: Effective offshore team management and stakeholder communication
