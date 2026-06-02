from search import find_index

def test_find_first():
    assert find_index([1,2,3,4,5,6], 1) == 0

def test_find_middle():
    assert find_index([1,2,3,4,5,6], 3) == 2

def test_not_found():
    assert find_index([1,2,3,4,5,6], 7) == -1