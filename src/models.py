from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import Enum


@dataclass(frozen=True)
class FileMeta:
    source: str            # 'CBS' | 'CARDS' | 'LOANS'
    file_name: str         
    business_date: date
    sequence: int          # 1 = main file for the day, 2+ = supplementary
    checksum: str          # SHA-256 of the file contents
    received_at: datetime


class FileAction(Enum): #Enum class
    LOAD = "LOAD"
    LOAD_AND_RERUN_DATE = "LOAD_AND_RERUN_DATE"
    SKIP_DUPLICATE = "SKIP_DUPLICATE"
    REJECT = "REJECT"


@dataclass(frozen=True)
class Contract:
    source: str
    required: frozenset[str]   # canonical column names
    aliases: dict[str, str]    # incoming name -> canonical name, e.g. {'txn_amount': 'amount'}
    amount_unit: str           # 'rupees' | 'paise'


@dataclass(frozen=True)
class CleanRow:
    txn_ref: str
    account_id: str
    business_date: date
    amount_inr: Decimal
    dr_cr: str                 # 'DR' | 'CR'
    currency: str


REJECT_CODES = {"MISSING_FIELD", "BAD_AMOUNT", "BAD_DATE", "DATE_MISMATCH",
                "BAD_CURRENCY", "BAD_DRCR", "AMBIGUOUS_COLUMN"}

# Not in the brief: the three sources the bank told us about.
KNOWN_SOURCES = ("CBS", "CARDS", "LOANS")