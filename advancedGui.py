from tkinter import *
from tkinter.colorchooser import askcolor
from textbox import Numbox
 
class AdvancedGui():
    color = "white"
    
    def __init__(self, getAdvanced = None, title = "Advanced Options", geometry = '+630+230', edits = None, adjust = None):
        def pointsInfo():
            if self.pInfo != None:
                self.showPointInfo.config(text = self.getAdvanced.currentPoint)
                self.pInfo = self.gui.after(1, pointsInfo)
        def colorInfo():
            def check(c):
                if c*255.0 <= 255.0:
                    return c*255.0
                return c
            if self.cInfo != None:
                r, g, b, a = self.getAdvanced.color
                
                self.showColorInfo.config(text = "Color = (r = {}, g = {}, b = {})".format(check(r), check(g), check(b)))
                self.cInfo = self.gui.after(1, colorInfo)
        self.getAdvanced = getAdvanced
        self.adjust = adjust
        self.edits = edits
        self.title = title
        self.gui = Tk()
        self.gui.title(self.title)
        self.gui.geometry(geometry)
        self.showPointInfo = Label(self.gui, text = self.getAdvanced.currentPoint)
        self.showPointInfo.grid(column = 0, row = 0)
        self.showColorInfo = Label(self.gui, text = "Color = " + str(self.getAdvanced.color))
        self.showColorInfo.grid(column = 0, row = 1)
        self.openColors = Button(self.gui, text = "Choose a color", command = self.__setColor)
        self.openColors.grid(column = 0, row = 2)
        self.paint = Button(self.gui, text = "Paint", command = lambda : self.getAdvanced.paint(self.gui.winfo_children()))
        self.paint.grid(column = 1, row = 2)
        self.cancel = Button(self.gui, text = "Cancel", command = self.__cancelAdvancedGui)
        self.cancel.grid(column = 2, row = 2)
        self.enterZoom = Numbox(self.gui, width = 10)
        self.enterZoom.setValue(self.getAdvanced.zoomFactor)
        self.enterZoom.bind(valueType = int)
        self.enterZoom.grid(column = 0, row = 3)
        self.updateZoom = Button(self.gui, text = "Update zoom factor", command = self.__updateZoomFactor)
        self.updateZoom.grid(column = 1, row = 3)
        self.undo = Button(self.gui, text = "Undo", command = self.getAdvanced.undo)
        self.undo.grid(column = 0, row = 4)
        self.reset = Button(self.gui, text = "Reset", command = self.getAdvanced.reset)
        self.reset.grid(column = 1, row = 4)
        self.doAdvanced = Button(self.gui, text = "Advanced", command = self.__advance)
        self.doAdvanced.grid(column = 2, row = 4)
        self.pInfo = self.gui.after(1, pointsInfo)
        self.cInfo = self.gui.after(1, colorInfo)
        self.gui.protocol("WM_DELETE_WINDOW", self.__cancelAdvancedGui)  
        self.gui.mainloop()
        
    def __advance(self):
        def open():
            def setButtonsState(state):
                buttons = self.gui.winfo_children()
                for s in buttons:
                    s["state"] = state
                    
            def cancelAdvanced():
                setButtonsState("normal")
                self.info.destroy()
                
            def createCrop():
                self.getAdvanced.createCroppedImage(self.adjust)
                
            def separatePoints(points):
                return [x.numbox for (x, y) in points] + [y.numbox for (x, y) in points]
            
            def processPoints(points):
                return [(x.processValue(int), y.processValue(int)) for (x, y) in points]
            
            def action(method, *methodArgs, **methodKwargs):
                method(*methodArgs, **methodKwargs)
                if "warp" in str(methodArgs) and self.getAdvanced.startWarp:
                    self.getAdvanced.refreshWarp()
                else:
                    self.info.destroy()
                    open()
                
            def copyAction(event):
                if copy["text"] == "Copy":
                    copy["text"] = "Stop"
                    copy.config(command = self.getAdvanced.copySelection)
                elif copy["text"] == "Stop":
                    copy["text"] = "Copy"
                    copy.config(command = lambda : self.getAdvanced.copySelection(action))
                    
            def actionButtons(event, act, type = "image"):
                b = event.widget
                arr = self.actionPoints if type == "points" else self.getAdvanced.warpDeletes if type == "warp" else self.actions
                index = [a for a in arr if b in a][0][-1]
                if act == "visible":
                    b["text"] = "Not visible" if b["text"] == "Visible" else "Visible"
                    self.getAdvanced.setVisibility(index)
                elif act == "dup":
                    action(self.getAdvanced.duplicate, index)
                elif act == "rot":
                    self.getAdvanced.rotate(getButtons(), action, self.adjust, index)
                elif act == "res":
                    self.getAdvanced.resize(getButtons(), action, self.adjust, index)
                elif act == "pix":
                    self.getAdvanced.pixelate(getButtons(), action, index)
                elif act == "del":
                    action(self.getAdvanced.delete, index, type)
                else:
                    action(self.getAdvanced.move, act, index)
                    
            def getButtons():
                self.buttons = self.info.winfo_children()
                return self.buttons
            
            def clear(event):
                c = "points" if clearAll["text"] == "Clear all" else "copies" if clearAll["text"] == "Clear points" else "warps" if clearAll["text"] == "Clear copies" else "pixels" if clearAll["text"] == "Clear warps" else "rotates" if clearAll["text"] == "Clear pixels" else "resizes" if clearAll["text"] == "Clear rotates" else "inserts" if clearAll["text"] == "Clear resizes" else "images" if clearAll["text"] == "Clear inserts" else "all"
                clearAll["text"] = "Clear " + c
                clearAll.config(command = lambda : action(self.getAdvanced.clearAll, c))
            
            setButtonsState("disabled")
            self.info = Tk()
            self.info.title("Advanced information")
            self.info.geometry('+530+230')
            p = self.getAdvanced.points
            c = True if len(p) > 1 and p[0].getPoint() == p[-1].getPoint() else False
            if c:
                p = p[:-1]
            points = []
            self.actionPoints = []
            t = 0
            while t < len(p):
                n = Label(self.info, text = "P" + str(t+1) + ". ")
                n.grid(column = 0, row = t)
                xLabel = Label(self.info, text = "x = ")
                xLabel.grid(column = 1, row = t)
                x = Numbox(self.info, width = 10)
                x.setValue(p[t].x)
                x.setRange(0, self.getAdvanced.width-1)
                x.bind(valueType = int)
                x.grid(column = 2, row = t)
                yLabel = Label(self.info, text = "y = ")
                yLabel.grid(column = 3, row = t)
                y = Numbox(self.info, width = 10)
                y.setValue(p[t].y)
                y.setRange(0, self.getAdvanced.height-1)
                y.bind(valueType = int)
                y.grid(column = 4, row = t)
                d = Button(self.info, text = "Delete")
                d.grid(column = 5, row = t)
                d.bind("<ButtonRelease-1>", lambda event : actionButtons(event, "del", "points"))
                self.actionPoints.append((d, t))
                points.append((x, y))
                t += 1
            place = self.getAdvanced.placedImages
            placedIm = []
            self.actions = []
            a = t
            for c in place:
                n = Label(self.info, text = place[c.index].name + str(c.index+1) + ". ")
                n.grid(column = 0, row = t)
                xLabel = Label(self.info, text = "x = ")
                xLabel.grid(column = 1, row = t)
                x = Numbox(self.info, width = 10)
                x.setValue(place[c.index].x)
                x.setRange(0, self.getAdvanced.width-1)
                x.bind(valueType = int)
                x.grid(column = 2, row = t)
                yLabel = Label(self.info, text = "y = ")
                yLabel.grid(column = 3, row = t)
                y = Numbox(self.info, width = 10)
                y.setValue(place[c.index].y)
                y.setRange(0, self.getAdvanced.height-1)
                y.bind(valueType = int)
                y.grid(column = 4, row = t)
                visibility = Button(self.info, text = "Visible" if c.visible else "Not visible")
                visibility.grid(column = 5, row = t)
                visibility.bind("<ButtonRelease-1>", lambda event : actionButtons(event, "visible"))
                up = Button(self.info, text = "Up")
                up.grid(column = 6, row = t)
                up.bind("<ButtonRelease-1>", lambda event : actionButtons(event, "up"))
                down = Button(self.info, text = "Down")
                down.grid(column = 7, row = t)
                down.bind("<ButtonRelease-1>", lambda event : actionButtons(event, "down"))
                dup = Button(self.info, text = "Duplicate")
                dup.grid(column = 8, row = t)
                dup.bind("<ButtonRelease-1>", lambda event : actionButtons(event, "dup"))
                rot = Button(self.info, text = "Rotate")
                rot.grid(column = 9, row = t)
                rot.bind("<ButtonRelease-1>", lambda event : actionButtons(event, "rot"))
                res = Button(self.info, text = "Resize")
                res.grid(column = 10, row = t)
                res.bind("<ButtonRelease-1>", lambda event : actionButtons(event, "res"))
                pix = Button(self.info, text = "Pixelate")
                pix.grid(column = 11, row = t)
                pix.bind("<ButtonRelease-1>", lambda event : actionButtons(event, "pix"))
                delete = Button(self.info, text = "Delete")
                delete.grid(column = 12, row = t)
                delete.bind("<ButtonRelease-1>", lambda event : actionButtons(event, "del"))
                self.actions.append((visibility, up, down, dup, rot, res, pix, delete, c.index))
                placedIm.append((x, y))
                t += 1
            col = 0
            b = Button(self.info, text = "Crop" if c else "Close", command = createCrop if c else cancelAdvanced)
            b.grid(column = col, row = t)
            col += 1
            if c:
                w = Button(self.info, text = "Warp Perspective", command = lambda : self.getAdvanced.warpPerspective(getButtons(), actionButtons, action))
                w.grid(column = col, row = t)
                col += 1
                w["state"] = "disabled" if len(p) != 4 else "normal"
            pix = Button(self.info, text = "Pixelate", command = lambda : self.getAdvanced.pixelate(getButtons(), action))
            pix.grid(column = col, row = t)
            col += 1
            insert = Button(self.info, text = "Insert", command = lambda : action(self.getAdvanced.insert))
            insert.grid(column = col, row = t)
            col += 1
            if len(p) > 0 or len(place) > 0:
                u = Button(self.info, text = "Update", command = lambda : self.getAdvanced.update(processPoints(points), processPoints(placedIm)))
                u.grid(column = col, row = t)
                col += 1
                clearAll = Button(self.info, text = "Clear all", command = lambda : action(self.getAdvanced.clearAll, "all"))
                clearAll.grid(column = col, row = t)
                col += 1
                clearAll.bind("<Button-3>", clear)
            if c:
                copy = Button(self.info, text = "Copy", command = lambda : self.getAdvanced.copySelection(action))
                copy.grid(column = col, row = t)
                col += 1
                copy.bind("<Button-3>", copyAction)
                d = Button(self.info, text = "Cancel", command = cancelAdvanced)
                d.grid(column = col, row = t)
            self.info.protocol("WM_DELETE_WINDOW", cancelAdvanced)  
            self.info.mainloop()
        open()
        
    def __updateZoomFactor(self):
        self.getAdvanced.setZoomFactor(self.enterZoom.processValue(int))
        self.gui.focus()
         
    def __setColor(self):
        newColor = askcolor(color = self.color if self.color == "white" else self.color[1], parent = self.gui, title = self.title)
        self.color = self.color if newColor == (None, None) else newColor
        self.getAdvanced.setBoundaryColor(self.color[0])
        
    def __cancelAdvancedGui(self):
        if self.cancel["state"] == "normal":
            if self.getAdvanced != None:
                self.getAdvanced.setIsAdvanced(self.adjust)
            if self.edits != None:
                for b in self.edits:
                    b["state"] = "normal"
            self.gui.after_cancel(self.pInfo)
            self.gui.after_cancel(self.cInfo)
            self.pInfo = self.cInfo = None
            self.gui.destroy()