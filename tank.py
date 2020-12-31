import sys
import random
import bteve as eve
import game

rnd = random.randrange

# res = 1280 x 720
# cells = 1280/80 x 720/80 = 16 x 9
CELLS = (16,9)

# ======================================================================
class TankGame:
    def __init__(self, gd):
        gd.BitmapHandle(0)
        gd.cmd_loadimage(0, 0) # load to loc 0
        # This is 80 x 400 and has 5 images (80x80)
        fn = "fruit.png" 
        with open(fn, "rb") as f:
            gd.load(f)
        gd.cmd_setbitmap(0, eve.ARGB4, 80, 80)

        gd.SaveContext()
        gd.cmd_romfont(31, 34)
        gd.RestoreContext()

        self.initialize()
        self.gd = gd
        self.reset()

    def initialize(self):
        self.board = [[rnd(5) for y in range(CELLS[1])] for x in range(CELLS[0])]

    def reset(self):
        self.off = 0
        #pass

    def update(self, cc):
        pass

    def draw(self):
        off = self.off
        gd = self.gd
        gd.ClearColorRGB(80, 0, 80)
        gd.Clear()
        gd.VertexFormat(0)
        gd.Begin(eve.BITMAPS)
        gd.SaveContext()
        for x in range(CELLS[0]):
            for y in range(CELLS[1]):
                gd.Cell(self.board[x][y])
                # drawing at x > 1120 seems to fail.
                #game.Point(off + x*80, off + y*80).draw(gd)
                gd.Vertex2f(off + x*80, off + y*80)
        gd.RestoreContext()
        #gd.Begin(eve.LINES)
        #gd.LineWidth(10)
        #gd.Vertex2f(off,off)
        #gd.Vertex2f(1280,off)
        gd.swap()

    def play(self):
        while True: # replay game loop
            while True: # game loop
                cc = self.gd.controllers()
                # Start "restarts"
                if cc[0]['b+']: 
                    #print("DBG-start")
                    break
                # Home quits
                if cc[0]['bh'] or cc[1]['bh']:  
                    #print("DBG-home")
                    return
                self.update(cc)
                self.draw()
            self.initialize()
            self.reset()

# ======================================================================
if sys.implementation.name == 'circuitpython':
    def run(gd):
        TankGame(gd).play()
else:
    from spidriver import SPIDriver
    gd = eve.GameduinoSPIDriver(SPIDriver(sys.argv[1]))
    TankGame(gd).play()