"""created by L. Pidde 01/2020
this is a control script to send keypresses/holds on a raspberry pi to any tango servers
-it works as a keylogger on the otherwise deactivated keyboard of the pi (tty1,2,3,4,5 and 6 are deactivated)
-key are bound to actions by config file 'c7controlKeys.cfg' and send a PRESS, RELEASE and regular heartBEAT signals
    to any receiving tango server
-the receiving server must implement a controlKey_[action] command to be able to execute key hold actions
-single press signals can call a normal tango command
"""

import keyboard
import time
from tango import DeviceProxy
from threading import Lock

active_beats_lock = Lock()
active_beats = []


def key_event(key):
    """handles key=keyboard.KeyboardEvent events"""

    if key.event_type == "down":
        if key.name not in keys_held_down:
            print('%s %s' % (key.name, key.event_type))
            keys_held_down.append(key.name)
    elif key.event_type == "up":
        keys_held_down.remove(key.name)
        print('%s %s' % (key.name, key.event_type))


if __name__ == "__main__":
    # listeners works in background (separate Thread)
    keyboard.hook(key_event)

    # initialize known events from cfg file
    config_file = open('c7controlKeys.cfg', 'r')
    for textline in config_file.readlines():
        if textline[0] != '#' and len(textline) > 0:
            #todo
    config_file.close()

    # keep alive
    #keyboard.wait()
    while True:
        time.sleep(1)

     #self.tdc_proxy = DeviceProxy(self.tdc_name)