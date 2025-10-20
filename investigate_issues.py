#!/usr/bin/env python3
"""
Investigation script to analyze low-performing areas in the RAG system.
Focuses on keyword matching, word count issues, and intent routing problems.
"""

import requests
import json
import time
from typing import Dict, List, Any

# Test configuration
BASE_URL = "http://localhost:8000"
API_ENDPOINT = f"{BASE_URL}/api/chat"

# Problematic test cases from our results
PROBLEMATIC_TESTS = [
    # Krishna low performers
    {
        "id": "K3",
        "profile": "krishna",
        "mode": "de", 
        "query": "You mentioned improving data-pipeline performance by 45%. What exact optimizations did you apply?",
        "expected_keywords": ["performance", "45%", "optimization", "delta", "zorder", "optimize", "caching"],
        "expected_intent": "metrics_performance",
        "actual_intent": "followup_drilldown",
        "keyword_score": 0.286,  # 2/7
        "word_count": 97,
        "target_words": 100
    },
    
    {
        "id": "K6",
        "profile": "krishna",
        "mode": "ai",
        "query": "Describe how you collaborated with data scientists and business teams to deploy ML models into production.",
        "expected_keywords": ["collaborated", "data scientists", "business", "teams", "ml", "models", "production"],
        "expected_intent": "collaboration_leadership", 
        "actual_intent": "collaboration_leadership",
        "keyword_score": 0.0,  # 0/7
        "word_count": 102,
        "target_words": 120
    },
    
    # Tejuu low performers
    {
        "id": "T9",
        "profile": "tejuu",
        "mode": "ae",
        "query": "How did you optimize dbt models for performance and maintainability in your Stryker project?",
        "expected_keywords": ["dbt", "models", "performance", "maintainability", "stryker", "optimize", "incremental"],
        "expected_intent": "technical_architecture",
        "actual_intent": "metrics_performance",
        "keyword_score": 0.571,  # 4/7
        "word_count": 95,
        "target_words": 120
    },
    
    {
        "id": "T12",
        "profile": "tejuu",
        "mode": "bi",
        "query": "Describe how you measure report adoption and user engagement for your dashboards.",
        "expected_keywords": ["report", "adoption", "user", "engagement", "dashboards", "measure", "kpis"],
        "expected_intent": "metrics_performance",
        "actual_intent": "metrics_performance",
        "keyword_score": 0.857,  # 6/7
        "word_count": 90,
        "target_words": 120
    }
]

def investigate_query(test_data: Dict[str, Any]) -> Dict[str, Any]:
    """Investigate a specific problematic query in detail."""
    test_id = test_data["id"]
    profile = test_data["profile"]
    mode = test_data["mode"]
    query = test_data["query"]
    expected_keywords = test_data["expected_keywords"]
    expected_intent = test_data["expected_intent"]
    
    print(f"\n🔍 INVESTIGATING {test_id} - {profile.upper()} {mode.upper()}")
    print(f"Query: {query}")
    print(f"Expected Intent: {expected_intent}")
    print(f"Expected Keywords: {expected_keywords}")
    
    payload = {
        "message": query,
        "profile": profile,
        "mode": mode,
        "session_id": f"investigate_{test_id}"
    }
    
    try:
        start_time = time.time()
        response = requests.post(API_ENDPOINT, json=payload, timeout=30)
        latency_ms = int((time.time() - start_time) * 1000)
        
        if response.status_code == 200:
            data = response.json()
            
            # Extract detailed information
            answer = data.get("answer", "")
            sources = data.get("sources", [])
            intent = data.get("intent", "unknown")
            confidence = data.get("confidence", 0.0)
            template_used = data.get("template_used", "unknown")
            domain_used = data.get("domain_used", "unknown")
            
            print(f"\n📊 RESPONSE ANALYSIS:")
            print(f"Intent: {intent} (expected: {expected_intent})")
            print(f"Template: {template_used}")
            print(f"Domain: {domain_used}")
            print(f"Confidence: {confidence}")
            print(f"Latency: {latency_ms}ms")
            
            # Analyze word count
            word_count = len(answer.split())
            line_count = len([line for line in answer.split('\n') if line.strip()])
            print(f"Word count: {word_count} (target: {test_data['target_words']})")
            print(f"Line count: {line_count}")
            
            # Analyze keyword matching in detail
            answer_lower = answer.lower()
            print(f"\n🔍 KEYWORD ANALYSIS:")
            keyword_matches = []
            keyword_misses = []
            
            for keyword in expected_keywords:
                if keyword.lower() in answer_lower:
                    keyword_matches.append(keyword)
                    print(f"  ✅ '{keyword}' - FOUND")
                else:
                    keyword_misses.append(keyword)
                    print(f"  ❌ '{keyword}' - MISSING")
            
            keyword_score = len(keyword_matches) / len(expected_keywords)
            print(f"Keyword Score: {len(keyword_matches)}/{len(expected_keywords)} ({keyword_score:.1%})")
            
            # Analyze sources
            print(f"\n📚 SOURCE ANALYSIS:")
            print(f"Number of sources: {len(sources)}")
            for i, source in enumerate(sources[:3], 1):  # Show first 3 sources
                title = source.get("title", "Unknown")
                score = source.get("score", 0.0)
                print(f"  {i}. {title} (score: {score:.3f})")
            
            # Show full answer for analysis
            print(f"\n📝 FULL ANSWER:")
            print(f"{answer}")
            
            return {
                "test_id": test_id,
                "intent_match": intent == expected_intent,
                "keyword_score": keyword_score,
                "word_count": word_count,
                "target_words": test_data["target_words"],
                "word_count_ok": word_count >= test_data["target_words"],
                "sources_count": len(sources),
                "answer": answer
            }
        else:
            print(f"❌ Request failed: {response.status_code}")
            return {"error": f"HTTP {response.status_code}"}
            
    except Exception as e:
        print(f"❌ Request error: {e}")
        return {"error": str(e)}

def analyze_template_lengths():
    """Analyze template length configurations."""
    print("\n🔍 TEMPLATE LENGTH ANALYSIS")
    print("=" * 50)
    
    # Read template configuration
    try:
        with open("/Users/krishnasathvikmantripragada/rag-chatbot/prompts/v1/templates.yaml", "r") as f:
            import yaml
            data = yaml.safe_load(f)
            
        print("Current template length settings:")
        print(f"Default: {data['defaults']['target_words_low']}-{data['defaults']['target_words_high']} words")
        
        for template in data["templates"]:
            template_id = template["id"]
            low = template.get("target_words_low", data["defaults"]["target_words_low"])
            high = template.get("target_words_high", data["defaults"]["target_words_high"])
            print(f"{template_id}: {low}-{high} words")
            
    except Exception as e:
        print(f"Error reading template config: {e}")

def analyze_keyword_issues():
    """Analyze common keyword matching issues."""
    print("\n🔍 KEYWORD MATCHING ANALYSIS")
    print("=" * 50)
    
    # Test some specific keyword patterns
    test_queries = [
        {
            "query": "dbt performance optimization",
            "keywords": ["dbt", "performance", "optimization"],
            "profile": "tejuu",
            "mode": "ae"
        },
        {
            "query": "Power BI row level security",
            "keywords": ["power bi", "row level", "security"],
            "profile": "tejuu", 
            "mode": "bi"
        },
        {
            "query": "Delta Lake ZORDER optimization",
            "keywords": ["delta", "zorder", "optimization"],
            "profile": "krishna",
            "mode": "de"
        }
    ]
    
    for test in test_queries:
        print(f"\nTesting: {test['query']}")
        payload = {
            "message": test["query"],
            "profile": test["profile"],
            "mode": test["mode"],
            "session_id": "keyword_test"
        }
        
        try:
            response = requests.post(API_ENDPOINT, json=payload, timeout=15)
            if response.status_code == 200:
                data = response.json()
                answer = data.get("answer", "").lower()
                
                print(f"Answer preview: {answer[:100]}...")
                for keyword in test["keywords"]:
                    found = keyword.lower() in answer
                    print(f"  '{keyword}': {'✅' if found else '❌'}")
        except Exception as e:
            print(f"Error: {e}")

def run_investigation():
    """Run comprehensive investigation of low-performing areas."""
    print("🔍 RAG SYSTEM ISSUE INVESTIGATION")
    print("=" * 60)
    
    # Test health first
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=10)
        if response.status_code != 200:
            print("❌ Health check failed")
            return
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return
    
    # Investigate each problematic test case
    results = []
    for test_data in PROBLEMATIC_TESTS:
        result = investigate_query(test_data)
        if "error" not in result:
            results.append(result)
    
    # Analyze template lengths
    analyze_template_lengths()
    
    # Analyze keyword issues
    analyze_keyword_issues()
    
    # Summary of findings
    print("\n" + "=" * 60)
    print("📊 INVESTIGATION SUMMARY")
    print("=" * 60)
    
    if results:
        intent_matches = sum(1 for r in results if r.get("intent_match", False))
        word_count_ok = sum(1 for r in results if r.get("word_count_ok", False))
        avg_keyword_score = sum(r.get("keyword_score", 0) for r in results) / len(results)
        
        print(f"Intent matching: {intent_matches}/{len(results)} ({intent_matches/len(results):.1%})")
        print(f"Word count targets: {word_count_ok}/{len(results)} ({word_count_ok/len(results):.1%})")
        print(f"Average keyword score: {avg_keyword_score:.1%}")
        
        print(f"\n🔍 KEY FINDINGS:")
        print(f"1. Intent routing issues: {len(results) - intent_matches} cases")
        print(f"2. Word count issues: {len(results) - word_count_ok} cases")
        print(f"3. Keyword matching: {avg_keyword_score:.1%} average score")
        
        print(f"\n💡 RECOMMENDATIONS:")
        if intent_matches < len(results):
            print("- Fix intent routing logic in router.py")
        if word_count_ok < len(results):
            print("- Increase template target word counts")
        if avg_keyword_score < 0.7:
            print("- Improve keyword matching in retrieval")
            print("- Add more specific content to knowledge base")

if __name__ == "__main__":
    run_investigation()
