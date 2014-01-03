## Python control script for 4x4x4 LED Cube
## John Caswell, 2014

import serial
import time
import struct
import random
import threading
from bottle import route, get, post, request, run, redirect, static_file

## Configuration:  set these to match your setup
interface  = "0.0.0.0"       # Interface to listen on, 0.0.0.0 is all interfaces
port       = 8080            # Port to listen on
serialPort = "/dev/ttyUSB0"  # Serial port where LED cube is connected
baud       = 9600            # Baud rate of cube, 9600 is default
timeout    = 30              # How long to run animations in sequence
serverHome = "/home/pi/Projects/LEDCube" # Path to installation
## End config

## Globals
matrix = 0x0000000000000000
animation = "beamdown"
status = "stopped"
starting = True
modes = ["beamdown", "bounce", "crazy", "helix", "innerouter",\
         "raindrops", "spin", "twinkle", "sequence", "random"]

## Attempt to open connection to cube
try:
    arduino = serial.Serial(serialPort, baud)
    time.sleep(2)
except:
    print("Error opening serial port, quitting.")
    quit()

## Cube control thread, this handles interfacing with the cube
## It is controlled by the status, starting, animation, and matrix globals
## If status is running, it will draw a frame of animation and yield
def cube():
    global matrix
    global starting
    mask = [0x8001, 0x810, 0x180, 0x1008, 0x2004, 0x4002]
    i = 0
    while True:
        if status == "running":
            ## Light each plane in order, faster and faster until we fill the cube
            if animation == "beamdown":
                if starting:
                    plane = 0xffff
                    sleeptime = 1
                    starting = False
                    done = False
                if plane < 0x10000000000000000 and not done:
                    arduino.write(struct.pack("Q", plane))
                    if sleeptime > 0.016:
                        time.sleep(sleeptime)
                        plane = plane * 0x10000
                    else:
                        arduino.write(struct.pack("<Q", 0xffffffffffffffff))
                        done = True
                elif not done:
                    plane = 0xffff
                    sleeptime = sleeptime / 2.0
                else:
                    time.sleep(0.001)
            ## Just randomly set the states of LEDs
            elif animation == "crazy":
                arduino.write(struct.pack("<Q", random.randint(0, 0xffffffffffffffff)))
                time.sleep(0.5)
            ## Raindrops trickle from the top layer down
            elif animation == "raindrops":
                drops = random.randint(0, 2)
                for x in range(0, drops):
                    matrix += 1 << random.randint(0, 15)
                arduino.write(struct.pack("<Q", matrix))
                matrix *= 0x10000
                matrix &= 0xffffffffffffffff
                time.sleep(0.15)
            ## Rotating double helix
            elif animation == "helix":
                if starting:
                    i = 0
                    starting = False
                arduino.write(struct.pack("<Q", matrix))
                matrix = matrix >> 16
                matrix |= (mask[i] << 48)
                i += 1
                if i > 5:
                    i = 0
                time.sleep(0.125)
            ## Alternate inner and outer cube wireframe
            elif animation == "innerouter":
                arduino.write(struct.pack("<Q", 0x66006600000))
                time.sleep(1)
                arduino.write(struct.pack("<Q", 0xf99f90099009f99f))
                time.sleep(1)
        else:
            time.sleep(0.001)
    
## Create the thread to control the cube and start it
t = threading.Thread(target = cube)
t.setDaemon(True)
t.start()

## Handle main control buttons
@route('/start')
def start():
    global status
    status = "running"
    redirect("/")

@route('/stop')
def stop():
    global matrix
    global status
    global starting
    starting = True
    status = "stopped"
    matrix = 0x0000000000000000
    arduino.write(struct.pack("<Q", matrix))
    redirect("/")

@route('/pause')
def pause():
    global status
    status = "paused"
    redirect("/")
    
## Add path for images
@route('/images/<filename>')
def images(filename):
    return static_file(filename, root=serverHome + "/images/")
    
## Define main page
@get('/')
def root():
    header = '''<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">
<html>
<head>
<meta http-equiv="Content-type" content="text/html;charset=UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>LED Cube Control</title>
<style type="text/css">body{color:#ffffff}</style>
</head>
<body style="background-color:#000000">
<div align="center">
'''
    body = '''<img src="/images/pps.jpg" alt="buttons" usemap="#buttonmap">
<map name="buttonmap">
<area shape="circle" coords="108,112,34" href="/pause" alt="Pause">
<area shape="circle" coords="195,112,34" href="/start" alt="Play">
<area shape="circle" coords="277,112,34" href="/stop" alt="Stop">
</map>
<form action="" method="post">
<select name="animation">
'''
    formlist= ""
    for mode in modes:
        formlist += "<option"
        if mode == animation:
            formlist += " selected=\"selected\""
        formlist += ">" + mode + "</option>\n"
    footer='''</select>
<input type="image" src="/images/go.png">
</form>
</div>
</body>
</html>
'''
    response = header
    response += "current animation:  "
    response += animation + " "
    response += status + "<br>\n"
    response += body
    response += formlist
    response += footer
    return response

## Handle animation selection form
@post('/')
def form():
    global animation
    global matrix
    global starting
    starting = True
    animation = request.forms.get('animation')
    matrix = 0x0000000000000000
    return start()

## Start HTTP Server
run(host=interface, port=port)

