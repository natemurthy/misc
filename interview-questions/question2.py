# given
arr = ['a','b','a','c','d','d','e','d','x']

# find letter that occurs most often

import operator

def get_max_char_occurence(chars):
    char_occurence_dict = {}
    for c in chars:
        if c not in char_occurence_dict.keys():
            char_occurence_dict[c] = 1
        else:
            char_occurence_dict[c] += 1
    return max(char_occurence_dict.iteritems(), key=operator.itemgetter(1))[0]
