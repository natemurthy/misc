#!/bin/env python

def test(expected, actual):
    if expected == actual:
        print("Pass")
    else:
        print("Fail (expected '{}', actual '{}')".format(expected, actual))

"""
Rotational Cipher
https://www.facebookrecruiting.com/portal/coding_practice_question/?problem_id=238827593802550
"""
lower_alpha_to_index = {}
for i, v in enumerate(range(ord('a'),ord('z')+1)):
    lower_alpha_to_index[chr(v)] = i

lower_index_to_alpha = {}
for i, v in enumerate(range(ord('a'),ord('z')+1)):
    lower_index_to_alpha[i] = chr(v)
  
upper_alpha_to_index = {}
for i, v in enumerate(range(ord('A'),ord('Z')+1)):
    upper_alpha_to_index[chr(v)] = i
  
upper_index_to_alpha = {}
for i, v in enumerate(range(ord('A'),ord('Z')+1)):
    upper_index_to_alpha[i] = chr(v)
  
nums = [str(i) for i in range(0,10)]

def rotationalCipher(input, rotation_factor):
    result = ""
    for c in input:
        if c in lower_alpha_to_index.keys():
            ix = (lower_alpha_to_index[c]+rotation_factor)%26
            result += lower_index_to_alpha[ix]
        elif c in upper_alpha_to_index.keys():
            ix = (upper_alpha_to_index[c]+rotation_factor)%26
            result += upper_index_to_alpha[ix]
        elif c in nums:
            result += str((int(c)+rotation_factor)%10)
        else:
            result += c
    return result

input_1 = "All-convoYs-9-be:Alert1."
rotation_factor_1 = 4
expected_1 = "Epp-gsrzsCw-3-fi:Epivx5."
output_1 = rotationalCipher(input_1, rotation_factor_1)
test(expected_1, output_1)

input_2 = "abcdZXYzxy-999.@"
rotation_factor_2 = 200
expected_2 = "stuvRPQrpq-999.@"
output_2 = rotationalCipher(input_2, rotation_factor_2)
test(expected_2, output_2)


"""
Matching Pairs
https://www.facebookrecruiting.com/portal/coding_practice_question/?problem_id=559324704673058
"""
def matching_pairs(s, t):
    s_mismatches = []
    t_mismatches = []
    n = len(s)
    k = 0
    for i in range(n):
        if s[i] != t[i]:
            s_mismatches.append(s[i])
            t_mismatches.append(t[i])
        else:
            k += 1

    if len(s_mismatches) == 0:
        k -= 2

    s_mismatches.sort()
    t_mismatches.sort()

    for i in range(len(s_mismatches)-1):
        if s_mismatches[i] in t_mismatches and s_mismatches[i+1] in t_mismatches:
            k += 2

    return k


s_1, t_1 = "abcde", "adcbe"
expected_1 = 5
output_1 = matching_pairs(s_1, t_1)
test(expected_1, output_1)

s_2, t_2 = "abcd", "abcd"
expected_2 = 2
output_2 = matching_pairs(s_2, t_2)
test(expected_2, output_2)
test(1, matching_pairs("mno", "mno"))
test(1, matching_pairs("a", "a"))
