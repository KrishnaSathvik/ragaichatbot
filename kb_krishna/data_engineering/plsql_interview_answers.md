---
tags: [krishna, oracle, plsql, interview, concepts]
persona: plsql
---

# Oracle PL/SQL Interview Answers (No Code)

## Guardrails (Mandatory)
- Default to explanation only (no code)
- Only include code when the user explicitly asks ("write", "show", "example", "snippet", "demo")
- Never mention "my recent work", "client", org names, or fake project details
- Never end with "moving forward" / "next steps" / "I plan to"
- Stay Oracle-first; don't pivot to Databricks/PySpark unless asked
- End with practical closure like "That's the pattern I'd stick to in production."

---

## Procedures vs Functions

A procedure performs an action — typically DML operations — and communicates results through OUT parameters. A function returns a single value and can be called from SQL (if it has no side effects). In Oracle PL/SQL environments, procedures handle complex business logic while functions work well for calculations or lookups that need to work inside queries.

---

## BULK COLLECT and FORALL

BULK COLLECT fetches many rows into a collection per round-trip, so you avoid row-by-row fetch overhead. FORALL is the bulk DML counterpart — it applies inserts, updates, or deletes for a set of collection elements without looping one row at a time.

In production, the standard pattern is BULK COLLECT with a LIMIT inside a loop, then run FORALL for that chunk — so you get the speed-up without pulling everything into memory at once. One gotcha is error handling: if you need partial success, use FORALL with SAVE EXCEPTIONS and inspect SQL percent BULK_EXCEPTIONS after. In practice, I use this pattern whenever I'm processing batches larger than a few hundred rows.

---

## Exception Handling in Production Batches

In production batches, separate expected failures from unexpected ones. Expected cases get handled with clear app errors using RAISE_APPLICATION_ERROR. Unexpected ones get logged with SQLCODE/SQLERRM (and DBMS_UTILITY.FORMAT_ERROR_BACKTRACE if available) and then re-raised so monitoring catches the run. For production logging, use an error table with an autonomous transaction procedure so logs survive a rollback — DBMS_OUTPUT is fine for dev/debug but not reliable in production since output depends on client settings. For DML, don't rely on NO_DATA_FOUND — that's SELECT INTO only — so check SQL%ROWCOUNT and treat '0 rows' as a business condition. Biggest gotcha is swallowing errors with WHEN OTHERS; always log then re-raise. That's the pattern to stick to in production.

---

## Packages (Spec vs Body)

The spec is the public contract — procedure and function signatures, public types, constants. The body is the implementation plus private helpers and private state you don't want exposed.

What works well is you can change the body without breaking callers as long as the spec stays stable. The gotcha is spec changes can invalidate dependents, so those changes should be controlled. In practice, I use packages when I want a clean API boundary and reusable helper logic that stays hidden from callers.

---

## Why Use Packages

Packages are used for organization, reuse, and encapsulation. They let you group related functionality under one logical API, and you can expose only what consumers need while keeping helper logic private. That improves maintainability and makes it easier to standardize patterns like validation, logging, and error handling.

They also help with dependency management: teams can evolve implementations in the body without impacting callers, as long as the spec stays stable. And in real systems, packages can improve runtime efficiency because the code is compiled and commonly reused rather than duplicated across many standalone procedures. The main caution is: if you change the package spec, dependent objects can become invalid, so changes should be controlled and released carefully.

---

## REF CURSOR

A REF CURSOR is a pointer to a result set that can be passed to a caller. Used when a procedure needs to return query results without knowing the exact structure at compile time. The caller opens, fetches, and closes it. In Oracle PL/SQL environments, REF CURSOR is preferred over collections when the result set is large or when the caller needs to stream rows rather than load everything into memory.

---

## DBMS_XPLAN.DISPLAY_CURSOR

DISPLAY_CURSOR is for the actual plan of a statement Oracle already executed, identified by SQL_ID (and child). The practical win is using the format ALLSTATS LAST that shows real row counts, because that's how you catch estimate vs reality problems — bad join order, wrong cardinality, unexpected full scans. The only gotcha is making sure you're looking at the right child cursor when the SQL is executed multiple times. For the last statement in your session, pass NULL for SQL_ID. For historical AWR plans, use DISPLAY_AWR instead.

---

## Function on Indexed Column (TRUNC example)

TRUNC on the column forces Oracle to apply a function per row, so the normal index on that date column usually can't be used effectively — it becomes a full table scan. The clean rewrite is a range predicate: start of day inclusive, next day exclusive (date_col >= :d AND date_col < :d + 1). If you absolutely must keep TRUNC, then it becomes a function-based index conversation — but I prefer the range rewrite first. That's what I'd recommend in production.

---

## Row-by-Row Performance Problem

If a PL/SQL job is slow due to row-by-row updates, refactor to bulk operations. Replace cursor loops with BULK COLLECT + FORALL. Use LIMIT to batch memory. Commit per batch (e.g., every 1000 rows) rather than per row — per-row commits kill redo/undo performance. Check the execution plan to make sure indexes are being used. That's the standard refactor pattern.

---

## Triggers — When to Use and Avoid

Avoid triggers for complex business logic, cross-table validation, or anything that should be explicit in application code. Triggers are acceptable for audit logging, auto-populating columns (like created_date), or enforcing simple constraints. For bulk operations, use compound triggers (12c+) to avoid performance issues and the mutating table error. That's the pattern I'd follow.

---

## Cursors (Implicit vs Explicit)

Implicit cursors are created automatically for single-row SELECT INTO and DML. Access via SQL percent ROWCOUNT, SQL percent FOUND, SQL percent NOTFOUND. Explicit cursors give you control: you OPEN, FETCH, and CLOSE. Use explicit cursors when you need to process row by row or pass the cursor between procedures. Cursor FOR loops are the cleanest syntax for simple iteration.

---

## Percent TYPE and Percent ROWTYPE

Percent TYPE binds a variable to a column's data type — safer than hardcoding VARCHAR2(100) because it adapts if the column changes. Percent ROWTYPE represents an entire row from a table or cursor. Both reduce maintenance and prevent type mismatches.

---

## Dynamic SQL (EXECUTE IMMEDIATE)

Use EXECUTE IMMEDIATE for DDL, dynamic table names, or building queries at runtime. Always use bind variables (USING clause) to avoid SQL injection and improve plan reuse. For static SQL, regular SQL is faster and safer. Common pattern: build the SQL string, then EXECUTE IMMEDIATE with bind placeholders (:1, :2).

---

## Mutating Table Error

A mutating table error (ORA-04091) happens when a row-level trigger tries to query or modify the same table that fired it. Oracle blocks this because the table is in a transitional state.

The clean fix is compound triggers — collect data during AFTER EACH ROW and process it in AFTER STATEMENT when the table is stable. Legacy workaround was package variables to cache row data, but compound triggers are cleaner. Statement-level triggers don't have this problem because they fire once after all rows are processed. In practice, I reach for compound triggers only when I genuinely need cross-row logic; otherwise I try to handle it in application code.

---

## Strong vs Weak REF CURSOR

A strong REF CURSOR has a RETURN type — the compiler checks at compile time that you're fetching the right structure. A weak REF CURSOR (or SYS_REFCURSOR, which is the predefined weak type) has no return type — you can open it for any query, but type mismatches are caught at runtime. Use strong when the structure is fixed and you want compile-time safety. Use weak (SYS_REFCURSOR) when returning different result sets from the same procedure or when the query structure varies.

---

## Pipelined Table Functions

Pipelined functions return rows as they're produced using PIPE ROW, instead of building the whole collection first. The caller can start consuming rows immediately. Good for transforming large datasets, ETL-style row generation, or streaming results without memory overhead. The function returns a collection type, is marked PIPELINED, and uses PIPE ROW for each output row. Caller uses TABLE() in the FROM clause.

---

## Collections (VARRAY vs Nested Table vs Associative Array)

Associative arrays are index-by tables (key-value) — sparse, in-memory only, keys can be strings or integers. Nested tables can be stored in database columns, start dense but can become sparse, unbounded size. VARRAYs have a fixed max size, always dense, stored inline with the row. Use associative arrays for in-memory lookups, nested tables when you need SQL operations or database storage, VARRAYs for small fixed-size lists that stay with the row.

---

## Window (Analytic) Functions

ROW_NUMBER assigns unique sequential numbers within a partition. RANK gives the same rank to ties but skips the next number. DENSE_RANK gives ties the same rank without gaps. LAG/LEAD access previous/next rows without self-joins. SUM/AVG OVER creates running totals. These run after WHERE but before ORDER BY, so you can filter on them in a subquery. Common use: de-duplicating rows with ROW_NUMBER OVER (PARTITION BY key ORDER BY date DESC) and keeping rn = 1.

---

## Table Partitioning

Range partitioning splits by value ranges — common for dates. List partitioning splits by specific values — good for region codes. Hash partitioning distributes by hash function — balances load when no natural range/list exists. Composite combines two methods (e.g., range-hash). Partitioning improves query performance through partition pruning, makes maintenance easier (drop old partitions), and enables parallel DML. Local indexes align with partitions; global indexes span all partitions.

---

## DBMS_PROFILER

DBMS_PROFILER profiles PL/SQL execution line by line. Start with DBMS_PROFILER.START_PROFILER, run your code, then STOP_PROFILER. Results go into profiler tables (PLSQL_PROFILER_DATA, etc.). Query those tables to see which lines took the most time. Useful for finding hot spots in complex procedures. Alternative: DBMS_HPROF for hierarchical profiling with call stacks. Both require setup (create profiler tables first).

---

## PLS_INTEGER vs NUMBER Performance

PLS_INTEGER uses machine arithmetic — faster for integer operations (loops, counters). NUMBER is arbitrary precision and slower. For loop indices and counting, prefer PLS_INTEGER. SIMPLE_INTEGER (11g+) is even faster because it doesn't check for null or overflow. One gotcha: PLS_INTEGER wraps silently on overflow if you're not careful, so only use it where values stay in range.

---

## Bind Variables and Parse Overhead

Without bind variables, every distinct literal creates a new SQL statement requiring a hard parse — library cache thrash. With bind variables (:1, :2 or USING clause), Oracle reuses the same cursor and execution plan — soft parse only. This is critical for OLTP. In PL/SQL, static SQL automatically uses binds for variables. In dynamic SQL, always use the USING clause. Concatenating values directly into SQL strings is both slow and a SQL injection risk.

---

## INSTEAD OF Triggers

You can't DML directly into a complex view (joins, aggregates, DISTINCT). INSTEAD OF triggers let you define what INSERT/UPDATE/DELETE on that view actually does — typically splitting into base table operations. Common for application layers that want to treat a view as a table. One per DML type per view.

---

## Object Dependencies

When you change a table or package spec, dependent objects (procedures, views, triggers) go INVALID. Oracle usually recompiles them automatically on next use (automatic recompilation). For production, compile explicitly after DDL changes (ALTER ... COMPILE). Check DBA_DEPENDENCIES to see what depends on what. Cascading invalidation can cause runtime errors if recompilation fails.

---

## Optimizer Basics (Stats, Bind Peeking, Cardinality)

The Oracle optimizer relies on statistics to make good decisions — table stats, column stats, histograms. If stats are stale or missing, you get bad plans. Bind peeking means Oracle looks at the first bind value to pick a plan, which can backfire if data is skewed — one value might want an index, another wants a full scan. Adaptive cursor sharing helps but isn't perfect.

Cardinality mismatch is the root of most bad plans: Oracle estimates 100 rows, gets 1 million, and the join order or access path is wrong. DBMS_XPLAN with ALLSTATS LAST shows actual vs estimated rows — that's where you catch it. The fix is usually better stats, histograms on skewed columns, or sometimes SQL hints as a last resort.

---

## Transactions (Commit/Rollback Placement)

Commit placement matters for both performance and correctness. Committing per row kills performance — redo log sync on every commit. Committing per batch (every 1000 or 10000 rows) is the standard pattern for bulk operations. But be careful: if you commit mid-batch and then fail, you have partial data and need to handle restart logic.

Autonomous transactions are useful for logging — you want the error log entry to survive even if the main transaction rolls back. But don't overuse them; they're a separate transaction context, so they can't see uncommitted changes from the parent. The gotcha is that autonomous transaction errors don't automatically roll back the parent.

---

## DBMS_SCHEDULER Basics

DBMS_SCHEDULER is Oracle's built-in job scheduler — better than OS cron because it's database-aware (handles RAC, tracks job history, supports dependencies). Basic pattern: create a program (what to run), create a schedule (when to run), create a job (links them together).

For batch PL/SQL jobs, you typically call a stored procedure. The scheduler logs runs in DBA_SCHEDULER_JOB_RUN_DETAILS — useful for monitoring and debugging. One thing to watch: if a job fails, you need explicit logging in your procedure because scheduler logs might not capture detailed errors. Also, scheduler jobs run as the job owner, so permissions matter.

---

## PL/SQL Developer Introduction

My background is strong in SQL, especially in data engineering use cases where I build ETL-style workflows and handle complex transformations. On the Oracle PL/SQL side, I've written stored procedures and functions to keep business logic close to the data, and I structure code in a way that's readable and easy to support.

When working with larger volumes, I focus on performance — so I prefer set-based SQL first, and when procedural work is needed, I use bulk processing patterns like BULK COLLECT and FORALL appropriately to avoid row-by-row bottlenecks. I also take error handling seriously — clear exception handling, logging, and safe failure behavior — so production support is smoother.

For tuning, I use explain plans and runtime signals to find what's actually slow — join order, missing indexes, full scans, or filtering issues — and then I optimize with query rewrite, indexing strategy, and clean access patterns. Overall, my goal is always the same: deliver database logic that's correct, performant, and maintainable.

---

## My Background (Honest Framing)

My recent work has been data engineering heavy — building large-scale ETL pipelines, data transformations, and analytics. I have strong SQL experience across multiple database platforms. For Oracle PL/SQL, I'm comfortable with stored procedures, functions, packages, bulk processing with BULK COLLECT and FORALL, exception handling frameworks, and performance tuning using explain plans. In Oracle PL/SQL environments, I follow standard patterns for bulk operations, exception handling, and performance optimization.
