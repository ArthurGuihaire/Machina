import socket
import threading

socket_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
socket_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
socket_server.bind(("0.0.0.0", 65432))
socket_server.listen(1)

def accept_conn(sock):
    conn, _ = sock.accept()
    return conn

socket_client.connect(("127.0.0.1", 65432))
conn, _ = socket_server.accept()
socket_client.send("a".encode())
socket_client.send("b".encode())
print(conn.recv(256).decode())