"""
variant_analysis.py — Anti-memorization analysis for MindRead++ benchmark.

Compares model accuracy across all 5 variant types to detect surface-pattern
reliance. High variance across variants indicates pattern-matching rather
than genuine reasoning.

Variant Consistency Score (VCS):
  VCS = 1 - std_dev(accuracy across 5 variants)
  Higher VCS = more consistent = less surface-pattern reliance
"""

from __future__ import annotations

import json
import argparse
import os
import sys
import numpy as np  # type: ignore[import-not-found]
from collections import defaultdict


VARIANT_TYPES = ["original", "paraphrase_a", "paraphrase_b", "role_swap", "distractor"]


def compute_variant_accuracy(results: list[dict]) -> dict:
    """Compute accuracy per variant type.
    
    Args:
        results: List of dicts with keys: question_id, variant, predicted, correct
    
    Returns:
        Dict mapping variant_type -> {accuracy, correct, total}
    """
    variant_groups = defaultdict(list)
    
    for r in results:
        variant = r.get("variant", "original")
        is_correct = r.get("predicted", "").upper() == r.get("correct", "").upper()
        variant_groups[variant].append(is_correct)
    
    accuracies = {}
    for variant in VARIANT_TYPES:
        group = variant_groups.get(variant, [])
        if group:
            correct = sum(group)
            total = len(group)
            accuracies[variant] = {
                "accuracy": correct / total,
                "correct": correct,
                "total": total
            }
        else:
            accuracies[variant] = {"accuracy": 0.0, "correct": 0, "total": 0}
    
    return accuracies


def compute_vcs(variant_accuracies: dict) -> float:
    """Compute Variant Consistency Score.
    
    VCS = 1 - std_dev(accuracy across variants with data)
    Range: 0.0 to 1.0 (higher = more consistent)
    """
    accs = [v["accuracy"] for v in variant_accuracies.values() if v["total"] > 0]
    
    if len(accs) < 2:
        return 1.0  # Can't compute variance with < 2 data points
    
    std = float(np.std(accs))
    vcs = max(0.0, 1.0 - std)  # type: ignore[call-overload]
    return round(vcs, 4)  # type: ignore[call-overload]


def compute_per_scenario_variance(results: list[dict]) -> list[dict]:
    """Compute accuracy variance per scenario across variants.
    
    Returns list of scenarios sorted by variance (highest first),
    helping identify which scenarios are most affected by surface changes.
    """
    scenario_variant_results = defaultdict(lambda: defaultdict(list))
    
    for r in results:
        sid = r.get("scenario_id", "unknown")
        variant = r.get("variant", "original")
        is_correct = r.get("predicted", "").upper() == r.get("correct", "").upper()
        scenario_variant_results[sid][variant].append(is_correct)
    
    scenario_variances = []
    for sid, variants in scenario_variant_results.items():
        accs = []
        for variant_type in VARIANT_TYPES:
            if variant_type in variants:
                group = variants[variant_type]
                accs.append(sum(group) / len(group))
        
        if len(accs) >= 2:
            variance = float(np.var(accs))
            scenario_variances.append({
                "scenario_id": sid,
                "variant_accuracies": {vt: sum(variants.get(vt, [])) / max(len(variants.get(vt, [])), 1)
                                       for vt in VARIANT_TYPES if vt in variants},
                "accuracy_variance": round(variance, 4),  # type: ignore[call-overload]
                "flagged": variance > 0.1  # High variance threshold
            })
    
    scenario_variances.sort(key=lambda x: x["accuracy_variance"], reverse=True)
    return scenario_variances


def analyze_model(results: list[dict]) -> dict:
    """Full variant analysis for a model.
    
    Returns comprehensive report including VCS, per-variant accuracy,
    and per-scenario variance analysis.
    """
    variant_accuracies = compute_variant_accuracy(results)
    vcs = compute_vcs(variant_accuracies)
    per_scenario = compute_per_scenario_variance(results)
    
    flagged_count = sum(1 for s in per_scenario if s.get("flagged", False))
    
    # Interpretation
    if vcs >= 0.9:
        interpretation = "Highly consistent — reasoning appears robust to surface changes"
    elif vcs >= 0.7:
        interpretation = "Mostly consistent — minor sensitivity to paraphrasing"
    elif vcs >= 0.5:
        interpretation = "Moderately inconsistent — significant surface-pattern reliance"
    else:
        interpretation = "Highly inconsistent — likely pattern-matching, not reasoning"
    
    return {
        "vcs": vcs,
        "interpretation": interpretation,
        "variant_accuracies": variant_accuracies,
        "flagged_scenarios": flagged_count,
        "total_scenarios_analyzed": len(per_scenario),
        "per_scenario_variance": per_scenario
    }


def main():
    parser = argparse.ArgumentParser(
        description="MindRead++ Variant Analysis — anti-memorization scoring",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example usage:
  python variant_analysis.py --results results/gpt4o_all_variants.json
  python variant_analysis.py --results results/gpt4o_all_variants.json --output results/gpt4o_vcs.json

VCS Interpretation:
  ≥ 0.9  Highly consistent
  ≥ 0.7  Mostly consistent
  ≥ 0.5  Moderately inconsistent
  < 0.5  Highly inconsistent (pattern-matcher)
        """
    )
    parser.add_argument("--results", required=True, help="Path to model results JSON (all variants)")
    parser.add_argument("--output", default=None, help="Path to save analysis (JSON)")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.results):
        print(f"Error: File not found: {args.results}")
        sys.exit(1)
    
    with open(args.results, "r", encoding="utf-8") as f:
        results = json.load(f)
    
    report = analyze_model(results)
    
    print("=" * 50)
    print("MindRead++ Variant Analysis")
    print("=" * 50)
    print(f"\nVariant Consistency Score (VCS): {report['vcs']:.2%}")
    print(f"Interpretation: {report['interpretation']}")
    
    print("\nAccuracy by variant type:")
    for vt in VARIANT_TYPES:
        va = report["variant_accuracies"][vt]
        bar = "█" * int(va["accuracy"] * 20) + "░" * (20 - int(va["accuracy"] * 20))
        print(f"  {vt:20s}: {bar} {va['accuracy']:.1%} ({va['correct']}/{va['total']})")
    
    print(f"\nFlagged scenarios (high variance): {report['flagged_scenarios']}/{report['total_scenarios_analyzed']}")
    
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        print(f"\nReport saved to: {args.output}")


if __name__ == "__main__":
    main()
