# SafeMode: Explainable, Multi-Timescale Behavioral Detection Research Prototype

[![Platform](https://img.shields.io/badge/Platform-Windows%2011%20AMD64-blue.svg)](#)
[![Python](https://img.shields.io/badge/Python-3.14-green.svg)](#)
[![Version](https://img.shields.io/badge/Detector%20Version-SM--AY26--FINAL--v1-orange.svg)](#)
[![Tests](https://img.shields.io/badge/Tests-35%20Passed-brightgreen.svg)](#)
[![Security Gates](https://img.shields.io/badge/Security%20Gates-S1--S14%20PASS-success.svg)](#)

SafeMode is an academic research prototype developed for AY2026-27 investigating explainable, multi-timescale ransomware behavioral detection on Windows. It combines filesystem deception signals with temporal file/process behavioral context to evaluate resilience against controlled temporal dilation and decoy-avoidance strategies without kernel drivers or machine learning.

> **Research Integrity Notice:** SafeMode operates exclusively within an isolated laboratory environment using controlled synthetic workloads. It does not contain or detonate real ransomware, does not encrypt personal files, and makes no claim of commercial readiness, production deployment, or zero-day malware efficacy.

---

## 1. Research Question & Contribution Framing

### Research Question
*Can a lightweight, explainable combination of deception signals and temporal file/process behavioral context detect ransomware-like activity while remaining resilient to controlled temporal dilation and decoy-avoidance strategies, while maintaining acceptable endpoint resource overhead?*

### Academic Contribution Framing
A deterministic, rule-explainable behavioral detection framework featuring:
1. **Multi-Timescale Campaign Memory:** Retains sub-threshold evidence across spaced bursts with mathematical exponential decay, countering temporal dilation (slow/intermittent workloads).
2. **Context-Aware Behavioral Correlation:** Distinguishes structural file transformations (extension modifications, file deletions) from purely organizational renames and additive file copying.
3. **Fail-Safe Containment Architecture:** Strict process registry verification preventing arbitrary process control or out-of-boundary containment actions.
4. **Reproducible Experimental Instrumentation:** Full empirical pipeline tracking raw filesystem events, structured decisions, resource telemetry, and derived metrics.

---

## 2. System Architecture

SafeMode processes Windows file-system activity through a sequence of detection, correlation, and safety stages. The design separates short-term event observation from longer-term campaign memory so that related activity can still be correlated when it occurs in separated bursts.

### Processing Flow

```text
Windows File-System Activity
            |
            v
1. Event Collection
   Watchdog captures file-system events
            |
            v
2. Temporal Event Buffer
   Maintains recent events within a configurable
   short-term observation window
            |
            v
3. Signal Extraction
   Converts raw events into behavioral signals
   such as decoy interaction, rapid transformation,
   rename, delete, and multi-file activity
            |
            v
4. Campaign Memory
   Retains relevant evidence across longer periods
   using evidence deduplication, exponential decay,
   and hysteresis
            |
            v
5. Correlation Engine
   Combines current and historical evidence and
   produces an explainable detection decision
            |
            v
6. Response Manager
   Applies safety gates before any containment action
   and records the resulting response decision
            |
            v
Decision + Structured Audit Evidence
```

### Main Components

| Component                 | Purpose                                                                             |
| ------------------------- | ----------------------------------------------------------------------------------- |
| **Event Collection**      | Captures file-system activity generated inside the isolated laboratory              |
| **Temporal Event Buffer** | Maintains recent events for short-window behavioral analysis                        |
| **Signal Extraction**     | Converts raw file activity into security-relevant behavioral signals                |
| **Campaign Memory**       | Preserves relevant evidence across separated activity bursts                        |
| **Correlation Engine**    | Combines signals and campaign history to generate explainable risk decisions        |
| **Response Manager**      | Enforces process and laboratory safety controls before a response action            |
| **Telemetry**             | Records CPU, memory, process, and execution measurements                            |
| **Structured Storage**    | Preserves events, decisions, manifests, and experiment outcomes for reproducibility |

### Detection and Response Model

SafeMode uses two detector modes during experimental evaluation:

* **SHORT_WINDOW_BASELINE** — evaluates behavior using the short-term observation window.
* **STATEFUL_MULTI_TIMESCALE** — additionally retains relevant historical evidence through campaign memory.

The response layer is deliberately fail-safe. A containment action must pass laboratory-boundary, process-identity, executable-identity, and workload-registration checks before an actual process-control operation is permitted.

The current prototype is deterministic and rule-explainable. It does not use machine-learning inference or require a training dataset.

---

## 3. Experimental Reproducibility Workflow

To reproduce the complete experimental evaluation from scratch:

### Prerequisites
- Python 3.10+ (tested on Python 3.14.6 AMD64)
- Windows 10/11 environment with active Microsoft Defender

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Initialize Lab Environment
```bash
python -m app lab init
```
*Creates 10 decoy canary files inside `lab/decoys` and establishes the isolated directory structure.*

### Step 3: Run Full Test Suite & Security Gates
```bash
pytest
```
*Executes all 35 tests, including S1-S14 security validation gates, metric invariants, and result consistency checks.*

### Step 4: Execute Benchmark Evaluation Matrix
```bash
python -m app experiment run
```
*Executes 22 paired experiment runs (11 scenarios * 2 detector modes) tracking telemetry, manifests, and resource usage.*

### Step 5: Aggregate Results & Generate Visualizations
```bash
python -m app results aggregate
python -m app results report
```
*Processes raw outcome manifests into CSV summaries (`experiments.csv`, `metrics.csv`, `scenario_summary.csv`) and generates 5 research charts in `data/figures/`.*

### Step 6: Verify Consistency Programmatically
```bash
python scripts/validate_results_consistency.py
```
*Validates 1:1 mathematical and empirical correspondence across raw JSONL traces, outcome JSON files, CSV tables, and summary statistics.*

---

## 4. Key Empirical Findings (`SM-AY26-FINAL-v1`)

| Metric Category | Short-Window Baseline (5s) | Stateful Multi-Timescale | Research Insight |
| :--- | :---: | :---: | :--- |
| **Attack Detection Rate** | 0.0% (0/6) | **100.0% (6/6)** | Stateful memory retains evidence across dilated bursts |
| **Synthetic Evasion Rate** | 100.0% (6/6) | **0.0% (0/6)** | Spaced/intermittent tactics defeated by state retention |
| **Benign False Positive Rate** | **0.0% (0/5)** | **0.0% (0/5)** | Contextual rules isolate benign copying and photo renames |
| **Mean Detection Latency** | N/A (Evaded) | **2.20 seconds** | Rapid escalation upon qualifying multi-file behavior |
| **Mean Process RSS Memory** | 71.22 MB | 72.24 MB | Minimal memory divergence between modes |
| **Mean CPU Utilization** | 38.80% | 33.56% | Single-core burst processing overhead |

*Full evaluation tables, traces, and latency graphs are documented in [`docs/research/final_results.md`](docs/research/final_results.md).*

---

## 5. Security & Safety Gates

SafeMode incorporates 14 automated security verification gates (`S1` through `S14`):
- **S1-S2:** Strict lab boundary canonicalization and workload whitelisting.
- **S3-S5:** Containment restricted to registered lab subprocesses; identity & executable verification.
- **S6-S8:** Prevention of out-of-boundary file modification, path traversal (`..`), or external cleanup.
- **S9:** Disallowance of arbitrary shell command syntax (`shell=False` strictly enforced).
- **S10-S11:** Creation time validation (>2.0s drift rejected) and PID reuse lifecycle protection.
- **S12:** Non-interfering coexistence with active Microsoft Defender Antivirus.
- **S13-S14:** Workload run UUID isolation and fail-safe configuration defaults (`lab_mode=False`).

*Detailed test logs and audit evidence are in [`docs/security/final_security_validation.md`](docs/security/final_security_validation.md).*

---

## 6. Repository Layout

The repository is separated into detection code, safety controls, experiment workloads, evidence, validation, and research documentation.

```text
SafeMode/
|
+-- app/
|   Core SafeMode application
|
|   +-- correlation/       Event buffering and campaign memory
|   +-- detection/         Behavioral signal extraction and correlation
|   +-- experiment/        Experiment execution and metric processing
|   +-- models/            Event and decision data structures
|   +-- response/          Safety-gated response handling
|   +-- storage/           Structured event and decision logging
|   +-- telemetry/         Process context and resource monitoring
|   +-- utils/             Path and security validation helpers
|   +-- workloads/         Controlled benign and adversarial workloads
|   +-- config.py          Central detector configuration
|   +-- __main__.py        Command-line interface
|
+-- lab/
|   Controlled SafeMode laboratory environment
|
|   +-- decoys/            Synthetic canary files
|   +-- protected/         Protected laboratory content
|   +-- runs/              Run-specific laboratory data
|   +-- workloads/         Generated workload data
|
+-- data/
|   Experimental evidence and generated research outputs
|
|   +-- events/            Raw event and decision traces
|   +-- experiments/       Experiment manifests and outcome records
|   +-- resources/         CPU and memory telemetry
|   +-- results/           Validated CSV result tables
|   +-- figures/           Research charts
|   +-- archive_prompt4/   Preserved development/provenance records
|
+-- docs/
|   Project and research documentation
|
|   +-- research/          Results, scope, methodology, limitations
|   +-- security/          Security validation and code-audit records
|
+-- scripts/
|   Validation and analysis utilities
|
|   +-- validate_results_consistency.py
|
+-- tests/
|   Automated tests covering functionality and security gates
|
+-- requirements.txt
|   Python dependency specification
|
+-- README.md
    Project description and reproducibility instructions
```

### Useful Locations During Evaluation

| Need                                | Location                                  |
| ----------------------------------- | ----------------------------------------- |
| Understand the detector             | `app/`                                    |
| Run controlled workloads            | `app/workloads/`                          |
| Inspect raw evidence                | `data/events/` and `data/experiments/`    |
| Review research results             | `data/results/` and `docs/research/`      |
| Review security verification        | `tests/` and `docs/security/`             |
| Reproduce result consistency checks | `scripts/validate_results_consistency.py` |

This structure keeps **implementation**, **experimental evidence**, and **validation evidence** separate, making the prototype easier to inspect and reproduce.
