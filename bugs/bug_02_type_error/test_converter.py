from converter import sum_string_numbers

def test_sum_basic():
    assert sum_string_numbers(["1", "2", "3"]) == 6

def test_sum_larger_numbers():
    assert sum_string_numbers(["10", "20", "30"]) == 60

def test_sum_single():
    assert sum_string_numbers(["42"]) == 42