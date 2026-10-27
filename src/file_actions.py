
from .model import KNOWN_SOURCES, FileAction, FileMeta

Decision = tuple[FileAction, str]
def _same_source(incoming: FileMeta, loaded: list[FileMeta]) -> list[FileMeta]:
    "Only files from the same source are compared with each other."
    return [f for f in loaded if f.source == incoming.source]

#duplicate - for same source same checksum of new and old file 
def _check_duplicate(incoming: FileMeta, loaded: list[FileMeta]) -> Decision | None:#from the same_source fn get all the old files with same source , then match the checksum 
    """Rule 2: same checksum already loaded means same contents, so skip."""
    for old in _same_source(incoming, loaded):
        if old.checksum == incoming.checksum:
            return (FileAction.SKIP_DUPLICATE,
                    f"Same contents as '{old.file_name}', which is already loaded. Nothing to do.")
    return None

# meta data new file - wrong sources , seq<1 and if null checksum
def _check_metadata(incoming: FileMeta, loaded: list[FileMeta]) -> Decision | None:
    """Rule 1: refuse files whose own details make no sense."""
    if incoming.source not in KNOWN_SOURCES:
        return (FileAction.REJECT,
                f"Unknown source '{incoming.source}'. Expected one of: {', '.join(KNOWN_SOURCES)}.")
    if incoming.sequence < 1:
        return (FileAction.REJECT,
                f"Sequence {incoming.sequence} is not valid. Use 1 for the main file, 2 or more for supplementary files.")
    if not incoming.checksum.strip():
        return (FileAction.REJECT,
                "The file has no checksum, so it cannot be checked for duplicates.")
    return None

def _check_corrected_resend(incoming: FileMeta, loaded: list[FileMeta]) -> Decision | None:
    """Rule 3 : same name but different contents is a corrected re-send.
    The old data is now wrong, so the date must be reconciled again."""
    for old in _same_source(incoming, loaded):
        if old.file_name == incoming.file_name:
            return (FileAction.LOAD_AND_RERUN_DATE,
                    f"'{incoming.file_name}' was loaded before with different contents. "
                    f"Treating it as a corrected re-send: replace the old data and reconcile {incoming.business_date} again.")
    return None

def _check_sequence_conflict(incoming: FileMeta, loaded: list[FileMeta]) -> Decision | None:
    """Rule 4 : two different files claiming to be the
    same sequence for the same day. We cannot tell which is right, so a person decides."""
    for old in _same_source(incoming, loaded):
        if old.business_date == incoming.business_date and old.sequence == incoming.sequence:
            return (FileAction.REJECT,
                    f"{incoming.source} already has file '{old.file_name}' as sequence {old.sequence} "
                    f"for {incoming.business_date}, with different contents and a different name. "
                    "Ask the source which one is correct.")
    return None

def _check_supplementary(incoming: FileMeta, loaded: list[FileMeta]) -> Decision | None:
    """Rule 5 (brief): a supplementary file (sequence 2+) means its date is reconciled again.
    My decision where the brief is silent: if the main file has not arrived yet, load the
    supplementary file but do not rerun, because the date will be reconciled when the main file lands."""
    if incoming.sequence < 2:
        return None
    main_is_loaded = any(
        old.business_date == incoming.business_date and old.sequence == 1
        for old in _same_source(incoming, loaded)
    )
    if main_is_loaded:
        return (FileAction.LOAD_AND_RERUN_DATE,
                f"Supplementary file (sequence {incoming.sequence}) for {incoming.business_date}. "
                "Load it and reconcile that date again.")
    return (FileAction.LOAD,
            f"Supplementary file (sequence {incoming.sequence}) arrived before the main file for "
            f"{incoming.business_date}. Load it; the date is reconciled when the main file arrives.")



RULES = [
    _check_metadata,
    _check_duplicate,
    _check_corrected_resend,
    _check_sequence_conflict,
    _check_supplementary,
]

def decide_file_action(incoming: FileMeta, loaded: list[FileMeta]) -> tuple[FileAction, str]:
    """Decide what to do with an arriving file, given the files already loaded.
    Return the action and a reason an operations analyst can read."""
    for rule in RULES:
        decision = rule(incoming, loaded)
        if decision is not None:
            return decision
    return FileAction.LOAD,f"New file is Available for date {incoming.business_date}. Please Load it."