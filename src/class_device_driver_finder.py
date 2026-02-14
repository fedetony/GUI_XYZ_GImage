"""
"""

import logging
import sys
import glob
import usb
import re
import os, sys, ctypes, subprocess
import json

import platform
devdriver_fun_name="Device Driver"
from class_LogHandler import get_appPath, LM ,init_logger_manager
try:
    log = LM.get_logger_with_handler(devdriver_fun_name,
                                     "debug",
                                     True,
                                     "%(asctime)s [%(levelname)s] (%(name)s) %(message)s")
    log.info(f"{devdriver_fun_name} Logger started")
except (AttributeError, ImportError):
    LM = init_logger_manager(None)
    log = LM.get_logger(__name__)
    log.info("Application starting...")

ap=get_appPath()
img_path=os.path.join(ap,"img")
config_path=os.path.join(ap,"config")
temp_path=os.path.join(ap,"temp")
gimage_path=os.path.join(ap,"gimage")

FTDI_AVAILABLE=False
try:
    import pylibftdi as ftdi
    FTDI_AVAILABLE=True
except ImportError as eee:
    log.warning(f"ftdi module is not installed:{eee}")    

WIN32COM_AVAILABLE = False
FTD_AVAILABLE = False
system = platform.system()
if system == "Windows":
    try:
        import win32com.client
        WIN32COM_AVAILABLE = True
    except ImportError as eee:
        log.warning(f"win32com.client module is not installed:{eee}")
        
    try:
        import ftd2xx as ftd
        FTD_AVAILABLE = True
    except ImportError as eee:
        log.warning(f"win32com.client module is not installed:{eee}")
        

"""
A text based interface. For example use over serial ports like
"/dev/ttyS1" or "/dev/ttyUSB0" on Linux machines or "COM1" on Windows.
The interface is a simple implementation that has been used for
recording CAN traces.
See the interface documentation for the format being used.
"""

import struct
from typing import Any, List, Tuple, Optional, Union

# python-can library
from can.bus import BusABC
from can import Message, CanError


import typing_extensions
#from can.typechecking import AutoDetectedConfig
# Used for the Abstract Base Class
ChannelStr = str
ChannelInt = int
Channel = Union[ChannelInt, ChannelStr]
AutoDetectedConfig = typing_extensions.TypedDict(
    "AutoDetectedConfig", {"interface": str, "channel": Channel}
)

try:
    import serial
except ImportError:
    log.warning(
        "You won't be able to use the serial can backend without "
        "the serial module installed!"
    )
    serial = None

try:
    from serial.tools.list_ports import comports as list_comports
except ImportError:
    # If unavailable on some platform, just return nothing
    def list_comports() -> List[Any]:
        return []

def get_device_manager():
    system = platform.system()
    if system == "Windows":
        return WindowsDeviceManager()
    elif system == "Linux":
        return LinuxDeviceManager()
    elif system == "Darwin":
        return MacDeviceManager()
    else:
        raise RuntimeError(f"Unsupported OS: {system}")
    
class DeviceInfo:
    def __init__(self, dtype, name, identifier, info=None, friendly_map=None):
        self.type = dtype
        self.name = name
        self.id = identifier
        self.info = info or {}
        self.friendly_map = friendly_map or {}
        self.friendly = self.add_friendly_descriptor()

    def add_friendly_descriptor(self):
        vid = self.info.get("vid")
        pid = self.info.get("pid")

        if vid is not None and pid is not None:
            key = f"{vid:04X}:{pid:04X}"
            if key in self.friendly_map:
                return self.friendly_map[key]

        # Fallbacks
        if self.info.get("product"):
            return self.info["product"]

        if self.info.get("description"):
            return self.info["description"]

        return self.name


class CommonDeviceFunctions:
    def safe_import(self, module_name):
        try:
            return __import__(module_name)
        except ImportError as eee:
            log.error(f"Error importing {module_name}: {eee}")            
            return None

class SuperDeviceManagerSqueleton:
    def __init__(self):
        self.common = CommonDeviceFunctions()
        self.usb_friendly = self.load_friendly_names()

    def load_friendly_names(self):
        path = os.path.join(config_path, "friendly_names_devices.json")
        try:
            with open(path, "r") as f:
                return json.load(f)
        except Exception as eee:
            log.warning("Friendly Names were not Defined: {eee}")
            return {}
        
    def list_all_devices(self):
        """
        Return a unified list of DeviceInfo objects.
        Each detector method returns a list of DeviceInfo entries.
        This function aggregates them safely.
        """
        devices = []

        # List of detector method names to call
        detector_methods = [
            "detect_serial",
            "detect_usb",
            "detect_ftdi",
            "detect_can",
            "detect_ble",
            "detect_tcpip",
        ]

        for method_name in detector_methods:
            method = getattr(self, method_name, None)

            if callable(method):
                try:
                    result = method()
                    if isinstance(result, list):
                        devices.extend(result)
                except Exception as e:
                    # Never break the whole system because one detector failed
                    print(f"[WARN] Detector '{method_name}' failed: {e}")

        return devices

    def detect_serial(self):
        ports = []
        try:
            import serial.tools.list_ports
            for p in serial.tools.list_ports.comports():
                ports.append(DeviceInfo(
                    "serial",
                    p.device,
                    p.serial_number or p.device,
                    {
                        "description": p.description,
                        "vid": p.vid,
                        "pid": p.pid,
                        "manufacturer": p.manufacturer,
                        "product": p.product
                    }, 
                    friendly_map=self.usb_friendly
                ))
        except Exception:
            pass
        return ports

    def detect_ftdi(self):
        devices = []
        if not FTDI_AVAILABLE:
            return devices        
        if self.ftdi:
            try:
                for idx, info in enumerate(self.ftdi.Driver().list_devices()):
                    devices.append(DeviceInfo(
                        "ftdi",
                        f"FTDI {info}",
                        str(idx),
                        {"raw": info},
                        friendly_map=self.usb_friendly
                    ))
            except Exception:
                pass
        return devices

    def detect_usb(self):
        devices = []
        if not self.usb:
            return devices

        try:
            for dev in self.usb.core.find(find_all=True):
                vid = dev.idVendor
                pid = dev.idProduct

                devices.append(DeviceInfo(
                    "usb",
                    f"USB {vid:04x}:{pid:04x}",
                    f"{vid:04x}:{pid:04x}",
                    {
                        "vid": vid,
                        "pid": pid,                        
                        "bus": getattr(dev, "bus", None),
                        "address": getattr(dev, "address", None)
                    },
                    friendly_map=self.usb_friendly
                ))
        except Exception:
            pass

        return devices


    def detect_can(self):
        devices = []

        can = self.common.safe_import("can")
        if not can:
            return devices

        # python-can 4.x exposes VALID_INTERFACES
        try:
            valid_interfaces = list(can.interfaces.VALID_INTERFACES)
        except Exception:
            return devices

        for interface in valid_interfaces:
            try:
                # Dynamically import the backend module
                module = __import__(f"can.interfaces.{interface}", fromlist=["*"])

                # Only backends that implement list_available_channels()
                if hasattr(module, "list_available_channels"):
                    channels = module.list_available_channels()

                    for ch in channels:
                        devices.append(DeviceInfo(
                            "can",
                            f"{interface} {ch}",
                            ch,
                            {"backend": interface},
                            friendly_map=self.usb_friendly
                        ))
            except Exception:
                # Ignore backends that fail (missing drivers, unsupported OS, etc.)
                pass

        # Lawicel / USB2CAN (FTDI 0403:6001)
        if self.usb:
            try:
                for dev in self.usb.core.find(find_all=True):
                    if dev.idVendor == 0x0403 and dev.idProduct == 0x6001:
                        devices.append(DeviceInfo(
                            "can",
                            "Lawicel USB2CAN",
                            "0403:6001",
                            {"backend": "lawicel","vid":dev.idVendor,"pid":dev.idProduct},
                            friendly_map=self.usb_friendly
                        )
                        )
            except Exception:
                pass

        return devices



    def detect_ble(self):
        devices = []
        bleak = self.common.safe_import("bleak")

        if not bleak:
            return devices

        try:
            from bleak import BleakScanner
            found = BleakScanner.discover(timeout=2.0)

            # If discover() is async, handle both cases
            if hasattr(found, "__await__"):
                import asyncio
                found = asyncio.run(found)

            for d in found:
                devices.append(DeviceInfo(
                    "ble",
                    d.name or "Unknown BLE Device",
                    d.address,
                    {"rssi": d.rssi},
                    friendly_map=self.usb_friendly
                ))
        except Exception:
            pass

        return devices

    def detect_tcpip_custom(self, ip_list, port_list, timeout=0.1):
        devices = []
        import socket

        for ip in ip_list:
            for port in port_list:
                try:
                    with socket.create_connection((ip, port), timeout=timeout):
                        devices.append(DeviceInfo(
                            "tcpip",
                            f"{ip}:{port}",
                            ip,
                            {"port": port},
                            friendly_map=self.usb_friendly
                        ))
                except Exception:
                    pass

        return devices

    @staticmethod
    def expand_ip_range(ip_range):
        base, rng = ip_range.rsplit(".", 1)
        start, end = map(int, rng.split("-"))
        return [f"{base}.{i}" for i in range(start, end+1)]


    def detect_tcpip(self, sn_range=None, common_ports=None):
        devices = []

        # Always include localhost
        devices.append(DeviceInfo(
            "tcpip",
            "localhost",
            "127.0.0.1",
            {"note": "Local machine"},
            friendly_map=self.usb_friendly
        ))

        import socket

        # Default ports for instruments
        if not common_ports:
            common_ports = [80, 5025, 4880, 4881]
        else:
            common_ports = self._limit_n_unique(common_ports, 0, 65535)

        # Default IP range
        if not sn_range:
            sn_range = [1, 255]

        # Normalize IP range
        if len(sn_range) == 2:
            sn_range = self._limit_n_unique(sn_range, 1, 255)
            start, end = min(sn_range), max(sn_range)
            address_range = range(start, end + 1)
        else:
            address_range = self._limit_n_unique(sn_range, 1, 255)

        try:
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            subnet = local_ip.rsplit(".", 1)[0] + "."

            log.info(f"Scanning {subnet}{start}-{end} on ports {common_ports}")

            for i in address_range:
                ip = subnet + str(i)

                # Skip own IP
                if ip == local_ip:
                    continue

                for port in common_ports:
                    try:
                        socket.create_connection((ip, port), timeout=0.05)

                        devices.append(DeviceInfo(
                            "tcpip",
                            f"{ip}:{port}",
                            ip,
                            {"port": port},
                            friendly_map=self.usb_friendly
                        ))
                        break  # stop scanning more ports for this IP

                    except Exception:
                        pass

            log.info("TCP/IP scan finished")

        except Exception as e:
            log.error(f"TCP/IP scan failed: {e}")

        return devices


    @staticmethod
    def _limit_n_unique(a_list,min_int,max_int):
        address_range=[]
        for add in a_list:
            add = min(max_int,max(min_int,int(add)))
            address_range.append(add)
            address_range=list(set(address_range))
        return address_range

    
    def detect_visa(self):
        devices = []

        # Try to import pyvisa safely
        visa = self.common.safe_import("pyvisa")
        if not visa:
            return devices  # pyvisa not installed

        try:
            rm = visa.ResourceManager()

            # List all VISA resources (ASRL, USB, TCPIP, GPIB, PXI…)
            resources = rm.list_resources()

            for r in resources:
                try:
                    info = {}

                    # Try to get resource info (safe)
                    try:
                        res = rm.open_resource(r)
                        info["resource_class"] = res.resource_class
                        info["interface_type"] = res.interface_type
                        info["interface_board"] = res.interface_board_number
                        info["manufacturer"] = res.manufacturer_name
                        info["model"] = res.model_name
                        info["serial"] = res.serial_number
                    except Exception:
                        pass  # Some VISA devices don't allow querying

                    devices.append(DeviceInfo(
                        "visa",
                        r,          # e.g. "USB0::0x0957::0x1798::MY12345678::INSTR"
                        r,
                        info,
                        friendly_map=self.usb_friendly
                    ))

                except Exception:
                    pass

        except Exception:
            pass

        return devices

class WindowsDeviceManager(SuperDeviceManagerSqueleton):
    def __init__(self):
        super().__init__()
        self.win32com = self.common.safe_import("win32com.client")
        self.ftd = self.common.safe_import("ftd2xx")
        self.serial = self.common.safe_import("serial")
        self.usb = self.common.safe_import("usb")

    def list_all_devices(self):
        devices = []
        devices += self.detect_serial()
        devices += self.detect_usb()
        devices += self.detect_ftdi()
        devices += self.detect_can()
        return devices

class LinuxDeviceManager(SuperDeviceManagerSqueleton):
    def __init__(self):
        super().__init__()
        self.serial = self.common.safe_import("serial")
        self.usb = self.common.safe_import("usb")
        self.ftdi = self.common.safe_import("pylibftdi")

    def list_all_devices(self):
        devices = []
        devices += self.detect_serial()
        devices += self.detect_usb()
        devices += self.detect_ftdi()
        devices += self.detect_can()
        return devices

class MacDeviceManager(SuperDeviceManagerSqueleton):
    def __init__(self):
        super().__init__()
        self.serial = self.common.safe_import("serial")
        self.usb = self.common.safe_import("usb")
        self.ftdi = self.common.safe_import("pylibftdi")

    def list_all_devices(self):
        devices = []
        devices += self.detect_serial()
        devices += self.detect_usb()
        devices += self.detect_ftdi()
        return devices


class SuperDeviceManager:
    def __init__(self):
        self.finder = DeviceFinder()

    def list_all_devices(self):
        devices = []

        # 1. Serial ports
        for port in self.finder.Get_serial_ports():
            devices.append({
                "type": "serial",
                "name": port,
                "id": port,
                "info": {}
            })

        # 2. USB devices (generic)
        for idx, dev in self.finder.get_usb_device().items():
            devices.append({
                "type": "usb",
                "name": f"USB {hex(dev.idVendor)}:{hex(dev.idProduct)}",
                "id": f"{dev.idVendor:04x}:{dev.idProduct:04x}",
                "info": {
                    "vendor": dev.idVendor,
                    "product": dev.idProduct
                }
            })

        # 3. FTDI devices
        for idx, info in self.finder.get_FTDI_devices().items():
            devices.append({
                "type": "ftdi",
                "name": f"FTDI {info}",
                "id": str(idx),
                "info": {"raw": info}
            })

        # 4. Serial tools (extra metadata)
        for idx, dev in self.finder.get_devices_serial_tools().items():
            devices.append({
                "type": "serial",
                "name": dev["device"],
                "id": dev["serial_number"] or dev["device"],
                "info": dev
            })

        return devices

class DriverFinder:
    def __init__(self):
        miCanVendorId = "VID_0403&PID_ECD9"
        FtdiVendorId  = "VID_0403&PID_6010"        
        lawicelId = "VID_0403&PID_6001"
        vectorId  = "VID_1248" #vector
        pcanId = "VID_0C72"
        kvaserId = "kvaser"#"VID_0BFD" #kvaser

        self.idList=[FtdiVendorId,miCanVendorId,vectorId,pcanId,lawicelId,kvaserId]
        self.Dpinst=self.get_Dpinst()
        self.allow_uninstall = False

    def Is64bit(self):
        try:
            i = ctypes.c_int()
            kernel32 = ctypes.windll.kernel32
            process = kernel32.GetCurrentProcess()
            kernel32.IsWow64Process(process, ctypes.byref(i))
            return (i.value != 0)
        except:
            return 0

    def UninstallDrivers(self,path,vendorid): 
        files = os.listdir(path)
        for f in files:
            (root,ext) = os.path.splitext(f)

            if ext == ".inf":
                inf_fname = os.path.join(path, f)

                with open(inf_fname, 'r', encoding="latin_1") as fin:
                    txt = fin.read()
                fin.close()

                if (vendorid in txt):    # or (FtdiVendorId in txt):
                    try:                        
                        if self.allow_uninstall:
                            print("Deinstalling: \"{}\"...".format(inf_fname))
                            result = subprocess.call(self.Dpinst + " " + "/S /U \"%s\"" % (inf_fname), shell=False)
                            print("OK: result =",result)
                    except Exception as e:
                        print("ERROR:{}".format(e))

    def FindDrivers(self,path,vendorid,printfind=True):        
        drivers=[]
        files = os.listdir(path)
        for f in files:
            (root,ext) = os.path.splitext(f)
            if ext == ".inf":
                inf_fname = os.path.join(path, f)
                with open(inf_fname, 'r', encoding="latin_1") as fin: #encoding="utf-8") as fin:                
                    txt = fin.read()            
                fin.close()            
                                
                if (vendorid in txt or vendorid in inf_fname):   
                    if printfind== True:
                        print("Found Driver File: \"{}\"...".format(inf_fname))               
                    drivers.append("{}".format(inf_fname))              
                    
        return drivers

    def get_Dpinst(self):
        if self.Is64bit():
            Dpinst = os.path.join("..","DPInst","amd64","dpinst.exe")
        elif sys.getwindowsversion()[:4] < (5,1,0,0):     # Win2k und kleiner
            Dpinst = os.path.join("..","DPInst","win2k","dpinst.exe")
        else:
            Dpinst = os.path.join("..","DPInst","x86","dpinst.exe")
        return Dpinst
    
    def get_idlist(self):
        return self.idList

    def set_idlist(self,idlist):
        self.idList=idlist
    
    def append_id_to_idlist(self,id):
        self.idList.append(id)
    
    def remove_id_from_idlist(self,id):
        for idindex,ids in enumerate(self.idList):            
            if ids == id:
                self.idList.pop(idindex)
                break

    def get_drivers(self,printfind=True):                
        SystemRoot = os.environ["SystemRoot"]        
        driverdict={}
        for ids in self.idList:
            #print("************ {} ***********".format(ids))
            if sys.getwindowsversion()[:4] >= (6,0,0,0):    # Vista, Win7
                driver_repository = os.path.join(SystemRoot, "System32", "DriverStore", "FileRepository")
                driver_dirs       = os.listdir(driver_repository)            
                for d in driver_dirs:
                    drivers=self.FindDrivers(os.path.join(driver_repository,d),ids,printfind)
                    if len(drivers)>0:
                        driverdict.update({ids:drivers})
            else:
                drivers=self.FindDrivers(os.path.join(SystemRoot, "inf"),ids,printfind)
                if len(drivers)>0:
                    driverdict.update({ids:drivers})
        return driverdict
            



class DeviceFinder:
    def __init__(self):
        found_devices={}

    def Get_serial_ports(self):
            """ Lists serial port names
                :raises EnvironmentError:
                    On unsupported or unknown platforms
                :returns:
                    A list of the serial ports available on the system
            """
            if sys.platform.startswith('win'):
                ports = ['COM%s' % (i + 1) for i in range(256)]
            elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
                # this excludes your current terminal "/dev/tty"
                ports = glob.glob('/dev/tty[A-Za-z]*')
            elif sys.platform.startswith('darwin'):
                ports = glob.glob('/dev/tty.*')
            else:
                raise EnvironmentError('Unsupported platform')

            result = []
            for port in ports:
                try:
                    s = serial.Serial(port)
                    s.close()
                    result.append(port)
                except (OSError, serial.SerialException):
                    pass
            return result

    def get_usb_device(self): 
        # with pure PyUSB
        Devices={}
        try:
            for iii,dev in enumerate(usb.core.find(find_all=True)):
                #print(dev)                           
                #print(usb.util.get_string( dev, dev.iSerialNumber ) )
                Devices.update({iii:dev})
        except:
            pass
        #dev2 = usb.core.find(idProduct=0x0009)
        #print( usb.util.get_string( dev2, dev2.iSerialNumber ) )
        return Devices

    def get_FTDI_devices(self):
        #Windows: https://iosoft.blog/2018/12/02/ftdi-python-part-1/
        #Linux: https://iosoft.blog/2018/12/05/ftdi-python-part-2/
        """
        If you want to avoid running all your code as root, you need to give permission for user-space applications to access the USB device. 
        FTDI devices usually have a PID of 0403, so to allow user access to all FTDI devices, create a file /etc/udev/rules.d/99-libftdi.rules with the contents:
        SUBSYSTEMS=="usb", ATTRS{idVendor}=="0403", GROUP="dialout", MODE="0660"
        """
        Devices={} 
        if sys.platform.startswith('win'):
            for iii in range(256):
                try:
                    ddd = ftd.open(iii)    # Open first FTDI device
                    info=ddd.getDeviceInfo()                                            
                    Devices.update({iii:info})
                    ddd.close()   # explicit close 'cause of delayed GC in java
                except:                       
                    pass
        elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin') or sys.platform.startswith('darwin'):
            list=ftdi.Driver().list_devices()
            for iii,info in enumerate(list):
                Devices.update({iii:info})
        else:
            raise EnvironmentError('Unsupported platform')
        
        return Devices

    def get_serial_descriptions(self):        
        descriptions={}
        if WIN32COM_AVAILABLE==False:
            return descriptions
        #https://learn.microsoft.com/en-us/windows/win32/cimwin32prov/win32-serialport
        '''
        uint16   Availability;
        boolean  Binary;
        uint16   Capabilities[];
        string   CapabilityDescriptions[];
        string   Caption;
        uint32   ConfigManagerErrorCode;
        boolean  ConfigManagerUserConfig;
        string   CreationClassName;
        string   Description;
        string   DeviceID;
        boolean  ErrorCleared;
        string   ErrorDescription;
        datetime InstallDate;
        uint32   LastErrorCode;
        uint32   MaxBaudRate;
        uint32   MaximumInputBufferSize;
        uint32   MaximumOutputBufferSize;
        uint32   MaxNumberControlled;
        string   Name;
        boolean  OSAutoDiscovered;
        string   PNPDeviceID;
        uint16   PowerManagementCapabilities[];
        boolean  PowerManagementSupported;
        uint16   ProtocolSupported;
        string   ProviderType;
        boolean  SettableBaudRate;
        boolean  SettableDataBits;
        boolean  SettableFlowControl;
        boolean  SettableParity;
        boolean  SettableParityCheck;
        boolean  SettableRLSD;
        boolean  SettableStopBits;
        string   Status;
        uint16   StatusInfo;
        boolean  Supports16BitMode;
        boolean  SupportsDTRDSR;
        boolean  SupportsElapsedTimeouts;
        boolean  SupportsIntTimeouts;
        boolean  SupportsParityCheck;
        boolean  SupportsRLSD;
        boolean  SupportsRTSCTS;
        boolean  SupportsSpecialCharacters;
        boolean  SupportsXOnXOff;
        boolean  SupportsXOnXOffSet;
        string   SystemCreationClassName;
        string   SystemName;
        datetime TimeOfLastReset;
        '''
        wmi = win32com.client.GetObject("winmgmts:")
        for serial in wmi.InstancesOf("Win32_SerialPort"):
            descriptions.update({serial.Name:serial.Description})
            #print (serial.Name, serial.Description)
        return descriptions

    def get_USBController_descriptions(self):
        descriptions={}
        if WIN32COM_AVAILABLE==False:
            return descriptions
        # https://learn.microsoft.com/en-us/windows/win32/cimwin32prov/win32-usbcontroller
        '''
        uint16   Availability;
        string   Caption;
        uint32   ConfigManagerErrorCode;
        boolean  ConfigManagerUserConfig;
        string   CreationClassName;
        string   Description;
        string   DeviceID;
        boolean  ErrorCleared;
        string   ErrorDescription;
        datetime InstallDate;
        uint32   LastErrorCode;
        string   Manufacturer;
        uint32   MaxNumberControlled;
        string   Name;
        string   PNPDeviceID;
        uint16   PowerManagementCapabilities[];
        boolean  PowerManagementSupported;
        uint16   ProtocolSupported;
        string   Status;
        uint16   StatusInfo;
        string   SystemCreationClassName;
        string   SystemName;
        datetime TimeOfLastReset;
        '''
        wmi = win32com.client.GetObject("winmgmts:")
        for USBDevices in wmi.InstancesOf("Win32_USBController"):
            descriptions.update({USBDevices.Name:USBDevices.Description})
            
        return descriptions

    def WMIDateStringToDate(self,dtmDate):
        if dtmDate[4] == 0:
            strDateTime = dtmDate[5] + "/"
        else:
            strDateTime = dtmDate[4] + dtmDate[5] + "/"

        if dtmDate[6] == 0:
            strDateTime = strDateTime + dtmDate[7] + "/"
        else:
            strDateTime = strDateTime + dtmDate[6] + dtmDate[7] + "/"
            strDateTime = (
                strDateTime
                + dtmDate[0]
                + dtmDate[1]
                + dtmDate[2]
                + dtmDate[3]
                + " "
                + dtmDate[8]
                + dtmDate[9]
                + ":"
                + dtmDate[10]
                + dtmDate[11]
                + ":"
                + dtmDate[12]
                + dtmDate[13]
            )
        return strDateTime

    def scan_Available_Ports(self):
        """
        Returns Available Serial Ports
        """
        Ports={}
        available = []
        for iii in range(256):
            try:
                sss = serial.Serial('COM'+str(iii))
                #print("Port:{} Name:{} open:{}".format(sss.portstr,sss.name,sss.is_open))            
                available.append((sss.portstr))   
                #print(sss.)         
                Ports.update({sss.portstr:{"Name:":sss.name,"Open":sss.is_open,"Available":True,"Settings":sss.get_settings()}})
                sss.close()   # explicit close 'cause of delayed GC in java
            except serial.SerialException as eee:           
                try:
                    if str(eee).find('Access is denied.') != -1:
                        Ports.update({'COM'+str(iii):{"Name:":'COM'+str(iii),"Open":True,"Available":False,"Settings":None}})                    
                except:
                    pass           
                pass
        return Ports,available

    def Split_text(self,separator,line):
            alist=[]
            count=0
            try:                                      
                mf =re.split(separator,line)                               
                x=re.findall(separator,line)
            except:
                mf = None
                
            try:
                if mf is not None:                  
                    for item in mf:                                                       
                        alist.append(item)                    
                    if x is not None:
                        count=len(x)     
                else:
                    alist.append(line)
            except Exception as e:                        
                alist=[]
                pass
            return alist,count              

    def find_serial_devices(self,serial_matcher="",showAll=False):
        """
        Finds a list of USB devices where the serial number (partially) matches the given string.
        :param str serial_matcher (optional):
            only device IDs starting with this string are returned
        :rtype: List[str]
        """
        #https://learn.microsoft.com/en-us/windows/win32/cimwin32prov/win32-usbcontrollerdevice
        '''
        uint32                NegotiatedDataWidth;
        uint64                NegotiatedSpeed;
        uint16                AccessState;
        uint32                NumberOfHardResets;
        uint32                NumberOfSoftResets;
        CIM_USBController REF Antecedent;
        CIM_LogicalDevice REF Dependent;
        '''
        if WIN32COM_AVAILABLE==False:
            return []
        objWMIService = win32com.client.Dispatch("WbemScripting.SWbemLocator")
        objSWbemServices = objWMIService.ConnectServer(".", "root\\cimv2")
        items = objSWbemServices.ExecQuery("SELECT * FROM Win32_USBControllerDevice")   
        #for item in items:
        #    print (item.AccessState) 
        #    print (item.Dependent) 
        if showAll==False:    
            ids = (item.Dependent.strip('"')[-8:] for item in items)
        else:
            ids=[]
            for item in items:
                sl,_=self.Split_text('"',item.Dependent)
                #print(sl)
                if len(sl)>1:
                    ids.append(sl[1])
        if serial_matcher != "":
            return [e for e in ids if e.startswith(serial_matcher)]
        else:
            return [e for e in ids]
        
    def get_devices_serial_tools(self):
        """
        class serial.tools.list_ports.ListPortInfo
        This object holds information about a serial port. It supports indexed access for backwards compatibility, as in port, desc, hwid = info.
        device:        Full device name/path, e.g. /dev/ttyUSB0. This is also the information returned as first element when accessed by index.
        name:        Short device name, e.g. ttyUSB0.
        description:        Human readable description or n/a. This is also the information returned as second element when accessed by index.
        hwid:        Technical description or n/a. This is also the information returned as third element when accessed by index.
        USB specific data, these are all None if it is not a USB device (or the platform does not support extended info).
        vid:        USB Vendor ID (integer, 0...65535).
        pid:        USB product ID (integer, 0...65535).
        serial_number:        USB serial number as a string.
        location:        USB device location string (“<bus>-<port>[-<port>]...”)
        manufacturer:        USB manufacturer string, as reported by device.
        product:        USB product string, as reported by device.
        interface:        Interface specifc description, e.g. used in compound USB devices.
        """
        devlist=list_comports()
        devices={}
        for iii,dev in enumerate(devlist):           
            print(dev)  
            #print(type(dev.pid))
            if isinstance(dev.pid,int):
                pid=dev.pid
            else:
                pid=0
            if isinstance(dev.vid,int):
                vid=dev.vid
            else:
                vid=0
            devdict={"device":dev.device,
                     "name":dev.name,
                     "description":dev.description,
                     "hwid":dev.hwid,
                     "vid":vid,
                     "pid":pid,
                     "serial_number":dev.serial_number,
                     "location":dev.location,
                     "manufacturer":dev.manufacturer,
                     "product":dev.product,
                     "interface":dev.interface,
                     }
            devices.update({iii:devdict})
            #print(dev.name," hwid:",dev.hwid," vid:",hex(vid)," pid:",hex(pid)," SerNo:",dev.serial_number, " Manufacturer:",dev.manufacturer," Product:",dev.product)
        return devices

class SerialBus(BusABC):
    """
    Enable basic can communication over a serial device.
    .. note:: See :meth:`~_recv_internal` for some special semantics.
    """

    def __init__(
        self,
        channel: str,
        baudrate: int = 115200,
        timeout: float = 0.1,
        rtscts: bool = False,
        *args,
        **kwargs,
    ) -> None:
        """
        :param channel:
            The serial device to open. For example "/dev/ttyS1" or
            "/dev/ttyUSB0" on Linux or "COM1" on Windows systems.
        :param baudrate:
            Baud rate of the serial device in bit/s (default 115200).
            .. warning::
                Some serial port implementations don't care about the baudrate.
        :param timeout:
            Timeout for the serial device in seconds (default 0.1).
        :param rtscts:
            turn hardware handshake (RTS/CTS) on and off
        """
        if not channel:
            raise ValueError("Must specify a serial port.")

        self.channel_info = f"Serial interface: {channel}"
        self._ser = serial.serial_for_url(
            channel, baudrate=baudrate, timeout=timeout, rtscts=rtscts
        )

        super().__init__(channel, *args, **kwargs)

    def shutdown(self) -> None:
        """
        Close the serial interface.
        """
        self._ser.close()

    def send(self, msg: Message, timeout: Optional[float] = None) -> None:
        """
        Send a message over the serial device.
        :param msg:
            Message to send.
            .. note:: Flags like ``extended_id``, ``is_remote_frame`` and
                      ``is_error_frame`` will be ignored.
            .. note:: If the timestamp is a float value it will be converted
                      to an integer.
        :param timeout:
            This parameter will be ignored. The timeout value of the channel is
            used instead.
        """
        # Pack timestamp
        try:
            timestamp = struct.pack("<I", int(msg.timestamp * 1000))
        except struct.error:
            raise ValueError("Timestamp is out of range")

        # Pack arbitration ID
        try:
            arbitration_id = struct.pack("<I", msg.arbitration_id)
        except struct.error:
            raise ValueError("Arbitration ID is out of range")

        # Assemble message
        byte_msg = bytearray()
        byte_msg.append(0xAA)
        byte_msg += timestamp
        byte_msg.append(msg.dlc)
        byte_msg += arbitration_id
        byte_msg += msg.data
        byte_msg.append(0xBB)

        # Write to serial device
        self._ser.write(byte_msg)

    def _recv_internal(
        self, timeout: Optional[float]
    ) -> Tuple[Optional[Message], bool]:
        """
        Read a message from the serial device.
        :param timeout:
            .. warning::
                This parameter will be ignored. The timeout value of the channel is used.
        :returns:
            Received message and `False` (because no filtering as taken place).
            .. warning::
                Flags like is_extended_id, is_remote_frame and is_error_frame
                will not be set over this function, the flags in the return
                message are the default values.
        """
        try:
            rx_byte = self._ser.read()
            if rx_byte and ord(rx_byte) == 0xAA:

                s = self._ser.read(4)
                timestamp = struct.unpack("<I", s)[0]
                dlc = ord(self._ser.read())
                if dlc > 8:
                    raise CanError("received DLC may not exceed 8 bytes")

                s = self._ser.read(4)
                arbitration_id = struct.unpack("<I", s)[0]
                if arbitration_id >= 0x20000000:
                    raise CanError(
                        "received arbitration id may not exceed 2^29 (0x20000000)"
                    )

                data = self._ser.read(dlc)

                delimiter_byte = ord(self._ser.read())
                if delimiter_byte == 0xBB:
                    # received message data okay
                    msg = Message(
                        # TODO: We are only guessing that they are milliseconds
                        timestamp=timestamp / 1000,
                        arbitration_id=arbitration_id,
                        dlc=dlc,
                        data=data,
                    )
                    return msg, False

                else:
                    raise CanError(
                        f"invalid delimiter byte while reading message: {delimiter_byte}"
                    )

            else:
                return None, False

        except serial.SerialException as error:
            raise CanError("could not read from serial") from error

    def fileno(self) -> int:
        if hasattr(self._ser, "fileno"):
            return self._ser.fileno()
        # Return an invalid file descriptor on Windows
        return -1

    @staticmethod
    def _detect_available_configs() -> List[AutoDetectedConfig]:
        return [
            {"interface": "serial", "channel": port.device} for port in list_comports()
        ]
    


    if __name__ == "__main__":
        # devfinder=DeviceFinder()
        # drifinder=DriverFinder()
        # print("++++++++++++ get serial ports ++++++++++++++++++")
        # portlist=devfinder.Get_serial_ports()
        # print(portlist)
        # print("++++++++++++ Scanned devices ++++++++++++++++++")
        # ports,available=devfinder.scan_Available_Ports()
        # print("available: {}".format(available))
        # print("Scanned: {}".format(ports))
        # print("++++++++++++ find serial devices ++++++++++++++++++")
        # serlist=devfinder.find_serial_devices("",True) #All
        # print(serlist)
        # serlist=devfinder.find_serial_devices("LW") #Filtered
        # print(serlist)        
        # print("++++++++++++get Serial devices ++++++++++++++++++")
        # serialdev=devfinder.get_serial_descriptions()
        # print(serialdev)
        # print("++++++++++++get USBController   ++++++++++++++++++")
        # usbdev=devfinder.get_USBController_descriptions()
        # #Prints a lot of stuff
        # #print(usbdev)
        # print("++++++++++++ using pyusb   ++++++++++++++++++")
        # usbdev2=devfinder.get_usb_device()
        # print(usbdev2)
        # for iii in usbdev2:
        #     if isinstance(usbdev2[iii],usb.core.Device):
        #         print(iii,hex(int(usbdev2[iii].idVendor)),hex(int(usbdev2[iii].idProduct)))
        #         if usbdev2[iii].idVendor == 0xbfd: #kvaser
        #             print("kvaser device found at {}".format(iii))
        #             # product 1 channel : 0x30,
        #             # product 2 channel : 0x123,

        #             #print(usbdev2[iii])
        #         if usbdev2[iii].idVendor == 0x403: #USB2CAN/Lawicel/OTT
        #             if usbdev2[iii].idProduct == 0x6001: #USB2CAN/Lawicel
        #                 print("USB2CAN/Lawicel device found at {}".format(iii))
        #                 #print(usbdev2[iii])
        #             if usbdev2[iii].idProduct == 0xecd9: #OTT
        #                 print("OTT device found at {}".format(iii))
        #                 #print(usbdev2[iii])
        #         if usbdev2[iii].idVendor == 0x1248: #Vector prod 0x1050
        #             print("Vector device found at {}".format(iii))
        #             #print(usbdev2[iii])                
        #         if usbdev2[iii].idVendor == 0xc72: #Peak Can  0xc
        #             print("PCAN device found at {}".format(iii))
        #             #print(usbdev2[iii])                                        
        # print("++++++++++++ FTDI devices   ++++++++++++++++++")
        # FTDIdev=devfinder.get_FTDI_devices()
        # print(FTDIdev)
        # print("++++++++++++ serial tools   ++++++++++++++++++")
        # devlist=list_comports()
        # SerTooldev=devfinder.get_devices_serial_tools()
        # print(SerTooldev)
        # print("++++++++++++++++++++++++++++++++++++++++++++++")
        # print("################## Drivers ###################")
        # drivers=drifinder.get_drivers()
        # print(drivers)
        # print("##############################################")
        dm = get_device_manager()
        devices = []
        # devices = dm.list_all_devices()
        devices += dm.detect_tcpip([1,75],[80])
        # devices=dm.detect_ble()
        devices += dm.detect_ftdi()
        devices += dm.detect_visa()
        devices += dm.detect_serial()
        devices += dm.detect_usb()

        print("*"*33)
        for d in devices:
            print(f"[{d.type}] {d.friendly} {d.name} → {d.info}")

        
        