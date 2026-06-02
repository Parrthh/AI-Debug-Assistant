def sum_up_to_index(numbers, n):
    # Returns the sum of the numbers up to the index n
    total = 0
    for i in range(n+1):
        total += numbers[i]
    return total