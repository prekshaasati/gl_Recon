from datetime import date

from factories import make_file
from src import FileAction, decide_file_action



# test load
def test_new_main_file_is_loaded():
    action, _ = decide_file_action(make_file(), loaded=[])
    assert action == FileAction.LOAD

#test duplicate with same file name and checksum
def test_same_checksum_is_skipped_as_duplicate():
    old = make_file()
    action, _ = decide_file_action(make_file(), loaded=[old])
    assert action == FileAction.SKIP_DUPLICATE

#test duplicate when file name is different with same content : 
def test_same_checksum_with_different_file_name_is_still_a_duplicate():
    old = make_file(file_name="cbs_txn_20261007_1.csv")
    incoming = make_file(file_name="cbs_txn_20261007_1_copy.csv")
    action, _ = decide_file_action(incoming, loaded=[old])
    assert action == FileAction.SKIP_DUPLICATE

# test LOAD_AND_RERUN_DATE same file with diffrent contwnt 
def test_same_name_new_checksum_is_corrected_resend():
    old = make_file(checksum="old")
    incoming = make_file(checksum="new")
    action, reason = decide_file_action(incoming, loaded=[old])
    assert action == FileAction.LOAD_AND_RERUN_DATE
    assert "corrected re-send" in reason

# test LOAD_AND_RERUN_DATE when supplementy file is sent 
def test_supplementary_file_triggers_rerun_of_its_date():
    main = make_file()
    supplementary = make_file(file_name="cbs_txn_20261007_2.csv", sequence=2, checksum="checksum-b")
    action, _ = decide_file_action(supplementary, loaded=[main])
    assert action == FileAction.LOAD_AND_RERUN_DATE

#test LOAD_AND_RERUN_DATE when supplementry file is resent 
def test_corrected_resend_of_a_supplementary_file_reruns_its_date():
    old = make_file(file_name="cbs_txn_20261007_2.csv", sequence=2, checksum="old")
    incoming = make_file(file_name="cbs_txn_20261007_2.csv", sequence=2, checksum="new")
    action, _ = decide_file_action(incoming, loaded=[make_file(), old])
    assert action == FileAction.LOAD_AND_RERUN_DATE


# test LOAD when supplementry file is sent before main is loaded 
def test_supplementary_before_main_is_loaded_without_rerun():
    supplementary = make_file(file_name="cbs_txn_20261007_2.csv", sequence=2)
    action, reason = decide_file_action(supplementary, loaded=[])
    assert action == FileAction.LOAD
    assert "before the main file" in reason

#test LOAD if supplementary file wait for main file on same date 
def test_supplementary_waits_for_main_of_the_same_date_not_another_date():
    main_other_day = make_file(business_date=date(2026, 10, 6), file_name="cbs_txn_20261006_1.csv")
    supplementary = make_file(file_name="cbs_txn_20261007_2.csv", sequence=2, checksum="checksum-b")
    action, _ = decide_file_action(supplementary, loaded=[main_other_day])
    assert action == FileAction.LOAD

#test Reject
def test_second_file_with_same_sequence_and_different_name_is_rejected():
    old = make_file(file_name="cbs_txn_20261007_1.csv", checksum="a")
    incoming = make_file(file_name="cbs_txn_20261007_1_final.csv", checksum="b")
    action, _ = decide_file_action(incoming, loaded=[old])
    assert action == FileAction.REJECT

#test not reject on same checksum but differenct source 
def test_same_checksum_in_another_source_is_not_a_duplicate():
    cards_file = make_file(source="CARDS", file_name="cards_txn_20261007_1.csv")
    action, _ = decide_file_action(make_file(), loaded=[cards_file])
    assert action == FileAction.LOAD

# test reject on diffrent source
def test_unknown_source_is_rejected():
    action, reason = decide_file_action(make_file(source="UPI"), loaded=[])
    assert action == FileAction.REJECT
    assert "Unknown source" in reason

#test reject on less than 1 seq
def test_sequence_below_one_is_rejected():
    action, _ = decide_file_action(make_file(sequence=0), loaded=[])
    assert action == FileAction.REJECT

#test reject on blank checksum
def test_blank_checksum_is_rejected():
    action, _ = decide_file_action(make_file(checksum="  "), loaded=[])
    assert action == FileAction.REJECT



#check order of file action 
def test_duplicate_rule_wins_over_supplementary_rule():
    supplementary = make_file(file_name="cbs_txn_20261007_2.csv", sequence=2, checksum="same")
    action, _ = decide_file_action(supplementary, loaded=[make_file(), supplementary])
    assert action == FileAction.SKIP_DUPLICATE


def test_every_decision_has_a_readable_reason():
    cases = [
        make_file(),
        make_file(source="UPI"),
        make_file(sequence=2, file_name="cbs_txn_20261007_2.csv"),
    ]
    for incoming in cases:
        _, reason = decide_file_action(incoming, loaded=[])
        assert len(reason) > 10
