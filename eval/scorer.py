"""
scorer.py — Accuracy scoring for MindRead++ benchmark.

Scores model responses against ground truth answers per tier (T1, T2, T3)
and computes overall accuracy metrics.
"""

import json
import re
import argparse
import sys
import os


def extract_answer(response_text: str | None) -> str | None:
    """Extract the final answer letter from a model response.
    
    Expected format:
        REASONING: ...
        ANSWER: A
    
    Returns uppercase letter (A-D) or None if not found.
    """
    if not response_text:
        return None

    # Try structured format first
    match = re.search(r"ANSWER:\s*([A-Da-d])", response_text)
    if match:
        return match.group(1).upper()
    
    # Fallback: last single letter on its own line
    match = re.search(r"^([A-Da-d])\s*$", response_text.strip(), re.MULTILINE)
    if match:
        return match.group(1).upper()
    
    # Fallback: last mention of A), B), C), or D)
    matches = re.findall(r"([A-Da-d])\)", response_text)
    if matches:
        return matches[-1].upper()
    
    return None


def score_response(predicted: str | None, correct: str) -> bool:
    """Check if a predicted answer matches the correct answer."""
    if predicted is None:
        return False
    return predicted.strip().upper() == correct.strip().upper()


def score_tier(results: list[dict], tier: int) -> dict:
    """Score accuracy for a specific tier.
    
    Args:
        results: List of dicts with keys: question_id, tier, predicted, correct
        tier: Tier number (1, 2, or 3)
    
    Returns:
        Dict with accuracy, correct_count, total_count
    """
    tier_results = [r for r in results if r["tier"] == tier]
    if not tier_results:
        return {"accuracy": 0.0, "correct": 0, "total": 0}
    
    correct = sum(1 for r in tier_results if score_response(r.get("predicted"), r["correct"]))
    total = len(tier_results)
    
    return {
        "accuracy": correct / total if total > 0 else 0.0,
        "correct": correct,
        "total": total
    }


def score_model(results: list[dict]) -> dict:
    """Score a model across all tiers and compute summary stats.
    
    Args:
        results: List of dicts with keys: question_id, tier, predicted, correct
    
    Returns:
        Dict with per-tier scores, overall accuracy, and tier breakdown
    """
    t1 = score_tier(results, 1)
    t2 = score_tier(results, 2)
    t3 = score_tier(results, 3)
    
    total_correct = t1["correct"] + t2["correct"] + t3["correct"]
    total_questions = t1["total"] + t2["total"] + t3["total"]
    
    return {
        "tier_1": t1,
        "tier_2": t2,
        "tier_3": t3,
        "overall": {
            "accuracy": total_correct / total_questions if total_questions > 0 else 0.0,
            "correct": total_correct,
            "total": total_questions
        }
    }


def load_results_file(filepath: str) -> list[dict]:
    """Load model results from JSON file."""
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser(
        description="MindRead++ Scorer — compute accuracy per tier",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example usage:
  python scorer.py --results results/gpt4o_responses.json
  python scorer.py --results results/gpt4o_responses.json --output results/gpt4o_scores.json

Input format (JSON list):
  [
    {"question_id": "Q_SCN001_T1", "tier": 1, "predicted": "A", "correct": "A", "reasoning": "..."},
    ...
  ]
        """
    )
    parser.add_argument("--results", required=True, help="Path to model results JSON file")
    parser.add_argument("--output", default=None, help="Path to save scores (JSON)")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.results):
        print(f"Error: Results file not found: {args.results}")
        sys.exit(1)
    
    results = load_results_file(args.results)
    scores = score_model(results)
    
    print("=" * 50)
    print("MindRead++ Scoring Results")
    print("=" * 50)
    print(f"\nTier 1 (First-order ToM):  {scores['tier_1']['accuracy']:.1%} ({scores['tier_1']['correct']}/{scores['tier_1']['total']})")
    print(f"Tier 2 (Second-order ToM): {scores['tier_2']['accuracy']:.1%} ({scores['tier_2']['correct']}/{scores['tier_2']['total']})")
    print(f"Tier 3 (Counterfactual):   {scores['tier_3']['accuracy']:.1%} ({scores['tier_3']['correct']}/{scores['tier_3']['total']})")
    print(f"\nOverall: {scores['overall']['accuracy']:.1%} ({scores['overall']['correct']}/{scores['overall']['total']})")
    
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(scores, f, indent=2)
        print(f"\nScores saved to: {args.output}")


if __name__ == "__main__":
    main()
