"""
see: https://github.com/bminor/bash/blob/master/braces.c


$ echo "a{b,c}"    # 1 * 2 = 2
> ab ac

[[a], [b,c]]

$ echo "a{b,c,d}"  # 1 * 3
> ab ac ad
[[a], [b,c,d]]


$ echo "a{b,c,d{1,2}}{f,g}"
> abf acf ad1f ad2f abg acg ad1g ad2g
[[a], [b,c,[d,[1,2]]], [f,g]]
[echo("a"), echo("{b,c,d{1,2}}"), echo("{f,g}")]
[..., [b, c, echo("d{1,2}")], ...]
[..., [b, c, [d, echo("{1,2}")]], ...]

$ echo "aa{b,c}"
> aab aac
[[aa], [b,c]]

i = 0
result = []
if input_t[0] != '{' or input_t[0] != '}':
  substr = ""
  substr += input_t[0]
  i += 1
  
  result.append([input[0]])
    
  
input

l = 0, r = len(input_s)-1


"""
def inner(inner_s):
    result = []
    n = len(inner_s)
    i = 0
    while i < n:
        c = inner_s[i]
        if c != '{' and c != ',' and c != '}':
            result.append(c)
        i += 1
    return result, n


def echo(input_s):
    result = []
    i = 0
    while i < len(input_s):
        c = input_s[i]
        if c == '{':
            sub_arr, d = inner(input_s[i:])
            result.append(sub_arr)
            i += d
        elif c == '}':
            continue
        else:
            result.append(c)
            i += 1

    #output = ""
    #for c in result:
        #if isinstance(c, str):
            #output += c
        #elif isinstance(c, list):

    return result

print echo("a{b,c}")


"""
def echo(input_s):
  n = len(input_s)
  result = []
  gen = []
  substr = ""
  st = []
  while i < n:
    
    if input_s[i] != '{' or input_s[i] != '}':
      substr += input_s[i]
      
    elif input_s[i] == '{':
      i 
      gen.append([substr])
      st = []
      j = i
      while input_s[j] != '{':
        st.push(input_s[j])
        j += 1
        if 
        
    i += 1
        
  return result
"""
