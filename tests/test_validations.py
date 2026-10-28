from datetime import date
from decimal import Decimal

import pytest

from factories import FILE_DATE, make_contract, make_loans_contract, make_row
from src import REJECT_CODES, CleanRow, validate_row


def check(row, contract=None):
    return validate_row(row, contract or make_contract(), FILE_DATE)

# ---- a good row ----------------------------------------------------------

def test_valid_row_becomes_clean_row():
    result = check(make_row())
    assert result == CleanRow("T1", "A100", date(2026, 10, 7), Decimal("1500.50"), "DR", "INR")

# ---- column names: aliases, extras, ambiguity ----------------------------
def test_alias_column_is_renamed_to_canonical_name():
    row = make_row()
    row["txn_amount"] = row.pop("amount")#remove amount column and return it's value to txn_amount 
    assert check(row).amount_inr == Decimal("1500.50")


def test_unknown_extra_column_is_ignored():
    extr_col=check(make_row(branch_code="B7"))
    assert isinstance(extr_col, CleanRow)


def test_column_and_its_alias_together_is_ambiguous():
    assert check(make_row(txn_amount="99")) == "AMBIGUOUS_COLUMN"


def test_column_names_are_matched_exactly_as_written():
    row = make_row()
    row[" amount"] = row.pop("amount")      # header with a stray space is NOT the amount column
    assert check(row) == "MISSING_FIELD"

# ---- trimming and missing values -----------------------------------------

def test_whitespace_around_values_is_trimmed():
    result = check(make_row(txn_ref="  T9  ", dr_cr=" dr ", amount=" 10.00 "))
    assert result.txn_ref == "T9" and result.dr_cr == "DR" and result.amount_inr == Decimal("10.00")


def test_value_that_is_blank_after_trimming_is_missing():
    assert check(make_row(account_id="   ")) == "MISSING_FIELD"


def test_missing_column_is_missing_field():
    row = make_row()
    del row["account_id"]
    assert check(row) == "MISSING_FIELD"


# ---- amounts -------------------------------------------------------------
@pytest.mark.parametrize("text", ["0", "0.00", "-5", "abc", "1,000.00", "1e5", "NaN", "Infinity", "10.005"])
def test_amount_must_be_a_positive_plain_decimal(text):
    assert check(make_row(amount=text)) == "BAD_AMOUNT"


def test_amount_keeps_exact_decimal_value_not_float():
    assert check(make_row(amount="1234567890123.45")).amount_inr == Decimal("1234567890123.45")


def test_paise_are_converted_to_rupees_when_contract_says_paise():
    result = check(make_row(amount="150050"), make_loans_contract())
    assert result.amount_inr == Decimal("1500.50")


def test_paise_with_a_decimal_point_is_a_bad_amount():
    assert check(make_row(amount="150.5"), make_loans_contract()) == "BAD_AMOUNT"


# ---- direction -----------------------------------------------------------

@pytest.mark.parametrize("text,expected", [("D", "DR"), ("dr", "DR"), ("C", "CR"), ("Cr", "CR")])
def test_dr_cr_accepts_case_and_normalises(text, expected):
    assert check(make_row(dr_cr=text)).dr_cr == expected


def test_dr_cr_other_value_is_bad_drcr():
    assert check(make_row(dr_cr="X")) == "BAD_DRCR"

# ---- dates ---------------------------------------------------------------

@pytest.mark.parametrize("text", ["07-10-2026", "2026-10-7", "20261007", "2026/10/07", "2026-02-30"])
def test_business_date_must_be_strict_yyyy_mm_dd(text):
    assert check(make_row(business_date=text)) == "BAD_DATE"


def test_valid_date_that_is_not_the_file_date_is_mismatch():
    assert check(make_row(business_date="2026-10-06")) == "DATE_MISMATCH"


# ---- currency ------------------------------------------------------------

def test_currency_other_than_inr_is_bad_currency():
    assert check(make_row(currency="USD")) == "BAD_CURRENCY"


def test_currency_inr_is_accepted_in_any_case():
    assert check(make_row(currency="inr")).currency == "INR"


def test_loans_row_without_currency_column_is_inr():
    row = make_row(amount="100")
    del row["currency"]
    assert check(row, make_loans_contract()).currency == "INR"


def test_non_loans_row_without_currency_is_missing_field():
    row = make_row()
    del row["currency"]
    assert check(row) == "MISSING_FIELD"
# ---- exactly one code ----------------------------------------------------

def test_row_with_several_problems_returns_only_the_first_in_check_order():
    row = make_row(amount="abc", business_date="bad", dr_cr="X", currency="USD")
    assert check(row) == "BAD_AMOUNT"


def test_every_returned_code_is_in_reject_codes():
    bad_rows = [make_row(amount="x"), make_row(business_date="x"), make_row(dr_cr="x"),
                make_row(currency="x"), make_row(account_id=""), make_row(txn_amount="1")]
    for row in bad_rows:
        assert check(row) in REJECT_CODES