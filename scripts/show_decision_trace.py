import json

p = "data/events/c86a2d4c-9bf2-4738-a950-9fccd7f6ef9d_decisions.jsonl"

print("SAFE MODE - EXPLAINABLE DECISION TRACE")
print("=" * 110)

with open(p, encoding="utf-8") as f:
    for line in f:
        d = json.loads(line)

        timestamp = str(d.get("timestamp", ""))
        score = d.get("score", "")
        risk = d.get("risk_level", "")
        window = d.get("window_seconds", "")
        signals = d.get("signals", [])

        print()
        print(f"Time: {timestamp}")
        print(f"Risk: {risk}")
        print(f"Score: {score}")
        print(f"Window: {window}s")
        print("Signals:")

        for signal in signals:
            name = signal.get("name", "")
            count = signal.get("evidence_count", 0)
            print(f"  - {name}: {count} evidence events")

        print(f"Explanation: {d.get('explanation', '')}")

        pc = d.get("process_context", {})
        print(f"Process attribution exact match: {pc.get('exact_match')}")
        print(f"Attribution note: {pc.get('note', '')}")

        print("-" * 110)
