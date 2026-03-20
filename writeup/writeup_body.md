# MindRead++: A Multi-Tier Theory of Mind Benchmark with Anti-Memorization Controls

## Motivation & Gap

Theory of Mind (ToM) — the ability to attribute mental states to others — is a cornerstone of human social cognition. Existing ToM benchmarks for large language models, such as the Sally-Anne test and its derivatives, suffer from three critical limitations:

1. **Flat difficulty**: Most benchmarks test only first-order belief attribution ("What does Sally think?"), ignoring the recursive nature of real-world social reasoning.
2. **Memorization vulnerability**: Fixed scenarios with well-known structures allow models to pattern-match rather than reason. Many current benchmarks have been absorbed into training data.
3. **Binary scoring**: Pass/fail metrics cannot distinguish between a model that reasons correctly and one that guesses correctly through surface heuristics.

MindRead++ addresses all three gaps with a purpose-built benchmark featuring **tiered complexity**, **anti-memorization controls**, and a novel **Reasoning Consistency Index** that evaluates the quality of reasoning, not just the answer.

## Benchmark Design

### Scenarios

MindRead++ contains **50 original scenarios**, each featuring three named characters (A, B, C), 2–4 events, and carefully constructed **information asymmetries**. Every scenario specifies which characters witness which events, creating precise belief states that can be mathematically verified.

Settings span three categories to ensure diversity:
- **Domestic/everyday** (17 scenarios): kitchens, gardens, living rooms
- **Workplace/professional** (17 scenarios): offices, labs, meeting rooms
- **Social/public** (16 scenarios): parks, cafés, schools

### Three-Tier Question Structure

Each scenario generates three questions at increasing cognitive complexity:

| Tier | Type | Example |
|------|------|---------|
| **T1** | First-order ToM | "Where does Sara think the notebook is?" |
| **T2** | Second-order ToM | "Where does Sara think Tom thinks the notebook is?" |
| **T3** | Counterfactual ToM | "If Sara had seen Tom move the notebook, what would she think Tom intended?" |

This yields **150 questions** total. Every question includes one correct answer and three plausible distractors, all requiring chain-of-thought reasoning.

## Anti-Memorization Filter

To prevent models from exploiting memorized patterns, each scenario exists in **five variants**:

1. **Original** — base scenario as authored
2. **Paraphrase A** — different character names, setting, and object; identical logic
3. **Paraphrase B** — different vocabulary and sentence structure; identical logic
4. **Role-swapped foil** — characters' information access is transposed
5. **Distractor injection** — a plausible but false belief statement is inserted mid-narrative

Variants 1–3 test **paraphrase robustness**: a genuine reasoner should score equally across surface changes. Variant 4 directly tests whether the model tracks information states or relies on character-name heuristics. Variant 5 tests resistance to misleading context.

This produces **250 variant scenarios** for comprehensive anti-memorization evaluation.

## Reasoning Consistency Index (RCI)

Traditional accuracy conflates correct reasoning with lucky guessing. Our Reasoning Consistency Index separates them:

**RCI = (correct answers with valid reasoning trace) / (total correct answers)**

A reasoning trace is marked **valid** only if it satisfies all four criteria:

1. **Event citation** — references at least one specific story event
2. **Witness attribution** — correctly identifies who witnessed what
3. **Belief isolation** — separates what a character knows from what actually happened
4. **Answer consistency** — the final answer follows logically from the stated reasoning

An RCI of 0.9+ indicates a strong genuine reasoner. Below 0.5 suggests the model frequently guesses correctly without valid reasoning support.

## Scoring & Discriminatory Power

The composite score weights higher-order reasoning more heavily:

```
Composite = 0.20×T1 + 0.30×T2 + 0.30×T3 + 0.10×RCI + 0.10×VCS
```

Where VCS (Variant Consistency Score) = 1 − σ(accuracy across 5 variants).

This weighting scheme ensures that:
- First-order ToM (easiest, most pattern-matchable) contributes least
- Second-order and counterfactual reasoning (requiring genuine nested cognition) dominate
- Models that guess correctly or rely on surface patterns are penalized via RCI and VCS

## Evaluation Methodology

Models are evaluated using standardized prompts with `temperature=0.0` for reproducibility. Each response must include a structured chain-of-thought followed by a single-letter answer. The system prompt explicitly instructs models to track character knowledge based solely on witnessed events.

We provide complete evaluation infrastructure: a benchmark runner supporting OpenAI, Anthropic, Google, and Together AI APIs; automated scoring, RCI computation, and variant analysis; and visualization tools generating tier comparison charts, cognitive radar profiles, and RCI-accuracy scatter plots.

## Preliminary Observations

Initial testing reveals a consistent **accuracy gradient** across tiers (T1 > T2 > T3), confirming that higher-order ToM is genuinely more challenging. The gap between T2 and T3 is particularly diagnostic — models that maintain accuracy across this boundary demonstrate more robust social reasoning capabilities.

Variant analysis shows that role-swapped foils produce the largest accuracy drops in models that rely on character-position heuristics, while distractor injection disproportionately affects models with weaker belief-isolation capabilities.

## Conclusion

MindRead++ provides a rigorous, multi-dimensional evaluation of social cognition in language models. By combining tiered complexity, anti-memorization controls, and reasoning quality metrics, it offers a more discriminating assessment of genuine Theory of Mind capabilities than existing benchmarks. The complete dataset, evaluation tools, and results are publicly available for the research community.
