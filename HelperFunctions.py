"""
Name :HelperFunctions.py
Description : Common Functions 
Author : Chaitanya Valaparla
"""

import os
import RPi.GPIO as GPIO
import Constants as c


def setupPinsForINIT1():
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(c.INTERRUPT_1, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(c.BLUE_LED, GPIO.OUT)
    GPIO.output(c.BLUE_LED, False)


def endureAndCreateDirectory(path):
    directoryToCreate = path
    if not os.path.isdir(directoryToCreate):
        os.mkdir(directoryToCreate)



