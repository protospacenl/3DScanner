#!/usr/bin/env python3

#Error list:
#E404: Connection not established
#E99 : Parameters out of range
#E50 : No data available
#E2  : Function aborted (user)

from multiprocessing.dummy import Pool
from subprocess import check_output, call
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
from tkinter import ttk
from tkinter import filedialog
import tkinter as tk

import numpy as np
import cv2
import urllib
import urllib.request
from http import server
import socketserver
import winsound

import serial 
import time 
import pyfirmata

client_path = r"C:\Users\Public\GitHub\3DScanner\firmware\client\Client.py"
multicast_group = ('224.0.0.10', 10000)
master_ip = ('192.168.178.20', 10000)

download_flag = 1
preview_flag = 0
current_thread = 0

selected_camera = 'no camera selected'
selected_camera_number = 0

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

sock.settimeout(1)

connection_list = []
camera_list = []

ttl = struct.pack('b', 1)
sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)

window = tk.Tk()
window.title("3D Scanner")
window.geometry("895x540")

preview_label  = tk.LabelFrame(window, text="Camera preview", width=655, height=505, labelanchor=N).place(x=220, y=10)
default_path_label = tk.Label(window, text="Select download path").grid(column=1, row=4, sticky=W)
preview_image  = tk.Label(window)
preview_image.place(x=225, y=25)

download_path = None

current_thread = None
button_thread = None
_pollButton = True

def read_button_loop():
    global _pollButton

    btnInterface = pyfirmata.Arduino("COM4")
    btnButton = btnInterface.get_pin('d:2:i')
    iterator = pyfirmata.util.Iterator(btnInterface)
    iterator.start()

    while _pollButton:
        print("poll: {0}".format(_pollButton))
        if str(btnButton.read()) == 'True':
            print(btnButton.read())
            print(photo())
            btnInterface.pass_time(1)
        else:
            print(btnButton.read())
            btnInterface.pass_time(1)
        time.sleep(0.5)

def download_photos(ip, remote_path, local_path):
    try:
        print('downloading: pi@{0}:{1} -> {2}'.format(ip, remote_path, local_path))
        sys.stdout.flush()
        
        output = call(['pscp.exe', '-r', '-pw', 'protoscan1', 
                                   'pi@{0}:{1}'.format(ip, remote_path),
                                   local_path]), ip
        return output
    except Exception as e:
        print(e)
        return ip, e


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
    return 1

def process_data(command):
    photo_number = 0
    current_photo = 0
    data_flag = 0
    
    try:
        if command == "preview" or command == "stop_preview":
            preview_ip = (connection_list[selected_camera_number], 10000)
            sock.sendto(str.encode(command), preview_ip) 
        else:
            sock.sendto(str.encode(command), multicast_group)
        
        while True:
            try:
                data, server = sock.recvfrom(32)
                data_flag = 1
                photo_number += 1
                

                if command[0:5] == "photo" and photo_number == len(connection_list):
                    current_photo += 1
                    photo_number = 0
                    sock.sendto(str.encode(str(current_photo)), multicast_group)
                    tk.Label(window, text="{0} photo(s) done".format(current_photo)).grid(column=1, row=0, sticky=W)

                    
                if command == "connect":  
                    ip = str(server)[2:15]
                    cam_nr = 'Camera ' + ip[11:13]
                    if not ip in connection_list:
                        connection_list.append(ip)
                        camera_list.append(cam_nr)
                        
            except socket.timeout:
                if command == "connect":
                    if not connection_list:
                        print("Connection failed, please repeat connect function")
                        return 404
                    connection_list.sort()
                    camera_list.sort()
                    preview_dropdwn.set_menu("no camera selected", *camera_list)
                    
                if data_flag == 0:
                    if command != "preview" and command != "stop_preview":
                        print("No data retrieved, please repeat connect function")
                        return 50
                print ('%s finished succesfully!' %command)
                if command[0:5] == "photo":
                    #sock.sendto(str.encode("stop_photo"), multicast_group)
                    sock.sendto(str.encode("light"), master_ip)
                    
                    winsound.Beep(2500, 500)
                    winsound.Beep(2500, 500)
                break
            else:
                print (data.decode() + str(server))
                
    finally:
        return 1

def connection_check():
    if not connection_list:
        print("Connection not yet established, please run connect function")
        return 0
    return 1

def connect():
    global connection_list
    global camera_list
    
    sock.settimeout(1)
    del connection_list[:]
    del camera_list[:]
    process_data("connect")

    tk.Label(window, text="{0} camera(s) connected".format(len(connection_list))).grid(column=1, row=7, sticky=W)
    
    if connection_check() == 1:
        return 1
    return 404

def photo():
    sock.settimeout(6)
    float_check = re.compile('\d+(\.\d+)?')
    
    if connection_check() == 1:
        par1 = amount.get()
        par2 = delay.get()
        if (par1.isdigit() and (par2.isdigit() or float_check.match(par2))):
            if (int(par1) <= 50 and float(par2) <= 5):
                winsound.Beep(2500, 600)
                message = ("photo" + " " + par1 + " " + par2)
                print ('sending "%s"' % message)
                process_data(message)
                return 1
            print("Parameters out of range, max 50 photos at a 5 second delay.")
            return 99
        print("Wrong input, please enter numbers only.")
        return 99
    return 404

def save_to_directory():
    global download_path 

    download_path = Path(filedialog.askdirectory()) #open file dialog
    print(download_path)

    if download_path == "":
        tk.Label(window, text="Select download path").grid(column=1, row=4, sticky=W)
    else: 
        tk.Label(window, text="File path: {0}".format(download_path)).grid(column=1, row=4, sticky=W) 

def download():
    global download_flag, download_path
    download_flag = 0
    counter_thread = threading.Thread(target=counter)
    counter_thread.start()
    
    if connection_check() == 1: 
        download_message = "Downloading photos"
        print(download_message)

        if not download_path or not download_path.exists():  
            print("Path {0} does not exist".format(download_path))
            download_flag = 1
            return 2
        elif len(sorted(download_path.glob("**/*.jpg"))) > 0:
            result = mb.askquestion("Folder already exists", "Are you sure you wish to overwrite an existing folder?", icon='warning')
            if result == "no": 
                print("Download aborted")
                download_flag = 1
                return 2
                
        download_pool = Pool(len(connection_list))
        download_map = []
        for x in range (0, len(connection_list)):
            args = (connection_list[x], '/opt/3dscanner/photos/*', "{0}".format(download_path.resolve()))
            download_map.append(args)
        download_result = download_pool.starmap(download_photos, download_map)
        
        for status, ip in download_result:
            if not status == 0:
                print("Download failed for {0}: {1}".format(ip, status))
        print("download done.")
        download_flag = 1
        return 1
    return 404

def sync():
    if connection_check() == 1:
    
        for x in range (0, len(connection_list)):
            os.system(r'pscp.exe -pw protoscan1 {0} pi@{1}:/home/pi/3DScanner/firmware/client'.format (client_path, connection_list[x]))
        print("sync complete!")
        reload()
        
        return 1
    return 404
    
def reload():
    sock.settimeout(1)
    if connection_check() == 1:
        process_data("reload")
        return 1
    return 404
        
def kill():
    sock.settimeout(1)
    if connection_check() == 1:
        result = mb.askquestion("Kill program", "Are you sure you wish to kill the current script?", icon='warning')
        if result == "no":
            print("Kill aborted")
            return 2
        else:
            process_data("kill")
            return 1
    return 404

def preview():
    global preview_flag
    global selected_camera
    global selected_camera_number
    if not connection_check():
        return 0
    
    selected_camera = p_menu.get()
    selected_camera_number = int(selected_camera[7:9]) - 1
    
    if selected_camera == "no camera selected":
        print("No camera selected, please select a camera")
        return 0
    
    process_data("preview")
    preview_button.config(text="Stop", bg="red", command = lambda: button(7))
    print("{0} preview, press stop to cancel".format (selected_camera))
    urllib.request.urlcleanup()
    stream=urllib.request.urlopen("http://{0}:8000/stream.mjpg".format (connection_list[selected_camera_number]))
    stream_bytes= bytes()
    while True:
        stream_bytes+=stream.read(1024)
        a = stream_bytes.find(b'\xff\xd8')
        b = stream_bytes.find(b'\xff\xd9')
        if a!=-1 and b!=-1:
            jpg = stream_bytes[a:b+2]
            stream_bytes= stream_bytes[b+2:]
            i = cv2.imdecode(np.fromstring(jpg, dtype=np.uint8),cv2.IMREAD_COLOR)            
            tki = PIL.ImageTk.PhotoImage(PIL.Image.fromarray(cv2.cvtColor(i, cv2.COLOR_BGR2RGB)))
            preview_image.configure(image=tki)                
            preview_image._backbuffer_ = tki
        if cv2.waitKey(1) ==27:
            exit(0)
        if preview_flag == 1:
            preview_flag = 0
            preview_image.configure(image='')
            preview_button.config(text="Preview", bg="white", command = lambda: button(6))
            return 1
        
commands = {0 : photo,
            1 : download,
            2 : sync,
            3 : reload,
            4 : connect,
            5 : kill,
            6 : preview,
            7 : None,
            8 : save_to_directory}

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
#p_menu.set(connection_list[0])

createEntry("Amount", 1, 6,  amount)
createEntry("Delay",  2, 6,  delay )
#createEntry("Folder", 5, 10, folder)

createButton("Photos",   0, "white", 0)
createButton("Download", 4, "white", 1)
createButton("Save to...", 3, "white", 8)
createButton("Sync",     6, "white", 2)
createButton("Reload",   7, "white", 3)
createButton("Connect",  8, "white", 4)
createButton("Kill",     9, "white", 5)
preview_button  = createButton("Preview",  10, "white", 6)

createLabel("max. 50", 110, 25)
createLabel("max. 5s", 110, 45)
downloadpro_label = createLabel("", 67, 70)

preview_dropdwn = ttk.OptionMenu(window, p_menu, "no camera connected", *camera_list)
preview_dropdwn.place(x=67, y=220)

current_thread = threading.Thread(target=commands[4])
current_thread.start()

button_thread = threading.Thread(target=read_button_loop)
button_thread.start()

window.mainloop()
