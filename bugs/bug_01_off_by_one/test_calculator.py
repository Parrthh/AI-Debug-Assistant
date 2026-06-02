from calculator import sum_up_to_index

def test_sum_up_to_index_basic():
    numbers = [10, 20, 30, 40, 50]
    assert sum_up_to_index(numbers, 2) == 30

def test_sum_up_to_index_middle():
    numbers = [5,15,25,35]
    assert sum_up_to_index(numbers, 1) == 5

def test_sum_up_to_index_full():
    numbers = [1,2,3,4]
    assert sum_up_to_index(numbers, 3) == 6