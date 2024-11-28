# Yukon Control Boards Overview

This repository contains the MicroPython firmware, libraries, and examples for controlling the Pimoroni Yukon modular robotics platform. Yukon is powered by the RP2040 and is designed to drive various hardware modules like motors, servos, and sensors, supporting high-power robotics and engineering projects.

This guide focuses on summarizing key information from the original readme and adds details about the three main subsystems involved in a modular microfactory: the gantry, printer spool, and storage systems.

## Subsystems Overview

The microfactory is divided into three main subsystems, each with a dedicated Yukon control board and custom firmware:

1. **Gantry System**
   - The gantry system is responsible for positioning and transferring components or materials between different modules. It includes dual motor and servo modules configured to manage precise movements. The gantry is crucial for the automation of the microfactory, allowing materials to be transferred efficiently between the different processing stages.
   - The control board firmware (`main_gantry.py`) includes various functions to facilitate precise control of the gantry. Key functions include:
     - **Homing**: The `home()` function is used to calibrate the starting position of the gantry by moving it towards the home endstop sensor. This ensures all subsequent movements are accurate.
     - **Movement Control**: Functions like `move_left(steps)` and `move_right(steps)` allow for precise positioning of the gantry by specifying step counts. These movements are monitored by sensors to avoid collisions.
     - **Input Monitoring**: The gantry system utilizes several sensors, such as hall effect sensors and limit switches, to detect positions and ensure safe operation. The `check_inputs()` function reads sensor states to facilitate decision-making during operation.

2. **Printer Spool System**
   - The printer spool subsystem handles the loading and unloading of filament from the spool to the printer. This system is essential for maintaining a continuous supply of filament during printing operations, ensuring minimal downtime.
   - The printer spool control board utilizes big motor modules, stepper motors, and servos for precise control over the filament. The firmware (`main_printer.py`) includes key functions such as:
     - **Docking and Undocking**: The `dock()` and `undock()` functions control the engagement of the printer spool with the printer. This allows for easy attachment and detachment of the filament supply.
     - **Spool Control**: The `spool_up(time, max_speed)` function gradually increases the speed of the spool motor, enabling precise control over the filament feed rate. This function features ramp-up, full-speed, and ramp-down phases to ensure smooth operation and prevent sudden movements.
     - **Filament Intake**: The `intake_filament()` function manages the engagement of servos and motors to load filament into the printer. It uses sensors to ensure the filament is properly aligned and securely locked before printing begins.

3. **Storage System**
   - The storage system is responsible for managing the storage and dispensing of filament. It ensures that there is always enough filament available for the printer, and provides mechanisms to cut and retract filament as needed.
   - The storage control board firmware (`main_storage.py`) utilizes dual motor modules and servos to control filament dispensing. Key components and functions include:
     - **StepperServoSet Class**: This class is central to the operation of the storage system. It controls both the stepper motor and servo motor, providing methods such as `extrude_filament(amount)` to dispense a specific length of filament, and `deliver_filament_until()` to keep dispensing until a stop command is received.
     - **Filament Management**: Functions like `cutFilament()` and `pull_out()` are used to manage the filament effectively. The cutter mechanism is controlled by a servo, which is engaged to cut the filament when needed, ensuring that the correct length is maintained for further operations.
     - **Sensor Integration**: The storage system also includes a filament counter (`FilamentCounter` class) to monitor the amount of filament dispensed. This is crucial for maintaining accuracy and avoiding wastage.

## Motor and Sensor Files

The motor and sensor files (`motors.py` and `sensors.py`) are shared across all three subsystems (gantry, printer spool, and storage). These files provide the foundational classes and functions that allow the Yukon boards to control motors and read sensor data effectively.

1. **Motor Control (`motors.py`)**
   - The `motors.py` file defines various motor classes used in all subsystems, such as `StepperMotor`, `ServoMotor`, and specialized versions like `FilamentDriveMotor`, `GantryMotor`, and `FilamentLockServo`. These classes encapsulate the functionality needed to control the motors, including initialization, movement, and enabling/disabling the motors.
   - **Shared Usage**: The gantry system uses `GantryMotor` for precise positioning, while the printer spool and storage systems use `FilamentDriveMotor` and `FilamentLockServo` to control the loading and unloading of filament. Each motor class is designed to handle specific tasks, such as continuous extrusion (`extrude_while()`) or precise movements (`move_by_steps()`), making them versatile for different requirements.

2. **Sensor Integration (`sensors.py`)**
   - The `sensors.py` file provides classes for handling sensor inputs, such as `Sensor` and `FilamentCounter`. These classes are used to read input signals from various sensors like limit switches, hall effect sensors, and filament counters.
   - **Shared Usage**: The `FilamentCounter` class, for example, is used in both the printer spool and storage subsystems to track the length of filament dispensed, ensuring accurate control. The `Sensor` class is utilized in the gantry to monitor positions and prevent collisions during movements. By using common sensor classes, the firmware can maintain consistent behavior and simplify the integration of new sensors if needed.

## Flashing Firmware with Thonny

To flash firmware onto the Yukon boards, you can use the Thonny IDE:

1. Connect the control board to your computer using a USB cable.
2. Open Thonny and select the appropriate board (RP2040-based Yukon) from the "Interpreter" settings.
3. Put the board into bootloader mode by holding the BOOT/USER button while powering it on.
4. In Thonny, use the "File > Save As" option to write new firmware (e.g., `main_gantry.py`, `main_printer.py`, or `main_storage.py`) to the board.

This method allows you to easily update or modify the firmware on each control board, ensuring that all three subsystems are running the latest version of the control software.

## Controlling Subsystems from a Raspberry Pi

The Yukon control boards are connected to a Raspberry Pi and are controlled via a REPL (Read-Eval-Print Loop) interface. This allows for real-time control and coordination between the subsystems, making it possible to automate the operations of the microfactory.

Functions defined in the subsystem firmware files can be triggered from the Raspberry Pi, enabling coordinated actions such as:
- **Homing the Gantry**: Use the command `gantryStepper1.home("right", lambda: io.input(home_right))` to home the gantry, ensuring it starts from a known reference position before executing movements.
- **Filament Intake**: The `intake_filament()` function can be called to load filament into the printer or storage subsystem. This ensures that filament is always ready for use when needed, reducing downtime.
- **Filament Delivery**: The `deliver_filament(length)` function dispenses a precise length of filament, which is particularly useful when preparing the printer for a new print job. The `deliver_filament_until()` function allows continuous delivery until a stop command is issued, providing flexibility in operation.

This flexible control mechanism allows you to sequence movements and operations effectively across all three subsystems, enabling a high degree of automation and coordination within the microfactory.

