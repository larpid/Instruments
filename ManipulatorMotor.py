"""this script implements movement functionalities for our manipulator (currently only the main motor)
written by Lars Pidde, 01/2020"""

import atexit
import RPi.GPIO as GPIO
import time


class ManipulatorMotor:

    # setup GPIO pins
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(26, GPIO.OUT)  # Pulse input. signal triggered on rising edge. pulse length should be >= 0.4us.
                              # rising edge distance should be at least 1us
    GPIO.setup(6, GPIO.OUT)  # rotation direction
    GPIO.setup(13, GPIO.OUT)  # turns all windings off (no movement or holding torque)
    GPIO.setup(19, GPIO.OUT)  # step angle: ON means basic, OFF means set by driver switch
    atexit.register(lambda: GPIO.cleanup())

    # idle GPIO setting:
    GPIO.output(26, GPIO.LOW)
    GPIO.output(6, GPIO.LOW)
    GPIO.output(13, GPIO.HIGH)  # leaving it off would make the motor get very hot
    GPIO.output(19, GPIO.LOW)

    @staticmethod
    def move(direction_is_cw, pulse_frequency, duration):
        """this is a blocking function. it should therefore be called repeatedly with short durations"""

        pulse_distance = (1.0/pulse_frequency)

        # turn windings on
        GPIO.output(13, GPIO.LOW)

        # set rotation direction
        if direction_is_cw:
            GPIO.output(6, GPIO.HIGH)
        else:
            GPIO.output(6, GPIO.LOW)

        start_movement_time = time.time()
        while time.time() - start_movement_time < duration:
            GPIO.output(26, GPIO.HIGH)
            time.sleep(.000001)
            GPIO.output(26, GPIO.LOW)
            time.sleep(pulse_distance - .000001)

        # turn windings off again
        GPIO.output(13, GPIO.HIGH)

    class PulseRotationMode:
        """context manager to handle the wiring turn off and direction pin"""

        def __init__(self, direction_is_cw):
            # set rotation direction
            if direction_is_cw:
                GPIO.output(6, GPIO.HIGH)
            else:
                GPIO.output(6, GPIO.LOW)

        def __enter__(self):
            # turn windings on
            GPIO.output(13, GPIO.LOW)
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            # turn windings off
            GPIO.output(13, GPIO.HIGH)

        @staticmethod
        def move_one_step():
            """timing managed by caller"""

            GPIO.output(26, GPIO.HIGH)
            time.sleep(.000001)
            GPIO.output(26, GPIO.LOW)
            time.sleep(.000001)  # guarantees a minimum pulse distance (not necessarily needed)


if __name__ == "__main__":
    """test code"""
    import sys
    print("this test usage calls ManipulatorMotor.move(True, pulse_frequency, duration)")
    if len(sys.argv) == 3:
        sys.argv[1] = float(sys.argv[1])
        sys.argv[2] = float(sys.argv[2])
        ManipulatorMotor.move(*sys.argv)
    else:
        print("test usage needs pulse_frequency and duration. e.g.: \"python3 ManipulatorMotor.py 500 1\"")
