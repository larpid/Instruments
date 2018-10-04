# -*- coding: utf-8 -*-
"""
Created on Tue Aug 7 16:00:00 2018

@author: larpid
"""

import Stage
import sys
import time
import serial
from parse import *
from serial.tools import list_ports


class PIStage(Stage.Stage):

    def __init__(self, axis='1', velocity=2):
        super(PIStage, self).__init__()
        self.axis = axis
        self.velocity = velocity  # unit: mm/s
        self.ser = serial.Serial()

    def connect(self):
        self.PI_connect()
        self.PI_setup()

    def PI_connect(self):
        self.ser = serial.Serial(       # baudrate, timeout, bytesize, parity and stopbits values copied from PITerminal standard values
            port=self.selectStagePort(),
            baudrate=57600,
            timeout=1,
            bytesize=8,
            parity='N',
            stopbits=1)
        #
        # confirm connection:
        print('connection established, stage respond on command \"IDN?\":')
        self.ser.write('IDN?\n')
        print(self.PI_read())
        #

    def PI_setup(self): #needs reworking
        # get minimum positions:
        self.ser.write('TMN?\n')
        readbuffer = self.PI_read()
        for eachline in readbuffer:
            if parse('{}={:e}{}', eachline)[0] == self.axis:
                self.position_min = parse('{}={:e}{}', eachline)[1]
        print('position_min is now set to: ' + str(self.position_min))
        self.pi_error_check()
        #
        # get maximum positions:
        self.ser.write('TMX?\n')
        readbuffer = self.PI_read()
        for eachline in readbuffer:
            if parse('{}={:e}{}', eachline)[0] == self.axis:
                self.position_max = parse('{}={:e}{}', eachline)[1]
        print('position_max is now set to: ' + str(self.position_max))
        self.pi_error_check()
        #
        # TODO: use this for sth or remove
        self.ser.write('POS?\n')
        print('positions:')
        print(self.PI_read())
        self.pi_error_check()
        #
        # set velocity
        self.ser.write('VEL ' + self.axis + ' ' + str(self.velocity) + '\n')
        self.ser.write('VEL?\n')
        print('velocities:')
        print(self.PI_read())
        self.pi_error_check()
        #
        # FRF
        self.pi_error_check()
        self.ser.write('FRF 1\n')
        self.pi_error_check()
        self.ser.write('FRF?\n')
        print('FRF result:')
        print(self.PI_read())
        self.pi_error_check()

    def disconnect(self):
        self.ser.close()
        print('Connection has been closed')

    def move_absolute(self, new_position):
        '''Move the stage to the given position in its range'''

        time_to_sleep = (abs(self.position_current - new_position)) / self.velocity
        if new_position >= self.position_min and new_position <= self.position_max:
            self.PI_servo(self.axis)
            self.ser.write('MOV ' + self.axis + ' ' + str(new_position) + '\n')
            self.position_current = new_position
            time.sleep(time_to_sleep)
            print('Stage was moved to ' + str(new_position))
        else:
            print('position is out of range')

    def PI_GetControllerIdentification(selfself):
        self.ser.write('IDN?\n')
        for eachline in self.PI_read():
            print(eachline)

    def PI_read(self):  # needs more elegant solution (wit less waittime)
        return self.ser.readlines()

    def PI_servo(self, axisID):
        self.ser.write('SVO ' + axisID + ' 1\n')
        self.ser.write('SVO? ' + axisID + '\n')
        print('servo state:')
        print(self.ser.readline())

    def pi_error_check(self, force_output=False):
        self.ser.write('ERR?\n')
        readbuffer = self.PI_read()
        if (readbuffer[0][0] != '0' or force_output):
            print('Controller reports Error Code: ' + readbuffer[0])
        if readbuffer[0][0] != '0':
            exit()

    def selectStagePort(self):
        ports_available = list_ports.comports()
        print(ports_available)
        print('select device:')
        for portindex, eachport in enumerate(ports_available):
            print(str(portindex) + ' - ' + eachport.device + '\t' + eachport.description)
        return ports_available[int(input())].device