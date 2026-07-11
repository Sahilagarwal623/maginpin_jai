"""
Category-aware message templates for deterministic composition.
Each trigger kind has a template function that takes extracted facts
and returns a message body + CTA.
"""
from __future__ import annotations
from typing import Any, Optional


def _get_merchant_name(merchant: dict) -> str:
    identity = merchant.get("identity", {})
    return identity.get("name", "there")


def _get_owner_name(merchant: dict) -> str:
    identity = merchant.get("identity", {})
    return identity.get("owner_first_name", "")


def _get_salutation(category: dict, merchant: dict) -> str:
    slug = category.get("slug", "")
    owner = _get_owner_name(merchant)
    if slug == "dentists" and owner:
        return f"Dr. {owner}"
    if owner:
        return owner
    return _get_merchant_name(merchant)


def _get_active_offers(merchant: dict) -> list[dict]:
    return [o for o in merchant.get("offers", []) if o.get("status") == "active"]


def _fmt_pct(val: float) -> str:
    return f"{abs(int(val * 100))}%"


# ── RESEARCH DIGEST ──────────────────────────────────

def template_research_digest(category: dict, merchant: dict, trigger: dict, customer: Optional[dict] = None) -> tuple[str, str]:
    sal = _get_salutation(category, merchant)
    payload = trigger.get("payload", {})
    top_item_id = payload.get("top_item_id", "")
    digest_items = category.get("digest", [])
    item = next((d for d in digest_items if d.get("id") == top_item_id), None)
    if not item:
        item = digest_items[0] if digest_items else {}
    title = item.get("title", "new research update")
    source = item.get("source", "")
    trial_n = item.get("trial_n")
    summary = item.get("summary", "")
    actionable = item.get("actionable", "")
    parts = [f"{sal}, {source.split(',')[0] if source else 'latest research'} just dropped."]
    if trial_n:
        parts.append(f"Key finding ({trial_n:,}-patient trial): {title}.")
    else:
        parts.append(f"Key finding: {title}.")
    if actionable:
        parts.append(f"{actionable}.")
    parts.append("Want me to pull the details?")
    if source:
        parts.append(f"— {source}")
    return " ".join(parts), "open_ended"


# ── REGULATION / COMPLIANCE ──────────────────────────

def template_regulation_change(category: dict, merchant: dict, trigger: dict, customer: Optional[dict] = None) -> tuple[str, str]:
    sal = _get_salutation(category, merchant)
    payload = trigger.get("payload", {})
    top_item_id = payload.get("top_item_id", "")
    deadline = payload.get("deadline_iso", "")
    digest_items = category.get("digest", [])
    item = next((d for d in digest_items if d.get("id") == top_item_id), None)
    if not item:
        item = digest_items[0] if digest_items else {}
    title = item.get("title", "regulatory update")
    source = item.get("source", "")
    actionable = item.get("actionable", "")
    parts = [f"{sal}, heads up — {title}."]
    if deadline:
        parts.append(f"Deadline: {deadline[:10]}.")
    if actionable:
        parts.append(actionable + ".")
    parts.append("Need help reviewing your setup?")
    if source:
        parts.append(f"— {source}")
    return " ".join(parts), "open_ended"


# ── PERFORMANCE DIP ──────────────────────────────────

def template_perf_dip(category: dict, merchant: dict, trigger: dict, customer: Optional[dict] = None) -> tuple[str, str]:
    sal = _get_salutation(category, merchant)
    payload = trigger.get("payload", {})
    metric = payload.get("metric", "performance")
    delta = payload.get("delta_pct", 0)
    window = payload.get("window", "7d")
    offers = _get_active_offers(merchant)
    parts = [f"{sal}, your {metric} dropped {_fmt_pct(delta)} this {window}."]
    if offers:
        parts.append(f"Your \"{offers[0]['title']}\" offer is still active — promoting it could help recover.")
    else:
        peer_stats = category.get("peer_stats", {})
        avg_ctr = peer_stats.get("avg_ctr")
        if avg_ctr:
            parts.append(f"Peer median CTR is {avg_ctr:.1%} — running a service+price offer could close the gap.")
    parts.append("Want me to draft a campaign?")
    return " ".join(parts), "open_ended"


# ── PERFORMANCE SPIKE ────────────────────────────────

def template_perf_spike(category: dict, merchant: dict, trigger: dict, customer: Optional[dict] = None) -> tuple[str, str]:
    sal = _get_salutation(category, merchant)
    payload = trigger.get("payload", {})
    metric = payload.get("metric", "views")
    delta = payload.get("delta_pct", 0)
    driver = payload.get("likely_driver", "")
    parts = [f"{sal}, good signal — your {metric} are up {_fmt_pct(delta)} this week."]
    if driver:
        parts.append(f"Likely driver: {driver.replace('_', ' ')}.")
    parts.append("Want to capitalize with a push?")
    return " ".join(parts), "open_ended"


# ── RENEWAL DUE ──────────────────────────────────────

def template_renewal_due(category: dict, merchant: dict, trigger: dict, customer: Optional[dict] = None) -> tuple[str, str]:
    sal = _get_salutation(category, merchant)
    payload = trigger.get("payload", {})
    days = payload.get("days_remaining", 0)
    plan = payload.get("plan", "")
    perf = merchant.get("performance", {})
    views = perf.get("views", 0)
    calls = perf.get("calls", 0)
    parts = [f"{sal}, your {plan} subscription expires in {days} days."]
    if views or calls:
        parts.append(f"In the last 30 days: {views:,} views, {calls} calls.")
    parts.append("Renewing keeps your listing active + offers visible. Want to continue?")
    return " ".join(parts), "open_ended"


# ── FESTIVAL UPCOMING ────────────────────────────────

def template_festival(category: dict, merchant: dict, trigger: dict, customer: Optional[dict] = None) -> tuple[str, str]:
    sal = _get_salutation(category, merchant)
    payload = trigger.get("payload", {})
    festival = payload.get("festival", "upcoming festival")
    days_until = payload.get("days_until", 0)
    offers = _get_active_offers(merchant)
    parts = [f"{sal}, {festival} is {days_until} days away."]
    if offers:
        parts.append(f"Your \"{offers[0]['title']}\" could get a festive boost.")
    else:
        parts.append("Running a festive offer now could capture early planners.")
    parts.append("Want me to set up a campaign?")
    return " ".join(parts), "open_ended"


# ── RECALL DUE (customer-facing) ─────────────────────

def template_recall_due(category: dict, merchant: dict, trigger: dict, customer: Optional[dict] = None) -> tuple[str, str]:
    merchant_name = _get_merchant_name(merchant)
    payload = trigger.get("payload", {})
    service_due = payload.get("service_due", "").replace("_", " ")
    slots = payload.get("available_slots", [])
    offers = _get_active_offers(merchant)
    cust_name = ""
    lang = "en"
    if customer:
        cust_name = customer.get("identity", {}).get("name", "")
        lang = customer.get("identity", {}).get("language_pref", "en")
    greeting = f"Hi {cust_name}" if cust_name else "Hi"
    parts = [f"{greeting}, {merchant_name} here."]
    if service_due:
        parts.append(f"Your {service_due} is coming up.")
    if slots:
        slot_strs = [s.get("label", "") for s in slots[:2] if s.get("label")]
        if slot_strs:
            if "hi" in lang.lower():
                parts.append(f"Aapke liye slots ready hain: {' ya '.join(slot_strs)}.")
            else:
                parts.append(f"Available slots: {' or '.join(slot_strs)}.")
    if offers:
        parts.append(f"{offers[0]['title']}.")
    if len(slots) == 2:
        parts.append("Reply 1 or 2 to book, or tell us a time that works.")
    else:
        parts.append("Reply to book or suggest a time.")
    return " ".join(parts), "open_ended"


# ── REVIEW THEME EMERGED ─────────────────────────────

def template_review_theme(category: dict, merchant: dict, trigger: dict, customer: Optional[dict] = None) -> tuple[str, str]:
    sal = _get_salutation(category, merchant)
    payload = trigger.get("payload", {})
    theme = payload.get("theme", "").replace("_", " ")
    count = payload.get("occurrences_30d", 0)
    quote = payload.get("common_quote", "")
    parts = [f"{sal}, noticed a pattern in your reviews — \"{theme}\" came up {count} times this month."]
    if quote:
        parts.append(f"Sample: \"{quote}\".")
    parts.append("Want to address it or reply to those reviews?")
    return " ".join(parts), "open_ended"


# ── MILESTONE REACHED ────────────────────────────────

def template_milestone(category: dict, merchant: dict, trigger: dict, customer: Optional[dict] = None) -> tuple[str, str]:
    sal = _get_salutation(category, merchant)
    payload = trigger.get("payload", {})
    metric = payload.get("metric", "").replace("_", " ")
    value = payload.get("value_now", 0)
    milestone = payload.get("milestone_value", 0)
    imminent = payload.get("is_imminent", False)
    if imminent:
        parts = [f"{sal}, you're at {value} {metric} — just {milestone - value} away from {milestone}!"]
        parts.append("A quick review push could get you there this week. Want me to set it up?")
    else:
        parts = [f"{sal}, congrats — you crossed {milestone} {metric}!"]
        parts.append("Want to celebrate with a special offer for your customers?")
    return " ".join(parts), "open_ended"


# ── IPL MATCH ────────────────────────────────────────

def template_ipl_match(category: dict, merchant: dict, trigger: dict, customer: Optional[dict] = None) -> tuple[str, str]:
    sal = _get_salutation(category, merchant)
    payload = trigger.get("payload", {})
    match = payload.get("match", "")
    city = payload.get("city", "")
    offers = _get_active_offers(merchant)
    parts = [f"{sal}, {match} tonight in {city}."]
    if offers:
        parts.append(f"Your \"{offers[0]['title']}\" could ride the match-night crowd.")
    else:
        parts.append("Match nights usually boost orders — running a combo deal could capture it.")
    parts.append("Want me to push a match-night post?")
    return " ".join(parts), "open_ended"


# ── ACTIVE PLANNING INTENT ───────────────────────────

def template_active_planning(category: dict, merchant: dict, trigger: dict, customer: Optional[dict] = None) -> tuple[str, str]:
    sal = _get_salutation(category, merchant)
    payload = trigger.get("payload", {})
    topic = payload.get("intent_topic", "").replace("_", " ")
    parts = [f"{sal}, following up on the {topic} discussion."]
    parts.append("I've drafted a plan — want me to share it so you can review?")
    return " ".join(parts), "open_ended"


# ── WINBACK ELIGIBLE ─────────────────────────────────

def template_winback(category: dict, merchant: dict, trigger: dict, customer: Optional[dict] = None) -> tuple[str, str]:
    sal = _get_salutation(category, merchant)
    payload = trigger.get("payload", {})
    days = payload.get("days_since_expiry", 0)
    dip = payload.get("perf_dip_pct", 0)
    perf = merchant.get("performance", {})
    views = perf.get("views", 0)
    parts = [f"{sal}, it's been {days} days since your subscription paused."]
    if dip:
        parts.append(f"Your visibility has dropped {_fmt_pct(dip)} since then.")
    if views:
        parts.append(f"Still getting {views:,} views/month though — reactivating would convert more of those to calls.")
    parts.append("Want to hear what's changed since you left?")
    return " ".join(parts), "open_ended"


# ── SUPPLY ALERT ─────────────────────────────────────

def template_supply_alert(category: dict, merchant: dict, trigger: dict, customer: Optional[dict] = None) -> tuple[str, str]:
    sal = _get_salutation(category, merchant)
    payload = trigger.get("payload", {})
    molecule = payload.get("molecule", "product")
    batches = payload.get("affected_batches", [])
    mfr = payload.get("manufacturer", "")
    parts = [f"{sal}, urgent — voluntary recall on {molecule} batches {', '.join(batches[:3])} by {mfr}."]
    parts.append("Want me to filter your customer list for that molecule so you can notify them?")
    return " ".join(parts), "open_ended"


# ── CHRONIC REFILL DUE (customer-facing) ─────────────

def template_chronic_refill(category: dict, merchant: dict, trigger: dict, customer: Optional[dict] = None) -> tuple[str, str]:
    merchant_name = _get_merchant_name(merchant)
    payload = trigger.get("payload", {})
    molecules = payload.get("molecule_list", [])
    runs_out = payload.get("stock_runs_out_iso", "")[:10]
    delivery_saved = payload.get("delivery_address_saved", False)
    cust_name = ""
    if customer:
        cust_name = customer.get("identity", {}).get("name", "")
    greeting = f"Namaste {cust_name}" if cust_name else "Namaste"
    mol_str = ", ".join(molecules[:3])
    parts = [f"{greeting}, {merchant_name} se."]
    parts.append(f"Aapki {mol_str} supply {runs_out} tak khatam ho jayegi.")
    if delivery_saved:
        parts.append("Aapka delivery address saved hai — reply REFILL for home delivery.")
    else:
        parts.append("Reply REFILL to reorder, ya store visit karein.")
    return " ".join(parts), "open_ended"


# ── SEASONAL ─────────────────────────────────────────

def template_seasonal(category: dict, merchant: dict, trigger: dict, customer: Optional[dict] = None) -> tuple[str, str]:
    sal = _get_salutation(category, merchant)
    payload = trigger.get("payload", {})
    season = payload.get("season", "").replace("_", " ")
    trends = payload.get("trends", [])
    parts = [f"{sal}, {season} demand shifts are kicking in."]
    if trends:
        rising = [t.replace("_demand_+", " demand up ") for t in trends if "+"] [:2]
        if rising:
            parts.append(f"Trending up: {', '.join(rising)}.")
    if payload.get("shelf_action_recommended"):
        parts.append("Shelf adjustment recommended. Want a suggested stock list?")
    else:
        parts.append("Want to discuss stocking strategy?")
    return " ".join(parts), "open_ended"


# ── GBP UNVERIFIED ───────────────────────────────────

def template_gbp_unverified(category: dict, merchant: dict, trigger: dict, customer: Optional[dict] = None) -> tuple[str, str]:
    sal = _get_salutation(category, merchant)
    payload = trigger.get("payload", {})
    uplift = payload.get("estimated_uplift_pct", 0)
    parts = [f"{sal}, your Google Business Profile isn't verified yet."]
    if uplift:
        parts.append(f"Verified profiles typically get {_fmt_pct(uplift)} more visibility.")
    parts.append("It takes about 5 minutes via phone or postcard. Want me to walk you through it?")
    return " ".join(parts), "open_ended"


# ── CDE OPPORTUNITY ──────────────────────────────────

def template_cde(category: dict, merchant: dict, trigger: dict, customer: Optional[dict] = None) -> tuple[str, str]:
    sal = _get_salutation(category, merchant)
    payload = trigger.get("payload", {})
    item_id = payload.get("digest_item_id", "")
    credits = payload.get("credits", 0)
    fee = payload.get("fee", "")
    digest_items = category.get("digest", [])
    item = next((d for d in digest_items if d.get("id") == item_id), None)
    if not item:
        item = {}
    title = item.get("title", "upcoming CDE opportunity")
    date = item.get("date", "")
    parts = [f"{sal}, CDE opportunity: {title}."]
    if date:
        parts.append(f"Date: {date[:10]}.")
    if credits:
        parts.append(f"{credits} CDE credits.")
    if fee:
        parts.append(f"Fee: {fee.replace('_', ' ')}.")
    parts.append("Interested?")
    return " ".join(parts), "open_ended"


# ── COMPETITOR OPENED ────────────────────────────────

def template_competitor(category: dict, merchant: dict, trigger: dict, customer: Optional[dict] = None) -> tuple[str, str]:
    sal = _get_salutation(category, merchant)
    payload = trigger.get("payload", {})
    name = payload.get("competitor_name", "a new competitor")
    dist = payload.get("distance_km", 0)
    their_offer = payload.get("their_offer", "")
    offers = _get_active_offers(merchant)
    parts = [f"{sal}, new listing spotted — {name}, {dist}km from you."]
    if their_offer and offers:
        parts.append(f"They're running \"{their_offer}\". Your \"{offers[0]['title']}\" is competitive.")
    elif their_offer:
        parts.append(f"They're running \"{their_offer}\".")
    parts.append("Want to see how your listing compares?")
    return " ".join(parts), "open_ended"


# ── DORMANT WITH VERA ────────────────────────────────

def template_dormant(category: dict, merchant: dict, trigger: dict, customer: Optional[dict] = None) -> tuple[str, str]:
    sal = _get_salutation(category, merchant)
    payload = trigger.get("payload", {})
    days = payload.get("days_since_last_merchant_message", 0)
    perf = merchant.get("performance", {})
    views = perf.get("views", 0)
    parts = [f"{sal}, been a while — {days} days since we last chatted."]
    if views:
        parts.append(f"Your listing is still getting {views:,} views/month.")
    parts.append("Anything I can help with?")
    return " ".join(parts), "open_ended"


# ── CURIOUS ASK ──────────────────────────────────────

def template_curious_ask(category: dict, merchant: dict, trigger: dict, customer: Optional[dict] = None) -> tuple[str, str]:
    sal = _get_salutation(category, merchant)
    slug = category.get("slug", "")
    questions = {
        "dentists": "what treatment are patients asking about most this week?",
        "salons": "which service has been in highest demand this week?",
        "restaurants": "which dish has been your bestseller this week?",
        "gyms": "what's the most common fitness goal new members mention?",
        "pharmacies": "which OTC product has been moving fastest this week?",
    }
    question = questions.get(slug, "what's been keeping you busiest this week?")
    return f"{sal}, quick one — {question}", "open_ended"


# ── CUSTOMER LAPSED (customer-facing) ────────────────

def template_customer_lapsed(category: dict, merchant: dict, trigger: dict, customer: Optional[dict] = None) -> tuple[str, str]:
    merchant_name = _get_merchant_name(merchant)
    payload = trigger.get("payload", {})
    days = payload.get("days_since_last_visit", 0)
    prev_focus = payload.get("previous_focus", "").replace("_", " ")
    offers = _get_active_offers(merchant)
    cust_name = ""
    if customer:
        cust_name = customer.get("identity", {}).get("name", "")
    greeting = f"Hi {cust_name}" if cust_name else "Hi"
    parts = [f"{greeting}, {merchant_name} here."]
    parts.append(f"It's been {days} days since your last visit.")
    if prev_focus:
        parts.append(f"How's your {prev_focus} journey going?")
    if offers:
        parts.append(f"We have \"{offers[0]['title']}\" running if you'd like to restart.")
    parts.append("Reply YES to book a session.")
    return " ".join(parts), "open_ended"


# ── TRIAL FOLLOWUP (customer-facing) ─────────────────

def template_trial_followup(category: dict, merchant: dict, trigger: dict, customer: Optional[dict] = None) -> tuple[str, str]:
    merchant_name = _get_merchant_name(merchant)
    payload = trigger.get("payload", {})
    sessions = payload.get("next_session_options", [])
    cust_name = ""
    if customer:
        cust_name = customer.get("identity", {}).get("name", "")
    greeting = f"Hi {cust_name}" if cust_name else "Hi"
    parts = [f"{greeting}, {merchant_name} here."]
    parts.append("Hope you enjoyed the trial session!")
    if sessions:
        slot = sessions[0].get("label", "")
        if slot:
            parts.append(f"Next available: {slot}.")
    parts.append("Want to continue? Reply YES to book.")
    return " ".join(parts), "open_ended"


# ── WEDDING PACKAGE FOLLOWUP (customer-facing) ──────

def template_wedding_followup(category: dict, merchant: dict, trigger: dict, customer: Optional[dict] = None) -> tuple[str, str]:
    merchant_name = _get_merchant_name(merchant)
    payload = trigger.get("payload", {})
    days_to = payload.get("days_to_wedding", 0)
    next_step = payload.get("next_step_window_open", "").replace("_", " ")
    cust_name = ""
    if customer:
        cust_name = customer.get("identity", {}).get("name", "")
    greeting = f"Hi {cust_name}" if cust_name else "Hi"
    parts = [f"{greeting}, {merchant_name} here."]
    parts.append(f"Your wedding is {days_to} days away!")
    if next_step:
        parts.append(f"It's the right time to start your {next_step}.")
    parts.append("Want me to set up a schedule?")
    return " ".join(parts), "open_ended"


# ── SEASONAL PERF DIP ────────────────────────────────

def template_seasonal_perf_dip(category: dict, merchant: dict, trigger: dict, customer: Optional[dict] = None) -> tuple[str, str]:
    sal = _get_salutation(category, merchant)
    payload = trigger.get("payload", {})
    metric = payload.get("metric", "views")
    delta = payload.get("delta_pct", 0)
    note = payload.get("season_note", "").replace("_", " ")
    parts = [f"{sal}, your {metric} dipped {_fmt_pct(delta)} this week — but this is typical for {note}."]
    offers = _get_active_offers(merchant)
    if offers:
        parts.append(f"Your \"{offers[0]['title']}\" can help retain interest during the slow window.")
    parts.append("Want tips on navigating this season?")
    return " ".join(parts), "open_ended"


# ── FALLBACK ─────────────────────────────────────────

def template_fallback(category: dict, merchant: dict, trigger: dict, customer: Optional[dict] = None) -> tuple[str, str]:
    sal = _get_salutation(category, merchant)
    kind = trigger.get("kind", "update")
    perf = merchant.get("performance", {})
    views = perf.get("views", 0)
    parts = [f"{sal}, quick update on your listing."]
    if views:
        parts.append(f"You're getting {views:,} views this month.")
    parts.append("Anything I can help with?")
    return " ".join(parts), "open_ended"


# ── TEMPLATE REGISTRY ────────────────────────────────

TEMPLATE_MAP: dict[str, Any] = {
    "research_digest": template_research_digest,
    "regulation_change": template_regulation_change,
    "perf_dip": template_perf_dip,
    "perf_spike": template_perf_spike,
    "renewal_due": template_renewal_due,
    "festival_upcoming": template_festival,
    "recall_due": template_recall_due,
    "review_theme_emerged": template_review_theme,
    "milestone_reached": template_milestone,
    "ipl_match_today": template_ipl_match,
    "active_planning_intent": template_active_planning,
    "winback_eligible": template_winback,
    "supply_alert": template_supply_alert,
    "chronic_refill_due": template_chronic_refill,
    "category_seasonal": template_seasonal,
    "gbp_unverified": template_gbp_unverified,
    "cde_opportunity": template_cde,
    "competitor_opened": template_competitor,
    "dormant_with_vera": template_dormant,
    "curious_ask_due": template_curious_ask,
    "customer_lapsed_hard": template_customer_lapsed,
    "customer_lapsed_soft": template_customer_lapsed,
    "trial_followup": template_trial_followup,
    "wedding_package_followup": template_wedding_followup,
    "seasonal_perf_dip": template_seasonal_perf_dip,
}


def render_template(
    kind: str,
    category: dict,
    merchant: dict,
    trigger: dict,
    customer: Optional[dict] = None,
) -> tuple[str, str]:
    fn = TEMPLATE_MAP.get(kind, template_fallback)
    return fn(category, merchant, trigger, customer)
