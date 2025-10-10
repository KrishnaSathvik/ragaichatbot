# Interview Preparation: Jacob's RAG & GenAI Questions

## Project Context: Pharma Complaint RAG System at Amazon Q
- **Role**: Onsite AI/ML Engineer & Coordinator
- **Focus**: RAG pipeline accuracy improvement, LangChain/LangGraph, Python/FastAPI
- **Team**: Coordinating with Avijit (offshore) and Jacob (client lead)
- **Goal**: Improve existing RAG system for pharma complaint document classification

## 1. RAG Fundamentals & Project Flow

### Q: Walk me through the RAG solution you built

**Answer:** At Walgreens, I built a GenAI-powered knowledge assistant for internal pharmacy teams. The system follows a RAG architecture - we ingest policy documents, chunk them into 800-1000 token segments, generate embeddings using OpenAI models, and store them in Pinecone for vector search. When users ask questions, the query is embedded, relevant chunks are retrieved, and GPT-4 generates context-grounded answers with citations. I wrapped this in a FastAPI microservice and deployed it on Azure Kubernetes Service with CI/CD. The system reduced manual search time by 60% and improved accuracy through prompt optimization and caching.

### Q: How did you decide your chunking strategy?

**Answer:** I treated chunking as balancing granularity and context. Too small chunks lose meaning; too large chunks reduce retrieval precision. I found 800-1000 tokens with 100-token overlap worked best for enterprise text at Walgreens. The overlap preserved sentence continuity so context doesn't break mid-paragraph. I used LangChain's RecursiveCharacterTextSplitter which respects sentence boundaries. For multi-paragraph documents, this approach maintained semantic coherence while keeping each chunk focused enough for accurate retrieval.

### Q: How do you handle hallucination or irrelevant responses?

**Answer:** I reduced hallucinations through multiple layers. First, I set temperature to 0.2 for more deterministic outputs. Second, I refined prompt templates to explicitly instruct "answer only using provided context". Third, I added a validation step using LangGraph nodes to check if the generated answer actually references the retrieved chunks. Fourth, I implemented source citations so users can verify answers. This multi-layered approach reduced hallucinations by about 35% in our Walgreens RAG system.

## 2. Accuracy & Optimization (Key Focus)

### Q: If you had to improve accuracy of an existing RAG system, what steps would you take?

**Answer:** I've actually done this at Walgreens. I'd start with a diagnostic approach - checking how documents are chunked, what embedding model is used, and what retrieval strategy is in place. Often issues come from misaligned chunking or embeddings not tuned to domain vocabulary. I'd run test queries to measure recall and precision, then iterate on chunk size, retriever filters, and embedding model. If the pharma complaint data is domain-heavy, I might use domain-specific embeddings from Hugging Face. On the model side, I'd ensure temperature and max_token limits are optimized for factual, concise answers. Each incremental change should be validated against a test set.

### Q: What parameters do you usually tune in a RAG pipeline?

**Answer:** At Walgreens, I tuned several parameters systematically. For chunking: size (800-1000 tokens), overlap (100 tokens), and separator strategy. For retrieval: top_k (I use 3-5), similarity threshold (0.7+), and metadata filtering. For generation: temperature (0.2 for factual, 0.7 for creative), max_tokens (depends on use case), and top_p (0.92). I also tuned prompt templates heavily - adding explicit instructions like "cite sources" and "answer only from context". These tuning efforts improved our accuracy by 25-30% based on validation metrics.

### Q: How do you handle performance-accuracy trade-offs?

**Answer:** I approach this by measuring both metrics independently. At Walgreens, we needed sub-2-second responses but couldn't sacrifice accuracy. I improved performance by reducing top_k from 10 to 3 (still retrieved enough context), caching frequent query embeddings in Redis, and using async FastAPI endpoints. For accuracy, I focused on chunk quality and prompt engineering rather than throwing more context at the model. The key was finding that sweet spot - 3 well-chosen chunks with tight prompts gave us 92% accuracy at 1.8s latency vs 95% accuracy at 5s latency with 10 chunks.

### Q: How can we improve the knowledge base quality itself?

**Answer:** The KB is the foundation - embeddings are only as good as the source data. I'd first check for duplicates, incomplete text, or irrelevant sections that could dilute retrieval. Sometimes even normalizing units or terminology improves vector search precision. For pharma complaints, I'd ensure 'OBI' and 'on-body injector' are treated as the same term using synonym mapping or text pre-processing. I'd also validate that complaint text is properly formatted - removing headers, footers, or repetitive patterns. A clean and consistent KB always leads to stronger embeddings and more accurate retrieval.

### Q: How do you identify whether errors come from retrieval or generation?

**Answer:** I debug this systematically by logging both stages separately. First, I check retrieval quality - are the top-k chunks actually relevant to the query? I look at similarity scores and manually review chunks. If chunks are wrong, it's a retrieval problem (embedding model, chunking, or metadata filtering). If chunks are correct but the answer is wrong, it's a generation problem (temperature, prompt template, or model hallucination). At Walgreens, I added validation nodes in LangGraph to catch this - one node validates retrieval quality, another validates answer grounding. This two-stage check helped us pinpoint issues quickly.

## 3. Python / API / Implementation Logic

### Q: Why did you choose FastAPI for your GenAI system?

**Answer:** I chose FastAPI because it's asynchronous and lightweight, which is crucial for handling multiple inference requests efficiently. This is especially important when working with long LLM response times. I structured the app with separate routers for embedding, retrieval, and generation endpoints, ensuring modularity and maintainability. FastAPI's built-in validation through Pydantic models helps maintain schema consistency for API responses. I also appreciate how easy it is to containerize and integrate with Azure DevOps pipelines. In terms of performance, I've seen a reduction in average response latency by about 30% compared to Flask.

### Q: How did you structure your FastAPI app?

**Answer:** I followed a clean modular structure at Walgreens. Created separate routers for different functionalities - `/embed` for embedding generation, `/retrieve` for vector search, `/ask` for full RAG flow. Each router has its own service layer with business logic, and Pydantic models for request/response validation. I separated concerns - embeddings.py handles OpenAI calls, retrieval.py handles Pinecone operations, prompts.py manages templates. This made testing easier and allowed us to swap components without breaking others. I also added middleware for logging, error handling, and HIPAA-compliant request tracking.

### Q: How do you handle asynchronous requests or concurrent queries?

**Answer:** FastAPI's async/await makes this natural. I marked all I/O-heavy operations as async - OpenAI API calls, Pinecone queries, database lookups. This prevents blocking and allows the server to handle multiple requests concurrently. At Walgreens, we tested with 50 concurrent users and maintained sub-2-second responses. I also implemented connection pooling for Pinecone and used httpx async client for OpenAI calls. For heavy workloads, I added a Redis queue to handle burst traffic and background processing for non-critical embeddings.

### Q: How do you cache frequent queries or embeddings?

**Answer:** I implemented two-level caching at Walgreens. For embeddings, I cached query embeddings in Redis with a 24-hour TTL - many users ask similar questions. For full responses, I cached the generated answer keyed by query hash, but with shorter TTL (1 hour) since context might change. This cut repeated embedding API calls by 70% and reduced average latency by 40%. I also cached the top-k retrieved chunks per query pattern. The tricky part was cache invalidation - when we updated the KB, I had to clear relevant caches. Used Redis pub/sub to coordinate cache clearing across multiple API instances.

## 4. LangChain / LangGraph / Agentic Systems

### Q: What are the key LangChain components you've used?

**Answer:** At Walgreens, I used several core LangChain components. Document loaders for ingesting PDFs and text files. RecursiveCharacterTextSplitter for chunking with overlap. OpenAIEmbeddings wrapper for generating vectors. VectorStoreRetriever for Pinecone integration. RetrievalQA chain for the basic RAG flow. I also used PromptTemplate for standardizing prompts and OutputParser for structured responses. For advanced flows, I used LangGraph to define custom nodes and edges. The modular design made it easy to swap components - like changing from Pinecone to Weaviate just required updating the VectorStore initialization.

### Q: What problem does LangGraph solve that LangChain doesn't?

**Answer:** LangChain chains are linear and hard to add conditional logic or loops. LangGraph gives you a graph-based framework with explicit nodes and edges, making complex workflows deterministic and auditable. At Walgreens, I used LangGraph for validation flows - retrieve → validate relevance → generate → check grounding → return or retry. Each node is a function, edges define transitions, and you can add conditions like "if confidence < 0.8, fetch more chunks". This level of control is crucial for production systems where you need explainability and error handling. It's like Airflow for LLM workflows.

### Q: Can you describe a LangGraph workflow you designed?

**Answer:** I designed a validation workflow at Walgreens. Node 1: Embed user query. Node 2: Retrieve top-5 chunks from Pinecone. Node 3: Validation node checks if chunks are actually relevant (similarity > 0.75). If yes, proceed to Node 4 (generation); if no, go to Node 5 (fallback retrieval with relaxed filters). Node 4: Generate answer with GPT-4. Node 6: Grounding check - does answer reference retrieved chunks? If yes, return; if no, regenerate with stricter prompt. This flow reduced bad answers by 45% compared to straight RetrievalQA chain. Each node logged state for debugging.

### Q: What are agents and how do they differ from standard chains?

**Answer:** Agents are LLM-driven controllers that decide what action or tool to use next based on the task. Unlike chains which follow a fixed sequence, agents plan, reason, and adapt dynamically. For example, an agent might decide to call a search API, then a calculator tool, then summarize - all based on the user query. LangChain's AgentExecutor handles this loop: LLM thinks → picks tool → executes → observes result → thinks again until done. I haven't deployed fully autonomous agents in production yet, but I understand the pattern. The tricky part is preventing infinite loops and ensuring reliability - that's why I prefer LangGraph's structured approach for production systems.

### Q: How would you prevent an agent from running in infinite loops?

**Answer:** I'd implement multiple safety mechanisms. First, set a max_iterations limit (like 10) in AgentExecutor. Second, track state - if the agent tries the same action 3 times without progress, trigger fallback. Third, add timeout enforcement at the execution level. Fourth, use LangGraph instead of pure agents for production - define explicit paths so the flow is deterministic. At Walgreens, I prevented loops by monitoring agent output for repetitive patterns and introducing a feedback mechanism to halt execution if it detects redundancy. This reduced unnecessary iterations by 40% and kept latency under 2 seconds.

## 5. MLOps / Deployment / Infrastructure

### Q: How did you containerize and deploy your RAG system?

**Answer:** I containerized the FastAPI service using Docker with a multi-stage build for smaller image size. Created Dockerfile with Python 3.11, installed dependencies from requirements.txt, and exposed port 8000. Built the image, pushed to Azure Container Registry, and deployed to AKS using Kubernetes manifests. Set up horizontal pod autoscaling based on CPU usage (scale 2-10 pods). Configured liveness and readiness probes for health checks. Integrated with Azure DevOps for CI/CD - on git push, pipeline runs tests, builds image, and deploys to staging, then prod after approval. This gave us zero-downtime deployments and easy rollbacks.

### Q: How does your CI/CD pipeline work?

**Answer:** At Walgreens, I set up Azure DevOps pipelines with multiple stages. Stage 1: Unit tests (pytest) and linting (flake8, black). Stage 2: Build Docker image and push to ACR. Stage 3: Deploy to staging AKS cluster. Stage 4: Run integration tests against staging. Stage 5: Manual approval gate. Stage 6: Deploy to production AKS. Each stage has gates - if tests fail, pipeline stops. I also added MLflow logging to track model versions deployed per release. This automated most of the deployment process and reduced deployment time from 2 hours to 15 minutes.

### Q: How do you manage secrets and API keys in production?

**Answer:** I use Azure Key Vault for secrets management at Walgreens. API keys for OpenAI, Pinecone credentials, and database passwords are stored in Key Vault and injected as environment variables at runtime. The FastAPI app reads from env vars, never hardcoded. For Kubernetes, I use Secrets mounted as volumes. I also rotate keys quarterly and use service principals with least-privilege access. All API calls are logged (without exposing keys) for audit trails. This approach kept us HIPAA-compliant and passed security reviews.

## 6. Compliance / Documentation / Governance

### Q: How do you ensure HIPAA compliance in your AI pipelines?

**Answer:** Since our data contained healthcare text at Walgreens, compliance was built into the design from day one. Before embedding, I added a PII scrubbing step using spaCy NER to mask patient names, IDs, dates, and addresses. We governed access using Unity Catalog for role-based control - only authorized users could query certain KB sections. Every retrieval call was logged with source metadata for traceability. I also ensured data at rest was encrypted in Pinecone and data in transit used TLS. All LLM outputs are traceable back to source documents for audit support. This kept us HIPAA-compliant and passed internal audits.

### Q: How do you maintain traceability from output back to source?

**Answer:** Every retrieval result includes metadata - source file, section, page number, timestamp. When generating the answer, I include these as citations. At Walgreens, I logged every API call with query hash, retrieved chunk IDs, and generated response for audit trails. Used Elasticsearch for log storage with 90-day retention. If a user flags an incorrect answer, we can trace back to which chunks were retrieved, what prompt was used, and what the model generated. This traceability was crucial for HIPAA compliance and quality improvement iterations.

## 7. Domain-Specific: Pharma Complaint RAG

### Q: How would you apply RAG to pharma complaint documents?

**Answer:** From what I understand, this system uses complaint documents as the knowledge base. That's a great use case because retrieval accuracy depends heavily on KB quality. I'd focus on improving chunking strategy for long complaint texts, cleaning repetitive patterns, and maybe exploring hybrid retrieval - semantic + keyword - to catch product-specific terms like drug names or device codes. We could evaluate domain-tuned embeddings from Hugging Face for medical terminology. I'd also add metadata filtering by complaint type, severity, or product category to narrow retrieval scope. These steps can significantly improve answer precision for pharma-specific queries.

### Q: What challenges might you face with domain-specific text?

**Answer:** Medical terminology and abbreviations can be tricky for general embeddings. At Walgreens, we handled this by maintaining a terminology mapping - 'OBI' and 'on-body injector' treated as synonyms. I'd also normalize drug names (generic vs brand). Another challenge is complaint text structure - often it's free-form with varying quality. I'd implement text cleaning to remove headers, footers, and repetitive legal disclaimers before chunking. For rare medical terms, I might combine semantic search with exact keyword matching (hybrid retrieval) to ensure we don't miss critical mentions.

### Q: How would you ensure responses are factual and compliant?

**Answer:** Multiple guardrails are needed. First, temperature set low (0.2) for deterministic outputs. Second, explicit prompt instruction: "answer only using provided context - if information is not in context, say you don't know". Third, add a validation node in LangGraph that checks if generated answer contains citations to retrieved chunks. Fourth, implement a confidence score based on retrieval similarity - if top chunk score is below 0.75, flag as uncertain. Fifth, for sensitive pharma data, add human-in-the-loop review for critical queries. This layered approach keeps responses factual and audit-ready.

## 8. Performance & Optimization

### Q: How would you improve performance of a RAG system?

**Answer:** I'd optimize multiple layers. For embeddings: cache frequent queries in Redis, batch embed multiple docs together, truncate very long inputs. For retrieval: reduce top_k from 10 to 3-5 (still enough context), use metadata pre-filtering to narrow search space, implement approximate nearest neighbor search. For generation: reduce max_tokens from 1000 to 500, use gpt-4o-mini instead of gpt-4, implement streaming for perceived speed. At Walgreens, these optimizations cut latency from 5s to 1.8s and handled 500 queries/day reliably. The biggest win was embedding caching - 70% of queries hit cache.

### Q: How do you measure retrieval quality?

**Answer:** I measure retrieval using precision and recall metrics. Precision: how many retrieved chunks are actually relevant? Recall: did we retrieve all relevant chunks in the KB? At Walgreens, I created a validation set of 100 queries with manually labeled relevant chunks. Then measured retrieval@k - what percentage of queries had relevant chunks in top-k results. I aimed for 85%+ recall at k=5. I also tracked similarity scores distribution - if average score is below 0.7, it means queries aren't matching well. Used this data to tune chunk size and embedding model selection.

## 9. LangChain Components & Implementation

### Q: How does LangGraph's node-edge architecture work?

**Answer:** LangGraph uses nodes for actions and edges for transitions. Each node is a Python function that takes state as input and returns updated state. Edges define flow - can be simple (always go to next node) or conditional (go to node A if condition, else node B). State is a typed dict that flows through the graph. At Walgreens, I defined nodes like: embed_query, retrieve_chunks, validate_relevance, generate_answer, check_grounding. Edges had conditions like "if similarity > 0.75, proceed to generate, else fetch more chunks". This gave us a deterministic, debuggable workflow unlike black-box agent loops.

### Q: Have you used hybrid retrieval (semantic + keyword)?

**Answer:** Yes, at Walgreens for policy queries containing specific codes or identifiers. Semantic search using embeddings is great for conceptual matching but can miss exact terms. I combined it with BM25 keyword search - retrieved top-5 from each, then re-ranked using reciprocal rank fusion. This hybrid approach improved precision by 20% for queries with technical codes or drug names. For pharma complaints, this would be valuable since product codes and specific drug names need exact matching while complaint descriptions need semantic understanding.

## 10. Deployment & Production Considerations

### Q: How do you ensure zero-downtime deployments?

**Answer:** I use blue-green deployment strategy on AKS at Walgreens. Keep old version (blue) running while deploying new version (green) to separate pods. Run smoke tests on green environment. Once validated, switch ingress traffic from blue to green using Kubernetes service selector update. Keep blue running for 30 minutes as fallback. If issues arise, instant rollback by switching traffic back. This approach gave us zero-downtime updates and safe rollback capability. Also used canary deployments for risky changes - route 10% traffic to new version first, monitor metrics, then gradually increase to 100%.

### Q: How do you monitor latency and throughput in production?

**Answer:** I instrumented our FastAPI app with Prometheus metrics at Walgreens. Tracked request count, latency percentiles (p50, p95, p99), error rates, and embedding cache hit rate. Set up Grafana dashboards showing real-time metrics. Added alerts if p95 latency exceeds 3 seconds or error rate exceeds 2%. Also logged slow queries for analysis. Used Application Insights for distributed tracing to see time breakdown - embedding: 0.8s, retrieval: 0.2s, generation: 1.5s. This helped pinpoint bottlenecks. Throughput-wise, our AKS cluster handled 500 queries/day with 2-pod minimum, scaling to 10 pods during peak hours.

## 11. Coordination & Team Collaboration

### Q: How do you coordinate with offshore teams?

**Answer:** At Walgreens, I coordinated with offshore data engineers regularly. I used daily stand-ups (30 minutes) to align on progress and blockers. For asynchronous communication, I used Slack for quick questions and Jira for task tracking. I made sure to document decisions and context in Confluence so offshore team had visibility. For code reviews, I provided detailed feedback with examples rather than just "fix this". I also scheduled weekly deep-dives to discuss architecture or complex issues. Time zone difference meant I had to be clear in written communication and available during overlap hours (early mornings).

### Q: How do you balance technical development and coordination duties?

**Answer:** I allocate time blocks at Walgreens - mornings for meetings and coordination (standup, client calls, offshore sync), afternoons for focused coding. I timebox coordination work to 30% of my day and development to 70%. For urgent blockers, I handle them immediately but delegate follow-ups. I also use async communication effectively - document decisions in Jira comments so offshore team can proceed without waiting for me. The key is being responsive but not letting coordination consume all development time. I protect 2-hour blocks daily for deep work on complex features.

## 12. Strategic Thinking & Problem Solving

### Q: What was your biggest challenge building a RAG pipeline?

**Answer:** The biggest challenge at Walgreens was balancing context length with relevance. Initially, I retrieved 10 chunks to ensure coverage, but this created two problems: token cost was high and generated answers became verbose. The tricky part was finding the right balance. I experimented with different top_k values and chunk sizes, measuring both accuracy and latency. Eventually settled on 3 chunks of 800 tokens each with tight prompt instructions. This maintained 92% accuracy while cutting latency by 40% and reducing API costs by $2K/month. The lesson was that more context doesn't always mean better answers.

### Q: What would you do in your first 30 days on this project?

**Answer:** First week: Deep dive into current architecture - understand chunking, embeddings, retrieval strategy, and prompt templates. Run test queries to baseline accuracy and latency. Second week: Identify quick wins - maybe tuning top_k, adjusting chunk overlap, or optimizing prompts. Document current system architecture for team clarity. Third week: Implement one significant improvement based on diagnosis - could be hybrid retrieval, better embeddings, or LangGraph validation flow. Fourth week: Set up monitoring and metrics framework so we can measure improvements objectively. Throughout, I'd sync with Avijit to understand offshore progress and ensure alignment on technical decisions.

### Q: Why do you think you're a good fit for this onsite GenAI coordination role?

**Answer:** I've built production RAG systems end-to-end at Walgreens - from data ingestion to deployment on AKS. I understand the full stack: Python, FastAPI, LangChain, LangGraph, vector DBs, LLMs, and cloud infrastructure. I've also coordinated with offshore teams, handled client communications, and balanced technical work with leadership. For this role, I can contribute both hands-on Python development and ensure smooth coordination between onsite and offshore. I'm comfortable explaining complex GenAI concepts to stakeholders and translating requirements into technical implementation. This project perfectly aligns with what I've built and want to scale next.

## 13. Communication Style Tips

### Opening Your Explanation (First 30 Seconds)
"Sure - I'll walk you through the RAG-based GenAI assistant I built at Walgreens. It's a Retrieval-Augmented Generation system that allows internal pharmacy teams to ask questions in natural language and get responses grounded in policy and compliance documents. I designed and deployed it end-to-end using LangChain, OpenAI embeddings, Pinecone vector DB, and FastAPI APIs - all hosted on Azure Kubernetes Service."

### When Asked About Unknown Topics
"I haven't directly implemented that yet, but I understand the concept. Based on my current experience, it would work similarly to how I've handled it in Azure. I can ramp up quickly once I get familiar with the AWS tools or environment."

### When Showing Confidence
"I'm really excited about this opportunity. The project aligns perfectly with my RAG and GenAI experience at Walgreens, and I'm confident I can contribute both to technical improvements and team coordination."

### Active Listening Acknowledgment
"Yes, that's exactly what we implemented too - we faced the same issue during retrieval tuning at Walgreens."

## 14. Key Metrics to Remember

- **Walgreens RAG System Performance:**
  - Reduced manual search time by 60%
  - Improved accuracy by 25-30% through tuning
  - Cut latency from 5s to 1.8s (40% improvement)
  - Reduced hallucinations by 35%
  - Achieved 92% accuracy at 1.8s latency
  - Embedding cache hit rate: 70%
  - Handled 500 queries/day
  - Cost savings: $2K/month through optimization
  - Deployment time: 6 hours to 45 minutes (reduced by 87%)

- **Technical Specs:**
  - Chunk size: 800-1000 tokens
  - Chunk overlap: 100 tokens
  - Top-k retrieval: 3-5 chunks
  - Temperature: 0.2 (factual) to 0.7 (creative)
  - Max tokens: 500-650
  - Similarity threshold: 0.75+
  - Cache TTL: 24 hours (embeddings), 1 hour (responses)

## 15. Architecture Components

**Complete RAG Flow:**
1. Document Ingestion (Databricks + PySpark)
2. Text Cleaning & Standardization
3. Chunking (LangChain RecursiveCharacterTextSplitter, 800-1000 tokens, 100 overlap)
4. Embedding Generation (OpenAI text-embedding-3-small)
5. Vector Storage (Pinecone with metadata)
6. Query Embedding
7. Retrieval (top-k similarity search with metadata filtering)
8. Prompt Formation (context + query + instructions)
9. Generation (GPT-4 with temperature 0.2)
10. Validation (LangGraph nodes for relevance and grounding checks)
11. Response Formatting (with citations)
12. API Exposure (FastAPI with async endpoints)
13. Deployment (Docker + AKS + CI/CD)
14. Monitoring (Prometheus + Grafana + Application Insights)

**Tools Stack:**
- **Data Processing**: PySpark, Databricks
- **RAG Framework**: LangChain, LangGraph
- **Embeddings**: OpenAI text-embedding-3-small
- **Vector DB**: Pinecone
- **LLM**: GPT-4, GPT-4o-mini
- **API**: FastAPI (async)
- **Caching**: Redis
- **Container**: Docker
- **Orchestration**: Azure Kubernetes Service (AKS)
- **CI/CD**: Azure DevOps
- **ML Versioning**: MLflow
- **Monitoring**: Prometheus, Grafana, Application Insights
- **Governance**: Unity Catalog, Azure Key Vault
- **Compliance**: PII scrubbing (spaCy), TLS encryption

## 16. Interview Day Mindset

### What Jacob Is Looking For:
✅ Do you understand how the system works logically?
✅ Can you diagnose, improve, and explain a RAG pipeline?
✅ Are you comfortable collaborating and documenting your work?
✅ Can you own both technical work and coordination?

### How You Should Sound:
✅ Calm and conversational (not memorizing)
✅ Confident in what you did and what you can learn
✅ Logical flow in each answer
✅ Use practical verbs: "I built", "I tested", "I tuned", "I fixed"
✅ Show learning: "The tricky part was...", "I learned that..."

### Key Positioning:
"I've built production RAG systems at Walgreens using LangChain and LangGraph. I'll be supporting this project both from the engineering side and helping coordinate between offshore and onsite to make delivery seamless."

### If Uncertain:
"I haven't implemented that yet, but I understand the concept. Based on my Azure experience, I'm confident it'll be an easy switch and I can ramp up quickly."

### Closing Strong:
"Overall, I'm confident I can contribute to improving the RAG system - both by optimizing retrieval accuracy and refining model behavior through prompt and parameter tuning. I've already applied these optimizations in production, so I'm comfortable experimenting, validating, and documenting changes."

## 17. Project Walkthrough - The WALKS Framework

### 5-Step Framework for "Walk me through your project" Questions

**W - What**: Give simple one-line overview
**A - Architecture**: Explain technical workflow clearly
**L - Logic / Your Role**: Talk about what you personally did
**K - Key Challenges**: Show you solved real problems
**S - Success / Metrics**: End with impact and improvement numbers

### Full Project Explanation (10-12 Sentences, 2 Minutes)

**Walgreens RAG Project:**
"At Walgreens, I've been working on a Generative AI knowledge assistant built using a Retrieval-Augmented Generation pipeline. The goal was to help internal pharmacy and operations teams quickly retrieve information from thousands of policy and procedure documents. The system uses LangChain and LangGraph to manage query flows - documents are chunked, embedded using OpenAI embeddings, stored in a vector database, and retrieved dynamically based on user questions. I built and optimized this full pipeline, from data ingestion and embedding generation to API integration and model evaluation. We deployed the model using FastAPI on Azure, containerized with Docker for scalability. I also implemented logging, prompt versioning, and a monitoring layer for token usage and response accuracy. One of the biggest challenges was tuning the chunking and retrieval logic to maintain context without losing precision. After several iterations, we improved factual accuracy by 45% and reduced average response latency by around 40%. Another key area I handled was compliance - implementing a PII scrubbing module to mask sensitive information before embedding. That ensured full HIPAA alignment. Overall, the solution turned manual document lookups into conversational queries and saved several minutes per search, making it much easier for teams to find reliable information quickly."

### Agentic AI / LangGraph Extension Project (10-12 Sentences)

**Q: Tell me about your agent workflow or LangGraph implementation**

**Answer:** "In addition to the core RAG system at Walgreens, I worked on extending it with an agentic workflow using LangGraph. The goal was to make our AI assistant more autonomous - able to decide which tool or API to use based on the user's question instead of following a fixed chain. LangGraph gave us a graph-based structure where each node represented a specific function - like document retrieval, validation, summarization, or reporting - and edges defined the possible decision paths. This made it easier to plan multi-step tasks dynamically. I designed the workflow so the agent could analyze a user query, call the retriever node first, validate the confidence of results, and then decide whether to run a summarizer or re-query the vector store. Each node was fully instrumented with logging for traceability. We also added a feedback loop where if confidence dropped below 0.8, the system automatically re-fetched additional chunks or used a fallback API. This significantly improved accuracy and response quality. I implemented this using LangChain tools, LangGraph orchestration, and OpenAI models, all running behind a FastAPI service deployed on Azure. The structure not only improved explainability but also reduced latency because redundant tool calls were avoided. Overall, the agentic upgrade improved task execution speed by about 30% and made debugging far easier since each node's inputs and outputs were logged. This project really helped us move from static RAG pipelines to adaptive AI workflows that think more like decision agents."

### Quick 60-Second Version

**Q: Can you explain your RAG project in 60 seconds?**
A: "I built a RAG system at Walgreens using LangChain and Pinecone. It ingests internal PDFs, chunks them into 800-token segments, and generates embeddings for semantic search. A FastAPI service retrieves relevant chunks per query and passes them to GPT-4 for grounded answers. I integrated LangGraph for validation and deployed it on Azure AKS via Docker + CI/CD. This reduced search effort by 60% and latency by 40%, while staying HIPAA-compliant."

### Quick 45-Second Agentic Version

**Q: Explain your LangGraph agentic workflow briefly**
A: "I extended our RAG system at Walgreens into an agentic workflow using LangGraph. Instead of following a fixed chain, the agent could choose which tool or API to use dynamically - for example, calling the retriever, validating results, and deciding whether to summarize or re-query. LangGraph's node-based design helped us log and trace every step, which made debugging simple. We also used confidence thresholds to trigger fallback searches when results dropped below 0.8. This agentic approach improved execution speed by around 30% and gave us better accuracy and explainability across the pipeline."

**Q: Why chunk overlap?**
A: "Overlap preserves sentence continuity so context doesn't break mid-paragraph. 100 tokens was optimal in our tests."

**Q: Why LangGraph?**
A: "To make the flow deterministic and auditable - each node handles one stage, so we can debug or log easily."

**Q: How do you measure accuracy?**
A: "We compare retrieved context similarity and response grounding accuracy - basically how often the model cites correct chunks."

**Q: What was your biggest challenge?**
A: "Initially, latency - we optimized by caching frequent embeddings and limiting context tokens."

**Q: What did you learn?**
A: "That prompt design and retrieval tuning matter as much as model selection for enterprise-grade GenAI."

## 18. Visual LangGraph Workflow Explanation

### 30-Second Whiteboard Sketch (Talk While Drawing)

**Visual Flow:**
```
[User Query]
     |
     v
[Preprocess Node]
(lang detect, PII mask, normalize)
     |
     v
[Retriever Node]
(Embed → Vector DB top_k=5, metadata filter)
     |
     v
[Validator Node]
(check relevance ≥ 0.8, dedupe, re-rank)
   |        \
   | ok      \ low confidence
   v          v
[Generator]  [Refetch/Expand]
(GPT w/     (increase top_k, widen filters)
 grounded
 context)
     |
     v
[Post-process]
(citations, guardrails, format)
     |
     v
[Response + Logs/Telemetry]
```

**One-Liner Explanation:** "Each rectangle is a LangGraph node; edges are conditions. If the validator's confidence drops below 0.8, we follow the 'expand' edge to refetch context; otherwise we generate, cite sources, and return."

### 90-Second Detailed Version

**Node Descriptions:**

1. **Preprocess Node**
   - Lowercase/normalize, strip HTML, light PII masking, handle abbreviations
   - Optional: intent detection (QA vs summarize vs classify)

2. **Retriever Node**
   - embed(query) → vector search (top_k=5, cosine similarity)
   - Metadata filters (domain=policy, product=XYZ, date≤today)
   - Hybrid boost (keyword BM25) for rare drug terms

3. **Validator Node**
   - Score overlap & semantic similarity; drop near-duplicates
   - Compute context confidence (mean/max of top-k scores + coverage)
   - **Branching:** if confidence < 0.8 → go to Refetch/Expand; else → Generator

4. **Refetch/Expand Node** (loop)
   - Increase top_k to 8-10, relax filters, add synonyms/aliases
   - Optional second retriever (hybrid) → back to Validator

5. **Generator Node**
   - Structured prompt: system guardrails + user + only validated chunks
   - temperature=0.2, max_tokens capped, require citations per claim
   - If missing citations → route back to Refetch once (safety loop)

6. **Post-process Node**
   - Format answer, attach citations, red-flag unsupported claims
   - Light redact if PII slipped through; finalize JSON

7. **Telemetry/Logging Node** (side-tap from every node)
   - Log: query id, retrieved chunk ids, scores, model+version, latency, tokens, cost
   - Emit metrics to dashboard: accuracy proxy, avg latency, refetch rate

**Key Edges and Conditions:**
- Validator.confidence < 0.8 → Refetch/Expand
- Generator.missing_citations → Refetch (1 retry max)
- Timeout or API error → graceful fallback (cached FAQ / smaller model)

**Why LangGraph Helps:**
- Nodes = single-purpose, testable steps
- Edges = explicit control flow (no hidden agent loops)
- Easy to trace: replay exact path (Preprocess → Retrieve → Validate → Refetch → Validate → Generate)

**Typical Settings:**
- Retriever: top_k=5 initially, expand to 8-10 on refetch, overlap-aware chunking (800-1000 tokens, 100 overlap)
- Thresholds: relevance 0.8; citation requirement on
- Caching: query+embedding cache; popular answers memoized with TTL
- Cost/latency monitoring: track tokens, alert if refetch rate > 20%

### Clean Closing Statement

"Think of it as a guarded, branching pipeline: retrieve → verify → (maybe expand) → generate → validate formatting. Every step is logged, every decision is explicit, so we get grounded answers with predictable behavior. This deterministic approach is crucial for production GenAI systems where explainability and reliability matter."

### Quick Verbal Explanation (If Asked to Describe Flow)

"At Walgreens, my LangGraph workflow starts with preprocessing the user query. Then we embed and retrieve top-5 chunks from our vector DB. The validator node checks if confidence is above 0.8 - if yes, we proceed to generation with GPT-4; if no, we expand retrieval to get more context. After generation, we post-process to add citations and ensure PII compliance. Every node logs state for debugging, and we can replay the exact decision path. This structure gave us 45% better accuracy and made the system auditable for HIPAA requirements."

