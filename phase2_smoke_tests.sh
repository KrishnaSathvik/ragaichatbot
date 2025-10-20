#!/usr/bin/env bash
set -euo pipefail

API_URL="${API_URL:-http://localhost:8000}"
JQ_FILTER='{intent:.intent, confidence:.confidence, profile_used:.profile_used, domain_used:.domain_used, qtype_used:.qtype_used, answer:(.answer|tostring|.[0:320])}'

call() {
  local msg="$1" profile="$2" mode="$3" audience="${4:-hiring_manager}" depth="${5:-normal}" sid="${6:-auto_$$}"
  echo -e "\n🔹 $(echo ${profile} | tr '[:lower:]' '[:upper:]')/$(echo ${mode} | tr '[:lower:]' '[:upper:]') | ${msg}"
  curl -s "${API_URL}/api/chat" \
    -H "Content-Type: application/json" \
    -d "{\"message\": \"${msg}\", \"profile\": \"${profile}\", \"mode\": \"${mode}\", \"audience\": \"${audience}\", \"depth\": \"${depth}\", \"session_id\": \"${sid}\"}" \
  | jq "$JQ_FILTER"
}

echo "=== Phase-2 Interview QA Smoke Tests ==="
echo "API: $API_URL"
echo "----------------------------------------"

############################################
# 1) KRISHNA — DATA ENGINEERING (de)
############################################
# Expect intents: intro_role, project_overview, project_how, project_why_tradeoffs, architecture_system, debug_perf, coding_sql
SID="krishna_de_$RANDOM"

call "Give me a quick intro to your current role"            krishna de recruiter short "$SID"   # intro_role
call "What was the problem and outcome in your Walgreens pipeline project?" krishna de hiring_manager normal "$SID"  # project_overview
call "How did you design the ingestion + bronze/silver/gold layers on Databricks?" krishna de hiring_manager deep "$SID" # project_how
call "Why Delta Live Tables instead of Airflow for orchestration? Trade-offs?"     krishna de hiring_manager normal "$SID" # project_why_tradeoffs
call "Walk me through the batch + streaming architecture, end-to-end"              krishna de hiring_manager deep "$SID" # architecture_system
call "You hit skew and long shuffles in a 2TB job—how did you diagnose and fix it?" krishna de hiring_manager normal "$SID" # debug_perf
call "Write a SQL query to find top 3 products by revenue per month"               krishna de staff_panel normal "$SID"    # coding_sql

############################################
# 2) KRISHNA — AI/ML / GenAI (ai)
############################################
# Expect intents: intro_role, project_overview, project_how, project_why_tradeoffs, architecture_system, debug_perf, tool_migration, coding_sql (PySpark ok)
SID="krishna_ai_$RANDOM"

call "Give me a short intro focused on your GenAI responsibilities"                krishna ai recruiter short "$SID" # intro_role
call "Explain the RAG project you shipped—who used it and what it solved"          krishna ai hiring_manager normal "$SID" # project_overview
call "How exactly did you implement hybrid retrieval (BM25 + vector) and reranking?" krishna ai hiring_manager deep "$SID" # project_how
call "Why LangGraph over agent loops? What trade-offs did you weigh?"              krishna ai hiring_manager normal "$SID" # project_why_tradeoffs
call "Describe the production architecture: ingestion→indexing→retriever→reranker→generator→guardrails" krishna ai hiring_manager deep "$SID" # architecture_system
call "Latency spiked on p95: how did you debug and bring it back down?"            krishna ai hiring_manager normal "$SID" # debug_perf
call "If you had to migrate from LangChain to LlamaIndex, what's your plan?"       krishna ai hiring_manager normal "$SID" # tool_migration

############################################
# 3) TEJUU — ANALYTICS ENGINEER (analytics)
############################################
# Expect intents: intro_role, project_overview, project_how, project_why_tradeoffs, governance_lineage, debug_perf, coding_sql
SID="tejuu_analytics_$RANDOM"

call "Quick intro to your AE role and scope"                                      tejuu analytics recruiter short "$SID" # intro_role
call "Describe your dbt project structure—staging/intermediate/marts and tests"   tejuu analytics hiring_manager normal "$SID" # project_overview
call "How did you cut dbt runtime by ~40%? Walk the steps (models, macros, deps)" tejuu analytics hiring_manager deep "$SID" # project_how
call "Why dbt over Dataform for your stack? Trade-offs and migration risks?"      tejuu analytics hiring_manager normal "$SID" # project_why_tradeoffs
call "How do you enforce data contracts, exposures, and lineage in dbt?"          tejuu analytics hiring_manager normal "$SID" # governance_lineage
call "A specific model took 45m. How did you find the bottleneck and optimize it?" tejuu analytics hiring_manager normal "$SID" # debug_perf
call "Write a SQL query to compute 7-day rolling active users by region"          tejuu analytics staff_panel normal "$SID" # coding_sql

############################################
# 4) TEJUU — BUSINESS INTELLIGENCE (business)
############################################
# Expect intents: intro_role, governance_lineage, project_overview, project_how, project_why_tradeoffs, coding_sql (DAX/M)
SID="tejuu_business_$RANDOM"

call "Introduce yourself for a BI role—keep it concise"                           tejuu business recruiter short "$SID" # intro_role
call "How do you implement RLS and certified datasets, and support self-service?" tejuu business hiring_manager normal "$SID" # governance_lineage
call "Give a high-level overview of a Power BI migration you led"                 tejuu business hiring_manager normal "$SID" # project_overview
call "How did you model the semantic layer and measures for executive dashboards?" tejuu business hiring_manager deep "$SID" # project_how
call "Why Fabric over Synapse+ADF for BI delivery? Discuss trade-offs"            tejuu business hiring_manager normal "$SID" # project_why_tradeoffs
call "Write a DAX measure for 30-day rolling revenue and explain it briefly"      tejuu business staff_panel normal "$SID" # coding_sql

echo -e "\n✅ Done."
