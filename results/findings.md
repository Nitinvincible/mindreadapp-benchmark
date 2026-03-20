# MindRead++ — Model Evaluation Findings

> **Benchmark version:** 1.0
> **Date:** _TBD_
> **Evaluator:** _TBD_

---

## Models Tested

| Model | Provider | Date Tested | Notes |
|-------|----------|-------------|-------|
| GPT-4o | OpenAI | — | `gpt-4o-2024-08-06` |
| Claude 3.5 Sonnet | Anthropic | — | `claude-sonnet-4-5` |
| Gemini 1.5 Pro | Google | — | `gemini-1.5-pro` |
| Llama 3.1 70B | Together AI | — | `Meta-Llama-3.1-70B-Instruct` |

---

## Summary Results

| Model | Composite | T1 | T2 | T3 | RCI | VCS |
|-------|-----------|----|----|----|----|-----|
| _TBD_ | — | — | — | — | — | — |

---

## Key Findings

### 1. Tier Performance Gradient
_Describe how accuracy changes from T1 → T2 → T3. Expected: T1 > T2 > T3._

### 2. Reasoning Consistency
_Describe RCI patterns. Which models show genuine reasoning vs. pattern-matching?_

### 3. Anti-Memorization Robustness
_Describe VCS patterns. Which models are robust across variants?_

### 4. Notable Failure Modes
_Document specific scenarios where models failed in interesting ways._

---

## Detailed Analysis

### Per-Tier Observations

**Tier 1 (First-order ToM):**
- _Findings..._

**Tier 2 (Second-order ToM):**
- _Findings..._

**Tier 3 (Counterfactual ToM):**
- _Findings..._

### Variant Sensitivity

**Paraphrase Robustness:**
- _Findings on paraphrase_a and paraphrase_b..._

**Role-Swap Impact:**
- _Findings on role_swap variant..._

**Distractor Injection:**
- _Findings on distractor variant..._

---

## Recommendations

1. _Recommendation 1_
2. _Recommendation 2_
3. _Recommendation 3_

---

## Appendix

- Full results: `model_scores.csv`
- Charts: `charts/` directory
- Raw responses: `{model}_responses_{timestamp}.json`
