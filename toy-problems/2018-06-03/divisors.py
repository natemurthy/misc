def divisors(N, numbers):
    ''' Counts all the divisors from 1 to N given a list of numbers
    by which to divide

    Args:
        N (int) - a potentially very large number
        numbers (list) - an array of one or more non-negative integers

    Returns:
        the count of all the integers that divide all the numbers 1 to N
        for each element in the list of numbers and ignoring already
        counted divisors.
    '''
    if len(numbers) == 1:
        return N/numbers[0]
    
    else:
        result = 0

        for j in numbers:
            result += N/j
        
        for i in range(len(numbers)-1):
            for j in range(i+1, len(numbers)):
		if numbers[j] % numbers[i] == 0:
		    result -= N/numbers[j]
        
        return result

