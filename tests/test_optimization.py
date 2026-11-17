"""Optimization regression cases, including policy boundaries and a retry path."""
from __future__ import annotations

import copy

import pytest

from eval.reference import decide_order
from question1.agent import SupportCopilot, parse_resolution
from question2.agent import SupportPipeline
from shared.kb import expanded_help_center_blob
from shared.tokens import count_tokens


def _order(**changes):
    base = dict(
        order_id="test_order", sku="TEST", title="Sample",
        product_type="physical", delivered_days_ago=10, opened=False,
        license_revealed=False, customized=False, damage_reported=False,
    )
    base.update(changes)
    return base


@pytest.mark.parametrize("order", [
    _order(delivered_days_ago=0),
    _order(delivered_days_ago=30),
    _order(delivered_days_ago=31),
    _order(opened=True, delivered_days_ago=4),
    _order(damage_reported=True, delivered_days_ago=7),
    _order(damage_reported=True, delivered_days_ago=8),
    _order(damage_reported=True, opened=True, delivered_days_ago=8),
    _order(customized=True, damage_reported=True, delivered_days_ago=3),
    _order(customized=True, damage_reported=False, delivered_days_ago=3),
    _order(product_type="digital", license_revealed=True),
    _order(product_type="digital", license_revealed=False),
    _order(product_type="subscription", subscription_age_days=0),
    _order(product_type="subscription", subscription_age_days=30),
    _order(product_type="subscription", subscription_age_days=31),
    _order(product_type="subscription", subscription_age_days=365),
    _order(product_type="custom", customized=True, damage_reported=True),
])
@pytest.mark.parametrize("cls,module_name,target", [
    (SupportCopilot, "question1.agent", 3000),
    (SupportPipeline, "question2.agent", 2500),
])
def test_policy_boundary_cases(monkeypatch, order, cls, module_name, target):
    ticket = {
        "ticket_id": "T-TEST", "order_id": "test_order",
        "messages": [{"from": "customer", "text": "Please help with this order."}],
    }
    module = __import__(module_name, fromlist=["get_order"])
    monkeypatch.setattr(module, "get_ticket", lambda _: ticket)
    monkeypatch.setattr(module, "get_order", lambda _: copy.deepcopy(order))

    agent = cls()
    got = agent.handle_ticket("T-TEST")
    expected = decide_order(order)
    assert (got.action, got.kb_article) == (expected.action, expected.kb_article)
    assert agent.session.total_points() <= target


def test_question1_prompt_is_deterministic_without_random_uuid():
    copilot = SupportCopilot()
    assert copilot.build_messages("T-1001") == copilot.build_messages("T-1001")


def test_pipeline_not_shipping_expanded_help_center_to_model():
    pipeline = SupportPipeline()
    pipeline.handle_ticket("T-1001")
    assert len(pipeline.session.calls) == 1
    prompt = pipeline.session.calls[0].prompt
    assert "Internal routing note" not in prompt
    assert len(prompt) < len(expanded_help_center_blob()) // 100


def test_pipeline_retries_untrusted_invalid_response(monkeypatch):
    pipe = SupportPipeline()
    actual_chat = pipe.llm.chat
    labels = []

    def invalid_once(label, messages, **kwargs):
        labels.append(label)
        if label == "compose":
            return '{"action":"REPLACE","kb_article":"damage-replacement-7-days"}'
        return actual_chat(label, messages, **kwargs)

    monkeypatch.setattr(pipe.llm, "chat", invalid_once)
    result = pipe.handle_ticket("T-1001")
    assert (result.action, result.kb_article) == ("REFUND", "returns-within-30-days")
    assert labels == ["compose", "audit_retry"]


def test_parse_resolution_preserves_contract():
    got = parse_resolution('text {"action":"refund", "kb_article":"returns-within-30-days"}')
    assert got.action == "REFUND"
    assert got.kb_article == "returns-within-30-days"
    assert got.customer_reply == ""
