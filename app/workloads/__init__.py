from app.workloads.adversarial import (
    FastTransformation,
    SlowTransformation,
    DecoyAvoidance,
    RenameHeavy,
    MixedBehavior,
    IntermittentTransformation
)
from app.workloads.benign import (
    BenignBulkCopy,
    BenignCompression,
    BenignDocumentEdit,
    BenignRenameBatch,
    BenignBackupStyle
)

def get_all_workloads():
    return [
        FastTransformation,
        SlowTransformation,
        DecoyAvoidance,
        RenameHeavy,
        MixedBehavior,
        IntermittentTransformation,
        BenignBulkCopy,
        BenignCompression,
        BenignDocumentEdit,
        BenignRenameBatch,
        BenignBackupStyle
    ]
