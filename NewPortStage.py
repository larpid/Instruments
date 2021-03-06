# -*- coding: utf-8 -*-
"""
Created on Wed Jul 19 15:58:15 2017

@author: vgrigore
"""

# -*- coding: utf-8 -*-
"""
Created on Tue May  9 14:06:55 2017

@author: vgrigore
"""

import sys
import clr 
import System
import Stage
import time

class NewPortStage(Stage.Stage):
    
    def __init__(self):
        self.NETAssemblyPath=r'C:\Windows\Microsoft.NET\assembly\GAC_64\Newport.XPS.CommandInterface\v4.0_1.0.0.0__9a267756cf640dcf'
        sys.path.append(self.NETAssemblyPath)
        clr.AddReference("Newport.XPS.CommandInterface")
        import CommandInterfaceXPS 
        self.myXPS=CommandInterfaceXPS.XPS()
        self.Address='192.168.254.254'
        self.Port=5001
        self.StageName="CykBlyat"
        self.velocity=100
        
    def XPS_Open (self):
        # Create XPS interface
        # Open a socket
        timeout = 1000
        result = self.myXPS.OpenInstrument(self.Address, self.Port, timeout)
        if result == 0:
            print( 'Open ', self.Address, ":", self.Port, " => Successful")
        else:
            print ('Open ', self.Address, ":", self.Port, " => failure ", result)
        
    def connect(self):
        self.XPS_Open()
        self.myXPS.GroupKill(System.String(self.StageName),System.String(""))
        self.myXPS.GroupInitialize(System.String(self.StageName),System.String(""))
        self.myXPS.GroupHomeSearch(System.String(self.StageName),System.String(""))
        self.myXPS.GroupMotionEnable(System.String(self.StageName),System.String(""))
        self.move_absolute(self.position_zero)
    
    
    
    def move_absolute(self, new_position):
        '''Moves stage to the given position in range of +/- 150 mm '''
        
        time_to_sleep=(abs(self.position_current-new_position))/self.velocity
        if (new_position<self.position_max)and(new_position<self.position_min):
            self.myXPS.GroupMoveAbsolute(System.String(self.StageName),[System.Double(new_position)],System.Int32(1),System.String(""))
            self.position_current=new_position
            time.sleep(time_to_sleep)
            print('Stage was moved to '+str(new_position))
        else:
            print('position is out of range')
        
    def position_get(self):
        pos=self.myXPS.GetCurrentPosition(System.Double(0),System.Double(0),System.Int32(1),System.Int32(1),System.Int32(1),System.Int32(1),System.String(self.StageName))
        return pos
    
    def disconnect(self):
        self.myXPS.GroupKill(System.String(self.StageName),System.String(""))
        print('Stage has been disconnected')
        
    
        
#%%

    
    def XPS_GetControllerVersion (self, myXPS, flag):
        result, version, errString = self.myXPS.FirmwareVersionGet(System.String(""),System.String(""))
        if flag == 1:
            if result == 0:
                print('XPS firmware version => ', version)
            else:
                print('FirmwareVersionGet Error => ',errString)
            return result, version
        
    def XPS_GetControllerState (self, myXPS, flag):
        result, state, errString = self.myXPS.ControllerStatusGet(System.Int32(0),System.String(""))
        if flag == 1:
            if result == 0:
                print('XPS controller state => ', state)
            else:
                print('ControllerStatusGet Error => ',errString)
        return result, state