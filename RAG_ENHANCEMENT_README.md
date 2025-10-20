# RAG Knowledge Normalization + Mode-Aware Indexing

## Overview

This enhancement implements a comprehensive RAG system with canonical knowledge base schema, mode-aware indexing, and interview-grade response generation. Both Krishna and Tejuu profiles now answer like seasoned pros in long-form interviews.

## Key Features

### 1. Canonical KB Schema
- **Consistent metadata structure** across all chunks
- **Mode-aware routing** (ai/de/ae/bi) with strict filtering
- **Quality scoring** for experience-based content prioritization
- **800-1000 token chunks** with 100-token overlap for optimal context

### 2. Enhanced Retrieval
- **Strict mode filtering** prevents cross-contamination between profiles
- **Quality-based reranking** prioritizes firsthand experience over generic guides
- **Section relevance boosting** for better context matching
- **Top-k optimization** (ai:6, de:4, ae:5, bi:5) based on content density

### 3. Interview-Grade Templates
- **Length knobs** for fuller responses (8-12 lines standard, 10-14 for intros)
- **Content-aware openings** with role/mode specific cues
- **Metrics integration** for concrete outcomes and measurable results
- **Follow-up support** with session memory and anchor bridging

### 4. Micro-KBs with Specific Metrics
- **Krishna AI/RAG**: Performance metrics, guardrails, LangGraph patterns
- **Krishna DE**: Delta optimizations, streaming SLA, production learnings
- **Tejuu AE**: dbt performance, semantic layer, governance frameworks
- **Tejuu BI**: Power BI governance, performance optimization, stakeholder management

## File Structure

```
rag-chatbot/
├── core/templates/
│   ├── ingest_patch.py          # Canonical schema ingestion
│   └── fragments/               # Enhanced template fragments
├── scripts/
│   └── generate_embeddings_normalized.py  # Enhanced ingestion script
├── kb_krishna/ai_ml/
│   ├── krishna_rag_metrics.md
│   ├── krishna_guardrails_ops.md
│   └── krishna_langgraph_patterns.md
├── kb_krishna/data_engineering/
│   ├── krishna_delta_optimizations.md
│   └── krishna_streaming_sla.md
├── kb_tejuu/analytics_mode/analytics_engineer/
│   ├── tejuu_dbt_perf.md
│   └── tejuu_semantic_layer.md
├── kb_tejuu/business_mode/business_intelligence/
│   ├── tejuu_pbi_governance.md
│   ├── tejuu_pbi_perf.md
│   └── tejuu_stakeholder_playbook.md
├── api/
│   ├── index.py                 # Enhanced API handler with Phase-2 metadata
│   └── utils.py                 # Enhanced retrieval with mode filtering
├── prompts/v1/
│   └── templates.yaml           # Enhanced templates with length knobs
└── test_rag_system.py           # Comprehensive test suite
```

## Setup Instructions

### 1. Environment Configuration
```bash
# Copy the example config
cp config.env.example .env

# Edit .env with your values
OPENAI_API_KEY=your_api_key_here
TEMPLATES_V2=true
USE_LLM=true
RETRIEVAL_TOPK=6
```

### 2. Rebuild Knowledge Base
```bash
# Run the enhanced ingestion script
python scripts/generate_embeddings_normalized.py
```

### 3. Start the Server
```bash
# Start the API server
python server.py
```

### 4. Run Tests
```bash
# Run comprehensive test suite
python test_rag_system.py
```

## API Usage

### Enhanced Chat Endpoint
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Walk me through your Walgreens RAG system end-to-end",
    "profile": "krishna",
    "mode": "ai",
    "session_id": "interview_1"
  }'
```

### Response Format
```json
{
  "answer": "Comprehensive interview-grade response...",
  "sources": [...],
  "intent": "technical_architecture",
  "confidence": 0.85,
  "template_used": "technical_architecture",
  "latency_ms": 1250,
  "timings": {
    "retrieval_ms": 200,
    "generation_ms": 800,
    "rewriter_ms": 250
  },
  "citations": [1, 2, 3],
  "domain_used": "ai",
  "profile_used": "krishna",
  "session_id": "interview_1"
}
```

## Performance Metrics

### Expected Performance
- **Success Rate**: 90%+ for interview-grade responses
- **Average Latency**: <3 seconds
- **Quality Score**: 4.0+/5.0
- **Response Length**: 8-12 lines (10-14 for intros)
- **Keyword Match**: 60%+ for domain-specific terms

### Mode-Specific Optimizations
- **AI Mode**: 6 chunks, hybrid retrieval benefits LLM answers
- **DE Mode**: 4 chunks, dense content, less noisy
- **AE Mode**: 5 chunks, balanced for analytics workflows
- **BI Mode**: 5 chunks, optimized for business intelligence

## Key Improvements

### 1. Knowledge Normalization
- **Canonical schema** ensures consistent metadata across all chunks
- **Mode-aware routing** prevents wrong content from appearing
- **Quality scoring** prioritizes experience over generic content

### 2. Retrieval Enhancement
- **Strict filtering** by profile+mode combination
- **Quality reranking** boosts firsthand experience content
- **Section relevance** improves context matching

### 3. Template System
- **Length knobs** for interview-appropriate response lengths
- **Content awareness** with role-specific openings
- **Metrics integration** for concrete, measurable outcomes

### 4. Micro-KB Content
- **Specific metrics** from real production experience
- **First-person narratives** that sound authentic
- **Concrete numbers** that interviewers love to hear

## Testing

The comprehensive test suite evaluates:
- **Health checks** for system availability
- **Query processing** across all profiles and modes
- **Response quality** with keyword matching and length validation
- **Performance metrics** including latency and confidence scores
- **Follow-up handling** with session memory

Run tests with:
```bash
python test_rag_system.py
```

## Troubleshooting

### Common Issues
1. **Low quality scores**: Check if micro-KBs are properly ingested
2. **Wrong mode responses**: Verify mode filtering in retrieval
3. **Short responses**: Ensure templates have proper length knobs
4. **Missing metrics**: Check if project_name and metrics variables are populated

### Debug Mode
Enable debug logging by setting environment variables:
```bash
export DEBUG=true
export LOG_LEVEL=DEBUG
```

## Next Steps

1. **Monitor performance** with the test suite
2. **Add more micro-KBs** for additional specific metrics
3. **Fine-tune templates** based on response quality
4. **Expand mode coverage** for additional domains
5. **Implement caching** for improved latency

## Support

For issues or questions:
1. Check the test suite output for specific failures
2. Review the logs for error messages
3. Verify environment configuration
4. Ensure all micro-KBs are properly ingested

The system is now ready for production use with interview-grade responses!
