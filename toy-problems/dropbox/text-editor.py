#!/bin/env python

OP_APPEND = "APPEND"
OP_BACKSPACE = "BACKSPACE"
OP_UNDO = "UNDO"
OP_REDO = "REDO"
OP_SELECT = "SELECT"
OP_BOLD = "BOLD"

def textEditor(text_input):
    text_input.sort(key = lambda x: x[0])
    output = ""
    appendHistory = []
    backspaceHistory = []
    for line in text_input:
        opr = line[1]
        if opr == OP_APPEND:
            pass
        if opr == OP_BACKSPACE:
            pass
        if opr == OP_UNDO:
            pass
        if opr == OP_REDO:
            pass
        if opr == OP_SELECT:
            pass
        if opr == OP_BOLD:
            pass

    return output

