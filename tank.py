import sys
import random
import bteve as eve
import game
import math

rnd = random.randrange

# TODO:
# x rocks take damage
# x loading screen mode
# x tank scores & hit display
# o tanks take damage

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
STATUS_WIDTH   = SCREEN_WIDTH - WINDOW_WIDTH
STATUS_WIDTH2  = STATUS_WIDTH/2

GAME_IDLE = 1
GAME_RUNNING = 2

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
BOARD_ROCK_D1 = 2
BOARD_ROCK_D2 = 3
BOARD_ROCK_D3 = 4
BOARD_DRAWABLES = BOARD_ROCK_D3
BOARD_TANK    = 5
BOARD_TURRET  = 6
BOARD_BULLET1 = 7
BOARD_BULLET2 = 8

board2cell = {
    BOARD_OPEN:    0,
    BOARD_ROCK:    1,
    BOARD_ROCK_D1: 1,
    BOARD_ROCK_D2: 1,
    BOARD_ROCK_D3: 1,
    BOARD_TANK:    2,
    BOARD_TURRET:  3,
    BOARD_BULLET1: 4,
    BOARD_BULLET2: 5
    }

def str2cell(x,y):
    char = BOARD_INIT_STR[x + CELLS[0]*y]
    if char == '@':
        return BOARD_ROCK
    else:
        return BOARD_OPEN

def sfx(gd, inst, midi = 0):
    gd.cmd_regwrite(eve.REG_SOUND, inst + (midi << 8))
    gd.cmd_regwrite(eve.REG_PLAY, 1)
    gd.flush()

# ======================================================================
class Bullet:
    VELOCITY=10.0
    def __init__(self, gd):
        self.gd = gd
        self.x = -1
        self.y = -1
        self.angle = -1
        self.rot = 0
        self.cells = [BOARD_BULLET1, BOARD_BULLET2]
        self.cell_index = 0
        self.active = False        
        
    def fire(self, x, y, angle):
        sfx(self.gd, eve.NOTCH)
        self.x = x
        self.y = y
        self.angle = angle
        self.rot = 0
        self.cell_index = 0
        self.active = True

    def update(self, board, otherTank):
        if self.active:
            self.rot += 5
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
                if not board.open_at(new_cell_i0,new_cell_j0):
                    self.active = False
                    board.hit_rock(new_cell_i0,new_cell_j0)
                elif not board.open_at(new_cell_i0,new_cell_j1):
                    self.active = False
                    board.hit_rock(new_cell_i0,new_cell_j1)
                elif not board.open_at(new_cell_i1,new_cell_j0):
                    self.active = False
                    board.hit_rock(new_cell_i1,new_cell_j0)
                elif not board.open_at(new_cell_i1,new_cell_j1):
                    self.active = False
                    board.hit_rock(new_cell_i1,new_cell_j1)
                else:
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
                # offscreen
                self.active = False

    def draw(self):
        gd = self.gd
        if self.active:
            #gd.VertexFormat(0)
            #gd.Begin(eve.BITMAPS)
            #gd.SaveContext() # ???
            gd.Cell(board2cell[self.cells[self.cell_index]])
            gd.cmd_loadidentity()
            gd.cmd_translate(CELL_SIZE_DIV2,CELL_SIZE_DIV2)
            gd.cmd_rotate(self.rot)
            gd.cmd_translate(-CELL_SIZE_DIV2,-CELL_SIZE_DIV2)
            gd.cmd_setmatrix()
            gd.Vertex2f(self.x, self.y)
            #gd.RestoreContext() # ???
            self.cell_index = (self.cell_index+1) % len(self.cells)

# ======================================================================
class Tank:
    MAX_VELOCITY  = 3.0
    TURN_VELOCITY = 5.0
    MAX_DAMAGE    = 4
    def __init__(self, gd, x, y, cells):
        self.gd = gd
        self.x = x
        self.y = y
        self.angle = 0
        self.turret_angle = 0
        self.cell = cells[0]
        self.turret_cell = cells[1]
        self.bullets = [Bullet(gd), Bullet(gd), Bullet(gd)]
        self.last_bzr = False
        self.damage = 0
    
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
            board.open_at(new_cell_i0,new_cell_j0) and
            board.open_at(new_cell_i0,new_cell_j1) and 
            board.open_at(new_cell_i1,new_cell_j0) and
            board.open_at(new_cell_i1,new_cell_j1)):
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

    def draw(self):
        gd = self.gd
        gd.ColorRGB(0xff,0xff,0xff)
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
            b.draw()
        gd.RestoreContext() # ???

    def score(self):
        return self.MAX_DAMAGE - self.damage

# ======================================================================
class TankGame:
    def __init__(self, gd):
        self.gd = gd
        gd.BitmapHandle(0)
        gd.cmd_loadimage(0, 0) # load to loc 0
        # This is 80 x 400 and has 5 images (80x80)
        fn = "tank.png" 
        with open(fn, "rb") as f:
            gd.load(f)
        gd.cmd_setbitmap(0, eve.ARGB4, CELL_SIZE, CELL_SIZE)

        gd.SaveContext()
        gd.cmd_romfont(22, 30)
        gd.cmd_romfont(31, 31)
        gd.cmd_romfont(24, 29)
        gd.RestoreContext()

        self.initialize()
        self.gd = gd
        self.reset()

    def initialize(self):
        self.mode = GAME_IDLE
        self.board = [[str2cell(x,y) for y in range(CELLS[1])] for x in range(CELLS[0])]
        self.tanks = [
            Tank(self.gd, CELLS[0]*CELL_SIZE/2,   720/8, [board2cell[BOARD_TANK], board2cell[BOARD_TURRET]]), 
            Tank(self.gd, CELLS[0]*CELL_SIZE/2, 7*720/8, [board2cell[BOARD_TANK], board2cell[BOARD_TURRET]])]

    def reset(self):
        self.off = 0
        #pass

    def update(self, cc):
        if self.mode == GAME_RUNNING:
            for i,t in enumerate(self.tanks):
                t.update(cc[i], self, self.tanks[1-i])
        else:
            if cc[0]['bb'] or cc[1]['bb']:
                self.mode = GAME_RUNNING

    def draw(self):
        off = self.off
        gd = self.gd
        gd.ClearColorRGB(40, 40, 40)
        gd.Clear()
        self.draw_board()
        self.draw_score()
        if self.mode == GAME_RUNNING:
            for t in self.tanks:
                t.draw()
        else:
            self.draw_intro()
        gd.swap()

    def draw_intro(self):
        gd = self.gd
        gd.ColorRGB(0xd0,0xd0,0x00)
        lh = 32
        gd.cmd_text(int(WINDOW_WIDTH/2), int((1/3)*WINDOW_HEIGHT), 31, eve.OPT_CENTER, "Two Player Tank")
        gd.cmd_text(int(WINDOW_WIDTH/2), int((2/3)*WINDOW_HEIGHT), 31, eve.OPT_CENTER, "Press B to start.")
        gd.cmd_text(int(WINDOW_WIDTH/2), int((2/3)*WINDOW_HEIGHT)+2*lh, 30, eve.OPT_CENTER, "Thumbsticks move tank & turret")
        gd.cmd_text(int(WINDOW_WIDTH/2), int((2/3)*WINDOW_HEIGHT)+3*lh, 30, eve.OPT_CENTER, "Right trigger fires bullets.")
    
    def draw_score(self):
        gd = self.gd
        gd.ColorRGB(0xf0,0xf0,0xf0)
        lh = 32
        gd.cmd_text(WINDOW_WIDTH + int(STATUS_WIDTH2), int((1/3)*WINDOW_HEIGHT), 29, eve.OPT_CENTER, "Player 1")
        score = "X " * self.tanks[0].score()
        gd.ColorRGB(0xf0,0x00,0x00)
        gd.cmd_text(WINDOW_WIDTH + int(STATUS_WIDTH2), int((1/3)*WINDOW_HEIGHT) + lh, 29, eve.OPT_CENTER, score)
        gd.ColorRGB(0xf0,0xf0,0xf0)
        gd.cmd_text(WINDOW_WIDTH + int(STATUS_WIDTH2), int((2/3)*WINDOW_HEIGHT), 29, eve.OPT_CENTER, "Player 2")
        score = "X " * self.tanks[1].score()
        gd.ColorRGB(0xf0,0x00,0x00)
        gd.cmd_text(WINDOW_WIDTH + int(STATUS_WIDTH2), int((2/3)*WINDOW_HEIGHT) + lh, 29, eve.OPT_CENTER, score)

    def draw_board(self):
        gd = self.gd
        gd.VertexFormat(0)
        gd.Begin(eve.BITMAPS)
        gd.SaveContext() # ???
        for x in range(CELLS[0]):
            for y in range(CELLS[1]):
                v = self.board[x][y]
                if v <= BOARD_DRAWABLES:
                    gd.Cell(board2cell[v])
                    if v - BOARD_ROCK > 0:
                        gd.cmd_translate(0,(v-BOARD_ROCK)*CELL_SIZE_DIV4)
                        gd.cmd_setmatrix()
                    gd.Vertex2f(x*CELL_SIZE, y*CELL_SIZE)
                    if v - BOARD_ROCK > 0:
                        gd.cmd_translate(0,-(v-BOARD_ROCK)*CELL_SIZE_DIV4)
                        gd.cmd_setmatrix()
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
    
    def open_at(self, x, y):
        return self.board[x][y] == BOARD_OPEN

    def hit_rock(self, x, y):
        v = self.board[x][y]
        v += 1
        if v > BOARD_ROCK_D3:
            v = BOARD_OPEN
        self.board[x][y] = v
        
# ======================================================================
if sys.implementation.name == 'circuitpython':
    def run(gd):
        TankGame(gd).play()
else:
    from spidriver import SPIDriver
    gd = eve.GameduinoSPIDriver(SPIDriver(sys.argv[1]))
    TankGame(gd).play()