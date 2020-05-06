"""Tango server for the implementation of the main movement functionality for our manipulator
(currently only the main motor)

do not create multiple device instances from one server process/ on the same PI. this would not only make no sense,
but could also grant unforeseen consequences
written by Lars Pidde, 01/2020"""

from ManipulatorMotor import ManipulatorMotor
import sys
import time
import threading
import queue
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
        print("starting device server instance")
        self.get_device_properties()  # without this all device properties are None
        self.active_controlKey_action = None
        self.active_controlKey_action_lock = threading.Lock()
        self.device_stop_requested = threading.Event()
        self.next_action_queue = queue.Queue()
        self.next_chunk_ready = threading.Event()
        self.chunk_start_thread = threading.Thread(target=self.chunk_start_thread_method, daemon=True)
        self.pulse_thread = threading.Thread(target=self.pulse_thread_method, daemon=True)
        self.chunk_start_thread.start()
        self.pulse_thread.start()
        self.set_state(DevState.ON)

    def delete_device(self):
        print("stopping device server instance")
        self.device_stop_requested.set()
        self.chunk_start_thread.join()
        self.pulse_thread.join()
        print("all clear")

    def chunk_start_thread_method(self):
        print("chunk start thread started")
        while not self.device_stop_requested.is_set():

            # prepare new action
            action_exists = False
            with self.active_controlKey_action_lock:
                if self.active_controlKey_action is not None:
                    direction_is_cw = self.active_controlKey_action.direction_is_cw
                    pulse_distance = 1.0 / self.active_controlKey_action.pulse_frequency
                    action_exists = True

            # routinely execute action in movement mode
            if action_exists:
                if self.next_action_queue.empty():
                    self.next_chunk_ready.set()
                    self.next_action_queue.put([direction_is_cw, pulse_distance])

                    while action_exists:
                        # check for a next chunk
                        next_chunk_ready = False
                        with self.active_controlKey_action_lock:
                            if self.active_controlKey_action is None:
                                action_exists = False
                            else:
                                if self.active_controlKey_action.next_chunk_ready():
                                    self.next_chunk_ready.set()
                                else:
                                    self.active_controlKey_action = None
                                    action_exists = False
                    else:
                        self.next_chunk_ready.clear()

        print("chunk start thread terminated")

    def pulse_thread_method(self):
        print("pulse thread started")
        while not self.device_stop_requested.is_set():
            direction_is_cw = None
            direction_is_cw, pulse_distance = self.next_action_queue.get(timeout=.01)

            if direction_is_cw is not None:
                chunk_duration = self.movement_chunk_duration_ms / 1000.0
                with ManipulatorMotor.PulseRotationMode(direction_is_cw) as prm:
                    while self.next_chunk_ready.is_set():
                        self.next_chunk_ready.clear()
                        chunk_start_time = time.time()
                        next_pulse_time = chunk_start_time
                        while next_pulse_time - chunk_start_time < chunk_duration:
                            current_time = time.time()
                            if current_time < next_pulse_time:
                                time.sleep(next_pulse_time - current_time)
                            prm.move_one_step()
                            next_pulse_time = current_time + pulse_distance - 0.000002

        print("pulse thread terminated")

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
            self.get_device_properties()
            with self.active_controlKey_action_lock:
                self.active_controlKey_action = ControlKeyAction("motor_CW", True, self.speed,
                                                                 self.max_heartbeat_distance_ms/1000.0)
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
        if command_code == 1:
            # start action
            self.set_state(DevState.MOVING)
            self.get_device_properties()
            with self.active_controlKey_action_lock:
                self.active_controlKey_action = ControlKeyAction("motor_CW_fast", True, self.speed_fast,
                                                                 self.max_heartbeat_distance_ms/1000.0)
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
        if command_code == 1:
            # start action
            self.set_state(DevState.MOVING)
            self.get_device_properties()
            with self.active_controlKey_action_lock:
                self.active_controlKey_action = ControlKeyAction("motor_CCW", False, self.speed,
                                                                 self.max_heartbeat_distance_ms/1000.0)
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
        if command_code == 1:
            # start action
            self.set_state(DevState.MOVING)
            self.get_device_properties()
            with self.active_controlKey_action_lock:
                self.active_controlKey_action = ControlKeyAction("motor_CCW_fast", False, self.speed_fast,
                                                                 self.max_heartbeat_distance_ms/1000.0)
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
    def __init__(self, name, direction_is_cw, pulse_frequency, max_heartbeat_distance):
        self._name = name
        self.direction_is_cw = direction_is_cw
        self.pulse_frequency = pulse_frequency
        self._max_heartbeat_distance = max_heartbeat_distance
        self._last_heartbeat = time.time()
        self._action_alive = True

    def heartbeat(self, name):
        if name == self._name:
            self._last_heartbeat = time.time()

    def next_chunk_ready(self):
        """permits execution of next chunk. action should be deleted if False returned"""
        if self._action_alive and time.time() - self._last_heartbeat < self._max_heartbeat_distance:
            return True
        else:
            if not self._action_alive:
                print("ERROR: tried to continue dead action")
                self._action_alive = False
            return False


if __name__ == "__main__":
    run([ManipulatorMotorTANGO])
