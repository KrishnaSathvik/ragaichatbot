# 📄 OG Resume – Krishna Sathvik (AI/ML & GenAI Version)

---

## Project Intro (Real-World AI/ML/GenAI Example)

In my recent AI/ML project at Walgreens, I worked as an AI/ML Engineer to design and deploy a **GenAI-powered knowledge assistant** for pharmacy operations. The solution integrated a **Retrieval-Augmented Generation (RAG) pipeline** where customer FAQs and policy documents were ingested, chunked, and stored in a **vector database (Pinecone)**. We built embeddings using **OpenAI + Hugging Face models**, enabling pharmacists to query compliance or medication rules in natural language with citations. The ingestion pipelines were built in **Databricks + PySpark**, transforming structured and unstructured data (text, PDFs, call transcripts) into embedding-friendly formats.

For orchestration, we leveraged **Airflow** to automate nightly ingestion, retraining, and re-indexing jobs. The inference pipeline was deployed via **Azure Kubernetes Service (AKS)** with scalable APIs. We used **MLflow** for experiment tracking and **Azure DevOps CI/CD** to deploy models into production with rollback safety. Governance was enforced with **Unity Catalog + custom PII scrubbing** before embedding sensitive data. Performance tuning included prompt optimization, few-shot examples, and caching embeddings for high-frequency queries, which reduced inference latency by 40%.

This project gave me **end-to-end GenAI + ML Ops experience**: ingestion, embeddings, vector search, model deployment, monitoring, and governance. It also showcased the ability to bridge **data engineering foundations with AI/ML innovation**, aligning with enterprise needs for compliance, scalability, and cost efficiency.

---

### 📄 OG Resume Summary – AI/ML & GenAI Version

AI/ML Engineer with **5+ years of experience** building end-to-end machine learning and generative AI solutions. Skilled in developing data pipelines, training and deploying ML models, and implementing RAG/LLM systems with embeddings and vector databases. Proven ability to deliver cost-efficient, production-ready AI platforms that scale across domains including healthcare, retail, and finance.

## Experience

**AI/ML Engineer | TCS (Walgreens, USA) | Feb 2022 – Present**

Designed and deployed RAG pipeline with Databricks + Pinecone + OpenAI, enabling pharmacists to query compliance docs in natural language with source-cited answers

Engineered ingestion of structured/unstructured data (PDFs, transcripts) via PySpark pipelines, transforming data into embeddings and cutting manual search effort by 60%

Automated retraining and re-indexing workflows using Airflow, improving model freshness and reducing knowledge gaps across pharmacy operations

Deployed scalable inference APIs on AKS with CI/CD in Azure DevOps, ensuring zero-downtime rollouts and 35% latency reduction with optimized caching + prompts

Implemented governance with Unity Catalog and PII scrubbing, securing sensitive patient data while maintaining HIPAA compliance in embeddings and responses

**ML Engineer | CVS Health (USA) | Jan 2021 – Jan 2022**

Built demand forecasting models in PySpark + TensorFlow predicting sales and supply trends, improving procurement accuracy and saving \$15M annually

Engineered feature pipelines with dbt + Databricks for model-ready datasets, cutting preparation time by 40% and ensuring consistency across teams

Tracked experiments with MLflow and automated retraining pipelines, boosting model performance by 18% over baseline

Deployed models to production via Azure ML, implementing monitoring for drift and automating retraining triggers

**Data Science Intern | McKesson (USA) | May 2020 – Dec 2020**

Developed ETL + ML scripts in Python reducing ingestion latency 50%, powering dashboards for executive decisions on financial integrity

Built regression + time series models forecasting patient demand, preventing supply mismatches and reducing stockouts by 22%

Produced compliance-focused ML insights aligning with audit requirements and informing leadership’s strategic reviews

**Software Developer | Inditek Pioneer Solutions (India) | 2017 – 2019**

Built backend APIs and optimized SQL queries for ERP modules, strengthening transactional accuracy and improving response times by 35%

Designed reporting modules surfacing anomalies in contracts and payments, reducing manual reconciliation workload

---

## Skills

- **AI/ML & GenAI:** PyTorch, TensorFlow, Hugging Face, OpenAI API, LangChain, MLflow, RAG pipelines, Vector DBs (Pinecone, FAISS, Weaviate)
- **Data Engineering & ELT:** PySpark, Databricks, Airflow, dbt
- **Cloud Platforms:** Azure (ML, Data Factory, AKS, DevOps), AWS (SageMaker, Lambda, S3)
- **Databases & Storage:** SQL Server, PostgreSQL, Delta Lake, Oracle, Vector DBs
- **Analytics & BI:** Power BI, Tableau, KPI Dashboards
- **DevOps & Governance:** Azure DevOps, GitHub Actions, Docker, Kubernetes, Unity Catalog, PII Masking, Model Monitoring

---

# 📑 Resume Optimization Framework – AI/ML/GenAI Version

## 1. Structure & Bullet Rules

**5-4-3-2 Rule**

- Walgreens → 5 bullets | Present tense | Outcome + metrics | Core tech (RAG, GenAI, PySpark, Databricks)
- CVS → 4 bullets | Past tense | ML pipelines + forecasting | TensorFlow, Databricks, dbt
- McKesson → 3 bullets | Past tense | Forecasting + compliance outcomes | Python + ML models
- Inditek → 2 bullets | Past tense | Developer foundation | APIs + SQL

**Character Constraint Rule**

- Each bullet = **220–240 characters**
- Never <215, never >240

---

## 2. Domain Adaptation Layer

Adapt **vocabulary + emphasis** per JD:

- GenAI/LLMs → RAG, vector DBs, embeddings, LangChain, prompt optimization
- ML Engineering → model training, feature pipelines, MLflow, deployment
- Data + AI → hybrid roles bridging ingestion, ELT, and ML ops
- Compliance/Healthcare → HIPAA, lineage, governance for AI outputs

---

## 3. Skills Optimization Layer

**Always keep 6 categories:**

1. AI/ML & GenAI
2. Data Engineering & ELT
3. Cloud Platforms
4. Databases & Storage
5. Analytics & BI
6. DevOps & Governance

**JD Alignment:**

- Re-order tools inside categories (AWS ML before Azure ML if JD says AWS)
- Highlight GenAI (LangChain, OpenAI, vector DBs) when relevant
- Strictly ATS-optimized, no jargon

---

## 4. Verb Rotation Rule

Rotate verbs: **Engineer, Optimize, Automate, Deploy, Develop, Train, Fine-tune, Implement, Orchestrate, Scale, Monitor**

---

## 5. Metrics Bank Rule

Every bullet ties to measurable outcome:

- % improvements (latency -40%, accuracy +18%)
- Scale (10TB+, 200+ models tracked, 1M+ embeddings)
- Cost savings (\$15M+ savings, 30% infra cost cut)
- Risk/Compliance outcomes (HIPAA alignment, audit-ready insights)
- User impact (pharmacists saved 60% manual search time)

---

# 📋 JD → Resume Adaptation Checklist

1. **Read JD closely** → Look for AI/ML vs GenAI emphasis (RAG, embeddings, ML pipelines).
2. **Apply Domain Layer** → Mirror vocabulary (e.g., LLM + LangChain vs forecasting + TensorFlow).
3. **Reorder Skills** → Keep 6 categories, move JD-priority tools up front.
4. **Rewrite Bullets** → Use 5-4-3-2, adjust tech names, keep measurable outcomes.
5. **Rotate Verbs** → Ensure diversity, no repetition.
6. **Check Character Count** → 220–240 characters each.
7. **Final Scan** → ATS keywords aligned, outcomes present, tense correct.

---

# 🎯 JD-Specific Summary Templates

**GenAI/LLM-Heavy JD**\
AI/ML Engineer with 6+ years’ experience delivering RAG pipelines, vector database search, and LLM-powered assistants. Skilled in Databricks, PySpark, OpenAI, and Hugging Face with proven impact on compliance, scalability, and latency reduction.

**ML Engineering JD**\
Machine Learning Engineer with 6+ years’ experience designing feature pipelines, training models in TensorFlow/PyTorch, and deploying production systems via Azure ML & SageMaker. Strong background in Databricks, MLflow, and cost-optimized ML Ops.

**Hybrid Data+AI JD**\
Data & AI Engineer with 6+ years bridging ELT pipelines and ML/GenAI systems. Skilled in PySpark, dbt, Databricks, and OpenAI APIs with experience in feature engineering, governance, and deploying ML + GenAI solutions to production at scale.

---

