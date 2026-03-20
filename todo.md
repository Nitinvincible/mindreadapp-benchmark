# MindRead++ — Complete Project Brief & Build Plan

> **Competition:** Kaggle · Measuring Progress Toward AGI · Social Cognition Track  
> **Submission:** Best Overall Benchmark  
> **Language:** English only  
> **Status:** 🟡 In Progress

---

## Phase 1 — Repository Setup
- [ ] Create GitHub repo: `mindreadpp-benchmark`
- [ ] Add `README.md` with project overview, structure, and usage
- [ ] Add `LICENSE` (MIT recommended)
- [ ] Add `.gitignore` for Python projects
- [ ] Set repo to Public before submission deadline

---

## Phase 2 — Dataset Creation

### 2.1 Scenario authoring
- [ ] Write **50 base vignettes** (3 characters, 2–4 events each)
  - [ ] 17 domestic / everyday settings
  - [ ] 17 workplace / professional settings
  - [ ] 16 social / public settings
- [ ] Ensure each vignette creates clear information asymmetries between agents

### 2.2 Question generation (per vignette × 3 tiers)
- [ ] **Tier 1** — First-order ToM question + correct answer + 3 distractors
- [ ] **Tier 2** — Second-order ToM question + correct answer + 3 distractors
- [ ] **Tier 3** — Counterfactual ToM question + correct answer + 3 distractors

### 2.3 Anti-memorization variants (per vignette × 5 variants)
- [ ] **Original** — base scenario as authored
- [ ] **Paraphrase A** — different names and setting, identical logic
- [ ] **Paraphrase B** — different vocabulary and framing, identical logic
- [ ] **Role-swapped foil** — characters' information access transposed
- [ ] **Distractor injection** — plausible-but-wrong belief inserted mid-story

### 2.4 Dataset files
- [ ] `data/scenarios_base.json` — all 50 base vignettes with metadata
- [ ] `data/questions.json` — all questions across 3 tiers × 50 scenarios
- [ ] `data/variants.json` — all 5 variants × 50 scenarios
- [ ] `data/mindreadpp_full.csv` — flat CSV combining all of the above
- [ ] `data/sample_10.json` — 10-scenario sample for quick inspection

---

## Phase 3 — Evaluation Scripts

### 3.1 Core evaluation
- [ ] `eval/run_benchmark.py` — main entry point, loads dataset, queries model, scores output
- [ ] `eval/scorer.py` — accuracy scoring per tier (T1, T2, T3)
- [ ] `eval/rci.py` — Reasoning Consistency Index computation
  - [ ] Chain-of-thought extractor
  - [ ] Trace-to-answer alignment checker
  - [ ] RCI score output per model

### 3.2 Anti-memorization analysis
- [ ] `eval/variant_analysis.py` — compares model performance across all 5 variants
- [ ] Outputs variance score per model (high variance = pattern-matcher)

### 3.3 Reporting
- [ ] `eval/report.py` — generates per-model cognitive profile as JSON + CSV
- [ ] `eval/visualize.py` — plots tier scores, RCI, variant variance as charts

---

## Phase 4 — Model Testing

- [ ] Test on **GPT-4o** via OpenAI API
- [ ] Test on **Claude 3.5 Sonnet** via Anthropic API
- [ ] Test on **Gemini 1.5 Pro** via Google API
- [ ] Test on **Llama 3.1 70B** via open weights
- [ ] Record results in `results/model_scores.csv`
- [ ] Write up findings in `results/findings.md`

---

## Phase 5 — Kaggle Writeup (≤ 1500 words)

- [x] Title: MindRead++
- [x] Subtitle confirmed ✓
- [x] Thumbnail: matrix-coded sci-fi card ✓
- [x] Submission Track: Best Overall Benchmark ✓
- [x] Project Description: markdown ready ✓
- [x] Media Gallery: infographic done ✓
- [ ] Attachments:
  - [ ] Link: GitHub repo URL
  - [ ] Link: Kaggle Dataset (once uploaded)
  - [ ] File: `sample_10.json` uploaded directly
- [ ] Full writeup body (≤ 1500 words) covering:
  - [ ] Motivation & gap in existing benchmarks
  - [ ] Benchmark design & methodology
  - [ ] Anti-memorization filter explanation
  - [ ] RCI metric definition
  - [ ] Evaluation criteria & discriminatory power
  - [ ] Results / preliminary findings

---

## Phase 6 — Kaggle Dataset Upload

- [ ] Create Kaggle Dataset: `mindreadpp-benchmark-dataset`
- [ ] Upload `mindreadpp_full.csv` and `scenarios_base.json`
- [ ] Set dataset to Public
- [ ] Link dataset in writeup attachments

---

## Phase 7 — Final Review & Submit

- [ ] Proofread full writeup for 1500-word limit
- [ ] Verify all links are public and accessible
- [ ] Check dataset format matches competition requirements
- [ ] Submit before deadline

---

## File Structure (target)

```
mindreadpp-benchmark/
├── README.md
├── LICENSE
├── TODO.md
├── data/
│   ├── scenarios_base.json
│   ├── questions.json
│   ├── variants.json
│   ├── mindreadpp_full.csv
│   └── sample_10.json
├── eval/
│   ├── run_benchmark.py
│   ├── scorer.py
│   ├── rci.py
│   ├── variant_analysis.py
│   ├── report.py
│   └── visualize.py
├── results/
│   ├── model_scores.csv
│   └── findings.md
└── writeup/
    ├── writeup_body.md
    └── infographic.png
```

---

## Build Order (recommended)

1. `README.md` — gives the repo a face immediately
2. `data/scenarios_base.json` — 10 sample scenarios to start
3. `data/questions.json` — questions for the 10 samples
4. `data/variants.json` — 5 variants for each sample
5. `eval/scorer.py` + `eval/rci.py` — core metrics
6. `eval/run_benchmark.py` — ties everything together
7. Scale to 50 full scenarios
8. Run models, record results
9. Write full writeup body
10. Submit

---

---

# SPECIFICATIONS & CONTEXT

> This section defines every data format, rubric, formula, and API spec needed to build MindRead++ without ambiguity. Read this before writing any code or data.

---

## SPEC 1 — JSON Schema: Scenarios

Every entry in `scenarios_base.json` must follow this exact schema:

```json
{
  "scenario_id": "SCN_001",
  "setting": "domestic",
  "characters": {
    "A": "Sara",
    "B": "Tom",
    "C": "Maya"
  },
  "events": [
    {
      "event_id": 1,
      "text": "Sara places her red notebook on the kitchen table.",
      "witnessed_by": ["A", "B"]
    },
    {
      "event_id": 2,
      "text": "Tom moves the notebook to the drawer while Sara is in the garden.",
      "witnessed_by": ["B", "C"]
    },
    {
      "event_id": 3,
      "text": "Sara comes back inside without speaking to Tom or Maya.",
      "witnessed_by": ["A"]
    }
  ],
  "belief_state_map": {
    "A_knows": ["event_1", "event_3"],
    "B_knows": ["event_1", "event_2", "event_3"],
    "C_knows": ["event_2"]
  },
  "ground_truth": {
    "A_believes_notebook_location": "kitchen table",
    "B_believes_notebook_location": "drawer",
    "C_believes_notebook_location": "drawer"
  },
  "tags": ["object_location", "false_belief", "information_asymmetry"],
  "difficulty": "medium"
}
```

**Field rules:**
- `scenario_id` — format `SCN_XXX`, zero-padded to 3 digits
- `setting` — one of: `domestic`, `workplace`, `social`
- `characters` — always exactly A, B, C with human first names
- `events` — minimum 2, maximum 4; each must specify `witnessed_by`
- `belief_state_map` — must be derivable directly from `witnessed_by` fields
- `ground_truth` — explicit belief state per character, used for answer validation
- `difficulty` — one of: `easy`, `medium`, `hard`

---

## SPEC 2 — JSON Schema: Questions

Every entry in `questions.json` must follow this schema:

```json
{
  "question_id": "Q_SCN001_T1",
  "scenario_id": "SCN_001",
  "variant": "original",
  "tier": 1,
  "tier_name": "first_order_tom",
  "question_text": "When Sara returns to the kitchen, where does she think her notebook is?",
  "answer_type": "multiple_choice",
  "choices": {
    "A": "On the kitchen table",
    "B": "In the drawer",
    "C": "In the garden",
    "D": "She does not know where it is"
  },
  "correct_answer": "A",
  "explanation": "Sara only witnessed event_1 and event_3. She never saw Tom move the notebook, so she still believes it is on the kitchen table where she left it.",
  "requires_cot": true
}
```

**Field rules:**
- `question_id` — format `Q_SCNXXX_TX` e.g. `Q_SCN001_T2`
- `variant` — one of: `original`, `paraphrase_a`, `paraphrase_b`, `role_swap`, `distractor`
- `tier` — integer 1, 2, or 3
- `answer_type` — always `multiple_choice` for this benchmark
- `choices` — always exactly 4 options (A, B, C, D)
- `correct_answer` — single capital letter
- `explanation` — human-readable justification citing specific events
- `requires_cot` — always `true`; every question requires a reasoning trace

**Tier question templates:**

| Tier | Question template |
|------|-------------------|
| T1 | "Where does [A] think [object] is?" / "What does [A] believe about [X]?" |
| T2 | "Where does [A] think [B] thinks [object] is?" / "What does [A] think [B] believes about [X]?" |
| T3 | "If [A] had witnessed [event], what would [A] think [B] intended by [action]?" |

---

## SPEC 3 — JSON Schema: Variants

Every entry in `variants.json` must follow this schema:

```json
{
  "variant_id": "VAR_SCN001_PA",
  "scenario_id": "SCN_001",
  "variant_type": "paraphrase_a",
  "character_map": {
    "A": "Priya",
    "B": "James",
    "C": "Lucia"
  },
  "setting_change": "office breakroom instead of kitchen",
  "object_change": "blue folder instead of red notebook",
  "events_text": [
    "Priya places her blue folder on the breakroom counter.",
    "James moves the folder to the cabinet while Priya is on a call.",
    "Priya returns to the breakroom without speaking to James or Lucia."
  ],
  "logic_preserved": true,
  "belief_state_map": {
    "A_knows": ["event_1", "event_3"],
    "B_knows": ["event_1", "event_2", "event_3"],
    "C_knows": ["event_2"]
  },
  "notes": "All character names, setting, and object changed. Information access structure identical to original."
}
```

**Variant construction rules:**

| Variant | What changes | What must stay identical |
|---------|-------------|--------------------------|
| `paraphrase_a` | Names, setting, object | Event sequence, witnessed_by, belief_state_map |
| `paraphrase_b` | Vocabulary, sentence structure | Event sequence, witnessed_by, belief_state_map |
| `role_swap` | Which character witnesses which events | Number of events, object, setting |
| `distractor` | Adds one false belief statement mid-story | Core event sequence and ground truth |

**Distractor injection rule:** The distractor statement must be:
1. Plausible given the story context
2. Contradicting the correct ground truth answer
3. Inserted after event 2 but before the final event
4. Phrased as an observation, not a direct statement of belief

---

## SPEC 4 — RCI Rubric (Reasoning Consistency Index)

### Formula
```
RCI = (correct answers with valid reasoning trace) / (total correct answers)
```

### What counts as a valid reasoning trace

A chain-of-thought is marked **VALID** if it satisfies ALL four criteria:

| Criterion | Description | Pass example | Fail example |
|-----------|-------------|--------------|--------------|
| **Event citation** | References at least one specific event | "Sara did not see Tom move it in event 2..." | "Sara probably doesn't know" |
| **Witness attribution** | Correctly identifies who witnessed what | "Only Tom and Maya witnessed the move..." | "Sara was there when Tom moved it" |
| **Belief isolation** | Separates what character knows vs what happened | "From Sara's perspective it's still on the table..." | "The notebook is in the drawer so Sara thinks it is too" |
| **Answer consistency** | Final answer follows logically from the trace | Trace says Sara didn't see move → answers "kitchen table" | Trace says Sara didn't see move → answers "drawer" |

A trace is marked **INVALID** if it fails ANY one criterion.

### RCI interpretation table

| RCI score | Interpretation |
|-----------|----------------|
| 0.9 – 1.0 | Strong genuine reasoner |
| 0.7 – 0.89 | Mostly reliable, occasional gaps |
| 0.5 – 0.69 | Mixed — likely pattern-matching combined with reasoning |
| < 0.5 | Probable guesser — right answers not supported by valid traces |

---

## SPEC 5 — Scoring Formula

### Tier accuracy
```
Tier_N_Accuracy = correct answers at Tier N / total questions at Tier N
```

### Variant consistency score
```
VCS = 1 - (std deviation of accuracy across 5 variants)
```
Higher VCS = more consistent = less surface-pattern reliance. Range: 0.0 to 1.0.

### Final composite score
```
Composite = (0.20 × T1_Accuracy)
          + (0.30 × T2_Accuracy)
          + (0.30 × T3_Accuracy)
          + (0.10 × RCI)
          + (0.10 × VCS)
```

**Weight rationale:**
- T1 weighted lowest (0.20) — easiest, most likely pattern-matched
- T2 and T3 weighted highest (0.30 each) — require genuine nested and counterfactual reasoning
- RCI and VCS each 10% — penalise guessing and surface-pattern reliance

---

## SPEC 6 — Model API Call Specification

### System prompt
```
You are being evaluated on a Theory of Mind benchmark.
You will be given a short story involving three characters and a series of events.
Read carefully and track what each character knows based only on what they witnessed.

For each question:
1. First write your reasoning step by step (chain of thought).
2. Then state your final answer as a single letter: A, B, C, or D.

Format your response exactly as:
REASONING: [your step-by-step reasoning here]
ANSWER: [single letter]
```

### User prompt template
```
Story:
{scenario_text}

Question ({tier_label}):
{question_text}

Options:
A) {choice_a}
B) {choice_b}
C) {choice_c}
D) {choice_d}
```

### API parameters (apply to all models)

| Parameter | Value | Reason |
|-----------|-------|--------|
| `temperature` | `0.0` | Deterministic outputs for reproducibility |
| `max_tokens` | `512` | Enough for reasoning trace + answer |
| `top_p` | `1.0` | No nucleus sampling at temp=0 |
| `n` | `1` | Single response per query |

### Model reference

| Model | API endpoint | Model string |
|-------|-------------|--------------|
| GPT-4o | OpenAI `/v1/chat/completions` | `gpt-4o-2024-08-06` |
| Claude 3.5 Sonnet | Anthropic `/v1/messages` | `claude-sonnet-4-5` |
| Gemini 1.5 Pro | Google `generateContent` | `gemini-1.5-pro` |
| Llama 3.1 70B | Together AI | `meta-llama/Meta-Llama-3.1-70B-Instruct` |

---

## SPEC 7 — Validation Plan

### Step 1 — Logic check (self-review)
For every scenario verify manually:
- [ ] `belief_state_map` is derivable purely from `witnessed_by` fields
- [ ] `ground_truth` follows logically from `belief_state_map`
- [ ] The correct answer to each question is unambiguous
- [ ] Distractors are plausible but clearly wrong given the logic

### Step 2 — Peer review (minimum 2 human reviewers)
Ask two people to answer 10 scenarios without seeing the answer key.

Target human accuracy benchmarks:
- T1: ≥ 85%
- T2: ≥ 70%
- T3: ≥ 55%

If a scenario scores below these thresholds with humans → revise or discard.

### Step 3 — Difficulty calibration
After human review, label each scenario:
- `easy` — all reviewers answered T1 and T2 correctly
- `medium` — reviewers split on T2, most correct on T1
- `hard` — reviewers split on T3, some errors on T2

### Step 4 — Variant logic audit
For each variant verify:
- [ ] `logic_preserved: true` is accurate
- [ ] Role-swapped foil actually inverts information access
- [ ] Distractor is inserted at the right position and does not accidentally become true

### Step 5 — Blind difficulty check
Run each scenario through GPT-4o at temperature=1.0 (non-deterministic, 5 runs):
- T1 correct > 95% across variants → too easy, consider revising
- T1 correct < 40% → likely ambiguous, review wording

---

## Full example scenario (end-to-end)

### Base scenario (SCN_001)

> Sara places her red notebook on the kitchen table. Both Sara and Tom are present.
> Tom moves the notebook to the drawer while Sara is in the garden. Maya witnesses this too.
> Sara returns to the kitchen without speaking to anyone.

### Tier 1 question
**Q:** When Sara returns, where does she think her notebook is?
- A) On the kitchen table ← **correct**
- B) In the drawer
- C) In the garden
- D) She does not know it exists

**Valid reasoning trace:**
> REASONING: Sara placed the notebook on the table in event 1 and was present. In event 2, Tom moved it to the drawer, but Sara was in the garden — she did not witness this. In event 3, Sara returned but received no new information. From Sara's perspective, the notebook is still on the table.
> ANSWER: A

### Tier 2 question
**Q:** Where does Sara think Tom thinks the notebook is?
- A) On the kitchen table ← **correct**
- B) In the drawer
- C) Sara thinks Tom doesn't know about the notebook
- D) In the garden

**Valid reasoning trace:**
> REASONING: Sara knows Tom was present in event 1 when she placed the notebook. Sara was in the garden during event 2 and does not know Tom moved it. From Sara's point of view, Tom also last saw the notebook on the table, so she would assume Tom's belief mirrors hers — notebook on the table.
> ANSWER: A

> ⚠️ This is intentionally tricky. The correct answer is A, not B. Tests whether models confuse "what B actually knows" with "what A thinks B knows."

### Tier 3 question
**Q:** If Sara had seen Tom move the notebook, what would she most likely think Tom intended?
- A) Tom was tidying up to help
- B) Tom was hiding the notebook from her ← **correct**
- C) Tom was moving it to a safer place
- D) Tom was confused about where it belonged

**Valid reasoning trace:**
> REASONING: Counterfactually, if Sara had witnessed Tom move her personal notebook without asking, in the absence of any context suggesting benign intent, moving someone's belongings without permission is typically interpreted as hiding or appropriating. Option B best reflects this default social interpretation.
> ANSWER: B

---

*Last updated: Full specifications added — ready to begin Phase 1 build*