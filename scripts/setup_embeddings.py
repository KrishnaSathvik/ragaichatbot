#!/usr/bin/env python3
"""
Setup script to generate embeddings for production deployment.
This should be run during the build process.
"""

import os
import sys
import subprocess
from pathlib import Path

def check_environment():
    """Check if required environment variables are set."""
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ ERROR: OPENAI_API_KEY environment variable not set")
        print("Please set your OpenAI API key:")
        print("export OPENAI_API_KEY='your-api-key-here'")
        return False
    return True

def generate_embeddings():
    """Generate embeddings using the fast script."""
    print("🔄 Generating embeddings...")
    
    try:
        # Run the fast embedding generation script
        result = subprocess.run([
            sys.executable, "scripts/generate_embeddings_fast.py"
        ], check=True, capture_output=True, text=True)
        
        print("✅ Embeddings generated successfully!")
        print(result.stdout)
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error generating embeddings: {e}")
        print(f"Error output: {e.stderr}")
        return False

def main():
    """Main setup function."""
    print("🚀 Setting up RAG chatbot embeddings...")
    
    # Check environment
    if not check_environment():
        sys.exit(1)
    
    # Create api directory if it doesn't exist
    os.makedirs("api", exist_ok=True)
    
    # Generate embeddings
    if not generate_embeddings():
        print("❌ Failed to generate embeddings")
        sys.exit(1)
    
    # Verify files were created
    required_files = ["api/embeddings.npy", "api/meta.json"]
    for file_path in required_files:
        if not os.path.exists(file_path):
            print(f"❌ Required file not found: {file_path}")
            sys.exit(1)
        else:
            size = os.path.getsize(file_path) / (1024 * 1024)
            print(f"✅ {file_path} created ({size:.1f} MB)")
    
    print("🎉 Setup complete! RAG chatbot is ready for deployment.")

if __name__ == "__main__":
    main()
