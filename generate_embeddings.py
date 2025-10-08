#!/usr/bin/env python3
"""
Generate embeddings.npy from existing meta.json for Render deployment.
This script reads the metadata and creates embeddings using OpenAI API.
"""

import os
import json
import numpy as np
from openai import OpenAI
from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv()

# Configuration
EMBEDDING_MODEL = "text-embedding-3-small"
METADATA_FILE = "api/meta.json"
OUTPUT_FILE = "api/embeddings.npy"

def get_embedding(text: str, client: OpenAI) -> list:
    """Get OpenAI embedding for text."""
    try:
        response = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Error getting embedding: {e}")
        return None

def main():
    """Generate embeddings from meta.json."""
    print("🚀 Starting embedding generation...")
    
    # Check if OpenAI API key is set
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not found in environment!")
        print("Please set it in your .env file or environment variables.")
        return
    
    # Initialize OpenAI client
    client = OpenAI(api_key=api_key)
    print(f"✅ OpenAI client initialized")
    
    # Load metadata
    print(f"📖 Reading metadata from {METADATA_FILE}...")
    try:
        with open(METADATA_FILE, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
    except FileNotFoundError:
        print(f"❌ File not found: {METADATA_FILE}")
        print("Please make sure meta.json exists in the api/ directory.")
        return
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing JSON: {e}")
        return
    
    print(f"✅ Loaded {len(metadata)} text chunks")
    
    # Generate embeddings
    print("🔄 Generating embeddings (this may take a while)...")
    embeddings = []
    failed_count = 0
    
    for i, item in enumerate(tqdm(metadata, desc="Processing", unit="chunk")):
        text = item.get('text', '')
        if not text:
            print(f"⚠️  Warning: Empty text at index {i}")
            # Use zero vector for empty text
            embeddings.append([0.0] * 1536)  # text-embedding-3-small has 1536 dimensions
            failed_count += 1
            continue
        
        embedding = get_embedding(text, client)
        if embedding:
            embeddings.append(embedding)
        else:
            # Use zero vector if embedding fails
            embeddings.append([0.0] * 1536)
            failed_count += 1
    
    # Convert to numpy array
    embeddings_array = np.array(embeddings, dtype=np.float32)
    print(f"✅ Generated embeddings shape: {embeddings_array.shape}")
    
    if failed_count > 0:
        print(f"⚠️  Warning: {failed_count} embeddings failed or were empty")
    
    # Save embeddings
    print(f"💾 Saving embeddings to {OUTPUT_FILE}...")
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    np.save(OUTPUT_FILE, embeddings_array)
    print(f"✅ Saved embeddings to {OUTPUT_FILE}")
    
    # Verify the file
    file_size = os.path.getsize(OUTPUT_FILE) / (1024 * 1024)  # Size in MB
    print(f"📊 File size: {file_size:.2f} MB")
    
    print("\n🎉 Embedding generation complete!")
    print(f"📂 Files created:")
    print(f"   - {OUTPUT_FILE}")
    print("\n📝 Next steps:")
    print("   1. Commit and push the embeddings.npy file to your repo")
    print("   2. Render will automatically redeploy with the new embeddings")
    print("   3. Your chatbot will then be able to answer questions!")

if __name__ == "__main__":
    main()

