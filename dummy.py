import socket
from pickle import dumps
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
while True:
    try:
        client.connect(('127.0.0.1',65432))
        break
    except:
        pass
ping_packet = dumps("ping")
for i in range(5):
    client.sendall(ping_packet)
    client.recv(64)