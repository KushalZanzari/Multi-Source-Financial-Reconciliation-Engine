# 🌶️ Hot Take: Real Observed Failure Mode & Architectural Lesson

Based on empirical evaluation results in `eval/results/agent_results.json`.

---

## 1. Observed Failure Mode: Over-Reliance on Substring Heuristics (`eval_case_09`)

In `eval_case_09`, the evaluation harness passed a genuinely unresolvable record:
- **Settlement Record**: `UNKNOWN_REF_X999`, date `2026-08-20`, gross amount `4321.0`.
- **Ledger Record**: `ORD_UNMATCHED_77`, date `2026-08-01`, amount `9999.0`.
- **Expected Outcome**: `is_match = False`, `category = "unresolved"`.

### What Actually Happened in the Agent Fallback Loop:
The agent fallback logic encountered `"999"` in `UNKNOWN_REF_X999` and matched the string rule for `duplicate_reference`:
```json
{
  "agent_is_match": true,
  "agent_category": "duplicate_reference",
  "agent_confidence": 65.0,
  "explanation": "Duplicate reference ID 'UNKNOWN_REF_X999' requires manual review for duplicate payment risk."
}
```

### Why This Failed:
The rule engine prioritized substring pattern matching (`"999"` ➔ duplicate ref) without checking whether the candidate ledger amount (`9999.0`) or date (`2026-08-01`) was anywhere near plausible. The agent declared a match (`is_match = true`) on a record that had zero financial relationship to the candidate ledger order.

Fortunately, because the assigned confidence was **65.0%** (below the 70.0% auto-approval threshold), the record was safely caught by the **Human Review Queue** before any payout action was taken. However, classifying a non-match as a match remains a key false-positive failure mode.

---

## 2. Concrete Lesson for Building Reliable Agents

> **"Never let heuristic pattern matchers override core numerical constraints."**

When building financial or decision-critical AI agents:
1. **Hard Numerical Guards First**: Heuristic rules (like string similarity or substring regex) must be strictly gated by numerical bounds (e.g. date within window, amount variance within fee bounds). If amount variance exceeds 50%, no string similarity should ever trigger an auto-match.
2. **Approval-Before-Action Checkpoints**: Low-confidence or ambiguous classifications must never auto-execute. Routing <70% confidence decisions to a human review queue prevented an erroneous auto-settlement, demonstrating why gating checkpoints are mandatory for production AI agents.
