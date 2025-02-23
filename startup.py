import threading
import subprocess

def run_file(file):
    subprocess.run(["python3", file])

option = int(input("Number of players (1 or 2): "))
'''while option!=1 and option!=2:
    print("Invalid choice! Enter 1 or 2")
    option = int(input("Number of players (1 or 2): "))
if option == 1:
    threading.Thread(target = run_file, args = ("single_server.py",)).start()
elif option == 2:'''
threading.Thread(target = run_file, args = ("double_server.py",)).start()

run_file("client_side.py")