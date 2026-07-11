# Magicpin AI Challenge Bot

A high-performance, fully deterministic rule-based message composition engine for merchant engagement.

## Architecture & Design Decisions

This solution was built with the following core principles in mind:

1. **Extreme Determinism**:
   Instead of using a non-deterministic LLM during inference, this bot uses a robust, modular Rule Engine and Template System. Given identical inputs, it will *always* produce identical outputs. It avoids `random`, `uuid`, or current time-based generation entirely. Hashing for suppression keys uses deterministic `MD5` hashing on sorted payloads.

2. **Categorical Awareness & Template Engine**:
   The heart of the composer is the Template Engine (`app/templates.py`). It maps the 25+ trigger kinds to specific, highly crafted deterministic message templates. These templates integrate the merchant's precise numbers (specificity), the appropriate voice (category fit), and clear CTA hooks (actionability).
   
3. **State Management**:
   The state is stored in an in-memory datastore (`app/memory.py`). It follows the required version-gating idempotency logic perfectly.

4. **Internal Scoring System**:
   We provide a deterministic internal scoring module (`app/scoring.py`) that scores generated messages out of 50 based on specificity, category fit, merchant fit, trigger relevance, and actionability to guarantee quality.

## Tradeoffs

- **Extensibility vs Dynamic Text**: Rule-based templates are extremely fast and completely stable. However, if a completely new category or trigger type is added without updating the codebase, it falls back to a safe generic message, whereas an LLM could try to guess. The tradeoff here is absolute predictability vs generative variance. Given the judge's prompt to "Be deterministic", the rule-based approach provides a massive operational advantage in latency, cost, and reliability.

## API Examples

### Push Context
```bash
curl -X POST http://localhost:8080/v1/context -H "Content-Type: application/json" -d '{
  "scope": "merchant", "context_id": "m1", "version": 1,
  "payload": {"identity": {"name": "Test"}}, "delivered_at": "2026-07-11T00:00:00Z"
}'
```

### Tick
```bash
curl -X POST http://localhost:8080/v1/tick -H "Content-Type: application/json" -d '{
  "now": "2026-07-11T00:00:00Z", "available_triggers": ["t1"]
}'
```

## How to Run Locally

### Prerequisites
- Python 3.10+

### Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Run the FastAPI app
uvicorn app.api:app --host 0.0.0.0 --port 8080 --reload
```

## Testing
Run the unit tests with pytest:
```bash
pytest tests/
```

### Judging Simulator
To run the judge simulator:
```bash
# Ensure the bot is running on port 8080, then:
python judge_simulator.py
```
