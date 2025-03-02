import pygame
import numpy as np
import queue
import socket
import pickle
import threading
# CHANGE CURRENT PLAYER BASED ON CONNECTION!!
pygame.init()
req_queue = queue.Queue()

def recieve_large(size):
    data = bytearray()
    while len(data) < size:
        data.extend(client.recv(size-len(data)))
    return data

option = int(input("Local (0) or remote (1): "))
error = True # For connecting to the server
if option == 0:
    client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    while error:
        error = False
        try:
            client.connect("/tmp/local_socket")
        except:
            print("Server is not running, trying again in 1 second")
            error = True
            pygame.time.wait(1000)
else:
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    while error:
        error = False
        try:
            client.connect((input("IP address: "),65432))
        except:
            print("Check port forwarding! Trying again in 1 second")
            error = True
            pygame.time.wait(1000)

client.sendall(pickle.dumps("Client connected"))

#region Initialize
colors = np.array([[128,128,128], [128,255,0], [255,255,255], [255,255,0], [0,0,255]])
colors_greyed = np.array([[128,128,128], [128,192,64], [192,192,192], [192,192,64], [64,64,192]])
menu_color = (64,64,96)
types_string = ["Village","Water Wheel","Farm","Lumber mill"]
build_cost = np.array([
[0,5,0,0,0],
[0,5,0,0,0],
[0,8,0,0,0],
[0,5,0,0,0],
], dtype=np.int16)
resource_types = np.array(["Water", "Food", "Wood", "Stone", "Copper", "Oil"], dtype=str)
collectible_resource_types = np.array(["Food", "Wood", "Stone", "Copper", "Oil"], dtype=str)
resource_colors = np.array([(128,128,255),(255,255,0),(192,192,128),(128,128,128),(255,128,0),(32,0,64)], dtype = np.int16)
num_resource_types = len(resource_types)
num_collectible_resource_types = len(collectible_resource_types)
resources = np.zeros((num_collectible_resource_types),dtype=np.int16)
resources[1] = 15
#endregion

#region Game variables
building_sight_range = 2
unit_sight_range = 3
nobuild_range = 4
#endregion

#region Recieve startup data
ping_packet = pickle.dumps("ping")
passturn_packet = pickle.dumps('pass')
map_width, map_height = pickle.loads(client.recv(64))
client.send(ping_packet)
map_info = np.frombuffer(recieve_large(map_width*map_height*(1+num_resource_types)), dtype=np.int8).reshape(map_width, map_height, 1+num_resource_types)
client.send(ping_packet)
x_disp, y_disp = pickle.loads(client.recv(64))
client.send(ping_packet)
opponent_start = pickle.loads(client.recv(64))
print(opponent_start)
#endregion

#region initialize display info
default_font = pygame.font.Font(None, 72)
display_info = pygame.display.Info()
screen_width, screen_height = display_info.current_w, display_info.current_h
screen = pygame.display.set_mode((screen_width, screen_height))
#pygame.display.toggle_fullscreen()
pygame.event.set_blocked(pygame.MOUSEMOTION)

tile_width = int(min(screen_width/12, screen_height/8))
tile_disp_x = int(screen_width/tile_width)
tile_disp_y = int(screen_height/tile_width)

print(f"Transferred: ({map_width}, {map_height})")
draw_width = min(screen_width/map_width, screen_height/map_height)
#endregion

unit_is_selected = False
unit_selected = 0

building_images = [
pygame.image.load("textures/buildings/PlainsVillage1.png"),
pygame.image.load("textures/buildings/water_wheel.png"),
pygame.image.load("textures/buildings/farm.png"),
]

resource_textures = [
pygame.transform.scale(pygame.image.load("textures/resources/food.png"), (150,150)),
pygame.transform.scale(pygame.image.load("textures/resources/wood.png"), (150,150)),
pygame.transform.scale(pygame.image.load("textures/resources/stone.png"), (150,150)),
pygame.transform.scale(pygame.image.load("textures/resources/copper.png"), (150,150)),
pygame.transform.scale(pygame.image.load("textures/resources/oil.png"), (150,150)),
pygame.transform.scale(pygame.image.load("textures/resources/water.png"), (150,150)),
]

class Tile(pygame.sprite.Sprite):
    def __init__(self,array):
        super().__init__()
        self.type = array[0]
        self.image = pygame.Surface((tile_width, tile_width))
        self.image.fill(colors[self.type])
        self.image_greyed = pygame.Surface((tile_width, tile_width))
        self.image_greyed.fill(colors_greyed[self.type])
        self.resources = array[1:]
        for i in range(len(self.resources)):
            if self.resources[i]:
                pygame.draw.rect(self.image, resource_colors[i], pygame.Rect(20*i, 0, 20, 20))
                pygame.draw.rect(self.image_greyed, resource_colors[i], pygame.Rect(20*i, 0, 20, 20))
        self.image_small = pygame.transform.scale(self.image,(draw_width, draw_width))
        self.image_greyed_small = pygame.transform.scale(self.image_greyed,(draw_width, draw_width))
        self.rect = self.image.get_rect()
    
    def draw(self,x,y,scaled):
        if scaled:
            if tiles_in_sight[x][y]:
                screen.blit(self.image_small, (x*draw_width+450, y*draw_width))
            else:
                screen.blit(self.image_greyed_small, (x*draw_width+450, y*draw_width))
        else:
            if tiles_in_sight[x][y]:
                screen.blit(self.image, ((x-x_disp)*tile_width, (y-y_disp)*tile_width))
            else:
                screen.blit(self.image_greyed, ((x-x_disp)*tile_width, (y-y_disp)*tile_width))

class Thing(pygame.sprite.Sprite):
    def __init__(self,type,x_loc,y_loc,rect):
        super().__init__()
        self.x, self.y = x_loc, y_loc
        self.type = type
        self.rect = rect

    def is_visible(self,x_loc,y_loc):
        return x_loc <= self.x < x_loc+tile_disp_x and y_loc <= self.y < y_loc+tile_disp_y

    def get_collisions(self,x_loc,y_loc):
        return self.x == int(x_loc/tile_width+x_disp) and self.y == int(y_loc/tile_width+y_disp)
'''
Units: 1 = builder, 2 = soldier
'''
class Unit(Thing):
    def __init__(self,type,x_loc,y_loc,team):
        self.image = pygame.Surface((tile_width/2, tile_width/2))
        self.team = team
        if team == 1:
            self.image.fill((0,255,255))
        elif team == 2:
            self.image.fill((255,0,0))
        rect = self.image.get_rect(topleft=(tile_width/4+(x_loc-x_disp)*tile_width,tile_width/4+(y_loc-y_disp)*tile_width))
        super().__init__(type,x_loc,y_loc,rect)
        if type == 1:
            self.moves_per_turn = 4
            self.moves = 4
            self.actions = 3

    def update_rect(self):
        self.rect = self.image.get_rect(topleft=(tile_width/4+(self.x-x_disp)*tile_width,tile_width/4+(self.y-y_disp)*tile_width))

    def move(self, move_x, move_y, forcemove = False):
        if self.moves > 0: # if has moves left
            if 0 <= self.x+move_x < map_width and 0 <= self.y+move_y < map_height: # if not moving off screen
                if  map_info[self.x+move_x][self.y+move_y][0] != 4: # if not moving onto ocean
                    self.moves -= 1
                    self.x += move_x
                    self.y += move_y
                    global redraw_map
                    redraw_map = True

    def build(self):
        if self.actions > 0:
            building_option = choose_buildings()
            # Check if the building is valid
            if can_build(building_option, self.x, self.y):
                self.actions -= 1
                for i in range(num_resource_types-1):
                    resources[i] -= build_cost[building_option-1][i]
                process_request((0,self.x,self.y,building_option,1))
                req_queue.put((0,self.x,self.y,building_option,2))
                global redraw_map
                redraw_map = True

    def update_visible(self):
        for x in range(self.x-unit_sight_range, self.x+unit_sight_range+1):
            for y in range(self.y-unit_sight_range, self.y+unit_sight_range+1):
                if 0 <= x < map_width and 0 <= y < map_height:
                    tiles_in_sight[x][y] = True

class Building(Thing):
    def __init__(self,type,x_loc,y_loc,team):
        self.image = pygame.transform.scale(building_images[type-1], (tile_width, tile_width))
        rect = self.image.get_rect(topleft=((x_loc-x_disp)*tile_width,(y_loc-y_disp)*tile_width))
        super().__init__(type,x_loc,y_loc,rect)
        self.team = team
    def update_rect(self):
        self.rect = self.image.get_rect(topleft=((self.x-x_disp)*tile_width,(self.y-y_disp)*tile_width))

    def update_visible(self):
        for x in range(self.x-building_sight_range, self.x+building_sight_range):
            for y in range(self.y-building_sight_range, self.y+building_sight_range):
                if 0 <= x < map_width and 0 <= y < map_height:
                    tiles_in_sight[x][y] = True
    
    def generate_resources(self):
        if 2 < self.type < 8:
            resources[self.type-3] += 1

#region Load map and units
map_tiles = []
for x in range(map_width):
    map_tiles.append([])
    for y in range(map_height):
        map_tiles[x].append(Tile(map_info[x][y]))

discovered_tiles = np.empty((map_width, map_height), dtype = bool)
discovered_tiles.fill(False)
tiles_in_sight = np.empty((map_width, map_height), dtype = bool)

my_units_list = [Unit(1, x_disp+6, y_disp+4,1)]
opponent_units_list = [Unit(1, opponent_start[0]+6, opponent_start[1]+4, 2)]

my_buildings_list = []
opponent_buildings_list = []
#endregion
'''Processing request(
new building (0) new unit (1) move unit (2) pass turn (3)
x,
y,
index/type
team)

Resources
["Water", "Food", "Wood", "Stone", "Copper", "Oil"] '''
server_ready = True
def can_build(option, x, y):
    for i in range(num_resource_types-1):
        if resources[i] < build_cost[option-1][i]:
            return False
    for building in my_buildings_list:
        if building.x == x and building.y == y:
            return False
    for building in opponent_buildings_list:
        if abs(building.x-x) <= nobuild_range and abs(building.y-y) <= nobuild_range:
            return False
        
    if option == 1:
        return map_info[x][y][0] != 4
    elif option == 2:
        return map_info[x][y][0] != 4 and map_info[x][y][1]
    elif option == 3:
        return map_info[x][y][0] != 4 and map_info[x][y][2]

def send_request():
    client.sendall(pickle.dumps(req_queue.get()))
    global server_ready
    server_ready = False

def process_requests():
    while True:
        data = client.recv(59)
        if data == ping_packet:
            if req_queue.empty():
                global server_ready
                server_ready = True
            else:
                send_request()
        elif data == passturn_packet:
            process_request((3,))
        else:
            process_request(pickle.loads(data))

def process_request(array):
    if array[0] == 0:
        if array[4] == 1:
            my_buildings_list.append(Building(array[3],array[1],array[2],array[4]))
        else:
            opponent_buildings_list.append(Building(array[3],array[1],array[2],array[4]))
    elif array[0] == 1:
        if array[4] == 0:
            my_units_list.append(Unit(array[3],array[1],array[2],array[4]))
        else:
            opponent_units_list
    elif array[0] == 2:
        if array[4] == 1:
            my_units_list[array[3]].move(array[1],array[2])
        elif array[4] == 2:
            opponent_units_list[array[3]].move(array[1],array[2])
    elif array[0] == 3:
        for unit in my_units_list:
            unit.moves = unit.moves_per_turn
        for unit in opponent_units_list:
            unit.moves = unit.moves_per_turn
        for building in my_buildings_list:
            building.generate_resources()
        for building in opponent_buildings_list:
            building.generate_resources()

def draw(x_disp,y_disp):
    for x in range(x_disp, x_disp+tile_disp_x):
        for y in range(y_disp, y_disp+tile_disp_y):
            if 0 <= x < map_width and 0 < y < map_height and discovered_tiles[x][y]:
                map_tiles[x][y].draw(x, y, False)
            else:
                pygame.draw.rect(screen,(64,64,64),pygame.Rect((x-x_disp)*tile_width,(y-y_disp)*tile_width,tile_width,tile_width))

def draw_minimap():
    screen.fill((128,128,128))
    for x in range(map_width):
        for y in range(map_height):
            if discovered_tiles[x][y]:
                map_tiles[x][y].draw(x,y,True)
            else:
                pygame.draw.rect(screen, (64,64,64), pygame.Rect(x*draw_width+450, y*draw_width, draw_width, draw_width))

hud_surface = pygame.Surface((screen_width, 200))
def update_hud():
    hud_surface.fill(menu_color)
    for i in range(num_collectible_resource_types):
        hud_surface.blit(resource_textures[i], (i*300+25, 25, 150, 150))
        hud_surface.blit(default_font.render(str(resources[i]), True, (255,255,255)), (i*300 + 214,64))

def make_visible(x_pos,y_pos,radius):
    for x in range(x_pos-radius, x_pos+radius+1):
        for y in range(y_pos-radius,y_pos+radius+1):
            if 0 <= x < map_width and 0 <= y < map_height:
                discovered_tiles[x][y] = True

def draw_units():
    for unit in my_units_list:
        if unit.is_visible(x_disp, y_disp):
            unit.update_rect()
            screen.blit(unit.image, unit.rect)
    for unit in opponent_units_list:
        if tiles_in_sight[unit.x][unit.y] and unit.is_visible(x_disp, y_disp):
                    unit.update_rect()
                    screen.blit(unit.image, unit.rect)

def draw_buildings():
    for building in my_buildings_list:
        if building.is_visible(x_disp, y_disp):
            building.update_rect()
            screen.blit(building.image, building.rect)
    for building in opponent_buildings_list:
        if building.is_visible(x_disp, y_disp) and discovered_tiles[building.x][building.y]:
            building.update_rect()
            screen.blit(building.image, building.rect)

def choose_buildings():
    pygame.draw.rect(screen,(64,64,96),pygame.Rect(screen_width*3/4,0,screen_width/4,screen_height))
    pygame.draw.line(screen,(0,0,0),(screen_width*3/4,100),(screen_width,100))
    screen.blit(default_font.render("Buildings",True,(255,255,255)),(screen_width*3/4+30, 30))
    for i in range(len(types_string)):
        screen.blit(default_font.render(types_string[i],True,(255,255,255)),(screen_width*3/4+30, 100*i+114))
        pygame.draw.line(screen,(0,0,0),(screen_width*3/4, (i+1)*100),(screen_width,(i+1)*100))
    pygame.display.flip()
    while True:
        event = pygame.event.wait()
        if event.type == pygame.MOUSEBUTTONDOWN and event.pos[0]>3/4*screen_width:
            option = int((event.pos[1])/100)
            if 0 < option < 1+len(types_string):
                return option
        elif event.type == pygame.QUIT:
            break

def update_sight():
    tiles_in_sight.fill(False)
    for unit in my_units_list:
        unit.update_visible()
    for building in my_buildings_list:
        building.update_visible()

def draw_everything():
    screen.fill((0,0,0))
    draw(x_disp, y_disp)
    draw_units()
    draw_buildings()
    screen.blit(hud_surface,(0,0))

# Draw the whole map and leave it on the screen for a few seconds
make_visible(my_units_list[0].x, my_units_list[0].y,3)
update_hud()
draw_everything()
pygame.display.flip()

threading.Thread(target=process_requests, daemon=True).start()

# Game Loop:
running = True
while running:
    redraw_map = False
    event = pygame.event.wait()
    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_UP:
            y_disp -= 1
            redraw_map = True
        elif event.key == pygame.K_DOWN:
            y_disp += 1
            redraw_map = True
        elif event.key == pygame.K_RIGHT:
            x_disp += 1
            redraw_map = True
        elif event.key == pygame.K_LEFT:
            x_disp -= 1
            redraw_map = True
        elif event.key == pygame.K_MINUS: # Enter minimap mode
            draw_minimap()
            pygame.display.flip()
        elif event.key == pygame.K_EQUALS: # Exit minimap mode
            redraw_map = True
        elif event.key == pygame.K_RETURN: # Pass turn
            req_queue.put(('pass'))

        elif unit_is_selected:
            if event.key == pygame.K_w:
                process_request((2,0,-1,unit_selected,1))
                req_queue.put((2,0,-1,unit_selected,2))
            elif event.key == pygame.K_s:
                process_request((2,0,1,unit_selected,1))
                req_queue.put((2,0,1,unit_selected,2))
            elif event.key == pygame.K_a:
                process_request((2,-1,0,unit_selected,1))
                req_queue.put((2,-1,0,unit_selected,2))
            elif event.key == pygame.K_d:
                process_request((2,1,0,unit_selected,1))
                req_queue.put((2,1,0,unit_selected,2))
            elif event.key == pygame.K_b:
                my_units_list[unit_selected].build()
            if server_ready and not req_queue.empty():
                send_request()
            if redraw_map:
                make_visible(my_units_list[unit_selected].x,my_units_list[unit_selected].y,3)
    elif event.type == pygame.QUIT:
        running = False
        turn_running = False
    elif event.type == pygame.MOUSEBUTTONDOWN:
        # Find collisions with units and icons
        unit_is_selected = False
        for i in range(len(my_units_list)):
            if my_units_list[i].get_collisions(event.pos[0],event.pos[1]):
                unit_is_selected = True
                unit_selected = i

    update_sight()
    if redraw_map:
        update_hud()
        draw_everything()
        pygame.display.flip()

pygame.quit()