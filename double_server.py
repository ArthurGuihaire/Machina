import socket
import threading
import os
import pickle
import random
import numpy
import math

# Game variables to be socket-transfered
map_width, map_height = 50,50
num_biomes = 20
# biome types: 1 = plains, 2 = tundra, 3 = desert, 4 = ocean
ocean_scale_factor = 0.7 # Divides size by 0.7 so bigger
resource_frequency = [[0.1,0.1,0.1,0.1,0.1,0.1], [0.1,0.08,0.1,0.1,0.1,0.2], [0.08, 0.02, 0.02, 0.1, 0.15, 0.1], [0,0.15,0,0,0,0.1]]
resource_frequency = numpy.array(resource_frequency, dtype = float)
resource_types = ["Water", "Food", "Wood", "Stone", "Copper", "Oil"]

num_resource_types = len(resource_types)

from requests import get as find_ip
print(find_ip('https://api64.ipify.org?format=text').text)

# UNIX socket path
local_socket_path = "/tmp/local_socket"
# Remove existing UNIX socket file if it exists
if os.path.exists(local_socket_path):
    os.remove(local_socket_path)
# Create two servers: one local, one remote
local_server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
remote_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
remote_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

local_server.bind(local_socket_path)  # local
remote_server.bind(("0.0.0.0", 65432))  # remote
local_server.listen()
remote_server.listen()

'''def run_program(program):
    with open(program) as file:
        exec(file.read())
threading.Thread(target=run_program, args=('client_side.py',)).start()'''

def send_large_data(sock, data): #ChatGPT code
    total_sent = 0
    while total_sent < len(data):
        sent = sock.send(data[total_sent:])
        total_sent += sent

def handle_client(conn, conn2):
    try:
        while True:
            data = conn.recv(1024)
            if not data:
                break
            conn2.sendall(data)
    except (ConnectionResetError, BrokenPipeError):
        print("Connection lost. Closing...")
    finally:
        conn.close()

def accept_connection(server, multi):
    conn, _ = server.accept()
    if multi:
        threading.Thread(target=send_startup_data, args=(conn,)).start()
    else:
        send_startup_data(conn)
    return conn

def make_map():
    biomes = []
    for i in range(num_biomes):
        biomes.append((random.randint(0,map_width-1), random.randint(0,map_height-1), int((random.randint(2,8))/2)))
    global map_tiles
    map_tiles = numpy.zeros((map_width,map_height,1+num_resource_types), dtype=numpy.int8)
    for x in range(map_width):
        for y in range(map_height):
            min_distance = 255
            for biome in biomes:
                distance = math.sqrt((biome[0]-x)**2 + (biome[1]-y)**2)
                if biome[2] == 4: # Ocean
                    distance *= ocean_scale_factor
                if distance < min_distance:
                    biome_type = biome[2]
                    min_distance = distance
            map_tiles[x][y][0] = biome_type
            for i in range(num_resource_types):
                if random.random() < resource_frequency[biome_type-1][i]:
                    map_tiles[x][y][i+1] = 1

def send_startup_data(sock):
    print(pickle.loads(sock.recv(1024)))
    sock.sendall(pickle.dumps((map_width, map_height)))
    sock.recv(1)
    sock.sendall(map_tiles.tobytes()) # More efficient than pickle for numpy array

print("Waiting for connection...")
threading.Thread(target=make_map).start()
local_conn=accept_connection(local_server, True)
remote_conn=accept_connection(remote_server, False)
print("Servers are running... Press Ctrl+C to stop.")
threading.Thread(target=handle_client, args=(local_conn,remote_conn)).start()
handle_client(remote_conn, local_conn)