#!/usr/bin/env python3
"""
Knowledge ingestion script for RAG chatbot.
Reads .md/.txt files from kb/ai_ml/ and kb/data_eng/, chunks them,
gets embeddings, and builds a FAISS vector index.
"""

import os
import json
import re
from pathlib import Path
from typing import List, Dict, Any
import tiktoken
import numpy as np
import faiss
from openai import OpenAI
from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv()

# Configuration
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
EMBEDDING_MODEL = "text-embedding-3-small"
OPENAI_CLIENT = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def extract_frontmatter(content: str) -> tuple[Dict[str, Any], str]:
    """Extract YAML frontmatter from markdown content."""
    if not content.startswith('---'):
        return {}, content
    
    parts = content.split('---', 2)
    if len(parts) < 3:
        return {}, content
    
    frontmatter_text = parts[1].strip()
    body = parts[2].strip()
    
    # Simple YAML parsing for tags
    tags = []
    for line in frontmatter_text.split('\n'):
        if line.strip().startswith('tags:'):
            # Extract tags from various formats
            tag_line = line.split('tags:')[1].strip()
            if tag_line.startswith('[') and tag_line.endswith(']'):
                tags = [t.strip().strip('"\'') for t in tag_line[1:-1].split(',')]
            elif ',' in tag_line:
                tags = [t.strip().strip('"\'') for t in tag_line.split(',')]
            else:
                tags = [tag_line.strip().strip('"\'')]
    
    metadata = {'tags': tags} if tags else {}
    return metadata, body

def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """Split text into overlapping chunks."""
    # Use tiktoken to count tokens more accurately
    encoding = tiktoken.get_encoding("cl100k_base")
    
    chunks = []
    tokens = encoding.encode(text)
    
    start = 0
    while start < len(tokens):
        end = min(start + chunk_size, len(tokens))
        chunk_tokens = tokens[start:end]
        chunk_text = encoding.decode(chunk_tokens)
        chunks.append(chunk_text)
        
        if end == len(tokens):
            break
        start = end - overlap
    
    return chunks

def get_embedding(text: str) -> List[float]:
    """Get OpenAI embedding for text."""
    response = OPENAI_CLIENT.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text
    )
    return response.data[0].embedding

def process_kb_directory(kb_path: Path) -> List[Dict[str, Any]]:
    """Process all .md/.txt files in a knowledge base directory."""
    documents = []
    
    for file_path in kb_path.rglob("*"):
        if file_path.suffix.lower() not in ['.md', '.txt']:
            continue
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract frontmatter and body
            metadata, body = extract_frontmatter(content)
            
            # Determine persona from directory path
            persona = "ai" if "ai_ml" in str(file_path) else "de"
            metadata['persona'] = persona
            metadata['file_path'] = str(file_path.relative_to(Path("kb_krishna")))
            metadata['file_name'] = file_path.name
            
            # Chunk the text
            chunks = chunk_text(body)
            
            for i, chunk in enumerate(chunks):
                if chunk.strip():  # Skip empty chunks
                    doc = {
                        'id': f"{file_path.stem}_{i}",
                        'text': chunk.strip(),
                        'metadata': metadata.copy()
                    }
                    documents.append(doc)
                    
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
    
    return documents

def build_faiss_index(documents: List[Dict[str, Any]]) -> tuple[faiss.Index, List[Dict[str, Any]]]:
    """Build FAISS index from documents."""
    if not documents:
        raise ValueError("No documents to index")
    
    print(f"Getting embeddings for {len(documents)} chunks...")
    embeddings = []
    metadata_list = []
    
    # Use tqdm for progress tracking
    for doc in tqdm(documents, desc="Processing chunks", unit="chunk"):
        embedding = get_embedding(doc['text'])
        embeddings.append(embedding)
        metadata_list.append({
            'id': doc['id'],
            'text': doc['text'],
            'metadata': doc['metadata']
        })
    
    # Convert to numpy array
    embeddings_array = np.array(embeddings).astype('float32')
    
    # Build FAISS index
    dimension = embeddings_array.shape[1]
    index = faiss.IndexFlatIP(dimension)  # Inner product for cosine similarity
    
    # Normalize embeddings for cosine similarity
    faiss.normalize_L2(embeddings_array)
    index.add(embeddings_array)
    
    print(f"✅ Built FAISS index with {index.ntotal} vectors")
    return index, metadata_list

def main():
    """Main ingestion function."""
    print("Starting knowledge ingestion...")
    
    # Process AI/ML knowledge base
    ai_ml_path = Path("kb_krishna/ai_ml")
    print(f"Processing AI/ML knowledge base: {ai_ml_path}")
    ai_ml_docs = process_kb_directory(ai_ml_path)
    
    # Process Data Engineering knowledge base
    data_eng_path = Path("kb_krishna/data_engineering")
    print(f"Processing Data Engineering knowledge base: {data_eng_path}")
    data_eng_docs = process_kb_directory(data_eng_path)
    
    # Combine all documents
    all_docs = ai_ml_docs + data_eng_docs
    print(f"Total documents: {len(all_docs)}")
    
    if not all_docs:
        print("No documents found! Make sure you have .md/.txt files in kb_krishna/ai_ml/ and kb_krishna/data_engineering/")
        return
    
    # Build FAISS index
    index, metadata_list = build_faiss_index(all_docs)
    
    # Save index and metadata
    os.makedirs("store", exist_ok=True)
    
    # Save FAISS index
    faiss.write_index(index, "store/faiss.index")
    print("Saved FAISS index to store/faiss.index")
    
    # Save metadata
    with open("store/meta.json", 'w', encoding='utf-8') as f:
        json.dump(metadata_list, f, indent=2, ensure_ascii=False)
    print("Saved metadata to store/meta.json")
    
    print(f"✅ Indexed {len(all_docs)} chunks from {len(ai_ml_docs + data_eng_docs)} documents.")
    print("🎉 Ingestion complete!")

if __name__ == "__main__":
    main()
