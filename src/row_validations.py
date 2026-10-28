#from datetime import date, datetime
#from .model import CleanRow, Contract


"""
Order of checks :
  1 AMBIGUOUS_COLUMN  a column and its alias both present
  2 MISSING_FIELD     a needed value is missing or blank after trimming
  3 BAD_AMOUNT        not a positive amount
  4 BAD_DATE          not a real YYYY-MM-DD date
  5 DATE_MISMATCH     valid date, but not the file's business date
  6 BAD_CURRENCY      not INR
  7 BAD_DRCR          not D, DR, C or CR"""

#def validate_row(row: dict[str, str], contract: Contract, file_date: date) -> CleanRow | str:
      
      
      
      
def rename_columns(
    row: dict[str, str],
    aliases: dict[str, str]
) -> dict[str, str] | None:

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


row = {
    "txn_ref": " TXN101 ",
    "txn_amount": " 1500",
    "account_id": "ACC501",
   # "amount": "1500"
}

aliases = {
    "txn_amount": "amount"
}

result = rename_columns(row, aliases)
result = trim_values(row)

print(result)