---
tags: [tejuu, experience, cvs-health, pharmacy-analytics, product-data-analyst, pyspark, databricks, azure]
persona: analytics
---

# Pharmacy Analytics Platform - CVS Health

## Project Overview

**Duration:** May 2020 – Jan 2022  
**Role:** Product Data Analyst  
**Company:** CVS Health  
**Project:** Pharmacy Analytics & Inventory Management Platform

## Technical Challenge

CVS Health had fragmented pharmacy and inventory reporting systems across 9,000+ stores nationwide. Each store was using different Access databases and Excel files to track inventory, prescriptions, and customer data. The challenge was creating a unified analytics platform that could process 10M+ pharmacy records daily while providing real-time insights for inventory management, prescription tracking, and customer analytics.

## My Role & Responsibilities

As the Product Data Analyst, I was responsible for:
- Migrating pharmacy and inventory reporting from Access and Excel into Azure SQL
- Building Power BI pipelines for real-time analytics
- Developing Python and SQL reconciliation scripts for data validation
- Processing large-scale pharmacy data using PySpark in Databricks
- Creating automated data profiling and quality validation frameworks

## Key Technical Achievements

### Data Migration & Modernization
I led the migration of pharmacy data from 9,000+ Access databases and Excel files into a unified Azure SQL data warehouse. The challenge was handling different data formats, inconsistent schemas, and ensuring data quality across all stores. I built automated ETL pipelines using Azure Data Factory that could process different file formats and validate data integrity.

**What I accomplished:**
- Migrated 10M+ pharmacy records from legacy systems
- Reduced data processing time from 8 hours to 2 hours daily
- Achieved 99.8% data accuracy through automated validation
- Enabled real-time inventory tracking across all stores

### PySpark Data Processing
I implemented PySpark in Databricks for processing large-scale pharmacy data and building data quality validation frameworks. I developed automated data profiling scripts using PySpark DataFrames and implemented incremental data processing patterns for real-time inventory tracking.

**Key technical implementations:**
- Built PySpark pipelines processing 10M+ records daily
- Implemented data quality validation using DataFrame operations
- Created automated reconciliation scripts for inventory tracking
- Developed real-time data processing patterns for prescription analytics

### Power BI Analytics Platform
I designed and built interactive Power BI dashboards that provided real-time insights into pharmacy operations, inventory levels, and customer analytics. The dashboards were used by store managers, regional directors, and corporate teams for decision-making.

**Business impact:**
- Reduced manual reporting time by 40% across all stores
- Enabled self-service analytics for 2,000+ users
- Improved inventory accuracy by 25%
- Reduced stockouts by 30%

## Technical Architecture

### Data Pipeline Design
```
Legacy Systems (Access/Excel) → Azure Data Factory → Azure SQL → Power BI
                                    ↓
                              Databricks (PySpark)
```

### Key Technologies Used
- **Azure Services**: Azure SQL, Data Factory, Databricks
- **Data Processing**: PySpark, Python, SQL
- **Analytics**: Power BI, DAX, Power Query
- **Data Quality**: Automated validation, reconciliation scripts

## Business Impact

### Quantifiable Results
- **Data Volume**: Successfully processed 10M+ pharmacy records daily
- **Performance**: Reduced data processing time by 75% (8 hours → 2 hours)
- **Data Quality**: Achieved 99.8% data accuracy through automated validation
- **User Adoption**: Enabled 2,000+ users with self-service analytics
- **Business Metrics**: Improved inventory accuracy by 25%, reduced stockouts by 30%

### Stakeholder Benefits
- **Store Managers**: Real-time inventory visibility and prescription tracking
- **Regional Directors**: Consolidated reporting across multiple stores
- **Corporate Teams**: Data-driven insights for strategic decision making
- **IT Teams**: Reduced manual data processing and improved system reliability

## Technical Skills Demonstrated

- **PySpark**: Advanced DataFrame operations, data processing, validation
- **Azure**: SQL Database, Data Factory, Databricks
- **Power BI**: Interactive dashboards, DAX, data modeling
- **SQL**: Complex queries, data transformation, optimization
- **Python**: Data processing, automation, validation scripts
- **Data Architecture**: ETL/ELT pipelines, data warehousing, real-time processing
- **Data Quality**: Validation frameworks, reconciliation, monitoring
