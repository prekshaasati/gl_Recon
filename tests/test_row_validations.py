from decimal import Decimal
import pytest
from datetime import date
from src.row_validations import parse_dr_cr, parse_amount,parse_currency, parse_date,rename_columns, trim_values


def test_parse_dr():
    assert parse_dr_cr("dr") == "DR"


def test_parse_cr():
    assert parse_dr_cr("cr") == "CR"


def test_parse_invalid_value():
    assert parse_dr_cr("invalid") is None

def test_parse_amount_in_rupees():
    assert parse_amount("100.50", "rupees") == Decimal("100.50")


def test_parse_whole_rupee_amount():
    assert parse_amount("250", "rupees") == Decimal("250.00")


def test_parse_invalid_amount():
    assert parse_amount("abc", "rupees") is None


def test_parse_zero_amount():
    assert parse_amount("0", "rupees") is None


def test_parse_negative_amount():
    assert parse_amount("-100", "rupees") is None


def test_parse_amount_in_paise():
    assert parse_amount("15050", "paise") == Decimal("150.50")


def test_parse_amount_unknown_unit_is_a_setup_error_not_a_bad_row():
    with pytest.raises(ValueError):
        parse_amount("5", "dollars")


def test_parse_date_rejects_non_ascii_digits():
    assert parse_date("２０２６-10-07") is None      # full-width digits


def test_parse_date_accepts_leap_day():
    assert parse_date("2028-02-29") == date(2028, 2, 29)


def test_parse_dr_cr_rejects_empty_text():
    assert parse_dr_cr("") is None


def test_parse_currency_rejects_other_codes():
    assert parse_currency("EUR") is None


def test_rename_columns_two_aliases_for_one_name_is_ambiguous():
    aliases = {"amt": "amount", "txn_amount": "amount"}
    assert rename_columns({"amt": "1", "txn_amount": "2"}, aliases) is None


def test_trim_values_turns_none_into_empty_string():
    assert trim_values({"a": None, "b": " x "}) == {"a": "", "b": "x"}

