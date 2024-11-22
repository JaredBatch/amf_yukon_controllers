# This file runs at power-up. It and files in the /lib directory get added to a LittleFS filesystem and appended to the firmware
# Overide this file with any of your own code that you wish to run at power-up, or remove the file to not have anything run.

## GANTRY ##

import time
import machine
import uselect
import sys
from utime import ticks_ms, ticks_add
from pimoroni_yukon import Yukon
from breakout_ioexpander import BreakoutIOExpander

from mods.motors import GantryMotor, FilamentDriveServo, FilamentLockServo, FilamentBlindDriveMotor

from pimoroni_yukon import SLOT1 as SLOT_STEPPER1
from pimoroni_yukon import SLOT2 as SLOT_STEPPER2
from pimoroni_yukon import SLOT3 as SLOT_SERVO1
from pimoroni_yukon import SLOT5 as SLOT_DC5

from pimoroni_yukon.modules import QuadServoRegModule as QuadServoModule
from pimoroni_yukon.modules import QuadServoDirectModule as QuadServoDirectModule
from pimoroni_yukon.modules import BigMotorModule
from pimoroni_yukon.modules import DualMotorModule

allow_unregistered=True

# Create a Yukon object to begin using the board
yukon = Yukon()
module1 = DualMotorModule()
module2 = DualMotorModule()
module3 = QuadServoModule()
module5 = BigMotorModule()


yukon.register_with_slot(module1, SLOT_STEPPER1)      # Register the DualMotorModule object with the slot
yukon.register_with_slot(module2, SLOT_STEPPER2)      # Register the DualMotorModule object with the slot
yukon.register_with_slot(module3, SLOT_SERVO1)      # Register the DualMotorModule object with the slot
yukon.register_with_slot(module5, SLOT_DC5)      # Register the BigMotorModule object with the slot          

yukon.verify_and_initialise()               # Verify that a DualMotorModule is attached to Yukon, and initialise it
yukon.enable_main_output()                  # Turn on power to the module slots

ADDRESS = 0x18
io = BreakoutIOExpander(yukon.i2c, ADDRESS)
halleffect = 3
home_left = 4
home_right = 5
guide_sensor = 6
filament_input_sensor = 7
filament_lock_sensor = 8

io.set_mode(halleffect, io.PIN_IN_PU)
io.set_mode(home_right, io.PIN_IN_PU)
io.set_mode(home_left, io.PIN_IN_PU)
io.set_mode(guide_sensor, io.PIN_IN_PU)
io.set_mode(filament_input_sensor, io.PIN_IN_PU)
io.set_mode(filament_lock_sensor, io.PIN_IN_PU)


gantryStepper1 = GantryMotor(module1)
gantryStepper1.initialise()

gantryFilamentStepper = FilamentBlindDriveMotor(module2)
gantryFilamentStepper.initialise()

gantrydriveStepperEngage = -42
gantrydriveStepperDisengage = -15
gantrydriveServo_slot = "servo2"
gantrydriveServo = FilamentDriveServo(module3, gantrydriveServo_slot)
gantrydriveServo.initialise()

lockEngage = 17.5
lockDisengage = 30
lockServo_slot = "servo4"
lockServo = FilamentLockServo(module3, lockServo_slot)
lockServo.initialise()

#module5.enable()   


def check_inputs():
    inputs_state = {
        "halleffect": io.input(halleffect),
        "home_right": io.input(home_right),
        "home_left": io.input(home_left),
        "guide_sensor": io.input(guide_sensor),
        "filament_input_sensor": 1 - io.input(filament_input_sensor),
        "filament_lock_sensor": 1 - io.input(filament_lock_sensor),
    }
    return inputs_state

def get_input_state(input_name):
    input_states = check_inputs()  # Get the current states
    return input_states.get(input_name, None)#

def check_intake():
    input_states = check_inputs()  # Get the current states
    if input_states.get("filament_input_sensor", None):
        print("Locked and Loaded")
        
def check_output():
    input_states = check_inputs()  # Get the current states
    if not input_states.get("filament_input_sensor", None):
        print("Slow down!")

def home():
    lockServo.disengage(lockDisengage)
    gantrydriveServo.disengage(gantrydriveStepperDisengage)
    yukon.monitored_sleep(1)
    gantryStepper1.home("right", lambda: io.input(home_right))
    yukon.monitored_sleep(0.5)
    print("Home Success")
    
def move_left(steps):
    gantryStepper1.move_to_position(gantryStepper1.current_position + steps, lambda: io.input(halleffect), lambda: io.input(home_right), lambda: io.input(home_left))
    print("Movement Successful")

def move_right(steps):
    gantryStepper1.move_to_position(gantryStepper1.current_position - steps, lambda: io.input(halleffect), lambda: io.input(home_right), lambda: io.input(home_left))
    print("Movement Successful")

def starting_state():
    lockServo.disengage(lockDisengage)
    yukon.monitored_sleep(1)
    gantrydriveServo.disengage(gantrydriveStepperDisengage)
    yukon.monitored_sleep(1)
    lockstate = 0

    gantryStepper1.home("right", lambda: io.input(home_right))
    yukon.monitored_sleep(0.5)
    
    yukon.monitored_sleep(1)

def intake_filament():
    if get_input_state("halleffect") and get_input_state("filament_input_sensor") and get_input_state("guide_sensor"):
        gantrydriveServo.engage(gantrydriveStepperEngage)
        yukon.monitored_sleep(0.1)
        lockServo.disengage(lockDisengage)
        while not get_input_state("filament_lock_sensor"):
            gantryFilamentStepper.extrude_while()
        yukon.monitored_sleep(0.1)
        if get_input_state("filament_lock_sensor"):
            gantryFilamentStepper.stop()
            print("Creep a bit more into the lock")
            yukon.monitored_sleep(1)
            gantryFilamentStepper.extrude_filament_blind(25, 5)
            lockServo.engage(lockEngage)
            yukon.monitored_sleep(1)
            gantrydriveServo.disengage(gantrydriveStepperDisengage)
            yukon.monitored_sleep(0.1)
            print("Intake successful.")
        else:
            print("Loading failed")
            gantrydriveServo.disengage(gantrydriveStepperDisengage)
    else:
        print("Conditions not met to intake filament")
        print(get_input_state("home_right"))
        print(get_input_state("filament_input_sensor"))
        print(get_input_state("guide_sensor"))
        
        
def initial_spool(load_time):
    start_time = ticks_ms()  # Start time in milliseconds
    
    gantrydriveServo.engage(gantrydriveStepperEngage)
    gantrydriveServo.engage(gantrydriveStepperEngage+10)
    
    lockServo.engage(lockEngage-1)
    
    gantryFilamentStepper.extrude_while_fast()
    yukon.monitored_sleep(0.1)
    module5.enable() 
    module5.motor.speed(0.05)
    
    elapsed_time = (ticks_ms() - start_time) / 1000.0
    
    while elapsed_time < load_time:
        elapsed_time = (ticks_ms() - start_time) / 1000.0
        yukon.monitored_sleep(0.1)
        print(elapsed_time)
    module5.motor.speed(0)
    gantryFilamentStepper.stop()
    gantrydriveServo.disengage(gantrydriveStepperDisengage)        
    yukon.monitored_sleep(0.1)
    
        
def spool_up(time, speed):
    # Divide the total time equally among the three phases
    RAMP_UP_TIME = 5
    FULL_SPEED_TIME = time
    RAMP_DOWN_TIME = 5

    SPEED_EXTENT = speed                     # The maximum speed to ramp to
    UPDATES = 20                            # How many times to update the motors per second
    
    lockServo.engage(lockEngage)
    module5.enable()
    
    initial_spool(30)  # Load up spool
    
    lockServo.engage(lockEngage)
    
    # Initialize variables
    start_time = ticks_ms()  # Start time in milliseconds
    current_time = start_time
    unlock = False           # Status flag for unlocking
    lockDisengage = True     # Placeholder for lock disengage action

    while True:
        # Calculate elapsed time in seconds
        elapsed_time = (ticks_ms() - start_time) / 1000.0

        if elapsed_time <= RAMP_UP_TIME:
            print("**Ramp Up Phase**")
            # Increase speed proportionally over RAMP_UP_TIME
            speed = (elapsed_time / RAMP_UP_TIME) * SPEED_EXTENT
        elif elapsed_time <= RAMP_UP_TIME + FULL_SPEED_TIME:
            print("**Full Speed Phase**")
            speed = SPEED_EXTENT  # Maintain full speed
        elif elapsed_time <= RAMP_UP_TIME + FULL_SPEED_TIME + RAMP_DOWN_TIME:
            print("**Ramp Down Phase**")
            if not unlock:
                lockServo.disengage(lockDisengage)  # Disengage the lock
                unlock = True  # Ensure this happens only once
            remaining_time = (RAMP_UP_TIME + FULL_SPEED_TIME + RAMP_DOWN_TIME) - elapsed_time
            speed = (remaining_time / RAMP_DOWN_TIME) * SPEED_EXTENT  # Decrease speed proportionally
        else:
            # **Completion**
            speed = 0  # Stop the motor
            module5.motor.speed(speed)  # Apply the stop command
            module5.disable()
            yukon.monitored_sleep(0.1)
            lockServo.disengage(lockDisengage)
            gantrydriveServo.engage(gantrydriveStepperEngage)
            yukon.monitored_sleep(0.1)
            print("Spool successful.")
            break  # Exit the loop

        # Apply the calculated speed to the motor
        module5.motor.speed(speed)

        # Advance the current time by a number of milliseconds
        current_time = ticks_add(current_time, int(1000 / UPDATES))

        # Monitor sensors until the current time is reached
        yukon.monitor_until_ms(current_time)
        
def spool_up_until(speed):
    # Constants
    RAMP_UP_TIME = 5
    RAMP_DOWN_TIME = 5
    SPEED_EXTENT = speed  # Maximum speed to ramp to
    UPDATES = 20       # Updates per second
    
    lockServo.engage(lockEngage)
    module5.enable()
    
    initial_spool()  # Load up spool
    
    # Initialize variables
    start_time = ticks_ms()  # Start time in milliseconds
    current_time = start_time
    unlock = False           # Status flag for unlocking
    lockDisengage = True     # Placeholder for lock disengage action

    # Set up input polling
    poller = uselect.poll()
    poller.register(sys.stdin, uselect.POLLIN)

    # Ramp-up phase
    while (ticks_ms() - start_time) / 1000.0 <= RAMP_UP_TIME:
        elapsed_time = (ticks_ms() - start_time) / 1000.0
        speed = (elapsed_time / RAMP_UP_TIME) * SPEED_EXTENT
        module5.motor.speed(speed)

    # Maintain full speed until stop command is received
    print("**Full Speed Phase**")
    module5.motor.speed(SPEED_EXTENT)

    try:
        while True:
            # Check for input without blocking
            events = poller.poll(0)
            if events:
                command = sys.stdin.readline().strip()
                if command.lower() == "stop":
                    break  # Exit to start the ramp-down

    finally:
        # Ramp-down phase
        print("**Ramp Down Phase**")
        start_time = ticks_ms()
        while (ticks_ms() - start_time) / 1000.0 <= RAMP_DOWN_TIME:
            if not unlock:
                lockServo.disengage(lockDisengage)  # Disengage the lock
                unlock = True
            elapsed_time = (ticks_ms() - start_time) / 1000.0
            remaining_time = RAMP_DOWN_TIME - elapsed_time
            speed = (remaining_time / RAMP_DOWN_TIME) * SPEED_EXTENT
            module5.motor.speed(speed)

        # Stop the motor and disable
        module5.motor.speed(0)
        module5.disable()
        yukon.monitored_sleep(0.1)
        gantrydriveServo.engage(gantrydriveStepperEngage)
        yukon.monitored_sleep(0.1)
        print("Spool successful.")


def retreiveFilament():
    gantrydriveServo.engage(gantrydriveStepperEngage)
    module5.enable() 
    module5.motor.speed(0.2)
    while get_input_state("filament_input_sensor"):
            gantryFilamentStepper.extrude_while()
    module5.disable()
    while not get_input_state("filament_input_sensor"):
            gantryFilamentStepper.extrude_while(-1)
    print("Filament retrieved.")


def deliverFilament(length=25):
    gantrydriveServo.engage(gantrydriveStepperEngage)
    module5.enable() 
    module5.motor.speed(0.2)
    gantryFilamentStepper.extrude_filament_blind(-length, length/5)
    module5.disable()
    print("Filament delivered successfully.")
    gantrydriveServo.disengage(gantrydriveStepperDisengage)
    
def deliverFilamentUntil():
    #print("Prime to begin output")
    yukon.monitored_sleep(0.5)
    gantrydriveServo.engage(gantrydriveStepperEngage)
    yukon.monitored_sleep(0.5)
    print("Filament delivery started")

    poller = uselect.poll()
    poller.register(sys.stdin, uselect.POLLIN)
    gantryFilamentStepper.extrude_while(-1)  

    try:
        while True:
            # This is where the stepper continuously extrudes
            # Check for input without blocking
            events = poller.poll(0)
            if events:
                command = sys.stdin.readline().strip()
                if command.lower() == "stop":
                    gantryFilamentStepper.stop()
                    #print("Delivery interrupted by REPL command")
                    break
    finally:
        gantrydriveServo.disengage(gantrydriveStepperDisengage)
        print("Filament delivery stopped")

def homeFilament():
    gantrydriveServo.engage(gantrydriveStepperEngage)
    if get_input_state("filament_input_sensor"):
        retreiveFilament()
    else:
        while not get_input_state("filament_input_sensor"):
            gantryFilamentStepper.extrude_while(-1)
            
def unspoolTension():
    module5.enable()
    gantrydriveServo.disengage(gantrydriveStepperDisengage)
    print("Tension off.")
    input_states = check_inputs()
    print(input_states.get("filament_input_sensor", None))
    while input_states.get("filament_input_sensor", None):
        module5.motor.speed(-0.2)
        input_states = check_inputs()
    print("Filament off spool.")
    speed = 0  # Stop the motor
    module5.motor.speed(speed)  # Apply the stop command
    module5.disable()
    yukon.monitored_sleep(0.5)













