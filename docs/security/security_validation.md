# SafeMode Security Validation Log & Safety Gates

This document records the formal security validation results for the **SafeMode Research Prototype (AY2026–27)** under **Prompt 4**.

## Security Architecture & Verification Gates

SafeMode enforces a zero-trust containment policy ensuring that automated response actions (DRY_RUN, SUSPEND, RESUME, TERMINATE) can **NEVER** target non-laboratory system processes, host system files, or unverified background tasks.

---

## Security Validation Suite Results (S1 – S6)

### TEST S1 — Lab Path Enforcement
* **Objective**: Confirm that workload parameters targeting paths outside `D:\Innovation_lab\lab` are strictly rejected prior to execution.
* **Test Vectors Evaluated**:
  1. `D:\Innovation_lab\lab\workloads\valid_test.txt` -> **ACCEPTED**
  2. `C:\Users` -> **REJECTED (Path violation)**
  3. `C:\` -> **REJECTED (Path violation)**
  4. `C:\Windows\System32` -> **REJECTED (Path violation)**
* **Result**: **PASS**. No external path access or writes permitted.

---

### TEST S2 — Workload Name Whitelisting
* **Objective**: Verify that only pre-registered synthetic workload scenario names can be executed and arbitrary shell commands are rejected.
* **Test Vectors Evaluated**:
  1. `FAST_TRANSFORMATION` -> **ACCEPTED (Registered scenario)**
  2. `BENIGN_BULK_COPY` -> **ACCEPTED (Registered scenario)**
  3. `UNKNOWN_MALWARE_X` -> **REJECTED (Unknown workload name)**
  4. `--command "powershell Remove-Item C:\*"` -> **REJECTED (Invalid CLI option)**
* **Result**: **PASS**. SafeMode CLI functions exclusively as a registered scenario runner, never a generic shell executor.

---

### TEST S3 — Containment Registration Gate
* **Objective**: Ensure that containment actions cannot be executed against any process PID that is not explicitly registered in the active `ProcessRegistry`.
* **Test Vectors Evaluated**:
  1. System process PID (e.g., `explorer.exe` PID) -> **REFUSED (Check 2 Failed: PID not registered)**
  2. Unregistered background python PID -> **REFUSED (Check 2 Failed: PID not registered)**
  3. Registered SafeMode synthetic subprocess PID -> **ACCEPTED (Identity verified)**
* **Result**: **PASS**. Arbitrary PIDs strictly blocked.

---

### TEST S4 — LAB_MODE Gate
* **Objective**: Verify that setting `LAB_MODE=False` in configuration immediately blocks all containment actions regardless of registration status.
* **Test Vectors Evaluated**:
  1. `LAB_MODE=True`, registered process -> **CONTAINMENT PERMITTED**
  2. `LAB_MODE=False`, registered process -> **REFUSED (Check 1 Failed: LAB_MODE is False)**
* **Result**: **PASS**. Global kill-switch functions deterministically.

---

### TEST S5 — Target Identity Check (PID Reuse Defense)
* **Objective**: Verify that containment checks executable binary path and process creation timestamp to prevent accidental targeting of recycled PIDs.
* **Test Vectors Evaluated**:
  1. Matching PID + matching executable path + matching start time -> **PASS**
  2. Matching PID + mismatched executable path (e.g. `cmd.exe` instead of `python.exe`) -> **REFUSED (Check 4 Failed: Executable identity mismatch)**
  3. Matching PID + mismatched process creation timestamp (> 2.0s delta) -> **REFUSED (Check 5 Failed: Start time mismatch)**
* **Result**: **PASS**. PID recycling attack surface mitigated.

---

### TEST S6 — No Outside-Lab Writes
* **Objective**: Audit filesystem operations during workload runs to ensure 100% of created and modified files reside inside `D:\Innovation_lab\lab`.
* **Method**: Full filesystem tree walk and canonical path comparison during execution of `FAST_TRANSFORMATION`, `SLOW_TRANSFORMATION`, and `BENIGN_BULK_COPY`.
* **Result**: **PASS**. All 100% created/modified paths verified to lie within `D:\Innovation_lab\lab`. Zero external writes.
