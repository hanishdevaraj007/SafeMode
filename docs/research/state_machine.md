# State Machine Architecture

The detector employs a deterministic state machine to track behavior across multiple time windows without retaining unbounded raw event data.

## States

1. **IDLE**: No suspicious activity. The detector only relies on short-window bursts.
2. **OBSERVING**: A suspicious signal was detected. The campaign window (e.g. 60s) opens.
3. **SUSPICIOUS**: Evidence has accumulated past the `de_escalation_threshold` (e.g. 40 points).
4. **HIGH_CONFIDENCE**: Evidence has accumulated past the `escalation_threshold` (e.g. 80 points). The campaign is highly likely to be malicious.
5. **CONTAINMENT_PENDING**: The system has issued a response action but is awaiting confirmation or execution.
6. **CONTAINED**: The campaign has been neutralized.

## Transitions & Hysteresis

The system prevents rapid oscillation between `IDLE` and `HIGH_CONFIDENCE` using dual-threshold hysteresis.
* `OBSERVING` -> `SUSPICIOUS` (Score >= 40)
* `SUSPICIOUS` -> `HIGH_CONFIDENCE` (Score >= 80)
* `HIGH_CONFIDENCE` -> `SUSPICIOUS` (Score drops below 80 but remains >= 40)
* `SUSPICIOUS` -> `OBSERVING` (Score drops below 40)

## Evidence Aging

Instead of retaining raw events forever, the `CampaignMemory` decays the accumulated score linearly based on the `evidence_decay_rate`.

## Inactivity Reset

If no new signals arrive within the `cooldown_period`, the campaign is forcibly reset to `IDLE` to prevent stale behavior from triggering alerts hours later.
