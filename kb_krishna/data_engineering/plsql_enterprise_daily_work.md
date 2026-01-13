---
tags: [krishna, oracle, plsql, enterprise, daily-work, interview, patterns, ingestion, validation, audit, checkpoint, idempotent]
persona: plsql
---

# Oracle PL/SQL Enterprise Daily Work Patterns

Interview-ready answers for enterprise Oracle environments. Generic enough for healthcare, pharma, finance, or any regulated industry.

---

## Daily Workflow (Day in the Life)

## Morning: Production Monitoring

In the morning, I check overnight batch jobs — did anything fail, are there data load issues, any SLA misses. I review logs (job logs, error tables) and investigate any failures: failed procedures, data mismatches, or performance issues. In regulated environments, timeliness and traceability matter, so monitoring is important.

## Midday: Development & Fixes

During the day, I work on new PL/SQL procedures, enhancements to existing packages, or performance fixes. Typical work includes writing stored procedures, functions, and packages, optimizing slow queries, and adding validation logic. If an upstream system changed its format, I update the parsing logic and test it.

## Afternoon: Testing & Deployments

Afternoon is usually testing and releases. Changes go through DEV → QA → UAT → PROD. I validate row counts, data accuracy, and performance before promoting code. I also attend requirement clarifications, defect triage, and release planning meetings.

---

## Memorized Answer: Tell Me About Your Daily Work

"On a daily basis, I monitor batch jobs, troubleshoot failures, and ensure data pipelines run reliably. I develop and maintain stored procedures and packages to ingest, transform, and validate data from upstream systems. I also spend time tuning SQL queries, handling exceptions, and working with QA and business teams to ensure data accuracy — especially in environments where auditability and traceability are important."

---

## Staging Tables

What works well is loading raw data into staging tables first, then validating before moving to production tables. This isolates bad data from good data and makes debugging easier. Gotcha: staging tables need a cleanup process or they grow indefinitely.

---

## Reject Tables with Reason Codes

I typically capture bad rows with a reject reason code instead of failing the whole load. Validate each row, if it fails a rule, insert into reject table with error reason, continue processing good rows. This lets clean data flow while problems are investigated separately. Tradeoff: you need a clean process to review and reprocess rejects, otherwise they pile up.

---

## Control Tables for Load Tracking

What works well is tracking load metadata in a control table: job name, start time, end time, row counts, status. Useful for monitoring, restartability, and auditing. I typically check this first when investigating failures.

---

## Handling Late or Incomplete Files

I check file existence and completeness before processing. What works well is using control totals (row count in header/trailer vs actual rows) to detect truncated files. Log and alert if files are missing or incomplete. Gotcha: if the trailer is missing, you might not know the file is truncated until reconciliation fails downstream.

---

## Duplicate Handling with ROW_NUMBER

I typically use natural key + ROW_NUMBER() to identify duplicates, or use unique constraints with exception logging. Pattern: rank duplicates by business key, keep the latest, push duplicates to reject table with reason. Tradeoff: deciding which duplicate to keep requires clear business rules.

---

## Control Totals for Validation

Compare row counts, sums, or hash totals between source and target. If they don't match, investigate before marking the load complete. What works well is checking control totals at both staging and final load.

---

## Key-Based Reconciliation

I typically compare keys between source and target to find: missing in target (not loaded), missing in source (orphans), and mismatches (different values for same key). Categorize discrepancies into mismatch buckets for easier investigation.

---

## Memorized Answer: Data Quality

"In production, I validate with control totals and key-based reconciliation, and I push bad rows to a reject table with reason codes so good data can still flow. Mismatches get categorized into buckets — missing in source, missing in target, value differences — so we can investigate efficiently."

---

## Checkpoint Logic for Restartability

I track progress in a control table so if a job fails mid-way, it can restart from the last successful checkpoint instead of reprocessing everything. Gotcha: checkpoint granularity matters — too fine is overhead, too coarse means more reprocessing.

---

## Idempotent Procedures

What works well is designing procedures so running them twice with the same input produces the same result. This usually means using MERGE instead of separate INSERT/UPDATE, or checking if data already exists before processing. Tradeoff: idempotent logic can be more complex to write and test.

---

## Commit Per Batch

I typically commit every N rows (e.g., 1000) instead of per row or at the end. This balances performance (fewer commits) with recoverability (less data to reprocess on failure). Tradeoff: you lose full atomicity, so you need restart logic and clear checkpoints.

---

## Memorized Answer: Handling Failures

"I design batch jobs to be restartable using checkpoints and idempotent logic, so failures don't require full reloads and don't introduce duplicates. I commit per batch rather than per row for performance, and I use control tables to track progress."

---

## Audit Columns

What works well is adding created_by, created_date, updated_by, updated_date to tables. Populate via trigger or procedure. In regulated environments, this is often mandatory.

---

## History Tables

For important changes, I insert the old row into a history table before updating. This preserves what the data looked like before the change. Gotcha: history tables grow fast — need archival or partition strategy.

---

## Soft Deletes

Instead of DELETE, I set a deleted_flag or end_date. This preserves the record for audit purposes while hiding it from normal queries. Tradeoff: all queries need to filter on the flag, which is easy to forget.

---

## SCD-Style Change Tracking

I typically track who changed what and when using effective_from, effective_to dates, plus change_type (insert/update/delete). This allows point-in-time queries. Gotcha: SCD logic adds complexity, so I only use it where auditability is required.

---

## Memorized Answer: Auditability

"In regulated environments, I implement audit columns and history tables to ensure full traceability of data changes. For deletions, I use soft deletes so records are preserved for audit purposes."

---

## Delta Detection

I identify changed records using timestamp columns (updated_date > last_run_date), change data capture (CDC) if available, or hash comparison of key columns. What works well is a reliable modified_date column maintained by triggers.

---

## MERGE for Upsert

I use MERGE to update existing records and insert new ones in a single statement. Cleaner than separate UPDATE + INSERT and avoids race conditions. Gotcha: keep the merge key stable and indexed, otherwise it becomes expensive.

---

## Full Load with Truncate

For small reference tables, sometimes a full load with TRUNCATE + INSERT is simpler than delta logic. Tradeoff: downtime during reload, and you lose history unless you archive first.

---

## Exception Handling: Expected vs Unexpected

I separate expected failures (business rules) from unexpected ones. Expected cases get handled with RAISE_APPLICATION_ERROR. Unexpected failures get logged with SQLCODE/SQLERRM and re-raised so monitoring catches them.

---

## Autonomous Logging

What works well is using an autonomous transaction procedure for error logging so logs survive even if the main transaction rolls back. Gotcha: keep logging lightweight — if logging fails or is slow, it becomes the problem.

---

## SAVE EXCEPTIONS for Bulk DML

When using FORALL, I add SAVE EXCEPTIONS to continue processing after row-level errors. Check SQL%BULK_EXCEPTIONS to see which rows failed. Tradeoff: you need to handle partial success explicitly.

---

## Bulk Processing with LIMIT

I replace row-by-row cursor loops with BULK COLLECT + FORALL. Use LIMIT to batch memory usage (e.g., 1000 rows per fetch). Tradeoff: larger batches are faster but use more PGA memory.

---

## Explain Plan Analysis with ALLSTATS LAST

I use DBMS_XPLAN.DISPLAY_CURSOR with format 'ALLSTATS LAST' to see actual vs estimated row counts. Fix cardinality mismatches first — that's usually the root cause of bad plans.

---

## Sargable Predicates

I avoid functions on indexed columns (like TRUNC(date_col)). What works well is rewriting as range predicates: date_col >= :start AND date_col < :end. This lets Oracle use the index.

---

## Scope Boundary (When It's DBA Territory)

From my side, I start with plan, predicates, indexing, and stats sanity. If it looks like a system-level wait issue, I validate with AWR/ASH with DBA support. I focus on changes that are correct, performant, and maintainable — and I coordinate with DBAs when tuning requires system-level access.

---

## Typical Enterprise Domains (Optional If Asked)

In regulated industries, PL/SQL developers typically work on data ingestion pipelines from upstream systems, transformation logic for reporting, batch job orchestration, data quality and validation frameworks, and audit requirements. These environments emphasize data correctness, auditability, and reliability over speed of feature delivery.
