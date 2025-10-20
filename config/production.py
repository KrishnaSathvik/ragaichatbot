"""
Production configuration for performance optimization.
"""

# Performance Settings
PERFORMANCE_CONFIG = {
    # Embedding settings
    "embedding_cache_size": 512,
    "embedding_timeout": 5.0,
    
    # Context settings
    "max_context_length": 1200,  # Reduced for speed
    "max_chunk_length": 400,     # Reduced for speed
    "top_k_results": 5,          # Reduced for speed
    
    # OpenAI settings
    "max_tokens_intro": 500,     # Reduced for speed
    "max_tokens_regular": 400,   # Reduced for speed
    "temperature": 0.2,          # Lower for consistency
    "top_p": 0.9,               # Tighter sampling
    "frequency_penalty": 0.2,   # Reduced for speed
    "timeout": 8.0,             # Faster timeout
    
    # Debug settings
    "verbose_logging": False,    # Disable for production
    "debug_output": False,      # Disable debug prints
}

# Model settings
MODEL_CONFIG = {
    "embedding_model": "text-embedding-3-small",
    "chat_model": "gpt-4o-mini",
    "max_retries": 2,
    "retry_delay": 1.0,
}

# Cache settings
CACHE_CONFIG = {
    "enable_redis": False,  # Set to True if Redis available
    "redis_url": "redis://localhost:6379",
    "cache_ttl": 3600,  # 1 hour
}

# Rate limiting
RATE_LIMIT_CONFIG = {
    "requests_per_minute": 60,
    "burst_size": 10,
}
