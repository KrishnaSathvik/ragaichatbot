---
tags: [interview, examples, scenarios, responses]
---

# Interview Response Examples

## Example 1: Partitioning Strategy
**Q: How do you pick partitioning for a 200M-row Delta table used by state and product queries?**

I start from access patterns and row distribution. For mixed state/product queries, I usually partition by `txn_date` (ingest/write efficiency + pruning) and use **Z-ORDER on state, product_id** for read locality. If state is very uneven, I avoid partitioning by it to prevent small/huge-file imbalance; I rely on **Z-ORDER + AQE** and sometimes **salting** if a few states dominate joins. On the write path I **OPTIMIZE** weekly to compact files and keep pruning effective. I validate with Spark UI (shuffle read, tasks skew) and query explain to confirm pruning stats.

## Example 2: Nested JSON Processing
**Q: You get nested JSON from an API; how do you land it in Silver?**

I infer or define a **StructType**, then normalize with `from_json`/`explode` into a flat schema we control. I keep raw JSON in Bronze for replay, and in Silver I enforce types, handle null defaults, and dedupe on `(business_key, event_ts)`. For evolution, I allow **additive** fields only and route breaking changes to a quarantine stream. Finally, I write Delta with merge-on keys and track schema drift in a small audit table.

## Example 3: ADF Orchestration
**Q: Orchestrating ADF → Databricks for incremental upserts—what's the flow?**

ADF pipeline passes a **watermark** (last modified) to a parameterized notebook. The notebook reads only changed rows, applies business rules, then runs a **Delta MERGE** keyed by the business ID plus `effective_ts`. I checkpoint the watermark in a control table, and failures roll back by not advancing it. I add a light set of row-count, duplicate, and null checks and publish metrics to a monitor table that feeds a Power BI ops dashboard.

## Example 4: Performance Troubleshooting
**Q: A long-running job regressed from 35 to 90 minutes—what's your first move?**

I open the **Spark UI** and compare stage DAGs between good vs bad runs to locate the new hot stage. If it's a join, I check skew (shuffle read variance) and either **broadcast** the small side, **repartition** by the join key, or **salt** the heavy key. If it's file I/O, I check small-file counts and run **OPTIMIZE**/`ZORDER`; if input grew, I bump `spark.sql.shuffle.partitions` or enable **AQE**. I also diff config and datasource versions and add a regression alert on duration.

## Example 5: Schema Evolution
**Q: How do you handle schema changes in production pipelines?**

I use a two-layer approach: Bronze accepts schema drift with permissive mode, Silver enforces strict schema. When new columns arrive, I validate them in dev first, then add with defaults in Silver after business approval. For Delta tables, I use `mergeSchema` in controlled deployments, never blindly. I also log schema changes to an audit table and update documentation. This keeps pipelines flexible but prevents downstream breakages.

## Example 6: Data Quality Framework
**Q: How do you implement data quality checks across your pipeline?**

I built a reusable PySpark validation framework that runs checks like row counts, null ratios, duplicates, and business rules. Results go into a monitoring Delta table, and violations trigger ADF alerts. I surface this in Power BI dashboards so business can see data health in real-time. For critical tables, I also do referential integrity checks and flag orphaned records in a quarantine table for manual review.

## Example 7: Cost Optimization
**Q: How do you optimize Databricks costs while maintaining performance?**

I use job clusters with auto-termination instead of always-on, right-size based on workload patterns, and enable auto-scaling. I compact small files weekly with `OPTIMIZE` and use ZORDER for query performance. For non-critical jobs, I use spot instances. I also monitor cluster utilization and tune executor memory to avoid over-provisioning. These changes typically cut costs by 25-30% while maintaining SLA performance.

## Example 8: Multi-Source Integration
**Q: How do you integrate data from different source systems with inconsistent schemas?**

I standardize schemas in the Silver layer using conformance rules. I map different source column names to standard names, handle data type differences with explicit casting, and apply business rules for missing or invalid values. I build unified dimensions in Gold that combine data from multiple sources. For example, I created a single store dimension that maps different store codes from pharmacy and sales systems to a standard format.
