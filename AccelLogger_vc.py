'''
Version: 1.2
Author: Joshua Lamb
'''
import time
import os
import datetime
import spidev
import RPi.GPIO as GPIO
import numpy as np
from Constants import *
from HelperFunctions import *

hf = HelperFunctions()
c = Constants()
'''
Check that we have necessary file structure and create it if we do not
'''
dirs = [c.ABSOLUTE_PATH, c.ABSOLUTE_PATH + "raw", c. ABSOLUTE_PATH + "fixed"]
for path in dirs:
    hf.ensureAndCreateDirectory(path)

'''
Set up pins for the INT1 on the accelerometer:
GPIO Mode - BOARD (Sets pin numbering to actual Pi pin numbers. NOT GPIO numbers)
Blue LED - Pin 3, OUTPUT
Interrupt 1 - Pin 18, INPUT, Pulled Down (Active High)
'''

hf.setupPinsForINIT1()

'''
Initialize SPI Communication
'''
spi = spidev.SpiDev()
spi.open(0, 0)
spi.mode = 3

id = spi.xfer([c.ACCEL_ID_REGISTER, 0])
print('Device ID (0xE5): {}'.format(hex(id[1])))
print('Beginning Collection')

'''
Offset values for each axis of the accelerometer are stored in /home/pi/offsets.txt
Read these offsets into an array and save them for later.
'''
try:
   fh = open("/home/pi/offsets.txt", "r")
except IOError:
   print ("Error: can\'t find file or read data")
else:
   offsets = fh.readlines()
   print ("Written content in the file successfully")
   #fh.close()


xoffset = float(offsets[0].replace('\n', ''))
yoffset = float(offsets[1].replace('\n', ''))
zoffset = float(offsets[2].replace('\n', ''))

# Read the Offsets
# xoffset = spi.xfer2([30 | 128, 0])
# yoffset = spi.xfer2([31 | 128, 0])
# zoffset = spi.xfer2([32 | 128, 0])


'''
This function initializes the accelerometer. The spi.xfer2() function sends the 2nd number in the array to the
register defined by the 1st number.
1. Turn off all functionality of the device.
2. Turn off the interrupt that signals data is ready.
3. Send all interrupts to INT1.
4. Set the data acquisition rate to 400Hz.
5. Set the resolution to 10-bit and the range to +/-8g.
6. Turn measurement on.
7. Enable FIFO mode. This sets the INT1 interrupt when 5 values have been stored.
'''
def initadxl345():
    # Enter Power Saving State
    # POWER_CTL REGISTER (0 0 Link AUTO_SLEEP Measure Sleep {Wakeup Wakeup})
    # Turn Data Ready Interrupt Off
    # INT_ENABLE REGISTER (DATA_READY SINGLE_TAP DOUBLE_TAP Activity Inactivity FREE_FALL Watermark Overrun)
    # Send Interrupts to INT1 (Set to 1 to send to INT2)
    # INT_MAP REGISTER (DATA_READY SINGLE_TAP DOUBLE_TAP Activity Inactivity FREE_FALL Watermark Overrun)
    # Set Data Rate to 400Hz
    # BW_RATE REGISTER (0 0 0 LOW_POWER {Rate Rate Rate Rate})
    # Enable 10 bit resolution and +/- 8g
    # DATA_FORMAT REGISTER (SELF_TEST SPI INT_INVERT 0 FULL_RES Justify {Range Range})
    # Enable Measurement
    # POWER_CTL REGISTER (0 0 Link AUTO_SLEEP Measure Sleep {Wakeup Wakeup})
    # FIFO Mode (Collect 5 samples before setting the watermark interrupt)
    # FIFO_CTL ({FIFO_MODE FIFO_MODE} Trigger {Samples Samples Samples Samples Samples})
    
    initadx = np.array([[0x2D, 0b00000000],[0x2E, 0b00000000], [0x2F, 0b00000000],[0x2C, 0b00001100],[0x31, 0b00000010],
                       [0x2D, 0b00001000], [0x38, 0b01000101]])
    for x in np.nditer(initadx):
        spi.xfer2(x)


'''
This function queries the accelerometer and returns the X, Y, Z acceleration values in an array.
'''
def readadxl345():
    rx = spi.xfer2([242, 0, 0, 0, 0, 0, 0])

    out = [rx[1] | (rx[2] << 8), rx[3] | (rx[4] << 8), rx[5] | (rx[6] << 8), 0]

    if out[0] & (1 << c.BITS_TO_SHIFT - 1):
        out[0] -= 1 << c.BITS_TO_SHIFT
    out[0] = out[0] * c.ACCEL_MULTIPLIER - xoffset

    if out[1] & (1 << c.BITS_TO_SHIFT - 1):
        out[1] -= 1 << c.BITS_TO_SHIFT
    out[1] = out[1] * c.ACCEL_MULTIPLIER - yoffset

    if out[2] & (1 << c.BITS_TO_SHIFT - 1):
        out[2] -= 1 << c.BITS_TO_SHIFT
    out[2] = out[2] * c.ACCEL_MULTIPLIER - zoffset

    return out


buffer_array = np.empty(shape=(c.NUM_ACCEL_BUFFER_ROWS, c.NUM_ACCEL_BUFFER_COLUMNS))

initadxl345()

spi.xfer2([0x2E, 0b00000010])

spi.xfer2([242, 0, 0, 0, 0, 0, 0])

trigger = 0
event = 1
arrayindex = 0
counter = 0

for j in range(3):
    GPIO.output(c.BLUE_LED, True)
    time.sleep(.25)
    GPIO.output(c.BLUE_LED, False)
    time.sleep(.25)

while True:

    while not GPIO.input(c.INTERRUPT_1):
        time.sleep(.005)

    buffer_counter = 0

    while buffer_counter < 5:
        axia = readadxl345()
        buffer_array[arrayindex] = [axia[0], axia[1], axia[2]]

        if ((axia[0] > c.POSITIVE_TRIGGER_THRESHOLD or axia[0] < c.NEGATIVE_TRIGGER_THRESHOLD or axia[1] > c.POSITIVE_TRIGGER_THRESHOLD or axia[1] < c.NEGATIVE_TRIGGER_THRESHOLD or axia[2] > c.POSITIVE_TRIGGER_THRESHOLD or axia[
            2] < c.NEGATIVE_TRIGGER_THRESHOLD) and trigger == 0):
            trigger = 1
            counter = 0
            GPIO.output(c.BLUE_LED, True)
            buffer_array[c.EVENT_TRIGGER_LOC] = [arrayindex, 0, 0]

        if arrayindex == 1199:
            arrayindex = 0

        else:
            arrayindex += 1

        if trigger == 1:
            counter += 1

        buffer_counter += 1

    if counter > c.COLLECTION_STOP:
        counter = 0
        trigger = 0

        GPIO.output(c.BLUE_LED, False)
        event_timestamp = datetime.datetime.now()

        
        hf.ensureAndCreateDirectory(c.ABSOLUTE_PATH + 'raw/{0}_{1}_{2}'.format(event_timestamp.year, 
                                                                               event_timestamp.month, 
                                                                               event_timestamp.day))
        hf.ensureAndCreateDirectory(c.ABSOLUTE_PATH + 'fixed/{0}_{1}_{2}'.format(event_timestamp.year, 
                                                                                 event_timestamp.month, 
                                                                                 event_timestamp.day))

        np.savetxt(c.ABSOLUTE_PATH + 'raw/{0}_{1}_{2}/RawEvent_{3}_{4}_{5}.txt'.format(event_timestamp.year,
                                                                                        event_timestamp.month,
                                                                                        event_timestamp.day,
                                                                                        event_timestamp.hour,
                                                                                        event_timestamp.minute,
                                                                                        event_timestamp.second),
                   buffer_array, delimiter=',', newline='\n', fmt='%3.4f')
        event += 1


