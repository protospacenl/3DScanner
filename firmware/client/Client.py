#!/usr/bin/env python2

import socket
import os
import struct
import fcntl
import json
import sys
import picamera
import time
import shutil
import RPi.GPIO as GPIO

import io
import logging
import SocketServer
import threading
from threading import Condition
import BaseHTTPServer

CONFIG_FILE_NAME="jozua.conf"
CONFIG_FILE_PATH=None

LED_GREEN=0
LED_RED=1
LED_ON=1
LED_OFF=0

JozuaConfig = None

CameraParameters = {    
                        "id": 1,
                        "resolution": { "width": 2592, "height": 1944 },
                        "preview": { "width": 640, "height": 480 },
                        "framerate": 30,
                        "delay": 0.55,
                        "iso": 200,
                        "exposure_compensation": 0,
                        "exposure_mode": "off",
                        "shutter_speed": 9000,
                        "brightness": 50,
                        "sharpness": 0,
                        "contrast": 0,
                        "awb_mode": "off",
                        "awb_gain": { "red": 1.5, "blue": 1.5 }
                    }

CaptureParameters = {
    "path": '/opt/3dscanner/photos',
    "bracketing": None
}

def get_ip_address(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', ifname[:15].encode())
    )[20:24])

def clear():
    data = "0"
    command = "0" 

def set_led_trigger(led, trigger):
    os.system("echo %s | sudo tee /sys/class/leds/led%d/trigger" % (trigger, led))

def set_led_state(led, state):
    os.system("echo %d | sudo tee /sys/class/leds/led%d/brightness" % (1 if state else 0, led))

CONFIG_FILE_PATH = "./%s" % (CONFIG_FILE_NAME)

if not os.path.exists(CONFIG_FILE_PATH):
    CONFIG_FILE_PATH = "/home/pi/.%s" % (CONFIG_FILE_NAME)
    if not os.path.exists(CONFIG_FILE_PATH):
        CONFIG_FILE_PATH = "/etc/%s" % (CONFIG_FILE_NAME)
        if not os.path.exists(CONFIG_FILE_PATH):
            CONFIG_FILE_PATH = None

if not CONFIG_FILE_PATH == None:
    with open(CONFIG_FILE_PATH, 'r') as f:
        JozuaConfig = json.load(f)

if JozuaConfig:
    if 'camera' in JozuaConfig:
        cameraconfig = JozuaConfig['camera'][0]
        CameraParameters['resolution'] = cameraconfig.get("resolution", { "width": 2592, "height": 1944 })
        CameraParameters['preview'] = cameraconfig.get("preview", { "width": 640, "height": 480 })
        CameraParameters['framerate'] =  cameraconfig.get("framerate", 30)
        CameraParameters['delay'] = cameraconfig.get("delay", 0.55)
        CameraParameters['iso'] = cameraconfig.get("iso", 200)
        CameraParameters['exposure_compensation'] = cameraconfig.get("exposure_compensation", 0)
        CameraParameters['exposure_mode'] = cameraconfig.get("exposure_mode", "off")
        CameraParameters['shutter_speed'] = cameraconfig.get("shutter_speed", 9000)
        CameraParameters['brightness'] = cameraconfig.get("brightness", 50)
        CameraParameters['sharpness'] = cameraconfig.get("sharpness", 0)
        CameraParameters['contrast'] = cameraconfig.get("contrast", 0)
        CameraParameters['awb_mode'] = cameraconfig.get("awb_mode", "off")
        CameraParameters['awb_gain'] = cameraconfig.get("awb_gain", { "red": 1.5, "blue": 1.5 })
    if 'capture' in JozuaConfig:
        captureconfig = JozuaConfig['capture']
        CaptureParameters['path'] = captureconfig.get('path', '/opt/3dscanner/photos')
        CaptureParameters['bracketing'] = captureconfig.get('bracketing', None)

print "Camera config: %s" % (CameraParameters)
print "Capture config: %s" % (CaptureParameters)

multicast_group = '224.0.0.10'
server_address = ('', 10000)

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

sock.bind(server_address)

ledpin = 7
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)
GPIO.setup(ledpin, GPIO.OUT)
GPIO.output(ledpin, True)

group = socket.inet_aton(multicast_group)
mreq = struct.pack('4sL', group, socket.INADDR_ANY)
sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

PAGE="""\
<html>
<head>
<title>picamera MJPEG streaming</title>
</head>
<body>
<h1>PiCamera MJPEG Streaming</h1>
<img src="stream.mjpg" width="640" height="480" />
</body>
</html>
"""
    
class StreamingOutput(object):
    def __init__(self):
        self.frame = None
        self.buffer = io.BytesIO()
        self.condition = Condition()

    def write(self, buf):
        if buf.startswith(b'\xff\xd8'):
            # New frame, copy the existing buffer's content and notify all
            # clients it's available
            self.buffer.truncate()
            with self.condition:
                self.frame = self.buffer.getvalue()
                self.condition.notify_all()
            self.buffer.seek(0)
        return self.buffer.write(buf)

class StreamingHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def finish(self, *args, **kw):
        try:
            if not self.wfile.close:
                self.wfile.flush()
                self.wfile.close()
        except socket.error:
            pass
        self.rfile.close()
        
    def handle(self):
        try:
            BaseHTTPServer.BaseHTTPRequestHandler.handle(self)
        except socket.error:
            pass
        
    def do_GET(self):
        if self.path == '/':
            self.send_response(301)
            self.send_header('Location', '/index.html')
            self.end_headers()
        elif self.path == '/index.html':
            content = PAGE.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
        elif self.path == '/stream.mjpg':
            self.send_response(200)
            self.send_header('Age', 0)
            self.send_header('Cache-Control', 'no-cache, private')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
            self.end_headers()
            try:
                while True:
                    with output.condition:
                        output.condition.wait()
                        frame = output.frame
                    self.wfile.write(b'--FRAME\r\n')
                    self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Content-Length', len(frame))
                    self.end_headers()
                    self.wfile.write(frame)
                    self.wfile.write(b'\r\n')
            except Exception as e:
                logging.warning(
                    'Removed streaming client %s: %s',
                    self.client_address, str(e))
        else:
            self.send_error(404)
            self.end_headers()

class StreamingServer(SocketServer.ThreadingMixIn, BaseHTTPServer.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True

address = ('', 8000)
server = StreamingServer(address, StreamingHandler)
output = StreamingOutput()
global stream_flag

def streaming_start():
    try:
        server.handle_request()
    except Exception as e:
        print("caught: %s" % str(e))
        
#Ensures pi gets proper IP address even if router boot-up was slower than pi boot-up     
while(get_ip_address('eth0')[0:7] != '192.168'):
    #print(get_ip_address('eth0')[0:7])
    os.system('sudo ifconfig eth0 up')

current_ip = get_ip_address('eth0')

set_led_trigger(LED_GREEN, "gpio")
set_led_trigger(LED_RED, "gpio")

while True:
    global stream_flag
    
    print ('\nwaiting to receive message')   
    data, address = sock.recvfrom(1024)

    
    print ('received %s bytes from %s' % (len(data), address))
    print (data)

    print ('sending acknowledgement to', address)
    
    if " " in data:
        command, par1, par2 = data.split(' ',2)
        print(data)
        print('command')
    else:
        command = data.decode()

# Check Message Data


    if command == 'photo':    
        print ('received photo')

        set_led_state(LED_RED, LED_ON)

        photo_flag = 0
        photo_number = 0
        photo_string = "0"
        if os.path.exists(CaptureParameters['path']):
            os.system("sudo rm -rf %s/*" % (CaptureParameters['path']))
        else:
            os.makedirs(CaptureParameters['path'])
        clear()
            
        #Turn on lighting
        GPIO.output(ledpin, False)
        
        #Camera settings            
        camera = picamera.PiCamera()
        camera.resolution = (CameraParameters['resolution']['width'], CameraParameters['resolution']['height'])
        camera.framerate = CameraParameters['framerate']
        camera.brightness = CameraParameters['brightness']
        camera.sharpness = CameraParameters['sharpness']
        camera.contrast = CameraParameters['contrast']
        camera.awb_mode = CameraParameters['awb_mode']
        camera.awb_gains = (CameraParameters['awb_gain']['red'], CameraParameters['awb_gain']['blue'])
        camera.iso = CameraParameters['iso']
        camera.exposure_compensation = CameraParameters['exposure_compensation']
        camera.exposure_mode = CameraParameters['exposure_mode']
        camera.shutter_speed = CameraParameters['shutter_speed']
        cameradelay = CameraParameters['delay']
        
        #Make photos
        for x in range(int(par1)):
            foto_num = x+1
            foto_path = "%s/%d" % (CaptureParameters['path'], foto_num)

            while(photo_number > photo_flag):
                photo_string, address = sock.recvfrom(1024)
                #if photo_string == "stop_photo"
                    #return 0
                photo_flag = int(photo_string)
                
            os.makedirs(foto_path)

            if CaptureParameters['bracketing'] and not CaptureParameters['bracketing']['mode'] == 'off':
                vmin = CaptureParameters['bracketing']['min']
                vmax = CaptureParameters['bracketing']['max']
                vsteps = CaptureParameters['bracketing']['steps']
                stepsize = 1

                if vsteps >= 1:
                    stepsize = (vmax-vmin) / vsteps

                for i in range(0, vsteps+1):
                    if CaptureParameters['bracketing']['mode'] == 'shutter':
                        camera.shutter_speed = vmin + i * stepsize
                    camera.capture('%s/%d_%d_%s.jpg' % (foto_path, i, foto_num, current_ip))
            else:
                camera.capture('%s/%d_%s.jpg' % (foto_path, foto_num, current_ip))
            sock.sendto("Photo: " + str(foto_num), address)
            
            photo_number += 1
            #time.sleep(float(par2)-(cameradelay))
            
        camera.close()
        set_led_state(LED_RED, LED_OFF)
        
    elif command == 'light':
        #Turn off lighting
        GPIO.output(ledpin, True)
            
    elif command == 'download':
        sock.sendto("Acknowledge " + command, address)
        #Send photos
        #for x in range(amount):
    
    elif command == 'reload':
        sock.sendto("Acknowledge " + command, address)
        sock.close()
        sys.exit(1)
        
    elif command == 'kill':
        sock.sendto("Acknowledge " + command, address)
        sys.exit()
        
    elif command == 'connect':
        print("Connect")
        set_led_state(LED_GREEN, LED_ON)
        sock.sendto("Acknowledge " + command, address)
        
    elif command == 'preview':
        set_led_trigger(LED_RED, "heartbeat")
        with picamera.PiCamera(resolution='640x480', framerate=24) as camera:
            camera.resolution = (CameraParameters['preview']['width'], CameraParameters['preview']['height'])
            camera.brightness = CameraParameters['brightness']
            camera.sharpness = CameraParameters['sharpness']
            camera.contrast = CameraParameters['contrast']
            camera.awb_mode = CameraParameters['awb_mode']
            camera.awb_gains = (CameraParameters['awb_gain']['red'], CameraParameters['awb_gain']['blue'])
            camera.iso = CameraParameters['iso']
            camera.exposure_compensation = CameraParameters['exposure_compensation']
            camera.exposure_mode = CameraParameters['exposure_mode']
            camera.shutter_speed = CameraParameters['shutter_speed']

            stream_flag = 1
            camera.start_recording(output, format='mjpeg')
            threading.Thread(target=streaming_start()).start()
            while data.decode() != "stop_preview":
                data, address = sock.recvfrom(1024)
            camera.stop_recording()
            camera.close()
        set_led_trigger(LED_RED, "gpio")
                
    else:
        if not command.isdigit():
            sock.sendto("Received wrong command", address)
            print ('Received wrong command')
