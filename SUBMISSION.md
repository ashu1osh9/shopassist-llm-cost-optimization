# ShopAssist — LLM cost optimization submission

## Scope and deliverables

- **Q1:** `question1/agent.py` — one LLM call per ticket, returns the original `TicketResolution` shape, including `customer_reply` and `raw_completion`.
- **Q2:** `question2/agent.py` — retains the `triage → retrieve → compose → audit` workflow and original `TicketResolution` output shape. Triage, retrieval and policy audit execute locally; compose normally makes one LLM call. A second call occurs only if the policy audit rejects a response.
- Tests: `tests/test_question1.py`, `tests/test_question2.py` and `tests/test_optimization.py`.
- Exact cost reporting: `scripts/cost_report.py` (reports one Q1 ticket and two Q2 tickets with separate physical and denial paths, plus every public ticket and T-1091).

## Cost optimizations

### Question 1

1. Removed a random run UUID, which changed the system prompt on every request.
2. Removed duplicated examples and instructions requesting lengthy analysis. The local simulator now returns concise JSON instead of a long trace.
3. Retained all five genuine KB policies, which are small in this track; removed verbose formatting and compacted the full order snapshot with JSON separators. The original ticket conversation and all order fields remain available to the model.
4. Used a stable, reusable system prompt; there is no fabricated cache discount. Prompts here are under the 1,024-token cache eligibility threshold.

**Expected effect:** far fewer input tokens and fewer output tokens, with the single-model-call requirement unchanged.

### Question 2

1. **Triage (local):** select applicable policy IDs from structured order facts without an LLM request.
2. **Retrieve (local):** load actual help-center Markdown files by ID, not the 200k-token expanded corpus. Include the general return article as a fall-through when appropriate.
3. **Compose (one LLM call):** use one concise prompt containing the original ticket thread, original order fields (only JSON whitespace changed) and selected real KB article text. Request concise JSON.
4. **Audit (local):** verify action enum, citation membership and order/policy eligibility before accepting. On an invalid model result, request one corrected model response; fail closed rather than approving an incorrect action after a second rejection.

**Expected effect:** eliminates unnecessary LLM calls and repeated context while keeping four logical stages. No changes to the simulator, prices, token counting, data files or evaluation reference code.

## Verification instructions

From project root, with Python and dependencies installed:

```bash
python -m pip install -r requirements.txt
pytest -q
python question1/run.py
python question2/run.py
python scripts/cost_report.py --output COST_REPORT.md
```

`COST_REPORT.md` created by the last command gives authoritative per-call input, cached-input and output tokens and points **according to this repository's exact `tiktoken` billing implementation**. The report script checks correctness and cost targets, failing with an exception if a public or holdout ticket is incorrect or over budget.

## Checks performed in preparation environment

- Static compilation completed.
- 42 tests passed, including all publicly provided examples, holdout subscription, policy boundary checks, single-call invariants, and invalid-response retry.
- **Testing limitation:** The packaging environment could not download `tiktoken` (network/DNS unavailable). Those tests were run using a *temporary external test-only token-counting shim*, not a modification of the repository. Decision correctness and control flow are verified against the local simulator; the numerical cost limits and exact token counts must be re-run using installed `tiktoken` by the command above. The shim is not included in this ZIP.

## Caveats

This repository uses a local `LlmClient` simulator, not a hosted model. Public/holdout correctness here does not prove hosted-model behavior or generalization to other company policies. A real production implementation would require live-model evaluation, adversarial testing, and possibly stronger independent policy validation. The optimized code does **not** import `eval.reference` directly; that reference is used only by existing simulator and tests.
