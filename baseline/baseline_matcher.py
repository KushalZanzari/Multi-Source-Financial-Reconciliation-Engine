"""Naive Baseline Matcher for Financial Reconciliation.

Strict, rule-based baseline that only matches records with EXACT amount and
EXACT reference_id / order_id match. No amount tolerance, no LLM reasoning,
no domain tools, no many-to-one combinatorial search, and no human review queue.
"""

from dataclasses import dataclass, field
from typing import Any
import pandas as pd


@dataclass
class BaselineMatch:
    """Represents an exact match produced by the baseline matcher."""
    settlement_id: str
    order_id: str
    bank_txn_id: str
    amount: float
    match_type: str = "exact_baseline"
    explanation: str = "Exact reference ID and exact gross amount match."


class BaselineMatcher:
    """Baseline matcher executing strict exact-string and exact-float matching only."""

    def run_baseline_pass(
        self,
        bank_df: pd.DataFrame,
        settlement_df: pd.DataFrame,
        ledger_df: pd.DataFrame,
    ) -> tuple[list[BaselineMatch], list[dict[str, Any]], float]:
        """Executes exact baseline reconciliation pass.

        Args:
            bank_df (pd.DataFrame): Bank statement records.
            settlement_df (pd.DataFrame): Gateway settlement report records.
            ledger_df (pd.DataFrame): Internal ledger records.

        Returns:
            tuple[list[BaselineMatch], list[dict[str, Any]], float]:
                - List of exact baseline matches
                - List of unmatched settlement records
                - Elapsed execution time in seconds
        """
        import time
        start_time = time.time()

        matches: list[BaselineMatch] = []
        unmatched_settlements: list[dict[str, Any]] = []

        # Index ledger by order_id for fast lookup
        ledger_by_id = {}
        for _, row in ledger_df.iterrows():
            oid = str(row.get("order_id", "")).strip()
            if oid:
                ledger_by_id[oid] = row.to_dict()

        # Index bank statement by reference_id
        bank_by_ref = {}
        for _, row in bank_df.iterrows():
            ref = str(row.get("reference_id", "")).strip()
            if ref:
                bank_by_ref[ref] = row.to_dict()

        for _, stl_row in settlement_df.iterrows():
            stl_id = str(stl_row.get("settlement_id", "")).strip()
            ref_id = str(stl_row.get("reference_id", "")).strip()
            ord_id = str(stl_row.get("order_id", "")).strip()
            gross_amt = float(stl_row.get("gross_amount", 0.0))

            matched = False

            # Strict exact match requirement:
            # 1. reference_id or order_id must match internal ledger order_id exactly
            # 2. gross_amount must equal ledger amount exactly (no tolerance, no fee adjustment deduction)
            # 3. reference_id must match bank statement reference_id exactly

            target_id = ref_id or ord_id
            ledger_match = ledger_by_id.get(target_id) or ledger_by_id.get(ord_id)
            bank_match = bank_by_ref.get(ref_id)

            if ledger_match and bank_match:
                leg_amt = float(ledger_match.get("amount", 0.0))
                # Strict exact amount equality check (no fee schedule deduction, no tolerance)
                if gross_amt == leg_amt:
                    matches.append(
                        BaselineMatch(
                            settlement_id=stl_id,
                            order_id=target_id,
                            bank_txn_id=str(bank_match.get("txn_id", "")),
                            amount=gross_amt,
                        )
                    )
                    matched = True

            if not matched:
                unmatched_settlements.append(stl_row.to_dict())

        elapsed = time.time() - start_time
        return matches, unmatched_settlements, elapsed
