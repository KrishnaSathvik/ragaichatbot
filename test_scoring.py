#!/usr/bin/env python3
"""
Comprehensive KB Comparison & Scoring Test
Scores answers out of 10 based on accuracy, specificity, and authenticity
"""

from core.answer_v2 import answer_question_template_v2

def main():
    print('=== COMPREHENSIVE KB COMPARISON & SCORING ===')
    print('Scoring answers out of 10 based on accuracy, specificity, and authenticity')
    print('=' * 70)

    # Test cases covering all question types
    test_cases = [
        # INTRO QUESTIONS
        ('Give me a quick intro to your current role', 'krishna', 'de', 'intro_role', 'Krishna DE Intro'),
        ('Introduce yourself for a BI role', 'tejuu', 'business', 'intro_role', 'Tejuu Business Intro'),
        
        # PROJECT QUESTIONS
        ('What was the problem and outcome in your Walgreens pipeline project?', 'krishna', 'de', 'project_overview', 'Krishna DE Walgreens Project'),
        ('How did you design the ingestion + bronze/silver/gold layers?', 'krishna', 'de', 'project_how', 'Krishna DE Medallion Architecture'),
        ('Why did you choose Databricks over Snowflake?', 'krishna', 'de', 'project_why_tradeoffs', 'Krishna DE Tool Choice'),
        
        # ARCHITECTURE QUESTIONS
        ('Explain the end-to-end architecture of your RAG system', 'krishna', 'ai', 'architecture_system', 'Krishna AI RAG Architecture'),
        
        # DEBUG/PERFORMANCE QUESTIONS
        ('How did you debug the slow pipeline performance?', 'krishna', 'de', 'debug_perf', 'Krishna DE Performance Debug'),
        
        # GOVERNANCE QUESTIONS
        ('How do you implement RLS and certified datasets?', 'tejuu', 'business', 'governance_lineage', 'Tejuu Business Governance'),
        
        # TOOL MIGRATION QUESTIONS
        ('How did you migrate from Informatica to Databricks?', 'krishna', 'de', 'tool_migration', 'Krishna DE Migration'),
        
        # BEHAVIORAL QUESTIONS
        ('Tell me about a time you had to work with a difficult stakeholder', 'krishna', 'de', 'behavioral_star', 'Krishna DE Behavioral'),
        
        # CODING QUESTIONS (with constraints)
        ('Write SQL for Postgres to find top 3 products by revenue per month from sales table', 'krishna', 'de', 'coding_sql', 'Krishna DE SQL Query'),
        ('Write a DAX measure for 30-day rolling revenue using Sales table and Date column', 'tejuu', 'business', 'coding_dax', 'Tejuu Business DAX'),
        
        # FOLLOW-UP QUESTIONS
        ('You mentioned bronze/silver/gold - can you elaborate on the silver layer?', 'krishna', 'de', 'followup_drilldown', 'Krishna DE Follow-up'),
    ]

    total_score = 0
    total_questions = len(test_cases)

    for question, profile, mode, expected_intent, test_name in test_cases:
        print(f'\n🔍 {test_name}')
        print(f'Question: "{question}"')
        print(f'Profile: {profile} | Mode: {mode} | Intent: {expected_intent}')
        print('-' * 60)
        
        try:
            result = answer_question_template_v2(question, 'test_session', profile, mode)
            answer = result['answer']
            intent = result['intent']
            ask_first = result.get('ask_first', False)
            
            print(f'Intent: {intent}')
            print(f'Ask First: {ask_first}')
            print(f'Answer: {answer}')
            print()
            
            # Score based on KB comparison
            score = 0
            
            # Intent routing accuracy (2 points)
            if intent == expected_intent:
                score += 2
                print('✅ Intent routing correct (+2)')
            else:
                print(f'❌ Intent routing incorrect: {intent} vs {expected_intent} (+0)')
            
            # Ask-first behavior (1 point)
            if expected_intent in ['coding_sql', 'coding_dax', 'coding_python', 'scenario_runbook']:
                if ask_first:
                    score += 1
                    print('✅ Ask-first behavior correct (+1)')
                else:
                    print('❌ Should have asked first (+0)')
            else:
                if not ask_first:
                    score += 1
                    print('✅ Direct answer behavior correct (+1)')
                else:
                    print('❌ Should have answered directly (+0)')
            
            # Content quality vs KB (7 points)
            content_score = 0
            
            # Check for specific company mentions
            if profile == 'krishna' and ('Walgreens' in answer or 'TCS' in answer):
                content_score += 1
                print('✅ Company mentioned (+1)')
            elif profile == 'tejuu' and ('Central Bank' in answer or 'Missouri' in answer):
                content_score += 1
                print('✅ Company mentioned (+1)')
            else:
                print('❌ Missing company context (+0)')
            
            # Check for specific technologies
            tech_terms = []
            if mode == 'de':
                tech_terms = ['Databricks', 'PySpark', 'Delta Lake', 'Azure', 'medallion']
            elif mode == 'ai':
                tech_terms = ['RAG', 'Pinecone', 'OpenAI', 'Databricks', 'embeddings']
            elif mode == 'business':
                tech_terms = ['Power BI', 'DAX', 'RLS', 'certified datasets']
            elif mode == 'analytics':
                tech_terms = ['dbt', 'Azure', 'Power BI', 'staging', 'marts']
            
            tech_mentioned = sum(1 for term in tech_terms if term.lower() in answer.lower())
            if tech_mentioned >= 2:
                content_score += 2
                print(f'✅ Technologies mentioned: {tech_mentioned}/5 (+2)')
            elif tech_mentioned >= 1:
                content_score += 1
                print(f'⚠️ Some technologies mentioned: {tech_mentioned}/5 (+1)')
            else:
                print(f'❌ Missing technology context: {tech_mentioned}/5 (+0)')
            
            # Check for specific metrics (if appropriate)
            if expected_intent in ['project_overview', 'debug_perf', 'architecture_system']:
                metric_terms = ['10TB', '35%', '8 hours', 'T+4', '500+', '60%', '45%', '25%']
                metrics_mentioned = sum(1 for term in metric_terms if term in answer)
                if metrics_mentioned >= 1:
                    content_score += 1
                    print(f'✅ Specific metrics mentioned: {metrics_mentioned} (+1)')
                else:
                    print('❌ Missing specific metrics (+0)')
            else:
                content_score += 1
                print('✅ Metrics not required for this question type (+1)')
            
            # Check for project-specific details
            if 'project' in expected_intent or 'architecture' in expected_intent:
                if 'pharmacy' in answer.lower() or 'compliance' in answer.lower() or 'bronze' in answer.lower():
                    content_score += 1
                    print('✅ Project-specific details mentioned (+1)')
                else:
                    print('❌ Missing project-specific details (+0)')
            else:
                content_score += 1
                print('✅ Project details not required for this question type (+1)')
            
            # Check for natural, human-like tone
            if len(answer.split()) >= 20 and not answer.startswith('```'):
                content_score += 1
                print('✅ Natural, detailed response (+1)')
            else:
                print('❌ Response too brief or code-only (+0)')
            
            # Check for proper role alignment
            if profile == 'tejuu' and mode == 'business' and 'Business Analyst' in answer:
                content_score += 1
                print('✅ Correct role alignment (+1)')
            elif profile == 'krishna' and mode == 'de' and 'Data Engineer' in answer:
                content_score += 1
                print('✅ Correct role alignment (+1)')
            elif profile == 'krishna' and mode == 'ai' and ('AI' in answer or 'ML' in answer or 'RAG' in answer):
                content_score += 1
                print('✅ Correct role alignment (+1)')
            else:
                print('❌ Role alignment unclear (+0)')
            
            total_score += score
            print(f'\n📊 SCORE: {score}/10')
            print(f'   Intent: 2/2, Behavior: 1/1, Content: {content_score}/7')
            
        except Exception as e:
            print(f'❌ Error: {e}')
            total_score += 0
            print(f'\n📊 SCORE: 0/10 (Error)')
        
        print('=' * 60)

    print(f'\n🎯 FINAL RESULTS:')
    print(f'Total Score: {total_score}/{total_questions * 10} ({total_score / (total_questions * 10) * 100:.1f}%)')
    print(f'Average Score: {total_score / total_questions:.1f}/10')
    print(f'Questions Tested: {total_questions}')

if __name__ == '__main__':
    main()
