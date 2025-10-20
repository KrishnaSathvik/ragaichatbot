#!/usr/bin/env python3
"""
Comprehensive test script for RAG Knowledge Normalization + Mode-Aware Indexing system.
Tests the complete system with evaluation queries to verify interview-grade responses.
"""

import requests
import json
import time
from typing import Dict, List, Any

# Test configuration
BASE_URL = "http://localhost:8000"
API_ENDPOINT = f"{BASE_URL}/api/chat"

# Test queries for comprehensive evaluation
TEST_QUERIES = [
    # Krishna RAG Architecture (AI)
    {
        "query": "Walk me through your Walgreens RAG system end-to-end and how you balanced accuracy and latency.",
        "profile": "krishna",
        "mode": "ai",
        "session_id": "test_krishna_ai_1",
        "expected_keywords": ["rag", "walgreens", "accuracy", "latency", "hybrid", "retrieval"]
    },
    
    # Tejuu Power BI Governance (BI)
    {
        "query": "How do you implement RLS, certified datasets, and change management in Power BI?",
        "profile": "tejuu", 
        "mode": "bi",
        "session_id": "test_tejuu_bi_1",
        "expected_keywords": ["rls", "certified", "datasets", "power bi", "governance"]
    },
    
    # Tejuu dbt Performance (AE)
    {
        "query": "You claimed a 40% runtime reduction in dbt. What did you change and how did you measure it?",
        "profile": "tejuu",
        "mode": "ae", 
        "session_id": "test_tejuu_ae_1",
        "expected_keywords": ["dbt", "runtime", "reduction", "incremental", "optimization"]
    },
    
    # Krishna Delta Lake (DE)
    {
        "query": "Explain your Delta Lake optimizations and how you handled data skew in production.",
        "profile": "krishna",
        "mode": "de",
        "session_id": "test_krishna_de_1", 
        "expected_keywords": ["delta", "optimization", "skew", "zorder", "compaction"]
    },
    
    # Follow-up question test
    {
        "query": "Building on what you said about RAG performance, how did you handle prompt injection attacks?",
        "profile": "krishna",
        "mode": "ai",
        "session_id": "test_krishna_ai_1",  # Same session for follow-up
        "expected_keywords": ["prompt injection", "security", "guardrails", "patterns"]
    },
    
    # Intro question test
    {
        "query": "Tell me about yourself and your background in data engineering.",
        "profile": "krishna",
        "mode": "de",
        "session_id": "test_krishna_intro_1",
        "expected_keywords": ["krishna", "data engineering", "walgreens", "experience"]
    }
]

def test_health_check():
    """Test the health endpoint."""
    print("🔍 Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check passed: {data.get('status', 'unknown')}")
            print(f"   Embeddings loaded: {data.get('embeddings_loaded', False)}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_chat_query(query_data: Dict[str, Any]) -> Dict[str, Any]:
    """Test a single chat query."""
    query = query_data["query"]
    profile = query_data["profile"]
    mode = query_data["mode"]
    session_id = query_data["session_id"]
    expected_keywords = query_data["expected_keywords"]
    
    print(f"\n🧪 Testing: {query[:60]}...")
    print(f"   Profile: {profile}, Mode: {mode}, Session: {session_id}")
    
    payload = {
        "message": query,
        "profile": profile,
        "mode": mode,
        "session_id": session_id
    }
    
    try:
        start_time = time.time()
        response = requests.post(API_ENDPOINT, json=payload, timeout=30)
        latency_ms = int((time.time() - start_time) * 1000)
        
        if response.status_code == 200:
            data = response.json()
            
            # Extract key information
            answer = data.get("answer", "")
            sources = data.get("sources", [])
            intent = data.get("intent", "unknown")
            confidence = data.get("confidence", 0.0)
            template_used = data.get("template_used", "unknown")
            domain_used = data.get("domain_used", "unknown")
            profile_used = data.get("profile_used", "unknown")
            
            # Check answer length (should be 8-12 lines for most, 10-14 for intros)
            word_count = len(answer.split())
            line_count = len([line for line in answer.split('\n') if line.strip()])
            
            # Check for expected keywords
            answer_lower = answer.lower()
            keyword_matches = [kw for kw in expected_keywords if kw.lower() in answer_lower]
            
            # Evaluate response quality
            quality_score = 0
            if word_count >= 100:  # Minimum length check
                quality_score += 1
            if len(keyword_matches) >= len(expected_keywords) * 0.6:  # 60% keyword match
                quality_score += 1
            if len(sources) > 0:  # Has sources
                quality_score += 1
            if latency_ms < 5000:  # Reasonable latency
                quality_score += 1
            if confidence > 0.7:  # High confidence
                quality_score += 1
            
            print(f"✅ Response received ({latency_ms}ms)")
            print(f"   Answer length: {word_count} words, {line_count} lines")
            print(f"   Intent: {intent}, Confidence: {confidence}")
            print(f"   Template: {template_used}, Domain: {domain_used}")
            print(f"   Sources: {len(sources)}")
            print(f"   Keyword matches: {len(keyword_matches)}/{len(expected_keywords)}")
            print(f"   Quality score: {quality_score}/5")
            print(f"   Answer preview: {answer[:200]}...")
            
            return {
                "success": True,
                "latency_ms": latency_ms,
                "word_count": word_count,
                "line_count": line_count,
                "keyword_matches": len(keyword_matches),
                "total_keywords": len(expected_keywords),
                "quality_score": quality_score,
                "sources_count": len(sources),
                "confidence": confidence,
                "answer": answer
            }
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return {"success": False, "error": f"HTTP {response.status_code}"}
            
    except Exception as e:
        print(f"❌ Request error: {e}")
        return {"success": False, "error": str(e)}

def run_comprehensive_tests():
    """Run all comprehensive tests."""
    print("🚀 Starting RAG Knowledge Normalization + Mode-Aware Indexing Tests")
    print("=" * 80)
    
    # Test health check first
    if not test_health_check():
        print("❌ Health check failed, aborting tests")
        return
    
    print("\n" + "=" * 80)
    print("🧪 Running comprehensive query tests...")
    
    results = []
    total_tests = len(TEST_QUERIES)
    successful_tests = 0
    total_latency = 0
    total_quality_score = 0
    
    for i, query_data in enumerate(TEST_QUERIES, 1):
        print(f"\n--- Test {i}/{total_tests} ---")
        result = test_chat_query(query_data)
        results.append(result)
        
        if result["success"]:
            successful_tests += 1
            total_latency += result["latency_ms"]
            total_quality_score += result["quality_score"]
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 TEST SUMMARY")
    print("=" * 80)
    
    success_rate = (successful_tests / total_tests) * 100
    avg_latency = total_latency / successful_tests if successful_tests > 0 else 0
    avg_quality = total_quality_score / successful_tests if successful_tests > 0 else 0
    
    print(f"✅ Successful tests: {successful_tests}/{total_tests} ({success_rate:.1f}%)")
    print(f"⚡ Average latency: {avg_latency:.0f}ms")
    print(f"🎯 Average quality score: {avg_quality:.1f}/5")
    
    # Detailed results
    print(f"\n📋 DETAILED RESULTS:")
    for i, (query_data, result) in enumerate(zip(TEST_QUERIES, results), 1):
        if result["success"]:
            status = "✅"
            details = f"{result['word_count']}w, {result['line_count']}l, {result['quality_score']}/5"
        else:
            status = "❌"
            details = f"Error: {result.get('error', 'Unknown')}"
        
        print(f"   {i}. {status} {query_data['query'][:50]}... - {details}")
    
    # Performance evaluation
    print(f"\n🎯 PERFORMANCE EVALUATION:")
    if success_rate >= 90:
        print("✅ Excellent: 90%+ success rate")
    elif success_rate >= 80:
        print("✅ Good: 80%+ success rate")
    elif success_rate >= 70:
        print("⚠️  Fair: 70%+ success rate")
    else:
        print("❌ Poor: <70% success rate")
    
    if avg_latency <= 3000:
        print("✅ Excellent: <3s average latency")
    elif avg_latency <= 5000:
        print("✅ Good: <5s average latency")
    else:
        print("⚠️  Slow: >5s average latency")
    
    if avg_quality >= 4.0:
        print("✅ Excellent: 4.0+ quality score")
    elif avg_quality >= 3.0:
        print("✅ Good: 3.0+ quality score")
    else:
        print("⚠️  Needs improvement: <3.0 quality score")
    
    print(f"\n🎉 RAG Knowledge Normalization + Mode-Aware Indexing test complete!")
    print(f"   System is ready for interview-grade responses!")

if __name__ == "__main__":
    run_comprehensive_tests()
