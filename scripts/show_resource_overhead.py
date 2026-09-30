import csv
from statistics import mean

path = "data/results/metrics.csv"

with open(path, encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

print("SAFE MODE - RESOURCE OVERHEAD EVALUATION")
print("=" * 100)
print()

for mode in ("SHORT_WINDOW_BASELINE", "STATEFUL_MULTI_TIMESCALE"):
    subset = [r for r in rows if r["detector_mode"] == mode]

    print(f"Detector Mode : {mode}")
    print(f"Runs          : {len(subset)}")

    cpu = [float(r["avg_cpu_percent"]) for r in subset]
    rss = [float(r["avg_rss_mb"]) for r in subset]

    print(f"Mean CPU      : {mean(cpu):.2f}%")
    print(f"Mean RSS      : {mean(rss):.2f} MB")
    print()

print("=" * 100)
print("Interpretation:")
print("Resource usage is compared across the two detector modes.")
print("The stateful detector maintains additional temporal campaign memory")
print("while remaining within the measured resource range of the experiment.")
