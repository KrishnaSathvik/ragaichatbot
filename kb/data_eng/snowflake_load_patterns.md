---
tags: [data-eng, snowflake, spark-connector, copy-into, snowpipe, performance]
---

# Snowflake Load Patterns

## A) Spark → Snowflake Connector (Simple)
- Use `net.snowflake:spark-snowflake` + `net.snowflake:snowflake-jdbc`.
- Write mode: `append` to a staging table; finalize with Snowflake-side `MERGE`.
- Good for medium volumes; keeps pipeline in one place (Databricks).

**Example write:**
- options: `sfURL`, `sfUser`, `sfPassword`/`sfOAuth`, `sfDatabase`, `sfSchema`, `sfWarehouse`, `sfRole`.
- `df.write.format("snowflake").options(**sfOptions).option("dbtable","STAGE_TABLE").mode("append").save()`

## B) External Stage + COPY INTO (High-throughput / Decoupled)
1) Spark writes Parquet to cloud storage (ADLS/S3) with partitioning.
2) Snowflake `COPY INTO <table>` from the external stage with file pattern.
3) Automate with **Snowpipe** or orchestration tool; track file manifests / checkpoints.

**Pros:** better parallelism, resilient to retries, clear separation of compute concerns.
**Cons:** more moving parts (stages, pipes, notifications).

## Performance & Cost Tips
- Use `COPY INTO` with `ON_ERROR='CONTINUE'` to isolate bad files; quarantine & reprocess.
- Cluster keys only where pruning helps. Avoid over-clustering.
- Compress & partition data output; align Snowflake micro-partitions with query patterns.
- Prefer `MERGE` with small change sets; if very large upsert, consider swap: load to temp + swap/rename.

## Load Patterns by Use Case
- **Batch loads**: Spark connector for simplicity, stage+COPY for high volume
- **Real-time**: Snowpipe with auto-ingest from cloud storage
- **Upserts**: Stage temp table + MERGE for idempotency
- **Historical reloads**: Direct COPY INTO with file pattern matching

## Monitoring & Validation
- Track file ingestion status via Snowflake metadata views
- Monitor COPY performance and error rates
- Validate row counts and data quality post-load
- Set up alerts for failed loads or SLA breaches
