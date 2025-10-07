---
tags: [data-eng, informatica, migration, pyspark, mapping, transformations, snowflake]
---

# Informatica → PySpark Migration Playbook

## Overall Approach
1) **Inventory & lineage**: export mapping XML / repository report; list source/target tables, lookups, joins, aggregations, filters, expressions, sequences.
2) **Semantics parity**: for each mapping, capture row-order assumptions, null-handling, case-sensitivity, timezone, numeric precision/scale, surrogate keys.
3) **Transform translation**: map each Informatica transformation → PySpark function (see table).
4) **Framework**: build a small PySpark "operator" layer so pipelines are declarative (config-driven).
5) **Testing**: golden-data tests (row/column counts, nulls, min/max, checksums), sample-based parity, KPI comparisons.
6) **Orchestration**: ADF or Databricks Workflows; parameterize envs; promote via DevOps CI/CD.
7) **Performance**: partitioning, broadcast/AQE, file compaction; pushdown where possible.
8) **Snowflake load**: choose **Spark → Snowflake connector** (batch) or **stage + COPY** (Snowpipe/auto-ingest) for high-throughput and decoupling.

## Common Transformation Mapping
- **Source Qualifier** → `spark.read` with predicates; pushdown via JDBC filter if possible.
- **Expression** (IIF/DECODE/SUBSTR/UPPER) → `when/otherwise`, `expr()`, `substring`, `upper`, `coalesce`.
- **Filter** → `df.filter("...")`.
- **Lookup** → left join with a broadcast-hint; handle not-found as default/null + `when` logic.
- **Joiner** → `df.join(other, keys, "inner/left/right/full")`; use `broadcast()` for small tables.
- **Aggregator** → `groupBy(...).agg(...)` with careful null-handling and data types.
- **Router** → multiple filters writing to multiple sinks.
- **Sequence Generator** → window functions with `row_number()` or Snowflake sequences on write.
- **Union** → `unionByName` with `allowMissingColumns=True`.
- **Sorter/Rank** → `orderBy`, window specs with `row_number`, `dense_rank`.

## Null & Datatype Rules
- Match Informatica's null rules explicitly; use `coalesce`, cast to target schema, standardize timestamp TZ and string trimming.

## Incremental Patterns
- Watermark on `last_update_ts`; Bronze → Silver Delta with `MERGE INTO`; or CDC using file-based change tables.
- For Snowflake targets, prefer **idempotent upserts** using stage + `COPY INTO` to temp table + `MERGE`.

## Migration Strategy
Start with simple mappings (single source, basic transformations), validate parity, then tackle complex joins and aggregations. Use a staging approach where you run both systems in parallel for validation before switching over.
