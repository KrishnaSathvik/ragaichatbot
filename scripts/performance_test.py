#!/usr/bin/env python3
"""
Performance testing script for the RAG chatbot.
"""

import requests
import time
import statistics
import json
from concurrent.futures import ThreadPoolExecutor
import sys

API_BASE = "http://localhost:8000/api"

def test_endpoint(message, profile, mode, expected_role=None):
    """Test a single endpoint and measure performance."""
    start_time = time.time()
    
    try:
        response = requests.post(
            f"{API_BASE}/chat",
            json={
                "message": message,
                "profile": profile,
                "mode": mode
            },
            timeout=15
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        if response.status_code == 200:
            data = response.json()
            answer = data.get("answer", "")
            
            # Check if role is correct
            role_correct = True
            if expected_role and expected_role.lower() not in answer.lower():
                role_correct = False
            
            return {
                "success": True,
                "duration": duration,
                "status_code": response.status_code,
                "role_correct": role_correct,
                "answer_length": len(answer),
                "latency_ms": data.get("latency_ms", 0)
            }
        else:
            return {
                "success": False,
                "duration": duration,
                "status_code": response.status_code,
                "error": response.text
            }
    except Exception as e:
        end_time = time.time()
        return {
            "success": False,
            "duration": end_time - start_time,
            "error": str(e)
        }

def run_performance_tests():
    """Run comprehensive performance tests."""
    print("🚀 Starting Performance Tests...")
    
    # Test cases
    test_cases = [
        {
            "name": "Krishna AI - Role",
            "message": "What is your current role?",
            "profile": "krishna",
            "mode": "ai",
            "expected_role": "AI/ML Engineer"
        },
        {
            "name": "Krishna DE - Role", 
            "message": "What is your current role?",
            "profile": "krishna",
            "mode": "de",
            "expected_role": "Data Engineer"
        },
        {
            "name": "Tejuu Analytics - Role",
            "message": "What is your current role?",
            "profile": "tejuu", 
            "mode": "ae",
            "expected_role": "Analytics Engineer"
        },
        {
            "name": "Tejuu Business - Role",
            "message": "What is your current role?",
            "profile": "tejuu",
            "mode": "bi", 
            "expected_role": "Business Analyst"
        },
        {
            "name": "Krishna AI - Technical",
            "message": "How do you implement RAG pipelines?",
            "profile": "krishna",
            "mode": "ai"
        },
        {
            "name": "Tejuu Analytics - Technical",
            "message": "How do you use dbt for data modeling?",
            "profile": "tejuu",
            "mode": "ae"
        }
    ]
    
    results = []
    
    # Single request tests
    print("\n📊 Single Request Tests:")
    for test_case in test_cases:
        print(f"Testing {test_case['name']}...")
        result = test_endpoint(
            test_case["message"],
            test_case["profile"], 
            test_case["mode"],
            test_case.get("expected_role")
        )
        result["test_name"] = test_case["name"]
        results.append(result)
        
        if result["success"]:
            print(f"  ✅ {result['duration']:.2f}s - {result['answer_length']} chars")
            if "role_correct" in result and not result["role_correct"]:
                print(f"  ⚠️  Role mismatch detected")
        else:
            print(f"  ❌ Failed: {result.get('error', 'Unknown error')}")
    
    # Concurrent load test
    print("\n🔄 Concurrent Load Test (5 requests):")
    concurrent_results = []
    
    def run_concurrent_test():
        return test_endpoint(
            "What is your current role?",
            "krishna",
            "ai",
            "AI/ML Engineer"
        )
    
    start_time = time.time()
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(run_concurrent_test) for _ in range(5)]
        concurrent_results = [future.result() for future in futures]
    end_time = time.time()
    
    concurrent_duration = end_time - start_time
    successful_concurrent = sum(1 for r in concurrent_results if r["success"])
    
    print(f"  Total time: {concurrent_duration:.2f}s")
    print(f"  Successful: {successful_concurrent}/5")
    print(f"  Average per request: {concurrent_duration/5:.2f}s")
    
    # Performance summary
    print("\n📈 Performance Summary:")
    successful_results = [r for r in results if r["success"]]
    
    if successful_results:
        durations = [r["duration"] for r in successful_results]
        latencies = [r.get("latency_ms", 0) for r in successful_results if r.get("latency_ms")]
        
        print(f"  Average response time: {statistics.mean(durations):.2f}s")
        print(f"  Median response time: {statistics.median(durations):.2f}s")
        print(f"  Min response time: {min(durations):.2f}s")
        print(f"  Max response time: {max(durations):.2f}s")
        
        if latencies:
            print(f"  Average API latency: {statistics.mean(latencies):.0f}ms")
        
        # Performance rating
        avg_time = statistics.mean(durations)
        if avg_time < 2.0:
            rating = "🚀 Excellent"
        elif avg_time < 3.0:
            rating = "✅ Good"
        elif avg_time < 4.0:
            rating = "⚠️  Acceptable"
        else:
            rating = "❌ Needs Improvement"
        
        print(f"  Performance Rating: {rating}")
    
    # Accuracy summary
    role_tests = [r for r in results if "role_correct" in r]
    if role_tests:
        correct_roles = sum(1 for r in role_tests if r["role_correct"])
        print(f"  Role Accuracy: {correct_roles}/{len(role_tests)} ({correct_roles/len(role_tests)*100:.1f}%)")
    
    print(f"\n✅ Performance testing complete!")

if __name__ == "__main__":
    run_performance_tests()
