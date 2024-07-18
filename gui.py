import tkinter
import os
# from langdetect import detect
# print(detect(buf))


VSTEP = 18
HSTEP = 13
width, height = 800, 600
iwidth, iheight = 800, 600

SCROLLY = 100

SB_WIDTH = 18
SB_HEIGHT= 50
MOUSESCROLL = 1

EMOJISPATH = "openmoji-16x16-color/"
emojis = {}
available = set()

def processEmojis():
    dir_list = os.listdir(EMOJISPATH)
    global maxParts
    for f in dir_list:
        available.add(f[:-4])
        parts = f.replace(".png", "").split("-")
        first = ord(chr(int(parts[0], 16)))
        if len(parts) > 2:
            continue
        if first in emojis and len(parts) > 1:
            emojis[first] |= set(parts[1:])
        else:
            if len(parts) > 1:
                emojis[first] = set(parts[1:])
            else:
                emojis[first] = set()

    with open("emo.txt", "w") as f:
        print(emojis, file=f)

def layout(text):
    x = 0
    y = VSTEP
    displayList = []
    emoji = ""
    emojisAll = []
    variants = set()
    addChar = True
    for c in text:
        enc = ord(c)
        stri = str(hex(enc))[2:].upper()
        # print(stri)
        if enc in emojis:
            copy = emoji
            if emoji :
                emoji += "-" + stri
                addChar = False
            else: 
                addChar = False
                emoji = stri
                variants = emojis[enc]
            if emoji not in available and copy and copy in available:
                c = tkinter.PhotoImage(file=EMOJISPATH+copy+".png")
                emojisAll.append(copy)
                addChar = True
                emoji = stri
                variants = emojis[enc]
        elif stri in variants:
            addChar = False
            emoji += "-" + stri
        else:
            addChar = True
            if emoji and copy and copy in available: 
                # c = emoji
                if x + HSTEP > width - 2*SB_WIDTH or c == "\n":
                    x = HSTEP
                    y+= VSTEP
                else:
                    x += HSTEP
                displayList.append((x,y,tkinter.PhotoImage(file=EMOJISPATH+copy+".png")))
                emojisAll.append(emoji)
                emoji = ""

        if addChar:
            if x + HSTEP > width - 2*SB_WIDTH or c == "\n":
                x = HSTEP
                y+= VSTEP
            else:
                x += HSTEP
            displayList.append((x,y,c))
    # print(emojisAll)
    return displayList

class Browser:
    def __init__(self):

        processEmojis()
        self.scroll = 0
        self.window = tkinter.Tk() #create window
        self.window.bind("<Down>", self.scrolldown)
        self.window.bind("<MouseWheel>", self.mouseWheel)
        self.window.bind("<Up>", self.scrollup)
        self.window.bind("<Configure>", self.resize)
        self.canvas = tkinter.Canvas(self.window, width=width + SB_WIDTH, height=height) #create canvas
        
        #position canvas inside window, fill on both dirs on resize
        self.canvas.pack(fill=tkinter.BOTH, expand=1) 
        self.barPos = 0
        self.end = 0
        self.sbHeight = 0
        self.difference = 0

    def resize(self,e):
        global width
        global height

        self.difference = e.height - iheight
        height = e.height
        width = e.width
        self.rerender()

    def rerender(self): 
        self.displayList = layout(self.content)

        if self.displayList:
            self.end = self.displayList[-1][1]
        if self.end:
            self.percentage = 1 - ((self.end - height )/ self.end)
            self.scrollrate = height / (self.end/SCROLLY)
            self.sbHeight = height * self.percentage + (self.difference * self.percentage)
        else:
            self.percentage = 0
            self.scrollrate = 0
            
        self.draw()

    def scrolldown(self, e, scroll = SCROLLY):
        if self.scroll + height >= self.end: return
        self.scroll += scroll
        self.barPos += self.scrollrate
        self.draw()

    def mouseWheel(self, e):
        # down -> -1 delta
        # up -> 1 delta
        if e.delta < 0:
            self.scrolldown(e, scroll=SCROLLY * MOUSESCROLL)
        else:
            self.scrollup(e, scroll=SCROLLY * MOUSESCROLL)

    def scrollup(self,e, scroll = SCROLLY):
        if self.scroll == 0: return
        self.scroll -= scroll
        self.barPos -= self.scrollrate
        self.draw()

    def drawScrollbar(self):
        if self.end <= height: return
        self.canvas.create_rectangle(width-SB_WIDTH, 0, width, height, fill="red")
        self.bar = self.canvas.create_rectangle(width - SB_WIDTH + 2 , self.barPos, width - 6, self.barPos +  self.sbHeight, fill="yellow")

    def draw(self):
        self.canvas.delete("all")
        self.drawScrollbar()
        for x,y,c in self.displayList:
            if y - self.scroll >  height: continue
            if y + VSTEP < self.scroll: continue
            if type(c) != type(""):
                # c = c.zoom(6,6)
                self.canvas.create_image(x,y-self.scroll,
                           image=c)
            else:
                self.canvas.create_text(x, y-self.scroll, text=c)

    def load(self, url):
        url.request()
        self.content = url.show()
        self.rerender()
