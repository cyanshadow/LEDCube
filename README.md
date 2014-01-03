LEDCube
=======

Firmware and UI for 4x4x4 LED Cube

Instructions:
This firmware is for AVR microcontrollers, specifically I use a 328p bootloaded with Arduino UNO bootloader.  I recommend using the Arduino IDE to build and burn the firmware.  This makes it as simple as loading the sketch in the IDE, selecting the port your FTDI or other usb interface is connected to, and uploading.

The Python interface has been tested on 2.7 and 3.3, and requires PySerial and Bottle, available at http://pyserial.sourceforge.net/ and http://bottlepy.org/ respectively.  Then edit LEDCube.py and change interface, port, serialPort, baud, timeout, and serverHome to match your desired settings and location of the script.  The script can be run with the command 'python LEDCube.py'.  Assuming the cube is attached to the local computer, just point a web browser at http://localhost:8080 (if default settings used) to control the cube.

See http://www.secondstringsamurai.com/ledcube/ for more information and instructions for building the cube.
