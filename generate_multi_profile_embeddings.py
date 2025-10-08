#!/usr/bin/env python3
"""
Generate embeddings for both Krishna and Tejuu profiles.
This script processes both knowledge bases and creates combined embeddings.
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
    
    print(f"📁 Processing {len(files)} files from {directory} for {persona}")
    
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
    """Generate embeddings for both profiles."""
    print("🚀 Starting multi-profile embedding generation...")
    
    # Check if OpenAI API key is set
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not found in environment!")
        print("Please set it in your .env file or environment variables.")
        return
    
    # Initialize OpenAI client
    client = OpenAI(api_key=api_key, timeout=30.0, max_retries=2)
    print(f"✅ OpenAI client initialized")
    
    # Load existing Krishna embeddings if they exist
    existing_metadata = []
    if os.path.exists(METADATA_FILE):
        print(f"📖 Loading existing metadata from {METADATA_FILE}...")
        try:
            with open(METADATA_FILE, 'r', encoding='utf-8') as f:
                existing_metadata = json.load(f)
            print(f"✅ Loaded {len(existing_metadata)} existing chunks")
        except Exception as e:
            print(f"⚠️  Error loading existing metadata: {e}")
    
    # Generate chunks for Tejuu's knowledge base
    print("\n🔄 Processing Tejuu's knowledge base...")
    tejuu_chunks = read_markdown_files("kb_tejuu", "tejuu")
    print(f"✅ Generated {len(tejuu_chunks)} chunks for Tejuu")
    
    # Combine all chunks
    all_chunks = existing_metadata + tejuu_chunks
    print(f"\n📊 Total chunks: {len(all_chunks)}")
    print(f"   - Krishna: {len(existing_metadata)}")
    print(f"   - Tejuu: {len(tejuu_chunks)}")
    
    # Generate embeddings
    print("\n🔄 Generating embeddings (this may take a while)...")
    embeddings = []
    failed_count = 0
    
    for i, chunk in enumerate(tqdm(all_chunks, desc="Processing", unit="chunk")):
        # Add unique ID if not present
        if 'id' not in chunk:
            persona = chunk['metadata']['persona']
            chunk['id'] = f"{persona}_{i}"
        
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
    print(f"✅ Generated embeddings shape: {embeddings_array.shape}")
    
    if failed_count > 0:
        print(f"⚠️  Warning: {failed_count} embeddings failed or were empty")
    
    # Save updated metadata
    print(f"💾 Saving updated metadata to {METADATA_FILE}...")
    os.makedirs(os.path.dirname(METADATA_FILE), exist_ok=True)
    with open(METADATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_chunks, f, indent=2, ensure_ascii=False)
    print(f"✅ Saved metadata to {METADATA_FILE}")
    
    # Save embeddings
    print(f"💾 Saving embeddings to {OUTPUT_FILE}...")
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    np.save(OUTPUT_FILE, embeddings_array)
    print(f"✅ Saved embeddings to {OUTPUT_FILE}")
    
    # Verify the files
    embeddings_size = os.path.getsize(OUTPUT_FILE) / (1024 * 1024)
    metadata_size = os.path.getsize(METADATA_FILE) / (1024 * 1024)
    print(f"📊 File sizes:")
    print(f"   - Embeddings: {embeddings_size:.2f} MB")
    print(f"   - Metadata: {metadata_size:.2f} MB")
    
    print("\n🎉 Multi-profile embedding generation complete!")
    print(f"📂 Files updated:")
    print(f"   - {OUTPUT_FILE}")
    print(f"   - {METADATA_FILE}")
    print("\n📝 Next steps:")
    print("   1. Test locally to make sure both profiles work")
    print("   2. Commit and push the updated files")
    print("   3. Render will automatically redeploy")
    print("   4. Both Krishna and Tejuu will have access to their knowledge bases!")

if __name__ == "__main__":
    main()
