import threading, subprocess

def run_file(file):
    subprocess.run(["python3", file])

threading.Thread(target = run_file, args = ("double_server.py",)).start()

option = int(input("Remote (1) or Local (2)"))
if option == 2:
    threading.Thread(target = run_file, args = ("client_side.py",)).start()

run_file("client_side.py")