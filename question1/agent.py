"""Question 1: one compact, policy-grounded LLM call per ticket."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass

from shared.billing import CostSession
from shared.kb import all_articles_blob
from shared.llm import ChatMessage, LlmClient
from shared.tools import format_thread, get_order, get_ticket


@dataclass
class TicketResolution:
    action: str
    kb_article: str
    customer_reply: str
    raw_completion: str


def parse_resolution(text: str) -> TicketResolution:
    """Keep the original output contract, including surrounding-text tolerance."""
    m = re.search(r"\{[\s\S]*\}", text)
    if not m:
        raise ValueError(f"No JSON in model output:\n{text[:400]}")
    data = json.loads(m.group())
    return TicketResolution(
        action=str(data["action"]).upper(),
        kb_article=str(data["kb_article"]),
        customer_reply=str(data.get("customer_reply", "")),
        raw_completion=text,
    )


# Small enough to include every real policy: no lossy policy selection needed.
# Fixed instruction + help-center text first is stable across customer tickets.
_SYSTEM = (
    "You are ShopAssist. Use the order facts and customer thread with the "
    "following policies. Select REFUND, REPLACE, SEND_ARTICLE, or "
    "ESCALATE_TIER2. Cite the applicable article ID. "
    "Return only JSON with action, kb_article, customer_reply.\n"
    "POLICIES:\n" + all_articles_blob()
)


class SupportCopilot:
    """Single-call Tier-1 assistant with compact input and concise JSON output."""

    def __init__(self, session: CostSession | None = None):
        self.session = session if session is not None else CostSession()
        self.llm = LlmClient(self.session)

    def build_messages(self, ticket_id: str) -> list[ChatMessage]:
        ticket = get_ticket(ticket_id)
        order = get_order(ticket["order_id"])
        # Retain all original order fields; compact whitespace only.
        snapshot = json.dumps(order, separators=(",", ":"))
        user = (
            f"TICKET {ticket_id}\n{format_thread(ticket)}\n"
            f"ORDER_SNAPSHOT:{snapshot}END_SNAPSHOT"
        )
        return [ChatMessage("system", _SYSTEM), ChatMessage("user", user)]

    def handle_ticket(self, ticket_id: str) -> TicketResolution:
        # Exactly one model call, preserving the original public API.
        return parse_resolution(self.llm.chat("handle_ticket", self.build_messages(ticket_id)))
