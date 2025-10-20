#!/usr/bin/env python3
"""
Tejuu-focused test suite for RAG Knowledge Normalization + Mode-Aware Indexing.
Tests Analytics Engineering, Data Modeling, BI Governance, and Power BI topics.
"""

import requests
import json
import time
from typing import Dict, List, Any

# Test configuration
BASE_URL = "http://localhost:8000"
API_ENDPOINT = f"{BASE_URL}/api/chat"

# Tejuu-focused test queries
TEJUU_TESTS = [
    # 🧩 Analytics Engineering / Data Modeling
    {
        "id": "9",
        "category": "Analytics Engineering",
        "query": "How did you optimize dbt models for performance and maintainability in your Stryker project?",
        "profile": "tejuu",
        "mode": "ae",
        "session_id": "tejuu_ae_1",
        "expected_keywords": ["dbt", "models", "performance", "maintainability", "stryker", "optimize", "incremental"],
        "expected_intent": "technical_architecture",
        "min_words": 120,
        "description": "Tests: technical_architecture, ae_dbt_advanced, incremental models + CI"
    },
    
    {
        "id": "10",
        "category": "Analytics Engineering", 
        "query": "Explain how you implemented a semantic layer in dbt and ensured data consistency across departments.",
        "profile": "tejuu",
        "mode": "ae",
        "session_id": "tejuu_ae_2",
        "expected_keywords": ["semantic", "layer", "dbt", "consistency", "departments", "exposures", "freshness"],
        "expected_intent": "domain_understanding",
        "min_words": 120,
        "description": "Tests: domain_understanding, ae, exposures + freshness tests"
    },
    
    # 📈 BI / Power BI Governance
    {
        "id": "11",
        "category": "BI Governance",
        "query": "How do you manage row-level security and certified datasets in Power BI for different departments?",
        "profile": "tejuu",
        "mode": "bi",
        "session_id": "tejuu_bi_1",
        "expected_keywords": ["row-level", "security", "rls", "certified", "datasets", "power bi", "departments"],
        "expected_intent": "technical_architecture",
        "min_words": 120,
        "description": "Tests: technical_architecture, bi, RLS roles + dataset governance"
    },
    
    {
        "id": "12",
        "category": "BI Governance",
        "query": "Describe how you measure report adoption and user engagement for your dashboards.",
        "profile": "tejuu",
        "mode": "bi",
        "session_id": "tejuu_bi_2",
        "expected_keywords": ["report", "adoption", "user", "engagement", "dashboards", "measure", "kpis"],
        "expected_intent": "metrics_performance",
        "min_words": 120,
        "description": "Tests: metrics_performance, bi, adoption KPIs and process automation"
    },
    
    # Additional comprehensive tests for Tejuu
    {
        "id": "13",
        "category": "Analytics Engineering",
        "query": "What challenges did you face when migrating from traditional ETL to dbt, and how did you overcome them?",
        "profile": "tejuu",
        "mode": "ae",
        "session_id": "tejuu_ae_3",
        "expected_keywords": ["migration", "etl", "dbt", "challenges", "overcome", "traditional"],
        "expected_intent": "learning_reflection",
        "min_words": 120,
        "description": "Tests: learning_reflection, ae, migration challenges and solutions"
    },
    
    {
        "id": "14",
        "category": "BI Governance",
        "query": "How do you ensure data quality and governance in your Power BI environment across multiple business units?",
        "profile": "tejuu",
        "mode": "bi",
        "session_id": "tejuu_bi_3",
        "expected_keywords": ["data quality", "governance", "power bi", "business units", "environment"],
        "expected_intent": "domain_understanding",
        "min_words": 120,
        "description": "Tests: domain_understanding, bi, data quality and governance"
    },
    
    {
        "id": "15",
        "category": "Analytics Engineering",
        "query": "Walk me through your dbt testing strategy and how you ensure data accuracy in production.",
        "profile": "tejuu",
        "mode": "ae",
        "session_id": "tejuu_ae_4",
        "expected_keywords": ["dbt", "testing", "strategy", "data accuracy", "production", "tests"],
        "expected_intent": "technical_architecture",
        "min_words": 120,
        "description": "Tests: technical_architecture, ae, dbt testing and data accuracy"
    },
    
    {
        "id": "16",
        "category": "BI Governance",
        "query": "How do you handle stakeholder requirements gathering and translate them into effective Power BI solutions?",
        "profile": "tejuu",
        "mode": "bi",
        "session_id": "tejuu_bi_4",
        "expected_keywords": ["stakeholder", "requirements", "gathering", "power bi", "solutions", "translate"],
        "expected_intent": "collaboration_leadership",
        "min_words": 120,
        "description": "Tests: collaboration_leadership, bi, stakeholder management and requirements"
    }
]

def test_tejuu_query(test_data: Dict[str, Any]) -> Dict[str, Any]:
    """Test a single Tejuu-focused query."""
    test_id = test_data["id"]
    category = test_data["category"]
    query = test_data["query"]
    profile = test_data["profile"]
    mode = test_data["mode"]
    session_id = test_data["session_id"]
    expected_keywords = test_data["expected_keywords"]
    expected_intent = test_data["expected_intent"]
    min_words = test_data["min_words"]
    description = test_data["description"]
    
    print(f"\n🧪 Test {test_id} - {category}")
    print(f"   {description}")
    print(f"   Query: {query[:80]}...")
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
            
            # Analyze response
            word_count = len(answer.split())
            line_count = len([line for line in answer.split('\n') if line.strip()])
            
            # Check for expected keywords
            answer_lower = answer.lower()
            keyword_matches = [kw for kw in expected_keywords if kw.lower() in answer_lower]
            keyword_score = len(keyword_matches) / len(expected_keywords)
            
            # Check intent matching
            intent_match = intent == expected_intent
            
            # Evaluate response quality
            quality_score = 0
            if word_count >= min_words:
                quality_score += 1
                print(f"   ✅ Word count: {word_count} (≥{min_words})")
            else:
                print(f"   ⚠️  Word count: {word_count} (<{min_words})")
                
            if keyword_score >= 0.6:
                quality_score += 1
                print(f"   ✅ Keywords: {len(keyword_matches)}/{len(expected_keywords)} ({keyword_score:.1%})")
            else:
                print(f"   ⚠️  Keywords: {len(keyword_matches)}/{len(expected_keywords)} ({keyword_score:.1%})")
                
            if len(sources) > 0:
                quality_score += 1
                print(f"   ✅ Sources: {len(sources)}")
            else:
                print(f"   ⚠️  Sources: {len(sources)}")
                
            if latency_ms < 5000:
                quality_score += 1
                print(f"   ✅ Latency: {latency_ms}ms")
            else:
                print(f"   ⚠️  Latency: {latency_ms}ms")
                
            if intent_match:
                quality_score += 1
                print(f"   ✅ Intent: {intent} (matches {expected_intent})")
            else:
                print(f"   ⚠️  Intent: {intent} (expected {expected_intent})")
            
            print(f"   📊 Quality Score: {quality_score}/5")
            print(f"   📝 Answer Preview: {answer[:150]}...")
            
            return {
                "success": True,
                "test_id": test_id,
                "category": category,
                "latency_ms": latency_ms,
                "word_count": word_count,
                "line_count": line_count,
                "keyword_score": keyword_score,
                "intent_match": intent_match,
                "quality_score": quality_score,
                "sources_count": len(sources),
                "confidence": confidence,
                "answer": answer
            }
        else:
            print(f"   ❌ Request failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return {"success": False, "test_id": test_id, "error": f"HTTP {response.status_code}"}
            
    except Exception as e:
        print(f"   ❌ Request error: {e}")
        return {"success": False, "test_id": test_id, "error": str(e)}

def run_tejuu_tests():
    """Run all Tejuu-focused tests."""
    print("🚀 Starting Tejuu-Focused RAG System Tests")
    print("=" * 80)
    
    # Test health check first
    print("🔍 Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check passed: {data.get('status', 'unknown')}")
            print(f"   Embeddings loaded: {data.get('embeddings_loaded', False)}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return
    
    print("\n" + "=" * 80)
    print("🧪 Running Tejuu-focused tests...")
    
    results = []
    total_tests = len(TEJUU_TESTS)
    successful_tests = 0
    total_latency = 0
    total_quality_score = 0
    category_scores = {}
    
    for test_data in TEJUU_TESTS:
        result = test_tejuu_query(test_data)
        results.append(result)
        
        if result["success"]:
            successful_tests += 1
            total_latency += result["latency_ms"]
            total_quality_score += result["quality_score"]
            
            # Track by category
            category = test_data["category"]
            if category not in category_scores:
                category_scores[category] = {"count": 0, "total_score": 0}
            category_scores[category]["count"] += 1
            category_scores[category]["total_score"] += result["quality_score"]
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 TEJUU-FOCUSED TEST SUMMARY")
    print("=" * 80)
    
    success_rate = (successful_tests / total_tests) * 100
    avg_latency = total_latency / successful_tests if successful_tests > 0 else 0
    avg_quality = total_quality_score / successful_tests if successful_tests > 0 else 0
    
    print(f"✅ Successful tests: {successful_tests}/{total_tests} ({success_rate:.1f}%)")
    print(f"⚡ Average latency: {avg_latency:.0f}ms")
    print(f"🎯 Average quality score: {avg_quality:.1f}/5")
    
    # Category breakdown
    print(f"\n📋 CATEGORY BREAKDOWN:")
    for category, stats in category_scores.items():
        avg_score = stats["total_score"] / stats["count"]
        print(f"   {category}: {avg_score:.1f}/5 ({stats['count']} tests)")
    
    # Detailed results
    print(f"\n📋 DETAILED RESULTS:")
    for result in results:
        if result["success"]:
            status = "✅"
            details = f"{result['word_count']}w, {result['quality_score']}/5"
        else:
            status = "❌"
            details = f"Error: {result.get('error', 'Unknown')}"
        
        print(f"   Test {result['test_id']}: {status} {details}")
    
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
    
    print(f"\n🎉 Tejuu-focused RAG system test complete!")
    print(f"   System is ready for analytics and BI interviews!")

if __name__ == "__main__":
    run_tejuu_tests()
