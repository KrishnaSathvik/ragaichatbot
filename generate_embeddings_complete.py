#!/usr/bin/env python3
"""
Complete embedding generation for BOTH Krishna and Tejuu with NEW knowledge base structure.
Processes:
- Krishna DE: kb/data_engineering/
- Krishna AI: kb/ai_ml/
- Tejuu ALL: kb_tejuu/
"""

import os
import json
import numpy as np
from openai import OpenAI
from dotenv import load_dotenv
from tqdm import tqdm
import glob

load_dotenv()

# Configuration
EMBEDDING_MODEL = "text-embedding-3-small"
OUTPUT_FILE = "api/embeddings.npy"
METADATA_FILE = "api/meta.json"

def get_embedding(text: str, client: OpenAI) -> list:
    """Get OpenAI embedding for text."""
    try:
        response = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=text,
            timeout=10.0
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Error getting embedding: {e}")
        return None

def read_markdown_files(directory: str, persona: str) -> list:
    """Read all markdown files from a directory and return chunks."""
    chunks = []
    files = glob.glob(f"{directory}/**/*.md", recursive=True)
    
    print(f"📁 Processing {len(files)} files from {directory} for persona '{persona}'")
    
    for file_path in files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Split content into chunks (roughly 1000 characters each)
            chunk_size = 1000
            overlap = 200
            
            for i in range(0, len(content), chunk_size - overlap):
                chunk_text = content[i:i + chunk_size]
                if len(chunk_text.strip()) > 100:  # Only include substantial chunks
                    chunks.append({
                        'text': chunk_text,
                        'metadata': {
                            'persona': persona,
                            'file_path': file_path,
                            'file_name': os.path.basename(file_path),
                            'chunk_index': len(chunks)
                        }
                    })
        
        except Exception as e:
            print(f"⚠️  Error reading {file_path}: {e}")
    
    return chunks

def main():
    """Generate embeddings for both profiles from scratch."""
    print("🚀 Starting COMPLETE embedding generation from scratch...")
    print("🗑️  Ignoring old metadata - processing ALL files fresh\n")
    
    # Check if OpenAI API key is set
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not found in environment!")
        return
    
    # Initialize OpenAI client
    client = OpenAI(api_key=api_key, timeout=30.0, max_retries=2)
    print(f"✅ OpenAI client initialized\n")
    
    # Process Krishna's Data Engineering knowledge base
    print("🔄 Processing Krishna's Data Engineering KB...")
    krishna_de_chunks = read_markdown_files("kb/data_engineering", "de")
    print(f"✅ Generated {len(krishna_de_chunks)} chunks for Krishna DE\n")
    
    # Process Krishna's AI/ML knowledge base
    print("🔄 Processing Krishna's AI/ML KB...")
    krishna_ai_chunks = read_markdown_files("kb/ai_ml", "ai")
    print(f"✅ Generated {len(krishna_ai_chunks)} chunks for Krishna AI\n")
    
    # Process Tejuu's knowledge base (all subdirectories)
    print("🔄 Processing Tejuu's complete KB...")
    tejuu_chunks = []
    
    # Tejuu Analytics Engineer (ae persona)
    tejuu_ae_chunks = read_markdown_files("kb_tejuu/analytics_engineer", "ae")
    print(f"   - Analytics Engineer: {len(tejuu_ae_chunks)} chunks")
    tejuu_chunks.extend(tejuu_ae_chunks)
    
    # Tejuu Business Analyst & BI (tejuu persona)
    tejuu_ba_chunks = read_markdown_files("kb_tejuu/business_analyst", "tejuu")
    print(f"   - Business Analyst: {len(tejuu_ba_chunks)} chunks")
    tejuu_chunks.extend(tejuu_ba_chunks)
    
    tejuu_bi_chunks = read_markdown_files("kb_tejuu/business_intelligence", "tejuu")
    print(f"   - Business Intelligence: {len(tejuu_bi_chunks)} chunks")
    tejuu_chunks.extend(tejuu_bi_chunks)
    
    print(f"✅ Generated {len(tejuu_chunks)} total chunks for Tejuu\n")
    
    # Combine all chunks
    all_chunks = krishna_de_chunks + krishna_ai_chunks + tejuu_chunks
    
    print(f"📊 TOTAL CHUNKS: {len(all_chunks)}")
    print(f"   - Krishna DE: {len(krishna_de_chunks)}")
    print(f"   - Krishna AI: {len(krishna_ai_chunks)}")
    print(f"   - Tejuu AE: {len(tejuu_ae_chunks)}")
    print(f"   - Tejuu BA/BI: {len(tejuu_ba_chunks) + len(tejuu_bi_chunks)}")
    print()
    
    # Generate embeddings
    print("🔄 Generating embeddings (this may take a while)...")
    embeddings = []
    failed_count = 0
    
    for i, chunk in enumerate(tqdm(all_chunks, desc="Processing", unit="chunk")):
        # Add unique ID
        persona = chunk['metadata']['persona']
        file_name = chunk['metadata']['file_name'].replace('.md', '')
        chunk['id'] = f"{persona}_{file_name}_{i}"
        
        text = chunk.get('text', '')
        if not text:
            print(f"⚠️  Warning: Empty text at index {i}")
            embeddings.append([0.0] * 1536)
            failed_count += 1
            continue
        
        embedding = get_embedding(text, client)
        if embedding:
            embeddings.append(embedding)
        else:
            embeddings.append([0.0] * 1536)
            failed_count += 1
    
    # Convert to numpy array
    embeddings_array = np.array(embeddings, dtype=np.float32)
    print(f"\n✅ Generated embeddings shape: {embeddings_array.shape}")
    
    if failed_count > 0:
        print(f"⚠️  Warning: {failed_count} embeddings failed or were empty")
    
    # Save metadata
    print(f"\n💾 Saving metadata to {METADATA_FILE}...")
    os.makedirs(os.path.dirname(METADATA_FILE), exist_ok=True)
    with open(METADATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_chunks, f, indent=2, ensure_ascii=False)
    print(f"✅ Saved metadata")
    
    # Save embeddings
    print(f"💾 Saving embeddings to {OUTPUT_FILE}...")
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    np.save(OUTPUT_FILE, embeddings_array)
    print(f"✅ Saved embeddings")
    
    # Verify file sizes
    embeddings_size = os.path.getsize(OUTPUT_FILE) / (1024 * 1024)
    metadata_size = os.path.getsize(METADATA_FILE) / (1024 * 1024)
    print(f"\n📊 File sizes:")
    print(f"   - Embeddings: {embeddings_size:.2f} MB")
    print(f"   - Metadata: {metadata_size:.2f} MB")
    
    print("\n🎉 Complete embedding generation finished!")
    print(f"📂 Files updated:")
    print(f"   - {OUTPUT_FILE}")
    print(f"   - {METADATA_FILE}")

if __name__ == "__main__":
    main()

