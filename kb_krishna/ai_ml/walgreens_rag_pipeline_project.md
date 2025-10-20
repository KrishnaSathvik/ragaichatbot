---
tags: [krishna, experience, walgreens, rag-pipeline, ai-ml-engineer, databricks, pinecone, openai]
persona: ai
---

# RAG Pipeline for Pharmacist Document Search - Walgreens

## Project Overview

**Duration:** Feb 2022 – Present  
**Role:** AI/ML Engineer  
**Company:** TCS (Walgreens, USA)  
**Project:** RAG Pipeline for Pharmacist Compliance Document Search

## Technical Challenge

Walgreens pharmacists were spending hours searching through compliance documents, policies, and procedures to find specific information. The existing search system was returning irrelevant results, and pharmacists needed a way to query documents in natural language with source-cited answers. The challenge was building a production-ready RAG (Retrieval-Augmented Generation) system that could handle HIPAA compliance, ensure low latency, and maintain high availability while serving 1000+ users daily.

## My Role & Responsibilities

As the AI/ML Engineer, I was responsible for:
- Designing and deploying the RAG pipeline with Databricks, Pinecone, and OpenAI
- Engineering ingestion of structured and unstructured data (PDFs, transcripts) via PySpark pipelines
- Automating retraining and re-indexing workflows using Airflow
- Deploying scalable inference APIs on AKS with CI/CD in Azure DevOps
- Implementing governance with Unity Catalog and PII scrubbing

## Key Technical Achievements

### RAG Pipeline Architecture
I designed and deployed a comprehensive RAG pipeline that enables pharmacists to query compliance documents in natural language with source-cited answers. The system processes both structured and unstructured data, transforming it into embeddings for efficient retrieval.

**What I accomplished:**
- Built end-to-end RAG pipeline serving 1000+ users daily
- Reduced manual search effort by 60% across pharmacy operations
- Achieved 35% latency reduction with optimized caching and prompts
- Ensured zero-downtime rollouts with comprehensive CI/CD

### Data Ingestion & Processing
I engineered ingestion of structured and unstructured data (PDFs, transcripts) via PySpark pipelines, transforming data into embeddings and cutting manual search effort by 60%. The system handles various document formats and ensures data quality throughout the pipeline.

**Key technical implementations:**
- Built PySpark pipelines for document processing and embedding generation
- Implemented automated data validation and quality checks
- Created scalable data processing workflows using Databricks
- Established data lineage tracking and monitoring

### Model Deployment & Optimization
I deployed scalable inference APIs on AKS with CI/CD in Azure DevOps, ensuring zero-downtime rollouts and 35% latency reduction with optimized caching and prompts. The system maintains high availability and performance under load.

**Deployment achievements:**
- Implemented AKS-based microservices architecture
- Built comprehensive CI/CD pipeline with Azure DevOps
- Optimized caching strategies for improved performance
- Established monitoring and alerting for production systems

### Data Governance & Compliance
I implemented governance with Unity Catalog and PII scrubbing, securing sensitive patient data while maintaining HIPAA compliance in embeddings and responses. This was crucial for healthcare data handling.

**Compliance measures:**
- Implemented PII scrubbing in embedding pipeline
- Established data governance with Unity Catalog
- Ensured HIPAA compliance throughout the system
- Created audit trails and data lineage tracking

## Technical Architecture

### RAG Pipeline Design
```
Documents → PySpark → Embeddings → Pinecone → OpenAI API → Responses
    ↓           ↓           ↓           ↓           ↓
Data Lake → Databricks → Vector DB → LLM → AKS APIs
```

### Key Technologies Used
- **AI/ML**: OpenAI API, LangChain, RAG pipelines, Vector DBs (Pinecone)
- **Data Processing**: PySpark, Databricks, Airflow
- **Cloud Platforms**: Azure (AKS, DevOps, Data Factory)
- **Data Governance**: Unity Catalog, PII scrubbing, monitoring

## Business Impact

### Quantifiable Results
- **User Adoption**: Serving 1000+ users daily across pharmacy operations
- **Efficiency**: Reduced manual search effort by 60%
- **Performance**: Achieved 35% latency reduction
- **Reliability**: Zero-downtime deployments with comprehensive CI/CD
- **Compliance**: Full HIPAA compliance with data governance

### User Benefits
- **Pharmacists**: Instant access to compliance information with source citations
- **Management**: Improved operational efficiency and reduced training time
- **IT Teams**: Scalable, maintainable system with comprehensive monitoring
- **Compliance**: Automated audit trails and data lineage tracking

## Technical Skills Demonstrated

- **RAG Systems**: Pipeline design, embedding generation, retrieval optimization
- **Vector Databases**: Pinecone integration, similarity search, indexing
- **LLM Integration**: OpenAI API, prompt engineering, response optimization
- **Data Engineering**: PySpark, Databricks, ETL/ELT pipelines
- **MLOps**: Model deployment, CI/CD, monitoring, governance
- **Cloud Platforms**: Azure (AKS, DevOps, Data Factory), scalable architectures
- **Data Governance**: Unity Catalog, PII scrubbing, compliance, security
