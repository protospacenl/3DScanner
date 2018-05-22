#Error list:
#E404: Connection not established
#E99 : Parameters out of range
#E50 : No data available
#E2  : Function aborted (user)
import threading
import logging
import socket
import struct

import sys
import os
import re
from pathlib import Path

import datetime
import time

import PIL.Image
import PIL.ImageTk
from tkinter import messagebox as mb
from tkinter import *

import tkinter as tk
import numpy as np
import cv2
import urllib
import urllib.request
from http import server
import socketserver

client_path = r"C:\Users\Public\PS-3D-scanner\Client.py"
reload_path = r"C:\Users\Public\PS-3D-scanner\Reload.py"

multicast_group = ('224.0.0.10', 10000)

download_flag = 1
preview_flag = 0
connection_number = -1
current_thread = 0

ts = time.time()
st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d_%H-%M-%S')

# RE float checker
float_check = re.compile('\d+(\.\d+)?')

# Create the datagram socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Set a timeout so the socket does not block indefinitely when trying
# to receive data.
sock.settimeout(1)

connection_list = []

# Set the time-to-live for messages to 1 so they do not go past the
# local network segment.
ttl = struct.pack('b', 1)
sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)

window = tk.Tk()
window.title("3D Scanner")
window.geometry("575x300")


#preview_border = tk.Label(window)
#preview_border.place(x=225, y=25)
preview_label  = tk.LabelFrame(window, text="Camera preview", width=335, height=265, labelanchor=N).place(x=220, y=10)
preview_image  = tk.Label(window)
preview_image.place(x=225, y=25)

def counter():
    global download_flag
    x = 5
    
    download_message = "Downloading photos"
    
    while not download_flag:

        downloadpro_label.config(text = download_message)
        x = x + 1
        
        if x >= 5:
            download_message = download_message + '.'
            if x == 10:
                x = -5
                
        elif x <= 0:
            download_message = download_message[:-1]
            if x == 0:
                x = 5
            
        time.sleep(.25)
        
    downloadpro_label.config(text = "Download complete!")  
    return(1)

def process_data(command):
    global connection_number
    global connection_list
    photo_number = -1
    current_photo = 0
    data_flag = 0
    
    try:
        if command == "preview" or command == "stop_preview":
            preview_ip = (p_menu.get(), 10000)
            sock.sendto(str.encode(command), preview_ip) 
        else:
            sock.sendto(str.encode(command), multicast_group)
        
        while True:
            try:
                data, server = sock.recvfrom(32)
                data_flag = 1
                photo_number += 1
                
                if command[0:5] == "photo" and photo_number == connection_number:
                    current_photo += 1
                    photo_number = -1
                    sock.sendto(str.encode(str(current_photo)), multicast_group)
                    tk.Label(window, text="{0} photo(s) done".format(current_photo)).grid(column=1, row=0, sticky=W)     
                    
                if command == "connect":
                    connection_number += 1
                    connection_list.append(connection_number)
                    connection_list[connection_number] = str(server)[2:16]

            except socket.timeout:
                if not connection_list and command == "connect":
                    print("Connection failed, please repeat connect function")
                    return(404)
                if data_flag == 0:
                    if command != "preview" and command != "stop_preview":
                        print("No data retrieved, please repeat connect function")
                        return(50)
                print ('%s finished succesfully!' %command)
                if command[0:5] == "photo":
                    sent = sock.sendto(str.encode("light"), multicast_group)
                break
            else:
                print (data.decode() + str(server))
                
    finally:
        return (1)
    
def connection_check():
    if not connection_list:
        print("Connection not yet established, please run connect function")
        return (0)
    return (1)

def connect():
    sock.settimeout(1)
    global connection_number
    connection_number = -1
    process_data("connect")
    tk.Label(window, text="{0} camera(s) connected".format(connection_number + 1)).grid(column=1, row=7, sticky=W)
    
    if connection_check() == 1:
        return (1)
    return (404)

def photo():
    sock.settimeout(6)
    global connection_list
    
    if connection_check() == 1:
        par1 = amount.get()
        par2 = delay.get()
        if (par1.isdigit() and (par2.isdigit() or float_check.match(par2))):
            if (int(par1) <= 50 and float(par2) <= 5):
                message = ("photo" + " " + par1 + " " + par2)
                # Send data to the multicast group
                print ('sending "%s"' % message)

                # Look for responses from all recipients
                process_data(message)
                return (1)
            print("Parameters out of range, max 50 photos at a 5 second delay.")
            return(99)
        print("Wrong input, please enter numbers only.")
        return(99)
    return (404)

def download():
    global ts
    global st
    global connection_number
    global connection_list
    global download_flag
    
    download_flag = 0
    
    counter_thread = threading.Thread(target=counter)
    counter_thread.start()
    
    if connection_check() == 1:
        
        download_message = "Downloading photos"
        print(download_message)
        
        na = folder.get()
        if not os.path.exists("c:\Temp\_pifotos\%s" %na):
            os.system ('mkdir c:\Temp\_pifotos\%s' %na)
        else:
            result = mb.askquestion("Folder already exists", "Are you sure you wish to overwrite an existing folder?", icon='warning')
            if result == "no":
                print("Download aborted")
                download_flag = 1
                return(2)
        for x in range (0, connection_number+1):
            os.system('pscp.exe -pw protoscan1 pi@{0}:/home/pi/Desktop/photos/*.jpg c:\Temp\_pifotos\{1}\\'.format (connection_list[x], na))
        
        print("download complete!")
        download_flag = 1
        return (1)
    return (404)
   
def sync():
    global st
    global connection_number
    global connection_list
    
    if connection_check() == 1:
    
        for x in range (0, connection_number+1):
            os.system(r'pscp.exe -pw protoscan1 {0} pi@{1}:/home/pi'.format (client_path, connection_list[x]))
            os.system(r'pscp.exe -pw protoscan1 {0} pi@{1}:/home/pi'.format (reload_path, connection_list[x]))
        print("sync complete!")
        reload()
        tk.Label(window, text="Last synced : {0}".format(st)).grid(column=1, row=5)
        
        return (1)
    return (404)
    
def reload():
    sock.settimeout(1)
    if connection_check() == 1:
        process_data("reload")
        return (1)
    return (404)
        
def kill():
    sock.settimeout(1)
    if connection_check() == 1:
        result = mb.askquestion("Kill program", "Are you sure you wish to kill the current script?", icon='warning')
        if result == "no":
            print("Kill aborted")
            return(2)
        else:
            process_data("kill")
            return (1)
    return (404)

def preview():
    global preview_flag
    if not connection_check():
        return 0
    if p_menu.get() == preview_select[0]:
        print("No camera selected, please select a camera")
        return 404
    
    process_data("preview")
    preview_button.config(text="Stop", bg="red", command = lambda: button(7))
    print("{0} preview, press stop to cancel".format (p_menu.get()))
    urllib.request.urlcleanup()
    stream=urllib.request.urlopen("http://{0}:8000/stream.mjpg".format (p_menu.get()))
    streamBytes= bytes()
    while True:
        streamBytes+=stream.read(1024)
        a = streamBytes.find(b'\xff\xd8')
        b = streamBytes.find(b'\xff\xd9')
        if a!=-1 and b!=-1:
            jpg = streamBytes[a:b+2]
            streamBytes= streamBytes[b+2:]
            i = cv2.imdecode(np.fromstring(jpg, dtype=np.uint8),cv2.IMREAD_COLOR)            
            tki = PIL.ImageTk.PhotoImage(PIL.Image.fromarray(cv2.cvtColor(i, cv2.COLOR_BGR2RGB)))
            preview_image.configure(image=tki)                
            preview_image._backbuffer_ = tki  #avoid flicker caused by premature gc
            #cv2.imshow('i',i)
        if cv2.waitKey(1) ==27:
            exit(0)
        if preview_flag == 1:
            preview_flag = 0
            preview_image.configure(image='')
            preview_button.config(text="Preview", bg="white", command = lambda: button(6))
            return
        
commands = {0 : photo,
            1 : download,
            2 : sync,
            3 : reload,
            4 : connect,
            5 : kill,
            6 : preview,}

preview_select = ["no camera",
                  "192.168.178.20",
                  "192.168.178.21",
                  "192.168.178.22",
                  "192.168.178.27",]

def button(command_number):
    global current_thread
    global preview_flag
    
    if command_number == 7:
        preview_flag = 1
        time.sleep(0.1)
        threading.Thread(target=process_data("stop_preview"))
    elif current_thread.isAlive():
        print("Process still running, please wait")
    else:
        current_thread = threading.Thread(target=commands[command_number])
        current_thread.start()
        
def createEntry(name, position, size, variable):
    new_label = tk.Label(window, text=name)
    new_label.grid(column=0, row=position)
    new_entry = tk.Entry(window, width=size, text=variable)
    new_entry.grid(column=1, row=position, sticky=W)
    return new_entry

def createButton(button_text, position, colour, function_number):
    vars()[str(function_number)] = tk.Button(width=8, text=button_text, command = lambda: button(function_number), bg = colour)
    vars()[str(function_number)].grid(column=0, row=position, sticky=W)
    return vars()[str(function_number)]
    
def createLabel(name, coordx, coordy):
    new_label = tk.Label(window, text=name)
    new_label.place(x=coordx, y=coordy)
    return new_label

amount  = tk.StringVar()
delay   = tk.StringVar()
folder  = tk.StringVar()

p_menu  = tk.StringVar()
p_menu.set(preview_select[0])

createEntry("Amount", 1, 6,  amount)
createEntry("Delay",  2, 6,  delay )
createEntry("Folder", 4, 10, folder)

createButton("Photos",   0, "white", 0)
createButton("Download", 3, "white", 1)
createButton("Sync",     5, "white", 2)
createButton("Reload",   6, "white", 3)
createButton("Connect",  7, "white", 4)
createButton("Kill",     8, "white", 5)
preview_button  = createButton("Preview",  9, "white", 6)

createLabel("max. 50", 110, 25)
createLabel("max. 5s", 110, 45)
downloadpro_label = createLabel("", 67, 70)

preview_dropdwn = tk.OptionMenu(window, p_menu, *preview_select)
preview_dropdwn.place(x=67, y=216)

current_thread = threading.Thread(target=commands[4])
current_thread.start()

window.mainloop()