---
tags: [tejuu, experience, stryker, data-migration, analytics-engineer, pyspark, databricks, azure]
persona: analytics
---

# Enterprise Data Migration Project - Stryker

## Project Overview

**Duration:** Jan 2022 – Dec 2024  
**Role:** Data Engineer  
**Company:** Stryker  
**Project:** Enterprise Data Migration from Legacy Systems to Azure

## Technical Challenge

Stryker had a complex data landscape with multiple legacy systems (Oracle, SQL Server, Excel) that were creating data silos and making it difficult to get a unified view of business operations. The challenge was migrating 15M+ transactions monthly from these disparate systems into a modern Azure-based data platform while ensuring data quality, performance, and business continuity.

## My Role & Responsibilities

As the Data Engineer, I was responsible for:
- Designing the overall data architecture and migration strategy
- Building ETL/ELT pipelines using PySpark and Databricks
- Implementing data quality frameworks and validation processes
- Optimizing performance and reducing costs
- Ensuring data governance and security compliance
- Mentoring offshore developers and establishing best practices

## Key Technical Achievements

### Data Architecture Design
I designed a comprehensive medallion architecture (Bronze → Silver → Gold) using Azure Synapse and Databricks:
- **Bronze Layer**: Raw data ingestion from source systems
- **Silver Layer**: Data cleansing, validation, and business rule application
- **Gold Layer**: Aggregated, business-ready datasets for analytics

### PySpark Pipeline Development
I built sophisticated data processing pipelines using PySpark:
- **Data Ingestion**: Automated ingestion from Oracle, SQL Server, and file systems
- **Data Transformation**: Complex business logic implementation using DataFrame operations
- **Data Quality**: Automated validation checks and exception handling
- **Performance Optimization**: Implemented partitioning, caching, and query optimization

### Databricks Implementation
I implemented Databricks as our primary data processing platform:
- **Job Clusters**: Automated job scheduling and resource management
- **Delta Lake**: ACID transactions and time travel capabilities
- **Unity Catalog**: Data governance and lineage tracking
- **Notebooks**: Collaborative development and documentation

### Data Quality Framework
I established comprehensive data quality processes:
- **Validation Rules**: Automated checks for data completeness, accuracy, and consistency
- **Monitoring**: Real-time alerts for data quality issues
- **Reconciliation**: Automated reconciliation between source and target systems
- **Audit Trail**: Complete lineage tracking for all data transformations

## Technical Impact

- **Data Volume**: Successfully migrated 15M+ transactions monthly
- **Performance**: Reduced pipeline runtime from 8 hours to 2 hours (75% improvement)
- **Cost Optimization**: Achieved 35% cost reduction through efficient resource utilization
- **Data Quality**: Achieved 99.9% data accuracy through automated validation
- **Scalability**: Built platform that can handle 10x current data volume
- **User Support**: Enabled 1,000+ users with self-service analytics capabilities

## Technical Implementation Details

**Azure Services Used:**
- **Azure Synapse**: Data warehousing and analytics
- **Azure Data Factory**: Orchestration and scheduling
- **Azure Databricks**: Data processing and analytics
- **Azure SQL**: Relational data storage
- **Azure Storage**: Data lake storage

**PySpark Optimizations:**
- **Partitioning**: Implemented date and region-based partitioning
- **Caching**: Strategic caching of frequently accessed datasets
- **Broadcast Joins**: Optimized join operations for better performance
- **Window Functions**: Efficient analytical calculations
- **UDFs**: Custom functions for complex business logic

**Data Quality Measures:**
- **Schema Validation**: Automated schema evolution and validation
- **Deduplication**: Advanced deduplication algorithms
- **Data Profiling**: Automated data profiling and anomaly detection
- **Reconciliation**: Automated reconciliation processes

## Challenges & Solutions

**Challenge**: Complex data transformations across different source systems
**Solution**: Created a flexible transformation framework that could handle various data formats and business rules

**Challenge**: Ensuring data quality during migration
**Solution**: Implemented comprehensive validation framework with automated testing and monitoring

**Challenge**: Performance optimization for large-scale data processing
**Solution**: Used advanced PySpark techniques including partitioning, caching, and query optimization

**Challenge**: Managing offshore development team
**Solution**: Established clear coding standards, documentation requirements, and code review processes

## Lessons Learned

This project taught me the importance of building scalable, maintainable data architectures. The key to success was spending time upfront on architecture design and establishing strong data quality processes.

Working with offshore teams required clear communication, comprehensive documentation, and robust testing processes to ensure code quality and consistency.

## Technical Skills Developed

- **PySpark**: Advanced DataFrame operations, window functions, UDFs
- **Databricks**: Job clusters, Delta Lake, Unity Catalog
- **Azure**: Synapse, Data Factory, Storage, SQL Database
- **Data Architecture**: Medallion architecture, data modeling, ETL/ELT patterns
- **Performance Optimization**: Partitioning, caching, query optimization
- **Data Quality**: Validation frameworks, monitoring, reconciliation
- **DevOps**: CI/CD pipelines, automated testing, deployment automation
