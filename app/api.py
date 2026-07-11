"""
FastAPI application defining the required endpoints for the AI Challenge.
"""

import time
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.models import (
    ContextPushRequest, ContextPushAccepted, ContextPushRejected,
    TickRequest, TickResponse, TickAction,
    ReplyRequest, ReplyResponse,
    HealthResponse, MetadataResponse
)
from app.memory import Memory
from app.composer import compose, handle_reply
from app.scoring import score_message

app = FastAPI(title="Magicpin AI Challenge Bot")
START_TIME = time.time()
memory = Memory()


@app.get("/v1/healthz", response_model=HealthResponse)
async def healthz():
    """Liveness probe."""
    return HealthResponse(
        uptime_seconds=int(time.time() - START_TIME),
        contexts_loaded=memory.count_by_scope()
    )


@app.get("/v1/metadata", response_model=MetadataResponse)
async def metadata():
    """Bot identity."""
    return MetadataResponse()


@app.post("/v1/context")
async def push_context(req: ContextPushRequest):
    """Receive a context push."""
    accepted, curr_ver = memory.store_context(
        scope=req.scope,
        context_id=req.context_id,
        version=req.version,
        payload=req.payload
    )
    
    if not accepted:
        return JSONResponse(
            status_code=409,
            content=ContextPushRejected(
                reason="stale_version",
                current_version=curr_ver
            ).model_dump()
        )
        
    return ContextPushAccepted(
        ack_id=f"ack_{req.context_id}_v{req.version}",
        stored_at=datetime.utcnow().isoformat() + "Z"
    )


@app.post("/v1/tick", response_model=TickResponse)
async def tick(req: TickRequest):
    """Periodic wake-up; bot can initiate."""
    actions = []
    
    # Sort triggers for determinism
    for trg_id in sorted(req.available_triggers):
        trigger = memory.get_context("trigger", trg_id)
        if not trigger:
            continue
            
        merchant_id = trigger.get("merchant_id")
        if not merchant_id:
            continue
            
        merchant = memory.get_context("merchant", merchant_id)
        if not merchant:
            continue
            
        cat_slug = merchant.get("category_slug")
        category = memory.get_context("category", cat_slug) if cat_slug else None
        if not category:
            continue
            
        customer = None
        customer_id = trigger.get("customer_id")
        if customer_id:
            customer = memory.get_context("customer", customer_id)
            
        # Compose message
        composed = compose(category, merchant, trigger, customer)
        
        # Check suppression
        if memory.is_suppressed(composed.suppression_key):
            continue
            
        # Score the message internally (optional, but good for reporting)
        score = score_message(composed.message, category, merchant, trigger, customer)
        
        actions.append(TickAction(
            conversation_id=f"conv_{merchant_id}_{trg_id}",
            merchant_id=merchant_id,
            customer_id=customer_id,
            send_as=composed.send_as,
            trigger_id=trg_id,
            template_name="vera_generic_v1",
            template_params=[],
            body=composed.message,
            cta=composed.cta,
            suppression_key=composed.suppression_key,
            rationale=f"{composed.rationale} (Score: {score:.1f}/50)"
        ))
        
        # Suppress future sends
        memory.suppress(composed.suppression_key)

    return TickResponse(actions=actions)


@app.post("/v1/reply", response_model=ReplyResponse)
async def reply(req: ReplyRequest):
    """Receive a reply from the simulated merchant/customer."""
    # Store incoming message
    memory.append_turn(
        req.conversation_id,
        {"from": req.from_role, "msg": req.message}
    )
    
    state = memory.get_conversation(req.conversation_id)
    merchant = memory.get_context("merchant", req.merchant_id) if req.merchant_id else {}
    customer = memory.get_context("customer", req.customer_id) if req.customer_id else None
    
    # Let the deterministic handler generate the reply
    result = handle_reply(state, req.message, merchant, customer)
    
    if result.get("action") == "send":
        # Store outgoing message
        memory.append_turn(
            req.conversation_id,
            {"from": "vera", "msg": result.get("body", "")}
        )
        
    return ReplyResponse(**result)


@app.post("/v1/teardown")
async def teardown():
    """Optional teardown hook to clean up memory."""
    memory.clear_all()
    return {"status": "ok"}
