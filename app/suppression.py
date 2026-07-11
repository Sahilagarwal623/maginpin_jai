"""
Suppression key generation and tracking.
Uses deterministic hashing based on category, trigger, and payload.
"""

import hashlib
import json
from typing import Any


def generate_suppression_key(category: dict, trigger: dict, customer: dict = None) -> str:
    """
    Generate a deterministic suppression key.
    Example: category + trigger_kind + target_id + timestamp/version
    """
    cat_slug = category.get("slug", "unknown")
    kind = trigger.get("kind", "unknown")
    
    # We use suppression key from trigger if provided, else generate one
    provided_key = trigger.get("suppression_key", "")
    if provided_key:
        return provided_key

    # Generate a stable hash if no suppression key provided
    payload = trigger.get("payload", {})
    
    components = [
        f"cat:{cat_slug}",
        f"kind:{kind}",
    ]
    
    if trigger.get("scope") == "customer" and customer:
        cust_id = customer.get("customer_id", "")
        components.append(f"cust:{cust_id}")
    else:
        merchant_id = trigger.get("merchant_id", "")
        components.append(f"merch:{merchant_id}")
        
    payload_str = json.dumps(payload, sort_keys=True)
    payload_hash = hashlib.md5(payload_str.encode("utf-8")).hexdigest()[:8]
    components.append(f"p:{payload_hash}")
    
    return "|".join(components)
