from tkinter import *
import re

class Numbox:
    def __init__(self, *entryArgs, **entryKwargs):
        self.minimum = None
        self.maximum = None
        self.numbox = Entry(*entryArgs, **entryKwargs)
    
    def checkValue(self, event, addNegative, valueType):
        def isCharNotExists(isC):
            return c == isC and getText.find(c) <= -1
       
        def checkCharacters():
            check = False
            t = valueType
            if t == float:
                check = isCharNotExists(".")
                n = addNegative
                if n == True:
                    check = check or (isCharNotExists("-") and textWidget.index(INSERT) <= 0)
            return check      
        
        def getIncrementValue(a):
            a = str(a)
            c = a[a.find(".")+1:]
            if c == a:
                return 1
            else:
                return valueType("0." + "0"*(len(c)-1) + "1")
            
        checkChars = [str(c) for c in range(10)]
        [checkChars.append(c) for c in ["\x08", ""]]
        c = str(event.char)
        textWidget = event.widget
        getText = str(textWidget.get())
        d = str(event.keysym)
        if d == "Up":
            a = valueType(getText)
            b = getIncrementValue(a)
            a += b
            if self.maximum != None:
                if a > self.maximum:
                    a -= b
            self.setValue(a)
        elif d == "Down":
            a = valueType(getText)
            b = getIncrementValue(a)
            a -= b
            if self.minimum != None:
                if a < self.minimum:
                    a += b
            self.setValue(a)
        if self.minimum != None and self.maximum != None:   
            if c != "\x08":
                i = textWidget.index(INSERT)
                t = getText[:i] + c + getText[i:]
                s = re.sub('[0-9]', '', t) 
                checkRange = [("min", self.minimum), ("max", self.maximum), ("mid", self.maximum//2 if valueType is int else self.maximum/2)] 
                for (m, n) in checkRange:
                    if m == s:
                        self.setValue(n)
                        return "break"
                checkRange = ["mi", "ma", "m"]
                for g in checkRange:
                    if g == s:
                        return "continue"
                if s != "":
                    return "break"
                r = int(t)
                if r < self.minimum or r > self.maximum:
                    self.setValue(getText)
                    return "break"
        return "continue" if c in checkChars or checkCharacters() else "break"


    def setValue(self, value):
        self.numbox.delete(0, END)
        self.numbox.insert(0, value)
        
    def setRange(self, minimum, maximum):
        self.minimum = minimum
        self.maximum = maximum

    def processValue(self, valueType = float):
        c = self.numbox.get()
        c = re.sub('[a-z]', '', c)
        return valueType(0 if c == "" else c)
    
    def grid(self, **gridKwargs):
        self.numbox.grid(**gridKwargs)
        
    def pack(self, **packKwargs):
        self.numbox.pack(**packKwargs)
        
    def bind(self, addNegative = False, valueType = float):
        self.numbox.bind("<Key>", lambda event : self.checkValue(event, addNegative, valueType))