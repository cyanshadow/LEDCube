/**
 * 4x4x4 LED Cube.
 * Sparkly lights for great enjoyment.
 * John Caswell, 2014
 */

unsigned char matrix[8];  // This holds the data that is being displayed on the cube
unsigned char buffer[8];  // This holds incoming data until 64 bits are received
int index = 0;            // Track how many bytes have been received via serial
boolean show = false;     // Should we update the cube?

void lightMatrix() {
  // The following uses the port registers to quickly set the state of the io pins
  // Pins 0 and 1 are our serial line, so we don't touch those.
  // Pins 2 and 3 go to the 3-8 decoder which is being used as a 2-4
  // To select which layer of the cube gets lit.
  // The rest of the shifting operations move the bits into the right
  // positions to correspond with the pins controlled by the port registers.
  for(int i = 0; i < 8; i+=2) {
    PORTD = (PORTD & 0x03) | i * 0x02 | (0xF0 & (matrix[i] << 4));
    PORTB = (PORTB & 0xC0) | (0x3F & ((matrix[i] >> 4) | (matrix[i + 1] << 4)));
    PORTC = (PORTC & 0xC0) | (0x3F & (matrix[i + 1] >> 2));
    delay(4);  // My transistors have a small delay compared to the 3-8 decoder
    // The above delay and then setting all the pins to off with the below
    // prevents ghosting.  The cube could run at ~250 fps, but this brings it
    // down to about ~60 fps (1000/16ms per frame) which is acceptable.
    PORTD = PORTD & 0x03;
    PORTB = PORTB & 0xC0;
    PORTC = PORTC & 0xC0;
  }
}

void setup() {
  // Initialize the serial port and set all other pins to output.
  Serial.begin(9600);
  for(int i = 2; i < 20; i++) {
    pinMode(i, OUTPUT);
  }
}

void loop() {
  // Update the matrix here, so we can be sure it's not updated while
  // drawing the cube.  If we updated during serialEvent(), which is
  // interrupt driven, there could be the possibility that we'd update
  // partway through lightMatrix()
  if(show) {
    memcpy(matrix, buffer, 8);
    show = false;
  }
  lightMatrix();  // Always refresh the cube
}

void serialEvent() {
  // Called when triggered by interrupt on serial line, which means
  // new data has arrived.  We hold the incoming data in a buffer
  // until there's enough to describe the state of the cube, and then
  // set a flag to update the cube matrix when it is safe to do so.
  while(Serial.available()) {
    buffer[index] = (char)Serial.read();
    index++;
    if(index > 7) {
      index = 0;
      show = true;
    }
  }
}
