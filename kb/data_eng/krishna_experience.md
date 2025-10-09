---
tags: [krishna, experience, resume, data-engineer, walgreens, cvs, mckesson, indietek]
persona: krishna
---

# Krishna's Professional Experience & Background

## Professional Summary

Data Engineer with 6+ years of experience evolving from backend development into advanced data engineering. Skilled in Databricks, PySpark, SQL, and Azure, with proven success delivering 10TB+ scale pipelines, medallion architectures, and governance frameworks. Recognized for performance tuning, cost optimization, and enabling analytics that improve decision-making across healthcare, retail, and finance domains.

## Professional Experience

### Data Engineer — TCS (Walgreens, USA)
**Duration:** Feb 2022 – Present

**Key Responsibilities and Achievements:**

At Walgreens through TCS, I engineered Delta Lakehouse pipelines in Databricks and PySpark, processing 10TB+ monthly data across sales, pharmacy, and supply chain, enabling real-time analytics and reducing ad-hoc reporting by 32%.

I designed medallion architecture flows (Bronze, Silver, Gold) with schema enforcement, deduplication, and fact/dimension modeling, improving KPI reporting accuracy by 30%.

I automated orchestration with ADF triggering Databricks notebooks, implementing dynamic parameterization and CI/CD via Azure DevOps to achieve zero-downtime deployments.

I implemented Unity Catalog for role-based access, PII masking, and lineage tracking, ensuring compliance and secure access for regulated data and anonymized reporting.

I optimized partitioning strategies, resolved skew with salting and broadcast joins, and compacted small Delta files—reducing critical job runtime from 2+ hours to under 40 minutes.

**Technologies Used:**
- Azure Data Factory, Databricks, PySpark, Delta Lake
- Unity Catalog, Azure DevOps, CI/CD
- SQL Server, Azure Synapse, Power BI
- Azure Storage, Azure Key Vault, Azure Monitor

### Analytics Engineer — CVS Health (USA)
**Duration:** Jan 2021 – Jan 2022

**Key Responsibilities and Achievements:**

At CVS Health, I built ingestion pipelines in ADF and Databricks integrating supply chain and sales data, producing audit-ready datasets powering KPI dashboards across 200+ retail sites.

I modeled fact/dimension schemas in SQL and dbt, improving reconciliation agility and accuracy by 20% while supporting finance and operations decision-making.

I collaborated with stakeholders to define business rules for replenishment and billing, surfacing 20+ KPIs leveraged by leadership for operational strategy.

I optimized Databricks jobs with incremental models and clustering, cutting compute costs by 18% and improving pipeline performance by 25%.

**Technologies Used:**
- Azure Data Factory, Databricks, PySpark
- dbt, SQL, Python, Pandas
- SQL Server, Power BI, Azure Synapse
- Azure Storage, Azure Key Vault

**Challenges Overcome:**
- Integrating disparate supply chain data sources
- Building scalable ETL pipelines for retail operations
- Optimizing compute costs while maintaining performance
- Ensuring data quality across multiple retail locations

### Data Science Intern — McKesson (USA)
**Duration:** May 2020 – Dec 2020

**Key Responsibilities and Achievements:**

At McKesson, I automated ETL scripts in Python and SQL reducing ingestion latency by 50%, accelerating delivery of compliance dashboards for executive monitoring.

I built forecasting models aligning patient demand with supply capacity, preventing mismatches and driving $20M+ savings in procurement.

I produced insights from claims and sales data supporting compliance reviews and informing leadership's cost-recovery initiatives.

**Technologies Used:**
- Python, SQL, Pandas, NumPy
- SQL Server, Oracle
- Power BI, Tableau
- ETL tools, Data validation scripts

**Key Learnings:**
- Importance of compliance in healthcare data engineering
- Building data pipelines that align with regulatory requirements
- Data modeling techniques for supply chain optimization
- Data quality challenges in healthcare environments

### Software Developer — Inditek Pioneer Solutions (India)
**Duration:** 2017 – 2019

**Key Responsibilities and Achievements:**

At Indietek, I developed backend APIs and optimized SQL queries for ERP modules, improving system response by 35% and strengthening transactional accuracy in client billing.

I designed reporting modules surfacing missed payments and contract discrepancies, cutting manual reconciliation and improving transparency in logistics workflows.

**Technologies Used:**
- SQL Server, Oracle
- C#, .NET Framework
- JavaScript, HTML, CSS
- ERP systems, API development

**Skills Developed:**
- Backend API development and optimization
- SQL performance tuning and query optimization
- ERP system integration and customization
- Business process automation

## Skills

- **Data Engineering & ELT:** Databricks, PySpark, dbt, Airflow, ADF
- **Cloud Platforms:** Azure (Synapse, Data Factory, DevOps), Snowflake, AWS (Glue, Lambda)
- **Databases & Storage:** SQL Server, PostgreSQL, Delta Lake, Oracle
- **Analytics & BI:** Power BI, Tableau, KPI Dashboards
- **DevOps & Orchestration:** GitHub Actions, Azure DevOps, Docker, Kubernetes
- **Governance & Security:** Data Quality Validation, PII Masking, Unity Catalog

## Key Achievements & Metrics

### Technical Achievements
- **Scale**: Successfully handling 10TB+ monthly data processing
- **Performance**: 75% reduction in job runtime (2+ hours to 40 minutes)
- **Cost**: 30% reduction in processing costs through optimization
- **Reliability**: Improved SLA compliance and system stability

### Business Impact
- **Modernization**: Successfully migrated legacy systems
- **Governance**: Implemented enterprise-grade data governance
- **Collaboration**: Enhanced cross-team productivity
- **Quality**: Improved data quality and business confidence
- Reduced ad-hoc reporting requests by 32%
- Improved KPI reporting accuracy by 30%
- Enabled real-time analytics across 200+ retail sites
- Uncovered $20M+ in procurement savings

## Interview Talking Points

### Problem-Solving Examples

**Challenge: Large-Scale Data Pipeline Optimization**
At Walgreens, we had these critical data pipelines that were taking over 2 hours to run and costing us a fortune in compute resources. The business was getting frustrated with delays and we were hitting our SLA limits. What I did was analyze the execution plans, identify bottlenecks, and implement strategic partitioning by date, state, and product. I also resolved data skew using salting techniques and optimized joins with broadcast strategies. The result was incredible - we cut runtime by 75% from 2+ hours down to under 40 minutes, and reduced processing costs by 30%. This really transformed our data platform performance.

**Challenge: Legacy System Migration**
One of my biggest challenges was migrating from fragmented legacy systems to a modern medallion architecture at Walgreens. We had data scattered across different systems with inconsistent schemas and quality issues. What I did was design a Bronze-Silver-Gold architecture using Delta Lake that handled schema evolution and data quality validation. I built comprehensive deduplication logic and implemented Unity Catalog for governance. The result was a unified data platform that improved reporting accuracy by 30% and reduced ad-hoc requests by 32%.

**Challenge: Data Governance Implementation**
At Walgreens, implementing proper data governance was crucial for HIPAA compliance and business trust. We had sensitive data scattered across systems with inconsistent access controls. What I did was implement Unity Catalog with role-based access control, PII masking for sensitive fields, and complete lineage tracking. I also set up automated data quality monitoring and validation frameworks. The result was full HIPAA compliance, improved data trust, and secure access for business teams.

### Technical Strengths

**Data Engineering & PySpark**
I'm really strong in PySpark and Databricks. I've built pipelines processing 10TB+ monthly data across multiple business domains. I know how to optimize for performance using partitioning, skew resolution, and join strategies. I'm experienced with Delta Lake features like schema evolution, ACID transactions, and time travel.

**ETL & Data Pipelines**
I've built comprehensive ETL pipelines using Azure Data Factory, dbt, and custom Python scripts. I know how to handle data validation, error logging, and automated retry mechanisms. I'm experienced with incremental processing, data quality frameworks, and pipeline monitoring.

**Cloud Architecture**
I'm experienced with Azure services including Data Factory, Databricks, Synapse, and DevOps. I know how to design scalable architectures, implement CI/CD, and ensure security and compliance. I've also worked with AWS services and understand multi-cloud strategies.

**Data Governance**
I've implemented enterprise-grade data governance using Unity Catalog, including role-based access control, PII masking, and lineage tracking. I understand compliance requirements like HIPAA and know how to balance security with business access needs.

## Work Style & Approach

### My Philosophy
I believe in building robust, scalable data solutions that can handle real-world challenges. When I design a data pipeline or architecture, I think about performance, cost optimization, and maintainability. I don't just deliver a solution - I make sure it's production-ready and can scale with business needs.

### Collaboration
I work well in cross-functional teams. I've collaborated with data scientists, business analysts, offshore developers, and executives. I believe in clear communication, documentation, and knowledge sharing. I've mentored teams and helped them understand complex technical concepts.

### Continuous Learning
I'm always learning new data engineering technologies and best practices. I recently got deep into Delta Lake features and advanced PySpark optimization, and I'm exploring more advanced data governance practices. I believe in staying current with industry trends and applying new techniques to solve business problems.

### Problem-Solving Approach
When I face a complex problem, I start by understanding the business context and technical constraints. I analyze the data, design a solution, and build it iteratively. I believe in thorough testing, monitoring, and continuous optimization. I also believe in documenting everything so the team can maintain and improve the solution.

