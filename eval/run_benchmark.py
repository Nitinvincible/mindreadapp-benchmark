"""
run_benchmark.py — Main entry point for MindRead++ benchmark evaluation.

Loads dataset, queries model APIs, scores output, computes RCI and VCS,
and saves comprehensive results.

Usage:
  python run_benchmark.py --model gemini-2.0-flash --api-key YOUR_KEY
  python run_benchmark.py --model gpt-4o --api-key YOUR_KEY --sample
  python run_benchmark.py --help
"""
from __future__ import annotations

import json
import argparse
import os
import sys
import time
from datetime import datetime

# Try to import API clients (graceful fallback)
try:
    import openai  # type: ignore[import-not-found]
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

try:
    import anthropic  # type: ignore[import-not-found]
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False

try:
    from google import genai  # type: ignore[import-not-found]
    from google.genai import types  # type: ignore[import-not-found]
    HAS_GOOGLE = True
except ImportError:
    HAS_GOOGLE = False

try:
    from sarvamai import SarvamAI  # type: ignore[import-not-found]
    HAS_SARVAM = True
except ImportError:
    HAS_SARVAM = False

# Import evaluation modules
EVAL_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, EVAL_DIR)
from scorer import score_model, extract_answer  # type: ignore[import-not-found]
from rci import compute_rci  # type: ignore[import-not-found]
from variant_analysis import analyze_model as compute_variant_analysis  # type: ignore[import-not-found]
from report import generate_cognitive_profile  # type: ignore[import-not-found]

# ── Constants ───────────────────────────────────────────────────────────────

DATA_DIR = os.path.join(os.path.dirname(EVAL_DIR), "data")
RESULTS_DIR = os.path.join(os.path.dirname(EVAL_DIR), "results")

SYSTEM_PROMPT = """You are being evaluated on a Theory of Mind benchmark.
You will be given a short story involving three characters and a series of events.
Read carefully and track what each character knows based only on what they witnessed.

For each question:
1. First write your reasoning step by step (chain of thought).
2. Then state your final answer as a single letter: A, B, C, or D.

Format your response exactly as:
REASONING: [your step-by-step reasoning here]
ANSWER: [single letter]"""

USER_PROMPT_TEMPLATE = """Story:
{scenario_text}

Question ({tier_label}):
{question_text}

Options:
A) {choice_a}
B) {choice_b}
C) {choice_c}
D) {choice_d}"""

MODEL_CONFIG = {
    "gpt-4o": {
        "provider": "openai",
        "model_string": "gpt-4o-2024-08-06",
        "requires": "openai"
    },
    "claude-3.5-sonnet": {
        "provider": "anthropic",
        "model_string": "claude-sonnet-4-5",
        "requires": "anthropic"
    },
    "gemini-2.0-flash": {
        "provider": "google",
        "model_string": "gemini-2.0-flash",
        "requires": "google"
    },
    "llama-3.1-70b": {
        "provider": "openai",  # Uses Together AI with OpenAI-compatible API
        "model_string": "meta-llama/Meta-Llama-3.1-70B-Instruct",
        "base_url": "https://api.together.xyz/v1",
        "requires": "openai"
    },
    "sarvam-30b": {
        "provider": "sarvam",
        "model_string": "sarvam-30b",
        "requires": "sarvamai"
    }
}

API_PARAMS = {
    "temperature": 0.0,
    "max_tokens": 512,
    "top_p": 1.0,
}

TIER_LABELS = {1: "Tier 1 — First-order ToM", 2: "Tier 2 — Second-order ToM", 3: "Tier 3 — Counterfactual ToM"}


# ── Data Loading ────────────────────────────────────────────────────────────

def load_dataset(sample: bool = False):
    """Load scenarios, questions from data directory."""
    if sample:
        sample_path = os.path.join(DATA_DIR, "sample_10.json")
        with open(sample_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data["scenarios"], data["questions"]
    
    scenarios_path = os.path.join(DATA_DIR, "scenarios_base.json")
    questions_path = os.path.join(DATA_DIR, "questions.json")
    
    with open(scenarios_path, "r", encoding="utf-8") as f:
        scenarios = json.load(f)
    with open(questions_path, "r", encoding="utf-8") as f:
        questions = json.load(f)
    
    return scenarios, questions


def build_narrative(scenario: dict) -> str:
    """Build narrative text from scenario events."""
    return " ".join(e["text"] for e in scenario["events"])


# ── API Callers ─────────────────────────────────────────────────────────────

def call_openai(model_string: str, api_key: str, prompt: str,
                base_url: str | None = None) -> str:
    """Call OpenAI-compatible API."""
    if not HAS_OPENAI:
        raise ImportError("openai package not installed. Run: pip install openai")
    
    kwargs = {"api_key": api_key}
    if base_url:
        kwargs["base_url"] = base_url
    
    client = openai.OpenAI(**kwargs)
    response = client.chat.completions.create(
        model=model_string,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        temperature=API_PARAMS["temperature"],
        max_tokens=API_PARAMS["max_tokens"],
        top_p=API_PARAMS["top_p"],
        n=1
    )
    return response.choices[0].message.content


def call_anthropic(model_string: str, api_key: str, prompt: str) -> str:
    """Call Anthropic API."""
    if not HAS_ANTHROPIC:
        raise ImportError("anthropic package not installed. Run: pip install anthropic")
    
    client = anthropic.Anthropic(api_key=api_key)
    response = client.messages.create(
        model=model_string,
        max_tokens=API_PARAMS["max_tokens"],
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
        temperature=API_PARAMS["temperature"],
        top_p=API_PARAMS["top_p"],
    )
    return response.content[0].text


def call_google(model_string: str, api_key: str, prompt: str) -> str:
    """Call Google Gemini API."""
    if not HAS_GOOGLE:
        raise ImportError("google-genai package not installed. Run: pip install google-genai")
    
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=model_string,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=API_PARAMS["temperature"],
            max_output_tokens=API_PARAMS["max_tokens"],
            top_p=API_PARAMS["top_p"],
        )
    )
    return response.text or ""


def call_sarvam(model_string: str, api_key: str, prompt: str) -> str:
    """Call Sarvam AI API."""
    if not HAS_SARVAM:
        raise ImportError("sarvamai package not installed. Run: pip install sarvamai")
    
    client = SarvamAI(api_subscription_key=api_key)
    response = client.chat.completions(
        model=model_string,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        temperature=API_PARAMS["temperature"],
        top_p=API_PARAMS["top_p"],
        max_tokens=API_PARAMS["max_tokens"],
    )
    content = response.choices[0].message.content
    return content if content is not None else ""


def call_model(model_name: str, api_key: str, prompt: str) -> str:
    """Route to the appropriate API caller."""
    config = MODEL_CONFIG.get(model_name)
    if not config:
        raise ValueError(f"Unknown model: {model_name}. Available: {list(MODEL_CONFIG.keys())}")
    
    provider = config["provider"]
    model_string = config["model_string"]
    
    if provider == "openai":
        return call_openai(model_string, api_key, prompt,
                          base_url=config.get("base_url"))  # type: ignore[arg-type]
    elif provider == "anthropic":
        return call_anthropic(model_string, api_key, prompt)
    elif provider == "google":
        return call_google(model_string, api_key, prompt)
    elif provider == "sarvam":
        return call_sarvam(model_string, api_key, prompt)
    else:
        raise ValueError(f"Unknown provider: {provider}")


# ── Main Benchmark Loop ────────────────────────────────────────────────────

def run_benchmark(model_name: str, api_key: str, sample: bool = False,
                  delay: float = 1.0) -> list[dict]:
    """Run the full benchmark on a model.
    
    Args:
        model_name: Key in MODEL_CONFIG
        api_key: API key for the model provider
        sample: If True, use 10-scenario sample
        delay: Seconds between API calls
    
    Returns:
        List of result dicts with predictions and response texts
    """
    print(f"\n{'='*60}")
    print(f"  MindRead++ Benchmark — {model_name}")
    print(f"{'='*60}")
    
    scenarios, questions = load_dataset(sample=sample)
    scenario_map = {s["scenario_id"]: s for s in scenarios}
    
    print(f"  Scenarios: {len(scenarios)}")
    print(f"  Questions: {len(questions)}")
    print(f"  Mode: {'SAMPLE (10 scenarios)' if sample else 'FULL (50 scenarios)'}")
    print()
    
    results = []
    total = len(questions)
    
    for i, q in enumerate(questions):
        scenario = scenario_map[q["scenario_id"]]
        narrative = build_narrative(scenario)
        tier_label = TIER_LABELS.get(q["tier"], f"Tier {q['tier']}")
        
        prompt = USER_PROMPT_TEMPLATE.format(
            scenario_text=narrative,
            tier_label=tier_label,
            question_text=q["question_text"],
            choice_a=q["choices"]["A"],
            choice_b=q["choices"]["B"],
            choice_c=q["choices"]["C"],
            choice_d=q["choices"]["D"]
        )
        
        try:
            response_text = call_model(model_name, api_key, prompt)
            predicted = extract_answer(response_text)
        except Exception as e:
            print(f"  ⚠ Error on {q['question_id']}: {e}")
            response_text = f"ERROR: {e}"
            predicted = None
        
        is_correct = predicted and predicted.upper() == q["correct_answer"].upper()
        
        result = {
            "question_id": q["question_id"],
            "scenario_id": q["scenario_id"],
            "tier": q["tier"],
            "variant": q.get("variant", "original"),
            "predicted": predicted,
            "correct": q["correct_answer"],
            "is_correct": is_correct,
            "response_text": response_text,
        }
        results.append(result)
        
        status = "✓" if is_correct else "✗" if predicted else "?"
        print(f"  [{i+1:3d}/{total}] {q['question_id']:15s} T{q['tier']} | "
              f"Pred: {predicted or '?':1s} | Correct: {q['correct_answer']} | {status}")
        
        if delay > 0 and i < total - 1:
            time.sleep(delay)
    
    return results


def main():
    parser = argparse.ArgumentParser(
        description="MindRead++ Benchmark Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Available models:
  gpt-4o            OpenAI GPT-4o
  claude-3.5-sonnet Anthropic Claude 3.5 Sonnet
  gemini-2.0-flash  Google Gemini 2.0 Flash
  llama-3.1-70b     Meta Llama 3.1 70B (via Together AI)
  sarvam-30b        Sarvam 30B

Examples:
  python run_benchmark.py --model sarvam-30b --api-key YOUR_SARVAM_KEY --sample
  python run_benchmark.py --model gpt-4o --api-key sk-... --delay 2.0
        """
    )
    parser.add_argument("--model", required=True, choices=list(MODEL_CONFIG.keys()),
                        help="Model to evaluate")
    parser.add_argument("--api-key", required=True, help="API key for the model provider")
    parser.add_argument("--sample", action="store_true",
                        help="Use 10-scenario sample instead of full dataset")
    parser.add_argument("--delay", type=float, default=1.0,
                        help="Delay between API calls in seconds (default: 1.0)")
    parser.add_argument("--output", default=None,
                        help="Output directory (default: results/)")
    
    args = parser.parse_args()
    
    output_dir = args.output or RESULTS_DIR
    os.makedirs(output_dir, exist_ok=True)
    
    # Run benchmark
    results = run_benchmark(args.model, args.api_key,
                           sample=args.sample, delay=args.delay)
    
    # Save raw results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = os.path.join(output_dir, f"{args.model}_responses_{timestamp}.json")
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\n  Raw results saved: {results_file}")
    
    # Generate cognitive profile
    scenarios_path = os.path.join(DATA_DIR, "scenarios_base.json")
    scenarios = None
    if os.path.exists(scenarios_path):
        with open(scenarios_path, "r", encoding="utf-8") as f:
            scn_list = json.load(f)
            scenarios = {s["scenario_id"]: s for s in scn_list}
    
    profile = generate_cognitive_profile(args.model, results, scenarios)
    
    profile_file = os.path.join(output_dir, f"{args.model}_profile_{timestamp}.json")
    with open(profile_file, "w", encoding="utf-8") as f:
        json.dump(profile, f, indent=2)
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"  Results Summary — {args.model}")
    print(f"{'='*60}")
    print(f"  Composite Score:  {profile['composite_score']:.2%}")
    print(f"  T1 Accuracy:      {profile['tier_1_accuracy']:.1%}")
    print(f"  T2 Accuracy:      {profile['tier_2_accuracy']:.1%}")
    print(f"  T3 Accuracy:      {profile['tier_3_accuracy']:.1%}")
    print(f"  RCI:              {profile['rci']:.2%}  ({profile['rci_interpretation']})")
    print(f"  VCS:              {profile['vcs']:.2%}  ({profile['vcs_interpretation']})")
    print(f"\n  Profile saved: {profile_file}")
    print(f"  Results saved: {results_file}")


if __name__ == "__main__":
    main()
