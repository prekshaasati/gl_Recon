#functions to create objects and sample data that your tests can use.
from dataclasses import replace
from datetime import date, datetime

from src import Contract, FileMeta

FILE_DATE = date(2026, 10, 7)


def make_file(**changes) -> FileMeta:
    #A valid main CBS file for 2026-10-07. Can Pass keyword arguments to change fields.
    base = FileMeta(
        source="CBS",
        file_name="cbs_txn_20261007_1.csv",
        business_date=FILE_DATE,
        sequence=1,
        checksum="checksum-a",
        received_at=datetime(2026, 10, 7, 2, 0),
    )
    return replace(base, **changes)


def make_contract(**changes) -> Contract:
    #A CBS contract in rupees, with one alias (txn_amount -> amount)
    base = Contract(
        source="CBS",
        required=frozenset({"txn_ref", "account_id", "business_date", "amount", "dr_cr", "currency"}),
        aliases={"txn_amount": "amount"},
        amount_unit="rupees",
    )
    return replace(base, **changes)


def make_loans_contract() -> Contract:
    #Loans: amounts in paise, no currency column.
    return Contract(
        source="LOANS",
        required=frozenset({"txn_ref", "account_id", "business_date", "amount", "dr_cr"}),
        aliases={},
        amount_unit="paise",
    )


def make_row(**changes) -> dict:
    #A valid CBS row. Can pass keyword arguments to change a value.
    row = {"txn_ref": "T1", "account_id": "A100", "business_date": "2026-10-07",
           "amount": "1500.50", "dr_cr": "DR", "currency": "INR"}
    row.update(changes)
    return row
