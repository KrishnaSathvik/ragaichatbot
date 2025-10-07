---
tags: [data-eng, examples, mapping, pyspark, snowflake]
---

# Informatica Migration Examples

## Example: Expression + Filter + Lookup → PySpark

```python
from pyspark.sql import functions as F
from pyspark.sql.window import Window

src = (spark.read.format("jdbc")
  .option("url", jdbc_url)
  .option("dbtable", "SRC_ORDERS")
  .load())

lkp = (spark.read.format("jdbc")
  .option("url", jdbc_url)
  .option("dbtable", "DIM_PRODUCT")
  .load())

# Expression (IIF) & standardization
cur = (src
  .withColumn("TRIM_SKU", F.trim("SKU"))
  .withColumn("ORDER_DT", F.to_timestamp("ORDER_TS"))
  .withColumn("IS_PRIORITY",
              F.when(F.col("PRIORITY_FLAG") == "Y", F.lit(1)).otherwise(F.lit(0)))
  .filter("STATUS = 'COMPLETE'"))

# Lookup (broadcast) + join
cur = (cur.join(F.broadcast(lkp.select("SKU","PRODUCT_ID")), on="SKU", how="left")
          .fillna({"PRODUCT_ID": -1}))

# Surrogate key (sequence-like)
w = Window.orderBy(F.monotonically_increasing_id())
cur = cur.withColumn("LINE_ID", F.row_number().over(w))

# Final projection
out_df = cur.select("LINE_ID", "ORDER_ID", "PRODUCT_ID", "ORDER_DT", "IS_PRIORITY")
```

## Example: Write to Snowflake via Connector

```python
sfOptions = {
  "sfURL": SF_URL,
  "sfUser": SF_USER,
  "sfPassword": SF_PWD,     # or OAuth
  "sfDatabase": "SALES",
  "sfSchema": "CURATED",
  "sfWarehouse": "WH_XL",
  "sfRole": "SYSADMIN"
}
(out_df
  .write.format("snowflake")
  .options(**sfOptions)
  .option("dbtable", "ORDERS_STAGE")
  .mode("append")
  .save())
```

## Example: Stage + COPY Pattern

* Write partitioned Parquet to ADLS/S3 (e.g., by `order_dt`).
* Call Snowflake:

  ```sql
  COPY INTO SALES.CURATED.ORDERS
  FROM @ext_stage/orders/
  FILE_FORMAT=(TYPE=PARQUET)
  MATCH_BY_COLUMN_NAME=CASE_INSENSITIVE
  ON_ERROR=ABORT_STATEMENT;
  ```
* Wrap in task/pipe for automation.

## Example: Aggregator → PySpark

```python
# Informatica Aggregator becomes:
agg_df = (src_df
  .groupBy("STORE_ID", "PRODUCT_CATEGORY")
  .agg(
    F.sum("SALES_AMOUNT").alias("TOTAL_SALES"),
    F.count("*").alias("TRANSACTION_COUNT"),
    F.avg("UNIT_PRICE").alias("AVG_PRICE"),
    F.max("SALE_DATE").alias("LAST_SALE")
  )
  .filter("TOTAL_SALES > 1000"))  # Having clause
```

## Example: Router → Multiple Outputs

```python
# Router with multiple conditions
high_value = df.filter("SALES_AMOUNT > 10000")
medium_value = df.filter("SALES_AMOUNT BETWEEN 1000 AND 10000")
low_value = df.filter("SALES_AMOUNT < 1000")

# Write to different targets
high_value.write.mode("append").saveAsTable("high_value_sales")
medium_value.write.mode("append").saveAsTable("medium_value_sales")
low_value.write.mode("append").saveAsTable("low_value_sales")
```

## Example: Sequence Generator → Window Functions

```python
# Informatica sequence becomes:
w = Window.partitionBy("ORDER_ID").orderBy("LINE_NUMBER")
df_with_seq = df.withColumn("SEQUENCE_ID", F.row_number().over(w))

# Or for Snowflake sequences on write:
df_with_seq = df.withColumn("SEQUENCE_ID", F.expr("NEXTVAL('order_seq')"))
```
