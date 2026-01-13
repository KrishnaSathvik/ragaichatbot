#!/usr/bin/env python3
"""
Fast embedding generation script with performance optimizations.
"""

import os
import json
import numpy as np
from pathlib import Path
from openai import OpenAI
from tqdm import tqdm
import concurrent.futures
from functools import lru_cache

# Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is required")

client = OpenAI(api_key=OPENAI_API_KEY)

@lru_cache(maxsize=1000)
def get_embedding_cached(text: str) -> tuple:
    """Cached embedding generation."""
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text,
        timeout=5.0
    )
    return tuple(response.data[0].embedding)

def parse_frontmatter_persona(content: str) -> str:
    """Extract persona from YAML frontmatter if present."""
    if content.startswith('---'):
        end_idx = content.find('---', 3)
        if end_idx > 0:
            frontmatter = content[3:end_idx]
            for line in frontmatter.split('\n'):
                if line.strip().startswith('persona:'):
                    return line.split(':')[1].strip()
    return None

# Topic mapping from titles to canonical topics
TITLE_TO_TOPIC = {
    # Packages
    "packages": "packages", "spec vs body": "packages", "why use packages": "packages",
    "package specification": "packages", "package body": "packages",
    # Bulk operations
    "bulk collect": "bulk", "forall": "bulk", "save exceptions": "bulk",
    "indices of": "bulk", "values of": "bulk", "bulk operations safely": "bulk",
    # Exceptions
    "exception": "exceptions", "error handling": "exceptions", "raise": "exceptions",
    "when others": "exceptions", "autonomous": "exceptions", "logging errors": "exceptions",
    # Cursors
    "cursor": "cursors", "ref cursor": "cursors", "sys_refcursor": "cursors",
    "implicit": "cursors", "explicit": "cursors",
    # Tuning (execution plans, DBMS_XPLAN, AWR, ASH, waits, parse)
    "dbms_xplan": "tuning", "display_cursor": "tuning", "explain plan": "tuning",
    "sql_id": "tuning", "execution plan": "tuning", "allstats": "tuning",
    "awr": "tuning", "ash": "tuning", "awr vs ash": "tuning",
    "wait event": "tuning", "hard parse": "tuning", "soft parse": "tuning",
    "cardinality": "tuning", "statistics": "tuning", "optimizer": "tuning",
    "nested loop": "tuning", "hash join": "tuning", "plan instability": "tuning",
    "latch": "tuning", "contention": "tuning", "tune a slow": "tuning",
    "bind variable": "tuning",
    # Performance (indexing issues, PLS_INTEGER)
    "trunc": "performance", "indexed column": "performance", "function on indexed": "performance",
    "index not": "performance", "pls_integer": "performance", "row-by-row": "performance",
    "performance": "performance", "partition": "performance", "partitioning": "performance",
    # Triggers
    "trigger": "triggers", "mutating": "triggers", "compound trigger": "triggers",
    "instead of": "triggers",
    # Dynamic SQL
    "execute immediate": "dyn_sql", "dynamic sql": "dyn_sql",
    # Collections
    "collection": "collections", "varray": "collections", "nested table": "collections",
    "associative": "collections", "pipelined": "collections",
    # Analytics
    "window": "analytics", "analytic": "analytics", "row_number": "analytics",
    "rank": "analytics", "dense_rank": "analytics", "lag": "analytics", "lead": "analytics",
    # Transactions (locks, deadlocks, commit, ORA-01555)
    "transaction": "transactions", "commit": "transactions", "rollback": "transactions",
    "blocking": "transactions", "deadlock": "transactions", "lock": "transactions",
    "ora-01555": "transactions", "snapshot too old": "transactions",
    # Scheduler
    "scheduler": "scheduler", "dbms_scheduler": "scheduler", "job": "scheduler",
    # Procedures/Functions
    "procedure": "procedures", "function": "procedures",
    # Types
    "percent type": "types", "rowtype": "types",
    # DBA collaboration / scope
    "dba territory": "dba_scope", "collaborate with dba": "dba_scope",
    "check first": "dba_scope", "scope anchor": "dba_scope", "rac": "dba_scope",
    # Dependencies
    "dependencies": "dependencies", "invalidat": "dependencies",
}

def extract_title_and_topic(text: str) -> tuple:
    """Extract title from H2 header and map to topic."""
    import re
    # Find first H2 header
    match = re.search(r'^## (.+?)$', text, re.MULTILINE)
    if match:
        title = match.group(1).strip()
        title_lower = title.lower()
        # Find matching topic
        for key, topic in TITLE_TO_TOPIC.items():
            if key in title_lower:
                return title, topic
        return title, None
    return None, None

def read_markdown_files(directory: str, persona: str, file_filter: str = None) -> list:
    """Read markdown files and create chunks."""
    chunks = []
    directory_path = Path(directory)
    
    if not directory_path.exists():
        print(f"Directory {directory} does not exist")
        return chunks
    
    for file_path in directory_path.rglob("*.md"):
        # Apply file filter if specified
        if file_filter:
            if file_filter == "plsql" and "plsql" not in file_path.name.lower():
                continue
            elif file_filter == "no_plsql" and "plsql" in file_path.name.lower():
                continue
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Try to get persona from frontmatter, fallback to parameter
            file_persona = parse_frontmatter_persona(content) or persona
            
            # Enhanced chunking - split by H2 headers for interview answer files
            if 'interview_answers' in file_path.name or 'plsql' in file_path.name.lower():
                # Split by H2 headers for finer granularity
                sections = content.split('\n## ')
                for i, section in enumerate(sections):
                    if i > 0:
                        section = '## ' + section
                    
                    if len(section.strip()) > 50:
                        # Extract title and topic for better retrieval
                        title, topic = extract_title_and_topic(section)
                        chunks.append({
                            "text": section.strip(),
                            "metadata": {
                                "file_name": file_path.name,
                                "file_path": str(file_path),
                                "persona": file_persona,
                                "section": i,
                                "title": title,
                                "topic": topic
                            }
                        })
            else:
                # Default: split by H1 headers
                sections = content.split('\n# ')
                for i, section in enumerate(sections):
                    if i > 0:
                        section = '# ' + section
                    
                    if len(section.strip()) > 50:
                        chunks.append({
                            "text": section.strip(),
                            "metadata": {
                                "file_name": file_path.name,
                                "file_path": str(file_path),
                                "persona": file_persona,
                                "section": i
                            }
                        })
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
    
    return chunks

def generate_embeddings_batch(texts: list, batch_size: int = 50) -> list:
    """Generate embeddings in batches for better performance."""
    embeddings = []
    
    for i in tqdm(range(0, len(texts), batch_size), desc="Generating embeddings"):
        batch = texts[i:i + batch_size]
        
        # Use concurrent processing for batch
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_text = {executor.submit(get_embedding_cached, text): text for text in batch}
            
            for future in concurrent.futures.as_completed(future_to_text):
                try:
                    embedding = future.result()
                    embeddings.append(np.array(embedding, dtype=np.float32))
                except Exception as e:
                    print(f"Error generating embedding: {e}")
                    # Add zero embedding as fallback
                    embeddings.append(np.zeros(1536, dtype=np.float32))
    
    return embeddings

def main():
    print("🚀 Starting FAST embedding generation...")
    
    # Read all chunks
    all_chunks = []
    
    # Krishna DE
    print("📁 Processing Krishna DE...")
    krishna_de_chunks = read_markdown_files("kb_krishna/data_engineering", "de")
    all_chunks.extend(krishna_de_chunks)
    print(f"   - DE: {len(krishna_de_chunks)} chunks")
    
    # Krishna AI
    print("📁 Processing Krishna AI...")
    krishna_ai_chunks = read_markdown_files("kb_krishna/ai_ml", "ai")
    all_chunks.extend(krishna_ai_chunks)
    print(f"   - AI: {len(krishna_ai_chunks)} chunks")
    
    # Tejuu Analytics
    print("📁 Processing Tejuu Analytics...")
    tejuu_analytics_chunks = read_markdown_files("kb_tejuu/analytics_mode", "analytics")
    all_chunks.extend(tejuu_analytics_chunks)
    print(f"   - Analytics: {len(tejuu_analytics_chunks)} chunks")
    
    # Tejuu Business
    print("📁 Processing Tejuu Business...")
    tejuu_business_chunks = read_markdown_files("kb_tejuu/business_mode", "business")
    all_chunks.extend(tejuu_business_chunks)
    print(f"   - Business: {len(tejuu_business_chunks)} chunks")
    
    print(f"\n📊 TOTAL CHUNKS: {len(all_chunks)}")
    
    # Generate embeddings with batching
    print("\n🔄 Generating embeddings (optimized)...")
    texts = [chunk["text"] for chunk in all_chunks]
    embeddings = generate_embeddings_batch(texts, batch_size=25)  # Smaller batches for stability
    
    # Convert to numpy array
    embeddings_array = np.array(embeddings, dtype=np.float32)
    print(f"✅ Generated embeddings shape: {embeddings_array.shape}")
    
    # Create metadata
    metadata = []
    for i, chunk in enumerate(all_chunks):
        metadata.append({
            "id": f"chunk_{i}",
            "text": chunk["text"],
            "metadata": chunk["metadata"]
        })
    
    # Save files
    print("\n💾 Saving files...")
    
    # Save metadata
    with open("api/meta.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    print("✅ Saved metadata")
    
    # Save embeddings
    np.save("api/embeddings.npy", embeddings_array)
    print("✅ Saved embeddings")
    
    # File sizes
    meta_size = os.path.getsize("api/meta.json") / (1024 * 1024)
    emb_size = os.path.getsize("api/embeddings.npy") / (1024 * 1024)
    
    print(f"\n📊 File sizes:")
    print(f"   - Embeddings: {emb_size:.2f} MB")
    print(f"   - Metadata: {meta_size:.2f} MB")
    
    print("\n🎉 Fast embedding generation complete!")

if __name__ == "__main__":
    main()
