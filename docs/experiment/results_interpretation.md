# SafeMode Results Interpretation Guide

This document clarifies the scientific distinction between measured facts, derived metrics, observations, hypotheses, and research conclusions to prevent over-interpretation of experimental results.

---

## Terminology & Scientific Distinctions

### 1. Measured Result
An empirical value recorded directly during execution by system instrumentation.
* *Example*: "In Run `run-101`, the detector process CPU averaged 0.45% and peak RSS memory was 34.5 MB."

### 2. Derived Metric
A calculated statistical quantity computed from raw measured results across runs.
* *Example*: "Detection Rate for `SLOW_TRANSFORMATION` under Stateful Mode was 100% (1/1), compared to 0% (0/1) under Baseline Mode."

### 3. Observation
An empirical pattern identified when comparing derived metrics across experimental conditions.
* *Example*: "The Short-Window Baseline detector allowed `SLOW_TRANSFORMATION` to evade high-confidence alerts because inter-burst sleep delays exceeded the 5-second evaluation window, resetting the short-term buffer before threshold accumulation."

### 4. Hypothesis
A proposed explanation or prediction subject to empirical verification.
* *Example*: "Stateful multi-timescale memory with score decay prevents low-rate temporal evasion while keeping false positives at zero for benign bulk copies."

### 5. Limitation
A boundary condition of the experiment that restricts the generalizability of results.
* *Example*: "Workloads are synthetic simulations of file modification and rename patterns executed in user-space without kernel minifilter drivers or real malware payloads."

### 6. Conclusion
A scientific claim strictly supported by empirical data collected under the controlled experimental setup.
* *Permitted Statement*: "Under the tested synthetic workload set, the stateful multi-timescale detector successfully detected slow and intermittent transformations that evaded the short-window baseline detector."
* *Prohibited Statement*: "SafeMode defeats real-world ransomware and replaces commercial EDR products."
