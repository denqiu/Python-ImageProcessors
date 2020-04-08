from tkinter import *
from tkinter.filedialog import askopenfilename
from cv2 import *
from points import Point
import numpy as np
from numpy import dtype
from math import *
from textbox import Numbox

class Advanced:
    def __init__(self, name, image, setZoom = 1, isAdvanced = True):
        self.name = name
        self.brush = 3
        self.exitPoint = Point()
        self.currentPoint = "P = (x, y) -> (r,g,b)"
        self.warp = None
        self.__action = None
        self.__buttons = None
        self.__actionButtons = None
        self.__paint = False
        self.__brush = False
        self.__startBrush = False
        self.stopCopy = True
        self.startWarp = False
        self.setUpImage(image)
        self.copiedSelection = []
        self.placedImages = []
        self.points = []
        self.beforeImage = []
        self.setBoundaryColor()
        self.isAdvanced = isAdvanced
        self.setZoomFactor(setZoom)
        cv2.setMouseCallback(name, self.__doAdvanced)
                
    def __doAdvanced(self, event, x, y, flags, param):
        if self.isAdvanced:
            newPoint = Point(x, y)
            if event == cv2.EVENT_LBUTTONUP:
                if self.__brush:
                    self.__startBrush = not self.__startBrush
                if self.stopCopy or len(self.copiedSelection) == 0:
                    points = self.warpPoints if self.startWarp else self.points
                    if len(points) > 1 and points[0].getPoint() == points[-1].getPoint():
                        return
                    newPoint = self.__setNewPoint(newPoint, len(points), self.startX, self.startY, self.color)
                    points.append(newPoint)
                    if not self.__paint:
                        if len(points) > 0:
                            p = points[-1]
                            if len(points) > 1:
                                a = points[0]
                                dX = abs(a.x-p.x)
                                dY = abs(a.y-p.y)
                                if dX < 5 and dY < 5:
                                    points[-1].setPoint(points[0])
                                    if self.startWarp:
                                        self.refreshWarp()
                                    return
                            self.__createLine(p, newPoint)
                    self.__createPoint(newPoint, self.color)
                    if self.startWarp:
                        self.refreshWarp()
                else:
                    newPoint.setImage(self.copiedSelection)
                    newPoint.setIndex(len(self.placedImages))
                    newPoint.setName("Copy")
                    self.placedImages.append(newPoint)
                    self.__action(self.__placeImage, newPoint)          
                self.showImage() 
            elif event == cv2.EVENT_MOUSEWHEEL:
                dTop = y
                dBottom = self.height-y
                dLeft = x
                dRight = self.width-x
                distances = [("top", dTop), ("bottom", dBottom), ("left", dLeft), ("right", dRight)]
                if dTop != dBottom != dLeft != dRight:
                    v = self.__max(dTop, dBottom)
                    h = self.__max(dLeft, dRight)
                    distances = list(filter(lambda d : v in d or h in d, distances))
                for (d, value) in distances:
                    self.__zoomImage(d, flags > 0)
                self.__linePoints(self.points)
                self.showImage() 
                self.__setBeforeImageCopy()
            elif event == cv2.EVENT_MOUSEMOVE:
                r, g, b, a = self.__checkPixel(self.imageCopy[y, x])
                self.currentPoint = "P = (x = {}, y = {}) -> (r = {}, g = {}, b = {})".format(x, y, r*255, g*255, b*255)
                exitTop = y == 0 and x < self.width
                exitBottom = y == self.height-1 and x%self.width < self.width
                exitLeft = x == 0 and y < self.height
                exitRight = x == self.height-1 and y < self.height
                if exitTop or exitBottom or exitLeft or exitRight:
                    self.exitPoint.setPoint(newPoint)
                if len(self.beforeImage) > 0:
                    self.imageCopy = self.beforeImage
                    self.showImage()
                self.__setBeforeImageCopy()
                if self.__paint:
                    if self.__brush:
                        if self.__startBrush:
                            newPoint = self.__setNewPoint(newPoint, len(self.points), self.startX, self.startY, self.color)
                            newPoint.setName("brush")
                            self.points.append(newPoint)
                    fillPoints = list(filter(lambda p : p.visible, self.points))
                    for f in fillPoints:
                        self.__createPoint(f, f.color, expand = self.brush)
                else:
                    self.__setLines(self.points, newPoint)
                if self.startWarp:
                    self.__setLines(self.warpPoints, newPoint)
                self.placedImages = sorted(self.placedImages, key = lambda p : p.index)
                for i in self.placedImages:
                    if i.visible:
                        self.__placeImage(i)
                if len(self.copiedSelection) > 0 and not self.stopCopy:
                    newPoint.setImage(self.copiedSelection)
                    self.__placeImage(newPoint)
                if self.__paint:
                    cv2.waitKey(1)
                self.showImage()
            elif event == cv2.EVENT_RBUTTONUP:
                r, g, b, a = self.__checkPixel(self.imageCopy[y, x])
                self.color = (r, g, b, a)

    def __setLines(self, points, newPoint):
        getPoints = points[:len(points)]  
        if len(getPoints) < 2:     
            newPoint = self.__setNewPoint(newPoint, len(points), self.startX, self.startY, self.color)                             
            getPoints.append(newPoint)
        else:
            if getPoints[0].getPoint() != getPoints[-1].getPoint():
                newPoint = self.__setNewPoint(newPoint, len(points), self.startX, self.startY, self.color)
                getPoints.append(newPoint)
        self.__linePoints(getPoints)
               
    def __setNewPoint(self, newPoint, index, zX, zY, color):
        newPoint.setIndex(index)
        newPoint.setZoom(zX, zY)
        newPoint.setColor(color)
        return newPoint
    
    def __placeImage(self, o):
        def setPoint(i, j):
            p = Point(i+o.y, j+o.x)
            r, g, b, a = self.__checkPixel(o.image[i, j])
            p.setColor((r, g, b, a))
            return p
        h, w, _ = o.image.shape
        points = [setPoint(i, j) for j in range(w) for i in range(h) if i+o.y < self.height and j+o.x < self.width and Point(i+o.y, j+o.x)]
        for k in points:
            r, g, b, a = k.color
            if self.isNotPointOutOfBounds(r, g, b, w, h, k):
                self.imageCopy[k.x, k.y] = self.__newPixel(r, g, b, a, len(self.imageCopy[k.x, k.y]))
                
    def isNotPointOutOfBounds(self, r, g, b, w, h, p):
        def isInBounds(x, y):
            isR, isG, isB, a = self.__checkPixel(self.image[x, y])
            return (isR, isG, isB) == (r, g, b)
        notOut = True
        if r == g == b == 0.0:
            next = self.moveToNextPoints(p, w, h)
            next = [(x, y) for (x, y) in next if isInBounds(x, y)]
            notOut = len(next) > 0
        return notOut

    def moveToNextPoints(self, p, w, h):
        left = p.x-1 if p.x-1 > 0 else p.x
        right = p.x+1 if p.x+1 < w else p.x
        up = p.y-1 if p.y-1 > 0 else p.y
        down = p.y+1 if p.y+1 < h else p.y
        return list(set([(left, p.y), (right, p.y), (p.x, up), (p.x, down)]))
    
    def __max(self, a, b):
        return a if a > b else b        
                    
    def __zoomImage(self, direction, scrollDirection):            
        if direction == "top":
            if scrollDirection:
                self.startY += self.zoomFactor if self.startY < self.height else -self.zoomFactor
            else:
                self.startY -= self.zoomFactor if self.startY > 0 else 0
        elif direction == "bottom":
            if scrollDirection:
                self.endY -= self.zoomFactor if self.endY > 0 else 0
            else:
                self.endY += self.zoomFactor if self.endY < self.height else -self.zoomFactor
        elif direction == "left":
            if scrollDirection:
                self.startX += self.zoomFactor if self.startX < self.width else -self.zoomFactor
            else:
                self.startX -= self.zoomFactor if self.startX > 0 else 0
        elif direction == "right":
            if scrollDirection:
                self.endX -= self.zoomFactor if self.endX > 0 else 0
            else:
                self.endX += self.zoomFactor if self.endX < self.width else -self.zoomFactor
        if self.startX < self.endX and self.startY < self.endY:
            try:
                self.imageCopy = self.__cropImage(sy = self.startY, ey = self.endY, sx = self.startX, ex = self.endX)
                for p in self.points:
                    p.setX(p.x-self.startX)
                    p.setY(p.y-self.startY)
                    self.__createPoint(p, color)
                self.imageCopy = cv2.resize(self.imageCopy, (self.width, self.height))                
            except:
                pass
   
    def __cropImage(self, *cropArgs, **cropKwargs):
        def getC(c, p):
            return cropKwargs[c] if c in cropKwargs else p
        if len(cropArgs) == 4 or len(cropKwargs) == 4:
            startX = getC("sx", cropArgs[0]) if len(cropArgs) == 4 else cropKwargs["sx"]
            endX = getC("ex", cropArgs[1]) if len(cropArgs) == 4 else cropKwargs["ex"]
            startY = getC("sy", cropArgs[2]) if len(cropArgs) == 4 else cropKwargs["sy"]
            endY = getC("ey", cropArgs[3]) if len(cropArgs) == 4 else cropKwargs["ey"]
            return self.image[startY:endY, startX:endX]
        elif len(cropArgs) == 1:
            if type(cropArgs[0]) is tuple or type(cropArgs[0]) is list:
                mask = np.zeros(self.image.shape[0:2], dtype = np.uint8)
                points = np.array([[[p.x, p.y] for p in cropArgs[0]]])
                cv2.drawContours(mask, [points], -1, (255, 255, 255), -1, cv2.LINE_AA)
                result = cv2.bitwise_and(self.image, self.image, mask = mask)
                rect = cv2.boundingRect(points) 
                cropped = result[rect[1]: rect[1] + rect[3], rect[0]: rect[0] + rect[2]]
                return cropped
        return None
    
    def __createPoint(self, p, color, expand = 0):
        if expand > 0:
            self.__createPoint(p, color)
            for n in self.moveToNextPoints(p, self.width, self.height):
                self.__createPoint(Point(n), color, expand-1)
        else:
            r, g, b, a = color
            self.imageCopy[p.y, p.x] = self.__newPixel(r, g, b, a, len(self.imageCopy[p.y, p.x]))
   
    def __createLine(self, a, b):
        if a.getPoint() != b.getPoint():
            a = np.array([a.x, a.y])
            b = np.array([b.x, b.y])
            points = np.linspace(a, b, int(np.linalg.norm(a - b))+1)
            [self.__createPoint(Point(p), self.color) for p in points]
        
    def __linePoints(self, points):
        for p in range(len(points)-1):
            a = points[p]
            b = points[p+1]
            self.__createLine(a, b)
            
    def __setBeforeImageCopy(self):
        self.beforeImage = self.imageCopy.copy()
        
    def __refresh(self):
        e = self.exitPoint
        self.__doAdvanced(cv2.EVENT_MOUSEMOVE, e.x, e.y, 0, "")
    
    def reset(self):
        self.imageCopy = self.__cropImage(sy = 0, ey = self.height, sx = 0, ex = self.width)
        self.setUpStartEndPoints()
        self.__setBeforeImageCopy()
        self.__refresh()
        
    def createCroppedImage(self, adjust):
        self.imageCopy = cv2.resize(self.__cropImage(self.points[:-1]), (self.width, self.height))
        self.__setBeforeImageCopy()   
        adjust(None, self.name, self.imageCopy, True, "crop")
        self.__refresh()
   
    def copySelection(self, action = None):
        self.__action = action
        self.stopCopy = action == None
        if action != None:
            self.copiedSelection = self.__cropImage(self.points[:-1])
        else:
            self.__refresh()

    def undo(self):
        if len(self.points) > 0:
            self.points.pop()
            self.__refresh()
            
    def update(self, updatePoints, updateImages):
        for p in range(len(updatePoints)):
            if self.points[p].getPoint() != updatePoints[p]:
                self.points[p].setPoint(updatePoints[p])
        for c in range(len(updateImages)):
            if self.placedImages[c].getPoint() != updateImages[c]:
                self.placedImages[c].setPoint(updateImages[c])
        self.__refresh()
            
    def __getCropDimensions(self, points):
        a = points[0]
        b = points[1]
        if a.x == b.x:
            height = abs(a.y-b.y)
        else:
            height = int(((a.x-b.x)**2 + (a.y-b.y)**2)**(1/2))
        c = points[2]
        if b.y == c.y:
            width = abs(b.x-c.x)
        else:
            width = int(((b.x-c.x)**2 + (b.y-c.y)**2)**(1/2)) 
        return [width, height]  
    
    def move(self, m, c):
        i = None
        if m == "down":
            i = c+1
            i = i if i < len(self.placedImages) else 0
        elif m == "up":
            i = c-1
            i = i if i > -1 else len(self.placedImages)-1
        self.placedImages[i].setIndex(c)
        self.placedImages[c].setIndex(i)
        self.__refresh()
                    
    def delete(self, d, type):
        darr = self.points if type == "points" else self.warpPoints if type == "warp" else self.placedImages
        def remove(i):
            p = darr[i]
            if p.index != i:
                p.setIndex(i)
            return p
        darr.pop(d)
        if type == "image":
            self.placedImages = [remove(i) for i in range(len(darr))]
        else:
            if len(darr) > 1:
                if darr[0].getPoint() == darr[-1].getPoint():
                    darr.pop()
            if type == "points":
                self.points = [remove(i) for i in range(len(darr))]
            elif type == "warp":
                self.warpPoints = [remove(i) for i in range(len(darr))]
        self.__refresh()
        
    def duplicate(self, d):
        dup = self.placedImages[d].copy()
        dup.setIndex(dup.index + 1)        
        self.placedImages.append(dup)
        self.__refresh()
        
    def setVisibility(self, v):
        self.placedImages[v].setVisible()
        self.__refresh()
        
    def clearAll(self, c):
        def adjustIndices():
            for p in range(len(self.placedImages)):
                if self.placedImages[p].index != p:
                    self.placedImages[p].setIndex(p)
        if c == "all":
            self.points.clear()
            self.placedImages.clear()
        elif c == "points":
            self.points.clear()
        elif c == "warp points":
            self.warpPoints.clear()
        elif c == "pixels":
            self.placedImages = list(filter(lambda p : not p.isPixelated, self.placedImages))
            adjustIndices()
        elif c == "rotates":
            self.placedImages = list(filter(lambda p : not p.isRotated, self.placedImages))
        elif c == "resizes":
            self.placedImages = list(filter(lambda p : not p.isResized, self.placedImages))
        elif c == "inserts":
            self.placedImages = list(filter(lambda p : not p.isInserted, self.placedImages))
            adjustIndices()
        else:
            c = "Copy" if c == "copies" else "Warp" if c == "warps" else "image"
            self.placedImages = list(filter(lambda p : c != p.name, self.placedImages))
        self.__refresh()
        
    def refreshWarp(self):
        self.warp.destroy()
        self.warpPerspective(self.__buttons, self.__actionButtons, self.__action)
            
    def warpPerspective(self, buttons, actionButtons, action):
        self.__buttons = buttons
        self.__actionButtons = actionButtons
        self.__action = action
        for b in buttons:
            b["state"] = "disabled"
        self.startWarp = True
        self.__refresh()
        def execute():
            origin = np.array([[o.x, o.y] for o in self.points[:-1]], dtype = np.float32)
            destination = np.array([[d.x, d.y] for d in self.warpPoints[:-1]], dtype = np.float32)
            matrix = cv2.getPerspectiveTransform(origin, destination)
            width, height = self.__getCropDimensions(self.warpPoints)
            wIm = cv2.warpPerspective(self.image, matrix, (width, height))
            wp = self.warpPoints[0]
            wp.setImage(wIm)
            wp.setIndex(len(self.placedImages))
            wp.setName("Warp")
            self.placedImages.append(wp)
            self.__placeImage(wp)
            self.showImage()
            
        def openWarp():
            def undoWarpPoints():
                if len(self.warpPoints) > 0:
                    self.warpPoints.pop()
                    self.__refresh()
                    self.warp.destroy()
                    openWarp()
            
            def cancelWarp():
                self.startWarp = False
                self.__refresh()
                for b in buttons:
                    b["state"] = "normal"
                self.__buttons = None
                self.__actionButtons = None
                self.__action = None
                action(self.warp.destroy)
                
            def update(u):
                for p in range(len(u)):
                    if self.warpPoints[p].getPoint() != u[p]:
                        self.warpPoints[p].setPoint(u[p])
                self.__refresh()
            
            self.warp = Tk()
            self.warp.title("Set warp points")
            self.warp.geometry('+300+90')
            w = self.warpPoints
            c = True if len(w) > 1 and w[0].getPoint() == w[-1].getPoint() else False
            if c:
                w = w[:-1]
            points = []
            self.warpDeletes = []
            t = 0
            while t < len(w):
                n = Label(self.warp, text = "Warp" + str(t+1) + ". ")
                n.grid(column = 0, row = t)
                xLabel = Label(self.warp, text = "x = ")
                xLabel.grid(column = 1, row = t)
                x = Numbox(self.warp, width = 10)
                x.setValue(w[t].x)
                x.setRange(0, self.width-1)
                x.bind(valueType = int)
                x.grid(column = 2, row = t)
                yLabel = Label(self.warp, text = "y = ")
                yLabel.grid(column = 3, row = t)
                y = Numbox(self.warp, width = 10)
                y.setValue(w[t].y)
                y.setRange(0, self.height-1)
                y.bind(valueType = int)
                y.grid(column = 4, row = t)
                d = Button(self.warp, text = "Delete")
                d.grid(column = 5, row = t)
                d.bind("<ButtonRelease-1>", lambda event : actionButtons(event, "del", "warp"))
                self.warpDeletes.append((d, t))
                points.append((x, y))
                t += 1
            doWarp = Button(self.warp, text = "Warp Perspective", command = execute)
            doWarp.grid(column = 0, row = t)
            if len(self.warpPoints) != len(self.points):
                doWarp["state"] = "disabled" 
            undoWarp = Button(self.warp, text = "Undo", command = undoWarpPoints)
            undoWarp.grid(column = 1, row = t)
            updateWarp = Button(self.warp, text = "Update", command = lambda : update([(x.processValue(int), y.processValue(int)) for (x, y) in points]))
            updateWarp.grid(column = 2, row = t)
            clearWarp = Button(self.warp, text = "Clear all", command = lambda : action(self.clearAll, "warp points"))
            clearWarp.grid(column = 3, row = t)
            cancelWarp = Button(self.warp, text = "Cancel", command = cancelWarp)
            cancelWarp.grid(column = 4, row = t)
            self.warp.protocol("WM_DELETE_WINDOW", cancelWarp) 
            self.warp.mainloop() 
        
        openWarp()
    
    def pixelate(self, buttons, action, index = None):
        def execute():
            width = w.processValue(int)
            height = h.processValue(int)
            input = cv2.resize(im, (width, height), interpolation = cv2.INTER_LINEAR)
            output = cv2.resize(input, (imw, imh), interpolation = cv2.INTER_NEAREST)
            if self.__added:
                self.placedImages[-1].setImage(output)
                self.placedImages[-1].setDesiredPixelatedSize(width, height)
                self.__refresh()
            else:
                ip = Point(p)
                ip.setImage(output)
                ip.setIndex(len(self.placedImages))
                ip.setName("Pixelate")
                ip.setDesiredPixelatedSize(width, height)
                ip.setPixelated(True)
                self.placedImages.append(ip)
                self.__placeImage(ip)
                self.showImage()
                self.__added = True
            
        def cancelPix():
            for b in buttons:
                b["state"] = "normal"
            self.__added = None
            action(pix.destroy)
            
        if index == None:
            pi = Point()
            pi.setName("image")
            pi.setImage(self.imageCopy)
            pi.setIndex(len(self.placedImages))
            action(self.placedImages.append, pi)
            return
        for b in buttons:
            b["state"] = "disabled"
        p = self.placedImages[index]
        self.__added = p.isPixelated
        im = p.image
        imh, imw, _ = im.shape
        pix = Tk()
        pix.title("Pixelate {}".format(p.name + str(index+1)))
        pix.geometry('+300+90')
        wLabel = Label(pix, text = "Desired width = ")
        wLabel.pack(side = LEFT)
        w = Numbox(pix, width = 10)
        w.setValue(p.pixWidth)
        w.setRange(1, imw-1)
        w.bind(valueType = int)
        w.pack(side = LEFT)
        hLabel = Label(pix, text = "Desired height = ")
        hLabel.pack(side = LEFT)
        h = Numbox(pix, width = 10)
        h.setValue(p.pixHeight)
        h.setRange(1, imh-1)
        h.bind(valueType = int)
        h.pack(side = LEFT)
        doPix = Button(pix, text = "Pixelate", command = execute)
        doPix.pack(side = LEFT)
        cancelPix = Button(pix, text = "Cancel", command = cancelPix)
        cancelPix.pack(side = LEFT)
        pix.protocol("WM_DELETE_WINDOW", cancelPix) 
        pix.mainloop() 
        
    def rotate(self, buttons, action, adjust, index):
        def execute():
            angle = a.processValue()
            output = adjust(angle, self.name, p.image, True, "rotate", returnAdjust = True)
            if self.__added:
                self.placedImages[-1].setImage(output)
                self.placedImages[-1].setRotateAngle(angle)
                self.__refresh()
            else:
                rp = Point(p)
                rp.setImage(output)
                rp.setIndex(len(self.placedImages))
                rp.setName("Rotate")
                rp.setRotated(True)
                rp.setRotateAngle(angle)
                self.placedImages.append(rp)
                self.__placeImage(rp)
                self.showImage()
                self.__added = True
            
        def cancelRot():
            for b in buttons:
                b["state"] = "normal"
            self.__added = None
            action(rot.destroy)
            
        for b in buttons:
            b["state"] = "disabled"
        p = self.placedImages[index]
        self.__added = p.isRotated
        rot = Tk()
        rot.title("Rotate {}".format(p.name + str(index+1)))
        rot.geometry('+300+90')
        aLabel = Label(rot, text = "Angle = ")
        aLabel.pack(side = LEFT)
        a = Numbox(rot, width = 10)
        a.setValue(p.rotateAngle)
        a.setRange(-360, 360)
        a.bind(addNegative = True)
        a.pack(side = LEFT)
        doRot = Button(rot, text = "Rotate", command = execute)
        doRot.pack(side = LEFT)
        cancelRot = Button(rot, text = "Cancel", command = cancelRot)
        cancelRot.pack(side = LEFT)
        rot.protocol("WM_DELETE_WINDOW", cancelRot) 
        rot.mainloop()
        
    def paint(self, buttons):
        def isTool():
            if isPaint["text"] == "Fill tool":
                isPaint["text"] = "Brush tool"
                self.__brush = True
            else:
                isPaint["text"] = "Fill tool"
                self.__brush = False
        def updateBrush():
            self.brush = brushSize.processValue(valueType = int)
        def clearPaint():
            self.points = list(filter(lambda p : not p.visible or p.name != "brush", self.points))
            self.__refresh()
        def execute():
            def getColor(x, y):
                r, g, b, a = self.__checkPixel(self.imageCopy[y, x])
                return (r, g, b)
            
            def moveFill(f, beforeColor, newColor):
                def checkColor(x, y):
                    def round(c):
                        c = int(c*255)
                        r = 10**(len(str(c))-1)
                        half = r//2
                        check = c % r
                        if check < half:
                            c -= check
                        else:
                            c += (r-check)
                        return c
                    r, g, b = getColor(x, y)
                    sr, sg, sb = beforeColor
                    r = round(r)
                    g = round(g)
                    b = round(b)
                    sr = round(sr)
                    sg = round(sg)
                    sb = round(sb)
                    return len(list(filter(lambda c : c, [r == sr, g == sg, b == sb]))) > 2
                r, g, b, a = newColor
                self.imageCopy[f.y, f.x] = self.__newPixel(r, g, b, a, len(self.imageCopy[f.y, f.x]))
                next = self.moveToNextPoints(f, self.width, self.height)
                next = [Point(x, y) for (x, y) in next if checkColor(x, y)]
                path = []
                while len(next) > 0:
                    t = []
                    for n in next:
                        path.append((n.x, n.y))
                        r, g, b, a = newColor
                        self.imageCopy[n.y, n.x] = self.__newPixel(r, g, b, a, len(self.imageCopy[n.y, n.x]))
                        self.__setBeforeImageCopy()
                        cv2.waitKey(1)
                        self.showImage()
                        t += self.moveToNextPoints(n, self.width, self.height)
                        t = list(set(t))
                    next = [Point(x, y) for (x, y) in t if (x, y) not in path and checkColor(x, y)]
                    
            fillPoints = list(filter(lambda p : p.visible, self.points))
            for f in fillPoints:
                f.setVisible()
                self.__refresh()
                beforeColor = getColor(f.x, f.y)
                moveFill(f, beforeColor, f.color)
                self.points.remove(f)
                
        def cancelPaint():
            for b in buttons:
                b["state"] = "normal"
            for p in self.points:
                p.setVisible(True) 
            self.__paint = False
            f.destroy()
            
        for b in buttons:
            b["state"] = "disabled"
        for p in self.points:
            p.setVisible(False) 
        self.__paint = True
        f = Tk()
        f.title("Paint")
        f.geometry('+300+90')
        brushSize = Numbox(f, width = 10)
        brushSize.setValue(3)
        brushSize.bind(valueType = int)
        brushSize.pack(side = LEFT)
        updateBrush = Button(f, text = "Update brush size", command = updateBrush) 
        updateBrush.pack(side = LEFT)
        isPaint = Button(f, text = "Fill tool", command = isTool)
        isPaint.pack(side = LEFT)
        doFill = Button(f, text = "Fill", command = execute)
        doFill.pack(side = LEFT)
        clearF = Button(f, text = "Clear", command = clearPaint)
        clearF.pack(side = LEFT)
        cancelF = Button(f, text = "Cancel", command = cancelPaint)
        cancelF.pack(side = LEFT)
        f.protocol("WM_DELETE_WINDOW", cancelPaint) 
        f.mainloop()
               
    def setIsAdvanced(self, adjust = None):
        self.isAdvanced = not self.isAdvanced
        if adjust != None:
            adjust(None, self.name, self.imageCopy, True, "advanced")
        
    def setBoundaryColor(self, color = "white"):
        if color == "white":
            self.color = (1, 1, 1, None)
        else:
            r, g, b, a = self.__checkPixel(color)
            self.color = (b, g, r, a)
        
    def setZoomFactor(self, isZoomFactor):
        self.zoomFactor = isZoomFactor
        
    def showImage(self):
        cv2.imshow(self.name, self.imageCopy)
        
    def resize(self, buttons, action, adjust, index):
        def execute():
            r = f.processValue()
            output = adjust(r, self.name, original, True, "resize", returnAdjust = True)
            if self.__added:
                self.placedImages[-1].setImage(output)
                self.placedImages[-1].setResizeFactor(r)
                self.__refresh()
            else:
                rp = Point(p)
                rp.setImage(output)
                rp.setIndex(len(self.placedImages))
                rp.setName("Resize")
                rp.setResized(True)
                rp.setResizeFactor(r)
                self.placedImages.append(rp)
                self.__placeImage(rp)
                self.showImage()
                self.__added = True
            
        def cancelRes():
            for b in buttons:
                b["state"] = "normal"
            self.__added = None
            action(res.destroy)
            
        for b in buttons:
            b["state"] = "disabled"
        p = self.placedImages[index]
        original = p.image
        self.__added = p.isResized
        res = Tk()
        res.title("Resize {}".format(p.name + str(index+1)))
        res.geometry('+300+90')
        fLabel = Label(res, text = "Factor = ")
        fLabel.pack(side = LEFT)
        f = Numbox(res, width = 10)
        f.setValue(p.resizeFactor)
        f.bind()
        f.pack(side = LEFT)
        doRes = Button(res, text = "Resize", command = execute)
        doRes.pack(side = LEFT)
        cancelRes = Button(res, text = "Cancel", command = cancelRes)
        cancelRes.pack(side = LEFT)
        res.protocol("WM_DELETE_WINDOW", cancelRes) 
        res.mainloop() 
        
    def insert(self):
        file = askopenfilename()
        if file != "":
            add = cv2.imread(file, cv2.IMREAD_UNCHANGED).astype(np.float32)/255.0
            h, w, _ = add.shape
            if h > self.height:
                h = self.height
            if w > self.width:
                w = self.width
            add = cv2.resize(add, (w, h))
            a = Point()
            a.setImage(add)
            a.setIndex(len(self.placedImages))
            a.setName("Insert")
            a.setInsert(True)
            self.placedImages.append(a)
            self.__refresh()
        
    def setUpStartEndPoints(self):
        self.startY = 0
        self.startX = 0
        self.endY = self.height-1
        self.endX = self.width-1
    
    def __checkPixel(self, pixel):
        if len(pixel) == 4:
            b, g, r, a = pixel
            return (r, g, b, a)
        else:
            b, g, r = pixel
            return (r, g, b, None)
        
    def __newPixel(self, r, g, b, a, n):
        arr = [b, g, r] 
        if n == 4:
            arr += [a]
        return np.array(arr, dtype = np.float32)
                
    def setUpImage(self, newImage):
        def veryCloseToZero(repeat):
            return float("0." + "0"*repeat + "1")
        h, w, _ = newImage.shape
        c = veryCloseToZero(50)
        for i in range(h):
            for j in range(w):
                r, g, b, a = self.__checkPixel(newImage[i, j])
                if b == g == r == 0.0:
                    newImage[i, j] = self.__newPixel(r, g, b, a, len(newImage[i, j]))
        self.image = newImage
        self.imageCopy = newImage.copy()
        self.__setBeforeImageCopy()
        self.height = h
        self.width = w 
        self.warpPoints = [Point(), Point(0, h-1), Point(w-1, h-1), Point(w-1, 0), Point()]
        for r in range(len(self.warpPoints)):
            self.warpPoints[r].setIndex(r)
        self.setUpStartEndPoints()  