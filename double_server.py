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

local_socket_path = "/tmp/local_socket"
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

def accept_connection(server):
    conn, _ = server.accept()
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
    sock.recv(64)
    sock.sendall(map_tiles.tobytes()) # More efficient than pickle for numpy array
    #region Generate Start
    x_disp = random.randint(0, map_width - 12)
    y_disp = random.randint(0, map_height - 8)
    while map_tiles[x_disp+6][y_disp+4][0] == 4:
        x_disp = random.randint(0, map_width - 12)
        y_disp = random.randint(0, map_height - 8) # Distance from the top of the map
    #endregion
    sock.recv(64)
    sock.sendall(pickle.dumps(x_disp, y_disp))
    return (x_disp, y_disp)

def exchange_starts(start1, start2, conn1, conn2):
    conn1.sendall(pickle.dumps(start2))
    conn2.sendall(pickle.dumps(start1))

def synchronize(conn1, conn2):
    conn1.recv(64)
    conn2.recv(64)

print("Waiting for connection...")
make_map()
local_conn=accept_connection(local_server)
start1 = send_startup_data(local_conn)
print("Waiting for another connection...")
remote_conn=accept_connection(remote_server)
start2 = send_startup_data(remote_conn)
print("Servers are running... Press Ctrl+C to stop.")

synchronize(local_conn, remote_conn)
exchange_starts(local_conn, remote_conn, start1, start2)

threading.Thread(target=handle_client, args=(local_conn,remote_conn)).start()
handle_client(remote_conn, local_conn)