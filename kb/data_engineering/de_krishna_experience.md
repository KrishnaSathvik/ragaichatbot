---
tags: [data-engineer, krishna, experience, walgreens, azure, databricks, resume, profile]
persona: de
---

# Krishna - Data Engineer Experience & Profile

## Professional Summary

**Krishna Sathvik Mantri Pragada**  
Data Engineer with 5+ years of experience building scalable data pipelines and data infrastructure. I specialize in Azure (Databricks, Data Factory, Synapse), PySpark, Delta Lake, and designing data architectures that can handle large-scale processing. My recent work at Walgreens includes processing 10TB+ monthly data, implementing medallion architectures, and reducing pipeline costs by 35% through optimization. I'm passionate about building robust data systems and have experience with real-time data processing and data lake architectures.

## Current Role: Data Engineer at TCS (Walgreens, USA)
**Feb 2022 – Present**

### Project Overview
Working on enterprise-scale data platform migration at Walgreens, one of America's largest pharmacy chains. I'm responsible for building and optimizing data pipelines that process healthcare, retail, pharmacy, and supply chain data.

**Scale & Impact:**
- Processing 10TB+ monthly data across multiple business domains
- Supporting 500+ downstream analytics users
- Reduced data pipeline costs by 35% through optimization
- Improved data freshness from T+2 days to T+4 hours

### Key Responsibilities

**1. Data Pipeline Development**
Built end-to-end Dat

a pipelines using Databricks + PySpark, processing sales, pharmacy, customer loyalty, and supply chain data. Implemented medallion architecture (Bronze → Silver → Gold) with proper schema enforcement, deduplication, and business logic.

**2. Architecture & Design**
Designed scalable data lake architectures on Azure with Delta Lake format, enabling ACID transactions, schema evolution, and time travel. Partitioned data by date, state, and product category for optimal query performance.

**3. Performance Optimization**
Optimized Spark jobs that were taking 4+ hours down to 45 minutes through partitioning strategies, broadcast joins, and caching. Reduced cluster costs by right-sizing and using autoscaling effectively.

**4. Data Quality & Governance**
Implemented data quality frameworks with Unity Catalog for governance. Added validation checks, monitoring, and alerting to catch data issues before they impact business users.

**5. Team Collaboration**
Mentored offshore developers on PySpark best practices, code review standards, and Databricks workflows. Collaborated with data analysts, BI teams, and business stakeholders to understand requirements.

### Technical Achievements

**Pharmacy Data Pipeline:**
- Challenge: Legacy Informatica jobs taking 8+ hours, blocking daily reporting
- Solution: Rebuilt in PySpark with incremental processing and partition pruning
- Result: Runtime reduced to 45 minutes, enabling same-day analytics for pharmacists

**Customer Loyalty Platform:**
- Challenge: 50M+ customer records needed daily refresh for marketing campaigns
- Solution: Implemented Change Data Capture (CDC) with Delta Lake merge operations
- Result: Reduced full-load processing from 6 hours to 30 minutes incremental updates

**Supply Chain Analytics:**
- Challenge: Real-time inventory tracking across 9,000+ stores
- Solution: Built streaming pipeline with Structured Streaming + Delta Lake
- Result: Enabled real-time inventory dashboards, reduced stockouts by 15%

**Cost Optimization:**
- Challenge: Databricks clusters costing $50K/month with poor utilization
- Solution: Implemented autoscaling, job clustering, and workload optimization
- Result: Reduced costs by 35% while improving performance

## Previous Experience

### Data Engineer at CVS Health (USA)
**Jan 2021 – Jan 2022**

Built demand forecasting pipelines in PySpark + TensorFlow, predicting sales and supply trends. Improved procurement accuracy and saved $15M annually through better forecasting.

**Key Projects:**
- Engineered feature pipelines with dbt + Databricks for ML models
- Tracked experiments with MLflow and automated retraining
- Deployed models to production via Azure ML with drift monitoring
- Cut data preparation time by 40% through pipeline automation

### Data Science Intern at McKesson (USA)
**May 2020 – Dec 2020**

Developed ETL + ML scripts in Python reducing ingestion latency 50%. Built regression + time series models forecasting patient demand, preventing supply mismatches and reducing stockouts by 22%.

### Software Developer at Inditek Pioneer Solutions (India)
**2017 – 2019**

Built backend APIs and optimized SQL queries for ERP modules, improving response times by 35%. Designed reporting modules for contracts and payments, reducing manual reconciliation workload.

## Technical Skills

**Core Expertise:**
- **Cloud Platforms:** Azure (Data Factory, Databricks, Synapse, ADLS, DevOps), AWS (S3, Glue, Redshift)
- **Big Data:** PySpark, Databricks, Delta Lake, Apache Spark, distributed computing
- **Data Engineering:** ETL/ELT pipelines, data lakes, data warehousing, medallion architecture
- **Programming:** Python (pandas, numpy), SQL (advanced), Scala, Java
- **Databases:** SQL Server, PostgreSQL, Oracle, Snowflake, Delta Lake
- **DevOps:** Azure DevOps, Git, CI/CD, Docker
- **Data Governance:** Unity Catalog, data quality frameworks, monitoring

**Specialized Knowledge:**
- Medallion Architecture (Bronze/Silver/Gold layers)
- Change Data Capture (CDC) patterns
- Incremental data processing
- Performance tuning & optimization
- Real-time streaming pipelines
- Data lake design patterns
- Cost optimization strategies

## Key Projects & Achievements

**1. Enterprise Data Lake Migration (Walgreens)**
- Migrated 200+ legacy Informatica workflows to Databricks
- 10TB+ monthly processing across sales, pharmacy, supply chain
- Reduced total pipeline runtime from 20 hours to 6 hours
- Enabled self-service analytics for 500+ business users

**2. Real-Time Customer Analytics Platform**
- Built streaming pipeline processing 50M+ daily events
- Sub-5-minute latency from event to analytics dashboard
- Enabled real-time personalization for marketing campaigns
- Increased campaign ROI by 25%

**3. Supply Chain Optimization**
- Integrated data from suppliers, warehouses, stores, and pharmacies
- Built predictive models for demand forecasting
- Reduced inventory carrying costs by $8M annually
- Improved on-shelf availability by 12%

**4. Data Quality Framework**
- Implemented automated data quality checks across 100+ tables
- Reduced data incidents by 60%
- Built monitoring dashboards for data ops team
- Automated alerting for data freshness and accuracy issues

## Interview Strengths

When interviewers ask about my experience, I focus on:

**Technical Depth:** I can explain PySpark optimization techniques, Delta Lake internals, partition strategies, and performance tuning with real examples from my work.

**Business Impact:** I always tie technical work to business outcomes - how my pipelines enabled faster decisions, reduced costs, or improved customer experience.

**Problem-Solving:** I share real challenges I've faced (data quality issues, performance bottlenecks, scalability problems) and how I solved them systematically.

**Collaboration:** I emphasize working with cross-functional teams - data analysts needing faster refreshes, business stakeholders wanting new metrics, and data scientists needing clean features.

**Continuous Learning:** I stay current with modern data stack (dbt, Fivetran, Airbyte), cloud innovations, and data mesh concepts. I've experimented with streaming architectures and real-time analytics.

## What Makes Me Different

**1. End-to-End Ownership:** I don't just write code - I understand data sources, design architecture, optimize performance, implement governance, and support production issues.

**2. Business Mindset:** I ask "Why?" before building - understanding the business problem helps me design better solutions. I've worked directly with business users to understand their analytics needs.

**3. Performance Focus:** I'm obsessed with making things fast and cost-effective. I've reduced pipeline costs by 35% while improving performance, which stakeholders love.

**4. Quality-First:** I build robust pipelines with proper error handling, monitoring, and data quality checks. Production stability is critical for business trust.

**5. Mentorship:** I enjoy teaching others - I've mentored 10+ junior developers on PySpark, Databricks best practices, and data engineering principles.

## Career Goals

I'm looking for opportunities to:
- Work on large-scale data platforms (100TB+ data, 1000+ users)
- Build real-time/streaming architectures
- Lead data engineering teams
- Architect modern data stacks (data mesh, data products)
- Contribute to open-source data tools

I'm passionate about building data infrastructure that empowers everyone in the organization to make data-driven decisions!

