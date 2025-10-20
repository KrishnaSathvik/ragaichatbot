---
tags: [data-engineer, krishna, experience, walgreens, azure, databricks, resume, profile]
persona: de
---

# Krishna - Data Engineer Experience & Profile

## Professional Summary

I'm Krishna, a Data Engineer with 5+ years of experience building scalable data pipelines and data infrastructure. I specialize in Azure (Databricks, Data Factory, Synapse), PySpark, Delta Lake, and designing data architectures that can handle large-scale processing. My recent work at Walgreens includes processing 10TB+ monthly data, implementing medallion architectures, and reducing pipeline costs by 35% through optimization. I'm passionate about building robust data systems and have experience with real-time data processing and data lake architectures.

## Current Role: Data Engineer at TCS (Walgreens, USA)
**Feb 2022 – Present**

### Project Overview
So at Walgreens, I'm working on this massive enterprise-scale data platform migration. It's one of America's largest pharmacy chains, so the scale is incredible. I'm responsible for building and optimizing data pipelines that process healthcare, retail, pharmacy, and supply chain data.

**What I've accomplished:**
- Processing 10TB+ monthly data across multiple business domains
- Supporting 500+ downstream analytics users
- Reduced data pipeline costs by 35% through optimization
- Improved data freshness from T+2 days to T+4 hours

### Key Responsibilities

**Data Pipeline Development**
So I built these end-to-end data pipelines using Databricks + PySpark, processing sales, pharmacy, customer loyalty, and supply chain data. What I did was implement a medallion architecture (Bronze → Silver → Gold) with proper schema enforcement, deduplication, and business logic. This really helped us organize the data flow and ensure quality at each layer.

**Architecture & Design**
I designed scalable data lake architectures on Azure with Delta Lake format, which enabled ACID transactions, schema evolution, and time travel. I partitioned the data by date, state, and product category for optimal query performance. This was crucial because we were dealing with massive amounts of data and needed to make sure queries ran efficiently.

**Performance Optimization**
One of my biggest wins was optimizing Spark jobs that were taking 4+ hours down to 45 minutes. I did this through partitioning strategies, broadcast joins, and caching. I also reduced cluster costs by right-sizing and using autoscaling effectively. The stakeholders were really happy with the performance improvements and cost savings.

**Data Quality & Governance**
I implemented data quality frameworks with Unity Catalog for governance. I added validation checks, monitoring, and alerting to catch data issues before they impact business users. This was super important because data quality issues can really hurt business decisions.

**Team Collaboration**
I mentor offshore developers on PySpark best practices, code review standards, and Databricks workflows. I also collaborate with data analysts, BI teams, and business stakeholders to understand requirements. I believe in knowledge sharing and helping the team grow.

### Technical Achievements

**Pharmacy Data Pipeline:**
So we had this huge challenge with legacy Informatica jobs taking 8+ hours, which was blocking daily reporting. The pharmacists were getting frustrated because they couldn't get their analytics on time. What I did was rebuild the entire pipeline in PySpark with incremental processing and partition pruning. The result was amazing - runtime reduced to 45 minutes, enabling same-day analytics for pharmacists. They were really happy with the improvement.

**Customer Loyalty Platform:**
Another major project was the customer loyalty platform where we had 50M+ customer records that needed daily refresh for marketing campaigns. The challenge was that the full load was taking 6 hours every day. I implemented Change Data Capture (CDC) with Delta Lake merge operations. This was a game-changer - we reduced full-load processing from 6 hours to 30 minutes incremental updates. The marketing team could now get fresh data much faster.

**Supply Chain Analytics:**
One of my favorite projects was building real-time inventory tracking across 9,000+ stores. The challenge was that we needed real-time visibility into inventory levels. I built a streaming pipeline with Structured Streaming + Delta Lake. The result was that we enabled real-time inventory dashboards and reduced stockouts by 15%. The operations team was thrilled with the real-time visibility.

**Cost Optimization:**
This was a big win for the company. We had Databricks clusters costing $50K/month with poor utilization. The stakeholders were concerned about the costs. I implemented autoscaling, job clustering, and workload optimization. The result was that we reduced costs by 35% while actually improving performance. Everyone was happy with the cost savings and better performance.

## Previous Experience

### Analytics Engineer at CVS Health (USA)
**Oct 2020 – Dec 2021**

At CVS Health, I built demand forecasting pipelines in PySpark + TensorFlow, predicting sales and supply trends. This was really exciting because I got to work with both data engineering and machine learning. I improved procurement accuracy and saved $15M annually through better forecasting. The business impact was huge.

**Key Projects:**
- Engineered feature pipelines with dbt + Databricks for ML models
- Tracked experiments with MLflow and automated retraining
- Deployed models to production via Azure ML with drift monitoring
- Cut data preparation time by 40% through pipeline automation

### Data Science Intern at McKesson (USA)
**Mar 2020 – Sep 2020**

This was my first real experience with ETL + ML scripts in Python. I reduced ingestion latency by 50%, which was a big win. I built regression + time series models forecasting patient demand, preventing supply mismatches and reducing stockouts by 22%. It was really satisfying to see the impact on patient care.

### Software Developer at Inditek Pioneer Solutions (India)
**Jun 2018 – Dec 2019**

This was where I started my career. I built backend APIs and optimized SQL queries for ERP modules, improving response times by 35%. I also designed reporting modules for contracts and payments, reducing manual reconciliation workload. It was a great foundation for my data engineering career.

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

**Technical Depth:** I can explain PySpark optimization techniques, Delta Lake internals, partition strategies, and performance tuning with real examples from my work. I love diving deep into the technical details and showing how I've solved complex problems.

**Business Impact:** I always tie technical work to business outcomes - how my pipelines enabled faster decisions, reduced costs, or improved customer experience. I believe that's what makes a good data engineer - understanding the business value of what we build.

**Problem-Solving:** I share real challenges I've faced (data quality issues, performance bottlenecks, scalability problems) and how I solved them systematically. I think it's important to show that I can handle difficult situations and find solutions.

**Collaboration:** I emphasize working with cross-functional teams - data analysts needing faster refreshes, business stakeholders wanting new metrics, and data scientists needing clean features. I believe collaboration is key to success in data engineering.

**Continuous Learning:** I stay current with modern data stack (dbt, Fivetran, Airbyte), cloud innovations, and data mesh concepts. I've experimented with streaming architectures and real-time analytics. I'm always learning new things and staying up-to-date with the latest trends.

## What Makes Me Different

**End-to-End Ownership:** I don't just write code - I understand data sources, design architecture, optimize performance, implement governance, and support production issues. I believe in taking ownership of the entire data pipeline lifecycle.

**Business Mindset:** I ask "Why?" before building - understanding the business problem helps me design better solutions. I've worked directly with business users to understand their analytics needs. I think it's important to understand the business context behind what we're building.

**Performance Focus:** I'm obsessed with making things fast and cost-effective. I've reduced pipeline costs by 35% while improving performance, which stakeholders love. I believe that performance optimization is not just about speed, but also about cost efficiency.

**Quality-First:** I build robust pipelines with proper error handling, monitoring, and data quality checks. Production stability is critical for business trust. I've learned that it's better to build it right the first time than to fix issues later.

**Mentorship:** I enjoy teaching others - I've mentored 10+ junior developers on PySpark, Databricks best practices, and data engineering principles. I believe in knowledge sharing and helping the team grow.

## Career Goals

I'm looking for opportunities to:
- Work on large-scale data platforms (100TB+ data, 1000+ users)
- Build real-time/streaming architectures
- Lead data engineering teams
- Architect modern data stacks (data mesh, data products)
- Contribute to open-source data tools

I'm passionate about building data infrastructure that empowers everyone in the organization to make data-driven decisions! I believe that good data engineering can really transform how companies operate and make decisions.

