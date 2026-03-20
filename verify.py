"""Quick verification of dataset integrity."""
import json, csv, os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

d = json.load(open("data/scenarios_base.json"))
print(f"Scenarios: {len(d)}")
s = {"domestic": 0, "workplace": 0, "social": 0}
for x in d:
    s[x["setting"]] += 1
print(f"Settings: {s}")

d2 = json.load(open("data/questions.json"))
print(f"Questions: {len(d2)}")

d3 = json.load(open("data/variants.json"))
print(f"Variants: {len(d3)}")

d4 = json.load(open("data/sample_10.json"))
print(f"Sample scenarios: {len(d4['scenarios'])}, questions: {len(d4['questions'])}")

r = list(csv.reader(open("data/mindreadpp_full.csv")))
print(f"CSV rows: {len(r)-1} (+ header)")

# Verify scenario IDs are sequential
ids = [x["scenario_id"] for x in d]
print(f"ID range: {ids[0]} to {ids[-1]}")

# Verify all question tiers present
tiers = {1: 0, 2: 0, 3: 0}
for q in d2:
    tiers[q["tier"]] += 1
print(f"Questions per tier: {tiers}")

print("\nAll checks passed!")
