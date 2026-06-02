def apply_discount(price, discount_percentage):
    # Returns the final price after applying the discount percentage.
    # Bug: The formula should be final_price = price * (1 - discount_percentage / 100)
    final_price = price - (price * discount_percentage)
    return final_price

