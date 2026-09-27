# Detection Logic & Behavioral Memory

## Overview
This document explains the detection architecture, including the new multi-timescale stateful behavior memory.

## Pipeline Flow

1. **Raw Telemetry**: `watchdog` detects `created`, `modified`, `deleted`, `renamed`.
2. **Short-Term Window**: Events enter the `TemporalEventBuffer` (e.g., 5 seconds) to identify high-frequency bursts.
3. **Signal Extraction**: The buffer yields behavioral `Signals` (e.g., `MULTI_FILE_TRANSFORMATION`, `RENAME_BURST`).
4. **Campaign Memory**: Signals update the `CampaignMemory`. Unlike the short buffer, this maintains an accumulating score over a longer campaign window (e.g., 60 seconds).
5. **Evidence Aging**: As time passes without signals, the score decays. A long inactivity period fully resets the state to `IDLE`.
6. **Correlation Engine**: Evaluates the `CampaignState` to produce an Explainable Decision.
7. **Safe Containment Controller**: If `HIGH_CONFIDENCE` is reached, it passes the decision to the `ResponseManager`.

## Decoy Role & Avoidance Handling
Decoy interaction provides an immediate heavy score increase (+40). However, a workload avoiding decoys (e.g., `DECOY_AVOIDANCE`) can still reach `HIGH_CONFIDENCE` via repeated `MULTI_FILE_TRANSFORMATION` (+25) and `RENAME_BURST` (+20). This ensures evasion resistance against smart attackers.

## Process Attribution Modes
Because `watchdog` lacks ETW, process attribution operates in two modes:
* `TEMPORAL_CONTEXT`: Best-effort snapshot of currently running processes. Used for live passive monitoring.
* `EXPERIMENT_EXACT`: Exact PID registration populated explicitly by the `WorkloadRunner` for lab experiments.

## Containment Safety Model
The `ResponseManager` refuses to Suspend/Terminate a PID unless it is strictly verified against the `ProcessRegistry` as a registered, active SafeMode lab workload. `DRY_RUN` is used to audit what would happen without causing endpoint damage.
