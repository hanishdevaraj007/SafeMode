# SafeMode Research Prototype: System & Research Limitations
**Document ID:** `DOC-RES-LIMITATIONS-v1`  
**Prototype Version:** `SM-AY26-FINAL-v1`

This document articulates the genuine scientific and architectural boundaries of the SafeMode research prototype. These limitations are structural scope constraints necessary for academic integrity and reproducibility.

---

### 1. Synthetic Workloads vs. Real Malware
All evaluation is conducted using deterministic, synthetic behavioral workloads within an isolated directory (`lab/`). No live ransomware samples, compiled malicious payloads, or destructive encryption algorithms are detonated. Consequently, evasion tactics relying on API hooking, memory injection, code obfuscation, or living-off-the-land binaries (LotL) are not modeled.

### 2. No Claim of Real-World Effectiveness
The prototype demonstrates detection of *specific behavioral patterns* (e.g., rapid bursts, spaced bursts, and decoy avoidance) under controlled laboratory conditions. It makes **no claim** of efficacy against zero-day ransomware or wild malware strains.

### 3. User-Space Filesystem Telemetry
Telemetry is collected entirely in user-space via Python `watchdog` (Windows `ReadDirectoryChangesW` API). This avoids kernel instability and blue screens but is subject to known Windows user-space telemetry limitations (e.g., potential event dropping during extreme I/O saturation and lack of pre-operation filtering).

### 4. Lack of Kernel-Level Event Causality
Because neither kernel minifilter drivers nor Event Tracing for Windows (ETW) are implemented, the filesystem notification stream does not inherently carry the causal process identifier (PID) of the modifying process.

### 5. Scope of Exact Process Attribution
Exact process attribution (`EXPERIMENT_EXACT`) is available **only** for SafeMode-managed synthetic subprocesses explicitly registered into the internal `ProcessRegistry`. All generic background monitoring operates strictly under `TEMPORAL_CONTEXT` (probabilistic snapshot of active processes during the temporal correlation window).

### 6. Host-Specific Resource Measurements
All CPU utilization and RSS memory footprints were recorded on a single host platform (Windows 11 AMD64, 8-core CPU, Python 3.14.6). Resource utilization figures represent prototype runtime behavior on this specific hardware and OS build, not generalized operational benchmarks.

### 7. Threshold and Configuration Dependence
Behavioral thresholds (such as the escalation threshold of `80.0`, de-escalation threshold of `40.0`, evidence decay rate of `0.5/s`, and burst counts) were empirically calibrated for the evaluated experimental suite. They are not mathematically proven to be optimal across arbitrary multi-tenant production environments.

### 8. Workload Diversity Boundaries
The experimental matrix comprises 11 distinct scenarios (6 attack simulations, 5 benign workloads). While covering primary temporal dilation and spatial avoidance dimensions, it does not represent the full spectrum of enterprise workflows (e.g., database transactions, IDE compilation, continuous integration builds, or hypervisor disk image I/O).

### 9. Absence of Large-Scale Endpoint Datasets
The prototype was evaluated within a local laboratory setup rather than across a fleet of production workstations or enterprise telemetry logs. Findings reflect controlled laboratory behavior, not large-scale field performance.

### 10. Laboratory Repetition Sample Sizes
The definitive benchmark suite utilized paired single and multi-repetition runs across all 11 scenarios and 2 detector modes (22 total runs). While sufficient to prove deterministic algorithmic correctness and invariant satisfaction, broader statistical variance across thousands of hours remains future work.

### 11. Potential Overlap with Intense Benign Activity
High-volume administrative tasks that combine rapid content rewriting with extension altering (e.g., batch transcoding of audio/video across formats, or destructive automated disk cleanup tools) could produce elevated risk scores if executed without registered process context. SafeMode relies on evidence decay and contextual signal correlation to mitigate this, but legitimate edge-case overlap remains possible.

### 12. Non-Production Prototype Status
SafeMode is an academic research prototype designed to explore explainable, multi-timescale temporal correlation and deception signal integration. It is **not** an enterprise Endpoint Detection and Response (EDR) product, SaaS platform, or production security agent.
