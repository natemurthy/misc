"""
https://www.geeksforgeeks.org/python-remove-unwanted-spaces-from-string/
"""

def solution(phrase):
    clean = ""

    for i in range(len(phrase)-1):

        if phrase[i] == ' ':
            continue
        
        if phrase[i] != ' ':
            clean += phrase[i]
            if phrase[i+1] == ' ':
                clean += ' '
    
    if phrase[-1] != ' ':
        clean += phrase[-1]
    
    return clean


print solution("   hello   world       my god  that        ")
print solution("at         some point we          will  fly")

