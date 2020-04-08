from cv2 import *
import numpy as np
from tkinter.filedialog import askopenfilename

class ColorDifference:
    def __init__(self, name, image):
        self.name = name
        self.image = image
        self.imageCopy = image.copy()
        self.luminancePoints = [("White",[]),("Black",[])]
        self.isMouseCall = True
        self.quality = False
        self.shadows = False
        self.show(name)
        
    def substitution(self):
        def sub(y, x):
            r, g, b, a = self.getValues(self.imageCopy[y, x])
            if b > g:
                self.imageCopy[y, x] = self.checkNewPixel(g, g, r, a)
            elif g > b:
                self.imageCopy[y, x] = self.checkNewPixel(b, b, r, a)
        h, w, _ = self.imageCopy.shape
        print(self.name, "Substituting")
        [sub(y, x) for x in range(w) for y in range(h)]
        self.showWrite("Substitution")
        
    def swapBlueGreen(self):
        def swap(y, x):
            r, g, b, a = self.getValues(self.imageCopy[y, x])
            if b > g or g > b:
                if self.__color == "":
                    self.__color = "Green" if b > g else "Blue"
                self.imageCopy[y, x] = self.checkNewPixel(g, b, r, a)
        self.__color = ""
        h, w, _ = self.imageCopy.shape
        print(self.name, "Swapping")
        [swap(y, x) for x in range(w) for y in range(h)]
        self.showWrite("Swap" + self.__color)
        self.__color = ""
        
    def __maximum(self, a, b):
        return a if a > b else b
    
    def __getMatte(self, r, g, b):
        return b-self.__maximum(g, r)
        
    def extractMatte(self, isMatteNegative = False):
        def extract(y, x):
            r, g, b, a = self.getValues(self.image[y, x])
            matte = self.__getMatte(r, g, b)
            if isMatteNegative:
                if matte < 0:
                    matte *= -1
            self.imageCopy[y, x] = self.checkNewPixel(matte, matte, matte, a)
        h, w, _ = self.imageCopy.shape
        print(self.name, "Extracting Matte Edit Negatives " + str(isMatteNegative))
        [extract(y, x) for x in range(w) for y in range(h)]
        self.showWrite("MatteExtraction" + str(isMatteNegative))
        
    def __lumi(self, r, g, b):
        def linear(c):
            if c <= 0.04045:
                return c / 12.92
            else:
                return ((c+0.055)/1.055)**(2.4)
        luminance = 0.2126*linear(r) + 0.7152*linear(g) + 0.0722*linear(b)
        if luminance <= (216/24389):
            luminance = luminance*(24389/27)
        else:
            luminance = (luminance**(1/3))*116-16
        return luminance
        
    def luminance(self, lum = 7.5):
        def getL(y, x):
            r, g, b, a = self.getValues(self.imageCopy[y, x])
            lumi = self.__lumi(r, g, b)
            lumi = lumi if lumi >= lum else 0
            self.luminancePoints[1 if lumi == 0 else 0][1].append((y, x))
            self.imageCopy[y, x] = self.checkNewPixel(lumi, lumi, lumi, a)
        self.clearLuminance()
        h, w, _ = self.imageCopy.shape
        print(self.name, "Luminance " + str(lum))
        [getL(y, x) for x in range(w) for y in range(h)]
        self.showWrite("Luminance" + str(lum))
        
    def clearLuminance(self):
        for i in range(2):
            self.luminancePoints[i][1].clear()   
                 
    def changeColors(self, c = "Background"):
        def change(y, x):
            r, g, b, a = self.getValues(self.imageCopy[y, x])
            ir, ig, ib, ia = self.getValues(im[y, x])
            m = self.__getMatte(r, g, b)
            if m < 0:
                m *= -1
            values = [abs(m-v) for v in [0, 0.4]]
            d = values[1] < values[0] if c == "Background" else values[0] < values[1]
            if d:
                self.imageCopy[y, x] = self.checkNewPixel(ib, ig, ir, a)
                if self.quality:
                    points.remove((y,x))
                if self.shadows:
                    if (y, x) in self.luminancePoints[1][1]:
                        self.imageCopy[y, x] = self.checkNewPixel(0, 0, 0, a)
                    
        file = askopenfilename()
        if file != "":
            im = cv2.imread(file, cv2.IMREAD_UNCHANGED).astype(np.float32)/255.0
            h, w, _ = self.imageCopy.shape
            im = cv2.resize(im, (w, h))
            points = []
            if self.quality or self.shadows:
                points = [(y, x) for x in range(w) for y in range(h)]
            print(self.name, "Changing " + c)
            [change(y, x) for x in range(w) for y in range(h)]
            q = ""
            for (s, b) in [("Quality", self.quality), ("Shadows", self.shadows)]:
                if b:
                    print(self.name, "Changing " + s)
                    q += s
            if len(points) > 0:
                for (y, x) in points:
                    r, g, b, a = self.getValues(self.image[y, x])
                    self.imageCopy[y, x] = self.checkNewPixel(b, g, r, a)
            self.show(c + "Change" + q)
            file = file[:file.rfind(".")]
            file += c + "Change" + q + self.name
            self.write(file)
            
    def fixQuality(self):
        self.quality = not self.quality
        print(self.name, "Fix Quality " + str(self.quality))
        
    def getShadows(self):
        self.shadows = not self.shadows
        print(self.name, "Get Shadows " + str(self.shadows))
        
    def show(self, show):  
        cv2.namedWindow(show)
        cv2.setMouseCallback(show, self.mouseCallback)
        cv2.imshow(show, self.imageCopy)  
        
    def write(self, write): 
        cv2.imwrite(write + ".png", self.imageCopy*255.0 if self.imageCopy.shape[2] == 4 else self.imageCopy)
    
    def showWrite(self, showWrite):
        showWrite = self.name + showWrite
        self.show(showWrite)
        self.write(showWrite)
        
    def reset(self):
        self.imageCopy = self.image.copy()
        print(self.name, "Reset")
        self.showWrite("")
        
    def getValues(self, pixel):
        if len(pixel) == 4:
            b, g, r, a = pixel
            return (r, g, b, a)
        else:
            b, g, r = pixel
            return (r, g, b, None)
        
    def mouseCallback(self, event, x, y, flags, param):
        if self.isMouseCall and event == cv2.EVENT_MOUSEMOVE:
            r, g, b, a = self.getValues(self.imageCopy[y, x])
            m = b-self.__maximum(g, r)
            print((x, y), "->", m, "->", self.__lumi(r, g, b), "->", (r, g, b))
        elif event == cv2.EVENT_RBUTTONDOWN:
            self.isMouseCallBack()
            
    def isMouseCallBack(self):
        self.isMouseCall = not self.isMouseCall
        print(self.name, "Mouse call back is " + str(self.isMouseCall))
            
    def checkNewPixel(self, b, g, r, a):
        arr = [b, g, r] 
        if a != None:
            arr += [a]
        return np.array(arr, dtype = np.float32)
        
if __name__ == '__main__':
    def performColorDifference():
        ok = cv2.waitKey(0) % 256
        if ok == ord('n'):
            c.extractMatte(True)
            performColorDifference()
        elif ok == ord('f'):
            c.changeColors("Foreground")
            performColorDifference()
        elif ok == ord('i'):
            c.luminance(float(input("Compare luminance against: ")))
            performColorDifference()
        else:
            perform = [('s', c.substitution), ('w', c.swapBlueGreen), ('m', c.extractMatte), ('b', c.changeColors), ('q', c.fixQuality), ('h', c.getShadows), ('l', c.luminance), ('c', c.clearLuminance), ('r', c.reset), ('e', c.isMouseCallBack)]
            for (p, method) in perform:
                if ok == ord(p):
                    method()
                    performColorDifference()
                    break
            
    names = ["skullLuminance.png", "dogGreenscreen.png", "skullBluescreen.png"]
    sizes = [1, 1, 1]
    for m in range(len(sizes)):
        n = names[m]
        image = cv2.imread(n, cv2.IMREAD_UNCHANGED).astype(np.float32)/255.0
        imh, imw, _ = image.shape
        r = sizes[m]
        imh = int(r*imh)
        imw = int(r*imw)
        image = cv2.resize(image, (imw, imh))
        c = ColorDifference(n[:n.find(".")], image)
        performColorDifference()
    cv2.waitKey(0)