# This file runs at power-up. It and files in the /lib directory get added to a LittleFS filesystem and appended to the firmware
# Overide this file with any of your own code that you wish to run at power-up, or remove the file to not have anything run.

### STORAGE ###

class StepperServoSet:
    def __init__(self, motor_module, servo_module, stepper_slot, servo_slot, filament_counter, io, driveStepperEngage=-83, driveStepperDisengage=-20):
        # motor_module: The motor module used to control the stepper motor.
        # servo_module: The servo module used to control the servo.
        # stepper_slot: The slot in which the stepper motor is connected.
        # servo_slot: The slot in which the servo motor is connected.
        # filament_counter: The counter used to measure the filament movement.
        # io: The IO expander used for interfacing with external devices.
        # driveStepperEngage: Default position value to engage the stepper motor.
        # driveStepperDisengage: Default position value to disengage the stepper motor.
        # Initialize the stepper motor
        self.stepper = FilamentDriveMotor(motor_module, filament_counter, io)
        self.stepper.initialise()

        # Store engage and disengage positions for driveStepper
        self.driveStepperEngage = driveStepperEngage
        self.driveStepperDisengage = driveStepperDisengage

        # Initialize the drive servo
        self.driveServo = FilamentDriveServo(servo_module, servo_slot)
        self.driveServo.initialise()

    def engage_drive_servo(self):
        self.driveServo.engage(self.driveStepperEngage)

    def disengage_drive_servo(self):
        self.driveServo.disengage(self.driveStepperDisengage)

    def extrude_filament(self, amount):
        self.engage_drive_servo()
        self.stepper.extrude_length(amount)
        self.disengage_drive_servo()

    def extrude_filament_until(self):
        self.engage_drive_servo()
        self.stepper.extrude_while()

    def deliver_filament(self, amount):
        self.engage_drive_servo()
        self.stepper.extrude_length(amount)
        self.disengage_drive_servo()
        print("Filament delivery successful.")

    def deliver_filament_until(self):
        self.engage_drive_servo()
        self.stepper.extrude_while()
        print("Filament delivery started")

        poller = uselect.poll()
        poller.register(sys.stdin, uselect.POLLIN)
        try:
            is_running = True
            while is_running:
                # Run extrude_while continuously
                # Check for input without blocking
                events = poller.poll(0)  # 0 timeout means non-blocking
                if events:
                    command = sys.stdin.readline().strip()
                    if command.lower() == "stop":
                        self.stepper.stop()
                        is_running = False
                        break
        finally:
            self.disengage_drive_servo()
            print("Filament delivery stopped")

    def little_push(self):
        self.engage_drive_servo()
        self.stepper.extrude_filament_blind(50, 5)
        self.stepper.extrude_filament_blind(-50, 5)
        self.disengage_drive_servo()
        print("Little push successful.")
        
    def pull_out(self):
        self.engage_drive_servo()
        self.stepper.extrude_filament_blind(-500, 50)
        self.disengage_drive_servo()
        print("Pull out successful.")

def dock():
    outputServo.engage(outputEngage)
    yukon.monitored_sleep(0.5)
    print("Dock successful.")
    
def undock():
    outputServo.disengage(outputDisengage)
    yukon.monitored_sleep(0.5)
    print("Undock successful.")
    
def cutFilament():
    #print("Cut filament")
    cutterServo.engage(cutterEngage)
    yukon.monitored_sleep(0.5) #Let it rest before taking values
    cutterServo.disengage(cutterDisengage)
    yukon.monitored_sleep(0.5) #Let it rest before taking values
    print("Filament cutting successful.")


import time
import machine
import sys
import uselect
from pimoroni_yukon import Yukon
from breakout_ioexpander import BreakoutIOExpander

from mods.sensors import FilamentCounter 
from mods.motors import FilamentDriveMotor, FilamentDriveServo

from pimoroni_yukon import SLOT1 as SLOT_SERVO1
from pimoroni_yukon import SLOT2 as SLOT_STEPPER1
from pimoroni_yukon import SLOT6 as SLOT_STEPPER2

from pimoroni_yukon.modules import QuadServoRegModule as QuadServoModule
from pimoroni_yukon.modules import DualMotorModule

# Create a Yukon object to begin using the board
yukon = Yukon()
module1 = DualMotorModule()
module2 = QuadServoModule()
module3 = DualMotorModule()  # Added module3 to manage the extra stepper

# Register modules
yukon.register_with_slot(module1, SLOT_STEPPER1)
yukon.register_with_slot(module2, SLOT_SERVO1)
yukon.register_with_slot(module3, SLOT_STEPPER2)
yukon.verify_and_initialise()
yukon.enable_main_output()

ADDRESS = 0x18
io = BreakoutIOExpander(yukon.i2c, ADDRESS)

counter_pin_number = 1 
filament_counter = FilamentCounter(counter_pin_number)

# Initialize the filament counter
filament_counter.initialise(io)

# Create multiple StepperServoSet instances
# motor_module, servo_module, stepper_slot, servo_slot, filament_counter, io, driveStepperEngage=-83, driveStepperDisengage=-20
stepper_TL = StepperServoSet(module1, module2, SLOT_STEPPER1, "servo4", filament_counter, io, -41, -20)
stepper_TR = StepperServoSet(module3, module2, SLOT_STEPPER2, "servo2", filament_counter, io, -41, -20)

cutterEngage = -86
cutterDisengage = -42
cutterServo_slot = "servo3"
cutterServo = FilamentDriveServo(module2, cutterServo_slot)
cutterServo.initialise()

outputEngage = -54
outputDisengage = -63
outputServo_slot = "servo1"
outputServo = FilamentDriveServo(module2, outputServo_slot)
outputServo.initialise()



    





