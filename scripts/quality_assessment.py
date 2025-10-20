#!/usr/bin/env python3
"""
Answer quality assessment script for the RAG chatbot.
"""

import requests
import json
import time
from typing import Dict, List, Any

API_BASE = "http://localhost:8000/api"

def assess_answer_quality(answer: str, expected_elements: List[str]) -> Dict[str, Any]:
    """Assess the quality of an answer based on expected elements."""
    quality_score = 0
    max_score = len(expected_elements)
    found_elements = []
    missing_elements = []
    
    answer_lower = answer.lower()
    
    for element in expected_elements:
        if element.lower() in answer_lower:
            quality_score += 1
            found_elements.append(element)
        else:
            missing_elements.append(element)
    
    # Additional quality metrics
    word_count = len(answer.split())
    sentence_count = answer.count('.') + answer.count('!') + answer.count('?')
    
    # Check for technical depth indicators
    technical_indicators = [
        'databricks', 'pyspark', 'delta lake', 'azure', 'pipeline', 'etl', 'elt',
        'rag', 'openai', 'pinecone', 'dbt', 'power bi', 'sql', 'python',
        'machine learning', 'data engineering', 'analytics', 'business intelligence'
    ]
    
    technical_depth = sum(1 for indicator in technical_indicators if indicator in answer_lower)
    
    # Check for specific metrics/numbers (indicates concrete experience)
    has_metrics = any(char.isdigit() for char in answer)
    
    # Check for project-specific details
    has_project_details = any(word in answer_lower for word in [
        'project', 'recently', 'currently', 'implemented', 'achieved', 'reduced', 'improved'
    ])
    
    return {
        "quality_score": quality_score,
        "max_score": max_score,
        "quality_percentage": (quality_score / max_score) * 100 if max_score > 0 else 0,
        "found_elements": found_elements,
        "missing_elements": missing_elements,
        "word_count": word_count,
        "sentence_count": sentence_count,
        "technical_depth": technical_depth,
        "has_metrics": has_metrics,
        "has_project_details": has_project_details,
        "overall_quality": "Excellent" if quality_score >= max_score * 0.9 else
                          "Good" if quality_score >= max_score * 0.7 else
                          "Fair" if quality_score >= max_score * 0.5 else
                          "Poor"
    }

def test_quality_scenarios():
    """Test various quality scenarios."""
    print("🔍 Starting Answer Quality Assessment...")
    
    test_cases = [
        {
            "name": "Krishna AI - Role",
            "message": "What is your current role?",
            "profile": "krishna",
            "mode": "ai",
            "expected_elements": [
                "AI/ML Engineer", "Krishna", "5 years", "Walgreens", "RAG", "Databricks", "Pinecone", "OpenAI"
            ]
        },
        {
            "name": "Krishna DE - Role",
            "message": "What is your current role?",
            "profile": "krishna", 
            "mode": "de",
            "expected_elements": [
                "Data Engineer", "Krishna", "5 years", "Walgreens", "Azure", "Databricks", "Data Factory", "PySpark"
            ]
        },
        {
            "name": "Tejuu Analytics - Role",
            "message": "What is your current role?",
            "profile": "tejuu",
            "mode": "ae", 
            "expected_elements": [
                "Senior Analytics Engineer", "Central Bank", "6 years", "Azure", "Synapse", "Data Factory", "Databricks"
            ]
        },
        {
            "name": "Tejuu Business - Role",
            "message": "What is your current role?",
            "profile": "tejuu",
            "mode": "bi",
            "expected_elements": [
                "Senior Business Analyst", "Central Bank", "6 years", "Power BI", "SQL", "data visualization", "business intelligence"
            ]
        },
        {
            "name": "Krishna AI - Technical",
            "message": "How do you implement RAG pipelines?",
            "profile": "krishna",
            "mode": "ai",
            "expected_elements": [
                "RAG", "Databricks", "Pinecone", "OpenAI", "embedding", "pipeline", "pharmacists", "compliance"
            ]
        },
        {
            "name": "Tejuu Analytics - Technical", 
            "message": "How do you use dbt for data modeling?",
            "profile": "tejuu",
            "mode": "ae",
            "expected_elements": [
                "dbt", "data modeling", "dimensional", "star schema", "snowflake", "incremental", "materialization"
            ]
        },
        {
            "name": "Complex Technical Question",
            "message": "How do you handle schema evolution and data drift?",
            "profile": "krishna",
            "mode": "de", 
            "expected_elements": [
                "schema evolution", "data drift", "Delta Lake", "medallion", "Bronze", "Silver", "Gold", "pipeline"
            ]
        }
    ]
    
    results = []
    
    for test_case in test_cases:
        print(f"\n📊 Testing {test_case['name']}...")
        
        try:
            response = requests.post(
                f"{API_BASE}/chat",
                json={
                    "message": test_case["message"],
                    "profile": test_case["profile"],
                    "mode": test_case["mode"]
                },
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                answer = data.get("answer", "")
                
                # Assess quality
                quality_assessment = assess_answer_quality(answer, test_case["expected_elements"])
                quality_assessment["test_name"] = test_case["name"]
                quality_assessment["answer"] = answer
                results.append(quality_assessment)
                
                print(f"  ✅ Quality Score: {quality_assessment['quality_score']}/{quality_assessment['max_score']} ({quality_assessment['quality_percentage']:.1f}%)")
                print(f"  📝 Overall Quality: {quality_assessment['overall_quality']}")
                print(f"  🔧 Technical Depth: {quality_assessment['technical_depth']} indicators")
                print(f"  📊 Has Metrics: {'Yes' if quality_assessment['has_metrics'] else 'No'}")
                print(f"  🎯 Project Details: {'Yes' if quality_assessment['has_project_details'] else 'No'}")
                
                if quality_assessment['missing_elements']:
                    print(f"  ⚠️  Missing: {', '.join(quality_assessment['missing_elements'])}")
                    
            else:
                print(f"  ❌ Failed: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
    
    # Overall quality summary
    print("\n📈 Quality Summary:")
    if results:
        avg_quality = sum(r["quality_percentage"] for r in results) / len(results)
        avg_technical_depth = sum(r["technical_depth"] for r in results) / len(results)
        metrics_coverage = sum(1 for r in results if r["has_metrics"]) / len(results) * 100
        project_coverage = sum(1 for r in results if r["has_project_details"]) / len(results) * 100
        
        print(f"  Average Quality Score: {avg_quality:.1f}%")
        print(f"  Average Technical Depth: {avg_technical_depth:.1f} indicators")
        print(f"  Metrics Coverage: {metrics_coverage:.1f}%")
        print(f"  Project Details Coverage: {project_coverage:.1f}%")
        
        # Quality distribution
        excellent = sum(1 for r in results if r["overall_quality"] == "Excellent")
        good = sum(1 for r in results if r["overall_quality"] == "Good")
        fair = sum(1 for r in results if r["overall_quality"] == "Fair")
        poor = sum(1 for r in results if r["overall_quality"] == "Poor")
        
        print(f"\n  Quality Distribution:")
        print(f"    Excellent: {excellent}/{len(results)} ({excellent/len(results)*100:.1f}%)")
        print(f"    Good: {good}/{len(results)} ({good/len(results)*100:.1f}%)")
        print(f"    Fair: {fair}/{len(results)} ({fair/len(results)*100:.1f}%)")
        print(f"    Poor: {poor}/{len(results)} ({poor/len(results)*100:.1f}%)")
        
        # Overall assessment
        if avg_quality >= 90:
            overall_rating = "🏆 Excellent"
        elif avg_quality >= 80:
            overall_rating = "✅ Very Good"
        elif avg_quality >= 70:
            overall_rating = "👍 Good"
        elif avg_quality >= 60:
            overall_rating = "⚠️ Fair"
        else:
            overall_rating = "❌ Needs Improvement"
            
        print(f"\n  Overall Quality Rating: {overall_rating}")
    
    print(f"\n✅ Quality assessment complete!")

if __name__ == "__main__":
    test_quality_scenarios()
