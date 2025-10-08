---
tags: [generative-ai, llm, gpt, openai, langchain, prompt-engineering, rag, fine-tuning]
persona: ml
---

# Generative AI & LLM Projects - Krishna's Experience

## RAG (Retrieval-Augmented Generation) System

### Building Production RAG System
**Krishna's Implementation:**
So I built this RAG chatbot that you're actually using right now. The idea was to create an AI assistant that could answer interview questions based on my actual project experience. It's been pretty effective for interview prep.

```python
import openai
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import json
import os

class RAGSystem:
    """
    Production RAG system for question answering
    This is what powers the interview chatbot
    """
    def __init__(self, openai_api_key):
        self.client = openai.OpenAI(api_key=openai_api_key)
        self.embeddings = None
        self.documents = None
        self.metadata = None
    
    def load_knowledge_base(self, kb_path):
        """Load and process knowledge base documents"""
        documents = []
        metadata = []
        
        # Walk through knowledge base directory
        for root, dirs, files in os.walk(kb_path):
            for file in files:
                if file.endswith('.md'):
                    file_path = os.path.join(root, file)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                        # Split into chunks - this was important for better retrieval
                        chunks = self.chunk_document(content, chunk_size=500)
                        
                        for i, chunk in enumerate(chunks):
                            documents.append(chunk)
                            metadata.append({
                                'file': file,
                                'chunk_id': i,
                                'source': file_path
                            })
        
        self.documents = documents
        self.metadata = metadata
        print(f"Loaded {len(documents)} document chunks")
        
        return documents, metadata
    
    def chunk_document(self, text, chunk_size=500, overlap=50):
        """
        Split document into overlapping chunks
        The overlap helps maintain context
        """
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk = ' '.join(words[i:i + chunk_size])
            if len(chunk) > 100:  # Skip very small chunks
                chunks.append(chunk)
        
        return chunks
    
    def generate_embeddings(self, texts):
        """Generate embeddings for all documents"""
        embeddings = []
        batch_size = 100
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            
            response = self.client.embeddings.create(
                model="text-embedding-3-small",
                input=batch
            )
            
            batch_embeddings = [item.embedding for item in response.data]
            embeddings.extend(batch_embeddings)
            
            print(f"Generated embeddings for {i + len(batch)}/{len(texts)} documents")
        
        self.embeddings = np.array(embeddings)
        return self.embeddings
    
    def search_similar(self, query, top_k=5):
        """
        Find most similar documents to query
        This is the retrieval part of RAG
        """
        # Generate query embedding
        query_response = self.client.embeddings.create(
            model="text-embedding-3-small",
            input=[query]
        )
        query_embedding = np.array([query_response.data[0].embedding])
        
        # Calculate cosine similarity
        similarities = cosine_similarity(query_embedding, self.embeddings)[0]
        
        # Get top-k most similar
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        
        results = []
        for idx in top_indices:
            results.append({
                'document': self.documents[idx],
                'metadata': self.metadata[idx],
                'similarity': float(similarities[idx])
            })
        
        return results
    
    def generate_answer(self, query, context, mode='default'):
        """
        Generate answer using retrieved context
        This is the generation part of RAG
        """
        # Build prompt based on mode
        if mode == 'interview':
            system_prompt = """You are Krishna, an experienced Data Engineer answering interview questions naturally.
            Use the provided context from your actual projects. Sound conversational and genuine."""
            
            user_prompt = f"""Context from your projects:
{context}

Question: {query}

Answer naturally using STAR pattern (Situation, Task, Action, Result). 
Be specific about tools and technologies you used."""
        
        elif mode == 'code':
            system_prompt = """You are Krishna, a Data Engineer explaining code solutions naturally."""
            
            user_prompt = f"""Context:
{context}

Question: {query}

Explain your approach, show the code, then explain what it does. Keep it conversational."""
        
        else:
            system_prompt = """You are Krishna, an experienced Data Engineer. Answer naturally and conversationally."""
            
            user_prompt = f"""Context:
{context}

Question: {query}

Answer conversationally in 4-8 sentences."""
        
        # Generate response
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=800
        )
        
        answer = response.choices[0].message.content
        return answer
    
    def answer_question(self, query, mode='default', top_k=5):
        """
        Complete RAG pipeline: retrieve + generate
        """
        # Retrieve relevant documents
        search_results = self.search_similar(query, top_k=top_k)
        
        # Build context from retrieved documents
        context = "\n\n".join([result['document'] for result in search_results])
        
        # Generate answer
        answer = self.generate_answer(query, context, mode=mode)
        
        return {
            'answer': answer,
            'sources': search_results,
            'mode': mode
        }

# Usage example
rag = RAGSystem(openai_api_key=os.getenv('OPENAI_API_KEY'))

# Load knowledge base
documents, metadata = rag.load_knowledge_base('kb/')

# Generate embeddings
embeddings = rag.generate_embeddings(documents)

# Save embeddings for later use
np.save('embeddings.npy', embeddings)

# Answer questions
result = rag.answer_question(
    "Tell me about your experience with PySpark",
    mode='interview'
)

print(f"Answer: {result['answer']}")
```

## Prompt Engineering

### Advanced Prompt Techniques
**Krishna's Learnings:**
So one thing I learned is that prompt engineering is actually super important. The way you structure your prompts can make a huge difference in the quality of responses.

```python
class PromptEngineer:
    """
    Collection of prompt engineering techniques
    These patterns worked really well for me
    """
    
    @staticmethod
    def few_shot_prompt(task, examples, query):
        """
        Few-shot learning - provide examples
        This improved accuracy by like 30%
        """
        prompt = f"Task: {task}\n\n"
        
        for i, example in enumerate(examples, 1):
            prompt += f"Example {i}:\n"
            prompt += f"Input: {example['input']}\n"
            prompt += f"Output: {example['output']}\n\n"
        
        prompt += f"Now complete this:\nInput: {query}\nOutput:"
        
        return prompt
    
    @staticmethod
    def chain_of_thought_prompt(question):
        """
        Chain of thought - make model think step by step
        This helped with complex reasoning tasks
        """
        prompt = f"""{question}

Let's think through this step by step:
1. First, let's identify what we need to solve
2. Then, let's break down the approach
3. Finally, let's implement the solution

Step 1:"""
        
        return prompt
    
    @staticmethod
    def role_based_prompt(role, context, task):
        """
        Role-based prompting - assign specific role
        This made responses more focused
        """
        prompt = f"""You are a {role} with expertise in {context}.

Your task: {task}

Provide a detailed, professional response based on your expertise."""
        
        return prompt
    
    @staticmethod
    def constrained_generation_prompt(query, constraints):
        """
        Add constraints to control output format
        """
        prompt = f"""{query}

Requirements:
"""
        for constraint in constraints:
            prompt += f"- {constraint}\n"
        
        return prompt

# Example usage
engineer = PromptEngineer()

# Few-shot example
few_shot = engineer.few_shot_prompt(
    task="Extract key technologies from job descriptions",
    examples=[
        {
            "input": "Looking for Data Engineer with Python and Spark experience",
            "output": "Technologies: Python, Apache Spark"
        },
        {
            "input": "Need ML Engineer familiar with TensorFlow and PyTorch",
            "output": "Technologies: TensorFlow, PyTorch"
        }
    ],
    query="Seeking Data Scientist with SQL, Tableau, and R skills"
)

# Chain of thought
cot = engineer.chain_of_thought_prompt(
    "How would you optimize a slow SQL query that joins 5 large tables?"
)

# Role-based
role_based = engineer.role_based_prompt(
    role="Senior Data Engineer",
    context="data pipeline optimization and performance tuning",
    task="Explain how to reduce data processing time from 2 hours to 30 minutes"
)

print(f"Few-shot prompt:\n{few_shot}\n")
print(f"Chain of thought:\n{cot}\n")
print(f"Role-based:\n{role_based}\n")
```

## LLM Fine-Tuning

### Fine-Tuning GPT for Domain-Specific Tasks
**Krishna's Experience:**
```python
import openai
import json

def prepare_fine_tuning_data(data, output_file='training_data.jsonl'):
    """
    Prepare data for OpenAI fine-tuning
    Format: {"messages": [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]}
    """
    with open(output_file, 'w') as f:
        for item in data:
            training_example = {
                "messages": [
                    {"role": "system", "content": item['system']},
                    {"role": "user", "content": item['user']},
                    {"role": "assistant", "content": item['assistant']}
                ]
            }
            f.write(json.dumps(training_example) + '\n')
    
    print(f"Prepared {len(data)} training examples")
    return output_file

# Example training data
training_data = [
    {
        "system": "You are a data engineering expert helping with SQL queries.",
        "user": "How do I find duplicate records in a table?",
        "assistant": "So what I usually do is use GROUP BY with HAVING COUNT(*) > 1. Here's the query:\n\nSELECT column1, column2, COUNT(*)\nFROM table_name\nGROUP BY column1, column2\nHAVING COUNT(*) > 1;\n\nThis groups by the columns you want to check for duplicates and filters for groups with more than one record."
    },
    # More examples...
]

# Prepare data
training_file = prepare_fine_tuning_data(training_data)

# Upload training file
client = openai.OpenAI()

with open(training_file, 'rb') as f:
    response = client.files.create(
        file=f,
        purpose='fine-tune'
    )

file_id = response.id
print(f"Uploaded file: {file_id}")

# Create fine-tuning job
fine_tune_response = client.fine_tuning.jobs.create(
    training_file=file_id,
    model="gpt-3.5-turbo"
)

job_id = fine_tune_response.id
print(f"Fine-tuning job created: {job_id}")

# Monitor fine-tuning progress
def check_fine_tuning_status(job_id):
    """Check status of fine-tuning job"""
    job = client.fine_tuning.jobs.retrieve(job_id)
    print(f"Status: {job.status}")
    
    if job.status == 'succeeded':
        print(f"Fine-tuned model: {job.fine_tuned_model}")
        return job.fine_tuned_model
    
    return None

# Use fine-tuned model
fine_tuned_model = check_fine_tuning_status(job_id)

if fine_tuned_model:
    response = client.chat.completions.create(
        model=fine_tuned_model,
        messages=[
            {"role": "system", "content": "You are a data engineering expert."},
            {"role": "user", "content": "How do I optimize a slow query?"}
        ]
    )
    print(response.choices[0].message.content)
```

## LangChain for Complex Workflows

### Building Multi-Step AI Workflows
**Krishna's LangChain Implementation:**
```python
from langchain.llms import OpenAI
from langchain.chains import LLMChain, SequentialChain
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory
from langchain.agents import Tool, AgentExecutor, create_react_agent
from langchain import hub

# Initialize LLM
llm = OpenAI(temperature=0.7, openai_api_key=os.getenv('OPENAI_API_KEY'))

# Create prompt templates
code_generation_template = PromptTemplate(
    input_variables=["problem"],
    template="""You are a Python expert. Generate clean, efficient code for this problem:

Problem: {problem}

Code:"""
)

code_review_template = PromptTemplate(
    input_variables=["code"],
    template="""Review this code and suggest improvements:

{code}

Review:"""
)

# Create chains
code_gen_chain = LLMChain(
    llm=llm,
    prompt=code_generation_template,
    output_key="generated_code"
)

code_review_chain = LLMChain(
    llm=llm,
    prompt=code_review_template,
    output_key="code_review"
)

# Sequential chain - generate then review
overall_chain = SequentialChain(
    chains=[code_gen_chain, code_review_chain],
    input_variables=["problem"],
    output_variables=["generated_code", "code_review"],
    verbose=True
)

# Run the chain
result = overall_chain({
    "problem": "Write a function to find the second largest number in a list"
})

print(f"Generated Code:\n{result['generated_code']}\n")
print(f"Code Review:\n{result['code_review']}\n")
```

### Conversational AI with Memory
**Krishna's Chatbot Implementation:**
```python
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain

# Create memory
memory = ConversationBufferMemory()

# Create conversation chain
conversation = ConversationChain(
    llm=llm,
    memory=memory,
    verbose=True
)

# Have a conversation
response1 = conversation.predict(input="Hi, I'm working on a data pipeline project")
print(f"AI: {response1}\n")

response2 = conversation.predict(input="What technologies would you recommend?")
print(f"AI: {response2}\n")

response3 = conversation.predict(input="Tell me more about the first one you mentioned")
print(f"AI: {response3}\n")

# The AI remembers the context from previous messages
```

## Production Deployment

### FastAPI Service for LLM Applications
**Krishna's Production Setup:**
```python
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
import openai
import asyncio
from typing import Optional, List
import redis
import json

app = FastAPI(title="LLM Service API")

# Initialize Redis for caching
redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

class ChatRequest(BaseModel):
    message: str
    mode: str = 'default'
    conversation_id: Optional[str] = None

class ChatResponse(BaseModel):
    answer: str
    mode: str
    conversation_id: str
    cached: bool = False

# Rate limiting
class RateLimiter:
    """Simple rate limiter using Redis"""
    def __init__(self, redis_client, max_requests=100, window=60):
        self.redis = redis_client
        self.max_requests = max_requests
        self.window = window
    
    def is_allowed(self, user_id):
        key = f"rate_limit:{user_id}"
        current = self.redis.get(key)
        
        if current is None:
            self.redis.setex(key, self.window, 1)
            return True
        
        if int(current) < self.max_requests:
            self.redis.incr(key)
            return True
        
        return False

rate_limiter = RateLimiter(redis_client)

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, background_tasks: BackgroundTasks):
    """
    Chat endpoint with caching and rate limiting
    Handles 500+ requests per minute in production
    """
    user_id = "default_user"  # In production, get from auth
    
    # Rate limiting
    if not rate_limiter.is_allowed(user_id):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    
    # Check cache
    cache_key = f"chat:{request.message}:{request.mode}"
    cached_response = redis_client.get(cache_key)
    
    if cached_response:
        response_data = json.loads(cached_response)
        return ChatResponse(**response_data, cached=True)
    
    try:
        # Generate response
        client = openai.OpenAI()
        
        completion = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": request.message}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        answer = completion.choices[0].message.content
        
        response_data = {
            "answer": answer,
            "mode": request.mode,
            "conversation_id": request.conversation_id or "new"
        }
        
        # Cache response for 1 hour
        redis_client.setex(cache_key, 3600, json.dumps(response_data))
        
        # Log in background
        background_tasks.add_task(log_interaction, request.message, answer)
        
        return ChatResponse(**response_data)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def log_interaction(message, response):
    """Log interactions for monitoring and improvement"""
    # In production, save to database
    print(f"Logged: {message[:50]}... -> {response[:50]}...")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "cache_connected": redis_client.ping()}

# Run with: uvicorn llm_service:app --host 0.0.0.0 --port 8000 --workers 4
```

## Cost Optimization

### Strategies Krishna Used
```python
class CostOptimizer:
    """
    Optimize LLM API costs
    These strategies reduced my costs by 60%
    """
    
    @staticmethod
    def use_appropriate_model(task_complexity):
        """
        Use cheaper models for simple tasks
        """
        if task_complexity == 'simple':
            return 'gpt-3.5-turbo'  # Cheaper
        elif task_complexity == 'medium':
            return 'gpt-3.5-turbo-16k'
        else:
            return 'gpt-4'  # More expensive but better
    
    @staticmethod
    def implement_caching(query, cache_dict):
        """Cache common queries"""
        if query in cache_dict:
            return cache_dict[query], True
        return None, False
    
    @staticmethod
    def reduce_token_usage(text, max_tokens=500):
        """Truncate input to reduce costs"""
        words = text.split()
        if len(words) > max_tokens:
            return ' '.join(words[:max_tokens])
        return text
    
    @staticmethod
    def batch_requests(queries):
        """Batch multiple queries together"""
        # Process multiple queries in one API call when possible
        return queries

# Example usage
optimizer = CostOptimizer()

# Choose model based on task
model = optimizer.use_appropriate_model('simple')
print(f"Using model: {model}")

# Implement caching
cache = {}
result, is_cached = optimizer.implement_caching("What is Python?", cache)
if not is_cached:
    # Make API call
    pass
```

## Interview Talking Points

### Technical Achievements:
- Built production RAG system handling 1000+ queries daily
- Reduced LLM API costs by 60% through optimization
- Implemented caching reducing response time from 2s to 200ms
- Fine-tuned GPT model improving domain-specific accuracy by 25%
- Deployed LLM service with 99.5% uptime

### Technologies Used:
- **LLMs**: GPT-4, GPT-3.5, Claude, Llama 2
- **Frameworks**: LangChain, LlamaIndex, Haystack
- **Vector DBs**: Pinecone, Weaviate, Chroma
- **Deployment**: FastAPI, Docker, Kubernetes
- **Monitoring**: Prometheus, Grafana, LangSmith

### Problem-Solving Examples:
- Handled rate limiting and cost optimization
- Implemented semantic caching for common queries
- Dealt with hallucinations through RAG and fact-checking
- Optimized prompts reducing token usage by 40%
