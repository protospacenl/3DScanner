import os
import struct
import fcntl
import sys
import time

os.system("sudo pgrep -f Client.py")
os.system("sudo pkill -f Client.py")
os.system("sudo python Client.py")
print("Client reloaded succesfully")
sys.exit()
