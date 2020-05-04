"""Tango server for the implementation of the movement functionalities for our manipulator (currently only the main motor)
written by Lars Pidde, 01/2020"""

from ManipulatorMotor import ManipulatorMotor
import sys
import time
from threading import Thread, Lock
from serial.serialutil import SerialException
from tango import AttrWriteType
import tango
from tango import DevState
from tango.server import run
from tango.server import Device, DeviceMeta
from tango.server import device_property
from tango.server import attribute, command, pipe
from TangoHelper import StoreStdOut


class ManipulatorMotorTANGO(Device, metaclass=DeviceMeta):

    speed = device_property(dtype=float,
                            default_value=100.0,
                            doc="standard mode rotation speed given as step pulses per second")

    speed_fast = device_property(dtype=float,
                                 default_value=500.0,
                                 doc="fast mode rotation speed given as step pulses per second.")

    movement_chunk_duration_ms = device_property(dtype=float,
                                             default_value=50.0,
                                             doc="time (in ms) of a single chunk of the continuous motion.\n" +
                                             "no heartbeat checks are made in between.")

    max_heartbeat_distance_ms = device_property(dtype=float,
                                             default_value=150.0,
                                             doc="maximum time (in ms) since last received heartbeat.\n" +
                                             "if time is exceeded continuous motion will be terminated.\n" +
                                             "should be more than movement_chunk_duration")

    def init_device(self):
        sys.stdout = StoreStdOut()
        self.get_device_properties()  # without this all device properties are None
        self.active_controlKey_action = None
        # needed to reliably setup the action. its methods dont need thread safety
        self.active_controlKey_action_lock = Lock()
        self.set_state(DevState.ON)
        self.action_thread = Thread(target=self.action_thread_method, daemon=True)
        self.thread_start_time = time.time()
        self.action_thread.start()

    def action_thread_method(self):
        thread_internal_start_time = self.thread_start_time
        # check is used to end thread on device reinitialization
        while thread_internal_start_time == self.thread_start_time:
            if self.active_controlKey_action is not None:
                print(thread_internal_start_time)
                action_survived = self.active_controlKey_action.execute_next_chunk()
                if not action_survived:
                    with self.active_controlKey_action_lock:
                        self.active_controlKey_action = None

    @attribute(dtype=str)
    def server_message(self):
        return sys.stdout.read_stored_message()

    @command(dtype_in=int)
    def controlKey_motor_CW(self, command_code):
        def move_one_chunk():
            ManipulatorMotor.move(True, self.speed, self.movement_chunk_duration_ms/1000.0)

        if command_code == 1:
            # start action
            self.set_state(DevState.MOVING)
            with self.active_controlKey_action_lock:
                self.active_controlKey_action = ControlKeyAction("motor_CW",
                                                                 move_one_chunk, self.max_heartbeat_distance_ms)
        elif command_code == 0:
            # end action
            self.set_state(DevState.ON)
            with self.active_controlKey_action_lock:
                self.active_controlKey_action = None
        elif command_code == 2:
            # update beat time
            if self.active_controlKey_action is not None:
                self.active_controlKey_action.heartbeat("motor_CW")

    @command(dtype_in=int)
    def controlKey_motor_CW_fast(self, command_code):
        def move_one_chunk():
            ManipulatorMotor.move(True, self.speed_fast, self.movement_chunk_duration_ms/1000.0)

        if command_code == 1:
            # start action
            self.set_state(DevState.MOVING)
            with self.active_controlKey_action_lock:
                self.active_controlKey_action = ControlKeyAction("motor_CW_fast",
                                                                 move_one_chunk, self.max_heartbeat_distance_ms)
        elif command_code == 0:
            # end action
            self.set_state(DevState.ON)
            with self.active_controlKey_action_lock:
                self.active_controlKey_action = None
        elif command_code == 2:
            # update beat time
            if self.active_controlKey_action is not None:
                self.active_controlKey_action.heartbeat("motor_CW_fast")

    @command(dtype_in=int)
    def controlKey_motor_CCW(self, command_code):
        def move_one_chunk():
            ManipulatorMotor.move(False, self.speed, self.movement_chunk_duration_ms/1000.0)

        if command_code == 1:
            # start action
            self.set_state(DevState.MOVING)
            with self.active_controlKey_action_lock:
                self.active_controlKey_action = ControlKeyAction("motor_CCW",
                                                                 move_one_chunk, self.max_heartbeat_distance_ms)
        elif command_code == 0:
            # end action
            self.set_state(DevState.ON)
            with self.active_controlKey_action_lock:
                self.active_controlKey_action = None
        elif command_code == 2:
            # update beat time
            if self.active_controlKey_action is not None:
                self.active_controlKey_action.heartbeat("motor_CCW")

    @command(dtype_in=int)
    def controlKey_motor_CCW_fast(self, command_code):
        def move_one_chunk():
            ManipulatorMotor.move(False, self.speed_fast, self.movement_chunk_duration_ms/1000.0)

        if command_code == 1:
            # start action
            self.set_state(DevState.MOVING)
            with self.active_controlKey_action_lock:
                self.active_controlKey_action = ControlKeyAction("motor_CCW_fast",
                                                                 move_one_chunk, self.max_heartbeat_distance_ms)
        elif command_code == 0:
            # end action
            self.set_state(DevState.ON)
            with self.active_controlKey_action_lock:
                self.active_controlKey_action = None
        elif command_code == 2:
            # update beat time
            if self.active_controlKey_action is not None:
                self.active_controlKey_action.heartbeat("motor_CCW_fast")


class ControlKeyAction:
    def __init__(self, name, chunk_method, max_heartbeat_distance_ms):
        self.name = name
        self.act = chunk_method  # provides one short (not dividable) chunk of the continuous action
        self.max_heartbeat_distance = max_heartbeat_distance_ms/1000.0
        self.last_heartbeat = time.time()
        self.action_alive = True

    def heartbeat(self, name):
        if name == self.name:
            self.last_heartbeat = time.time()

    def execute_next_chunk(self):
        """should repeatedly be called to get somewhat continuous motion. use return value to delete action"""
        if self.action_alive and time.time() - self.last_heartbeat < self.max_heartbeat_distance:
            self.act()
            return True
        else:
            if not self.action_alive:
                print("ERROR: tried to continue dead action")
                self.action_alive = False
            return False


if __name__ == "__main__":
    run([ManipulatorMotorTANGO])
