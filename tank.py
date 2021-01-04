import sys
import random
import bteve as eve
import game
import math

rnd = random.randrange

# ======================================================================
# screen resolution = 1280 x 720
SCREEN_WIDTH   = 1280
SCREEN_HEIGHT  = 720
CELL_SIZE      = 36
# cells = 720/36 = 20 high.  Eyeballed to find 28 wide.
CELLS          = (28,20)
CELL_SIZE_DIV2 = CELL_SIZE/2
CELL_SIZE_DIV4 = CELL_SIZE/4
WINDOW_WIDTH   = CELLS[0]*CELL_SIZE
WINDOW_HEIGHT  = CELLS[1]*CELL_SIZE

# ======================================================================
# initial map
BOARD_INIT_STR = (\
    "............................" + # 0
    "............................" + # 1
    "............................" + # 2
    "......@....................." + # 3
    "............................" + # 4
    "........................@..." + # 5
    "............................" + # 6
    "........@.........@........." + # 7
    "......@@@@@.@.@@@@@@@@......" + # 8
    ".....@@@@@@@.@@@@@@@@@@....." + # 9
    ".....@@@@@@.@.@@@@@@@@@....." + # 10
    "......@@@@.@@@.@@@@@@@......" + # 11
    "........@.........@........." + # 12
    "............................" + # 13
    "....@......................." + # 14
    "............................" + # 15
    ".......................@...." + # 16
    "............................" + # 17
    "............................" + # 18
    "............................")  # 19

BOARD_OPEN    = 0
BOARD_ROCK    = 1
BOARD_TANK    = 2
BOARD_TURRET  = 3
BOARD_BULLET1 = 4
BOARD_BULLET2 = 5

def str2cell(x,y):
    char = BOARD_INIT_STR[x + CELLS[0]*y]
    if char == '@':
        return BOARD_ROCK
    else:
        return BOARD_OPEN

# ======================================================================
class Bullet:
    VELOCITY=10.0
    def __init__(self):
        self.x = -1
        self.y = -1
        self.angle = -1
        self.cells = [BOARD_BULLET1, BOARD_BULLET2]
        self.cell_index = 0
        self.active = False        
        
    def fire(self, x, y, angle):
        self.x = x
        self.y = y
        self.angle = angle
        self.cell_index = 0
        self.active = True

    def update(self, board, otherTank):
        if self.active:
            #print("active: ",self.x, self.y)
            r = math.radians(self.angle)
            new_x, new_y = self.x + math.cos(r) * Bullet.VELOCITY, self.y + math.sin(r) * Bullet.VELOCITY
            # not going to take up the whole cell, just 1/2 in the center
            new_x0, new_y0 = new_x + CELL_SIZE_DIV4, new_y + CELL_SIZE_DIV4
            new_x1, new_y1 = new_x0 + CELL_SIZE_DIV2, new_y0 + CELL_SIZE_DIV2
            new_cell_i0, new_cell_j0 = int(new_x0/CELL_SIZE), int(new_y0/CELL_SIZE)
            new_cell_i1, new_cell_j1 = int(new_x1/CELL_SIZE), int(new_y1/CELL_SIZE)
            if ((0 < new_x0) and (new_x1 < WINDOW_WIDTH) and   # WALLS
                (0 < new_y0) and (new_y1 < WINDOW_HEIGHT)):
                # inside window
                if ((board[new_cell_i0][new_cell_j0] == BOARD_OPEN) and # ROCKS
                    (board[new_cell_i0][new_cell_j1] == BOARD_OPEN) and 
                    (board[new_cell_i1][new_cell_j0] == BOARD_OPEN) and 
                    (board[new_cell_i1][new_cell_j1] == BOARD_OPEN)):
                    # not a rock
                    other_x0 = otherTank.x + CELL_SIZE_DIV4
                    other_x1 = otherTank.x + CELL_SIZE_DIV4 + CELL_SIZE_DIV2
                    other_y0 = otherTank.y + CELL_SIZE_DIV4
                    other_y1 = otherTank.y + CELL_SIZE_DIV4 + CELL_SIZE_DIV2
                    if ((new_x0 <= other_x1) and (new_x1 >= other_x0) and
                        (new_y0 <= other_y1) and (new_y1 >= other_y0)):
                        # hit other tank FIXME
                        self.active = False
                    else:
                        # hit nothing
                        self.x = new_x
                        self.y = new_y
                else:
                    # onscreen collision with Rock
                    self.active = False # FIXME
            else:
                # offscreen
                self.active = False

    def draw(self, gd):
        if self.active:
            #gd.VertexFormat(0)
            #gd.Begin(eve.BITMAPS)
            #gd.SaveContext() # ???
            gd.Cell(self.cells[self.cell_index])
            #gd.cmd_loadidentity()
            #gd.cmd_translate(CELL_SIZE_DIV2,CELL_SIZE_DIV2)
            #gd.cmd_rotate(self.angle)
            #gd.cmd_translate(-CELL_SIZE_DIV2,-CELL_SIZE_DIV2)
            #gd.cmd_setmatrix()
            gd.Vertex2f(self.x, self.y)
            #gd.RestoreContext() # ???
            self.cell_index = (self.cell_index+1) % len(self.cells)

# ======================================================================
class Tank:
    MAX_VELOCITY=3.0
    TURN_VELOCITY=5.0
    def __init__(self, x, y, cells):
        self.x = x
        self.y = y
        self.angle = 0
        self.turret_angle = 0
        self.cell = cells[0]
        self.turret_cell = cells[1]
        self.bullets = [Bullet(), Bullet(), Bullet()]
        self.last_bzr = False
    
    def update(self, c, board, otherTank):
        self.update_position(c, board)
        self.update_turret(c)
        self.update_bullets(c, board, otherTank)

    def update_position(self, c, board):
        # Left Thumbstick: lx, ly (0-63)
        dx, dy = c['lx'] - 32, c['ly'] - 32
        mag = math.sqrt(dx*dx+dy*dy) / 32
        if dx*dx > 0:
            turn_velocity = 0
            if dx < 0:
                turn_velocity = -Tank.TURN_VELOCITY 
            else: 
                turn_velocity = Tank.TURN_VELOCITY
            self.angle = (self.angle + turn_velocity) % 360
        if dy*dy > 0:
            velocity = 0
            if dy < 0:
                velocity = -mag * Tank.MAX_VELOCITY
            else:
                velocity = mag * Tank.MAX_VELOCITY
            self.collision_update(
                math.cos(math.radians(self.angle)) * velocity,
                math.sin(math.radians(self.angle)) * velocity,
                board)

    def collision_update(self, dx, dy, board):
        "check for wall, rock collision before updating x,y"
        new_x, new_y = self.x + dx, self.y + dy
        # tank is not going to take up the whole cell, just 1/2 in the center
        new_x0, new_y0 = new_x + CELL_SIZE_DIV4, new_y + CELL_SIZE_DIV4
        new_x1, new_y1 = new_x0 + CELL_SIZE_DIV2, new_y0 + CELL_SIZE_DIV2
        new_cell_i0, new_cell_j0 = int(new_x0/CELL_SIZE), int(new_y0/CELL_SIZE)
        new_cell_i1, new_cell_j1 = int(new_x1/CELL_SIZE), int(new_y1/CELL_SIZE)
        if ((0 < new_x0) and (new_x1 < WINDOW_WIDTH) and   # WALLS
            (0 < new_y0) and (new_y1 < WINDOW_HEIGHT) and
            # I think the above prevents out of bounds below...let's see.
            (board[new_cell_i0][new_cell_j0] == BOARD_OPEN) and     # ROCKS
            (board[new_cell_i0][new_cell_j1] == BOARD_OPEN) and 
            (board[new_cell_i1][new_cell_j0] == BOARD_OPEN) and 
            (board[new_cell_i1][new_cell_j1] == BOARD_OPEN)):
            self.x = new_x
            self.y = new_y

    def update_turret(self,c):
        # Right Thumbstick: rx, ry (0-31)
        dx, dy = c['rx'] - 16, c['ry'] - 16
        if dx*dx > 0:
            turret_velocity = 0
            if dx < 0:
                turret_velocity = -Tank.TURN_VELOCITY 
            else: 
                turret_velocity = Tank.TURN_VELOCITY
            self.turret_angle = (self.turret_angle + turret_velocity) % 360
        
    def update_bullets(self, c, board, otherTank):
        # falling edge trigger, see if we can activate a bullet
        fire = not self.last_bzr and c['bzr']
        self.last_bzr = c['bzr']
        for i in range(len(self.bullets)):
            if fire and not self.bullets[i].active:
                # activate a bullet
                bullet_x = self.x + CELL_SIZE_DIV2 * math.cos(math.radians(self.turret_angle))
                bullet_y = self.y + CELL_SIZE_DIV2 * math.sin(math.radians(self.turret_angle))
                self.bullets[i].fire(bullet_x, bullet_y, self.turret_angle)
                fire = False
            else:
                self.bullets[i].update(board, otherTank)

    def draw(self, gd):
        gd.VertexFormat(0)
        gd.Begin(eve.BITMAPS)
        gd.SaveContext() # ???
        gd.Cell(self.cell)
        gd.cmd_loadidentity()
        gd.cmd_translate(CELL_SIZE_DIV2,CELL_SIZE_DIV2)
        gd.cmd_rotate(self.angle)
        gd.cmd_translate(-CELL_SIZE_DIV2,-CELL_SIZE_DIV2)
        gd.cmd_setmatrix()
        gd.Vertex2f(self.x, self.y)
        gd.Cell(self.turret_cell)
        gd.cmd_loadidentity()
        gd.cmd_translate(CELL_SIZE_DIV2,CELL_SIZE_DIV2)
        gd.cmd_rotate(self.turret_angle)
        gd.cmd_translate(-CELL_SIZE_DIV2,-CELL_SIZE_DIV2)
        gd.cmd_setmatrix()
        gd.Vertex2f(self.x, self.y)
        for b in self.bullets:
            b.draw(gd)
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
            Tank(CELLS[0]*CELL_SIZE/2,   720/8, [BOARD_TANK, BOARD_TURRET]), 
            Tank(CELLS[0]*CELL_SIZE/2, 7*720/8, [BOARD_TANK, BOARD_TURRET])]

    def reset(self):
        self.off = 0
        #pass

    def update(self, cc):
        for i,t in enumerate(self.tanks):
            t.update(cc[i], self.board, self.tanks[1-i])

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