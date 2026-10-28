
"""
standardizing  incoming data, rejects invalid transactions with a specific reason, and lets valid transactions proceed in a predictable format.
Order of checks :
  1 AMBIGUOUS_COLUMN  a column and its alias both present
  2 MISSING_FIELD     a needed value is missing or blank after trimming
  3 BAD_AMOUNT        not a positive amount
  4 BAD_DATE          not a real YYYY-MM-DD date
  5 DATE_MISMATCH     valid date, but not the file's business date
  6 BAD_CURRENCY      not INR
  7 BAD_DRCR          not D, DR, C or CR"""


from datetime import date
from .model import CleanRow, Contract
import re
from decimal import Decimal

# Digits only, so none of these get through: -5, 1,000, 1e5, NaN, Infinity, 1_000
_RUPEES = re.compile(r"[0-9]+(\.[0-9]{1,2})?")   # up to 2 decimals
_PAISE = re.compile(r"[0-9]+")                   # paise are whole numbers
_DATE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")  # strictly YYYY-MM-DD
_DR_CR = {"D": "DR", "DR": "DR", "C": "CR", "CR": "CR"}

CORE_FIELDS = {"txn_ref","account_id","business_date","amount","dr_cr"}     
      
      
def rename_columns(row: dict[str, str],aliases: dict[str, str]) -> dict[str, str] | None:
    renamed: dict[str, str] = {}

    for name, value in row.items():
        canonical = aliases.get(name, name)#get alias name_col:std_col
        print(canonical)
        if canonical in renamed:
            return None

        renamed[canonical] = value 

    return renamed

def trim_values(row: dict[str, str]) -> dict[str, str]:
    cleaned = {}
    for name, value in row.items():#for each row's (name,value) pair ,remove whitespace in value and add pait in new dict
        cleaned[name] = (value or "").strip()
    return cleaned




def _needed_fields(contract: Contract) -> set[str]:
    needed = CORE_FIELDS | set(contract.required)
    if contract.source != "LOANS":      # Loans files have no currency column
        needed.add("currency")
    return needed

def parse_amount(text: str, unit: str) -> Decimal | None:
    #check if the amount is in right unit and convert decimal to 2 places else none
    if unit not in ("rupees", "paise"):
        raise ValueError(f"Unknown amount unit: {unit}")  
    pattern = _PAISE if unit == "paise" else _RUPEES
    if not pattern.fullmatch(text):
        return None
    amount = Decimal(text)
    if unit == "paise":
        amount = amount / 100
    if amount <= 0:
        return None
    return amount.quantize(Decimal("0.01"))

def parse_date(text: str) -> date | None:
   # check if the date format is valid and if the date is a valid date  or return  None.
    if not _DATE.fullmatch(text):
        return None
    try:
        return date.fromisoformat(text)
    except ValueError:        #like 2026-2-30 
        return None


def parse_dr_cr(text: str) -> str | None:
    #D, DR, C or CR in any case becomes 'DR' or 'CR'
    txt=text.upper()
    return _DR_CR.get(txt)


def parse_currency(text: str) -> str | None:
    #Only accept INR
    return "INR" if text.upper() == "INR" else None


def validate_row(row: dict[str, str], contract: Contract, file_date: date) -> CleanRow | str:
    renamed = rename_columns(row, contract.aliases)
    if renamed is None:
        return "AMBIGUOUS_COLUMN"
    values = trim_values(renamed)

    for field in _needed_fields(contract):
        if values.get(field, "") == "":
            return "MISSING_FIELD"

    amount = parse_amount(values["amount"], contract.amount_unit)
    if amount is None:
        return "BAD_AMOUNT"

    row_date = parse_date(values["business_date"])
    if row_date is None:
        return "BAD_DATE"
    if row_date != file_date:
        return "DATE_MISMATCH"

    currency = "INR" if contract.source == "LOANS" else parse_currency(values["currency"])
    if currency is None:
        return "BAD_CURRENCY"

    dr_cr = parse_dr_cr(values["dr_cr"])
    if dr_cr is None:
        return "BAD_DRCR"

    return CleanRow(
        txn_ref=values["txn_ref"],
        account_id=values["account_id"],
        business_date=row_date,
        amount_inr=amount,
        dr_cr=dr_cr,
        currency=currency,
    )






row = {
    "txn_ref": " TXN101 ",
    "txn_amount": " 1500",
    "account_id": "ACC501",
   # "amount": "1500"
}

aliases = {
    "txn_amount": "amount"
}

#result = rename_columns(row, aliases)
#result = trim_values(row)

#print(result)