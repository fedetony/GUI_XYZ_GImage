# GuiXYZ Version 3.1.0 -beta
![Python Logo](https://github.com/fedetony/GUI_XYZ_GImage/blob/GuiXYZ_V2.0/src/img/eye-in-a-sky-icon.ico "GuiXYZ V3.1.0 beta by FG") .

---

# **G‑Code Machine Interface & Translator**

This application is designed to control machines that use G‑code. It supports multiple controller types—such as Marlin, GRBL, TinyG, and others—and can be configured for:

- **Direct G‑code streaming**, or  
- **Translating G‑code from one machine interface to another**

The goal is to provide a flexible, customizable environment capable of adapting to almost any G‑code‑driven machine.

---

## **Project Status**

This software is currently under active development. Some features are incomplete or experimental, and the interface is still evolving. Since this is a one‑person project, feedback is incredibly valuable. If you encounter bugs, unclear behavior, or missing features, please open an issue—your input genuinely helps shape the project.

Configuring a new machine interface is not yet intuitive, but a full wiki and “how‑to” documentation are planned. If your machine is not yet supported, I’m happy to help you create a working configuration.

---

## **Design Philosophy**

Machines often use different controllers, each with its own G‑code dialect. This application provides a **generalized, customizable interface layer** that allows:

- Adding or removing machine interfaces  
- Defining how each action maps to each controller’s G‑code  
- Translating G‑code between interfaces  
- Extending or modifying behavior without touching the core code  

The configuration system is flexible enough to adapt to almost any machine that speaks G‑code.

---

## **Included Interface Configurations**

The project currently includes ready‑to‑use configurations for:

- **GRBL 0.9k (4‑axis)**
- **TinyG**
- **Marlin 2.0.x**
- **GRBL 1.1h**
- **GRBL 1.1e (G5X variant)**

More can be added easily through the configuration system.

---

## **Platform Support**

- Linux — fully supported
- Windows — fully supported

Both platforms share the same configuration logic and feature set.

---

## **Features**

### **Machine Communication**
- Select any supported interface for G‑code output  
- Communicate with machines over **serial ports**  
  - (Wi‑Fi and parallel‑port support planned)

### **Movement & Control**
- Preset movement commands (homing, axis moves, reset, alarm clear)  
- Planned: customizable multi‑axis control buttons

### **G‑Code Tools**
- Load, edit, and save G‑code files  
- Stream full programs or selected segments  
- Send single G‑code commands  
- Read and modify machine configuration  
- Translate G‑code between interfaces  
  - (Currently slow, but functional)  
- Validate G‑code against the selected interface  
  - (Work in progress)

### **Image‑to‑G‑Code (Experimental)**
- Convert images into G‑code  
- Vector and raster modes  
- Positioning and size customization  
- Currently outputs Marlin‑compatible G‑code only  
- GUI still under development

### **Custom Button System (Under Construction)**
- Create custom buttons for actions, scripts, or G‑code  
- Trigger on click, press, release, or toggle  
- Chain multiple actions  
- Loop actions  
- Custom visualizations

-----

Thank you for your support [web page][wp].

[wp]: https://github.com/fedetony








