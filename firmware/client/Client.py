import socket
import os
import struct
import fcntl
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

dir = 'Desktop/photos'

multicast_group = '224.0.0.10'
server_address = ('', 10000)

# Create the socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Bind to the server address
sock.bind(server_address)

#Init GPIO
ledpin = 7
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)
GPIO.setup(ledpin, GPIO.OUT)
GPIO.output(ledpin, True)

# Tell the operating system to add the socket to the multicast group
# on all interfaces.
group = socket.inet_aton(multicast_group)
mreq = struct.pack('4sL', group, socket.INADDR_ANY)
sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

# Receive/respond loop

PAGE="""\
<html>
<head>
<title>picamera MJPEG streaming demo</title>
</head>
<body>
<h1>PiCamera MJPEG Streaming Demo</h1>
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
        photo_flag = 0
        photo_number = 0
        photo_string = "0"
        if os.path.exists(dir):
            os.system("sudo rm -rf %s" %dir)
        os.makedirs(dir)
        clear()
            
        #Turn on lighting
        GPIO.output(ledpin, False)
        
        #Camera settings
        camera = picamera.PiCamera()
        camera.resolution = (2592, 1944)
        camera.framerate = 30
        camera.brightness = 50
        camera.awb_mode = 'off'
        camera.awb_gains = (1.5,1.5)
        camera.iso = 200
        camera.exposure_mode = 'off'
        camera.shutter_speed = 9000
        cameradelay = 0.55

        #Make photos
        for x in range(int(par1)):
            
            while(photo_number > photo_flag):
                photo_string, address = sock.recvfrom(1024)
                photo_flag = int(photo_string)
                
            camera.capture('/home/pi/%s/%s_%d.jpg' % (dir, get_ip_address('eth0'), x+1))
            sock.sendto("Photo: " + str(x+1), address)
            photo_number += 1
            time.sleep(float(par2)-(cameradelay))
            
        camera.close()
        
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
        os.system("sudo python Reload.py")
        
    elif command == 'kill':
        sock.sendto("Acknowledge " + command, address)
        sys.exit()
        
    elif command == 'connect':
        print("Connect")
        sock.sendto("Acknowledge " + command, address)
        
    elif command == 'preview':
        with picamera.PiCamera(resolution='320x240', framerate=24) as camera:
            stream_flag = 1
            camera.start_recording(output, format='mjpeg')
            threading.Thread(target=streaming_start()).start()
            while data.decode() != "stop_preview":
                data, address = sock.recvfrom(1024)
            camera.stop_recording()
            camera.close()
                
    else:
        if not command.isdigit():
            sock.sendto("Received wrong command", address)
            print ('Received wrong command')
