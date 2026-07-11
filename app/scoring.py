"""
Internal scoring engine for candidate messages.

Scores messages deterministically based on:
- Specificity
- Category fit
- Merchant fit
- Trigger relevance
- Actionability
"""

from typing import Any


def score_message(message: str, category: dict, merchant: dict, trigger: dict, customer: dict = None) -> float:
    """
    Deterministically score a candidate message.
    Scores out of 50 (10 points per dimension).
    """
    score = 0.0
    msg_lower = message.lower()

    # 1. Specificity (0-10)
    # Check for numbers, dates, prices, specific offers
    import re
    nums = len(re.findall(r'\d+', msg_lower))
    score += min(10, nums * 2)

    # 2. Category fit (0-10)
    # Check if voice guidelines and allowed vocab are used
    voice = category.get("voice", {})
    allowed = voice.get("vocab_allowed", [])
    taboos = voice.get("vocab_taboo", [])
    
    cat_score = 5
    for word in allowed:
        if word.lower() in msg_lower:
            cat_score += 2
    for word in taboos:
        if word.lower() in msg_lower:
            cat_score -= 3
    score += min(10, max(0, cat_score))

    # 3. Merchant fit (0-10)
    # Check for merchant name, offer title, specific metrics
    merch_score = 0
    name = merchant.get("identity", {}).get("name", "").lower()
    owner = merchant.get("identity", {}).get("owner_first_name", "").lower()
    
    if name and name in msg_lower:
        merch_score += 3
    if owner and owner in msg_lower:
        merch_score += 3
        
    for offer in merchant.get("offers", []):
        if offer.get("title", "").lower() in msg_lower:
            merch_score += 4
            break
            
    score += min(10, merch_score)

    # 4. Trigger relevance (0-10)
    # Ensure payload keywords exist in message
    trig_score = 0
    payload = trigger.get("payload", {})
    
    if isinstance(payload, dict):
        # Flatten payload string values and check
        for v in payload.values():
            if isinstance(v, str) and v.lower() in msg_lower:
                trig_score += 2
            elif isinstance(v, (int, float)) and str(v) in msg_lower:
                trig_score += 2
                
    score += min(10, trig_score + 2) # Base score for using the correct template

    # 5. Actionability (Engagement Compulsion) (0-10)
    # Check for questions, low friction CTAs (Reply YES, 1 or 2)
    action_score = 3
    if "?" in message:
        action_score += 3
    if "reply" in msg_lower or "want me to" in msg_lower:
        action_score += 4
        
    score += min(10, action_score)

    return score
