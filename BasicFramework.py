import serial
import time
import struct
import random

arduino = serial.Serial("/dev/ttyUSB0", 9600)
time.sleep(2)
sleepytime = 1
matrix = 0x0000000000000000
mask = [0x8001, 0x810, 0x180, 0x1008, 0x2004, 0x4002]
i = 0

while True:
    #arduino.write(struct.pack("<Q", 0x66006600000))
    #time.sleep(1)
    #arduino.write(struct.pack("<Q", 0xf99f90099009f99f))
    #time.sleep(1)
    
    
    arduino.write(struct.pack("<Q", matrix))
    matrix = matrix >> 16
    matrix |= (mask[i] << 48)
    i += 1
    if i > 5:
	    i = 0
    time.sleep(0.125)

    #drops = random.randint(0, 2)
    #for x in range(0, drops):
    #    matrix += 1 << random.randint(0, 15)
    #arduino.write(struct.pack("<Q", matrix))
    #matrix *= 0x10000
    #matrix &= 0xffffffffffffffff
    #time.sleep(0.15)

    #arduino.write(struct.pack("<Q", random.randint(0, 0xffffffffffffffff)))
    #time.sleep(0.5)

    #plane = 0xffff
    #while plane < 0x10000000000000000:
    #    arduino.write(struct.pack("<Q", plane))
    #    if sleepytime > 0.016:
    #        time.sleep(sleepytime)
    #        plane = plane * 0x10000
    #    else:
    #        arduino.write(struct.pack("<Q", 0xffffffffffffffff))
    #        while True:
    #            time.sleep(1)
    #        sleepytime = 1
    #sleepytime = sleepytime / 2
