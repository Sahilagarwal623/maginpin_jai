"""
Unit tests for the composition engine.
"""

from app.composer import compose, handle_reply
from app.templates import render_template
from app.suppression import generate_suppression_key

def test_deterministic_output():
    category = {"slug": "dentists"}
    merchant = {"identity": {"name": "Dr. Meera's Clinic", "owner_first_name": "Meera"}}
    trigger = {"kind": "research_digest", "payload": {"top_item_id": "test_id"}}
    
    # First call
    result1 = compose(category, merchant, trigger)
    # Second call with identical inputs
    result2 = compose(category, merchant, trigger)
    
    assert result1.message == result2.message
    assert result1.suppression_key == result2.suppression_key

def test_category_specific_output():
    category_dentist = {"slug": "dentists"}
    merchant = {"identity": {"owner_first_name": "Meera", "name": "Meera Clinic"}}
    trigger = {"kind": "research_digest", "payload": {}}
    
    result_dentist = compose(category_dentist, merchant, trigger)
    assert "Dr. Meera" in result_dentist.message

    category_salon = {"slug": "salons"}
    merchant_salon = {"identity": {"owner_first_name": "Priya", "name": "Priya Salon"}}
    
    result_salon = compose(category_salon, merchant_salon, trigger)
    assert "Priya" in result_salon.message
    assert "Dr. Priya" not in result_salon.message

def test_intent_transition():
    state = [{"from": "vera", "msg": "Want to run a campaign?"}]
    reply = "yes please let's do it"
    merchant = {}
    
    result = handle_reply(state, reply, merchant)
    assert result["action"] == "send"
    assert result["cta"] == "none"

def test_auto_reply_detection():
    state = [
        {"from": "merchant", "msg": "Thank you for contacting us. We will get back to you."},
        {"from": "merchant", "msg": "Thank you for contacting us. We will get back to you."}
    ]
    reply = "Thank you for contacting us. We will get back to you."
    
    result = handle_reply(state, reply, {})
    assert result["action"] == "end"

def test_hostile_handling():
    state = []
    reply = "Stop messaging me this is useless spam"
    
    result = handle_reply(state, reply, {})
    assert result["action"] == "end"
