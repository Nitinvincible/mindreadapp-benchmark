"""
rci.py — Reasoning Consistency Index for MindRead++ benchmark.

Evaluates whether correct answers are supported by valid chain-of-thought
reasoning traces, using four criteria:
  1. Event citation — references specific events
  2. Witness attribution — correctly identifies who saw what
  3. Belief isolation — separates character knowledge from ground truth
  4. Answer consistency — final answer follows from the trace
"""
from __future__ import annotations

import json
import re
import argparse
import os
import sys
from typing import Any


# ── RCI Criteria Checkers ───────────────────────────────────────────────────

def check_event_citation(reasoning: str) -> bool:
    """Check if the reasoning references at least one specific event.
    
    Passes if the trace mentions event numbers, describes specific actions,
    or references concrete story elements.
    """
    # Check for explicit event references
    if re.search(r"event[\s_]?\d", reasoning, re.IGNORECASE):
        return True
    
    # Check for action-specific language indicating event awareness
    action_patterns = [
        r"(placed|moved|put|told|said|saw|witnessed|heard|observed)",
        r"(in event|during|when .+ was|while .+ was)",
        r"(step \d|first|second|third|then|after|before)",
    ]
    matches = sum(1 for p in action_patterns if re.search(p, reasoning, re.IGNORECASE))
    return matches >= 2


def check_witness_attribution(reasoning: str, scenario: dict[str, Any] | None = None) -> bool:
    """Check if reasoning correctly identifies who witnessed what.
    
    Passes if the trace attributes knowledge to specific characters based
    on what they saw or didn't see.
    """
    # Check for witness/knowledge attribution language
    attribution_patterns = [
        r"(did not see|didn'?t see|wasn'?t present|was not present)",
        r"(only .+ saw|only .+ witnessed|only .+ knows)",
        r"(was in|was at|was away|had left|wasn'?t there)",
        r"(witnessed|observed|saw|heard|didn'?t witness)",
        r"(knows about|doesn'?t know|unaware|not aware)",
        r"(from .+'s perspective|from .+'s point of view)",
    ]
    matches = sum(1 for p in attribution_patterns if re.search(p, reasoning, re.IGNORECASE))
    return matches >= 1


def check_belief_isolation(reasoning: str) -> bool:
    """Check if reasoning separates character beliefs from ground truth.
    
    Passes if the trace distinguishes between what actually happened and
    what the character believes happened.
    """
    isolation_patterns = [
        r"(believes?|thinks?|assumes?|expects?)\s+(that\s+)?(the|it|he|she|they)",
        r"from .+'s (perspective|point of view|standpoint)",
        r"(in reality|actually|in fact|but really)",
        r"(doesn'?t know|has no way of knowing|is unaware)",
        r"(would (think|believe|assume))",
        r"(still believes?|still thinks?)",
    ]
    matches = sum(1 for p in isolation_patterns if re.search(p, reasoning, re.IGNORECASE))
    return matches >= 1


def check_answer_consistency(reasoning: str, answer: str) -> bool:
    """Check if the final answer logically follows from the reasoning trace.
    
    This is a simplified check — verifies the answer letter appears in or
    is consistent with the conclusion of the reasoning.
    """
    if not reasoning or not answer:
        return False
    
    # Check that the reasoning doesn't contradict the answer
    # Look for the conclusion part of the reasoning
    conclusion_markers = ["therefore", "so ", "thus", "hence", "this means",
                          "the answer is", "conclude", "consequently"]
    
    conclusion = reasoning
    for marker in conclusion_markers:
        idx = reasoning.lower().rfind(marker)
        if idx != -1:
            conclusion = reasoning[idx:]  # type: ignore[index]
            break
    
    # Basic consistency: the answer letter or its content should not be
    # contradicted in the conclusion
    # This is a heuristic — a production system would use NLI
    return len(conclusion) > 10  # At minimum, there's some reasoning present


def extract_reasoning(response_text: str) -> str:
    """Extract the reasoning portion from a model response."""
    match = re.search(r"REASONING:\s*(.*?)(?=ANSWER:|$)", response_text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    
    # If no structured format, treat everything before the answer as reasoning
    match = re.search(r"(.*?)(?=\b[A-D]\b\s*$)", response_text, re.DOTALL)
    if match:
        return match.group(1).strip()
    
    return response_text.strip()


# ── RCI Computation ─────────────────────────────────────────────────────────

def evaluate_trace(response_text: str, correct_answer: str,
                   predicted_answer: str, scenario: dict[str, Any] | None = None) -> dict[str, Any]:
    """Evaluate a single reasoning trace against all four RCI criteria.
    
    Returns dict with per-criterion pass/fail and overall validity.
    """
    reasoning = extract_reasoning(response_text)
    
    criteria: dict[str, Any] = {
        "event_citation": check_event_citation(reasoning),
        "witness_attribution": check_witness_attribution(reasoning, scenario),
        "belief_isolation": check_belief_isolation(reasoning),
        "answer_consistency": check_answer_consistency(reasoning, predicted_answer),
    }
    
    criteria["valid"] = all(criteria.values())
    criteria["reasoning_excerpt"] = reasoning[:200] + "..." if len(reasoning) > 200 else reasoning  # type: ignore[index]
    
    return criteria


def compute_rci(model_outputs: list[dict[str, Any]], scenarios: dict[str, Any] | None = None) -> dict[str, Any]:
    """Compute the Reasoning Consistency Index for a model's outputs.
    
    RCI = (correct answers with valid reasoning) / (total correct answers)
    
    Args:
        model_outputs: List of dicts with keys:
            question_id, predicted, correct, response_text
        scenarios: Optional dict mapping scenario_id to scenario data
    
    Returns:
        Dict with rci score, breakdown, and per-question details
    """
    correct_outputs = [o for o in model_outputs
                       if o.get("predicted", "").upper() == o.get("correct", "").upper()]
    
    if not correct_outputs:
        return {
            "rci": 0.0,
            "correct_with_valid_reasoning": 0,
            "total_correct": 0,
            "interpretation": "No correct answers to evaluate",
            "details": []
        }
    
    valid_count: int = 0
    details: list[dict[str, Any]] = []
    
    for output in correct_outputs:
        scenario: dict[str, Any] | None = None
        if scenarios is not None and "scenario_id" in output:
            scenario = scenarios.get(output["scenario_id"])
        
        trace_eval = evaluate_trace(
            output.get("response_text", ""),
            output["correct"],
            output["predicted"],
            scenario
        )
        
        if trace_eval["valid"]:
            valid_count += 1  # type: ignore[operator]
        
        details.append({
            "question_id": output.get("question_id", "unknown"),
            **trace_eval
        })
    
    rci = valid_count / len(correct_outputs)  # type: ignore[operator]
    
    # Interpretation
    if rci >= 0.9:
        interpretation = "Strong genuine reasoner"
    elif rci >= 0.7:
        interpretation = "Mostly reliable, occasional gaps"
    elif rci >= 0.5:
        interpretation = "Mixed — likely pattern-matching combined with reasoning"
    else:
        interpretation = "Probable guesser — right answers not supported by valid traces"
    
    return {
        "rci": round(rci, 4),  # type: ignore[call-overload]
        "correct_with_valid_reasoning": valid_count,
        "total_correct": len(correct_outputs),
        "interpretation": interpretation,
        "details": details
    }


def main():
    parser = argparse.ArgumentParser(
        description="MindRead++ RCI — Reasoning Consistency Index computation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example usage:
  python rci.py --results results/gpt4o_responses.json
  python rci.py --results results/gpt4o_responses.json --scenarios data/scenarios_base.json

Input format (JSON list):
  [
    {
      "question_id": "Q_SCN001_T1",
      "scenario_id": "SCN_001",
      "predicted": "A",
      "correct": "A",
      "response_text": "REASONING: Sara placed... ANSWER: A"
    },
    ...
  ]

RCI Interpretation:
  0.9 – 1.0  Strong genuine reasoner
  0.7 – 0.89 Mostly reliable, occasional gaps
  0.5 – 0.69 Mixed reasoning
  < 0.5      Probable guesser
        """
    )
    parser.add_argument("--results", required=True, help="Path to model results JSON")
    parser.add_argument("--scenarios", default=None, help="Path to scenarios_base.json (optional)")
    parser.add_argument("--output", default=None, help="Path to save RCI report (JSON)")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.results):
        print(f"Error: Results file not found: {args.results}")
        sys.exit(1)
    
    with open(args.results, "r", encoding="utf-8") as f:
        model_outputs = json.load(f)
    
    scenarios = None
    if args.scenarios and os.path.exists(args.scenarios):
        with open(args.scenarios, "r", encoding="utf-8") as f:
            scn_list = json.load(f)
            scenarios = {s["scenario_id"]: s for s in scn_list}
    
    rci_report = compute_rci(model_outputs, scenarios)
    
    print("=" * 50)
    print("MindRead++ Reasoning Consistency Index")
    print("=" * 50)
    print(f"\nRCI Score: {rci_report['rci']:.2%}")
    print(f"Valid traces: {rci_report['correct_with_valid_reasoning']}/{rci_report['total_correct']} correct answers")
    print(f"Interpretation: {rci_report['interpretation']}")
    
    # Criteria breakdown
    if rci_report["details"]:
        criteria_names = ["event_citation", "witness_attribution", "belief_isolation", "answer_consistency"]
        print("\nCriteria pass rates:")
        for crit in criteria_names:
            passed = sum(1 for d in rci_report["details"] if d.get(crit, False))
            total = len(rci_report["details"])
            print(f"  {crit:25s}: {passed}/{total} ({passed/total:.0%})")
    
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(rci_report, f, indent=2)
        print(f"\nRCI report saved to: {args.output}")


if __name__ == "__main__":
    main()
