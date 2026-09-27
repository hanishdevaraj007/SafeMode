# SafeMode Research Prototype: Research Scope & Scientific Claims
**Document ID:** `DOC-RES-SCOPE-v1`  
**Prototype Version:** `SM-AY26-FINAL-v1`

---

## 1. Primary Research Question
Can a lightweight, explainable, multi-timescale ransomware-behavior detection prototype that combines deception signals with temporal file/process context evaluate and demonstrate resilience to controlled temporal dilation and decoy-avoidance behaviors?

---

## 2. Definitive Scope Categorization

To maintain strict scientific honesty and avoid over-claiming, all statements regarding SafeMode are categorized into one of three explicit tiers:

### Tier 1: Demonstrated in the Prototype (Implementation Proven)
*Features and behaviors directly verified in the codebase and regression test suite:*
- **Multi-Signal Behavioral Extraction:** Deterministic identification of rapid modification bursts, suspicious extension renames, organizational renames, file deletions, repeated modifications, and decoy interactions.
- **Explainable Multi-Timescale Campaign Memory:** Stateful retention of behavioral evidence with bounded risk scoring (`[0.0, 100.0]`), unique evidence accounting, exponential decay (`0.5/s`), and escalation/de-escalation hysteresis.
- **Fail-Safe Containment Architecture:** Strict gatekeeping requiring `LAB_MODE=True`, internal `ProcessRegistry` validation, creation timestamp matching, executable path matching, and safe defaults (`DRY_RUN`, `lab_mode=False`).
- **Path Traversal & Boundary Hardening:** Reusable canonical validation (`validate_safe_lab_path`) enforcing containment within the configured lab directory and rejecting parent traversal (`..`), drive roots, or external absolute paths.
- **Reproducible Evaluation Framework:** Standardized experiment runner generating structured JSON manifests, JSONL event/decision traces, background resource telemetry, and validated CSV tables.

### Tier 2: Experimentally Observed (Empirically Measured)
*Empirical facts derived from the 22-run benchmark evaluation (`SM-AY26-FINAL-v1`):*
- **Temporal Evasion Countermeasure:** The Short-Window Baseline detector failed against all 6 attack simulations (0/6 detections, 100% synthetic evasion rate), because temporal dilation (8s pauses in `SLOW_TRANSFORMATION`, 4–6s delays in `INTERMITTENT_TRANSFORMATION`) evicted evidence from the 5-second sliding window before reaching the escalation threshold (`max_score <= 75.0`). In contrast, the Stateful Multi-Timescale detector achieved 100% detection (6/6 detections, 0% synthetic evasion) with an average detection latency of `2.20s`.
- **Benign Activity Discrimination:** Across 5 distinct benign workloads (`BENIGN_BULK_COPY`, `BENIGN_COMPRESSION`, `BENIGN_DOCUMENT_EDIT`, `BENIGN_RENAME_BATCH`, `BENIGN_BACKUP_STYLE`), the stateful detector produced **zero false positives** (0/5 false alarms, FP Rate = 0.0%). Benign scores peaked at `72.7` for intensive single-file document editing and `15.0` for bulk copying, remaining strictly below the `80.0` escalation threshold.
- **Bounded Resource Footprint:** Detector memory consumption remained virtually flat across all workloads (`71.22 MB` average baseline RSS vs `72.24 MB` average stateful RSS). Single-core CPU utilization averaged `38.80%` for baseline and `33.56%` for stateful runs during active burst processing.
- **Defender Coexistence:** Throughout all 22 controlled synthetic runs, Microsoft Defender Antivirus remained active with real-time protection enabled, and no interference or suppression with SafeMode telemetry was observed.

### Tier 3: Not Yet Established (Explicit Non-Claims)
*Capabilities outside the current research scope and explicitly NOT claimed:*
- **Real-World Ransomware Generalization:** Effectiveness against live, wild, or zero-day ransomware samples is unproven.
- **Commercial Product Readiness:** The prototype is not an enterprise EDR, SaaS agent, or commercial endpoint protection suite.
- **Kernel-Level Causality:** In-kernel process attribution without ETW or minifilter drivers is not established.
- **Large-Scale Endpoint Fleet Performance:** Behavior across thousands of production workstations or diverse non-laboratory user workflows is untested.
- **Zero False-Alarm Guarantee:** An absolute zero false-positive rate across all potential enterprise software (e.g. compilers, video transcoders) is not guaranteed.
