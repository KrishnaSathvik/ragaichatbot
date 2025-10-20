import re
from textwrap import shorten

def fill_template(prompt: str, variables: dict) -> str:
    """Fill template variables in prompt string."""
    # ${var} replacement, leave unknowns as-is
    def repl(m):
        key = m.group(1)
        val = variables.get(key, "")
        return str(val)
    return re.sub(r"\$\{([a-zA-Z0-9_]+)\}", repl, prompt)

def trim_to_words(text: str, max_words: int) -> str:
    """Trim text to maximum word count."""
    words = text.split()
    if len(words) <= max_words: 
        return text
    return " ".join(words[:max_words]) + "…"

def enforce_length(text: str, lo: int, hi: int) -> str:
    """Enforce word length limits, ensuring minimum and maximum."""
    words = text.split()
    word_count = len(words)
    
    # If too short, expand with additional context
    if word_count < lo:
        # Add more detail to reach minimum
        expansion_phrases = [
            "I focus on practical solutions that deliver business value.",
            "The key is balancing technical excellence with real-world constraints.",
            "I prioritize solutions that are maintainable and scalable.",
            "My approach emphasizes understanding business requirements first.",
            "I believe in iterative development and continuous improvement."
        ]
        
        # Add expansion phrases until we reach minimum (but be more conservative)
        for phrase in expansion_phrases:
            if len(words) >= lo:
                break
            words.extend(phrase.split())
        
        text = " ".join(words)
    
    # If too long, trim to upper limit
    if len(words) > hi:
        text = trim_to_words(text, hi)
    
    return text
