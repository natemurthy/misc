"""
DNA is composed of four nucleotide bases: A, T, C, and G. A strand of DNA is some sequence
of these four nucleotides (e.g. TCGAAGCC). A DNA sequencer is a machine which reads a strand 
of DNA in its organic form and converts it to a text string that a computer can 
then process.

We have a set of V sequences which correspond to DNA variants known to correlate with
diseases. These sequences have been carefully studied and are free of any errors.

We also have a set of S DNA sequences sequenced from a subject.  Sequences of DNA from the 
subject can occasionally contain mistakes (due to reading low quality DNA). With the DNA 
sequencer we're using we know that up to 2 letters may be incorrectly replaced with one of 
the three remaining letters.

Implement a method

find_suspect_variants(variants: Set[str], subjects: Set[str]) -> Set[str] 

to decide which - if any - of the disease variants may be present in the patient. 

We consider a variant present in the subject if

1. the variant sequence is of an equal length to the sequence taken from the subject and 
2. between 0 and 2 characters differ between them.


Examples:
find_suspect_variants({'TGAAC'}, {'TAGTC'}) -> {}
find_suspect_variants({'TGAAC'}, {'TAGTC', 'TAAGC'}) -> {'TGAAC'}
find_suspect_variants({'TGAAC', 'AAGGC'}, {'TAGTC', 'TAAGC'}) -> {'TGAAC', 'AAGGC'}
find_suspect_variants({'TGAAC'}, {'TGAA'}) -> {}
find_suspect_variants({'TGAAC', 'TGACA', 'GTTTT'}, {'TGAAC'}) -> {'TGAAC', 'TGACA'}

"""

"""

Discussion scratch notes:

variants = {"TCGAA", "TCGCC"}
sequences = {"TCGAT", "TC"}

assume we can index a str in a set S x V
is_close_match(sequence[0], variants) # returns True
is_close_match(sequence[1], variants) # returns False




can the length of these be useful for any data structure?

TGAAC
TAGTC

TGAAC
TAAGC


Reframing question: how many moves do i need to mutate AAGGC -> TAAGC ?
AAGGC
TAAGC


Preprocessing: consider prefixes (using Trie data structures)
https://albertauyeung.github.io/2020/06/15/python-trie.html/


But also:
https://en.wikipedia.org/wiki/Sequence_alignment
https://en.wikipedia.org/wiki/Needleman%E2%80%93Wunsch_algorithm



v = TGAAC

v[0]  = T
v[:1] = TG
v[:2] = TGA

v[-1] = C
v[::-2] = AC
v[::-3] = AAC

for v in candidate_variant:
  if v[0] == 

"""


from typing import Set

def is_close_match(s1: str, s2: str) -> bool:
    if len(s1) != len(s2):
        return False
    else:
        mismatch_count = 0
        is_match = True
        for i in range(len(s1)):
            if s1[i] != s2[i]:
                mismatch_count += 1
            if mismatch_count > 2:
                is_match = False
                break
        return is_match


def find_suspect_variants(variants: Set[str], sequences: Set[str]) -> Set[str]:
  """
  should return the variants that we find in the subject
  
  implementation steps i'm thinking (consider using exact match first, and then fuzzy match later)
  
  1. check to see all the sequences have the same length as the variants, remove any variant that has different length
     this should shrink the search space
  
  2. check if they are a close match 
  
  Aside: DNA sequence alignment
  """
  
  # TODO optimimze S x V (avoid brute force)
  
  candidate_variants = set()
  
  # can we do this loop in a linear fashion ?
  for v in variants:
    for s in sequences:
      if len(s) == len(v) and is_close_match(s,v):
        candidate_variants.add(v)
   
  return candidate_variants


def test(actual, expected):
  print(actual == expected)
  
test(find_suspect_variants({'TGAAC'}, {'TAGTC'}), set())
test(find_suspect_variants({'TGAAC'}, {'TAGTC', 'TAAGC'}), {'TGAAC'})
test(find_suspect_variants({'TGAAC', 'AAGGC'}, {'TAGTC', 'TAAGC'}), {'TGAAC', 'AAGGC'})
test(find_suspect_variants({'TGAAC'}, {'TGAA'}), set())
test(find_suspect_variants({'TGAAC', 'TGACA', 'GTTTT'}, {'TGAAC'}), {'TGAAC', 'TGACA'})
