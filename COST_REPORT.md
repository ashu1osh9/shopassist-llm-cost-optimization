# Exact token / billing report

Generated using the repository's `shared.tokens.count_tokens` (`tiktoken`, `cl100k_base`) and `CostSession`.

Billing: `uncached_input × 3 + cached_input × 0.3 + output × 15`. No prompt prefix is 1,024 tokens, so cached input is zero.

| Track / ticket | LLM call | Input | Cached | Output | Points | Limit | Result |
|---|---|---:|---:|---:|---:|---:|---|
| Q1 / T-1001 | `handle_ticket` | 373 | 0 | 46 | 1809 | 3000 | PASS |
| Q2 (physical) / T-1004 | `compose` | 232 | 0 | 36 | 1236 | 2500 | PASS |
| Q2 (denial) / T-1002 | `compose` | 242 | 0 | 39 | 1311 | 2500 | PASS |

## All public tickets and holdout

| Track | Ticket | Action | Article | Total points | Budget |
|---|---|---|---|---:|---:|
| Q1 | T-1001 | REFUND | `returns-within-30-days` | 1809 | 3000 |
| Q1 | T-1002 | SEND_ARTICLE | `digital-license-no-refund` | 1680 | 3000 |
| Q1 | T-1003 | ESCALATE_TIER2 | `custom-items-no-replace` | 1641 | 3000 |
| Q1 | T-1004 | REPLACE | `damage-replacement-7-days` | 1602 | 3000 |
| Q1 | T-1091 | SEND_ARTICLE | `subscription-cooling-off` | 1644 | 3000 |
| Q2 (physical) | T-1001 | REFUND | `returns-within-30-days` | 1335 | 2500 |
| Q2 (physical) | T-1002 | SEND_ARTICLE | `digital-license-no-refund` | 1311 | 2500 |
| Q2 (physical) | T-1003 | ESCALATE_TIER2 | `custom-items-no-replace` | 1272 | 2500 |
| Q2 (physical) | T-1004 | REPLACE | `damage-replacement-7-days` | 1236 | 2500 |
| Q2 (physical) | T-1091 | SEND_ARTICLE | `subscription-cooling-off` | 1164 | 2500 |
