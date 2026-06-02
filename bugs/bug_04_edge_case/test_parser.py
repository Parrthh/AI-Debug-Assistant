from parser import parse_numbers

def test_basic_parse():
    assert parse_numbers("1,2,3") == [1,2,3]

def test_single_number():
    assert parse_numbers("12") == [12]

def test_empty_string():
    assert parse_numbers("") == []
