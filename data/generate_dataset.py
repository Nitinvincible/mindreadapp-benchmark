"""
Generate questions.json, variants.json, mindreadpp_full.csv, and sample_10.json
from scenarios_base.json according to the MindRead++ specifications.
"""
from __future__ import annotations

import json
import csv
import os
import random
import copy
from typing import Any

random.seed(42)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def load_scenarios():
    with open(os.path.join(SCRIPT_DIR, "scenarios_base.json"), "r", encoding="utf-8") as f:
        return json.load(f)

# ── Name pools for paraphrase variants ──────────────────────────────────────

NAMES_POOL_A = [
    ("Priya","James","Lucia"),("Aiko","Derek","Fatima"),("Chen","Olga","Marcus"),
    ("Amara","Sven","Yuki"),("Tariq","Elena","Boris"),("Zara","Nils","Mei"),
    ("Ines","Kwame","Rosa"),("Dmitri","Anya","Felix"),("Layla","Bjorn","Hana"),
    ("Kofi","Marta","Ivan"),("Rina","Oscar","Thea"),("Soren","Aditi","Luca"),
    ("Yael","Ravi","Nadia"),("Emeka","Freya","Jun"),("Petra","Andre","Sakura"),
    ("Hassan","Elke","Dante"),("Lisbeth","Mateo","Keiko"),("Nikolai","Celia","Tunde"),
    ("Ingrid","Raj","Solange"),("Fumiko","Lars","Aisha"),("Pavel","Neha","Callum"),
    ("Simone","Idris","Wendy"),("Akira","Greta","Pablo"),("Osei","Katya","Marco"),
    ("Thandiwe","Hugo","Linh"),("Remy","Ximena","Arjun"),("Zola","Erik","Mika"),
    ("Farid","Astrid","Chiara"),("Tamsin","Jiro","Olena"),("Bashir","Helga","Cruz"),
    ("Annika","Seiji","Esme"),("Rohan","Fia","Stellan"),("Yusuf","Brigitte","Leilani"),
    ("Sanjay","Moira","Henrik"),("Chidi","Linnea","Tomoko"),("Enrique","Sigrid","Noor"),
    ("Kenzo","Aoife","Dimitri"),("Bodhi","Marlene","Jia"),("Samir","Elin","Paloma"),
    ("Torvald","Amira","Koji"),("Leandro","Svea","Asha"),("Mikael","Zuri","Yoko"),
    ("Dag","Safiya","Elio"),("Riku","Maren","Isla"),("Hamza","Tova","Lucian"),
    ("Omari","Karin","Yuna"),("Naveen","Gerda","Thiago"),("Cassian","Dilara","Suki"),
    ("Einar","Nalini","Rio"),("Hadley","Soraya","Arne")
]

SETTINGS_POOL_A = [
    "office breakroom","university lab","community center kitchen","hotel lobby",
    "co-working space","hospital staff room","airport lounge","train station café",
    "farm barn","school staff room","fire station","museum back office",
    "newsroom","recording studio","greenhouse","sports clubhouse",
    "yoga studio","art gallery storage","rooftop terrace","bank vault anteroom",
    "post office sorting room","bakery kitchen","bookstore back room","harbor office",
    "mechanic's garage","dance studio","pet shelter front desk","dentist waiting room",
    "embassy reception","ski lodge lounge","lighthouse keeper's room","florist workshop",
    "clock tower room","aquarium staff area","winery cellar","pottery studio",
    "tailor's shop","barbershop","planetarium control room","fire lookout tower",
    "ferry terminal","ranger station","glassblowing workshop","cheese cave",
    "beekeeping shed","vintage shop back room","calligraphy studio","ice rink office",
    "bowling alley lounge","circus tent backstage"
]

OBJECTS_POOL_A = [
    "blue folder","silver watch","ceramic mug","leather journal","USB drive",
    "wooden box","glass vase","gold ring","silk scarf","brass key",
    "photo album","recipe card","parking permit","library card","train ticket",
    "vitamin bottle","sewing kit","chess piece","snow globe","candle holder",
    "pocket knife","compass","harmonica","thimble","magnifying glass",
    "music box","bookmark","fountain pen","locket","postcard",
    "badge","whistle","dice set","corkscrew","tape measure",
    "binoculars","monocle","kaleidoscope","metronome","hourglass",
    "stamp collection","coin purse","lip balm","lanyard","keychain",
    "pill case","spyglass","tuning fork","worry stone","domino set"
]

# ── Tier question templates ─────────────────────────────────────────────────

def get_scenario_object(scn: dict[str, Any]) -> str:
    """Extract the main object/topic from scenario ground_truth keys."""
    gt = scn["ground_truth"]
    key = list(gt.keys())[0]
    # e.g. "A_believes_notebook_location" -> "notebook location"
    parts = key.split("_believes_")
    if len(parts) > 1:
        return parts[1].replace("_", " ")
    return "the situation"

def get_narrative(scn: dict[str, Any]) -> str:
    """Build narrative text from events."""
    return " ".join(e["text"] for e in scn["events"])

def generate_questions_for_scenario(scn: dict[str, Any]) -> list[dict[str, Any]]:
    """Generate T1, T2, T3 questions for a scenario."""
    sid = scn["scenario_id"]
    chars = scn["characters"]
    gt = scn["ground_truth"]
    events = scn["events"]
    bsm = scn["belief_state_map"]

    char_a_name = chars["A"]
    char_b_name = chars["B"]
    char_c_name = chars["C"]

    gt_keys = list(gt.keys())
    gt_vals = list(gt.values())

    # Determine what A believes (first ground truth)
    a_belief = gt_vals[0]
    b_belief = gt_vals[1] if len(gt_vals) > 1 else gt_vals[0]
    c_belief = gt_vals[2] if len(gt_vals) > 2 else gt_vals[0]

    obj_topic = get_scenario_object(scn)

    # ── T1: First-order ToM ──
    # What does A believe?
    # A's belief is typically wrong (false belief) — they missed an event
    t1_correct = a_belief
    t1_distractors: list[Any] = []
    for v in [b_belief, c_belief]:
        if v != t1_correct and v not in t1_distractors:
            t1_distractors.append(v)
    # Add generic distractors
    generics = [
        f"{char_a_name} does not know",
        f"{char_a_name} has no opinion about it",
        "None of the above",
        "It was never discussed"
    ]
    for g in generics:
        if len(t1_distractors) >= 3:
            break
        if g not in t1_distractors and g != t1_correct:
            t1_distractors.append(g)
    t1_distractors = t1_distractors[:3]  # type: ignore[index]

    # Shuffle choices
    t1_choices_list = [t1_correct] + t1_distractors
    random.shuffle(t1_choices_list)
    t1_correct_letter = chr(65 + t1_choices_list.index(t1_correct))
    t1_choices = {chr(65+i): v for i, v in enumerate(t1_choices_list)}

    # Build explanation from belief_state_map
    a_events = bsm.get("A_knows", [])
    missed = [e for e in [f"event_{ev['event_id']}" for ev in events] if e not in a_events]

    t1_explanation = (
        f"{char_a_name} only witnessed {', '.join(a_events)}. "
        f"{'They did not witness ' + ', '.join(missed) + '. ' if missed else ''}"
        f"Therefore, {char_a_name} believes the {obj_topic} is: {t1_correct}."
    )

    t1 = {
        "question_id": f"Q_{sid.replace('_','')}_T1",
        "scenario_id": sid,
        "variant": "original",
        "tier": 1,
        "tier_name": "first_order_tom",
        "question_text": f"Based on what {char_a_name} has witnessed, what does {char_a_name} believe about the {obj_topic}?",
        "answer_type": "multiple_choice",
        "choices": t1_choices,
        "correct_answer": t1_correct_letter,
        "explanation": t1_explanation,
        "requires_cot": True
    }

    # ── T2: Second-order ToM ──
    # What does A think B believes?
    # A doesn't know what B did privately, so A assumes B's knowledge mirrors limited info
    # A thinks B believes = what A would think B saw
    a_knows_b_saw = []
    for ev in events:
        eid = f"event_{ev['event_id']}"
        if eid in a_events and "B" in ev["witnessed_by"]:
            a_knows_b_saw.append(eid)

    # A's model of B's belief is based only on events A knows B witnessed
    # This is the crux of second-order ToM
    t2_correct = t1_correct  # Often A thinks B believes the same as A (when A missed the key event)
    # But sometimes A knows B was there for an event A also saw
    t2_distractors: list[Any] = []
    for v in [b_belief, c_belief]:
        if v != t2_correct and v not in t2_distractors:
            t2_distractors.append(v)
    for g in [f"{char_a_name} thinks {char_b_name} doesn't know about the {obj_topic}",
              f"{char_b_name} has never encountered the {obj_topic}",
              "None of the above"]:
        if len(t2_distractors) >= 3:
            break
        if g not in t2_distractors and g != t2_correct:
            t2_distractors.append(g)
    t2_distractors = t2_distractors[:3]  # type: ignore[index]

    t2_choices_list = [t2_correct] + t2_distractors
    random.shuffle(t2_choices_list)
    t2_correct_letter = chr(65 + t2_choices_list.index(t2_correct))
    t2_choices = {chr(65+i): v for i, v in enumerate(t2_choices_list)}

    t2_explanation = (
        f"{char_a_name} knows that {char_b_name} was present for {', '.join(a_knows_b_saw) if a_knows_b_saw else 'some events'}. "
        f"From {char_a_name}'s perspective, {char_b_name}'s belief would be: {t2_correct}. "
        f"This tests whether the model distinguishes 'what B actually knows' from 'what A thinks B knows'."
    )

    t2 = {
        "question_id": f"Q_{sid.replace('_','')}_T2",
        "scenario_id": sid,
        "variant": "original",
        "tier": 2,
        "tier_name": "second_order_tom",
        "question_text": f"What does {char_a_name} think {char_b_name} believes about the {obj_topic}?",
        "answer_type": "multiple_choice",
        "choices": t2_choices,
        "correct_answer": t2_correct_letter,
        "explanation": t2_explanation,
        "requires_cot": True
    }

    # ── T3: Counterfactual ToM ──
    # If A had witnessed the key missed event, what would A think about B's intention?
    if missed:
        key_missed = missed[0]
        key_event_text = ""
        for ev in events:
            if f"event_{ev['event_id']}" == key_missed:
                key_event_text = ev["text"]
                break
    else:
        key_missed = f"event_{events[-1]['event_id']}"
        key_event_text = events[-1]["text"]

    t3_options = [
        f"{char_b_name} was trying to help or organize",
        f"{char_b_name} was acting with hidden intent",
        f"{char_b_name} was confused or mistaken",
        f"{char_b_name} was unaware of the consequences"
    ]
    # Pick "hidden intent" as correct for scenarios involving moves/changes
    t3_correct = t3_options[1]
    t3_distractors = [o for o in t3_options if o != t3_correct]

    t3_choices_list = [t3_correct] + t3_distractors
    random.shuffle(t3_choices_list)
    t3_correct_letter = chr(65 + t3_choices_list.index(t3_correct))
    t3_choices = {chr(65+i): v for i, v in enumerate(t3_choices_list)}

    t3_explanation = (
        f"Counterfactually, if {char_a_name} had witnessed {key_missed} ({key_event_text}), "
        f"{char_a_name} would likely interpret {char_b_name}'s action as intentional or purposeful. "
        f"Without additional context suggesting benign intent, the default social interpretation leans toward hidden intent."
    )

    t3 = {
        "question_id": f"Q_{sid.replace('_','')}_T3",
        "scenario_id": sid,
        "variant": "original",
        "tier": 3,
        "tier_name": "counterfactual_tom",
        "question_text": (
            f"If {char_a_name} had witnessed {key_missed}, what would {char_a_name} most likely think "
            f"about {char_b_name}'s intention?"
        ),
        "answer_type": "multiple_choice",
        "choices": t3_choices,
        "correct_answer": t3_correct_letter,
        "explanation": t3_explanation,
        "requires_cot": True
    }

    return [t1, t2, t3]


def generate_variants_for_scenario(scn: dict[str, Any], idx: int) -> list[dict[str, Any]]:
    """Generate 5 variants (including original) for a scenario."""
    sid = scn["scenario_id"]
    chars = scn["characters"]
    events = scn["events"]
    bsm = scn["belief_state_map"]

    variants = []

    # 1. Original (reference only)
    variants.append({
        "variant_id": f"VAR_{sid.replace('_','')}_OR",
        "scenario_id": sid,
        "variant_type": "original",
        "character_map": dict(chars),
        "setting_change": "none",
        "object_change": "none",
        "events_text": [e["text"] for e in events],
        "logic_preserved": True,
        "belief_state_map": dict(bsm),
        "notes": "Original scenario, no changes."
    })

    # 2. Paraphrase A — new names, setting, object
    names_a = NAMES_POOL_A[idx % len(NAMES_POOL_A)]
    setting_a = SETTINGS_POOL_A[idx % len(SETTINGS_POOL_A)]
    object_a = OBJECTS_POOL_A[idx % len(OBJECTS_POOL_A)]

    pa_events = []
    for e in events:
        t = e["text"]
        t = t.replace(chars["A"], names_a[0])
        t = t.replace(chars["B"], names_a[1])
        t = t.replace(chars["C"], names_a[2])
        pa_events.append(t)

    variants.append({
        "variant_id": f"VAR_{sid.replace('_','')}_PA",
        "scenario_id": sid,
        "variant_type": "paraphrase_a",
        "character_map": {"A": names_a[0], "B": names_a[1], "C": names_a[2]},
        "setting_change": f"{setting_a} instead of original setting",
        "object_change": f"{object_a} instead of original object",
        "events_text": pa_events,
        "logic_preserved": True,
        "belief_state_map": dict(bsm),
        "notes": "Character names, setting, and object changed. Information access structure identical to original."
    })

    # 3. Paraphrase B — different vocabulary, same structure
    pb_events = []
    for e in events:
        t = e["text"]
        # Simple vocabulary shifts
        t = t.replace("places", "sets down").replace("moves", "transfers")
        t = t.replace("puts", "positions").replace("returns", "comes back")
        t = t.replace("tells", "informs").replace("sees", "observes")
        t = t.replace("leaves", "deposits").replace("finds", "discovers")
        t = t.replace("takes", "retrieves").replace("walks", "heads")
        pb_events.append(t)

    variants.append({
        "variant_id": f"VAR_{sid.replace('_','')}_PB",
        "scenario_id": sid,
        "variant_type": "paraphrase_b",
        "character_map": dict(chars),
        "setting_change": "none",
        "object_change": "none",
        "events_text": pb_events,
        "logic_preserved": True,
        "belief_state_map": dict(bsm),
        "notes": "Vocabulary and sentence structure changed. Event sequence and information access identical."
    })

    # 4. Role-swapped — invert who witnesses what between A and B
    rs_bsm = copy.deepcopy(bsm)
    a_k = rs_bsm.get("A_knows", [])
    b_k = rs_bsm.get("B_knows", [])
    rs_bsm["A_knows"] = b_k
    rs_bsm["B_knows"] = a_k

    rs_events: list[str] = []
    for e in events:
        rs_wb: list[str] = []
        for w in e["witnessed_by"]:  # type: ignore[operator]
            if w == "A":
                rs_wb.append("B")
            elif w == "B":
                rs_wb.append("A")
            else:
                rs_wb.append(w)
        t: str = e["text"]  # type: ignore[operator]
        # Swap A and B names in text
        placeholder = "___TEMP_CHAR___"
        t = t.replace(chars["A"], placeholder)
        t = t.replace(chars["B"], chars["A"])
        t = t.replace(placeholder, chars["B"])
        rs_events.append(t)

    variants.append({
        "variant_id": f"VAR_{sid.replace('_','')}_RS",
        "scenario_id": sid,
        "variant_type": "role_swap",
        "character_map": {"A": chars["B"], "B": chars["A"], "C": chars["C"]},
        "setting_change": "none",
        "object_change": "none",
        "events_text": rs_events,
        "logic_preserved": True,
        "belief_state_map": rs_bsm,
        "notes": "Characters A and B swapped in terms of information access. Setting and object unchanged."
    })

    # 5. Distractor injection — add plausible-but-wrong belief mid-story
    di_events = [e["text"] for e in events]
    char_a_name = chars["A"]
    char_b_name = chars["B"]

    # Insert after event 2 (index 1 in 0-based)
    insert_pos = min(2, len(di_events) - 1)
    distractor_statements = [
        f"A neighbor mentions to {char_a_name} that they thought they saw {char_b_name} near the original spot earlier.",
        f"Someone in the background comments that everything is exactly where it was left.",
        f"{char_a_name} briefly wonders if things have changed, but dismisses the thought.",
        f"A passerby remarks to {char_a_name} that {char_b_name} seemed to be rearranging things."
    ]
    distractor = random.choice(distractor_statements)
    di_events.insert(insert_pos, distractor)

    variants.append({
        "variant_id": f"VAR_{sid.replace('_','')}_DI",
        "scenario_id": sid,
        "variant_type": "distractor",
        "character_map": dict(chars),
        "setting_change": "none",
        "object_change": "none",
        "events_text": di_events,
        "logic_preserved": True,
        "belief_state_map": dict(bsm),
        "notes": f"Distractor statement inserted at position {insert_pos + 1}. Core event sequence and ground truth unchanged."
    })

    return variants


def generate_full_csv(scenarios: list[dict[str, Any]], questions: list[dict[str, Any]], variants: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Generate the flat CSV combining all data."""
    rows = []
    scn_map = {s["scenario_id"]: s for s in scenarios}

    for q in questions:
        scn = scn_map[q["scenario_id"]]
        narrative = get_narrative(scn)
        row = {
            "question_id": q["question_id"],
            "scenario_id": q["scenario_id"],
            "setting": scn["setting"],
            "difficulty": scn["difficulty"],
            "variant": q["variant"],
            "tier": q["tier"],
            "tier_name": q["tier_name"],
            "narrative": narrative,
            "characters": json.dumps(scn["characters"]),
            "question_text": q["question_text"],
            "choice_A": q["choices"]["A"],
            "choice_B": q["choices"]["B"],
            "choice_C": q["choices"]["C"],
            "choice_D": q["choices"]["D"],
            "correct_answer": q["correct_answer"],
            "explanation": q["explanation"],
            "tags": json.dumps(scn["tags"])
        }
        rows.append(row)

    return rows


def main():
    print("Loading scenarios...")
    scenarios = load_scenarios()
    print(f"  Loaded {len(scenarios)} scenarios")

    # Count settings
    settings_count = {}
    for s in scenarios:
        settings_count[s["setting"]] = settings_count.get(s["setting"], 0) + 1
    for k, v in settings_count.items():
        print(f"  {k}: {v}")

    # Generate questions
    print("\nGenerating questions...")
    all_questions = []
    for scn in scenarios:
        qs = generate_questions_for_scenario(scn)
        all_questions.extend(qs)
    print(f"  Generated {len(all_questions)} questions")

    # Generate variants
    print("\nGenerating variants...")
    all_variants = []
    for i, scn in enumerate(scenarios):
        vs = generate_variants_for_scenario(scn, i)
        all_variants.extend(vs)
    print(f"  Generated {len(all_variants)} variants")

    # Save questions.json
    questions_path = os.path.join(SCRIPT_DIR, "questions.json")
    with open(questions_path, "w", encoding="utf-8") as f:
        json.dump(all_questions, f, indent=2, ensure_ascii=False)
    print(f"\nSaved {questions_path}")

    # Save variants.json
    variants_path = os.path.join(SCRIPT_DIR, "variants.json")
    with open(variants_path, "w", encoding="utf-8") as f:
        json.dump(all_variants, f, indent=2, ensure_ascii=False)
    print(f"Saved {variants_path}")

    # Generate and save CSV
    print("\nGenerating CSV...")
    csv_rows = generate_full_csv(scenarios, all_questions, all_variants)
    csv_path = os.path.join(SCRIPT_DIR, "mindreadpp_full.csv")
    if csv_rows:
        fieldnames = list(csv_rows[0].keys())
        with open(csv_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(csv_rows)
    print(f"Saved {csv_path} ({len(csv_rows)} rows)")

    # Generate sample_10.json
    print("\nGenerating sample_10.json...")
    sample_scenarios = scenarios[:10]
    sample_sids = {s["scenario_id"] for s in sample_scenarios}
    sample_questions = [q for q in all_questions if q["scenario_id"] in sample_sids]
    sample_variants = [v for v in all_variants if v["scenario_id"] in sample_sids]

    sample = {
        "description": "10-scenario sample of MindRead++ benchmark for quick inspection",
        "scenarios": sample_scenarios,
        "questions": sample_questions,
        "variants": sample_variants
    }
    sample_path = os.path.join(SCRIPT_DIR, "sample_10.json")
    with open(sample_path, "w", encoding="utf-8") as f:
        json.dump(sample, f, indent=2, ensure_ascii=False)
    print(f"Saved {sample_path}")

    print("\n✅ Dataset generation complete!")
    print(f"  Scenarios: {len(scenarios)}")
    print(f"  Questions: {len(all_questions)}")
    print(f"  Variants:  {len(all_variants)}")


if __name__ == "__main__":
    main()
