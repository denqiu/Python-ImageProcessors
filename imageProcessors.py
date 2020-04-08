from tkinter.ttk import *
from tkinter import *
from tkinter.filedialog import askopenfilename
from advancedGui import AdvancedGui
from advanced import Advanced
from pathlib import Path
from cv2 import *
import numpy as np, os, math
         
def parentDirectory(filePath):
    return os.path.dirname(filePath)

def directoryName(filePath):
    return os.path.basename(filePath)

def isDirectory(filePath):
    return os.path.isdir(filePath)

def isFile(filePath):
    return os.path.isfile(filePath)
          
def createDirectory(name):
    global parent
    directory = str(parent) + "\\" + name
    if not os.path.exists(directory):
        os.makedirs(directory)
    return directory

def updateWindows(state, i):
    i = imageCombo.current() if i == None else i
    global windows
    windows = [(state, index) if index == i else (s, index) for (s, index) in windows]

def getWindowState():
    for (state, index) in windows:
        if index == imageCombo.current():
            return state
    return None

def getWindowIndex(index):
    j = 0
    for (state, i) in windows:
        if j == index:
            return i
        j += 1
    return -1

def addWindow():
    global countWindows
    countWindows += 1
    updateWindows("disabled", None)
    process.configure(state = getWindowState())
    if cancel["state"] == "normal":
        cancel["state"] = "disabled"
        
def cancelWindow(window, index):
    global countWindows
    countWindows -= 1
    updateWindows("normal", getWindowIndex(index))
    process.configure(state = getWindowState())
    if countWindows == 0:
        cancel["state"] = "normal"
    window.destroy()
    
def removeAllWindows():
    cv2.destroyAllWindows()
    
def checkValue(event, addNegative, valueType = "float"):
    def isCharNotExists(isC):
        return c == isC and getText.find(c) <= -1
   
    def checkCharacters():
        check = False
        t = valueType
        if t == "float":
            check = isCharNotExists(".")
            n = addNegative
            if n == True:
                check = check or (isCharNotExists("-") and textWidget.index(INSERT) <= 0)
        return check
    
    textWidget = event.widget
    getText = str(textWidget.get())
    checkChars = [str(c) for c in range(10)]
    [checkChars.append(c) for c in ["\x08", ""]]
    c = str(event.char)
    return "continue" if c in checkChars or checkCharacters() else "break"

def processValue(c, valueType = float):
    return valueType(0 if c == "" else c)

def resize(resizeFactor, sizeImage, isWindow):  
    if resizeFactor != None:
        w = isWindow
        if w == True:
            global originalImage
        getImage = originalImage if w == True else sizeImage
        global height
        height = int(getImage.shape[0]*resizeFactor)
        global width
        width = int(getImage.shape[1]*resizeFactor) 
    return cv2.resize(sizeImage, (width, height)) 

def readImage(file):
    return cv2.imread(str(file), cv2.IMREAD_UNCHANGED).astype(np.float32)/maxColorRange

def showImage(show, image):
    cv2.namedWindow(show)
    cv2.imshow(show, image)
    
def writeImage(show, write, image):
    directory = createDirectory("images") + "\\" + show if show == write else createDirectory(imageName) + "\\" + write + ".png"
    cv2.imwrite(directory, maxColorRange*image)

def showWriteImage(show, write, image):
    showImage(show, image)
    writeImage(show, write, image)
    
def fastFourierTransform2D(image):
    bound = 20 * np.log(np.abs(np.fft.fftshift(np.fft.fft2(cv2.imread(str(image))))) + 1)
    return (maxColorRange * bound / np.max(bound)).astype(np.uint8)

def adjust(value, name, im, isWindow, howAdjust, isAdvanced = None, returnAdjust = False):
    adjustedImage = im if isWindow == True else readImage(im)
    if howAdjust == "resize":
        if not value == None:
            adjustedImage = resize(value, adjustedImage, False if returnAdjust else isWindow)
    elif howAdjust == "rotate":
        value = 360 + value if value < 0 else value
        (height, width) = adjustedImage.shape[:2]
        (centerX, centerY) = (width / 2, height / 2)
        rotationMatrix = cv2.getRotationMatrix2D((centerX, centerY), -value, 1.0)
        cosine = np.abs(rotationMatrix[0, 0])
        sine = np.abs(rotationMatrix[0, 1])
        newWidth = int((height * sine) + (width * cosine))
        newHeight = int((height * cosine) + (width * sine))
        rotationMatrix[0, 2] += (newWidth / 2) - centerX
        rotationMatrix[1, 2] += (newHeight / 2) - centerY
        adjustedImage = cv2.warpAffine(adjustedImage, rotationMatrix, (newWidth, newHeight))
        
    if returnAdjust:
        return adjustedImage
        
    if isWindow == True:
        showWriteImage(name, imageName + "Adjusted", adjustedImage)
        global image
        image = adjustedImage
        if isAdvanced != None:
            isAdvanced.setUpImage(image)
    else:
        global adjustImages
        adjustImages = updateCurrentAdjustedItem(name, howAdjust, value)
        
        if howAdjust == "resize":
            showImage(name, adjustedImage)
        elif howAdjust == "rotate":
            showWriteImage(name, name, adjustedImage) 
            factor, rotate, current = getCurrentAdjustedItem(name)
            rotateLabel.configure(text = "Current degree = " + str(current))

def getCurrentAdjustedItem(currentItemName):
    global adjustImages
    for (name, factor, (current, rotate)) in adjustImages:
        if name == currentItemName:
            return [str(factor), rotate, current]
    return ["", None, None]  

def updateCurrentAdjustedItem(currentItem, valueToUpdate, value):
    global adjustImages  
    return [(name, value if name == currentItem and valueToUpdate == "resize" else factor, ((current + value - 360 if current + value >= 360 else current + value) if name == currentItem and valueToUpdate == "rotate" else current, value if name == currentItem and valueToUpdate == "rotate" else rotate)) for (name, factor, (current, rotate)) in adjustImages]
    
if __name__ == '__main__':
    maxColorRange = 255.0
    isProcessing = False
    while True:
        filePath = os.path.realpath(__file__)
        parent = parentDirectory(filePath)
        check = str(directoryName(parent))
        if check == "src" or check == "python":
            parent = parentDirectory(parent)
            
        selectedImages = [f for f in Path(createDirectory("images")).iterdir()]
        adjustImages = [(selectedImages[i].name, 0.1, (0, 0)) for i in range(len(selectedImages))]
        
        width = 0
        for i in selectedImages:
            w = len(i.name)
            if w > width:
                width = w
                
        select = Tk()
        select.title("Choose Images")
        select.geometry('+200+230') 
        selectLabel = Label(select, text = "Select Images:")
        selectLabel.grid(column = 0, row = 0)
                
        isRemoveImages = False
        selectedItems = []
        removeItems = []
                
        def exitSelect():
            if isRemoveImages == False:
                removeAllWindows()
                select.destroy()
        
        def getSelectedImages(event):
            boxSelected = selectBox.curselection()
            
            if isRemoveImages == True:
                removeUnselected = True
                for s in boxSelected:
                    if s not in selectedItems:
                        if s not in removeItems:
                            selectBox.itemconfig(s, selectbackground = "red")
                            selectBox.selection_set(s, s)
                            removeItems.append(s)
                            removeUnselected = False
                            break
                        
                for s in selectedItems:
                    if s not in boxSelected:
                        if s not in removeItems:
                            selectBox.itemconfig(s, selectbackground = "red")
                            selectBox.selection_set(s, s)
                            removeItems.append(s)
                            removeUnselected = False
                            break
                        else:
                            selectBox.itemconfig(s, selectbackground = "blue")
                            selectBox.selection_set(s, s)
                            removeItems.remove(s)
                            removeUnselected = False
                            break
                
                if removeUnselected == True:
                    for i in range(len(selectedImages)):
                        if i not in boxSelected:
                            if i in removeItems:
                                removeItems.remove(i)
                                removeUnselected = False
                                break
                print(boxSelected)
            else:                
                for s in boxSelected:
                    if s not in selectedItems:
                        selectBox.itemconfig(s, selectbackground = "blue")
                        selectedItems.append(s)
                        
                isRemoved = False
                for s in selectedItems:
                    if s not in boxSelected:
                        selectedItems.remove(s)
                        cv2.destroyWindow(selectBox.get(s))
                        isRemoved = True
                        
                adjustSelected['values'] = [""] if selectedItems == [] else [selectedImages[s].name for s in selectedItems]
                adjustSelected.current(0)
                
                adjustedItems = adjustItems()
                
        #         if isRemoved == False:
        #             #fourier = fastFourierTransform2D(selectedImages[getAdjustedIndex()])
        #             gray = cv2.cvtColor(cv2.imread(str(selectedImages[getAdjustedIndex()])), cv2.COLOR_BGR2GRAY)
        #             edges = cv2.Canny(gray, 100, 100, apertureSize = 3)
        #             lines = cv2.HoughLinesP(edges, 1, math.pi / 180.0, 100, minLineLength = 100, maxLineGap = 5)
        #             angles = []
        #             
        #             for x1, y1, x2, y2 in lines[0]:
        #                 angle = math.degrees(math.atan2(y2 - y1, x2 - x1))
        #                 angles.append(angle)
        #             
        #             medianAngle = np.median(angles)
        #             medianAngle = 360 + medianAngle if medianAngle < 0 else medianAngle
        #             global adjustImages
        #             adjustImages = updateCurrentAdjustedItem(adjustSelected.get(), "rotate", medianAngle)
        #         
                factor, rotate, current = getCurrentAdjustedItem(adjustSelected.get())
                
                factorValue.delete(0, END)
                rotateValue.delete(0, END)
                rotateLabel.configure(text = "Current degree = ")
                
                for a in range(len(adjustedItems)):
                    b = adjustedItems[a]
                    b["state"] = "disabled" if selectedItems == [] else "normal" 
                    
                if selectedItems != []:
                    factorValue.insert(0, factor)
                    rotateValue.insert(0, rotate)
                    rotateLabel.configure(text = "Current degree = " + str(current))
                    
        def adjustItems(*args):
             return [showSelected, factorValue, resizeButton, rotateValue, rotateButton, *args]   
         
        def clearSelected(event):
            if (event.state & 0x4) != 0: #checks ctrl+
                k = event.keycode
                if k == 68: #checks d
                    if isRemoveImages == True:
                        return
                    else:
                        selectBox.selection_clear(0, END)
                        for i in selectedImages:
                            getSelectedImages(event)
                elif k == 65:
                    if isRemoveImages == True:
                        for i in selectBox.curselection():
                            return#getSelectedImages(event)
        
        def updateSelected(event):
            factor, rotate, current = getCurrentAdjustedItem(adjustSelected.get())
            factorValue.delete(0, END)
            rotateValue.delete(0, END)
            factorValue.insert(0, factor)
            rotateValue.insert(0, rotate)
            rotateLabel.configure(text = "Current degree = " + str(current))
        
        def getAdjustedIndex():
            for s in selectedItems:
                if selectBox.get(s) == adjustSelected.get():
                    return s
            return -1
        
        def removeSelectedImages():
            global isRemoveImages
            adjustedItems = adjustItems(ok, add, adjustSelected)
            if isRemoveImages == True:
                isRemoveImages = False
                removeImage['fg'] = "black"
                for a in adjustedItems:
                    a["state"] = "normal"
            else:
                isRemoveImages = True
                removeImage['fg'] = "red"
                for a in adjustedItems:
                    a["state"] = "disabled"
            
    #         for s in selectedImages:
    #             selectBox.delete(s, s)
        
        def addFile():
            file = askopenfilename()
            if file != "":
                name = file[file.rfind("/")+1:]
                writeImage(name, name, readImage(file))
                global isProcessing
                isProcessing = True
                exitSelect()
            
        selectBox = Listbox(select, selectmode = MULTIPLE, width = width, height = len(selectedImages), exportselection = False)
        for i in selectedImages:
            selectBox.insert('end', i.name)
        selectBox.grid(column = 1, row = 0)
        selectBox.bind("<<ListboxSelect>>", getSelectedImages)
        selectBox.bind("<Key>", clearSelected)
        
        scrollSelect = Scrollbar(select, orient = "vertical", command = selectBox.yview)
        selectBox.configure(yscrollcommand = scrollSelect.set)
                    
        add = Button(select, text = "Add", command = addFile)
        add.grid(column = 2, row = 0)
        
        showSelected = Button(select, text = "Show", command = lambda : adjust(None, adjustSelected.get(), selectedImages[getAdjustedIndex()], False, "resize"), state = "disabled")
        showSelected.grid(column = 0, row = 1)
        
        removeImage = Button(select, text = "Remove", command = removeSelectedImages)
        removeImage.grid(column = 1, row = 1)
        
        adjustSelectedLabel = Label(select, text = "Selected images:")
        adjustSelectedLabel.grid(column = 0, row = 2)
        adjustSelected = Combobox(select, width = width, values = [selectBox.get(s) for s in selectedItems], state = "readonly")
        adjustSelected.grid(column = 1, row = 2)
        adjustSelected.bind("<<ComboboxSelected>>", updateSelected)
        
        factorLabel = Label(select, text = "Resize factor:")
        factorLabel.grid(column = 0, row = 3)
        factorValue = Entry(select, width = 10, state = "disabled")
        factorValue.bind("<Key>", lambda event : checkValue(event, False))
        factorValue.grid(column = 1, row = 3)
        resizeButton = Button(select, text = "Resize", command = lambda : adjust(processValue(factorValue.get()), adjustSelected.get(), selectedImages[getAdjustedIndex()], False, "resize"), state = "disabled")
        resizeButton.grid(column = 2, row = 3)
        
        rotateLabel = Label(select, text = "Current degree = ")
        rotateLabel.grid(column = 0, row = 4)
        rotateValue = Combobox(select, values = [r for r in range(361)], state = "disabled")
        rotateValue.grid(column = 1, row = 4)
        rotateValue.bind("<Key>", lambda event : checkValue(event, True))
        rotateButton = Button(select, text = "Rotate", command = lambda : adjust(processValue(rotateValue.get()), adjustSelected.get(), selectedImages[getAdjustedIndex()], False, "rotate"), state = "disabled")
        rotateButton.grid(column = 2, row = 4)
        
        ok = Button(select, text = "Ok", command = exitSelect)
        ok.grid(column = 0, row = 5)
        
        select.protocol("WM_DELETE_WINDOW", exitSelect)
        select.mainloop()
        
        selectedImages = [selectedImages[s] for s in selectedItems]
            
        f = 0
        while f < len(selectedImages):
            o = selectedImages[f]
            imageName = o.name[:-4]
            
            originalImage = readImage(o)
            width = 0
            height = 0
            hexIndex = 1
            image = resize(0.1, originalImage, False)
            
            countWindows = 0
            windows = [("normal", 0), ("normal", 2), ("normal", 4), ("normal", 5), ("normal", 6)]
            
            def processImage(p):
                return rgbProcess(p, -1, -1, -1, None)
            
            def processConvolve(size, kernel):    
                return rgbProcess("convolve", -1, -1, size, kernel)
            
            def rgbProcess(p, r, g, b, kernel):
                def getHeight():
                    return image.shape[0] if height > image.shape[0] else height
                def getWidth():
                    return image.shape[1] if width > image.shape[1] else width
                h = 0
                w = 0
                if p == "convolve":
                    h = getHeight() - 1
                    w = getWidth() - 1
                else:
                    h = getHeight()
                    w = getWidth()
                length = image.shape[2]
                newImage = np.zeros((h, w, length), np.float32)/maxColorRange
                if r > -1 and g > -1 and b > -1:
                    getRGB = [b, g, r, 1]
                for i in range(h):
                    for j in range(w):
                        pixel = image[i, j]
                        if p == "invert":
                            newImage[i, j] = [1 - pixel[p] if p < 3 else maxColorRange for p in range(length)]
                        elif p == "rgbMul":
                            newImage[i, j] = [getRGB[p]*pixel[p] for p in range(length)]
                        elif p == "contrast":
                            newImage[i, j] = [(((pixel[p]-0.33)*3) if pixel[p]-0.5 > 0 else pixel[p]) if p < 3 else maxColorRange for p in range(length)]
                        elif p == "convolve":
                            newImage[i, j] = calculateConvolution(i, j, b, kernel, length)
                return newImage
            
            def calculateConvolution(i, j, kernelSize, kernel, length):
                #kernelSize refers to kernel of KxK, or 3 in this case
                originalTop = 0 if i == 0 else i - 1
                originalBottom = height if i == height - 1 else i + 2
                originalLeft = 0 if j == 0 else j - 1
                originalRight = width if j == width - 1 else j + 2
                
                kernelTop = 1 if i == 0 else 0
                kernelBottom = kernelSize - 1 if i == height - 1 else kernelSize
                kernelLeft = 1 if j == 0 else 0
                kernelRight = kernelSize - 1 if j == width - 1 else kernelSize 
                
                convolution = np.zeros((1, 1, length), np.float32)/maxColorRange   
                for originalX, kernelX in zip(range(originalTop, originalBottom), range(kernelTop, kernelBottom)):
                    for originalY, kernelY in zip(range(originalLeft, originalRight), range(kernelLeft, kernelRight)):
                        convolution += [kernel[kernelSize*kernelX+kernelY]*image[originalX, originalY, p] for p in range(length)] 
                return convolution
            
            def adjustImage(name):
                addWindow()      
                setAdjust = Tk()
                setAdjust.title(name)
                setAdjust.geometry('+580+230')
                
                def cancelAdjust():
                    if cancelA["state"] == "normal":
                        cancelWindow(setAdjust, 0)
                                        
                def advanced():
                    edits = setAdjust.winfo_children()  
                    for b in edits:    
                        b["state"] = "disabled"  
                    setAdvanced.setIsAdvanced()
                    AdvancedGui(setAdvanced, edits = edits, adjust = adjust)
                    
                adjust(None, name, image, True, "resize")
                setAdvanced = Advanced(name, image.copy(), 2, False)            
                
                factorLabel = Label(setAdjust, text = "Resize factor:")
                factorLabel.grid(column = 0, row = 0)
                factor = Entry(setAdjust, width = 10)
                factor.insert(0, "0.1")
                factor.bind("<Key>", lambda event : checkValue(event, False))
                factor.grid(column = 1, row = 0)
                
                rotateLabel = Label(setAdjust, text = "Rotate degree:")
                rotateLabel.grid(column = 2, row = 0)
                rotateValue = Combobox(setAdjust, values = [r for r in range(361)])
                rotateValue.current(0)
                rotateValue.grid(column = 3, row = 0)
                rotateValue.bind("<Key>", lambda event : checkValue(event, True))
                        
                resizeButton = Button(setAdjust, text = "Resize", command = lambda : adjust(processValue(factor.get()), name, image, True, "resize", setAdvanced))
                resizeButton.grid(column = 0, row = 1)
                rotate = Button(setAdjust, text = "Rotate", command = lambda : adjust(processValue(rotateValue.get()), name, image, True, "rotate"))
                rotate.grid(column = 2, row = 1)
                
                advancedButton = Button(setAdjust, text = "Advanced", command = advanced)
                advancedButton.grid(column = 3, row = 1)
                
                cancelA = Button(setAdjust, text = "Cancel", command = cancelAdjust)
                cancelA.grid(column = 4, row = 1)
                setAdjust.protocol("WM_DELETE_WINDOW", cancelAdjust)  
                setAdjust.mainloop()
        
            def invertImage(name):
                name = str(name)
                index = name.find(" Image")
                name = name[:index] + "ed" + name[index:]
                showWriteImage(name, imageName + "Inverted", processImage("invert"))
            
            def setRGBMultiplicationValues(name):
                addWindow()
                values = Tk()
                values.title("Set RGB Values")
                values.geometry('+680+230')
            
                def cancelValues():
                    cancelWindow(values, 1)
            
                labels = ["red", "green", "blue"]
                presetValues = [0.9, 0.5, 0.9]
                colors = [Entry, Entry, Entry]
                a = 0
                while a < 3:
                    label = Label(values, text = labels[a] + " = ")
                    label.grid(column = 0, row = a)  
                    color = Entry(values, width = 10)  
                    color.insert(0, presetValues[a])  
                    color.grid(column = 1, row = a) 
                    color.bind("<Key>", lambda event : checkValue(event, False))
                    colors[a] = color
                    a += 1
                ok = Button(values, text = "Ok", command = lambda : rgbMultiplicationImage(name, processValue(colors[0].get()), processValue(colors[1].get()), processValue(colors[2].get())))
                ok.grid(column = 0, row = a)
                cancelV = Button(values, text = "Cancel", command = cancelValues)
                cancelV.grid(column = 1, row = a)
                values.protocol("WM_DELETE_WINDOW", cancelValues)  
                values.mainloop() 
            
            def rgbMultiplicationImage(name, r, g, b):
                name = str(name)
                n = name.split(" ")
                name = n[0] + " " + n[2] + " " + n[1]
                showWriteImage(name, imageName + "RGBMultiplication", rgbProcess("rgbMul", r, g, b, None))
            
            def contrastImage(name):
                showWriteImage(name, imageName + "Contrast", processImage("contrast"))
            
            def setConvolve(name):
                addWindow()
                conv = Tk()
                conv.title(name)
                conv.geometry('+780+230')
            
                def cancelConvolve():
                    cancelWindow(conv, 2)
                
                combo = Label(conv, text = "Set convolution:")
                combo.grid(column = 0, row = 0)
                convCombo = Combobox(conv, state = "readonly")
                convCombo['values'] = ("Box Blur", "Gaussian Blur", "Sharpening", "Vertical Sobel", "Horizontal Sobel")
                convCombo.current(0)
                convCombo.grid(column = 1, row = 0)
                convolveOk = Button(conv, text = "Convolve", command = lambda : convolveImage(name, convCombo.get()))
                convolveOk.grid(column = 0, row = 1)         
                cancelV = Button(conv, text = "Cancel", command = cancelConvolve)
                cancelV.grid(column = 1, row = 1)
                conv.protocol("WM_DELETE_WINDOW", cancelConvolve)  
                conv.mainloop() 
            
            def convolveImage(name, operation):
                size = 3
                total = size*size
                kernel = [0 for k in range(total)]
                for k in range(total):
                    if operation == "Box Blur":
                        kernel[k] = 1/9
                    elif operation == "Gaussian Blur":
                        kernel[k] = (1 if k == 0 or k == size - 1 or k == total - size or k == total - 1 else 2 if k % size == 0 or (k+1) % size == 0 or (k > 0 and k < size - 1) or (k > total - size and k < total - 1) else 4)/16
                    elif operation == "Sharpening":
                        kernel[k] = 0 if k == 0 or k == size - 1 or k == total - size or k == total - 1 else -1 if k % size == 0 or (k+1) % size == 0 or (k > 0 and k < size - 1) or (k > total - size and k < total - 1) else 5
                    elif operation == "Vertical Sobel":
                        kernel[k] = (1 if k == 0 or k == size - 1 or k == total - size or k == total - 1 else 0 if (k-1) % size == 0 else 2)*(-1 if k % size == 0 else 1)
                    elif operation == "Horizontal Sobel":
                        kernel[k] = (1 if k == 0 or k == size - 1 or k == total - size or k == total - 1 else 0 if (k >= size and k < total - size) else 2)*(-1 if (k >= 0 and k < size) else 1)
                showWriteImage(name + " " + operation, imageName + "Convolve - " + operation, processConvolve(size, kernel))
            
            def toneMapping(name):
                addWindow()
                map = Tk()
                map.title(name)
                map.geometry('+880+230')
            
                def cancelMap():
                    cancelWindow(map, 3)
                            
                def generateHexIndex():
                    global hexIndex
                    start = int(constant**(np.floor(np.log(hexIndex)/np.log(constant))))
                    remainder = -1
                    checkHex = 0
                    hex = ""
                    while remainder < 0 or remainder > 15:    
                        remainder = hexIndex % start
                        checkHex = int(np.floor(hexIndex/start))
                        hex = hex + (hexSymbols[checkHex-10] if checkHex > 9 else str(checkHex))
                        if hexIndex >= constant:
                            hex += str(remainder)
                        start //= constant
                    hexIndex += 1
                    zeros = ""
                    for z in range(3-len(hex)):
                        zeros += "0"
                    return "I" + zeros + hex
                
                constant = 16
                hexSymbols = ["A", "B", "C", "D", "E", "F"]    
                exclude = ["bin", "jars", "python", "src"]
                find = [[(f, generateHexIndex()), [(i, generateHexIndex()) for i in Path(createDirectory(f.name)).iterdir() if i != o]] for f in Path(createDirectory("")).iterdir() if isDirectory(f) and f.name[0] != "." and f.name not in exclude]
        
                secondLabel = Label(map, text = "Choose another image:")
                secondLabel.grid(column = 0, row = 0)
                secondTree = Treeview(map, selectmode = "browse")
                secondTree.column("#0", width = 300, stretch = NO)
                secondTree.heading("#0", text = "Name", anchor = W)
                
                for f in range(len(find)):
                    (path, pathIndex), fileImages = find[f]
                    folder = secondTree.insert("", f+1, text = path.name)
                    for (i, imageIndex) in fileImages:
                        secondTree.insert(folder, "end", text = i.name)
                  
                secondTree.grid(column = 1, row = 0)
                scrollY = Scrollbar(map, orient = "vertical", command = secondTree.yview)
                secondTree.configure(yscrollcommand = scrollY.set)
                scrollX = Scrollbar(map, orient = "horizontal", command = secondTree.xview)
                scrollX.place(x = 127, y = 210, width = 315)
                secondTree.configure(xscrollcommand = scrollX.set)
                
                def hexIndex():
                    return secondTree.selection()[0]
                
                def getSecondImage():
                    for f in range(len(find)):
                        (path, pathIndex), fileImages = find[f]
                        for (i, imageIndex) in fileImages:
                            if imageIndex == hexIndex():
                                s = resize(None, readImage(i), True)
                                showImage("Second Image", s)
                                return s
                    return None
                
                mapOk = Button(map, text = "Ok", command = lambda : mapImages(image, getSecondImage(), name))
                mapOk.grid(column = 0, row = 1)         
                cancelM = Button(map, text = "Cancel", command = cancelMap)
                cancelM.grid(column = 1, row = 1)
                
                def checkSelect(event):
                    fileImage = hexIndex()
                    folder = secondTree.parent(fileImage)
                    mapOk.configure(state = "normal" if folder else "disabled")
                    
                secondTree.bind("<<TreeviewSelect>>", checkSelect)
                map.protocol("WM_DELETE_WINDOW", cancelMap)  
                map.mainloop() 
                
            def mapImages(first, second, name):
                getImages = [first, second]
                mapFirst = computeMeanStandardDeviation(first)
                mapSecond = computeMeanStandardDeviation(second)
                values = [mapFirst, mapSecond]
                for i in range(2):
                    for j in range(2):
                        index = str((2*i+j)+1)
                        mappedImage = computeMappedImage(values[i], values[1 if i == 0 else 0], getImages[j])
                        showWriteImage(name + " " + index, imageName + "Map" + index, mappedImage)
                        
            def computeMappedImage(old, new, computeMapImage):
                oldAverage, oldStandardDeviation = old
                newAverage, newStandardDeviation = new
                for i in range(height):
                    for j in range(width):
                        for k in range(3):
                            computeMapImage[i, j, k] = (newStandardDeviation[k]/oldStandardDeviation[k])*(computeMapImage[i, j, k]-oldAverage[k]) + newAverage[k]
                return computeMapImage
            
            def computeMeanStandardDeviation(computeImage):
                average = np.zeros(3, np.float32)/maxColorRange
                count = 0
                for i in range(height):
                    for j in range(width):
                        for k in range(3):
                            average[k] += computeImage[i, j, k]
                        count += 1
                for a in range(3):
                    average[a] /= count
                standardDeviation = np.zeros(3, np.float32)/maxColorRange
                for i in range(height):
                    for j in range(width):
                        for k in range(3):
                            standardDeviation[k] += abs(computeImage[i, j, k] - average[k])**2
                for s in range(3):
                    standardDeviation[s] = (standardDeviation[s] / count)**(1/2)
                return [average, standardDeviation] 
            
            def setBilateralFilter(name):
                addWindow()
                bi = Tk()
                bi.title(name)
                bi.geometry('+980+230') 
                
                def cancelBi():
                    cancelWindow(bi, 4)
                     
                labels = ["Pixel Neighborhood Diameter", "Sigma Color Space", "Sigma Coordinate Space"]
                presetValues = [15, 75, 75]
                biArgs = [Entry, Entry, Entry]
                b = 0
                while b < 3:
                    label = Label(bi, text = labels[b] + " = ")
                    label.grid(column = 0, row = b)  
                    arg = Entry(bi, width = 10)  
                    arg.insert(0, presetValues[b])  
                    arg.grid(column = 1, row = b) 
                    arg.bind("<Key>", lambda event : checkValue(event, False, "int"))
                    biArgs[b] = arg
                    b += 1
                ok = Button(bi, text = "Ok", command = lambda : bilateralFilter(name, processValue(biArgs[0].get(), int), processValue(biArgs[1].get(), int), processValue(biArgs[2].get(), int)))
                ok.grid(column = 0, row = b)
                cancelB = Button(bi, text = "Cancel", command = cancelBi)
                cancelB.grid(column = 1, row = b)
                bi.protocol("WM_DELETE_WINDOW", cancelBi)  
                bi.mainloop() 
            
            def bilateralFilter(name, pixelNeighborhoodDiameter, sigmaColorSpace, sigmaCoordinateSpace):
                bilateralImage = cv2.bilateralFilter(image, pixelNeighborhoodDiameter, sigmaColorSpace, sigmaCoordinateSpace) 
                showWriteImage(name, imageName + "Bilateral", bilateralImage)
    
            imageProcessing = Tk()
            imageProcessing.title("Image Processing - " + imageName)
            imageProcessing.geometry('+500+230') 
            
            def cancelImageProcessing():
                if cancel["state"] == "normal":
                    imageProcessing.destroy()   
                    removeAllWindows()
                    
            def goBack():
                global f
                f -= 2
                cancelImageProcessing()
                    
            imageLabel = Label(imageProcessing, text = "Select image operation:")
            imageLabel.grid(column = 0, row = 0)
            names = ["Adjust", "Invert", "RGB Multiplication", "Contrast", "Convolve", "Tone Mapping", "Bilateral Filter"]
            imageCombo = Combobox(imageProcessing, width = 20, values = [n + " Image" for n in names], state = "readonly")
            imageCombo.current(0)
            imageCombo.grid(column = 1, row = 0)
            
            def updateText(event):
                combo = event.widget
                process.configure(text = combo.get(), command = lambda : operations[combo.current()](combo.get()), state = getWindowState())
            
            imageCombo.bind("<<ComboboxSelected>>", updateText)
            operations = [adjustImage, invertImage, setRGBMultiplicationValues, contrastImage, setConvolve, toneMapping, setBilateralFilter]
            process = Button(imageProcessing, text = imageCombo.get(), command = lambda : operations[imageCombo.current()](imageCombo.get()))
            process.grid(column = 0, row = 1)
            cancel = Button(imageProcessing, text = "Cancel" if f == len(selectedImages)-1 else "Continue", command = cancelImageProcessing)
            cancel.grid(column = 1, row = 1)
            back = Button(imageProcessing, text = "Back", command = goBack)
            back.grid(column = 2, row = 1)
            imageProcessing.protocol("WM_DELETE_WINDOW", cancelImageProcessing)
            imageProcessing.mainloop()
            f += 1
            if f == -1:
                isProcessing = True
                break
        if isProcessing == False:
            break
        else:
            isProcessing = False