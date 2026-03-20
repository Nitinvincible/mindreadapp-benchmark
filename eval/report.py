"""
report.py — Generate per-model cognitive profiles for MindRead++ benchmark.

Outputs a comprehensive JSON + CSV report combining tier accuracy, RCI,
VCS, and composite score per SPEC 5.
"""
from __future__ import annotations

import json
import csv
import argparse
import os
import sys
from typing import Any

# Import sibling modules
_eval_dir = os.path.dirname(os.path.abspath(__file__))
if _eval_dir not in sys.path:
    sys.path.insert(0, _eval_dir)

from scorer import score_model  # type: ignore[import-not-found]
from rci import compute_rci  # type: ignore[import-not-found]
from variant_analysis import analyze_model as compute_variant_analysis  # type: ignore[import-not-found]


def compute_composite(t1_acc: float, t2_acc: float, t3_acc: float,
                      rci: float, vcs: float) -> float:
    """Compute the final composite score per SPEC 5.
    
    Composite = 0.20×T1 + 0.30×T2 + 0.30×T3 + 0.10×RCI + 0.10×VCS
    """
    raw: float = (0.20 * t1_acc +
                  0.30 * t2_acc +
                  0.30 * t3_acc +
                  0.10 * rci +
                  0.10 * vcs)
    return round(raw, 4)  # type: ignore[call-overload]


def generate_cognitive_profile(model_name: str, results: list[dict[str, Any]],
                                scenarios: dict[str, Any] | None = None) -> dict[str, Any]:
    """Generate a complete cognitive profile for a model.
    
    Args:
        model_name: Name/identifier of the model
        results: List of model response dicts
        scenarios: Optional scenario data for enhanced RCI analysis
    
    Returns:
        Dict with all metrics and composite score
    """
    # Tier accuracy
    scores = score_model(results)
    t1_acc = scores["tier_1"]["accuracy"]
    t2_acc = scores["tier_2"]["accuracy"]
    t3_acc = scores["tier_3"]["accuracy"]
    
    # RCI
    rci_report = compute_rci(results, scenarios)
    rci_score = rci_report["rci"]
    
    # VCS (variant analysis)
    variant_report = compute_variant_analysis(results)
    vcs_score = variant_report["vcs"]
    
    # Composite
    composite = compute_composite(t1_acc, t2_acc, t3_acc, rci_score, vcs_score)
    
    profile = {
        "model": model_name,
        "composite_score": composite,
        "tier_1_accuracy": round(t1_acc, 4),  # type: ignore[call-overload]
        "tier_2_accuracy": round(t2_acc, 4),  # type: ignore[call-overload]
        "tier_3_accuracy": round(t3_acc, 4),  # type: ignore[call-overload]
        "overall_accuracy": round(scores["overall"]["accuracy"], 4),  # type: ignore[call-overload]
        "rci": rci_score,
        "rci_interpretation": rci_report["interpretation"],
        "vcs": vcs_score,
        "vcs_interpretation": variant_report["interpretation"],
        "tier_1_detail": scores["tier_1"],
        "tier_2_detail": scores["tier_2"],
        "tier_3_detail": scores["tier_3"],
        "weight_breakdown": {
            "T1_contribution": round(0.20 * t1_acc, 4),  # type: ignore[call-overload]
            "T2_contribution": round(0.30 * t2_acc, 4),  # type: ignore[call-overload]
            "T3_contribution": round(0.30 * t3_acc, 4),  # type: ignore[call-overload]
            "RCI_contribution": round(0.10 * rci_score, 4),  # type: ignore[call-overload]
            "VCS_contribution": round(0.10 * vcs_score, 4),  # type: ignore[call-overload]
        }
    }
    
    return profile


def save_profile_csv(profiles: list[dict], filepath: str):
    """Save multiple model profiles to CSV."""
    fieldnames = [
        "model", "composite_score",
        "tier_1_accuracy", "tier_2_accuracy", "tier_3_accuracy",
        "overall_accuracy", "rci", "vcs"
    ]
    
    with open(filepath, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(profiles)


def main():
    parser = argparse.ArgumentParser(
        description="MindRead++ Report — generate per-model cognitive profiles",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example usage:
  python report.py --results results/gpt4o_responses.json --model gpt-4o
  python report.py --input results/model_scores.csv --output results/

Output:
  - JSON cognitive profile per model
  - CSV summary row appended to model_scores.csv
        """
    )
    parser.add_argument("--results", required=True, help="Path to model results JSON")
    parser.add_argument("--model", default="unknown", help="Model name")
    parser.add_argument("--scenarios", default=None, help="Path to scenarios_base.json")
    parser.add_argument("--output", default="results/", help="Output directory")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.results):
        print(f"Error: File not found: {args.results}")
        sys.exit(1)
    
    with open(args.results, "r", encoding="utf-8") as f:
        results = json.load(f)
    
    scenarios = None
    if args.scenarios and os.path.exists(args.scenarios):
        with open(args.scenarios, "r", encoding="utf-8") as f:
            scn_list = json.load(f)
            scenarios = {s["scenario_id"]: s for s in scn_list}
    
    os.makedirs(args.output, exist_ok=True)
    
    profile = generate_cognitive_profile(args.model, results, scenarios)
    
    # Save JSON profile
    json_path = os.path.join(args.output, f"{args.model.replace('/', '_')}_profile.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(profile, f, indent=2)
    
    # Save/append to CSV
    csv_path = os.path.join(args.output, "model_scores.csv")
    save_profile_csv([profile], csv_path)
    
    # Display
    print("=" * 60)
    print(f"  MindRead++ Cognitive Profile: {args.model}")
    print("=" * 60)
    print(f"\n  Composite Score:    {profile['composite_score']:.2%}")
    print(f"  ─────────────────────────────────────")
    print(f"  T1 Accuracy:        {profile['tier_1_accuracy']:.1%}  (×0.20 = {profile['weight_breakdown']['T1_contribution']:.3f})")
    print(f"  T2 Accuracy:        {profile['tier_2_accuracy']:.1%}  (×0.30 = {profile['weight_breakdown']['T2_contribution']:.3f})")
    print(f"  T3 Accuracy:        {profile['tier_3_accuracy']:.1%}  (×0.30 = {profile['weight_breakdown']['T3_contribution']:.3f})")
    print(f"  RCI:                {profile['rci']:.1%}  (×0.10 = {profile['weight_breakdown']['RCI_contribution']:.3f})")
    print(f"  VCS:                {profile['vcs']:.1%}  (×0.10 = {profile['weight_breakdown']['VCS_contribution']:.3f})")
    print(f"\n  RCI: {profile['rci_interpretation']}")
    print(f"  VCS: {profile['vcs_interpretation']}")
    print(f"\n  Saved: {json_path}")
    print(f"  Saved: {csv_path}")


if __name__ == "__main__":
    main()
