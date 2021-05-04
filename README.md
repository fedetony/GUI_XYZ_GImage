# GuiXYZ Version 2.0.0 -beta

This application is used to control as host machines which use Gcode.
The application is under development so some of its features are still under construction.
Its build such that can be flexibly configured for any type of machine. Often Machines use different types of controllers to convert Gcode into actions. 
This software uses a general customizable interface for a Machine Gcode input.

Interfaces can be added or removed, and any action can be accomodated to any machine G-code format.
Configuration Files have a version for the following interfaces already defined:
GRBL 0.9k 4th axis
TinyG ?.?
Marlin 2.0.x 
GRBL 1.1h

Software features:
- Set any interface for Gcode.
- Interface through serial port with a Machine. (Wifi and Parallel ports are planned)
- Basic movement Preset Gcode commands (for active interface): Homing, x,y,z movements. Reset, alarm clear.
- Interface detection (in configuration)
- Manipulate,save load Gcode.
- Stream Gcode    
    -Stream part of a code
- Send single Gcode commands
- Machine configuration
    -Read
    -Modify
- Translate Gcode from one interface to other interface.
- Checking Gcode with respect to interface (Not working properly)
- Gimage manipulation 
    Generates gcode from an image (Under construction) Works partially only Marlin interface
    -Gui is not very intuitive
    -vectorize image
    -raster image
    -Customize positioning sizes    
General Batton Configuration.(Under construction)
    -Creation of customized buttons and visualizations for any action,gcode or script.
    -Batton action run under click, press, or relase, two state functionality.
    -action chain Linking
    -action Looping

Gcode Visualization: Not constructed yet, just planned. (requires batton visualizations)

-----

This is an example of [web page][wp] for you to add links after.
Like  `this` code.
Like this Logo:
![Python Logo](https://www.python.org/static/community_logos/python-logo.png "Sample inline image")



[wp]: http://docutils.sourceforge.net/rst.html








