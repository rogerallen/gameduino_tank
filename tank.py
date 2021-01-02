import sys
import random
import bteve as eve
import game
import math

rnd = random.randrange

# screen resolution = 1280 x 720
CELL_SIZE = 36
# cells = 720/36 = 20 high.  Eyeballed to find 28 wide.
CELLS = (28,20)
CELL_SIZE_DIV2 = CELL_SIZE/2

BOARD_INIT_STR = (\
    "............................" + # 0
    "............................" + # 1
    "............................" + # 2
    "............................" + # 3
    "............................" + # 4
    "............................" + # 5
    "............................" + # 6
    "........@.........@........." + # 7
    "......@@@@@.@.@@@@@@@@......" + # 8
    ".....@@@@@@@.@@@@@@@@@@....." + # 9
    ".....@@@@@@.@.@@@@@@@@@....." + # 10
    "......@@@@.@@@.@@@@@@@......" + # 11
    "........@.........@........." + # 12
    "............................" + # 13
    "............................" + # 14
    "............................" + # 15
    "............................" + # 16
    "............................" + # 17
    "............................" + # 18
    "............................")  # 19

def str2cell(x,y):
    char = BOARD_INIT_STR[x + CELLS[0]*y]
    if char == '.':
        return 0
    else:
        return 1

# ======================================================================
class Tank:
    def __init__(self, x, y, cells):
        self.x = x
        self.y = y
        self.turret_angle = 0
        self.cell = cells[0]
        self.turret_cell = cells[1]
    
    def update(self, c):
        # U: bdu D: bdd L: bdl R: bdr
        self.x += c['bdr'] * 1 + c['bdl'] * -1
        self.y += c['bdd'] * 1 + c['bdu'] * -1
        # Right Pot: rx, ry (0-31)
        dx, dy = c['rx'] - 16, c['ry'] - 16
        self.turret_angle = (-math.degrees(math.atan2(dy, dx))) % 360
        #print(self.turret_angle)

    def draw(self, gd):
        gd.VertexFormat(0)
        gd.Begin(eve.BITMAPS)
        gd.SaveContext() # ???
        gd.Cell(self.cell)
        gd.Vertex2f(self.x, self.y)
        gd.Cell(self.turret_cell)
        # do some rotation around 40,40 midpoint
        gd.cmd_loadidentity()
        gd.cmd_translate(CELL_SIZE_DIV2,CELL_SIZE_DIV2)
        gd.cmd_rotate(self.turret_angle)
        gd.cmd_translate(-CELL_SIZE_DIV2,-CELL_SIZE_DIV2)
        gd.cmd_setmatrix()
        gd.Vertex2f(self.x, self.y)
        gd.RestoreContext() # ???

# ======================================================================
class TankGame:
    def __init__(self, gd):
        gd.BitmapHandle(0)
        gd.cmd_loadimage(0, 0) # load to loc 0
        # This is 80 x 400 and has 5 images (80x80)
        fn = "tank.png" 
        with open(fn, "rb") as f:
            gd.load(f)
        gd.cmd_setbitmap(0, eve.ARGB4, CELL_SIZE, CELL_SIZE)

        gd.SaveContext()
        gd.cmd_romfont(31, 34)
        gd.RestoreContext()

        self.initialize()
        self.gd = gd
        self.reset()

    def initialize(self):
        self.board = [[str2cell(x,y) for y in range(CELLS[1])] for x in range(CELLS[0])]
        self.tanks = [
            Tank(CELLS[0]*CELL_SIZE/2,   720/8, [2,3]), 
            Tank(CELLS[0]*CELL_SIZE/2, 7*720/8, [2,3])]

    def reset(self):
        self.off = 0
        #pass

    def update(self, cc):
        for i,t in enumerate(self.tanks):
            t.update(cc[i])

    def draw(self):
        off = self.off
        gd = self.gd
        gd.ClearColorRGB(40, 40, 40)
        gd.Clear()
        self.draw_board(gd)
        for t in self.tanks:
            t.draw(gd)
        #gd.Begin(eve.LINES)
        #gd.LineWidth(10)
        #gd.Vertex2f(off,off)
        #gd.Vertex2f(1280,off)
        gd.swap()

    def draw_board(self, gd):
        gd.VertexFormat(0)
        gd.Begin(eve.BITMAPS)
        gd.SaveContext() # ???
        for x in range(CELLS[0]):
            for y in range(CELLS[1]):
                v = self.board[x][y]
                if v < 2:
                    gd.Cell(v)
                    gd.Vertex2f(x*CELL_SIZE, y*CELL_SIZE)
        gd.RestoreContext() # ???

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