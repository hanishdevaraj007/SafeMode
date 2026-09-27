# Workload Catalog

## Adversarial Workloads (Attack Simulations)

All adversarial workloads are designed as safe synthetic simulations operating strictly within the `lab` directory.

- **FAST_TRANSFORMATION**: Simulates rapid mass file modification and renaming. Used to baseline obvious attack behavior.
- **SLOW_TRANSFORMATION**: Inserts temporal delays between operations to evaluate evasion of tight correlation windows.
- **INTERMITTENT_TRANSFORMATION**: Transforms files in fragmented bursts with pauses to test if splitting activity reduces detector confidence.
- **RENAME_HEAVY**: Repeatedly renames multiple files within the lab to simulate rename-centric ransomware behavior.
- **DECOY_AVOIDANCE**: Deliberately targets only standard protected paths while avoiding the decoy folder, testing the detector's reliance on deception.
- **MIXED_BEHAVIOR**: Combines modifications, renames, and deletions into a complex behavioral sequence.

## Benign Workloads

Used to establish baseline performance and false-positive rates.

- **BENIGN_BULK_COPY**: Copies multiple files from one lab directory to another.
- **BENIGN_COMPRESSION**: Creates a ZIP archive from lab files, triggering rapid read/writes.
- **BENIGN_DOCUMENT_EDIT**: Simulates standard sequential saving of a text document with slight delays.
- **BENIGN_RENAME_BATCH**: Modifies the names of a batch of synthetic images for organizational purposes.
- **BENIGN_BACKUP_STYLE**: Creates temporary copies of files before rotating them to final destinations, closely mirroring typical backup software IO.
