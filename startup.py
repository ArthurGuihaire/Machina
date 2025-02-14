import threading
import subprocess

def run_file(file):
    subprocess.run(["python3", file])

option = 0
while option!=1 and option!=2:
    option = int(input("Type 1 to start a game or 2 to join a game: "))

if option == 1:
    threading.Thread(target = run_file, args = ["server.py"]).start()

threading.Thread(target = run_file, args = ["client_side.py"]).start()