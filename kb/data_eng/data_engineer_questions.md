---
tags: [pyspark, databricks, data-engineering, etl, dataframe, delta-lake, json, schema-drift, optimization, debugging, walgreens, azure-data-factory]
---

# Data Engineering Interview Questions & Answers

## Core PySpark + Databricks Questions

### Q1. What is your experience with PySpark in your current project?
**A:** In my Walgreens project, I built end-to-end PySpark pipelines in Databricks that processed over 10TB monthly. I handled ingestion of raw data into Bronze, applied transformations and schema validation in Silver, and modeled fact/dimension tables in Gold for reporting. I frequently used PySpark DataFrame APIs, window functions, UDFs, and joins. For example, I implemented deduplication logic using `dropDuplicates()` and window functions, ensuring the most recent transaction record is retained.

### Q2. How do you handle large datasets in PySpark efficiently?
**A:** First, I design partitioning strategies at ingestion (date-based partitions). Second, I tune Spark configurations like `spark.sql.shuffle.partitions` and executor memory. Third, I use optimizations such as broadcast joins for small lookup tables and salting for skewed keys. For large jobs, I enable Adaptive Query Execution. In one case, these changes reduced a pipeline runtime from 2+ hours to 40 minutes.

### Q3. How do you debug PySpark jobs when they fail?
**A:** I start with Spark UI to analyze DAGs, stages, and tasks. I check for skew (few tasks taking much longer) or memory errors. Then I check logs in Databricks for stack traces. I usually replay the job with a smaller dataset to isolate the failing transformation. For example, when a job failed due to a corrupt record, I added `_corrupt_record` handling and moved bad rows into a quarantine table.

### Q4. How do you handle nested JSON in PySpark?
**A:** I define a `StructType` schema, use `from_json` to parse the string column, and `explode` for arrays. Then I flatten with `withColumn` to extract nested attributes. For deeply nested JSON, I use recursive functions to normalize. Finally, I store it as a clean Delta table in Silver for downstream consumption.

### Q5. How do you handle duplicates in PySpark?
**A:** For simple duplicates, I use `dropDuplicates()`. For business-specific deduplication, I use window functions with `row_number()` ordered by timestamp, keeping only the latest row. In Walgreens, this was used for handling multiple prescription updates from pharmacy systems.

### Q6. How do you handle schema drift in PySpark pipelines?
**A:** In Bronze, I ingest with permissive mode to avoid job failure. In Silver, I enforce strict schema. If new columns appear, I add them with defaults in Silver after business validation. For Delta tables, I use `mergeSchema` in controlled deployments, never blindly. This allows flexibility but avoids breaking downstream queries.

## Advanced PySpark & Delta Lake Questions

### Q7. How do you design incremental loads in PySpark?
**A:** I use watermarking (modified_date column) or surrogate keys. ADF passes parameters to notebooks for last processed date. In PySpark, I filter only incremental rows and apply Delta merge to update/inserts. This reduced daily runs from processing 10TB full to ~300GB delta, saving cost and runtime.

### Q8. Can you explain time travel in Delta Lake? How have you used it?
**A:** Time travel lets me query data at a specific version or timestamp. At Walgreens, one job overwrote 2 days of data. Using `VERSION AS OF` in Delta, I restored the table to its previous state in minutes without reloading raw files.

### Q9. How do you handle slowly changing dimensions (SCD) in Databricks?
**A:** I used Delta merge for Type 2. Old record is closed with an end date, new record inserted with active flag = 1. This keeps historical changes. For example, when product pricing changed, our dimension table kept both old and new versions for accurate reporting.

### Q10. How do you monitor PySpark jobs?
**A:** I log metadata like job ID, start/end time, row counts, and error counts into monitoring tables. ADF sends failure alerts. Additionally, I surface monitoring dashboards in Power BI so IT and business both see pipeline health.

### Q11. How do you implement joins in PySpark for performance?
**A:** For large-large joins, I repartition on join keys to avoid skew. For small-large joins, I use `broadcast()`. For very skewed joins, I salt keys. I always monitor shuffle size in Spark UI.

### Q12. How do you handle corrupt records in ingestion?
**A:** I use PERMISSIVE mode in PySpark read, which places bad records in `_corrupt_record`. I redirect them into a quarantine Delta table for manual review, while valid data continues processing.

### Q13. How do you test PySpark pipelines?
**A:** Unit tests validate transformations with small sample data. Row count reconciliation checks ingestion completeness. Schema validation checks enforce consistency. We automated these checks in CI/CD pipelines.

### Q14. How do you manage dependencies across notebooks in Databricks?
**A:** I modularize common logic (like validations, schema enforcement) in utility notebooks or .py files stored in repos. Then I import them into main notebooks. This avoids code duplication and keeps pipelines maintainable.

### Q15. How do you handle late arriving data?
**A:** I use watermarking in Delta tables, so late data is still merged if within X days. If outside retention, we load them manually after business approval.

## Performance Optimization & Best Practices

### Q16. How do you handle large joins across multiple datasets?
**A:** First, partition both datasets on the join key. If one is small, broadcast it. If skew occurs, apply salting. If still heavy, break into smaller joins and cache intermediate results.

### Q17. How do you manage PySpark code for reusability?
**A:** I follow modular design: separate ingestion, transformation, validation, and load functions. I store configs in parameter files, not hardcoded. Reusable frameworks allowed offshore to easily plug in new sources with minimal code.

### Q18. How do you optimize PySpark DataFrame transformations?
**A:** Avoid wide transformations until necessary, use select instead of *, cache intermediate results when reused, and avoid UDFs unless unavoidable. Vectorized operations (pandas UDFs) are faster than row-wise ones.

### Q19. How do you manage error handling in PySpark?
**A:** I wrap critical transformations with try/except. Failures are logged into error tables. In ADF, we configure retries and failure alerts. This ensures job doesn't fail silently.

### Q20. What's the biggest challenge you solved with PySpark at Walgreens?
**A:** Optimizing a 10TB sales fact pipeline that originally took 2+ hours. By tuning partitioning, salting skewed joins, and compacting files, I reduced runtime to 40 minutes. This improved SLA compliance and cut costs by 30%.

## Key Takeaways

- **Performance**: Proper partitioning, broadcast joins, and adaptive query execution are crucial
- **Data Quality**: Implement comprehensive error handling and data validation
- **Monitoring**: Log metrics and create dashboards for pipeline health
- **Testing**: Unit tests and automated validation ensure pipeline reliability
- **Code Organization**: Modular design improves maintainability and reusability
- **Delta Lake**: Leverage time travel and merge capabilities for data management
