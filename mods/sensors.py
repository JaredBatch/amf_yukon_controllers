import time

from breakout_ioexpander import BreakoutIOExpander

from pimoroni_yukon import Yukon as yukon



class Sensor:
    
    ADDRESS = 0x18
    
    def __init__(self, pin, sensor_type='digital'):
        """
        Initialize the sensor object.
        :param pin: GPIO pin number
        :param sensor_type: 'digital' or 'ADC'
        """
        
        self.pin = pin
        self.sensor_type = sensor_type
        self.last_state = None
        

    def initialize(self, io):
        
        def initialize(self):
            raise NotImplementedError("This method should be overridden by subclasses")
    
#         if self.sensor_type == 'digital':
#             io.set_mode(self.pin, io.PIN_IN_PU)
#             print("✨ Sensor initialized as digital on pin", self.pin, "✨")
#         elif self.sensor_type == 'ADC':
#             io.set_mode(self.pin, io.PIN_ADC)
#             print("✨ Sensor initialized as ADC on pin", self.pin, "✨")
#         else:
#             raise ValueError("Sensor type must be 'digital' or 'ADC'.")

    def check_state(self, io):
        """
        Check the current state of the sensor.
        :return: Current state
        """
        if self.sensor_type == 'digital':
            current_state = io.input(self.pin)
            #print("✨ Current state of digital sensor on pin", self.pin, "is", current_state, "✨")
            self.last_state = current_state
            return current_state
        elif self.sensor_type == 'ADC':
            #current_state = 0  # Placeholder for ADC read value
            yukon.monitored_sleep(0.01) #Let it rest before taking values
            current_state = io.input_as_voltage(self.pin)
            #print("✨ Current state of ADC sensor on pin", self.pin, "is", current_state, "✨")
            self.last_state = current_state
            return current_state

#Class for filament sensor module 
# class FilamentSensor(Sensor):
#     def __init__(self, pin, filamentSensorThreshold=1.5):
#         super().__init__(pin, 'ADC')
#         self.filamentSensorThreshold = filamentSensorThreshold
# 
# 
#     def filament_state(self):
#         """
#         Check the current state of the filament.
#         :return: Current state (True for filament present)
#         """
#         ADC_state = super().check_state()
#         if ADC_state < self.filamentSensorThreshold: 
#             state = False
#         else:
#             state = True
#         return state 

# #Class for hall effect sensor module
# class HallEffectSensor(Sensor):
#     def __init__(self, pin):
#         super().__init__(pin, 'digital')
# 
# 
#     def HallEffect_state(self):
#         """
#         Check the current state of the hall effect sensor.
#         :return: Current state
#         """
#         state = super().check_state()
#         return state

# Class for filament counter module Orthus, needs to be completed
class FilamentCounter(Sensor):
    def __init__(self, pin):
        super().__init__(pin, 'digital')
        self.count = 0
        self.pulse_length = 0.156  # length of filament per pulse in mm

    def initialise(self, io):
        """
        Initialize the filament counter.
        """
        io.set_mode(self.pin, io.PIN_IN_PU)
        print("✨ Filament counter initialized as digital on pin", self.pin, "✨")
        self.last_state = self.check(io)

    def check(self, io):
        """
        Check the state of the filament counter and update the count if the state has changed.
        """
        save_last_state = self.last_state
        current_state = super().check_state(io)
        if current_state != save_last_state and current_state == 1:  # assuming a pulse is a transition to high
            self.count += 1
            
    def get_count(self):
        """
        Get the current filament count.
        :return: Filament count
        """
        return self.count

    def reset_count(self):
        """
        Reset the filament count to zero.
        """
        self.count = 0

    def filament_length(self):
        """
        Get the length of filament that has passed through.
        :return: Length of filament in mm
        """
        return self.count * self.pulse_length

    def watch_until_length(self, length_mm, io):
        """
        Watch the counter until a specific length of filament has passed through.
        :param length_mm: Length of filament in mm
        """
        self.reset_count()
        while self.filament_length() < length_mm:
            self.check(io)
            time.sleep(0.001)  # small delay to avoid busy-waiting
            print(f"Filament of {self.filament_length()} extruded")
        print(f" Desired length of {length_mm} mm of filament has passed through.")
