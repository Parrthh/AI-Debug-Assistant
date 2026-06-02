from discount import apply_discount

def test_ten_percentage_discount():
    assert apply_discount(100, 10) == 90

def test_fifty_percentage_discount():
    assert apply_discount(200, 50) == 100

def test_twenty_five_percentage_discount():
    assert apply_discount(80, 25) == 60