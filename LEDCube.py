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
serialPort = "COM/dev/tty"   # Serial port where LED cube is connected
baud       = 9600            # Baud rate of cube, 9600 is default
timeout    = 15              # How long, in seconds, to run animations in sequences
serverHome = "/path/to/dir/with/LEDCube.py" # Path to installation
## End config

## Globals
matrix = 0x0000000000000000
status = "stopped"
starting = True
modes = ["beamdown", "blink", "bounce", "crazy", "helix", "innerouter",\
         "raindrops", "spin", "twinkle", "_sequence", "_random"]
animation = modes[0]

## Attempt to open connection to cube
try:
    arduino = serial.Serial(serialPort, baud)
    time.sleep(2)
except:
    print("Error opening serial port, quitting.")
    quit()
    
## Animation functions.  These should perform a single frame of animation
## and then return.  They must be named the same as the strings in modes[].
## Recommended that a frame be no longer than 1 second, which feels like
## a reasonable delay with a web-based UI
## Animations with names starting with _ are special.  They are playlists,
## which will run other animations.  Provided are _sequence and _random, which
## play other animations in sequence, or randomly, respectively.  They will skip
## any animation whose name also starts with _, and any new playlists should
## implement this behavior.  By convention, place playlists at the end of the list.
def beamdown():
    ## Light each plane in order, faster and faster until we fill the cube
    global starting
    if not hasattr(beamdown, "plane"):
        beamdown.plane = 0xffff
    if not hasattr(beamdown, "sleeptime"):
        beamdown.sleeptime = 1
    if not hasattr(beamdown, "done"):
        beamdown.done = False
    if starting:
        beamdown.plane = 0xffff
        beamdown.sleeptime = 1
        starting = False
        beamdown.done = False
    if beamdown.plane < 0x10000000000000000 and not beamdown.done:
        arduino.write(struct.pack("Q", beamdown.plane))
        if beamdown.sleeptime > 0.016:
            time.sleep(beamdown.sleeptime)
            beamdown.plane = beamdown.plane * 0x10000
        else:
            arduino.write(struct.pack("<Q", 0xffffffffffffffff))
            beamdown.done = True
    elif not beamdown.done:
        beamdown.plane = 0xffff
        beamdown.sleeptime = beamdown.sleeptime / 2.0
    else:
        time.sleep(0.001)
        
def blink():
    if not hasattr(blink, "toggle"):
        blink.toggle = True
    if blink.toggle:
        arduino.write(struct.pack("<Q", 0xffffffffffffffff))
        blink.toggle = False
    else:
        arduino.write(struct.pack("<Q", 0x0000000000000000))
        blink.toggle = True
    time.sleep(1)

def bounce():
    pass
        
def crazy():
    ## Just randomly set the states of LEDs
    arduino.write(struct.pack("<Q", random.randint(0, 0xffffffffffffffff)))
    time.sleep(0.35)
    
def helix():
    ## Rotating double helix
    global starting
    global matrix
    if not hasattr(helix, "i"):
        helix.i = 0
    if not hasattr(helix, "mask"):
        helix.mask = [0x8001, 0x810, 0x180, 0x1008, 0x2004, 0x4002]
    if starting:
        helix.i = 0
        starting = False
    arduino.write(struct.pack("<Q", matrix))
    matrix = matrix >> 16
    matrix |= (helix.mask[helix.i] << 48)
    helix.i += 1
    if helix.i > 5:
        helix.i = 0
    time.sleep(0.125)
    
def innerouter():
    ## Alternate inner and outer cube wireframe
    if not hasattr(innerouter, "toggle"):
        innerouter.toggle = True
    if innerouter.toggle:
        arduino.write(struct.pack("<Q", 0x0000066006600000))
        innerouter.toggle = False
    else:
        arduino.write(struct.pack("<Q", 0xf99f90099009f99f))
        innerouter.toggle = True
    time.sleep(1)
    
def raindrops():
    ## Raindrops trickle from the top layer down
    global matrix
    drops = random.randint(0, 2)
    for x in range(0, drops):
        matrix += 1 << random.randint(0, 15)
    arduino.write(struct.pack("<Q", matrix))
    matrix *= 0x10000
    matrix &= 0xffffffffffffffff
    time.sleep(0.15)
    
def spin():
    pass
    
def twinkle():
    ## Twinkle on and off randomly, switching when cube is full / empty
    global starting
    global matrix
    if not hasattr(twinkle, "toggle"):
        twinkle.toggle = True
    if starting:
        twinkle.toggle = True
        starting = False
    if twinkle.toggle:
        if matrix < 0xffffffffffffffff:
            twink = 1 << random.randint(0, 63)
            if not twink & matrix:
                matrix |= twink
                arduino.write(struct.pack("<Q", matrix))
                time.sleep(0.15)
        else:
            twinkle.toggle = False
            time.sleep(0.5)
    else:
        if matrix > 0:
            twink = 1 << random.randint(0, 63)
            if matrix & twink:
                matrix &= matrix ^ twink
                arduino.write(struct.pack("Q", matrix))
                time.sleep(0.15)
        else:
            twinkle.toggle = True                    
            time.sleep(0.5)
            
def _sequence():
    global starting
    if not hasattr(_sequence, "_time"):
        _sequence._time = time.time()
    if not hasattr(_sequence, "i"):
        _sequence.i = 0
    if _sequence._time + timeout > time.time():
        if modes[_sequence.i][0] == '_':
            _sequence.i = _sequence.i + 1
            if _sequence.i >= len(modes):
                _sequence.i = 0
        else:
            globals()[modes[_sequence.i]]()
    else:
        _sequence._time = time.time()
        _sequence.i = _sequence.i + 1
        starting = True
        if _sequence.i >= len(modes):
            _sequence.i = 0
    
def _random():
    if not hasattr(_random, "_time"):
        _random._time = time.time()
    if not hasattr(_random, "i"):
        _random.i = random.randint(0, len(modes) - 1)
    if _random._time + timeout > time.time():
        if modes[_random.i][0] == '_':
            _random.i = random.randint(0, len(modes) - 1)
        else:
            globals()[modes[_random.i]]()
    else:
        _random._time = time.time()
        _random.i = random.randint(0, len(modes) - 1)
                
## Cube control thread, this handles interfacing with the cube
## It is controlled by the status, starting, animation, and matrix globals
## If status is running, it will call the named animation and yield
def cube():
    while True:
        if status == "running":
            globals()[animation]()  # Call the function named in animation
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

