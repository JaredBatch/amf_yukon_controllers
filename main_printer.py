# This file runs at power-up. It and files in the /lib directory get added to a LittleFS filesystem and appended to the firmware
# Overide this file with any of your own code that you wish to run at power-up, or remove the file to not have anything run.

## PRINTER ##

import time
import uselect
import sys
from utime import ticks_ms, ticks_add
from pimoroni_yukon import Yukon
from breakout_ioexpander import BreakoutIOExpander

from mods.motors import FilamentDriveServo, FilamentLockServo, FilamentBlindDriveMotor, dockingServo

from pimoroni_yukon import SLOT1 as SLOT_DC1
from pimoroni_yukon import SLOT2 as SLOT_STEPPER1
from pimoroni_yukon import SLOT3 as SLOT_SERVO1

from pimoroni_yukon.modules import BigMotorModule
from pimoroni_yukon.modules import DualMotorModule
from pimoroni_yukon.modules import QuadServoRegModule as QuadServoModule


# Create a Yukon object to begin using the board
yukon = Yukon()
module1 = BigMotorModule()
module2 = DualMotorModule()
module3 = QuadServoModule()


yukon.register_with_slot(module1, SLOT_DC1)      # Register the DualMotorModule object with the slot
yukon.register_with_slot(module2, SLOT_STEPPER1)      # Register the DualMotorModule object with the slot
yukon.register_with_slot(module3, SLOT_SERVO1)      # Register the DualMotorModule object with the slot         

yukon.verify_and_initialise()               # Verify that a DualMotorModule is attached to Yukon, and initialise it
yukon.enable_main_output()                  # Turn on power to the module slots

module1.enable()  

ADDRESS = 0x18
io = BreakoutIOExpander(yukon.i2c, ADDRESS)

intake_sensor = 3
guide_sensor = 4
filament_lock_sensor = 5

power_fls_sensor = 1

io.set_mode(intake_sensor, io.PIN_IN_PU)
io.set_mode(guide_sensor, io.PIN_IN_PU)
io.set_mode(filament_lock_sensor, io.PIN_IN_PU)
io.set_mode(power_fls_sensor, io.PIN_OUT)

io.output(power_fls_sensor, 1)

printerFilamentStepper = FilamentBlindDriveMotor(module2)
printerFilamentStepper.initialise()
 
inputEngage = -9
inputDisengage = -37
inputServo_slot = "servo1"
inputServo = dockingServo(module3, inputServo_slot)
inputServo.initialise()

printerdriveStepperEngage = 5
printerdriveStepperDisengage = 37
printerdriveServo_slot = "servo2"
printerdriveServo = FilamentDriveServo(module3, printerdriveServo_slot)
printerdriveServo.initialise()

lockEngage = 12
lockEngage_strong = 5
lockDisengage = 28
lockServo_slot = "servo3"
lockServo = FilamentLockServo(module3, lockServo_slot)
lockServo.initialise()


def check_inputs():
    inputs_state = {
        "intake_sensor": not io.input(intake_sensor),
        "guide_sensor": bool(io.input(guide_sensor)),
        "filament_lock_sensor": not io.input(filament_lock_sensor),
    }
    return inputs_state

def get_input_state(input_name):
    input_states = check_inputs()  # Get the current states
    return input_states.get(input_name, None)

def check_intake():
    input_states = check_inputs()  # Get the current states
    if input_states.get("intake_sensor", None):
        print("Sensor triggered")

def wait_for_intake(sensor=intake_sensor, timeout=60):
    start_time = time.time()
    lockServo.disengage(lockDisengage)
    printerdriveServo.disengage(printerdriveStepperDisengage)
    while time.time() - start_time < timeout:
        if get_input_state(sensor) == True:
            print("Sensor triggered")
            return True
        time.sleep(0.1)  # Small delay to avoid busy waiting
    return False
    

def dock():
    inputServo.engage(inputEngage)
    yukon.monitored_sleep(0.5)
    print("Dock successful.")
    
def undock():
    inputServo.disengage(inputDisengage)
    yukon.monitored_sleep(0.5)
    print("Undock successful.")


def spool_up(time, max_speed = 1):
    # Divide the total time equally among the three phases
    RAMP_UP_TIME = 10
    FULL_SPEED_TIME = time
    RAMP_DOWN_TIME = 5
    
    if max_speed > 1:
        max_speed = 1
    SPEED_EXTENT = -max_speed               # The maximum speed to ramp to, reversed
    UPDATES = 20                            # How many times to update the motors per second

    # Initialize variables
    start_time = ticks_ms()  # Start time in milliseconds
    current_time = start_time
    lockServo.engage(lockEngage_strong)
    time.sleep(0.5)
    printerdriveServo.disengage(printerdriveStepperDisengage)
    time.sleep(1)
    unlock = False           # Status flag for unlocking
    while True:
        # Check the sensor state and stop if the sensor is low
        if get_input_state("intake_sensor") == 0:
            # **Early exit due to sensor trigger**
            speed = 0  # Stop the motor
            module1.motor.speed(speed)  # Apply the stop command
            lockServo.disengage(lockDisengage)  # Disengage the lock
            break  # Exit the loop

        # Calculate elapsed time in seconds
        elapsed_time = (ticks_ms() - start_time) / 1000.0
        
        if elapsed_time <= RAMP_UP_TIME:
            # Increase speed proportionally over RAMP_UP_TIME
            speed = (elapsed_time / RAMP_UP_TIME) * SPEED_EXTENT
        elif elapsed_time <= RAMP_UP_TIME + FULL_SPEED_TIME:
            speed = SPEED_EXTENT  # Maintain full speed
        elif elapsed_time <= RAMP_UP_TIME + FULL_SPEED_TIME + RAMP_DOWN_TIME:
            remaining_time = (RAMP_UP_TIME + FULL_SPEED_TIME + RAMP_DOWN_TIME) - elapsed_time
            speed = (remaining_time / RAMP_DOWN_TIME) * SPEED_EXTENT  # Decrease speed proportionally
        else:
            # **Completion**
            speed = 0  # Stop the motor
            module1.motor.speed(speed)  # Apply the stop command
            lockServo.disengage(lockDisengage)  # Disengage the lock
            print("Spool up complete.")
            break  # Exit the loop

        # Apply the calculated speed to the motor
        module1.motor.speed(speed)

        # Advance the current time by a number of milliseconds
        current_time = ticks_add(current_time, int(1000 / UPDATES))

        # Monitor sensors until the current time is reached
        yukon.monitor_until_ms(current_time)
        
def spool_up_until(max_speed = 1):
    # Constants
    RAMP_UP_TIME = 5
    RAMP_DOWN_TIME = 5
    if max_speed > 1:
        max_speed = 1
    SPEED_EXTENT = -max_speed  # Maximum speed to ramp to
    UPDATES = 20       # Updates per second

    lockServo.engage(lockEngage_strong)
    time.sleep(0.5)
    printerdriveServo.disengage(printerdriveStepperDisengage)
    time.sleep(1)

    # Initialize variables
    start_time = ticks_ms()  # Start time in milliseconds
    current_time = start_time

    # Set up input polling
    poller = uselect.poll()
    poller.register(sys.stdin, uselect.POLLIN)

    # Ramp-up phase
    while True:
        # Calculate elapsed time
        elapsed_time = (ticks_ms() - start_time) / 1000.0

        if elapsed_time <= RAMP_UP_TIME:
            # Increase speed proportionally over RAMP_UP_TIME
            speed = (elapsed_time / RAMP_UP_TIME) * SPEED_EXTENT
            print("RAMP UP")
        else:
            break  # Exit ramp-up phase

        # Apply the calculated speed to the motor
        module1.motor.speed(speed)

        # Advance the current time by a number of milliseconds
        current_time = ticks_add(current_time, int(1000 / UPDATES))

        # Wait until the next update time
        yukon.monitor_until_ms(current_time)

    # Maintain full speed until stop command is received
    print("**Full Speed Phase**")
    module1.motor.speed(SPEED_EXTENT)

    try:
        while True:
            # Check for input without blocking
            events = poller.poll(0)
            if events:
                command = sys.stdin.readline().strip()
                if command.lower() == "stop":
                    break  # Exit to start the ramp down

            # Include a small delay to prevent CPU overload
            time.sleep(0.05)

    finally:
        # Ramp-down phase
        print("**RAMP DOWN**")
        start_down_time = ticks_ms()
        current_time = start_down_time
        while True:
            # Calculate elapsed time for ramp down
            elapsed_down_time = (ticks_ms() - start_down_time) / 1000.0
            if elapsed_down_time <= RAMP_DOWN_TIME:
                remaining_time = RAMP_DOWN_TIME - elapsed_down_time
                speed = (remaining_time / RAMP_DOWN_TIME) * SPEED_EXTENT
                module1.motor.speed(speed)
                print("RAMP DOWN", elapsed_down_time, speed)
            else:
                break  # Exit ramp-down phase

            # Advance the current time
            current_time = ticks_add(current_time, int(1000 / UPDATES))
            yukon.monitor_until_ms(current_time)

        # Stop the motor
        module1.motor.speed(0)
        lockServo.disengage(lockDisengage)
        print("Spool operation complete.")


        
def intake_filament():
    if get_input_state("intake_sensor") and get_input_state("guide_sensor"):
        printerdriveServo.engage(printerdriveStepperEngage)
        yukon.monitored_sleep(0.1)
        lockServo.disengage(lockDisengage)
        yukon.monitored_sleep(0.1)
        while not get_input_state("filament_lock_sensor"):
            #printerFilamentStepper.extrude_while()
            printerFilamentStepper.extrude_filament_blind(5, 1)
        yukon.monitored_sleep(0.1)
        if get_input_state("filament_lock_sensor"):
            printerFilamentStepper.stop()
            print("Creep a bit more into the lock")
            yukon.monitored_sleep(1)
            printerFilamentStepper.extrude_filament_blind(40, 5)
            lockServo.engage(lockEngage)
            yukon.monitored_sleep(1)
            printerdriveServo.disengage(printerdriveStepperDisengage)
            print("Intake complete.")
            yukon.monitored_sleep(0.1)
        else:
            print("Loading failed")
            printerdriveServo.disengage(printerdriveStepperDisengage0)
    else:
        print("Conditions not met to intake filament")
        print(get_input_state("filament_input_sensor"))
        print(get_input_state("guide_sensor"))




