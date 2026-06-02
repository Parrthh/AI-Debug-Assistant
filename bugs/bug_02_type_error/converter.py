def sum_string_numbers(numbers):
    # Takes a list of numbers as strings and returns their sum as an integer.
    total = 0
    for n in numbers:
        # Bug: It should be total += int(n) - then only we can add string to integer.
        total += n 
    return total
