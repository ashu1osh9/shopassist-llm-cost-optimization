"""Produce exact simulator token/point accounting using shared/tokens.py (tiktoken)."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from question1.agent import SupportCopilot
from question2.agent import SupportPipeline
from eval.reference import TICKET_EXPECTATIONS


CASES = (
    ("Q1", SupportCopilot, "T-1001", 3000),
    ("Q2 (physical)", SupportPipeline, "T-1004", 2500),
    ("Q2 (denial)", SupportPipeline, "T-1002", 2500),
)
PUBLIC = ("T-1001", "T-1002", "T-1003", "T-1004")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", help="Save exact Markdown report to this path")
    args = parser.parse_args()
    rows = [
        "# Exact token / billing report",
        "",
        "Generated using the repository's `shared.tokens.count_tokens` "
        "(`tiktoken`, `cl100k_base`) and `CostSession`.",
        "",
        "Billing: `uncached_input × 3 + cached_input × 0.3 + output × 15`. "
        "No prompt prefix is 1,024 tokens, so cached input is zero.",
        "",
        "| Track / ticket | LLM call | Input | Cached | Output | Points | Limit | Result |",
        "|---|---|---:|---:|---:|---:|---:|---|",
    ]
    for track, cls, ticket_id, target in CASES:
        agent = cls()
        resolution = agent.handle_ticket(ticket_id)
        expected = TICKET_EXPECTATIONS[ticket_id]
        if (resolution.action, resolution.kb_article) != (
            expected.action, expected.kb_article
        ):
            raise RuntimeError(f"Incorrect action or citation: {track} {ticket_id}")
        for call in agent.session.calls:
            points = call.points()
            rows.append(
                f"| {track} / {ticket_id} | `{call.label}` | {call.input_tokens} "
                f"| {call.cached_prefix_tokens} | {call.output_tokens} "
                f"| {points} | {target} | {'PASS' if points <= target else 'FAIL'} |"
            )
        if agent.session.total_points() > target:
            raise RuntimeError(f"Over budget: {track} {ticket_id}")
    rows += ["", "## All public tickets and holdout", "", "| Track | Ticket | Action | Article | Total points | Budget |", "|---|---|---|---|---:|---:|"]
    for track, cls, _, limit in (CASES[0], CASES[1]):
        for ticket_id in (*PUBLIC, "T-1091"):
            agent = cls()
            got = agent.handle_ticket(ticket_id)
            exp = TICKET_EXPECTATIONS[ticket_id]
            if (got.action, got.kb_article) != (exp.action, exp.kb_article):
                raise RuntimeError(f"Incorrect ticket: {track} {ticket_id}")
            points = agent.session.total_points()
            if points > limit:
                raise RuntimeError(f"Over budget: {track} {ticket_id}: {points}")
            rows.append(f"| {track} | {ticket_id} | {got.action} | `{got.kb_article}` | {points} | {limit} |")
    report = "\n".join(rows) + "\n"
    print(report)
    if args.output:
        path = Path(args.output)
        path.write_text(report, encoding="utf-8")
        print(f"Saved {path}")


if __name__ == "__main__":
    main()
