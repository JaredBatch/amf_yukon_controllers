import time
import math

from pimoroni_yukon import Yukon
yukon = Yukon()

from pimoroni_yukon.modules import QuadServoRegModule, QuadServoDirectModule
from pimoroni_yukon.modules import DualMotorModule
from pimoroni_yukon.devices.stepper import OkayStepper
#from pimoroni_yukon.modules import BigMotorModule

from mods import sensors


class StepperMotor():

    DEFAULT_CURRENT_SCALE = 0.5
    DEFAULT_MICROSTEPS = 4
    DEFAULT_STEPS_PER_UNIT = 52
    DEFAULT_MAX_CURRENT_LIMIT = 2

    def __init__(self, module, current_scale=DEFAULT_CURRENT_SCALE, microsteps=DEFAULT_MICROSTEPS, steps_per_unit=DEFAULT_STEPS_PER_UNIT):

        self.module = module
        self.current_scale = current_scale
        self.microsteps = microsteps
        self.steps_per_unit = steps_per_unit

        self.current_scale = current_scale
        self.microsteps = microsteps
        self.steps_per_unit = steps_per_unit
        

    def initialise(self, CUR_LIM=DEFAULT_MAX_CURRENT_LIMIT):
        self.module.set_current_limit(CUR_LIM)
        self.stepper = OkayStepper(self.module.motor1, self.module.motor2, current_scale=self.current_scale, microsteps=self.microsteps, steps_per_unit=self.steps_per_unit)
        self.module.disable()
        #print("Initialised stepper")

    def move_by(self, units, duration):
        self.module.enable()
        self.stepper.move_by(units, duration)

    def move_to(self, step, duration):
        self.module.enable()
        self.stepper.move_to(step, duration)

    def move_by_steps(self, step, duration):
        self.module.enable()
        self.stepper.move_by_steps(step, duration)

    def enable(self):
        self.module.enable()

    def disable(self):
        self.module.disable()

    def wait_for_move(self):
        self.stepper.wait_for_move()
        
    def stop(self):
        self.stepper.stop()

class ServoMotor:

    SERVO_EXTENT = 80.0 

    def __init__(self, module, pin):
        self.module = module
        self.pin = pin

    def initialise(self):
        self.module.enable()
        self.servo = getattr(self.module, self.pin)  # Dynamically get the servo attribute
        #print(f"Initialised {self.pin}")
        self.NUM_SERVOS = 1
        #print(f"Up to {self.NUM_SERVOS} servos available")

    def set_value(self, value):
        self.servo.value(value)

    def disable(self):
        self.module.disable()

    def enable(self):
        self.module.enable()

    def angle_from_index(self, index, offset=0.0, servo_extend=SERVO_EXTENT):
        phase = ((index / self.NUM_SERVOS) + offset) * math.pi * 2
        angle = math.sin(phase) * servo_extend
        return angle

class FilamentDriveMotor(StepperMotor):

    DEFAULT_CURRENT_SCALE = 0.5
    DEFAULT_MICROSTEPS = 4
    DEFAULT_STEPS_PER_UNIT = 52
    DEFAULT_MAX_CURRENT_LIMIT = 2

    def __init__(self, module, filament_counter, io, current_scale=DEFAULT_CURRENT_SCALE, microsteps=DEFAULT_MICROSTEPS, steps_per_unit=DEFAULT_STEPS_PER_UNIT):
        super().__init__(module, current_scale, microsteps, steps_per_unit)
        self.filament_counter = filament_counter
        self.io = io

    def initialise(self):
        super().initialise()

    def extrude_length(self, length_mm):
        self.filament_counter.reset_count()
        super().enable()
        while self.filament_counter.filament_length() < length_mm:
            self.filament_counter.check(self.io)
            super().move_by(2, 0.1)
        final_length = self.filament_counter.filament_length()
        super().disable()
        #print(f"Desired length of {length_mm} mm of filament has passed through. Final length: {final_length} mm")

    def extrude_filament_blind(self, length_mm, speed_s):
        super().enable()
        super().move_by(length_mm, speed_s)
        super().wait_for_move()
        super().disable()
    
    def extrude_while(self, dir=1):
        super().enable()
        super().move_by(dir*500000, 100000)
        #super().wait_for_move()
        
    def extrude_while_fast(self, dir=1):
        super().enable()
        super().move_by(dir*500000, 50000)
        #super().wait_for_move()
        
class FilamentBlindDriveMotor(StepperMotor):

    DEFAULT_CURRENT_SCALE = 0.5
    DEFAULT_MICROSTEPS = 4
    DEFAULT_STEPS_PER_UNIT = 52
    DEFAULT_MAX_CURRENT_LIMIT = 2

    def __init__(self, module, current_scale=DEFAULT_CURRENT_SCALE, microsteps=DEFAULT_MICROSTEPS, steps_per_unit=DEFAULT_STEPS_PER_UNIT):
        super().__init__(module, current_scale, microsteps, steps_per_unit)

    def initialise(self):
        super().initialise()

    def extrude_filament_blind(self, length_mm, speed_s):
        super().enable()
        super().move_by(length_mm, speed_s)
        super().wait_for_move()
        super().disable()
    
    def extrude_while(self, dir=1):
        super().enable()
        super().move_by(dir*500000, 100000)
        #super().wait_for_move()
        
    def extrude_while_fast(self, dir=1):
        super().enable()
        super().move_by(dir*500000, 50000)
        #super().wait_for_move()

class GantryMotor(StepperMotor):

    DEFAULT_CURRENT_SCALE = 0.5
    DEFAULT_MICROSTEPS = 4
    DEFAULT_STEPS_PER_UNIT = 52
    DEFAULT_MAX_CURRENT_LIMIT = 2

    def __init__(self, module, current_scale=DEFAULT_CURRENT_SCALE, microsteps=DEFAULT_MICROSTEPS, steps_per_unit=DEFAULT_STEPS_PER_UNIT):
        super().__init__( module, current_scale, microsteps, steps_per_unit)

    def initialise(self):
        super().initialise()
        self.current_position = None

    def move_left_wait(self, units, duration):
        super().move_by(-1*units, duration)
        super().wait_for_move()

    def move_right_wait(self, units, duration):
        super().move_by(units, duration)
        super().wait_for_move()

    def move_left(self, units, duration):
        super().move_by(-1*units, duration)

    def move_right(self, units, duration):
        super().move_by(units, duration)

    def move_left_int(self, steps, duration):
        super().move_by_steps(-1*steps, duration)
        super().wait_for_move()

    def move_right_int(self, steps, duration):
        super().move_by_steps(steps, duration)
        super().wait_for_move()

    def home(self, direction, endstop):
        #print(f"Homing {direction}")
        if direction == "right":
            self.move_left_int(20, 0.1)
            #print(endstop())
            while not endstop():
                self.move_right_int(20, 0.1)
                #print(endstop())
            self.move_left_int(40, 0.2)
            self.current_position = 0
        else:
            print("Incorrect direction - must be right")

    # def move_to_position(self, position, he_sensor):
    #     print(f"Moving to pos: {position}, current position is {self.current_position}")
    #     if self.current_position == None:
    #         print("Cannot move to position, gantry not homed")

    #     if position > self.current_position + 1:
    #         if he_sensor():
    #             self.move_left_int(20, 0.1)
    #         while not he_sensor():
    #             self.move_left_int(20, 0.1)
    #         self.current_position = self.current_position + 1
    #     elif position == self.current_position + 1:
    #         if he_sensor():
    #             self.move_left_int(20, 0.1)
    #         while not he_sensor():
    #             self.move_left_int(20, 0.1)
    #         self.current_position = self.current_position + 1
    #         self.move_right_int(20, 0.1)
    #         while not he_sensor():
    #             self.move_left_int(20, 0.2)
    #         self.current_position = self.current_position + 1

    #     if position < self.current_position - 1:
    #         if he_sensor():
    #             self.move_right_int(20, 0.1)
    #         while not he_sensor():
    #             self.move_right_int(20, 0.1)
    #         self.current_position = self.current_position - 1
    #     elif position == self.current_position + 1:
    #         if he_sensor():
    #             self.move_right_int(20, 0.1)
    #         while not he_sensor():
    #             self.move_right_int(20, 0.1)
    #         self.current_position = self.current_position - 1
    #         self.move_right_int(20, 0.1)
    #         while not he_sensor():
    #             self.move_right_int(20, 0.2)
    #         self.current_position = self.current_position - 1

    def move_to_position(self, position, he_sensor, right_endstop, left_endstop):
        print(f"Moving to pos: {position}, current position is {self.current_position}")
        if self.current_position is None or position < 0:
            print("Cannot move to position, gantry not homed or invalid position")
            return
        if position == 0:
            self.home("right", lambda: right_endstop())
        while self.current_position != position:
            if position > self.current_position:
                self.move_left_int(80, 1)
                while not he_sensor():
                    self.move_left_int(20, 0.1)
                self.current_position += 1
            elif position < self.current_position:
                self.move_right_int(80, 1)
                while not he_sensor():
                    self.move_right_int(20, 0.1)
                self.current_position -= 1





    def move_to_load_location(self, home_endstop):
        print("Loading")
        self.home("right", home_endstop)


    def move_to_unload_location(self):
        print("Unloading")

class FilamentDriveServo(ServoMotor):

    DEFAULT_POS_ENGAGED = 8
    DEFAULT_POS_DISENGAGED = 25
    # DEFAULT_PWM_ENGAGED = 1700
    # DEFAULT_PWN_DISENGAGED = 3200

    def __init__(self, module, pin):
        super().__init__(module, pin)

    def initialise(self):
        super().initialise()

    def defaultPosition(self):
        angle = self.angle_from_index(1)
        super().set_value(angle)
        #print(f"Set engage value to {angle}")

    def engage(self, pos_engage=DEFAULT_POS_ENGAGED):
        super().set_value(pos_engage)
        yukon.monitored_sleep(1)
        super().set_value(pos_engage+10)
        #print(f"Set engage value to {pos_engage}")

    def disengage(self, pos_disengage=DEFAULT_POS_DISENGAGED):
        super().set_value(pos_disengage)
        yukon.monitored_sleep(1)
        super().set_value(pos_disengage-10)
        #print(f"Set disengage value to {pos_disengage}")

    def disable(self):
        super().disable()
        
class dockingServo(ServoMotor):

    DEFAULT_POS_ENGAGED = 0
    DEFAULT_POS_DISENGAGED = 22

    def __init__(self, module, pin):
        super().__init__(module, pin)

    def initialise(self):
        super().initialise()

    def defaultPosition(self):
        angle = self.angle_from_index(1)
        super().set_value(angle)
        #print(f"Set engage value to {angle}")

    def engage(self, pos_engage=DEFAULT_POS_ENGAGED):
        super().set_value(pos_engage)
        yukon.monitored_sleep(1)
        super().set_value(pos_engage)
        #print(f"Set engage value to {pos_engage}")

    def disengage(self, pos_disengage=DEFAULT_POS_DISENGAGED):
        super().set_value(pos_disengage)
        yukon.monitored_sleep(1)
        super().set_value(pos_disengage)
        #print(f"Set disengage value to {pos_disengage}")

    def disable(self):
        super().disable()

class FilamentLockServo(ServoMotor):

    DEFAULT_POS_ENGAGED = 8
    DEFAULT_POS_DISENGAGED = 25
    # DEFAULT_PWM_ENGAGED = 1700
    # DEFAULT_PWN_DISENGAGED = 3200

    def __init__(self, module, pin):
        super().__init__(module, pin)

    def initialise(self):
        super().initialise()

    def defaultPosition(self):
        angle = self.angle_from_index(1)
        super().set_value(angle)
        #print(f"Set engage value to {angle}")

    def engage(self, pos_engage=DEFAULT_POS_ENGAGED):
        yukon.monitored_sleep(0.2)
        super().set_value(pos_engage)
        #print(f"Set engage value to {pos_engage}")

    def disengage(self, pos_disengage=DEFAULT_POS_DISENGAGED):
        super().set_value(pos_disengage)
        #print(f"Set disengage value to {pos_disengage}")

    def disable(self):
        super().disable()

class GuillotineMotor(ServoMotor):
    def __init__(self, pin, module):
        super().__init__(pin, module)

class OutputEngagementMotor(ServoMotor):
    def __init__(self, pin, module):
        super().__init__(pin, module)



