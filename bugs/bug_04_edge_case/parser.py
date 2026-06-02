def parse_numbers(data):
    # Parsing a comma-spearated string of numbers that returns a list of integers.
    return [int(x) for x in data.split(",")]