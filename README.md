# GuiXYZ Version 2.1.0 -beta
![Python Logo](https://github.com/fedetony/GUI_XYZ_GImage/blob/GuiXYZ_V2.0/src/img/eye-in-a-sky-icon.ico "GuiXYZ V2.10beta by FG") This application is used to control machines which use Gcode. Gcode interfaces as Marlin,GRBL and others can be configured to be used for Gcode streaming, or to translate the old Gcodes to a new machine. 

The application is under development so some of its features are still under construction. As also since its so extensive please support me by commenting on issues or bugs you run with the software. This has been until now a single person effort.

Software is not still very intuitive, specially when configuring a new interface, yet is planned to be updated and to make a wiki with information on "how to" and what everything does in the interface. If you have a machine is not in the interface configuration it is difficult for me to test it since I only have access to the few interfaces already in configurations. I'll be glad to support you with your new interface configuration.

Its build such that can be flexibly configured for any type of machine. Often Machines use different types of controllers to convert Gcode into actions. 
This software uses a general customizable interface for a Machine Gcode input.

Interfaces can be added or removed, and any action can be accomodated to any machine G-code format.
Configuration Files have a version for the following interfaces already defined:
GRBL 0.9k 4th axis
TinyG
Marlin 2.0.x 
GRBL 1.1h
GRBL 1.1e g5x

-----
Software features:
- Set any interface for Gcode.
- Interface through serial port with a Machine. (Wifi and Parallel ports are planned)
- Basic movement Preset Gcode commands (for active interface): Homing, x,y,z movements. Reset, alarm clear. (Planned to be variable for multiaxis machines)
- Interface detection (in configuration)
- Manipulate,save load Gcode.
- Stream Gcode    
    -Stream a part of a code
- Send single Gcode commands
- Machine configuration
    -Read
    -Modify
- Translate Gcode from one interface to other interface. (Is slow)
- Checking Gcode with respect to interface (Not working properly)
- Gimage manipulation 
    Generates gcode from an image (Under construction) Works partially only outputs Marlin interface gcode
    -Gui is not very intuitive
    -vectorize image
    -raster image
    -Customize positioning sizes    
General Batton Configuration.(Under construction)
    -Creation of customized buttons and visualizations for any action, gcode or script.
    -Batton action run under click, press, or relase, two state functionality.
    -action chain Linking
    -action Looping

Gcode Visualization: Not constructed yet, just planned. (requires batton visualizations)

-----

Thank you for your support [web page][wp].

[wp]: https://github.com/fedetony








