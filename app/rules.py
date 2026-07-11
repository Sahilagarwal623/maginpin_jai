"""
Modular rule engine for engagement composition.

Each rule defines:
- condition: when to apply this rule
- priority: ranking if multiple apply
- action: the composition function to use
"""

from typing import Callable, Any, Optional
from app.templates import render_template
from app.suppression import generate_suppression_key


class Rule:
    def __init__(self, name: str, condition: Callable, priority: int, action: Callable):
        self.name = name
        self.condition = condition
        self.priority = priority
        self.action = action


def _default_action(category: dict, merchant: dict, trigger: dict, customer: Optional[dict]) -> dict:
    kind = trigger.get("kind", "unknown")
    msg, cta = render_template(kind, category, merchant, trigger, customer)
    supp_key = generate_suppression_key(category, trigger, customer)
    
    send_as = "vera"
    if trigger.get("scope") == "customer" and customer is not None:
        send_as = "merchant_on_behalf"
        
    return {
        "message": msg,
        "cta": cta,
        "send_as": send_as,
        "suppression_key": supp_key,
        "rationale": f"Composed using rule engine for trigger kind: {kind}"
    }


# The Rule Engine simply routes by trigger kind for now, but allows extension
RULES = [
    Rule(
        name="Catch-All Trigger Routing",
        condition=lambda c, m, t, cust: True,
        priority=1,
        action=_default_action
    )
]


def evaluate_rules(category: dict, merchant: dict, trigger: dict, customer: Optional[dict]) -> Optional[dict]:
    """
    Evaluate rules deterministically. Sorts by priority descending.
    Returns the result of the first matching rule.
    """
    sorted_rules = sorted(RULES, key=lambda r: r.priority, reverse=True)
    for rule in sorted_rules:
        if rule.condition(category, merchant, trigger, customer):
            return rule.action(category, merchant, trigger, customer)
    return None
