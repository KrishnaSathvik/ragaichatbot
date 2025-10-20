---
tags: [krishna, experience, resume, ai-ml-engineer, genai-engineer, walgreens, cvs, mckesson, indietek]
persona: ai
---

# Krishna's AI/ML/GenAI Professional Experience & Background

## Professional Summary

I'm Krishna, an AI/ML Engineer with 5+ years of experience building end-to-end machine learning and generative AI solutions. I'm skilled in developing data pipelines, training and deploying ML models, and implementing RAG/LLM systems with embeddings and vector databases. I have a proven ability to deliver cost-efficient, production-ready AI platforms that scale across domains including healthcare, retail, and finance.

## Professional Experience

### AI/ML Engineer — TCS (Walgreens, USA)
**Duration:** Feb 2022 – Present

**Key Responsibilities and Achievements:**

So at Walgreens through TCS, I designed and deployed this RAG pipeline with Databricks, Pinecone, and OpenAI. The goal was to enable pharmacists to query compliance documents in natural language with source-cited answers. This was a game-changer because pharmacists could now get instant answers instead of spending hours searching through documents.

I engineered ingestion of structured and unstructured data (PDFs, transcripts) via PySpark pipelines, transforming data into embeddings and cutting manual search effort by 60%. The pharmacists were really happy with this improvement.

I automated retraining and re-indexing workflows using Airflow, which improved model freshness and reduced knowledge gaps across pharmacy operations. This was important because compliance documents change frequently, and we needed to keep the system up-to-date.

I deployed scalable inference APIs on AKS with CI/CD in Azure DevOps, ensuring zero-downtime rollouts and 35% latency reduction with optimized caching and prompts. The performance improvement was significant, and the system was much more reliable.

I implemented governance with Unity Catalog and PII scrubbing, securing sensitive patient data while maintaining HIPAA compliance in embeddings and responses. This was crucial because we were dealing with healthcare data and needed to ensure patient privacy.

**Technologies Used:**
- Databricks, PySpark, Pinecone, OpenAI API
- LangChain, RAG pipelines, Vector DBs
- Azure ML, AKS, Azure DevOps
- Unity Catalog, PII masking, HIPAA compliance

### ML Engineer — CVS Health (USA)
**Duration:** Oct 2020 – Dec 2021

**Key Responsibilities and Achievements:**

At CVS Health, I built demand forecasting models in PySpark and TensorFlow that predicted sales and supply trends. This was really exciting because I got to work with both data engineering and machine learning. I improved procurement accuracy and saved $15M annually, which was a huge win for the business.

I engineered feature pipelines with dbt and Databricks for model-ready datasets, cutting preparation time by 40% and ensuring consistency across teams. This was important because data scientists were spending too much time on data preparation instead of building models.

I tracked experiments with MLflow and automated retraining pipelines, which boosted model performance by 18% over baseline. The automated retraining was crucial because it kept the models fresh and accurate.

I deployed models to production via Azure ML, implementing monitoring for drift and automating retraining triggers. This was my first experience with MLOps, and I learned a lot about production ML systems.

**Technologies Used:**
- PySpark, TensorFlow, MLflow
- dbt, Databricks, Azure ML
- Python, Pandas, Scikit-learn
- SQL Server, Power BI

**Challenges Overcome:**
- Building scalable forecasting models for retail operations
- Implementing MLOps practices for model lifecycle management
- Ensuring model reliability in production environments
- Integrating ML models with business processes

### Data Science Intern — McKesson (USA)
**Duration:** Mar 2020 – Sep 2020

**Key Responsibilities and Achievements:**

At McKesson, I developed ETL and ML scripts in Python that reduced ingestion latency by 50%. This was my first real experience with ETL and ML, and it was really exciting to see the impact. The scripts powered dashboards for executive decisions on financial integrity, which was really important for the business.

I built regression and time series models that forecasted patient demand, preventing supply mismatches and reducing stockouts by 22%. This was really satisfying because it directly improved patient care by ensuring medications were available when needed.

I produced compliance-focused ML insights that aligned with audit requirements and informed leadership's strategic reviews. This was important because healthcare companies need to maintain strict compliance standards.

**Technologies Used:**
- Python, SQL, Pandas, NumPy
- Scikit-learn, TensorFlow
- SQL Server, Oracle
- Power BI, Tableau

**Key Learnings:**
- Building ML models for healthcare compliance
- Time series forecasting for supply chain optimization
- Integrating ML insights with business processes
- Ensuring model reliability in regulated environments

### Software Developer — Inditek Pioneer Solutions (India)
**Duration:** Jun 2018 – Dec 2019

**Key Responsibilities and Achievements:**

At Indietek, I built backend APIs and optimized SQL queries for ERP modules, which strengthened transactional accuracy and improved response times by 35%. This was where I started my career, and it was a great foundation for learning about system performance and optimization.

I designed reporting modules that surfaced anomalies in contracts and payments, reducing manual reconciliation workload. This was really satisfying because it helped the business team work more efficiently.

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

- **AI/ML & GenAI:** PyTorch, TensorFlow, Hugging Face, OpenAI API, LangChain, MLflow, RAG pipelines, Vector DBs (Pinecone, FAISS, Weaviate)
- **Data Engineering & ELT:** PySpark, Databricks, Airflow, dbt
- **Cloud Platforms:** Azure (ML, Data Factory, AKS, DevOps), AWS (SageMaker, Lambda, S3)
- **Databases & Storage:** SQL Server, PostgreSQL, Delta Lake, Oracle, Vector DBs
- **Analytics & BI:** Power BI, Tableau, KPI Dashboards
- **DevOps & Governance:** Azure DevOps, GitHub Actions, Docker, Kubernetes, Unity Catalog, PII Masking, Model Monitoring

## Key Achievements & Metrics

### AI/ML Impact
- Built RAG pipeline reducing manual search by 60%
- Developed forecasting models saving $15M+ annually
- Improved model performance by 18% over baseline
- Reduced stockouts by 22% through demand forecasting
- Achieved 35% latency reduction in inference APIs

### Scale & Performance
- Processed 10TB+ monthly data for ML pipelines
- Built models serving 1000+ concurrent users
- Implemented automated retraining for 20+ models
- Achieved 99.9% uptime for production ML services

### Business Impact
- Enabled natural language querying of compliance documents
- Improved procurement accuracy through demand forecasting
- Reduced manual reconciliation by 40%
- Uncovered $20M+ in procurement savings through ML insights

### Technical Leadership
- Led end-to-end RAG system implementation
- Mentored teams on MLOps best practices
- Established model governance and monitoring frameworks
- Implemented HIPAA-compliant AI systems

## Interview Talking Points

### Problem-Solving Examples

**Challenge: Building Production RAG System**
At Walgreens, I had to build a RAG pipeline for pharmacists to query compliance documents, but getting it production-ready was really challenging. We had to handle HIPAA compliance, ensure low latency, and maintain high availability. What I did was implement PII scrubbing in the embedding pipeline, deploy scalable inference APIs on AKS with CI/CD, and optimize caching and prompts. The result was a 35% latency reduction with zero-downtime deployments and full HIPAA compliance. The system now serves 1000+ users daily.

**Challenge: Large-Scale Forecasting Model Deployment**
At CVS, I built demand forecasting models that were performing well in development, but deploying them to production at scale was tricky. We had to handle real-time inference, manage model drift, and ensure reliability. What I did was implement MLflow for experiment tracking, build automated retraining pipelines, and deploy models via Azure ML with comprehensive monitoring. The result was models that improved performance by 18% over baseline and saved the company over $15 million annually.

**Challenge: ML Pipeline Optimization**
At McKesson, we had ML pipelines that were taking too long to run and costing too much. The data preparation was manual and error-prone. What I did was build automated ETL scripts using Python that reduced ingestion latency by 50% and implemented proper data validation. I also built feature pipelines that standardized data preparation across teams. The result was much more reliable and efficient ML operations.

### Technical Strengths

**RAG & GenAI Systems**
I'm really strong in building RAG systems and working with LLMs. I've built production RAG pipelines using Pinecone, OpenAI API, and LangChain. I know how to handle embeddings, implement semantic search, and optimize prompts for better responses. I understand vector databases and how to scale them for production use.

**MLOps & Production Deployment**
I'm experienced with the full ML lifecycle from development to production. I know how to use MLflow for experiment tracking, implement automated retraining, and deploy models at scale. I understand model monitoring, drift detection, and how to ensure model reliability in production.

**Machine Learning & Deep Learning**
I've built models across different domains including forecasting, NLP, and computer vision. I'm experienced with TensorFlow, PyTorch, and Scikit-learn. I know how to optimize models for performance and handle challenges like overfitting, data imbalance, and model interpretability.

**Cloud ML Services**
I'm experienced with cloud ML platforms including Azure ML, AWS SageMaker, and Google Vertex AI. I know how to leverage managed services for model training and deployment while maintaining control over the ML pipeline.

## Work Style & Approach

### My Philosophy
I believe in building AI systems that are not just technically sound but also reliable and maintainable. When I build an ML model or RAG system, I think about the entire lifecycle - from data preparation to production deployment and monitoring. I don't just deliver a model - I make sure it's production-ready and can scale with business needs.

### Collaboration
I work well in cross-functional teams. I've collaborated with data scientists, data engineers, product managers, and business stakeholders. I believe in clear communication, documentation, and knowledge sharing. I've mentored teams on ML best practices and helped them understand complex AI concepts.

### Continuous Learning
I'm always learning new AI/ML technologies and techniques. I recently got deep into RAG systems, vector databases, and advanced prompt engineering. I'm exploring newer LLM architectures and MLOps practices. I believe in staying current with AI research and applying new techniques to solve business problems.

### Problem-Solving Approach
When I face a complex AI/ML problem, I start by understanding the business context and data constraints. I prototype quickly, validate assumptions, and build iteratively. I believe in thorough testing, monitoring, and continuous optimization. I also believe in documenting everything so the team can understand and maintain the AI system.
