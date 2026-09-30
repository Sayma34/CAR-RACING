
from OpenGL.GL import *
from OpenGL.GLUT import *
import OpenGL.GLUT as glut
from OpenGL.GLU import *
import random
import time
import math

WINDOW_WIDTH, WINDOW_HEIGHT = 600, 800

START, PLAYING, PAUSED, GAMEOVER = 0, 1, 2, 3
game_state = START

TOP_DOWN, FIRST_PERSON = 0, 1
view_mode = TOP_DOWN

CLEAR, RAIN, SNOW = 0, 1, 2
weather_state = CLEAR
rain_particles = []
snow_particles = []

FOREST, DESERT, NIGHT_CITY = 0, 1, 2
biome_state = FOREST

SHIELD, NITRO, MAGNET = 3, 4, 5 
shield_active = False
nitro_timer = 0
magnet_timer = 0
cheat_enabled = False
cheat_timer = 0
obstacles_hit = 0
police_active = False

camera_y = 0
speed = 5.0
max_speed = 15.0
camera_angle = 0.3
player_dx = 0 

player_x = 300
player_y_offset = 100 
player_width = 40
player_height = 60
player_lives = 3
player_color = [1.0, 0.0, 0.0]

ROAD_LEFT = 150
ROAD_RIGHT = 450
LANE_WIDTH = 100

entities = []
trees = []
score = 0
distance_traveled = 0
shake_timer = 0
last_spawn_camera_y = -300 
spawn_interval = 400

def draw_jagged_polygon_3d(cx, cy, cz, radius, segments, color, seed_val):
    
    random.seed(seed_val)
    glColor3f(*color)
    glBegin(GL_TRIANGLES)
    verts = []
    for i in range(segments + 1):
        angle = 2.0 * math.pi * i / segments
        r = radius * (0.8 + random.random() * 0.4)
        verts.append((cx + r * math.cos(angle), cy + r * math.sin(angle), float(cz)))
    
    for i in range(segments):
        glVertex3f(cx, cy, float(cz))
        glVertex3f(*verts[i])
        glVertex3f(*verts[i+1])
    glEnd()
    random.seed(int(time.time()))

def draw_sphere_3d(cx, cy, cz, radius, color):
    
    glColor3f(*color)
    steps = 8
    for i in range(-steps, steps + 1):
        phi = math.pi * 0.5 * i / steps
        r = radius * math.cos(phi)
        z = cz + radius * math.sin(phi)
        glBegin(GL_TRIANGLES)
        for j in range(12):
            angle1 = 2.0 * math.pi * j / 12
            angle2 = 2.0 * math.pi * (j+1) / 12
            glVertex3f(cx, cy, z)
            glVertex3f(cx + r * math.cos(angle1), cy + r * math.sin(angle1), z)
            glVertex3f(cx + r * math.cos(angle2), cy + r * math.sin(angle2), z)
        glEnd()

def draw_circle_3d(cx, cy, cz, radius):
    glBegin(GL_TRIANGLES)
    for i in range(20):
        angle1 = 2.0 * math.pi * i / 20
        angle2 = 2.0 * math.pi * (i+1) / 20
        glVertex3f(cx, cy, float(cz))
        glVertex3f(cx + radius * math.cos(angle1), cy + radius * math.sin(angle1), float(cz))
        glVertex3f(cx + radius * math.cos(angle2), cy + radius * math.sin(angle2), float(cz))
    glEnd()

def draw_filled_rect_3d(x, y, z, w, h, depth, color):

    glColor3f(color[0]*0.7, color[1]*0.7, color[2]*0.7)
    glBegin(GL_TRIANGLES)
    glVertex3f(x-w/2, y+h/2, z); glVertex3f(x+w/2, y+h/2, z); glVertex3f(x+w/2, y+h/2, z+depth)
    glVertex3f(x-w/2, y+h/2, z); glVertex3f(x+w/2, y+h/2, z+depth); glVertex3f(x-w/2, y+h/2, z+depth)
    
    glVertex3f(x-w/2, y-h/2, z); glVertex3f(x+w/2, y-h/2, z); glVertex3f(x+w/2, y-h/2, z+depth)
    glVertex3f(x-w/2, y-h/2, z); glVertex3f(x+w/2, y-h/2, z+depth); glVertex3f(x-w/2, y-h/2, z+depth)
    
    glVertex3f(x-w/2, y-h/2, z); glVertex3f(x-w/2, y+h/2, z); glVertex3f(x-w/2, y+h/2, z+depth)
    glVertex3f(x-w/2, y-h/2, z); glVertex3f(x-w/2, y+h/2, z+depth); glVertex3f(x-w/2, y-h/2, z+depth)
    
    glVertex3f(x+w/2, y-h/2, z); glVertex3f(x+w/2, y+h/2, z); glVertex3f(x+w/2, y+h/2, z+depth)
    glVertex3f(x+w/2, y-h/2, z); glVertex3f(x+w/2, y+h/2, z+depth); glVertex3f(x+w/2, y-h/2, z+depth)
    glEnd()
    
    glColor3f(*color)
    glBegin(GL_TRIANGLES)
    glVertex3f(x-w/2, y-h/2, z+depth); glVertex3f(x+w/2, y-h/2, z+depth); glVertex3f(x+w/2, y+h/2, z+depth)
    glVertex3f(x-w/2, y-h/2, z+depth); glVertex3f(x+w/2, y+h/2, z+depth); glVertex3f(x-w/2, y+h/2, z+depth)
    glEnd()

def midpoint_line(x1, y1, x2, y2):
    glBegin(GL_POINTS)
    dx, dy = abs(x2-x1), abs(y2-y1)
    sx = 1 if x1 < x2 else -1
    sy = 1 if y1 < y2 else -1
    err = dx - dy
    while True:
        glVertex2f(x1, y1)
        if x1 == x2 and y1 == y2: break
        e2 = 2 * err
        if e2 > -dy: err -= dy; x1 += sx
        if e2 < dx: err += dx; y1 += sy
    glEnd()

def draw_tree(x, y):
    
    y_rel = y - camera_y
    x_offset = (WINDOW_HEIGHT - (y_rel + WINDOW_HEIGHT/2)) * camera_angle * 0.02
    cx = x + x_offset
    draw_filled_rect_3d(cx, y, 0, 22, 22, 100, [0.2, 0.1, 0.05])
    
    glColor3f(0.15, 0.08, 0.03)
    glBegin(GL_LINES)
    glVertex3f(cx, y, 60); glVertex3f(cx-15, y+10, 110)
    glVertex3f(cx, y, 65); glVertex3f(cx+15, y-10, 105)
    glVertex3f(cx, y, 70); glVertex3f(cx, y+15, 120)
    glEnd()

    draw_sphere_3d(cx, y, 100, 40, [0.0, 0.3, 0.0])   # Base
    draw_sphere_3d(cx-20, y+10, 90, 25, [0.0, 0.25, 0.0]) # Left side cluster
    draw_sphere_3d(cx+20, y-10, 85, 28, [0.0, 0.35, 0.0]) # Right side cluster
    draw_sphere_3d(cx, y, 125, 30, [0.1, 0.5, 0.1])   # Top tier
    draw_sphere_3d(cx+10, y+15, 140, 15, [0.2, 0.6, 0.2]) # Top peak cluster

def draw_car(x, y, w, h, color):
    
    y_rel = y - camera_y
    x_offset = (WINDOW_HEIGHT - (y_rel + WINDOW_HEIGHT/2)) * camera_angle * 0.02
    cx, cy = int(x + x_offset), y
    hw, hh = w // 2, h // 2
    
    draw_filled_rect_3d(cx, cy, 0, w, h, 12, color)
    
    glColor3f(0.7, 0.7, 0.8)
    glBegin(GL_LINES)
    glVertex3f(cx-hw+4, cy+hh-12, 12.1); glVertex3f(cx+hw-4, cy+hh-12, 12.1)
    glVertex3f(cx+hw-4, cy+hh-12, 12.1); glVertex3f(cx+hw-8, cy, 26)
    glVertex3f(cx+hw-8, cy, 26); glVertex3f(cx-hw+8, cy, 26)
    glVertex3f(cx-hw+8, cy, 26); glVertex3f(cx-hw+4, cy+hh-12, 12.1)
    glEnd()

    glColor3f(0.5, 0.8, 1)
    glBegin(GL_TRIANGLES)
    glVertex3f(cx-hw+4, cy+hh-12, 12.1); glVertex3f(cx+hw-4, cy+hh-12, 12.1); glVertex3f(cx+hw-8, cy, 26)
    glVertex3f(cx-hw+4, cy+hh-12, 12.1); glVertex3f(cx+hw-8, cy, 26); glVertex3f(cx-hw+8, cy, 26)
    glEnd()
    glColor3f(1, 1, 1)
    glBegin(GL_TRIANGLES)
    glVertex3f(cx, cy+hh-10, 13); glVertex3f(cx+5, cy+hh-10, 13); glVertex3f(cx-5, cy+5, 25)
    glVertex3f(cx+5, cy+hh-10, 13); glVertex3f(cx-5, cy+5, 25); glVertex3f(cx-10, cy+5, 25)
    glEnd()
    
    rc = [min(1.0, c*1.2) for c in color]
    draw_filled_rect_3d(cx, cy-hh//3, 26, w-14, h//2, 2, rc)

    spd_c = [c*0.7 for c in color]
    draw_filled_rect_3d(cx, cy-hh+4, 12, w+8, 10, 4, spd_c) # Wing plate
    draw_filled_rect_3d(cx-hw+4, cy-hh+4, 0, 4, 4, 12, spd_c) # Left support
    draw_filled_rect_3d(cx+hw-4, cy-hh+4, 0, 4, 4, 12, spd_c) # Right support
    
    draw_filled_rect_3d(cx-hw-4, cy+10, 8, 8, 4, 4, color)
    draw_filled_rect_3d(cx+hw+4, cy+10, 8, 8, 4, 4, color)
    
    draw_filled_rect_3d(cx-hw+12, cy-hh-4, 2, 6, 8, 4, [0.3, 0.3, 0.3])
    draw_filled_rect_3d(cx+hw-12, cy-hh-4, 2, 6, 8, 4, [0.3, 0.3, 0.3])

    wheel_w, wheel_h = 8, 12
    for wx, wy in [(cx-hw-2, cy+hh-15), (cx+hw+2, cy+hh-15), (cx-hw-2, cy-hh+15), (cx+hw+2, cy-hh+15)]:
        draw_filled_rect_3d(wx, wy, 0, wheel_w, wheel_h, 8, [0.1, 0.1, 0.1])
        glColor3f(0.6, 0.6, 0.6); draw_circle_3d(wx, wy, 8.1, 3.5)

    glColor3f(1, 1, 0.9); draw_circle_3d(cx-hw+8, cy+hh-2, 12.2, 5)
    draw_circle_3d(cx+hw-8, cy+hh-2, 12.2, 5)
    draw_filled_rect_3d(cx-hw+10, cy-hh+2, 8, 10, 4, 2, [1, 0, 0])
    draw_filled_rect_3d(cx+hw-10, cy-hh+2, 8, 10, 4, 2, [1, 0, 0])

def draw_coin(x, y):
    #Rotating 3D Golden Coin
    y_rel = y - camera_y
    x_offset = (WINDOW_HEIGHT - (y_rel + WINDOW_HEIGHT/2)) * camera_angle * 0.02
    cx = x + x_offset
    glPushMatrix(); glTranslatef(cx, y, 12); glRotatef(time.time() * 200, 0, 1, 0)
    glColor3f(0.8, 0.6, 0.0); draw_sphere_3d(0, 0, 0, 14, [0.8, 0.6, 0.0])
    draw_sphere_3d(0, 0, 0, 11, [1.0, 0.84, 0.0])
    glColor3f(0.5, 0.4, 0.0); draw_filled_rect_3d(0, 0, 1, 4, 15, 1, [0.5, 0.4, 0.0])
    glPopMatrix()

def draw_barrel(x, y):
    #3D Oil Barrel (Forest obstacle)
    y_rel = y - camera_y
    x_offset = (WINDOW_HEIGHT - (y_rel + WINDOW_HEIGHT/2)) * camera_angle * 0.02
    cx = x + x_offset
    draw_filled_rect_3d(cx, y, 0, 30, 30, 45, [0.4, 0.1, 0.1]) # Body
    glColor3f(0.2, 0.2, 0.2) # Rims
    midpoint_line(cx-15, y, cx+15, y) # Visual ring

def draw_barrier(x, y):
    #Concrete Barrier 
    y_rel = y - camera_y
    x_offset = (WINDOW_HEIGHT - (y_rel + WINDOW_HEIGHT/2)) * camera_angle * 0.02
    cx = x + x_offset
    draw_filled_rect_3d(cx, y, 0, 50, 20, 30, [0.6, 0.6, 0.6])
    glColor3f(0.8, 0, 0) # Stripe
    draw_filled_rect_3d(cx, y, 31, 50, 5, 2, [0.8, 0, 0])

def draw_cactus(x, y):
    # Desert tree replacement
    y_rel = y - camera_y
    x_offset = (WINDOW_HEIGHT - (y_rel + WINDOW_HEIGHT/2)) * camera_angle * 0.02
    cx = x + x_offset
    draw_filled_rect_3d(cx, y, 0, 14, 70, 18, [0.1, 0.5, 0.15])
    draw_filled_rect_3d(cx - 18, y + 12, 0, 12, 28, 14, [0.1, 0.5, 0.15])
    draw_filled_rect_3d(cx + 18, y - 8, 0, 12, 24, 14, [0.1, 0.5, 0.15])

def draw_building(x, y):
    # City tree replacement
    y_rel = y - camera_y
    x_offset = (WINDOW_HEIGHT - (y_rel + WINDOW_HEIGHT/2)) * camera_angle * 0.02
    cx = x + x_offset
    draw_filled_rect_3d(cx, y, 0, 48, 110, 55, [0.25, 0.28, 0.35])
    glColor3f(0.9, 0.8, 0.25)
    for window_y in range(int(y - 35), int(y + 45), 25):
        for window_x in (-12, 12):
            draw_filled_rect_3d(cx + window_x, window_y, 56, 7, 10, 2, [0.9, 0.8, 0.25])

def draw_sandbags(x, y):
    #Sandbag pile
    y_rel = y - camera_y
    x_offset = (WINDOW_HEIGHT - (y_rel + WINDOW_HEIGHT/2)) * camera_angle * 0.02
    cx = x + x_offset
    for ox, oy, oz in [(-10, -5, 0), (10, 5, 0), (0, 0, 10)]:
        draw_filled_rect_3d(cx+ox, y+oy, oz, 25, 15, 10, [0.76, 0.7, 0.5])

def draw_magnet(x, y):
    # Magnet
    y_rel = y - camera_y
    x_offset = (WINDOW_HEIGHT - (y_rel + WINDOW_HEIGHT/2)) * camera_angle * 0.02
    cx = x + x_offset
    
    draw_filled_rect_3d(cx - 10, y + 5, 12, 8, 20, 8, [1, 0, 0])
    draw_filled_rect_3d(cx + 10, y + 5, 12, 8, 20, 8, [1, 0, 0])
    draw_filled_rect_3d(cx, y - 10, 12, 28, 8, 8, [1, 0, 0])
    
    draw_filled_rect_3d(cx - 10, y + 15, 12, 8, 5, 9, [0.8, 0.8, 0.8])
    draw_filled_rect_3d(cx + 10, y + 15, 12, 8, 5, 9, [0.8, 0.8, 0.8])

def draw_shield(x, y):
    
    y_rel = y - camera_y
    x_offset = (WINDOW_HEIGHT - (y_rel + WINDOW_HEIGHT/2)) * camera_angle * 0.02
    cx = x + x_offset
    
    draw_filled_rect_3d(cx, y + 5, 10, 26, 20, 5, [0, 0.8, 1])
    draw_filled_rect_3d(cx, y - 10, 10, 20, 10, 5, [0, 0.8, 1]) # Taper
    draw_filled_rect_3d(cx, y - 18, 10, 10, 6, 5, [0, 0.8, 1]) # Point
    
    draw_filled_rect_3d(cx, y + 5, 10, 26, 5, 6, [1, 1, 1])
    draw_filled_rect_3d(cx, y, 10, 6, 25, 6, [1, 1, 1])

def draw_nitro(x, y):
    #Speed Booster
    y_rel = y - camera_y
    x_offset = (WINDOW_HEIGHT - (y_rel + WINDOW_HEIGHT/2)) * camera_angle * 0.02
    cx = x + x_offset
    
    colors = [[1, 0, 0], [1, 0.5, 0], [1, 1, 0]]
    
    for i in range(3):
        offset_y = i * 15 - 10
        c = colors[i]
        glColor3f(*c)
        glBegin(GL_TRIANGLES)
        glVertex3f(cx, y + offset_y + 15, 15)
        glVertex3f(cx - 15, y + offset_y, 15)
        glVertex3f(cx + 15, y + offset_y, 15)
        glEnd()
        
        glColor3f(c[0]*0.7, c[1]*0.7, c[2]*0.7)
        glBegin(GL_TRIANGLES)
        glVertex3f(cx, y + offset_y + 15, 15); glVertex3f(cx - 15, y + offset_y, 15); glVertex3f(cx - 15, y + offset_y, 5)
        glVertex3f(cx, y + offset_y + 15, 15); glVertex3f(cx + 15, y + offset_y, 15); glVertex3f(cx + 15, y + offset_y, 5)
        glEnd()

def draw_powerup(x, y, p_type):
    if p_type == MAGNET:
        draw_magnet(x, y)
    elif p_type == SHIELD:
        draw_shield(x, y)
    else: # NITRO
        draw_nitro(x, y)

def draw_dashboard():
    glDisable(GL_DEPTH_TEST)
    glMatrixMode(GL_PROJECTION); glPushMatrix(); glLoadIdentity(); gluOrtho2D(0, 600, 0, 800)
    glMatrixMode(GL_MODELVIEW); glPushMatrix(); glLoadIdentity()
    
    glColor3f(0.08, 0.08, 0.08)
    glBegin(GL_TRIANGLES)
    glVertex2f(0,0); glVertex2f(600,0); glVertex2f(600,180)
    glVertex2f(0,0); glVertex2f(600,180); glVertex2f(0,180)
    glEnd()
    
    rot = -player_dx * 5.0 
    glPushMatrix(); glTranslatef(300, 60, 0); glRotatef(rot, 0, 0, 1)
    
    glColor3f(0.15, 0.15, 0.15); draw_circle_3d(0, 0, 0, 85)
    glColor3f(0.05, 0.05, 0.05); draw_circle_3d(0, 0, 0, 70)
    
    glColor3f(0.3, 0.3, 0.3)
    for a in [0, 120, 240]:
        glPushMatrix(); glRotatef(a, 0, 0, 1); glBegin(GL_TRIANGLES)
        glVertex2f(-10, 0); glVertex2f(10, 0); glVertex2f(8, 70)
        glVertex2f(-10, 0); glVertex2f(8, 70); glVertex2f(-8, 70)
        glEnd(); glPopMatrix()
        
    glColor3f(0.2, 0.2, 0.25); draw_circle_3d(0, 0, 0, 25)
    glColor3f(1, 0.8, 0); draw_text(-8, -4, "V8", [1,1,0]) 
    
    glColor3f(0.8, 0.6, 0.5) 
    glBegin(GL_TRIANGLES) 
    glVertex2f(-80, -10); glVertex2f(-65, -10); glVertex2f(-60, 30)
    glVertex2f(-80, -10); glVertex2f(-60, 30); glVertex2f(-75, 30)
    glEnd()
    glBegin(GL_TRIANGLES) 
    glVertex2f(65, -10); glVertex2f(80, -10); glVertex2f(75, 30)
    glVertex2f(65, -10); glVertex2f(75, 30); glVertex2f(60, 30)
    glEnd()
    
    glPopMatrix() 
    
    glColor3f(0.7, 0.7, 0.7)
    glBegin(GL_LINES) 
    glVertex2f(20, 180); glVertex2f(580, 180)
    glVertex2f(580, 180); glVertex2f(600, 800)
    glVertex2f(600, 800); glVertex2f(0, 800)
    glVertex2f(0, 800); glVertex2f(20, 180)
    glEnd()

    glColor3f(0.9, 0.9, 0.9)
    glBegin(GL_TRIANGLES); glVertex2f(50, 750); glVertex2f(150, 780); glVertex2f(80, 700); glEnd()
    
    glColor3f(0.7, 0.5, 0.4)
    glBegin(GL_TRIANGLES) # Left Arm
    glVertex2f(150, -50); glVertex2f(230, -50); glVertex2f(235, 60 + rot/5)
    glVertex2f(150, -50); glVertex2f(235, 60 + rot/5); glVertex2f(220, 60 + rot/5)
    glEnd()
    glBegin(GL_TRIANGLES) # Right Arm
    glVertex2f(450, -50); glVertex2f(370, -50); glVertex2f(365, 60 - rot/5)
    glVertex2f(450, -50); glVertex2f(365, 60 - rot/5); glVertex2f(380, 60 - rot/5)
    glEnd()

    glPopMatrix(); glMatrixMode(GL_PROJECTION); glPopMatrix(); glMatrixMode(GL_MODELVIEW); glEnable(GL_DEPTH_TEST)

def draw_text(x, y, text, color=[1, 1, 1]):
    glColor3f(*color); glRasterPos2f(x, WINDOW_HEIGHT - y)
    for ch in text: glut.glutBitmapCharacter(glut.GLUT_BITMAP_HELVETICA_18, ord(ch))

def spawn_entity():
    global entities, last_spawn_camera_y, trees, camera_y
    x, y = random.choice([200, 300, 400]), camera_y + WINDOW_HEIGHT + 100
    etype = random.randint(0, 100)
    car_color = random.choice([[1,0,0.5], [0,1,1], [1,1,0], [0.5,0,1], [0,1,0.5]])
    
    if etype < 40: entities.append({'type': 0, 'x': x, 'y': y, 'color': [0.4, 0.4, 0.4], 'w': 30, 'h': 30, 'speed_mod': 0}) # Obstacle
    elif etype < 80: entities.append({'type': 1, 'x': x, 'y': y, 'color': car_color, 'w': 40, 'h': 60, 'speed_mod': random.uniform(0.3, 0.7), 'target_x': x, 'ai_timer': 60})
    elif etype < 90: entities.append({'type': 2, 'x': x, 'y': y, 'w': 25, 'h': 25})
    else: entities.append({'type': random.choice([SHIELD, NITRO, MAGNET]), 'x': x, 'y': y, 'w': 30, 'h': 30})
    trees.append({'x': ROAD_LEFT - 80, 'y': y})
    trees.append({'x': ROAD_RIGHT + 80, 'y': y})
    last_spawn_camera_y = camera_y

def update():
    global camera_y, player_x, player_dx, entities, trees, game_state, score, distance_traveled, last_spawn_camera_y, speed, shake_timer, player_lives, weather_state, biome_state, rain_particles, snow_particles, shield_active, nitro_timer, magnet_timer, cheat_enabled, cheat_timer, obstacles_hit, police_active
    if game_state != PLAYING: return
    
    if cheat_enabled:
        cheat_timer -= 1
        if cheat_timer <= 0: cheat_enabled = False

    cur_speed = speed * 2 if nitro_timer > 0 else speed
    camera_y += cur_speed; distance_traveled += cur_speed; score = int(distance_traveled / 100)
    if nitro_timer > 0: nitro_timer -= 1
    if magnet_timer > 0: magnet_timer -= 1
    biome_state = score // 1000 % 3; weather_state = (int(distance_traveled) // 3000) % 3
    if weather_state == RAIN:
        if len(rain_particles) < 100: rain_particles.append([random.randint(0, 600), float(800), float(random.randint(10, 20))])
        for p in rain_particles: p[1] -= 20; (p[1] < 0 and (p.__setitem__(1, 800.0), p.__setitem__(0, random.randint(0, 600))))
    elif weather_state == SNOW:
        if len(snow_particles) < 100: snow_particles.append([random.randint(0, 600), float(800), float(random.randint(2, 5))])
        for p in snow_particles: p[1] -= 5; p[0] += math.sin(time.time() + p[1]/10) * 2; (p[1] < 0 and (p.__setitem__(1, 800.0), p.__setitem__(0, random.randint(0, 600))))
    friction = 0.85 if weather_state == RAIN else 0.95
    player_x += player_dx; player_dx *= friction; player_x = max(ROAD_LEFT + 25, min(ROAD_RIGHT - 25, player_x))
    
    pworld_y = camera_y + player_y_offset

    if cheat_enabled:
        for e in entities:
            if abs(e['x'] - player_x) < 50 and 0 < (e['y'] - pworld_y) < 300:
                player_dx += 5 if player_x < 300 else -5 

    if speed < max_speed: speed += 0.0015 
    for e in entities[:]:
        if magnet_timer > 0 and e['type'] == 2 and abs(e['x'] - player_x) < 200: e['x'] += 5 if player_x > e['x'] else -5
        if e['type'] == 1:
            e['y'] += speed * e['speed_mod']; e['ai_timer'] -= 1
            if e['ai_timer'] <= 0: e['target_x'] = random.choice([200, 300, 400]); e['ai_timer'] = random.randint(60, 180)
            if abs(e['x'] - e['target_x']) > 2: e['x'] += 2 if e['target_x'] > e['x'] else -2
        if abs(player_x - e['x']) < (player_width/2 + e['w']/2) and abs(pworld_y - e['y']) < (player_height/2 + e['h']/2):
            if e['type'] == 2: distance_traveled += 500
            elif e['type'] == SHIELD: shield_active = True
            elif e['type'] == NITRO: nitro_timer = 180
            elif e['type'] == MAGNET: magnet_timer = 300
            
            else:
                if e['type'] == 0:  
                    obstacles_hit += 1
                    if obstacles_hit >= 3: police_active = True
                    entities.remove(e); continue 
                
                if cheat_enabled: pass 
                elif shield_active: shield_active = False
                else:
                    player_lives -= 1; shake_timer = 15
                    if player_lives <= 0: game_state = GAMEOVER
            entities.remove(e); continue
        if e['y'] < camera_y - 100: entities.remove(e)
    if camera_y - last_spawn_camera_y > max(150, spawn_interval - int(distance_traveled/100)): spawn_entity()
    for t in trees[:]: (t['y'] < camera_y - 100 and trees.remove(t))
    if shake_timer > 0: shake_timer -= 1

def idle(): update(); time.sleep(0.01); glutPostRedisplay()

def keyboard(key, x, y):
    global player_x, player_dx, game_state, camera_y, entities, trees, score, distance_traveled, player_lives, speed, view_mode, last_spawn_camera_y, weather_state, biome_state, shield_active, nitro_timer, magnet_timer, cheat_enabled, cheat_timer, obstacles_hit, police_active
    if key == b'c': 
        cheat_enabled = True
        cheat_timer = 600 # 10 seconds
    if key == b'a': 
        if weather_state == RAIN: player_dx -= 3
        else: player_x -= 20
    elif key == b'd':
        if weather_state == RAIN: player_dx += 3
        else: player_x += 20
    elif key == b'q': view_mode = FIRST_PERSON
    elif key == b'e': view_mode = TOP_DOWN
    elif key in [b' ', b'\r', b'\n']:
        if game_state == START: game_state = PLAYING; spawn_entity()
        else: game_state = PLAYING if game_state == PAUSED else PAUSED
    elif key == b'r':
        game_state = PLAYING; camera_y = 0; player_x = 300; player_dx = 0; entities = []; trees = []; score = 0; distance_traveled = 0; player_lives = 3; speed = 5.0; last_spawn_camera_y = -300; weather_state = CLEAR; biome_state = FOREST; shield_active = False; nitro_timer = 0; magnet_timer = 0; obstacles_hit = 0; police_active = False; spawn_entity()

def display():
    br, bg, bb = (0.4, 0.6, 1.0) if biome_state == FOREST else (0.8, 0.7, 0.2) if biome_state == DESERT else (0.05, 0.05, 0.15)
    gr, gg, gb = (0.1, 0.5, 0.1) if biome_state == FOREST else (0.7, 0.6, 0.2) if biome_state == DESERT else (0.1, 0.1, 0.2)
    if weather_state == RAIN: br*=0.6; bg*=0.6; bb*=0.6; gr*=0.8; gg*=0.8; gb*=0.8
    elif weather_state == SNOW: gr, gg, gb = 0.9, 0.9, 1.0
    glClearColor(br, bg, bb, 1); glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT); glEnable(GL_DEPTH_TEST)
    glMatrixMode(GL_PROJECTION); glLoadIdentity()
    if view_mode == FIRST_PERSON: gluPerspective(60, 600/800, 1, 20000); glMatrixMode(GL_MODELVIEW); glLoadIdentity(); gluLookAt(player_x, player_y_offset, 40, player_x, player_y_offset + 100, 30, 0, 0, 1)
    else: glOrtho(0, 600, 0, 800, -100, 500); glMatrixMode(GL_MODELVIEW); glLoadIdentity(); (shake_timer > 0 and glTranslatef(random.uniform(-5, 5), random.uniform(-5, 5), 0))
    glPushMatrix(); glTranslatef(0, -camera_y, 0)
    glColor3f(gr, gg, gb); 
    glBegin(GL_TRIANGLES)
    glVertex2f(-2000, 0); glVertex2f(ROAD_LEFT-20, 0); glVertex2f(ROAD_LEFT-20, camera_y+15000)
    glVertex2f(-2000, 0); glVertex2f(ROAD_LEFT-20, camera_y+15000); glVertex2f(-2000, camera_y+15000)
    
    glVertex2f(ROAD_RIGHT+20, 0); glVertex2f(WINDOW_WIDTH+2000, 0); glVertex2f(WINDOW_WIDTH+2000, camera_y+15000)
    glVertex2f(ROAD_RIGHT+20, 0); glVertex2f(WINDOW_WIDTH+2000, camera_y+15000); glVertex2f(ROAD_RIGHT+20, camera_y+15000)
    glEnd()
    glColor3f(0.2, 0.2, 0.2); 
    glBegin(GL_TRIANGLES)
    glVertex2f(ROAD_LEFT, 0); glVertex2f(ROAD_RIGHT, 0); glVertex2f(ROAD_RIGHT, camera_y+15000)
    glVertex2f(ROAD_LEFT, 0); glVertex2f(ROAD_RIGHT, camera_y+15000); glVertex2f(ROAD_LEFT, camera_y+15000)
    glEnd()
    glColor3f(1, 1, 1); sy = int(camera_y/100)*100
    for y in range(sy-100, sy+1000, 100): midpoint_line(250, y, 250, y+40); midpoint_line(350, y, 350, y+40)
    for t in trees: (draw_tree(t['x'], t['y']) if biome_state == FOREST else draw_cactus(t['x'], t['y']) if biome_state == DESERT else draw_building(t['x'], t['y']))
    for e in entities: 
        if e['type'] == 1: draw_car(e['x'], e['y'], e['w'], e['h'], e['color'])
        elif e['type'] == 2: draw_coin(e['x'], e['y'])
        elif e['type'] >= 3: draw_powerup(e['x'], e['y'], e['type'])
        else: # Obstacles as Biome 
            if biome_state == FOREST: draw_barrel(e['x'], e['y'])
            elif biome_state == DESERT: draw_sandbags(e['x'], e['y'])
            else: draw_barrier(e['x'], e['y'])
    if view_mode == TOP_DOWN: px, py = player_x, camera_y+player_y_offset; (shield_active and (glColor3f(0,0.8,1), draw_circle_3d(px, py, 35, 35))); draw_car(px, py, player_width, player_height, player_color)
    glPopMatrix()
    (view_mode == FIRST_PERSON and draw_dashboard())
    glDisable(GL_DEPTH_TEST); glMatrixMode(GL_PROJECTION); glPushMatrix(); glLoadIdentity(); gluOrtho2D(0, 600, 0, 800); glMatrixMode(GL_MODELVIEW); glPushMatrix(); glLoadIdentity()
    if weather_state == RAIN: glColor3f(0.6, 0.6, 1.0); ([midpoint_line(int(p[0]), int(p[1]), int(p[0]), int(p[1]+p[2])) for p in rain_particles])
    elif weather_state == SNOW: glColor3f(1, 1, 1); ([draw_circle_3d(p[0], p[1], 0, p[2]) for p in snow_particles])
    draw_text(10, 30, f"Score: {score} | Biome: {['Forest', 'Desert', 'City'][biome_state]}"); draw_text(10, 60, f"Lives: {player_lives} | Weather: {['Clear', 'Rain', 'Snow'][weather_state]}")
    draw_text(10, 30, f"Score: {score} | Biome: {['Forest', 'Desert', 'City'][biome_state]}"); draw_text(10, 60, f"Lives: {player_lives} | Weather: {['Clear', 'Rain', 'Snow'][weather_state]}")
    if cheat_enabled: draw_text(10, 90, f"CHEAT MODE: ON ({int(cheat_timer/60)}s)", [0, 1, 0])
    if police_active: 
        if (time.time() * 10) % 2 > 1: 
             draw_text(WINDOW_WIDTH//2 - 80, 200, "POLICE PURSUIT!", [1, 0, 0])
        else: 
             draw_text(WINDOW_WIDTH//2 - 80, 200, "POLICE PURSUIT!", [0, 0, 1])
    if game_state == START:
        glColor3f(0, 0, 0) 
        glBegin(GL_TRIANGLES)
        glVertex2f(0,0); glVertex2f(600,0); glVertex2f(600,800)
        glVertex2f(0,0); glVertex2f(600,800); glVertex2f(0,800)
        glEnd()
        draw_text(150, 100, "TOP-DOWN RACER ULTIMATE", [1,1,0]); draw_text(50, 200, "CONTROLS:"); draw_text(70, 240, "[A/D]: Steer | [Q/E]: Switch View"); draw_text(70, 280, "[SPACE/ENTER]: Start | [R]: Reset"); draw_text(50, 350, "POWERUPS:"); draw_text(70, 390, "Blue: Shield | Red: Nitro"); draw_text(150, 600, "PRESS ENTER TO START");
    elif game_state == GAMEOVER: draw_text(240, 300, "GAME OVER!", [1,0,0]); draw_text(210, 340, "PRESS R TO RESTART")
    glPopMatrix(); glMatrixMode(GL_PROJECTION); glPopMatrix(); glMatrixMode(GL_MODELVIEW); glutSwapBuffers()

def reshape(width, height):
    width = max(1, width)
    height = max(1, height)
    glViewport(0, 0, width, height)

def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(WINDOW_WIDTH, WINDOW_HEIGHT)
    glutInitWindowPosition(100, 100)
    window = glutCreateWindow(b"Car Racing")
    if not window:
        raise RuntimeError("GLUT could not create the game window.")
    glutReshapeFunc(reshape)
    glutDisplayFunc(display)
    glutKeyboardFunc(keyboard)
    glutIdleFunc(idle)
    glutShowWindow()
    while True:
        glutMainLoopEvent()
        time.sleep(0.01)
if __name__ == "__main__": main()

