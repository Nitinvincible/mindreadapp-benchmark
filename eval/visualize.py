"""
visualize.py — Chart generation for MindRead++ benchmark results.

Generates:
  1. Tier score bar chart (grouped by model)
  2. Composite score comparison
  3. RCI vs accuracy scatter
  4. Variant consistency heatmap
"""

import json
import csv
import argparse
import os
import sys
import matplotlib  # type: ignore[import-not-found]
matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt  # type: ignore[import-not-found]
import matplotlib.patches as mpatches  # type: ignore[import-not-found]
import numpy as np  # type: ignore[import-not-found]


# ── Color palette ───────────────────────────────────────────────────────────

COLORS = {
    "primary": "#6366f1",
    "secondary": "#8b5cf6",
    "accent": "#ec4899",
    "success": "#10b981",
    "warning": "#f59e0b",
    "danger": "#ef4444",
    "tier1": "#3b82f6",
    "tier2": "#8b5cf6",
    "tier3": "#ec4899",
    "rci": "#10b981",
    "vcs": "#f59e0b",
    "bg": "#1e1b4b",
    "text": "#e2e8f0",
    "grid": "#334155"
}

MODEL_COLORS = ["#6366f1", "#ec4899", "#10b981", "#f59e0b", "#3b82f6"]


def set_dark_style():
    """Apply dark theme to matplotlib."""
    plt.rcParams.update({
        "figure.facecolor": COLORS["bg"],
        "axes.facecolor": "#0f172a",
        "axes.edgecolor": COLORS["grid"],
        "axes.labelcolor": COLORS["text"],
        "xtick.color": COLORS["text"],
        "ytick.color": COLORS["text"],
        "text.color": COLORS["text"],
        "grid.color": COLORS["grid"],
        "grid.alpha": 0.3,
        "font.family": "sans-serif",
        "font.size": 11,
    })


def load_model_scores(filepath: str) -> list[dict]:
    """Load model scores from CSV."""
    scores = []
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            for key in ["composite_score", "tier_1_accuracy", "tier_2_accuracy",
                        "tier_3_accuracy", "overall_accuracy", "rci", "vcs"]:
                if key in row:
                    try:
                        row[key] = float(row[key])
                    except (ValueError, TypeError):
                        row[key] = 0.0
            scores.append(row)
    return scores


def plot_tier_comparison(scores: list[dict], output_dir: str):
    """Generate grouped bar chart comparing tier accuracy across models."""
    set_dark_style()
    
    models = [s["model"] for s in scores]
    n = len(models)
    
    if n == 0:
        return
    
    fig, ax = plt.subplots(figsize=(max(10, int(n * 2.5)), 6))
    
    x = np.arange(n)
    width = 0.22
    
    bars_t1 = ax.bar(x - width, [s["tier_1_accuracy"] for s in scores],
                     width, label="T1 (First-order)", color=COLORS["tier1"], alpha=0.9)
    bars_t2 = ax.bar(x, [s["tier_2_accuracy"] for s in scores],
                     width, label="T2 (Second-order)", color=COLORS["tier2"], alpha=0.9)
    bars_t3 = ax.bar(x + width, [s["tier_3_accuracy"] for s in scores],
                     width, label="T3 (Counterfactual)", color=COLORS["tier3"], alpha=0.9)
    
    ax.set_ylabel("Accuracy")
    ax.set_title("MindRead++ — Tier Accuracy Comparison", fontsize=14, fontweight="bold", pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels(models, rotation=15, ha="right")
    ax.set_ylim(0, 1.05)
    ax.legend(loc="upper right", framealpha=0.8)
    ax.grid(axis="y", alpha=0.2)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f"{y:.0%}"))
    
    # Add value labels
    for bars in [bars_t1, bars_t2, bars_t3]:
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2., height + 0.01,
                    f"{height:.0%}", ha="center", va="bottom", fontsize=8)
    
    plt.tight_layout()
    path = os.path.join(output_dir, "tier_comparison.png")
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {path}")


def plot_composite_scores(scores: list[dict], output_dir: str):
    """Generate horizontal bar chart of composite scores."""
    set_dark_style()
    
    models = [s["model"] for s in scores]
    composites = [s["composite_score"] for s in scores]
    n = len(models)
    
    if n == 0:
        return
    
    fig, ax = plt.subplots(figsize=(10, max(4, int(n * 1.2))))
    
    # Sort by composite score
    sorted_pairs = sorted(zip(models, composites), key=lambda p: p[1])
    models_sorted = [p[0] for p in sorted_pairs]
    comps_sorted = [p[1] for p in sorted_pairs]
    
    colors = [plt.cm.viridis(c / max(max(comps_sorted), 0.01)) for c in comps_sorted]
    
    bars = ax.barh(range(n), comps_sorted, color=colors, alpha=0.9, height=0.6)
    
    ax.set_yticks(range(n))
    ax.set_yticklabels(models_sorted)
    ax.set_xlabel("Composite Score")
    ax.set_title("MindRead++ — Composite Score Ranking", fontsize=14, fontweight="bold", pad=15)
    ax.set_xlim(0, 1.05)
    ax.grid(axis="x", alpha=0.2)
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:.0%}"))
    
    for bar, val in zip(bars, comps_sorted):
        ax.text(val + 0.01, bar.get_y() + bar.get_height() / 2,
                f"{val:.1%}", va="center", fontsize=10)
    
    plt.tight_layout()
    path = os.path.join(output_dir, "composite_scores.png")
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {path}")


def plot_rci_vs_accuracy(scores: list[dict], output_dir: str):
    """Generate scatter plot of RCI vs overall accuracy."""
    set_dark_style()
    
    models = [s["model"] for s in scores]
    accs = [s["overall_accuracy"] for s in scores]
    rcis = [s["rci"] for s in scores]
    
    if not models:
        return
    
    fig, ax = plt.subplots(figsize=(8, 6))
    
    for i, (model, acc, rci) in enumerate(zip(models, accs, rcis)):
        color = MODEL_COLORS[i % len(MODEL_COLORS)]
        ax.scatter(acc, rci, s=150, c=color, alpha=0.9, zorder=5, edgecolors="white", linewidth=1)
        ax.annotate(model, (acc, rci), textcoords="offset points", xytext=(8, 8),
                    fontsize=9, color=color)
    
    # Quadrant lines
    ax.axhline(y=0.7, color=COLORS["grid"], linestyle="--", alpha=0.5)
    ax.axvline(x=0.7, color=COLORS["grid"], linestyle="--", alpha=0.5)
    
    # Quadrant labels
    ax.text(0.85, 0.85, "Strong Reasoner", ha="center", fontsize=8, alpha=0.5, style="italic")
    ax.text(0.35, 0.85, "Over-reasoner", ha="center", fontsize=8, alpha=0.5, style="italic")
    ax.text(0.85, 0.35, "Lucky Guesser", ha="center", fontsize=8, alpha=0.5, style="italic")
    ax.text(0.35, 0.35, "Weak", ha="center", fontsize=8, alpha=0.5, style="italic")
    
    ax.set_xlabel("Overall Accuracy")
    ax.set_ylabel("RCI Score")
    ax.set_title("MindRead++ — RCI vs Accuracy", fontsize=14, fontweight="bold", pad=15)
    ax.set_xlim(0, 1.05)
    ax.set_ylim(0, 1.05)
    ax.grid(alpha=0.2)
    
    plt.tight_layout()
    path = os.path.join(output_dir, "rci_vs_accuracy.png")
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {path}")


def plot_radar_profile(scores: list[dict], output_dir: str):
    """Generate radar/spider chart showing multi-dimensional profile per model."""
    set_dark_style()
    
    categories = ["T1 Accuracy", "T2 Accuracy", "T3 Accuracy", "RCI", "VCS"]
    n_cats = len(categories)
    angles = np.linspace(0, 2 * np.pi, n_cats, endpoint=False).tolist()
    angles += angles[:1]
    
    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
    ax.set_facecolor("#0f172a")
    fig.patch.set_facecolor(COLORS["bg"])
    
    for i, s in enumerate(scores):
        values = [s["tier_1_accuracy"], s["tier_2_accuracy"], s["tier_3_accuracy"],
                  s["rci"], s["vcs"]]
        values += values[:1]  # type: ignore[index]
        
        color = MODEL_COLORS[i % len(MODEL_COLORS)]
        ax.plot(angles, values, "o-", color=color, linewidth=2, label=s["model"], alpha=0.8)
        ax.fill(angles, values, color=color, alpha=0.1)
    
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, color=COLORS["text"])
    ax.set_ylim(0, 1)
    ax.set_title("MindRead++ — Model Cognitive Profile", fontsize=14,
                 fontweight="bold", pad=20, color=COLORS["text"])
    ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1), framealpha=0.8)
    ax.grid(color=COLORS["grid"], alpha=0.3)
    
    plt.tight_layout()
    path = os.path.join(output_dir, "radar_profile.png")
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {path}")


def main():
    parser = argparse.ArgumentParser(
        description="MindRead++ Visualize — generate benchmark charts",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example usage:
  python visualize.py --input results/model_scores.csv --output results/charts/

Generates:
  - tier_comparison.png    Grouped bar chart of T1/T2/T3 accuracy
  - composite_scores.png   Horizontal bar chart of composite scores
  - rci_vs_accuracy.png    Scatter plot of RCI vs accuracy
  - radar_profile.png      Spider chart of multi-metric profile
        """
    )
    parser.add_argument("--input", required=True, help="Path to model_scores.csv")
    parser.add_argument("--output", default="results/charts/", help="Output directory for charts")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input):
        print(f"Error: File not found: {args.input}")
        sys.exit(1)
    
    os.makedirs(args.output, exist_ok=True)
    
    scores = load_model_scores(args.input)
    print(f"Loaded {len(scores)} model(s) from {args.input}")
    
    if not scores:
        print("No data to visualize.")
        sys.exit(0)
    
    print("\nGenerating charts:")
    plot_tier_comparison(scores, args.output)
    plot_composite_scores(scores, args.output)
    plot_rci_vs_accuracy(scores, args.output)
    plot_radar_profile(scores, args.output)
    
    print(f"\n✅ All charts saved to: {args.output}")


if __name__ == "__main__":
    main()
