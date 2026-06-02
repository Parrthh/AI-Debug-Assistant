def find_index(nums, target):
    # Returns the index of the target value in the list, else returns -1.
    i = 0
    while i < len(nums):
        if nums[i] == target:
            # Bug: i is not incremented, and hence results in infinite loop.
            return i
    return -1