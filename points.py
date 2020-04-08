import numpy as np

class Point:
    def __init__(self, *pointArgs, **pointKwargs):
        self.setX(0)
        self.setY(0)
        self.zoom = None
        self.setIndex(0)
        self.setName("point")
        self.setPixelated(False)
        self.setRotated(False)
        self.setRotateAngle(0)
        self.setResized(False)
        self.setResizeFactor(1)
        self.setInsert(False)
        self.setColor((255,255,255))
        self.setImage([])
        self.setDesiredPixelatedSize(1, 1)
        self.visible = True
        self.setPoint(*pointArgs, **pointKwargs)

    def toString(self):
        return "({}, {})".format(self.x, self.y)
    
    def setPoint(self, *pointArgs, **pointKwargs):
        def getP(c, p):
            return pointKwargs[c] if c in pointKwargs else p
        if len(pointArgs) == 1:
            p = getP("p", pointArgs[0])
            if type(p) is Point:
                self.setX(getP("x", p.x))
                self.setY(getP("y", p.y))
            elif type(p) is tuple or type(p) is list:
                self.setX(getP("x", p[0]))
                self.setY(getP("y", p[1]))
            elif isinstance(p, np.ndarray):
                x, y = p
                self.setX(getP("x", int(x)))
                self.setY(getP("y", int(y)))
            else:
                print(*pointArgs, "is not a Point object!")
                quit()
        if len(pointArgs) == 2:               
            self.setX(getP("x", pointArgs[0]))
            self.setY(getP("y", pointArgs[1])) 
        if len(pointArgs) == 0:               
            self.setX(getP("x", self.x))
            self.setY(getP("y", self.y))
            
    def getPoint(self):
        return (self.x, self.y)
            
    def setX(self, x):
        self.x = x
        
    def setY(self, y):
        self.y = y
    
    def setIndex(self, index):
        self.index = index
    
    def setZoom(self, zX, zY):
        self.zoom = Point(zX, zY)
        
    def setColor(self, color):
        self.color = color
        
    def setImage(self, image):
        self.image = image
        
    def setName(self, name):
        self.name = name
        
    def setVisible(self, v = None):
        self.visible = not self.visible if v == None else v
        
    def setDesiredPixelatedSize(self, width, height):
        self.setDesiredPixelatedWidth(width)
        self.setDesiredPixelatedHeight(height)
        
    def setDesiredPixelatedWidth(self, width):
        self.pixWidth = width
        
    def setDesiredPixelatedHeight(self, height):
        self.pixHeight = height
    
    def setPixelated(self, isPixelated):
        self.isPixelated = isPixelated
        
    def setRotated(self, isRotated):
        self.isRotated = isRotated
        
    def setRotateAngle(self, angle):
        self.rotateAngle = angle
        
    def setResized(self, isResized):
        self.isResized = isResized
        
    def setResizeFactor(self, factor):
        self.resizeFactor = factor
        
    def setInsert(self, isInserted):
        self.isInserted = isInserted
        
    def copy(self):
        p = Point(self)
        p.setIndex(self.index)
        p.zoom = self.zoom
        p.setImage(self.image)
        p.setName(self.name)
        p.visible = self.visible
        p.setColor(self.color)
        return p