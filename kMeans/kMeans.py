from cv2 import *
import numpy as np

class KMeans:
    def __init__(self, name, image):
        self.name = name
        self.seeds = []
        self.seedLocations = []
        self.seedGroups = []
        self.image = image
        h, w, _ = image.shape
        self.points = [(y, x) for x in range(w) for y in range(h)]
        self.minDistance = float("inf")
        self.iterations = 0
        
    def addSeed(self, seed):
        s, p = seed
        self.seeds.append(s)
        self.seedLocations.append(p)
        self.seedGroups.append([])
        
    def distance(self, x, y, s):
        b, g, r = self.image[y, x]
        sr, sg, sb = self.seeds[s]
        d = ((r-sr)**2 + (g-sg)**2 + (b-sb)**2)**(1/2)
        if d < self.minDistance:
            self.minDistance = d
        return (sr, sg, sb, s, d)
        
    def execute(self, iterations = 1):
        i = 0
        while i < iterations:
            print("Running k means")
            for (y, x) in self.points:
                distances = [self.distance(x,y,s) for s in range(len(self.seeds))]
                sr, sg, sb, s = [_ for (*_, d) in distances if d == self.minDistance][0]
                b, g, r = self.image[y, x]
                self.seedGroups[s].append((r, g, b))
                self.image[y, x] = np.array([sb, sg, sr], dtype = np.float32)
                self.minDistance = float("inf")
            cv2.imshow(self.name, self.image)
            i += 1
            self.iterations += 1
            print("Iteration", self.iterations)
            cv2.imwrite(self.name + str(self.iterations) + ".png", 255.0*self.image)
            if i < iterations:
                self.updateSeeds()
                print("Updated seeds", self.iterations)
                
    def updateSeeds(self):
        for s in range(len(self.seedGroups)):
            average = [0,0,0]
            for pixel in self.seedGroups[s]:
                for k in range(3):
                    average[k] += pixel[k]
            for a in range(3):
                try :
                    average[a] /= len(self.seedGroups[s])
                except:
                    print(average[a], len(self.seedGroups[s]))
            r, g, b = average
            self.seeds[s] = (r, g, b)
        
if __name__ == '__main__':
    def mouseCallback(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONUP:
            b, g, r = image[y, x]
            k.addSeed(((r, g, b), (x, y)))
            cv2.circle(image, (x,y), 5, (255, 255, 255), -1)
            cv2.imshow(n, image)
            cv2.imwrite(n + "Seeds.png", 255.0*image)
            
    def iterate(i = 1, update = False):
        if update:
            k.updateSeeds()
            copy = k.image.copy()
            for (x, y) in k.seedLocations:
                cv2.circle(copy, (x,y), 5, (255, 255, 255), -1)
            cv2.imshow(k.name, copy)
        ok = cv2.waitKey(0) % 256
        if ok == ord('k'):
            b = len(k.seeds) == 0
            if b:
                print("Please select seeds.")
            else:
                k.execute(i)            
            iterate(i, not b)
    
    names = ["teddy.PNG", "teddyOutside.JPG"]
    sizes = [1, 0.2]
    for m in range(2):
        n = names[m]
        image = cv2.imread(n, cv2.IMREAD_UNCHANGED).astype(np.float32)/255.0
        imh, imw, _ = image.shape
        r = sizes[m]
        imh = int(r*imh)
        imw = int(r*imw)
        image = cv2.resize(image, (imw, imh))
        copy = image.copy()
        n = n[:n.find(".")]
        print(n)
        k = KMeans(n, copy)
        cv2.namedWindow(n)
        cv2.setMouseCallback(n, mouseCallback)
        cv2.imshow(n, image)
        iterate(2)
    cv2.waitKey(0)