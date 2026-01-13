---
persona: plsql
title: Oracle DBA Lightning Round
topic: tuning
tags: [dba, awr, ash, waits, performance, tuning, transactions, optimizer]
---

# Oracle DBA Lightning Round

Interview-ready answers for DBA-heavy questions. Scoped to PL/SQL developer perspective — credible without overclaiming.

## AWR vs ASH

Sure. ASH samples active sessions during a window—useful for seeing what sessions were waiting on when the slowdown happened. AWR gives the historical snapshot view—great for trending and finding top SQL over time. In practice, I use AWR to understand long-term patterns and ASH to zoom into a specific incident.

Gotcha: AWR licensing depends on setup—not always available in all environments.

## What Wait Events Do You Look At First

Sure. I start with the dominant wait class rather than memorizing events. If it's I/O waits, I check access paths and indexing. If it's lock waits, I look for blocking sessions and transaction scope. If it's CPU, I look for inefficient SQL, bad join order, or excessive parsing.

Tradeoff: You need context—window and workload—to interpret waits correctly.

## How Do You Tune a Slow SQL

Sure. My approach is: confirm SQL and binds, check the plan and row estimates, then fix root cause—predicates, indexing, stats. If the plan flips across bind values, I look at skew and whether histograms or a different query shape is needed.

I identify the expensive step—full scan, bad join method, sort/hash spill—and validate whether the estimates match reality. From there it's about making predicates sargable, reducing rows early, and ensuring stats are current. That's the pattern I stick to.

## Why Would an Index Not Be Used

Sure. Common reasons are query shape and selectivity. If the predicate isn't sargable—like applying TRUNC or UPPER on the indexed column, implicit datatype conversions, or leading-wildcard LIKE—Oracle can't use the index effectively. Also, if the filter returns a large portion of rows, a full scan can be cheaper. Stale stats can also mislead the optimizer. I validate this by checking the plan and fixing the predicate and stats first before changing indexes.

Gotcha: Implicit datatype conversions can silently bypass indexes—easy to miss in code review.

## Bind Variables Good or Bad

Sure. Usually good—they reduce hard parsing and improve plan reuse. The tradeoff is data skew: one bind value may return very few rows and another returns millions, so a single plan might not fit all. That's where histograms or a different query shape helps.

## Statistics and Why They Matter

Sure. Optimizer stats describe table size, column distribution, and index selectivity. If stats are stale or missing, cardinality estimates can be wrong, leading to poor join order and access paths. So stats health is a basic check whenever performance suddenly shifts.

## Cardinality Estimation

Sure. It's Oracle's estimate of how many rows each step returns. If it's off, Oracle can pick the wrong join method or join order. When I see a bad plan, I check where estimates diverge from reality and fix the cause—usually predicates, stats, or skew.

## Nested Loop vs Hash Join

Sure. Nested loops works well when the driving set is small and there's a good index on the join column. Hash join is often better for larger sets where scans are expected. I don't force it blindly—I validate via the plan and row counts.

## Explain Plan vs Actual Runtime

Sure. Explain plan is the optimizer's chosen path and estimates. Runtime depends on real data, bind values, caching, and concurrency. So I use the plan as a guide, then confirm with actual row behavior and where time is spent.

## Plan Instability

Sure. I first confirm it's the same SQL text and binds. Then I check for stats changes, data skew, or environment differences. If needed, I stabilize the SQL with better predicates and indexing. Using hints or plan baselines is usually a last resort and needs DBA alignment.

## Hard Parse vs Soft Parse

Sure. A hard parse happens when Oracle can't reuse an existing cursor, so it has to fully parse, validate, and optimize the SQL to generate a plan—this is expensive under concurrency. A soft parse happens when Oracle finds a matching cursor and can reuse the existing plan with minimal overhead.

Gotcha: Lots of literal variations causing many hard parses is a common issue. Bind variables and consistent SQL text help keep parsing overhead down.

## ORA-01555 Snapshot Too Old

Sure. It means a query needed older undo data for a consistent read, but that undo was overwritten before the query finished—usually because the query ran too long while the system was generating lots of undo. The practical fixes are: tune the query to finish faster, reduce long-running transactions, and work with DBA on undo sizing/retention based on workload. That's the pattern I use.

## Finding Blocking Sessions

Sure. I start by identifying who is waiting and who is blocking—typically via V$SESSION using blocking session fields and then correlating to locks in V$LOCK or DBA_BLOCKERS/DBA_WAITERS depending on access. Then I check what SQL the blocker is running and why the transaction is holding locks so long—often it's an uncommitted transaction or work happening inside the transaction that should be outside. The goal is to shorten transaction scope and remove hot-row contention.

## Commit Inside a Loop

Sure. It depends. It can reduce lock duration and undo pressure, but it breaks atomicity and complicates restartability. In batch processing, I prefer commit per logical batch with clean restart markers, not per row.

Tradeoff: Atomicity vs resource pressure—depends on business requirements.

## What is a Deadlock

Sure. A deadlock is when two sessions each hold a lock the other needs, creating a cycle so neither can proceed. Oracle detects it and rolls back one side to break the cycle. Prevention is mostly design: keep transactions short, access tables/rows in a consistent order across code paths, and avoid patterns where different sessions update the same set of tables in different sequences.

## Bulk Operations Safely

Sure. I use set-based SQL first. If procedural is required, I use BULK COLLECT with LIMIT in a loop and FORALL per chunk. If partial failure is acceptable, I use SAVE EXCEPTIONS and log SQL Percent BULK_EXCEPTIONS.

## Logging Errors in PL/SQL Batches

Sure. Expected errors get handled cleanly with RAISE_APPLICATION_ERROR or controlled returns. Unexpected errors get logged with SQLCODE/SQLERRM and backtrace, then re-raised so monitoring sees the failure. If logs must survive rollback, I use an autonomous logger carefully.

## Latch and Contention

Sure. I don't claim deep memory internals, but when there's contention I look at symptoms: high CPU, parsing spikes, hot blocks, or shared pool pressure. From my side, reducing hard parse, improving SQL shape, and avoiding hot-row patterns usually helps, and DBAs validate the deeper cause.

## When to Use Partitioning

Sure. I use partitioning when tables are large and most queries naturally filter on a partition key—commonly date ranges—so Oracle can prune partitions and scan less data. It also helps maintenance like rolling purges and targeted loads. The tradeoff is added design and operational complexity—partition key choice, local/global indexes, and ensuring queries actually use partition pruning.

## When It Is DBA Territory

Sure. If I'm missing details, I state the assumption I'm making and proceed. And if it's outside PL/SQL scope—like system waits, storage, or RAC specifics—I'll say so and explain how I'd validate it with DBA tooling like AWR/ASH, then coordinate with the DBA team.

## How I Collaborate with DBAs

Sure. From a PL/SQL developer standpoint, I start with what I can control: execution plans, SQL rewrite, indexing opportunities, and stats sanity. If it still looks like a system-level bottleneck, that's where I partner with the DBA and use AWR/ASH to confirm waits and root cause.

## What I Check First as a PL/SQL Dev

Sure. I go in this order: confirm the exact SQL and bind values, check the execution plan and actual row counts if available, identify the expensive step—full scan, bad join method, sort/hash spill—then fix with query rewrite, correct predicates, indexing, and stats. If the plan flips across bind values, I look at skew and histograms.

## Scope Anchor for DBA Questions

Sure. From a PL/SQL developer standpoint, I start with what I can control: execution plans, SQL rewrite, indexing opportunities, and stats sanity. If it still looks like a system-level bottleneck, that's where I partner with the DBA and use AWR/ASH to confirm waits and root cause.

## RAC and Cluster Questions

Sure. I'm not claiming deep RAC internals, but from my side I watch for symptoms—plan changes, global cache waits, or contention patterns. If the indicators point to RAC-specific issues, that's a DBA-led area and I support by simplifying SQL patterns and reducing unnecessary hot blocks.
