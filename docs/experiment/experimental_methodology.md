# SafeMode Experimental Methodology

## 1. Overview & Research Question
This document describes the experimental protocol designed to evaluate the SafeMode behavioral detection prototype. The primary objective is to evaluate:

> "Can a lightweight and explainable combination of deception signals and temporal file/process behavior detect ransomware-like activity while remaining resilient to simple temporal/evasion strategies and maintaining acceptable endpoint overhead?"

---

## 2. Experimental Detector Modes

We compare two explicit detector configurations:

* **Mode A — SHORT_WINDOW_BASELINE**: Evaluates evidence strictly within a fixed 5-second sliding window without long-term history or score accumulation across bursts.
* **Mode B — STATEFUL_MULTI_TIMESCALE**: Evaluates evidence over both short-term (5-second) windows and a long-term multi-timescale campaign memory (60-second horizon) with exponential evidence aging, signal accumulation, and escalation hysteresis.

---

## 3. Benchmark Workload Matrix

The benchmark matrix consists of 11 deterministic synthetic workloads executed as isolated child subprocesses:

### Attack Simulation Workloads (Test-Positive Scenarios)
1. **FAST_TRANSFORMATION**: Rapidly modifies and renames 10 victim files in a single burst.
2. **SLOW_TRANSFORMATION**: Modifies and renames files across 5 separated bursts (2 files/burst) with 8-second inter-burst sleep delays.
3. **INTERMITTENT_TRANSFORMATION**: Modifies and renames files across 4 separated bursts (3 files/burst) with 6-second inter-burst sleep delays.
4. **RENAME_HEAVY**: Renames 15 victim files in rapid succession without prior in-place modification.
5. **DECOY_AVOIDANCE**: Operates exclusively in a protected subdirectory, attempting to avoid decoy files.
6. **MIXED_BEHAVIOR**: Intermingles file deletion, modification, and rename operations.

### Benign Workloads (Test-Negative Scenarios)
7. **BENIGN_BULK_COPY**: Copies 10 documents from a source folder to a destination folder.
8. **BENIGN_COMPRESSION**: Compresses 5 text files into a single `.zip` archive.
9. **BENIGN_DOCUMENT_EDIT**: Edits a single document in multiple sequential save steps.
10. **BENIGN_RENAME_BATCH**: Renames 5 image files (e.g., `pic_X.jpg` -> `vacation_X.jpg`).
11. **BENIGN_BACKUP_STYLE**: Copies files to temporary `.tmp` extensions and renames them to target filenames.

---

## 4. Controlled Variables & Paired Run Normalization
To ensure valid scientific comparison:
- Paired runs between Mode A and Mode B use identical workload parameters (file counts, burst sizes, delays, seed=42).
- Execution takes place inside the controlled laboratory directory (`D:\Innovation_lab\lab`).
- Windows Defender real-time protection remains fully active throughout all runs.

---

## 5. Metrics & Derived Measurements
- **Detection Rate**: Percentage of attack simulation runs reaching `HIGH_CONFIDENCE` (Score >= 80).
- **False-Positive Rate**: Percentage of benign runs reaching `HIGH_CONFIDENCE`.
- **Synthetic Evasion Rate**: Percentage of attack simulation runs avoiding high confidence threshold.
- **Detection Latency**: Seconds elapsed from first event to high-confidence alert.
- **Detector CPU Overhead**: Average and peak CPU percentage of the SafeMode detector process.
- **Detector Memory Overhead**: Average and peak RSS memory (MB) of the SafeMode detector process.

---

## 6. Security & Containment Safety Constraints
All containment actions (DRY_RUN, SUSPEND, RESUME, TERMINATE) must satisfy 10 security verification checks before execution (LAB_MODE active, ProcessRegistry record, PID running, executable identity match, creation time match, active lifecycle status, known scenario, target inside lab dir, action permitted, audit trail logged).
