"""
Word Segmentation 

Given a string without whitespace, and a vocabulary, write a function that splits 
the string into words.

For example, given the string

helloworld!

and the vocabulary 

['he', 'hell', 'hello', 'low', 'world', '!']

your function should return the list

['hello', 'world', '!']

Edge cases:
* If there are multiple ways to split a string, our function should return the list with 
  the least number of words.
* The string is not guaranteed to be splittable. In cases it is not, your function should 
  return an empty list.
* If the string is empty, your function should return an empty list
"""

# TODO this is incomplete
def split(text, vocabulary):
   result = []
   options = []
   if text in vocabulary:
        result = [text]
        options.append(result)
   else:
       i = 0
       while i < len(text):
           s = text[0:i+1]
           if s in vocabulary:
               result.append(s)
               split(text[i+1:], vocabulary)
   return options

