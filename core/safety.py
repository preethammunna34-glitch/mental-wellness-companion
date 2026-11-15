import re

# 1. Lexical Heuristics (Deterministic Override)
# These patterns bypass the LLM entirely to prevent hallucinations during a crisis.
CRISIS_PATTERNS = [
    r"\bhurt myself\b",
    r"\bsuicide\b",
    r"\bend it all\b",
    r"\bwant to die\b",
    r"\bkill myself\b",
    r"\boverdose\b"
]

def check_lexical_risk(user_input: str) -> bool:
    """Returns True if any high-risk regex patterns are detected."""
    text = user_input.lower()
    for pattern in CRISIS_PATTERNS:
        if re.search(pattern, text):
            return True
    return False

def get_semantic_risk_score(user_input: str) -> float:
    """
    Evaluates subtle distress signals. 
    In production, this would call an embedding classifier (e.g., a fine-tuned DistilBERT).
    For now, we use a mock scoring system to build the routing logic.
    """
    text = user_input.lower()
    passive_distress_phrases = ["pointless", "no way out", "too heavy", "give up", "can't do this anymore"]
    
    # Base safe score
    score = 0.1 
    
    # Elevate score if passive distress signals are found
    if any(phrase in text for phrase in passive_distress_phrases):
        score = 0.6  # Elevated, but stays below the 0.8 crisis threshold
        
    return score

def evaluate_safety(user_input: str) -> dict:
    """
    The main gatekeeper function called by the LangGraph router.
    """
    is_lexical_crisis = check_lexical_risk(user_input)
    semantic_score = get_semantic_risk_score(user_input)
    
    # Hard override: If keywords are found, instantly peg the risk score to maximum.
    final_score = 1.0 if is_lexical_crisis else semantic_score
    
    return {
        "risk_score": final_score,
        "is_safe": final_score < 0.8,
        "route": "crisis_protocol" if final_score >= 0.8 else "wellness_agent"
    }

# Quick local test to verify the logic
if __name__ == "__main__":
    print("Test 1 (Safe):", evaluate_safety("I'm feeling a bit stressed about work."))
    print("Test 2 (Passive):", evaluate_safety("Everything just feels pointless lately."))
    print("Test 3 (Crisis):", evaluate_safety("I want to end it all."))