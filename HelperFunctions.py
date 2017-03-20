"""
Name :HelperFunctions.py
Description : Common Functions 
Author : Chaitanya Valaparla
"""

import time
import os
import datetime
import spidev
import RPi.GPIO as GPIO
import numpy as np
from Constants import *

c = Constants()

class HelperFunctions:
    def ensureAndCreateDirectory(self, path):
        directoryToCreate = path
        if not os.path.isdir(directoryToCreate):
            os.mkdir(directoryToCreate)

    def setupPinsForINIT1(self):
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(c.INTERRUPT_1, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(c.BLUE_LED, GPIO.OUT)
        GPIO.output(c.BLUE_LED, False)

    
