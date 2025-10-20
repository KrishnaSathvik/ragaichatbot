from collections import deque
from typing import Dict, List, Any
import re

class ShortMemory:
    """Session-scoped conversation memory with enhanced context tracking."""
    
    def __init__(self, max_turns: int = 5):  # Increased from 3 to 5
        self.sessions: Dict[str, deque] = {}
        self.max_turns = max_turns
    
    def get(self, session_id: str) -> deque:
        """Get conversation history for session."""
        return self.sessions.get(session_id, deque(maxlen=self.max_turns))
    
    def add(self, session_id: str, qa_pair: Dict[str, str]):
        """Add Q/A pair to session memory."""
        if session_id not in self.sessions:
            self.sessions[session_id] = deque(maxlen=self.max_turns)
        self.sessions[session_id].append(qa_pair)
    
    def get_prior_point(self, session_id: str) -> str:
        """Get last mentioned point for follow-up questions."""
        history = self.get(session_id)
        if not history:
            return ""
        # Extract key points from last answer
        last_answer = history[-1].get("a", "")
        # Simple extraction - could be enhanced
        if "mentioned" in last_answer.lower():
            return "the approach I mentioned"
        elif "built" in last_answer.lower():
            return "the system I built"
        else:
            return "my previous experience"
    
    def get_last_topic(self, session_id: str) -> str:
        """Get the main topic from the last conversation turn."""
        history = self.get(session_id)
        if not history:
            return ""
        
        last_answer = history[-1].get("a", "").lower()
        
        # Look for project mentions
        if "walgreens" in last_answer and "project" in last_answer:
            return "the Walgreens project"
        elif "central bank" in last_answer and "project" in last_answer:
            return "the Central Bank project"
        elif "stryker" in last_answer and "project" in last_answer:
            return "the Stryker project"
        
        # Look for technical concepts
        tech_terms = [
            "partitioning", "optimization", "performance", "latency", "throughput",
            "rag system", "hybrid retrieval", "reranking", "embeddings",
            "dbt models", "semantic model", "power bi", "fabric",
            "delta lake", "medallion architecture", "azure", "databricks"
        ]
        
        for term in tech_terms:
            if term in last_answer:
                return term
        
        return "my previous experience"
    
    def get_conversation_context(self, session_id: str) -> str:
        """Get a summary of recent conversation context."""
        history = self.get(session_id)
        if not history:
            return ""
        
        # Get last 2-3 turns for context
        recent_turns = list(history)[-2:]
        context_parts = []
        
        for turn in recent_turns:
            q = turn.get("q", "")
            a = turn.get("a", "")
            if q and a:
                # Extract key terms from question and answer
                key_terms = self._extract_key_terms(q + " " + a)
                if key_terms:
                    context_parts.append(" ".join(key_terms[:3]))  # Top 3 terms
        
        return " ".join(context_parts)
    
    def _extract_key_terms(self, text: str) -> List[str]:
        """Extract key technical terms from text."""
        # Look for technical terms, company names, and metrics
        terms = []
        
        # Company names
        companies = ["walgreens", "central bank", "stryker", "tcs", "cvs", "mckesson"]
        for company in companies:
            if company in text.lower():
                terms.append(company)
        
        # Technical terms
        tech_terms = [
            "partitioning", "optimization", "performance", "latency", "throughput",
            "rag", "retrieval", "reranking", "embeddings", "dbt", "semantic",
            "power bi", "fabric", "delta lake", "medallion", "azure", "databricks",
            "pipeline", "etl", "data transformation", "data modeling"
        ]
        
        for term in tech_terms:
            if term in text.lower():
                terms.append(term)
        
        # Metrics
        metric_pattern = r'\b\d+(?:\.\d+)?\s*(?:%|TB|GB|hours?|minutes?|users?|M|K)\b'
        metrics = re.findall(metric_pattern, text, re.I)
        terms.extend(metrics)
        
        return terms
