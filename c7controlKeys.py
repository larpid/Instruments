"""created by L. Pidde 01/2020
this is a control script to send keypresses/holds on a raspberry pi to any tango servers
-it works as a keylogger on the otherwise deactivated keyboard of the pi (tty1,2,3,4,5 and 6 are deactivated)
-key are bound to actions by config file 'c7controlKeys.cfg' and send a PRESS, RELEASE and regular heartBEAT signals
    to any receiving tango server
-the receiving server must implement a controlKey_[action] command to be able to execute key hold actions
-single press signals can call a normal tango command

script needs tango and epics installed (sth like:
 apt-get install tango-common python3-pytango

)
"""

import keyboard
import time
import os
from tango import DeviceProxy, DeviceData
#import epics
from threading import Lock

# global settings
DEBUG = True
HEARTBEAT_DELAY = 50  # in ms (sends heartbeat every so often)


class ControlKeys:
    known_modifiers = ['shift', 'ctrl', 'alt', 'alt gr']

    def __init__(self):
        # thread shared objects
        self.active_beats_lock = Lock()
        self.active_beats = []

        # only used by key_event function
        self.keys_held_down = []
        self.last_key_event_time = 0

        # read only objects
        self.events = []
        self.device_proxies = {}

        # set up known events from config file
        print('evaluating config file...')
        config_file = open(os.path.join(os.path.dirname(__file__), 'c7controlKeys.ini'), 'r')
        for textline in config_file.readlines():
            textline = textline.split('#')[0].strip('\n')
            if len(textline.strip()) > 0 and len(textline.split('\t')) == 5:
                event = {}
                event['key'], event['modify'], event['type'], event['device'], event['command'] = \
                    textline.split('\t')
                if event['key'] in self.known_modifiers:
                    raise RuntimeError("%s is a possible modifier key and therefore can't trigger its own event" %
                                       event['key'])
                event['modify'] = event['modify'].split(';')
                for key in event['modify']:
                    if key != '' and key not in self.known_modifiers:
                        raise RuntimeError("unknown modifier: %s" % event['modify'])
                if event['device'] not in self.device_proxies and \
                        event['type'] in ['tango_command', 'tango_controlKey']:
                    self.device_proxies[event['device']] = DeviceProxy(event['device'])
                if event['type'] in ['tango_command', 'tango_controlKey', 'epics_command']:
                    self.events.append(event)
                else:
                    print('event type unknown for line: %s' % textline)
            else:
                if len(textline.strip()) > 0:
                    print("line \"%s\" has wrong number of tabs (use only one between each field)" % textline)
        config_file.close()

    def key_event(self, key):
        """handles key=keyboard.KeyboardEvent events"""

        if key.event_type == "down":
            if key.name not in self.keys_held_down and key.time >= self.last_key_event_time:
                if DEBUG:
                    print('%s %s %s' % (key.name, key.event_type, key.time))
                self.keys_held_down.append(key.name)

                for event in self.events:
                    if event['key'] == key.name:

                        # check required modifier keys (e.g.: is "ctrl" pressed for "ctrl" + "m" combination?)
                        modifiers_active = True
                        for modifier in self.known_modifiers:
                            if (modifier in event['modify']) != keyboard.is_pressed(modifier):
                                modifiers_active = False
                                print(modifier + " " + str(event['modify']) + " " + str(keyboard.is_pressed(modifier)))
                                break
                        if not modifiers_active:
                            continue

                        if DEBUG:
                            print(event['device'])

                        # choose action based on event type
                        if event['type'] == 'tango_command':
                            self.device_proxies[event['device']].command_inout(event['command'])
                        elif event['type'] == 'tango_controlKey':
                            if event['command'][:11] == 'controlKey_':
                                # command parameter: 1=start, 0=stop, 2=heartbeat
                                self.device_proxies[event['device']].command_inout(event['command'], 1)  # 1 starts
                                with self.active_beats_lock:
                                    self.active_beats.append(event)
                            else:
                                raise SyntaxError('tango_controlKey command must start with "controlKey_"')
                        elif event['type'] == 'epics_command':
                            print('epics_command event type not yet implemented')
                            # todo: maybe implement this at some point
                            # so far it has been taken out because getting epics known devices is really unreliable
                            # and bad
                            #epics.caput(event['command'], 1)
                        else:
                            print('unknown event type')

        elif key.event_type == "up":
            if key.name in self.keys_held_down:
                self.keys_held_down.remove(key.name)
            if DEBUG:
                print('%s %s' % (key.name, key.event_type))

            # send stop signal and unschedule heartbeat
            with self.active_beats_lock:
                for event_index, event in enumerate(self.active_beats):
                    if event['key'] == key.name or key.name in event['modify']:
                        # command parameter: 1=start, 0=stop, 2=heartbeat
                        self.device_proxies[event['device']].command_inout(event['command'], 0)  # 0 stops
                        self.active_beats[event_index] = None  # removes active heartbeat
                self.active_beats = [event for event in self.active_beats if event is not None]
        self.last_key_event_time = time.time()


if __name__ == "__main__":
    ck = ControlKeys()

    # listeners works in background (separate Thread)
    keyboard.hook(ck.key_event)
    print('started controlKeys script with following known key events:')
    print(ck.events)

    # heartbeat loop
    while True:
        with ck.active_beats_lock:
            for event in ck.active_beats:
                ck.device_proxies[event['device']].command_inout(event['command'], 2)  # 2 beats
        time.sleep(HEARTBEAT_DELAY/1000.0)
