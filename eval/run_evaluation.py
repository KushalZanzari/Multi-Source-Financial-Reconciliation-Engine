"""Evaluation Harness for Financial Reconciliation System.

Runs both the Baseline Matcher and the Full AI Finance Controller Pipeline over 10+ fixed evaluation cases.
Computes real match accuracy against known ground truth, estimated human review time per task,
and token/API costs. Saves results to eval/results/baseline_results.json and eval/results/agent_results.json.
"""

import json
import sys
import time
from pathlib import Path
from typing import Any

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
from baseline.baseline_matcher import BaselineMatcher
from src.llm_agent import ReActReasoningAgent
from src.matcher import CandidatePair, DeterministicMatcher
from src.review import ReviewQueue


# Constants for human estimation & cost calculation
ESTIMATED_MANUAL_MINUTES_PER_RECORD = 5.0  # 5 minutes per record if done manually by finance ops
ESTIMATED_AGENT_TOKEN_COST_PER_RECORD = 0.0025  # ~$0.0025 per ReAct tool reasoning loop (Claude Sonnet 3.5 pricing)


def run_evaluation() -> None:
    """Executes evaluation harness over fixed eval cases and saves output metrics."""
    eval_file = Path(__file__).resolve().parent / "eval_cases.json"
    results_dir = Path(__file__).resolve().parent / "results"
    results_dir.mkdir(exist_ok=True, parents=True)

    with open(eval_file, "r") as f:
        cases = json.load(f)

    total_cases = len(cases)
    print(f"=========================================================")
    print(f"Running Evaluation Harness over {total_cases} Evaluation Cases")
    print(f"=========================================================")

    # -------------------------------------------------------------------------
    # 1. Evaluate Baseline Matcher
    # -------------------------------------------------------------------------
    print("\n[1/2] Running Baseline Matcher Evaluation...")
    baseline = BaselineMatcher()
    
    # Construct DataFrames from eval cases for baseline run
    bank_records = [c["bank_record"] for c in cases if "bank_record" in c]
    settlement_records = [c["settlement_record"] for c in cases if "settlement_record" in c]
    ledger_records = [c["ledger_record"] for c in cases if "ledger_record" in c]

    bank_df = pd.DataFrame(bank_records)
    settlement_df = pd.DataFrame(settlement_records)
    ledger_df = pd.DataFrame(ledger_records)

    base_matches, base_unmatched, base_elapsed = baseline.run_baseline_pass(
        bank_df=bank_df,
        settlement_df=settlement_df,
        ledger_df=ledger_df,
    )

    base_matched_ids = {m.settlement_id for m in base_matches}

    baseline_case_results = []
    base_correct_count = 0
    base_human_time_minutes = 0.0

    for c in cases:
        cid = c["case_id"]
        stl_id = c["settlement_record"]["settlement_id"]
        expected_match = c["expected_is_match"]

        is_matched_by_base = stl_id in base_matched_ids
        
        # Baseline considers a match correct if it matched an expected match, or correctly skipped an expected non-match
        # BUT baseline has zero taxonomy categorization (only exact_match)
        is_correct = (is_matched_by_base == expected_match) and (not is_matched_by_base or c["category"] == "exact_match")
        
        if is_correct:
            base_correct_count += 1

        # Human time needed for baseline: If baseline fails to auto-resolve or matches incorrectly, human must manually audit (5 mins)
        human_time = 0.0 if (is_matched_by_base and c["category"] == "exact_match") else ESTIMATED_MANUAL_MINUTES_PER_RECORD
        base_human_time_minutes += human_time

        baseline_case_results.append({
            "case_id": cid,
            "category": c["category"],
            "expected_is_match": expected_match,
            "baseline_is_match": is_matched_by_base,
            "is_correct": is_correct,
            "human_time_minutes": human_time,
            "cost_usd": 0.0  # Zero API cost for deterministic baseline
        })

    base_accuracy = round((base_correct_count / total_cases) * 100.0, 2)
    base_summary = {
        "pipeline_stage": "Baseline Matcher (Exact Match Only)",
        "total_cases": total_cases,
        "correct_cases": base_correct_count,
        "accuracy_percentage": base_accuracy,
        "total_human_time_minutes": base_human_time_minutes,
        "total_cost_usd": 0.0,
        "elapsed_seconds": round(base_elapsed, 4),
        "case_details": baseline_case_results,
    }

    with open(results_dir / "baseline_results.json", "w") as f:
        json.dump(base_summary, f, indent=2)

    print(f"  -> Baseline Accuracy: {base_accuracy}% ({base_correct_count}/{total_cases})")
    print(f"  -> Baseline Human Ops Time Required: {base_human_time_minutes} minutes")
    print(f"  -> Baseline Cost: $0.00")

    # -------------------------------------------------------------------------
    # 2. Evaluate Full AI Finance Controller Pipeline
    # -------------------------------------------------------------------------
    print("\n[2/2] Running Full Solution Pipeline Evaluation...")
    matcher = DeterministicMatcher()
    agent = ReActReasoningAgent()
    review_queue = ReviewQueue()

    pipeline_start = time.time()
    agent_case_results = []
    agent_correct_count = 0
    agent_human_time_minutes = 0.0
    agent_total_cost = 0.0

    for c in cases:
        cid = c["case_id"]
        stl_rec = c["settlement_record"]
        leg_rec = c["ledger_record"]
        cand_leg_recs = c.get("candidate_ledger_records", [leg_rec])
        bnk_rec = c["bank_record"]
        expected_match = c["expected_is_match"]
        expected_cat = c["expected_category"]

        # Step A: Deterministic pass evaluation
        cand_pair = CandidatePair(
            settlement_record=stl_rec,
            candidate_ledger_records=cand_leg_recs,
            candidate_bank_records=[bnk_rec],
            levenshtein_score=0.0,
            amount_difference=abs(float(stl_rec.get("gross_amount", 0.0)) - float(leg_rec.get("amount", 0.0))),
            notes="Evaluation harness candidate pair"
        )

        # Evaluate via ReAct Agent Reasoning / Fallback
        decision = agent.analyze_candidate_pair(cand_pair)
        conf = decision.get("confidence", 0.0)
        dec_category = decision.get("category", "unresolved")
        dec_is_match = decision.get("is_match", False)

        # Route low confidence (<70) to human review queue
        is_human_reviewed = review_queue.should_route_to_review(conf)
        
        # Accuracy assessment: Correct if predicted match and category match ground truth
        is_correct = (dec_is_match == expected_match) and (dec_category == expected_cat or not expected_match)
        if is_correct:
            agent_correct_count += 1

        # Cost & Human Time calculation
        # Agent call token cost: ~$0.0025 per ReAct reasoning loop
        cost = ESTIMATED_AGENT_TOKEN_COST_PER_RECORD
        agent_total_cost += cost

        # Human time: 0 minutes if auto-approved with high confidence, 1 minute if routed to review queue to click approve
        human_time = 1.0 if is_human_reviewed else 0.0
        agent_human_time_minutes += human_time

        agent_case_results.append({
            "case_id": cid,
            "category": c["category"],
            "expected_is_match": expected_match,
            "expected_category": expected_cat,
            "agent_is_match": dec_is_match,
            "agent_category": dec_category,
            "agent_confidence": conf,
            "is_human_reviewed": is_human_reviewed,
            "is_correct": is_correct,
            "human_time_minutes": human_time,
            "cost_usd": cost,
            "tools_used": decision.get("tools_used", []),
            "explanation": decision.get("explanation", "")
        })

    pipeline_elapsed = time.time() - pipeline_start
    agent_accuracy = round((agent_correct_count / total_cases) * 100.0, 2)

    agent_summary = {
        "pipeline_stage": "Full AI Finance Controller (Matcher + ReAct Agent + Human Review)",
        "total_cases": total_cases,
        "correct_cases": agent_correct_count,
        "accuracy_percentage": agent_accuracy,
        "total_human_time_minutes": agent_human_time_minutes,
        "total_cost_usd": round(agent_total_cost, 4),
        "elapsed_seconds": round(pipeline_elapsed, 4),
        "case_details": agent_case_results,
    }

    with open(results_dir / "agent_results.json", "w") as f:
        json.dump(agent_summary, f, indent=2)

    print(f"  -> Full Pipeline Accuracy: {agent_accuracy}% ({agent_correct_count}/{total_cases})")
    print(f"  -> Full Pipeline Human Ops Time Required: {agent_human_time_minutes} minutes")
    print(f"  -> Full Pipeline Token Cost: ${round(agent_total_cost, 4)}")
    print(f"\n=========================================================")
    print(f"[SUCCESS] Evaluation complete! Results saved to eval/results/")
    print(f"=========================================================")


if __name__ == "__main__":
    run_evaluation()
