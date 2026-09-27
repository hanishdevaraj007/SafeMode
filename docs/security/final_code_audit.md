# SafeMode Final Codebase Security & Architectural Audit

**Document Version**: 1.0 (Phase 5 Final Audit)  
**Target Repository**: `D:\Innovation_lab`  
**Prototype**: SafeMode Research Prototype (AY2026–27)

---

## 1. Executive Summary

This audit assesses the functional, security, and scientific integrity of the SafeMode research prototype prior to final experimental evaluation. The audit verifies that:
1. The containment subsystem cannot target arbitrary host processes or system files.
2. The telemetry and correlation pipeline operates deterministically without unbounded state accumulation.
3. Path handling is strictly confined to the laboratory directory (`D:\Innovation_lab\lab`).
4. Windows Defender and host security features remain completely intact without bypasses or broad exclusions.

---

## 2. Component-by-Component Audit Matrix

| Component | Path | Core Purpose | Security-Sensitive Behavior | Potential Failure Modes | Audit Findings & Required Remediation |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Config** | `app/config.py` | Global configuration and paths | Path defaults, detection thresholds, response modes | Hard-coded host paths; unsafe defaults | **Pass with remediation**: Add reusable canonical path validator; change default `lab_mode` to `False` for fail-safe containment; increment detector version to `SM-AY26-FINAL-v1`. |
| **Logger** | `app/storage/logger.py` | JSONL telemetry and audit trail logging | Writing structured logs to disk | Unbounded file growth, path traversal in run IDs | **Pass**: All log writes use canonicalized paths in `data/`; run IDs validated as UUIDs. |
| **Decoy Manager** | `app/detection/decoys.py` | Deceptive bait file placement in lab | File creation/deletion in lab directory | Creating files outside lab; clobbering user files | **Pass**: Decoy directory strictly pinned to `config.decoy_dir` inside `lab/`. |
| **File Monitor** | `app/telemetry/monitor.py` | Watchdog directory event capture | Filesystem observation | Dropped events under burst load; watchdog thread exceptions | **Pass**: Queue-based buffering in `TemporalEventBuffer`; errors logged cleanly. |
| **Process Context** | `app/telemetry/process_context.py` | Approximate background process snapshot | Reading `psutil.process_iter()` | False claim of exact event-to-PID attribution | **Pass**: Clearly labeled `TEMPORAL_CONTEXT`, never claiming kernel minifilter attribution. |
| **Process Registry** | `app/telemetry/process_registry.py` | Exact experiment subprocess tracking | PID tracking, creation time, lifecycle status | PID reuse by unrelated host processes | **Pass**: Implements `validate_identity` verifying PID, creation timestamp, and binary path. |
| **Resource Monitor** | `app/telemetry/resource_monitor.py` | Sampling detector CPU and RAM | Calling `psutil.Process(detector_pid)` | High monitor overhead distorting measurements | **Pass**: Lightweight 0.5s sampling interval; tracks detector PID specifically, not whole system. |
| **Event Buffer** | `app/correlation/buffer.py` | 5.0-second sliding temporal window | In-memory event retention | Memory leaks from unbounded growth | **Pass**: Events pruned deterministically by timestamp (`event.timestamp < cutoff`). |
| **Signal Extractor** | `app/detection/signals.py` | Translating raw events into behavioral signals | Evaluating event sets against threshold rules | Re-extracting identical signals across polling cycles | **Remediation Needed**: Signal extractor outputs signals for all current buffer events, causing repeated addition if caller does not deduplicate evidence. |
| **Campaign Memory** | `app/correlation/state.py` | Stateful multi-timescale memory across bursts | Score accumulation, evidence aging, hysteresis | Unbounded score runaway (5,000+ scores); false positives on benign re-polling | **CRITICAL REMEDIATION**: State update lacks unique evidence tracking; identical signals re-accumulate every 100ms. Bounded 0–100 scale and evidence ID deduplication required. |
| **Correlation Engine** | `app/detection/correlation.py` | Mapping signals/state to decisions | Risk score calculation and classification | Disconnect between instantaneous score and final decision | **Remediation Needed**: Unify score scale to bounded 0–100; ensure `risk_level == "HIGH"` strictly matches `score >= 80`. |
| **Event Pipeline** | `app/correlation/pipeline.py` | Telemetry dispatcher and coordinator | Triggering evaluation and response | Polling rate mismatch with buffer window | **Pass with remediation**: Add evidence tracking between buffer evaluations. |
| **Response Actions** | `app/response/actions.py` | Automated containment (DRY_RUN, SUSPEND, RESUME, TERMINATE) | OS process suspension and termination via `psutil` | Accidental targeting of OS or user processes | **Pass**: 10 mandatory security verification checks enforced before any action. Never falls back to PID-only actions. |
| **Base Workload** | `app/workloads/base.py` | Common synthetic workload base class | Checking paths before file I/O | Path traversal escape (`..`) | **Remediation Needed**: Upgrade `check_safe_path` to use strict canonicalization and resolve symbolic links. |
| **Adversarial Workloads**| `app/workloads/adversarial.py` | Deterministic synthetic attacks (6 scenarios) | File creation, modification, renaming | Destruction of non-lab files; malware payload execution | **Pass**: Pure synthetic text files in `lab/workloads/`; no encryption keys or destructive routines. |
| **Benign Workloads** | `app/workloads/benign.py` | Deterministic benign operations (5 scenarios) | Bulk copy, compression, document editing | False positives triggered by aggressive burst rules | **Remediation Needed**: Ensure benign patterns (e.g. read/copy, zip archiving) do not trigger ransomware multi-file transformation signals. |
| **Workload Runner** | `app/workloads/runner.py` | Spawning isolated child subprocesses | Subprocess execution via `Popen` | Command injection; arbitrary code execution | **Pass**: Whitelisted scenario names only; argument arrays used; `shell=False`. |
| **Experiment Runner** | `app/experiment/runner.py` | Orchestrating benchmark evaluation runs | Launching workloads, monitoring, capturing metrics | Tight polling loop re-evaluating unchanged buffer events | **Remediation Needed**: Prevent 100ms polling from artificially inflating state scores. |
| **Aggregator** | `app/experiment/aggregator.py` | CSV synthesis and result validation | Calculating rates, writing CSVs | Inconsistent metric definitions (e.g. hiding benign FP rates) | **Remediation Needed**: Explicitly expose `false_positive_rate` alongside `detection_rate`; strictly validate all metrics. |
| **CLI** | `app/__main__.py` | User and automation command entry point | Argument parsing, dispatching | Unauthenticated command execution | **Pass**: Fixed subcommands (`lab`, `status`, `workload`, `experiment`, `results`, `containment`, `monitor`). |

---

## 3. Findings on Critical Anomalies

1. **Unbounded Risk Scores (~5,321 - 5,791)**:
   - **Root Cause**: `app/correlation/state.py` adds score increments (`+25`, `+20`, `+40`) for every signal passed to `update()`. In `app/experiment/runner.py`, `pipeline.evaluate()` was polled every 100ms. Because events stay in the 5-second `TemporalEventBuffer` for 50 polling cycles, the same events generated signals 50 times, multiplying the score by 50x per burst.
   - **Remediation**: 
     - Implement **Evidence Accounting**: Track processed `evidence_ids` (unique event IDs or `(signal_name, event_ids)` tuples). A signal can only add to campaign score once for any unique evidence set.
     - Enforce a **Bounded Risk Scale (0–100)**: Clamp all state scores mathematically to `[0.0, 100.0]`.

2. **Benign False Positives (Scores > 80 while Detection Rate = 0)**:
   - **Root Cause**: 
     - Same runaway accumulation bug: harmless benign file copies in the 5s window re-triggered `MULTI_FILE_TRANSFORMATION` multiple times across polling cycles.
     - Aggregator anomaly: `aggregator.py` set `det_rate = 0.0` for all benign scenarios regardless of whether `high_confidence_reached` was True, masking the false positives in the summary table while reporting max score > 80.
   - **Remediation**:
     - Deduplicate evidence so benign bulk copy events are evaluated once.
     - Refine `MULTI_FILE_TRANSFORMATION` to require both modification AND rename/delete or decoy signals, rather than triggering on simple benign file creation/copy.
     - Explicitly report `false_positive_rate` in the summary table.

3. **Windows Defender Claim**:
   - The phrase "zero Defender false alarms" was inaccurate because Defender was not benchmarked against a malware dataset. The audit verifies that during all synthetic runs, **no Defender interference was observed**.

---

## 4. Verification Checkpoint
All subsequent phases will implement the remediations documented above, followed by a complete re-execution and validation of the benchmark suite.
