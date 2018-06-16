def has_pair_with_sum(arr, sum):
    comp = {}
    for v in arr:
        if v in comp.keys():
            return True
        comp[sum-v] = None
    return False

if __name__ == "__main__":
    input1 = [1,2,4,9]
    print(has_pair_with_sum(input1, 8))

    input2 = [1,9,3,6,1,7,9]
    print(has_pair_with_sum(input2, 8))
