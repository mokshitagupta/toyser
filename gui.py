import tkinter
from langdetect import detect
# print(detect(buf))


VSTEP = 18
HSTEP = 13
WIDTH, HEIGHT = 800, 600
SCROLLY = 100


def layout(text):
    x = 0
    y = VSTEP
    displayList = []
    for c in text:
        if x + HSTEP > WIDTH or c == "\n":
            x = HSTEP
            y+= VSTEP
        else:
            x += HSTEP
        displayList.append((x,y,c))
    return displayList

class Browser:
    def __init__(self):

        self.scroll = 0
        self.window = tkinter.Tk() #create window
        self.window.bind("<Down>", self.scrolldown)
        self.window.bind("<Up>", self.scrollup)
        self.canvas = tkinter.Canvas(self.window, width=WIDTH, height=HEIGHT) #create canvas
        self.canvas.pack() #position canvas inside window

    def scrolldown(self, e):
        if self.scroll + HEIGHT > self.end: return
        self.scroll += SCROLLY
        self.draw()

    def scrollup(self, e):
        if self.scroll == 0: return
        self.scroll -= SCROLLY
        self.draw()

    def draw(self):
        self.canvas.delete("all")
        for x,y,c in self.displayList:
            if y - self.scroll >  HEIGHT: continue
            if y + VSTEP < self.scroll: continue
            self.canvas.create_text(x, y-self.scroll, text=c)

    def load(self, url):
        url.request()
        self.content = url.show()
        self.displayList = layout(self.content)
        self.end = self.displayList[-1][1]
        self.draw()
        
