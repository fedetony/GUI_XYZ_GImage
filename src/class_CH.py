import os
import re
import logging
import fileinput
import yaml
#from types import *
import class_LogHandler
ap=class_LogHandler.get_appPath()
img_path=os.path.join(ap,"img")
config_path=os.path.join(ap,"config")

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
formatter=logging.Formatter('[%(levelname)s] (%(threadName)-10s) %(message)s')
ahandler=logging.StreamHandler()
ahandler.setLevel(logging.INFO)
ahandler.setFormatter(formatter)
log.addHandler(ahandler)

class Command_Handler:    
    def __init__(self,selected_interface_id,yaml_config_file=None,Required_actions=None):            
        self.__name__="CH"
        self.parenth = Parenthesees()

        # Forward all public methods from parenth to this instance
        for name in dir(self.parenth):
            if not name.startswith("_"):  # skip private/internal
                attr = getattr(self.parenth, name)
                if callable(attr):
                    setattr(self, name, attr)
        # init all dictionaries empty
        self.yaml_filename=None
        self._clear_actual_interface_dictionaries()
        self._clear_data_dictionaries()
        # Set id
        self.id=selected_interface_id
        # Set default required commands
        if Required_actions is None:
            self.Required_actions={'interfaceId','interfaceName'}
        else:
            self.Required_actions=set(Required_actions)
        self.Required_read={'interfaceId'}
        self.Required_interface={'interfaceId'}
        # Set filenames
        if self.set_yaml_file(yaml_config_file):
            if self.load_and_set_config_from_yaml(self.yaml_filename,True,True):
                self._set_actual_interface_dictionaries()
        # if self.Set_all_Filenames(configfilelist)==True:                     
        #     self.Setup_Command_Handler()
        #     self.Init_Read_Interface_Configurations()

    def set_as_default_yaml_file(self,filename,log_check=True):
        """Checks if file exists and sets it if it does

        Args:
            filename (str): file to be set
            log_check (bool, optional): log File setting. Defaults to True.

        Returns:
            bool: True if file was set.
        """
        if os.path.exists(filename):
            self.yaml_filename=filename
            self._logcheck(f"File {self.yaml_filename} set as configuration file!",log_check,'info')
            return True
        self._logcheck(f"File {filename} does not exist!",log_check,'error')       
        return False     

    def save_all_configs_to_yaml(self,filepath):
        """
        Stores All parallel dictionaries into a single YAML file.
        """
        data = {
            "actions": {
                "format": self.Configdata,
                "info": self.Configdata_info,
                "type": self.Configdata_type
            },
            "read": {
                "format": self.ReadConfigallids,
                "info": self.ReadConfigallids_info,
                "type": self.ReadConfigallids_type
            },
            "behavior": {
                "format": self.InterfaceConfigallids,
                "info": self.InterfaceConfigallids_info,
                "type": self.InterfaceConfigallids_type
            }
        }

        with open(filepath, "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True)
    

    def load_config_from_yaml(self,filepath):
        """
        Loads the YAML file and sets the dictionaries.
        """
        with open(filepath, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if data is None: 
            log.error(f"{filepath} YAML file is empty or invalid!")
            return None,None,None
        actions = data.get("actions", None)
        read = data.get("read", None)
        behavior = data.get("behavior", None)
        if actions is None: 
            log.error(f"In {filepath} YAML file: actions format are invalid!")
        if read is None: 
            log.error(f"In {filepath} YAML file: read formats are invalid!")
        if behavior is None: 
            log.error(f"In {filepath} YAML file: behavior formats are invalid!")
        return actions, read, behavior
    
    def load_and_set_config_from_yaml(self,filepath:str,check_required=False,log_check=True):
        """Loads the YAML file and sets the dictionaries. 
        Returns True if setting was completed.

        Args:
            filepath (str): yaml file with path
            check_required (bool, optional): check required commands are present. Defaults to False.
            log_check (bool, optional): Log all checking process if True, if False will log errors only. Defaults to True.

        Returns:
            bool: True if dictionaries with commands for all interfaces were set.
        """
        self._logcheck(f"Loading yaml file {filepath}",log_check,'info')
        actions, read, behavior = self.load_config_from_yaml(filepath)
        if actions is None or read is None or behavior is None:
            log.error(f"File {filepath} contains erros, could not be loaded!")
            return False
        if check_required:
            r_a,r_r,r_b=[self.Required_actions,self.Required_read,self.Required_interface]
        else:
            r_a,r_r,r_b=[None,None,None]
        if not self.check_yaml_config(actions, read, behavior,r_a, r_r, r_b,log_check):
            return False
        # set values if all is ok
        self.Configdata = actions.get("format", {})
        self.Configdata_info = actions.get("info", {})
        self.Configdata_type = actions.get("type", {})

        self.ReadConfigallids = read.get("format", {})
        self.ReadConfigallids_info = read.get("info", {})
        self.ReadConfigallids_type = read.get("type", {})

        self.InterfaceConfigallids = behavior.get("format", {})
        self.InterfaceConfigallids_info = behavior.get("info", {})
        self.InterfaceConfigallids_type = behavior.get("type", {})
        self.yaml_filename = filepath
        return True

    def _get_unique_id(self):
        """Return the next available unique interface ID as a string."""
        id_list = self.get_id_list()
        if id_list is None:
            return "0"

        used = set(id_list)
        new_id = 0
        while str(new_id) in used:
            new_id += 1
        return str(new_id)

    def _create_non_existing_interface(self, a_name):
        """Initialize all dictionaries with a single interface."""
        if self.get_id_list() is not None:
            log.error("Cannot create first interface: dictionaries are not empty!")
            return False

        new_id = self._get_unique_id()

        dict_list = [
            self.Configdata,
            self.Configdata_info,
            self.Configdata_type,
            self.ReadConfigallids,
            self.ReadConfigallids_info,
            self.ReadConfigallids_type,
            self.InterfaceConfigallids,
            self.InterfaceConfigallids_info,
            self.InterfaceConfigallids_type,
        ]

        for ddd in dict_list:
            ddd["interfaceId"] = [new_id]
            ddd["interfaceName"] = [a_name]

        # Add required commands with empty values
        for cmd in self.Required_actions:
            self.Configdata.setdefault(cmd, [""])
        for cmd in self.Required_read:
            self.ReadConfigallids.setdefault(cmd, [""])
        for cmd in self.Required_interface:
            self.InterfaceConfigallids.setdefault(cmd, [""])

        return True

    def get_id_list(self):
        """Returns the first encounter of intefaceId list in any of 9 dictionaries"""
        for d in (
            self.Configdata,
            self.Configdata_info,
            self.Configdata_type,
            self.ReadConfigallids,
            self.ReadConfigallids_info,
            self.ReadConfigallids_type,
            self.InterfaceConfigallids,
            self.InterfaceConfigallids_info,
            self.InterfaceConfigallids_type,
        ):
            ids = d.get("interfaceId")
            if ids is not None:
                return ids
        return None


    def add_interface(self,a_name,clone_id=None):
        """Adds an interface to existing interfaces. If there are no interfaces will create a new one with minimum required commands empty.

        Args:
            a_name (str): Name of new interface
            clone_id (any, optional): Adds a new interface cloned from the id. If None adds a new empty inteface. Defaults to None.
        Returns: 
            bool: True if added an interface.
        """
        id_list=self.get_id_list()
        if id_list is None:
            return self._create_non_existing_interface(a_name)
        else:
            if clone_id is None or clone_id not in id_list:
                return self._create_empty_interface(a_name)
            elif clone_id is not None and clone_id in id_list:
                return self._clone_interface(a_name,clone_id)
        return False
    
    def remove_interface(self,an_id):
        """Removes interface from dictionaries

        Args:
            an_id (any): id to remove

        Returns:
            bool: True if interface was removed
        """
        id_list = self.get_id_list()
        if id_list is None or an_id not in id_list:
            return False

        index = id_list.index(an_id)

        dict_list = [
            self.Configdata,
            self.Configdata_info,
            self.Configdata_type,
            self.ReadConfigallids,
            self.ReadConfigallids_info,
            self.ReadConfigallids_type,
            self.InterfaceConfigallids,
            self.InterfaceConfigallids_info,
            self.InterfaceConfigallids_type,
        ]

        for d in dict_list:
            for cmd, values in d.items():
                if isinstance(values, list) and len(values) > index:
                    values.pop(index)
        return True

            
    def _clone_interface(self, a_name, clone_id):
        """Makes a clone of interface

        Args:
            a_name (str): New name 
            clone_id (any): id of interface to be cloned
        """

        id_list = self.get_id_list()
        if id_list is None:
            return self._create_non_existing_interface(a_name)

        if clone_id not in id_list:
            return False

        clone_index = id_list.index(clone_id)
        new_id = self._get_unique_id()

        dict_list = [
            self.Configdata,
            self.Configdata_info,
            self.Configdata_type,
            self.ReadConfigallids,
            self.ReadConfigallids_info,
            self.ReadConfigallids_type,
            self.InterfaceConfigallids,
            self.InterfaceConfigallids_info,
            self.InterfaceConfigallids_type,
        ]

        for d in dict_list:
            for cmd, values in d.items():
                if cmd == "interfaceId":
                    values.append(new_id)
                elif cmd == "interfaceName":
                    values.append(a_name)
                else:
                    values.append(values[clone_index])

        return True
    
    def _create_empty_interface(self, a_name):
        """Creates an empty interface based on existing commands of other interfaces.

        Args:
            a_name (str): Name of interface

        Returns:
            bool: True if interface was created
        """
        id_list = self.get_id_list()
        if id_list is None:
            return self._create_non_existing_interface(a_name)

        new_id = self._get_unique_id()

        dict_list = [
            self.Configdata,
            self.Configdata_info,
            self.Configdata_type,
            self.ReadConfigallids,
            self.ReadConfigallids_info,
            self.ReadConfigallids_type,
            self.InterfaceConfigallids,
            self.InterfaceConfigallids_info,
            self.InterfaceConfigallids_type,
        ]

        for d in dict_list:
            for cmd, values in d.items():
                if not isinstance(values, list):
                    continue  # skip non-list entries (should not happen but safe)

                if cmd == "interfaceId":
                    values.append(new_id)
                elif cmd == "interfaceName":
                    values.append(a_name)
                else:
                    values.append("")  # empty value for new interface

        return True

    def get_section_subtype_of_command(self, command) -> tuple:
        """
        Returns the (section, subtype) where a command is found.
        If not found, returns (None, None).
        """

        mapping = [
            (self.Configdata,              "actions",  "format"),
            (self.Configdata_info,         "actions",  "info"),
            (self.Configdata_type,         "actions",  "type"),
            (self.ReadConfigallids,        "read",     "format"),
            (self.ReadConfigallids_info,   "read",     "info"),
            (self.ReadConfigallids_type,   "read",     "type"),
            (self.InterfaceConfigallids,   "behavior", "format"),
            (self.InterfaceConfigallids_info,"behavior","info"),
            (self.InterfaceConfigallids_type,"behavior","type"),
        ]

        for a_dict, section, subtype in mapping:
            if command in a_dict:
                return section, subtype

        return None, None

    
    @staticmethod
    def _get_subtype_from_command(command):
        """Gets the sutype in accordance to the command

        Args:
            command (str): command

        Returns:
            str: 'format', 'info', 'type'
        """
        if "_info" in command:
            return "info"
        elif "_type" in command:
            return "type"
        return "format"
    
    
    def _add_command(self, section:str, subtype:str, command:any,
                 values_list:list, filename:str=None, log_value:bool=False):
        """Adds a command to the specific dictionary for all interfaces.

        Args:
            section (str): 'actions', 'read', 'behavior'
            subtype (str): 'format', 'info', 'type'
            command (any): the command key
            values_list (list): list of values
            filename (str, optional): if given will save to yaml file. Defaults to None.
            log_value (bool, optional): log print the changes. Defaults to False.

        Returns:
            bool: command was added
        """
        id_list = self.get_id_list()
        if id_list is None:
            log.error("Can't create commands without an interface!")
            return False

        num_int = len(id_list)
        if len(values_list) != num_int:
            log.error(f"Number of interfaces ({num_int}) does not match values ({len(values_list)})!")
            return False

        # Update all values
        for an_id, new_value in zip(id_list, values_list):
            self._update_value(section, subtype, command, an_id, new_value, None, log_value)

        # Save once
        if filename:
            self.save_all_configs_to_yaml(filename)

        return True
    
    def _remove_command(self, command:any, filename:str=None, log_value:bool=False):
        """
        Removes a command from whichever dictionary it belongs to.
        
        Args:
            section (str): 'actions', 'read', 'behavior'
            subtype (str): 'format', 'info', 'type'
            command (any): the command key
            filename (str, optional): if given will save to yaml file. Defaults to None.
            log_value (bool, optional): log print the changes. Defaults to False.

        Returns:
            bool: command was removed
        """

        section, subtype = self.get_section_subtype_of_command(command)
        if not section:
            return False

        mapping = {
            "actions": {
                "format": self.Configdata,
                "info": self.Configdata_info,
                "type": self.Configdata_type
            },
            "read": {
                "format": self.ReadConfigallids,
                "info": self.ReadConfigallids_info,
                "type": self.ReadConfigallids_type
            },
            "behavior": {
                "format": self.InterfaceConfigallids,
                "info": self.InterfaceConfigallids_info,
                "type": self.InterfaceConfigallids_type
            }
        }
        target_dict = mapping[section][subtype]
        if command in target_dict:
            del target_dict[command]

            if log_value:
                log.info(f"Removed command '{command}' from {section}.{subtype}")

            if filename:
                self.save_all_configs_to_yaml(filename)

            return True

        return False
    
    def _update_value(self, section:str, subtype:str, command:any, an_id:any,
                  new_value:any, filename:str=None, log_value:bool=False):
        """
        Add or update the value of a specific command in the target dictionary.
        
        Args:
            section (str): 'actions', 'read', 'behavior'
            subtype (str): 'format', 'info', 'type'
            command (any): the command key
            an_id (any): id of interface
            new_value (any): replacement or new value
            filename (str, optional): if given will save to yaml file. Defaults to None.
            log_value (bool, optional): log print the changes. Defaults to False.
        """

        # Select dictionary
        mapping = {
            "actions": {
                "format": self.Configdata,
                "info": self.Configdata_info,
                "type": self.Configdata_type
            },
            "read": {
                "format": self.ReadConfigallids,
                "info": self.ReadConfigallids_info,
                "type": self.ReadConfigallids_type
            },
            "behavior": {
                "format": self.InterfaceConfigallids,
                "info": self.InterfaceConfigallids_info,
                "type": self.InterfaceConfigallids_type
            }
        }

        target_dict = mapping[section][subtype]
        index = self.get_interface_column_from_id(target_dict,an_id)

        # Update existing command
        if command in target_dict:
            old_value = target_dict[command][index]
            target_dict[command][index] = new_value

            if log_value:
                log.info(f"Replaced {command}({an_id})={old_value} with {new_value}")

        # Create new command
        else:
            num_cols = self.get_number_of_interfaces(self.Configdata)
            new_list = ['' for _ in range(num_cols)]
            new_list[index] = new_value
            target_dict[command] = new_list

            if log_value:
                log.info(f"Added {command}({an_id})={new_value}")

        # Save YAML if requested
        if filename:
            self.save_all_configs_to_yaml(filename)
                 

    def check_yaml_config(
        self, actions, read, behavior,
        required_actions=None, required_read=None, required_behavior=None,
        log_check=False
    ):
        """Checks the configuration on the yaml file

        Args:
            actions (dict):actions dictionary
            read (dict): read dictionary
            behavior (dict): behavior dictionary
            required_actions (set, optional): Set of required commands. Defaults to None.
            required_read (set, optional): Set of required commands. Defaults to None.
            required_behavior (set, optional): Set of required commands. Defaults to None.
            log_check (bool, optional): _description_. Defaults to False.

        Returns:
            bool: True if all checks passed
        """
        if log_check:
            log.info("Checking information:")

        # Basic presence checks
        if actions is None:
            self._logcheck("No action commands available!", log_check, 'error')
            return False
        if read is None:
            self._logcheck("No reading commands available!", log_check, 'error')
            return False
        if behavior is None:
            self._logcheck("No behavior commands available!", log_check, 'error')
            return False

        # Check interface count consistency across subtypes
        for subtype in ["format", "info", "type"]:
            a_num = self.get_number_of_interfaces(actions.get(subtype, {}))
            r_num = self.get_number_of_interfaces(read.get(subtype, {}))
            b_num = self.get_number_of_interfaces(behavior.get(subtype, {}))

            if not (a_num == r_num == b_num):
                self._logcheck(
                    f"Number of interfaces for subtype '{subtype}' mismatch: "
                    f"actions({a_num}), read({r_num}), behavior({b_num})",
                    log_check, 'error'
                )
                return False

        # Use the interface count from the "format" subtype
        num_int = self.get_number_of_interfaces(actions.get("format", {}))

        # Validate each section
        self._logcheck("Checking actions dictionary...", log_check, 'info')
        a_ok = self._do_data_checks(actions, num_int, required_actions, log_check)

        self._logcheck("Checking read dictionary...", log_check, 'info')
        r_ok = self._do_data_checks(read, num_int, required_read, log_check)

        self._logcheck("Checking behavior dictionary...", log_check, 'info')
        b_ok = self._do_data_checks(behavior, num_int, required_behavior, log_check)

        return a_ok and r_ok and b_ok

    def _do_data_checks(self, data, num_int, required,log_check=False):
        """Perform validation checks for all subtypes inside a section."""
        ok = True

        for subtype in ["format", "info", "type"]:
            subdict = data.get(subtype, {})

            # Missing or invalid subtype dictionary
            if not isinstance(subdict, dict): 
                log.error(f"Missing or invalid subtype '{subtype}' dictionary!") 
                return False
            
            ok &= self.check_num_actions_in_data(subdict)
            self._logcheck(f"\tChecking {subtype}: Number of actions\t{str(ok).upper()}", log_check, 'info')
            ok &= self.check_id_in_data(subdict, num_int)
            self._logcheck(f"\tChecking {subtype}: ID in Data       \t{str(ok).upper()}", log_check, 'info')
            ok &= self.check_number_formats_in_data(subdict)
            self._logcheck(f"\tChecking {subtype}: Number of formats\t{str(ok).upper()}", log_check, 'info')

            # Required commands only apply to "format"
            if subtype == "format":
                ok &= self.check_req_actions_are_in_data(required, subdict)
                self._logcheck(f"\tChecking {subtype}: Required actions\t{str(ok).upper()}", log_check, 'info')

        return ok

    def _logcheck(self,msg:str,logcheck=True,logtype='info'):
        """logger helper function
        """
        if logcheck:
            if logtype=='info':
                log.info(msg)
            elif logtype=='warning':
                log.warning(msg)   
            elif logtype=='error':
                log.error(msg)
            elif logtype=='debug':
                log.error(msg) 
            elif logtype=='print':
                print(msg)    

    def set_yaml_file(self,yaml_file:str=None)->bool:
        """Checks for existance of the file , if deos not exist will try to set the default file

        Args:
            yaml_file (str, optional): Filename. Defaults to None.

        Returns:
            bool: True if a configuration file exists.
        """
        default_yaml=os.path.join(config_path,'default_config.yml')
        if yaml_file is None:
            yaml_file=default_yaml
        if self.set_as_default_yaml_file(yaml_file):
            return True
        if self.set_as_default_yaml_file(default_yaml):
            log.info("Default configuration set!")
            return True
        log.error("No configuration files available!")    
        return False   
    
    def set_new_interface(self,interface_id,force_refresh=False,log_check=True):
        """Sets a new interface with interface id if id is different than actual used id.

        Args:
            interface_id (any): id of interface to set
            force_refresh (bool, optional): reloads even if the id is same (makes load refresh). Defaults to False.
        """
        if self.id!=interface_id or force_refresh:
            self.set_id(interface_id)    
            if self.set_yaml_file(self.yaml_filename):
                if self.load_and_set_config_from_yaml(self.yaml_filename,True,log_check):
                    self._set_actual_interface_dictionaries()
    
    def set_id(self,selected_interface_id):
        """Sets new Id and refreshes Actual dictionaries

        Args:
            selected_interface_id (any): id to select
        """
        id_list=self.get_id_list()
        if id_list is None:
            return
        if selected_interface_id in id_list:
            self.id=str(selected_interface_id) 
            self._set_actual_interface_dictionaries()
    
    def join_datasets(self,data1,txtext1,data2,txtext2):
        datajoined={}
        for iii in data2:
            datajoined.update({iii+txtext2:data2[iii]})
        for iii in data1:
            datajoined.update({iii+txtext1:data1[iii]})
        return datajoined    

    def _set_actual_interface_dictionaries(self):
        """Sets self.id to Actual interface dictionaries"""
        self.Num_interfaces=self.get_number_of_interfaces(self.Configdata)

        self.Actual_Interface_Formats=self.get_interface_config(self.Configdata,self.id)
        self.Actual_Interface_FInfo=self.get_interface_config(self.Configdata_info,self.id)
        self.Actual_Interface_FTypes=self.get_interface_config(self.Configdata_type,self.id)

        self.Int_Config=self.get_interface_config(self.InterfaceConfigallids,self.id)
        self.Int_Config_info=self.get_interface_config(self.InterfaceConfigallids_info,self.id)                    
        self.Int_Config_type=self.get_interface_config(self.InterfaceConfigallids_type,self.id)

        self.Read_Config=self.get_interface_config(self.ReadConfigallids,self.id)
        self.Read_Config_info=self.get_interface_config(self.ReadConfigallids_info,self.id)
        self.Read_Config_type=self.get_interface_config(self.ReadConfigallids_type,self.id)
    
    def _clear_actual_interface_dictionaries(self):
        """Clears the actual interface dictionaries"""
        self.Num_interfaces=0

        self.Actual_Interface_Formats={}
        self.Actual_Interface_FInfo={}
        self.Actual_Interface_FTypes={}

        self.Int_Config={}
        self.Int_Config_info={}                    
        self.Int_Config_type={}

        self.Read_Config={}
        self.Read_Config_info={}
        self.Read_Config_type={}
    
    def _clear_data_dictionaries(self):
        """Clears all ids dictionaries
        """
        self.Configdata = {}
        self.Configdata_info = {}
        self.Configdata_type = {}

        self.ReadConfigallids = {}
        self.ReadConfigallids_info = {}
        self.ReadConfigallids_type = {}

        self.InterfaceConfigallids = {}
        self.InterfaceConfigallids_info = {}
        self.InterfaceConfigallids_type = {}
        
    def check_id_in_Config(self,id):
        try:
            isok=False
            newid=str(id)
            idlist=self.Configdata['interfaceId']
            #print(idlist,' Desired id->',newid)
            if newid in idlist:
                isok=True
            if newid==self.id and isok==False:
                self.set_id(idlist[0])
                log.error('None existing Id changed to ', self.id)
                isok=True
        except Exception as e:
            log.error(e)
            log.error('Invalid Machine Id!!!!!')
            isok=False
            pass    
        return isok
    
    def check_id_in_data_config(self,data,id):
        '''
        checks id but does not revert if error found
        '''
        try:
            isok=False
            newid=str(id)
            idlist=data['interfaceId']
            #print(idlist,' Desired id->',newid)
            if newid in idlist:
                isok=True            
        except Exception as e:
            log.error(e)
            log.error('Id in data error!!!!!')
            isok=False
            pass    
        return isok
    

    def get_number_of_interfaces(self,data):
        """ Gets the amount of interfaces from 'interfaceId' key in data"""
        try:
            idlist=data['interfaceId']
            if isinstance(idlist,(list,tuple)):
                return len(idlist)
            else:  
                return 1
        except (TypeError,ValueError,KeyError) as eee:
            log.error(f'Undefined Number of interfaces: {eee}')
            return 0 

    def get_action_format_from_id(self, data, action, interface_id):
        """
        Retrieve the value of a specific command (action) for a given interface ID.

        This function looks up:
        - the command name (`action`) inside the subtype dictionary `data`
        - the column index corresponding to `interface_id`
        - and returns the value stored at that column

        Args:
            data (dict): A subtype dictionary (e.g., actions["format"]).
            action (str): The command name to retrieve.
            interface_id (any): The interface ID whose value should be returned.

        Returns:
            any or None:
                The value stored for the given action and interface ID,
                or None if the action does not exist, the ID is not found,
                or the data is malformed.
        """
        if not isinstance(data, dict):
            return None

        # Command must exist
        aclist = data.get(action)
        if not isinstance(aclist, list):
            return None

        # Find the column for this interface ID
        idcol = self.get_interface_column_from_id(data, interface_id)
        if idcol is None:
            return None

        # Ensure index is valid
        if idcol < 0 or idcol >= len(aclist):
            return None

        return aclist[idcol]


    def get_interface_column_from_id(self, data, interface_id) -> int:
        """
        Return the column index corresponding to the given interface ID.

        Args:
            data (dict): A dictionary containing an 'interfaceId' list.
            interface_id (any): The ID to search for.

        Returns:
            int: The index of the interface ID, or None if not found.
        """
        if not isinstance(data, dict):
            log.error("get_interface_column_from_id: data is not a dictionary")
            return None

        id_list = data.get("interfaceId")
        if not isinstance(id_list, list):
            log.error("get_interface_column_from_id: 'interfaceId' is missing or not a list")
            return None

        target = str(interface_id)

        for index, an_id in enumerate(id_list):
            if str(an_id) == target:
                return index

        # Not found
        return None

        

    def get_interface_config(self,data:dict,interface_id)->dict:
        """Returns the dictionary with the data for specific interface id"""
        dataint={}    
        col_num=self.get_interface_column_from_id(data,interface_id) 
        num_inter=self.get_number_of_interfaces(data)
        if col_num != None and col_num<num_inter:  
            for key,value in data.items():
                alist=value        
                dataint[key]=alist[col_num]
        return dataint       
        
    def get_number_of_actions(self):
        """Number of commands in action dictionary"""
        return self.get_number_of_actions_in_data(self.Actual_Interface_Formats)

    def get_number_of_actions_in_data(self,data:dict):
        """Number of commands in data dictionary"""
        if isinstance(data,dict):
            return len(list(data.keys()))    

    def get_number_of_actual_interface_formats(self,cri=0):
        """Number of actions=0, read=1, behavior=2 commands in actual interface"""
        if cri==1:
            return self.get_number_of_actions_in_data(self.Read_Config)
        if cri==2:
            return self.get_number_of_actions_in_data(self.Int_Config)    
        return self.get_number_of_actions_in_data(self.Actual_Interface_Formats)    

    # def Load_command_config_from_file(self,filename=None,Logopen=False,typeofload=0):      
    #     '''
    #     typeofload=-1 loads all
    #     typeofload=0 loads actions
    #     typeofload=1 loads info
    #     typeofload=2 loads type
    #     ''' 
    #     if filename is None: 
    #         filename=self.filename
    #     data={}
    #     if filename is not None:            
    #         if Logopen==True:
    #             log.info('Opening:'+filename)
    #         try:                
    #             with open(filename, 'r') as yourFile:
    #                 #self.plaintextEdit_GcodeScript.setText(yourFile.read())        #textedit
    #                 linelist=yourFile.readlines() #makes list of lines  
    #             data=self.Get_Command_Config_Data_From_List(linelist,typeofload)     
    #             #if typeofload==1:
    #             #    print(data)                                           
    #             yourFile.close()                
    #         except Exception as e:
    #             log.error(e)
    #             log.info("Command Configuration File could not be read!")
    #     return data        
    
    # def Get_Command_Config_Data_From_List(self,linelist,typeofload=0):
    #     data={}
    #     '''
    #     interfaceId in any typeofload

    #     typeofload=-1 loads all
    #     typeofload=0 loads actions
    #     typeofload=1 loads info (except interfaceId)
    #     typeofload=2 loads type (except interfaceId)
    #     '''
    #     for line in linelist:
    #         #log.info(line)          
    #         Nomismatch=self.check_one_Parenthesees(line,IniP='<',EndP='>')  
    #         lastchar=''
    #         actionname=''
    #         item=''
    #         lineinfolist=[]
    #         countnum=0
    #         regextxt=''
    #         isregex=False
    #         for achar in line:
    #             if achar=='#' and countnum==0:                    
    #                 break
    #             if achar=='r' and lastchar=='<':
    #                regextxt=='r'
    #             if achar=="'" and lastchar=='r' and isregex==False:
    #                 isregex=True
    #                 regextxt=regextxt+achar
    #             elif achar=="'" and isregex==True:
    #                 isregex=False    
                
    #             if (achar =='<' or achar=='>') and isregex==True:
    #                 Nomismatch=True
    #                 #item=item+achar
    #             if achar =='<' and isregex==False:
    #                 #print(countnum)
    #                 item=''
    #                 countnum=countnum+1
    #             elif achar=='>' and isregex==False:
    #                 lastchar=achar    
    #                 if countnum==1:
    #                     actionname=item
    #                 else:
    #                     lineinfolist.append(item)
    #             elif achar=='_' and lastchar=='>':
    #                 lastchar=achar 
    #             else:    
    #                 item=item+achar
    #             lastchar=achar                       
    #         if actionname!='': 
    #             if Nomismatch==False:
    #                 log.info('Parenthesees <> Mismatch in:'+actionname)
    #             #log.info('action:'+actionname)   
    #             #print(lineinfolist)
    #             isinfo=False
    #             istype=False
    #             isid=False
    #             if '_info' in actionname:
    #                 isinfo=True
    #             if '_type' in actionname:
    #                 istype=True    
    #             if 'interfaceId' == actionname:                     
    #                 isid=True   
    #             if 'interfaceId_info' == actionname or 'interfaceId_type' == actionname:    
    #                 isid=True
    #             if isid==True:
    #                 data.update({actionname:list(lineinfolist)})
    #             else:            
    #                 if typeofload==-1: # loads all
    #                     data.update({actionname:list(lineinfolist)})     
    #                 if typeofload==0 and isinfo==False and istype==False: # loads actions
    #                     data.update({actionname:list(lineinfolist)})                             
    #                 if typeofload==1 and isinfo==True and istype==False: # loads info                                               
    #                     if 'interfaceId' not in actionname:                                     
    #                         actionname=actionname.replace('_info','')
    #                         data.update({actionname:list(lineinfolist)})
    #                 if typeofload==2 and isinfo==False and istype==True: # loads type
    #                     if 'interfaceId' not in actionname:                                                                 
    #                         actionname=actionname.replace('_type','')
    #                         data.update({actionname:list(lineinfolist)})                                     
    #     return data    

    def getGformatforAction(self,action):
        ActionFormat=None
        try:            
            ActionFormat=self.Actual_Interface_Formats[action]
        except:
            pass
        return ActionFormat

    def getGformatforActiondataid(self,data,action,id):
        ActionFormat=None
        try:       
            formatlist=data[action]              
            if self.check_id_in_data_config(data,id)==True:   
                idcol=self.get_interface_column_from_id(data,id)
                if idcol is not None:
                    ActionFormat=formatlist[idcol]
        except:
            pass
        return ActionFormat

    def getGformatforActionid(self,action,id):
        ActionFormat=None
        try:       
            formatlist=self.Configdata[action]  
            if self.check_id_in_Config(id)==True:   
                idcol=self.get_interface_column_from_id(self.Configdata,id)
                if idcol is not None:
                    ActionFormat=formatlist[idcol]
        except:
            pass
        return ActionFormat
    
    def getGformatforReadactionid(self,action,id):
        ActionFormat=None
        try:       
            formatlist=self.ReadConfigallids[action]  
            if self.check_id_in_Config(id)==True:   
                idcol=self.get_interface_column_from_id(self.ReadConfigallids,id)
                if idcol is not None:
                    ActionFormat=formatlist[idcol]
        except:
            pass
        return ActionFormat

    def getGformatforIntactionid(self,action,id):
        ActionFormat=None
        try:       
            formatlist=self.InterfaceConfigallids[action]  
            if self.check_id_in_Config(id)==True:   
                idcol=self.get_interface_column_from_id(self.InterfaceConfigallids,id)
                if idcol is not None:
                    ActionFormat=formatlist[idcol]
        except:
            pass
        return ActionFormat    

    def getListofAnyactionsindata(self,data,exceptlist=[]):        
        alist=[]
        for action in data:
            if action not in exceptlist:
                alist.append(action)
        return alist

    def getListofActions(self,exceptlist=[]): 
        return self.getListofAnyactionsindata(self.Actual_Interface_Formats,exceptlist)       

    def getListofReadactions(self,exceptlist=[]):        
        return self.getListofAnyactionsindata(self.Read_Config,exceptlist)                             
    
    def getListofInterfaceactions(self,exceptlist=[]):        
        return self.getListofAnyactionsindata(self.Int_Config,exceptlist)                             

    def num_groups(self,match):
        if match is not None:
            return len(match.groups())
        else:
            return 0 

    def Format_Number_of_formatspecifiers(self,aFormat):   
        aFormat=str(aFormat)     
        NS=0
        NSC=0
        txtlist,NSC=self.Split_text(r'\%\%',aFormat)        
        txtlist,NS=self.Split_text(r'\%',aFormat)
        amounts=[NS-NSC,NSC]
        return amounts

    def get_text_split_separatorfromregex(self,regex_sep):
        ppp=re.findall(regex_sep,'[({<>})]')
        if len(ppp)>0:
            return ppp[0] #separate first
        else:
            return regex_sep
    
    def Format_Get_optionlist_parameterlist(self,aFormat):
        aFormat=str(aFormat)
        minnumoptions=0
        optionslist,Numoptions=self.Format_which_Inside_Parenthesees(aFormat)
        for option in optionslist:
            if '&&' in option:
                minvaluelist,Numminval=self.Format_which_Inside_Parenthesees(option,r'\(',r'\)') #in [] 
                minop=option
                if Numminval>0:
                    minnumoptions=int(minvaluelist[0])
                else:
                    minnumoptions=1
        paramlist=[]            
        for option in optionslist:                
            varoptlist,Numspeciopt=self.Format_which_Inside_Parenthesees(option,r'\{',r'\}') #in [] 
            for jjj in varoptlist: 
                paramlist.append(jjj)    
        # remove &&(#) option
        oplist=[]
        for jjj in optionslist:
            if '&&' not in jjj:
                oplist.append(jjj)    
        optionslist=oplist                    
        return optionslist,paramlist,minnumoptions


    def Format_Get_main_Command(self,aFormat,Numoptions=None):
        if Numoptions==None:
            optionslist,Numoptions=self.Format_which_Inside_Parenthesees(aFormat)
        if Numoptions==0:
            return aFormat
        else:
            txt=str(aFormat)  
            sTxtlist = txt.split('[',1) #separate first
            stxt=sTxtlist[0]
            return stxt
    
    def Format_select_options_ored_parameters(self,aFormat,Parameters):
        aFormat=str(aFormat)
        orsplit,Norsplit=self.Split_text(r'\]\|\|\[',aFormat)
        if Norsplit>0:
            newFormat=aFormat            
            for iii in range(len(orsplit)):
                #print(str(iii)+'-->'+newFormat)                
                split1=newFormat.split(']||[',1)
                #print(split1)
                if len(split1)>1:
                    before=split1[0]+']'
                    after='['+split1[1]
                else:
                    break                        
                beflistop,Numbefopt=self.Format_which_Inside_Parenthesees(before)
                aftlistop,Numaftopt=self.Format_which_Inside_Parenthesees(after)
                varlistb,Numspecimain=self.Format_which_Inside_Parenthesees(beflistop[Numbefopt-1],r'\{',r'\}')
                Isonlistb=self.check_all_Parameters_are_in_list(varlistb,Parameters)
                varlista,Numspecimain=self.Format_which_Inside_Parenthesees(aftlistop[0],r'\{',r'\}')
                Isonlista=self.check_all_Parameters_are_in_list(varlista,Parameters) 
                if Isonlistb==False and Isonlista==False:
                    if '&&' not in beflistop[Numbefopt-1]:
                        before=before.replace('['+beflistop[Numbefopt-1]+']','')
                    else:    
                        if '&&' not in aftlistop[0]:
                            after=after.replace('['+aftlistop[0]+']','')    
                elif Isonlistb==True and Isonlista==False:                    
                    after=after.replace('['+aftlistop[0]+']','')                         
                elif Isonlistb==False and Isonlista==True:                                            
                    before=before.replace('['+beflistop[Numbefopt-1]+']','')           
                elif Isonlistb==True and Isonlista==True:
                    if '&&' not in aftlistop[0]:
                        after=after.replace('['+aftlistop[0]+']','')    
                newFormat=before+after                            
                    
            return newFormat                
        else:
            return aFormat
    
    def Format_replace_actions(self,aFormat):
        aFormat=str(aFormat)
        varlist,Numvars=self.Format_which_Inside_Parenthesees(aFormat,r'\{',r'\}') 
        action_list=self.getListofActions()
        newFormat=aFormat
        try:
            for var in varlist:
                if 'char(' in var:
                    vlist,Numv=self.Format_which_Inside_Parenthesees(var,r'\(',r'\)')                     
                    try:
                        if Numv>0:
                            valstr=vlist[0]
                            if '0x' in valstr:                                
                                hex_str=valstr                                
                                hex_int = int(hex_str, base=16)                                  
                                int_int=int(hex_int)
                                fff=chr(int_int)                                                          
                            else:                                
                                fff=chr(int(valstr))
                    except Exception as e:            
                        log.error(e)  
                        log.error('format replace actions')
                        fff=''
                        pass
                    if fff is not None:    
                        newFormat=newFormat.replace('{'+var+'}',fff)    
                for action in action_list:                    
                    if action in var: #action==var: 
                        vlist,Numv=self.Format_which_Inside_Parenthesees(var,r'\(',r'\)') 
                        if Numv>0:                        
                            fff=self.get_action_format_from_id(self.Configdata,action,vlist[0])
                            #print('here1:'+str(fff))
                        else:
                            #print(action)
                            fff=self.get_action_format_from_id(self.Configdata,action,self.id)    
                            #print('here2:'+str(fff))
                        if fff is not None:    
                            if 'char(' in fff:
                                fff='{'+fff+'}'
                            newFormat=newFormat.replace('{'+var+'}',fff)
        except Exception as e:            
            log.error(e)  
            log.error('Format Replace actions!')                       
            newFormat=aFormat
            pass                     
        return newFormat

    def Get_Gcode_for_Action(self,action,Parameters={},Parammustok=True):
        Gcode=''
        paramok=False        
        if self.Is_action_in_Config(action)==True:
            aFormat=self.getGformatforAction(action)
            #print(aFormat)  
            paramok=self.check_Parameters_for_Action(action,Parameters)
            #print('Paramok=',paramok)
            if paramok==True or Parammustok==False:
                Gcode=self.Get_code(aFormat,Parameters)
        else:
            log.error('No action defined as '+action+' in configuration file!')    
        return Gcode,paramok    

    def Get_Gcode_for_Action_id(self,action,anId,Parameters={},Parammustok=True):
        Gcode=''
        paramok=False        
        if self.Is_action_in_Config(action)==True:
            aFormat=self.getGformatforActionid(action,anId)
            #print(aFormat)  
            paramok=self.check_Parameters_for_Action(action,Parameters)
            #print('Paramok=',paramok)
            if paramok==True or Parammustok==False:
                Gcode=self.Get_code(aFormat,Parameters)
        else:            
            log.error('No action defined as '+action+' in configuration file!')    
        return Gcode,paramok   

    def Get_Gcode_for_Actionparamsfound(self,actionparamsfound,anId,Parammustok=True):
        Gcode=''
        paramok=False        
        actionline=actionparamsfound['_action_code_']
        actionline=self.Add_Id_to_actionFormat(actionline,anId)
        #print('Get gcode for Actionparams->',actionline)
        for action in actionparamsfound:
            if action !='_action_code_':
                if self.Is_action_in_Config(action)==True:
                    aFormat=self.getGformatforActionid(action,anId)
                    #print(aFormat)  
                    Parameters=actionparamsfound[action]
                    paramok=self.check_Parameters_for_Action(action,Parameters,anId)
                    #print('Paramok=',paramok)
                    if paramok==False and Parammustok==True:
                        log.warning('Wrong Parameters for ID:'+anId+' action:'+action)
                        break
                    if paramok==True or Parammustok==False:
                        aGcode=self.Get_code(aFormat,Parameters)
                        actionline=actionline.replace('{'+action+'('+anId+')}',aGcode)                        
                else:
                    paramok=False                    
                    log.error('No action defined as '+action+' in configuration file!')  
                    break
        Gcode=actionline
        return Gcode,paramok 

    def Get_code(self,aFormat,Parameters):
        aFormat=str(aFormat)        
        try:
            countnumoptions=0
            Numvarleft=1   
            newFormat=aFormat         
            while Numvarleft>0:            
                newFormat=self.Format_replace_actions(newFormat)
                newFormat=self.Format_select_options_ored_parameters(newFormat,Parameters)        
                optionslist,Numoptions=self.Format_which_Inside_Parenthesees(newFormat)
                The_code=''
                MCommand=self.Format_Get_main_Command(newFormat,Numoptions)
                varlist,Numspecimain=self.Format_which_Inside_Parenthesees(MCommand,r'\{',r'\}') #in []                        
                astr=MCommand
                #areallparams=self.check_all_Parameters_are_in_list(varlist,Parameters,True)   #Log when missing parameter in main
                areallparams=self.check_all_Parameters_are_in_list(varlist,Parameters)   
                if areallparams==True:
                    params=self.Get_only_the_Parameters_in_list(varlist,Parameters)
                    if Numspecimain>0:
                        astr=MCommand.format(**params)
                        #print(astr)
                    else:
                        astr=MCommand
                The_code=newFormat.replace(MCommand,astr)        
                minnumoptions=0        
                minop=None
                for option in optionslist:
                    if '&&' in option:
                        minvaluelist,Numminval=self.Format_which_Inside_Parenthesees(option,r'\(',r'\)') #in [] 
                        minop=option
                        if Numminval>0:
                            minnumoptions=int(minvaluelist[0])
                        else:
                            minnumoptions=1
                for option in optionslist:                
                    varoptlist,Numspeciopt=self.Format_which_Inside_Parenthesees(option,r'\{',r'\}') #in [] 
                    isoptparam=self.check_all_Parameters_are_in_list(varoptlist,Parameters)
                    optstr=''
                    if isoptparam==True:                
                        params=self.Get_only_the_Parameters_in_list(varoptlist,Parameters)                
                        if Numspeciopt>0:
                            optstr=option.format(**params)
                            astr=astr+optstr                    
                            countnumoptions=countnumoptions+1
                    if minop is option:
                        if countnumoptions>=minnumoptions:
                            The_code=The_code.replace('['+minop+']','')                                    
                    The_code=The_code.replace('['+option+']',optstr)            
                varcode,Numvarleft=self.Format_which_Inside_Parenthesees(The_code,r'\{',r'\}')            
                #log.info('Required '+ str(minnumoptions)+' Option parameters, '+str(countnumoptions)+' found!')  
                #self.countnumoptions=countnumoptions      
                #if Numvarleft>0:            
                #    The_code=self.Get_code(The_code,Parameters,countnumoptions)
                newFormat=The_code    
                            
                #countnumoptions=self.countnumoptions
            if countnumoptions<minnumoptions:
                log.error('Minimum '+ str(minnumoptions)+' Option parameters are Required: '+str(countnumoptions)+' found! '+str(minnumoptions-countnumoptions)+' missing!')        
        
        except Exception as e:            
            log.error(e)  
            log.error('Get Code!')                       
            #The_code=''
            pass        
        return The_code    

    def check_all_Parameters_are_in_list(self,varlist,Parameters,elog=False):
        isinparams=True
        for var in varlist:
            isinparams=False                
            for param in Parameters:            
                if var==param:
                    isinparams=True
                    break   
            if isinparams==False:
                if elog==True:
                    log.error('Missing parameter:'+var)
                break                                  
        return isinparams

    def Get_only_the_Parameters_in_list(self,varlist,Parameters):        
        Pardict={}
        #print(Parameters)
        for var in varlist:            
            for param in Parameters:            
                if var==param:
                    Pardict.update({var: Parameters[param]})           
                    break        
        #print(Pardict)                                                 
        return  Pardict  

    def Get_list_of_all_parameters_in_interface(self,interface_id):
        action_list=self.getListofActions()
        allParams=[]
        for action in action_list:
            ParamsReca=self.Get_Parameters_Needed_for_action(action,interface_id)
            for ParaR in ParamsReca:
                if ParaR not in allParams:
                    allParams.append(ParaR) 
        return allParams           
    
    def Get_Parameters_Needed_for_action(self,action,interface_id):
        Params={}
        if self.Is_action_in_Config(action)==False:
            log.error('action missing to get needed Parameters!')
            return Params
        aFormat=self.get_action_format_from_id(self.Configdata,action,interface_id)
        Params=self.Get_Parameters_Needed_for_Format(aFormat) 
        return Params

    def Get_Parameters_Needed_for_Format(self,aFormat):
        aFormat=str(aFormat)
        Params={}                
        newFormat=''
        count=0
        while aFormat!=newFormat:
            if count>0:
                aFormat=newFormat
            newFormat=self.Format_replace_actions(aFormat)        
            count=count+1            
            if count>20:
                aFormat=newFormat
        #print(newFormat)        
        allvarlist,Numallvar=self.Format_which_Inside_Parenthesees(newFormat,r'\{',r'\}')          
        opvarlist,atleast=self.Get_option_list(newFormat)

        for avar in allvarlist:
            if avar in opvarlist:
                Params.update({avar: 'optional' })
                for aaa in atleast:
                    if avar in aaa:
                        Params.update({avar: 'optional'+aaa[1] })
                        break
            else:
                Params.update({avar: 'required' })    
        return Params

    def Is_action_in_Config(self,action):
        alist=self.getListofActions()
        if action in alist:
            return True
        else:
            return False    

    def check_Parameters_for_Action(self,action,Parameters,anId=None):   
        if anId==None:
            anId=self.id
        if self.Is_action_in_Config(action)==False:
            return False
        RequiredParams=self.Get_Parameters_Needed_for_action(action,anId)     
        minimum_required=0
        minimum_oprequired=0
        for reqParam in RequiredParams:
            if '&&' in RequiredParams[reqParam]:
                oplistmin,Numopmin=self.Format_which_Inside_Parenthesees(RequiredParams[reqParam],r'\(',r'\)') 
                for opjjj in oplistmin:
                        minimum_oprequired=int(opjjj)             
            if 'required' in RequiredParams[reqParam]:           
                minimum_required=minimum_required+1
        minimum_req_total=minimum_required+minimum_oprequired            
        if minimum_req_total==0:
            return True
        required_found=0
        optional_found=0    
        for reqParam in RequiredParams:
            if 'required' in RequiredParams[reqParam]: 
                if reqParam in Parameters:
                    required_found=required_found+1
                else:
                    return False    
            if 'optional' in RequiredParams[reqParam]: 
                if reqParam in Parameters:
                    optional_found=optional_found+1
        if required_found==minimum_required and optional_found>=minimum_oprequired:
            return True
        return False
    
    def check_Parameters_for_Format(self,aFormat,Parameters):     
        #print('Format checking...')      
        RequiredParams=self.Get_Parameters_Needed_for_Format(aFormat)     
        minimum_required=0
        minimum_oprequired=0
        for reqParam in RequiredParams:
            if '&&' in RequiredParams[reqParam]:
                oplistmin,Numopmin=self.Format_which_Inside_Parenthesees(RequiredParams[reqParam],r'\(',r'\)') 
                for opjjj in oplistmin:
                        minimum_oprequired=int(opjjj)             
            if 'required' in RequiredParams[reqParam]:           
                minimum_required=minimum_required+1
        minimum_req_total=minimum_required+minimum_oprequired            
        if minimum_req_total==0:
            return True
        required_found=0
        optional_found=0    
        for reqParam in RequiredParams:
            if 'required' in RequiredParams[reqParam]: 
                if reqParam in Parameters:
                    required_found=required_found+1
                else:
                    return False    
            if 'optional' in RequiredParams[reqParam]: 
                if reqParam in Parameters:
                    optional_found=optional_found+1
        if required_found==minimum_required and optional_found>=minimum_oprequired:
            return True
        return False

    def check_number_formats_in_data(self, data):
        """
        Ensure that every command in the subtype dictionary has a value list
        matching the number of interfaces.

        Args:
            data (dict): A subtype dictionary.

        Returns:
            bool: True if all commands have correct list lengths, False otherwise.
        """
        num_inter = self.get_number_of_interfaces(data)
        if num_inter is None or num_inter == 0:
            return True  # nothing to validate

        ok = True
        for key, values in data.items():
            if not isinstance(values, list):
                log.error(f"Command '{key}' has invalid value type (expected list).")
                ok = False
                continue

            if len(values) < num_inter:
                missing = num_inter - len(values)
                log.error(f"Command '{key}' is missing {missing} interface value(s).")
                ok = False

        return ok

    def check_id_in_data(self, data, min_interfaces=1):
        """Validate the 'interfaceId' list inside a subtype dictionary."""

        idlist = data.get("interfaceId")
        if idlist is None:
            log.error("No 'interfaceId' defined in configuration file!")
            return False

        num_inter = self.get_number_of_interfaces(data)
        if num_inter is None or num_inter < min_interfaces:
            log.error(f"At least {min_interfaces} interfaces must be defined in 'interfaceId'")
            return False

        seen = set()
        for ids in idlist:
            if ids in seen:
                log.error(f"Repeated id {ids} in 'interfaceId'. Unique id is required!")
                return False
            seen.add(ids)

        return True

    def check_num_actions_in_data(self,data):                    
        numactions=self.get_number_of_actions_in_data(data)
        if numactions<1:
            log.error('No actions found in File!')
            return False
        return True    

    def check_req_actions_are_in_data(self, required, data):
        """
        Verify that all required commands exist in the 'format' subtype dictionary.

        Args:
            required (list or None): List of required command names.
            data (dict): The 'format' subtype dictionary.

        Returns:
            bool: True if all required commands are present, False otherwise.
        """
        if required is None:
            return True

        if not isinstance(data, dict):
            log.error("Invalid data structure while checking required commands.")
            return False

        ok = True
        for cmd in required:
            if cmd not in data:
                log.error(f"Missing required command: {cmd}")
                ok = False

        return ok
        
    
    def check_num_actions_in_data(self, data):
        """
        Ensure that the subtype dictionary contains at least one command.

        Args:
            data (dict): A subtype dictionary (format/info/type).

        Returns:
            bool: True if at least one command exists, False otherwise.
        """
        if not isinstance(data, dict):
            log.error("Invalid data structure: expected a dictionary.")
            return False

        num_actions = self.get_number_of_actions_in_data(data)
        if num_actions < 1:
            log.error("No commands found in this subtype dictionary.")
            return False

        return True

    
    def check_id_match_configs(self, data1, data2):
        """
        Verify that two subtype dictionaries have matching 'interfaceId' lists.

        Args:
            data1 (dict): First subtype dictionary.
            data2 (dict): Second subtype dictionary.

        Returns:
            bool: True if both contain identical interfaceId lists, False otherwise.
        """
        id1 = data1.get("interfaceId")
        id2 = data2.get("interfaceId")

        if id1 is None or id2 is None:
            log.error("Missing 'interfaceId' in one or both subtype dictionaries.")
            return False

        if len(id1) != len(id2):
            log.error("Mismatch in number of interface IDs between configurations.")
            return False

        # Check that all IDs match (order does not matter)
        if set(id1) != set(id2):
            log.error("Interface ID sets do not match between configurations.")
            return False

        return True


    def fill_parameters(self,parnamelist,parvallist):
        numpar=len(parnamelist)
        numval=len(parvallist)
        if numpar!=numval:
            numpar=min(numpar,numval)
            numval=numpar            
        param={}    
        if numpar>0:
            parlist={}
            for iii in range(numpar):
                parlist.update({parnamelist[iii]:parvallist[iii]})
            allparams=self.Get_list_of_all_parameters_in_interface(self.id)            
            try:
                for par in parnamelist:
                    if par in allparams:
                        param.update({par:parlist[par]})
            except:
                pass
        return param    
    
    def Get_list_of_all_parameters_all_interfaces(self):
        '''
        Returns all parameters in all actions. No read no General Interface parameters.
        '''
        allid=self.getGformatforAction('interfaceId')
        allparams=[]
        for ids in allid:
            aparams=self.Get_list_of_all_parameters_in_interface(ids)
            for ppp in aparams:
                if ppp not in allparams:
                    allparams.append(ppp)
        return allparams    

    def Get_option_list(self,aFormat):
        aFormat=str(aFormat)
        optionslist,Numoptions=self.Format_which_Inside_Parenthesees(aFormat) #in []
        opvarlist=[]        
        atleast=[]                
        addatleast=False
        for option in optionslist:  
            if '&&' in option:
                addatleast=True   
                optxt=option
            varoptlist,Numspeciopt=self.Format_which_Inside_Parenthesees(option,r'\{',r'\}') #in []             
            for opjjj in varoptlist:                
                if addatleast==True:       
                    atleast.append([opjjj,optxt])                   
                opvarlist.append(opjjj)
        return opvarlist,atleast  

    
    def get_regex_codes_to_find_parameters(self,aFormat):
        aFormat=str(aFormat)
        # ([XYZ][^\sXYZ]+) will match in any order parameters XYZ with or without spaces from gcode
        newFormat=self.Format_replace_actions(aFormat)        
        allparams=self.Get_list_of_all_parameters_all_interfaces() 
        opvarlist,atleast=self.Get_option_list(newFormat)                
        Parameters={}
        foundparameters=[]
        #Emptyreplace={}
        for param in allparams:            
            Parameters.update({param:'(.*)'})
            foundparameters.append(param)
            #Emptyreplace.update({param:''})
        justoptxt=''
        justoplist=[]
        for opiii in opvarlist:
            if '&&' not in opiii:
                aoptxt=self.Get_code(opiii,Parameters)
                aoptxt=aoptxt.replace('(.*)','')
                justoptxt=justoptxt+aoptxt
                justoplist.append(aoptxt.strip(' '))

        ch=chr(92)  # character \      
        justoptxt=justoptxt.replace(' ',ch+'s',1)        
        justoptxt=justoptxt.replace(' ','')          
        #print(justoptxt)
        #print(justoplist)
        
        varandval='(['+justoptxt+'][^'+ch+'s'+justoptxt+']+)'
        if '*' in justoptxt:
            #varandval='(.+)'
            allval='[;(\s]{1}(.+)' #comment type anything after first space or ; or (
        else:
            varandval='(['+justoptxt+'][^'+ch+'s'+justoptxt+']+)'
            allval='['+justoptxt+']([^'+ch+'s'+justoptxt+']+)'
        allvar='(['+justoptxt+'])'
        P_opread={'all_var_txt':justoptxt,'var_list':justoplist,'num_var':len(justoplist),'all_var_val':varandval,'all_val':allval,'all_var':allvar,'paramslist':foundparameters}
        for optxtiii in justoplist:
            if '*' in optxtiii:
                P_opread.update({optxtiii:'(.+)'})
            else:
                P_opread.update({optxtiii:'['+optxtiii+']([^'+ch+'s'+justoptxt+']+)'})
        '''        
        newFormat=newFormat.replace(ch,ch+ch)                               
        newFormat=newFormat.replace('||','?')         
        newFormat=newFormat.replace('.',ch+'.') 
        newFormat=newFormat.replace('^',ch+'^')                   
        newFormat=newFormat.replace('$',ch+'$')                       
        regexGcode=self.Get_code(newFormat,Parameters)        

        for iii in range(len(justoplist)):
            atxt='['+justoptxt+']'
            regexGcode=regexGcode.replace(justoplist[iii]+'(.*)',atxt+'(.*)')                                
        regexGcode=regexGcode.replace(' ',ch+'s?')
        return regexGcode
        '''    
        return P_opread    

    def get_main_code_from_gcode(self,Gcode,interface_id):
        '''
        Search all actions gcode format excluding optional parameters to match the gcode string
        '''
        allactions=self.getListofActions(exceptlist=['interfaceId','interfaceName'])
        if interface_id is None:
            interface_id=self.id
        foundcodeslist=[]  
        foundactionslist=[]  
        for action in allactions:
            aFormat=self.get_action_format_from_id(self.Configdata,action,interface_id)
            aFormat=self.Format_replace_actions(aFormat)
            ParamsNeed=self.Get_Parameters_Needed_for_Format(aFormat)
            Maincmd=self.Format_Get_main_Command(aFormat)
            for ppp in ParamsNeed:
                if 'required' in ParamsNeed[ppp]:
                    Maincmd=Maincmd.replace('{'+ppp+'}','')            
            Maincmd_strip=Maincmd.strip()            
            if Maincmd_strip!='':                
                stripfound=False
                if Maincmd_strip in Gcode:
                    stripfound=True                
                if Maincmd in Gcode:
                    foundcodeslist.append(Maincmd)        
                    foundactionslist.append(action)
                elif Maincmd not in Gcode and stripfound==True:
                    foundcodeslist.append(Maincmd_strip)          
                    foundactionslist.append(action)    
        return foundcodeslist,foundactionslist
    
    def Add_Id_to_actionFormat(self,aFormat,anId):        
        '''
        Replaces only actions and adds the corresponding id to the format.
        {action}->{action(id)}
        {action(xx)}->{action(id)}
        Returns the format.
        '''
        varalist,Numa=self.Format_which_Inside_Parenthesees(aFormat,r'\{',r'\}')             
        if Numa>0:
            actionlist=self.getListofActions(['interfaceId','interfaceName'])            
            for actpar in varalist:
                if 'char(' not in actpar:
                    plist,Nump=self.Format_which_Inside_Parenthesees(actpar,r'\(',r'\)')
                    if Nump>0:                                         
                        #actpars=actpar.replace('('+plist[0]+')','('+str(anId)+')')
                        actpare=actpar.replace('('+plist[0]+')','')
                        if actpare in actionlist:
                            aFormat=aFormat.replace('{'+actpar+'}','{'+actpare+'('+str(anId)+')}')  
                    else:
                        if actpar in actionlist:
                            aFormat=aFormat.replace('{'+actpar+'}','{'+actpar+'('+str(anId)+')}') 
                
        return aFormat

    def get_parameters_from_Gcode(self,Gcode,actionlist,interface_id,logerr=False):
        '''
        returns actions and parameters found in the Gcode
        '''
        actionparamsfound={}
        for action in actionlist:
            Params={}
            aFormat=self.get_action_format_from_id(self.Configdata,action,interface_id)                        
            #ParamsNeeded=self.Get_Parameters_Needed_for_action(action,interface_id)    
            aFormat=self.Add_Id_to_actionFormat(aFormat,interface_id)
            P_opread=self.get_regex_codes_to_find_parameters(aFormat)   
            #print('CH get parameters from Gcode->',Gcode,aFormat,P_opread)         
            if P_opread['num_var']==0:
                actionparamsfound.update({action:Params})
            if P_opread['num_var']>0:
                mg=re.search(P_opread['all_var_val'],Gcode)
                
                try:
                    numfound=len(mg.groups())                    
                    if numfound>0:                        
                        nmplist=P_opread['num_var']                              
                        mplist=P_opread['var_list']                           
                        for iii in range(nmplist):                            
                            var=mplist[iii]                                
                            #print(var)                  
                            par=re.search(P_opread[var],Gcode)
                            try:                                                        
                                Params.update({var : par.group(1)})   
                                #print(var,par.group(1))                                     
                            except:
                                pass                                                                
                    actionparamsfound.update({action:Params})                    
                except Exception as e:
                    if logerr==True:
                        log.error(e) 
                        log.error('Parameters from Gcode!')                     
                    pass
        replace=False
        if len(actionparamsfound)>1:
            for apf in actionparamsfound:
                idgcode,isok=self.Get_Gcode_for_Action_id(apf,interface_id,actionparamsfound[apf],True)
                if isok==True:
                    testgcode=Gcode.replace(idgcode,'')
                    if testgcode=='':
                        # if it matches exactly one of the codes when there are more than one then returns only that one
                        newapf={apf:actionparamsfound[apf]}
                        replace=True
                        break
        if replace==True:
            actionparamsfound=newapf                

        return actionparamsfound        

    def get_action_from_gcode(self,Gcode,interface_id=None):    
        '''
        returns dictionary with {action:parameters} found in the Gcode for id given        
        _action_code_ key holds the action code line        
        '''    
        actionparamsfound={}
        if Gcode != None or Gcode != '':
            #allactions=self.getListofActions(exceptlist=['interfaceId','interfaceName'])
            if interface_id is None:
                interface_id=self.id            
            foundcodeslist,foundactionslist=self.get_main_code_from_gcode(Gcode,interface_id)
            #print('foundMain->',foundactionslist)
            if len(foundcodeslist)==0: #when no Main code but just parameters
                #already seached inside all parameters in get_main_code_from_gcode
                #actionparamsfound=self.get_parameters_from_Gcode(Gcode,allactions,interface_id)
                actionparamsfound={}                
            else:
                actionparamsfound=self.get_parameters_from_Gcode(Gcode,foundactionslist,interface_id)     
            actioncode=self.get_action_code(actionparamsfound,Gcode,interface_id)   
            actioncode=self.Add_Id_to_actionFormat(actioncode,interface_id) 
            actionparamsfound.update({'_action_code_':actioncode})
        return actionparamsfound                   

    def get_action_code(self,actionsparamsfound,Gcode,interface_id):
        '''
        Returns the Gcode line replacing it for the actions matched for specified id.        
        '''
        modGcode=Gcode
        #print('get action code actionsparamsfound ->',actionsparamsfound)
        for actpar in actionsparamsfound:            
            aFormat=self.getGformatforActionid(actpar,interface_id)
            aFormat=self.Add_Id_to_actionFormat(aFormat,interface_id)
            aFormat=self.Format_replace_actions(aFormat)
            #print('Here 1',modGcode,aFormat,actpar)
            if aFormat in Gcode:
                modGcode=modGcode.replace(aFormat,'{'+actpar+'}')
                #print('Here 2',modGcode,aFormat,actpar)
            else:                    
                #print('Here 3')
                MainComm=self.Format_Get_main_Command(aFormat)
                modGcode=modGcode.replace(MainComm,'{'+actpar+'}')
                Parneed=self.Get_Parameters_Needed_for_action(actpar,interface_id)
                aFormat=self.Add_Id_to_actionFormat(aFormat,interface_id)
                P_get=self.get_regex_codes_to_find_parameters(aFormat)
                #print('inside getaction code->',aFormat,P_get)
                for sss in range(P_get['num_var']):
                    Ismsgtext=False
                    for par in P_get['var_list']:
                        if '*' in par:
                            Ismsgtext=False
                            break
                    if Ismsgtext==False:    
                        mp=re.search(P_get['all_var_val'],modGcode)
                        try:
                            nmp=len(mp.groups())
                            #print('Here found',mp)
                            for iii in range(nmp):
                                pareval=mp.group(iii+1)
                                modGcode=modGcode.replace(pareval,'')
                                #print('Here 5')
                        except:
                            pass        
                    else:
                        modGcode='{'+actpar+'}'
        while '  ' in modGcode: #replace all double spaces to single spaces
            modGcode=modGcode.replace('  ',' ')                            
        return modGcode    

    
    def action_code_match_action(self,action_code,action,justin=False):
        atxt='{'+str(action)+'}'
        if  atxt in action_code:
            if action_code.strip() is atxt:
                return True
            return justin    
        else:
            return False    
                 
    def check_format(self,aFormat,Parameters={}): 
        '''
        Checks parenthesees and if there is parameters the required parameters
        ''' 
        #print('check start')      
        isok= self.check_Parenthesees_in_one_Format(aFormat)
        #print(isok,len(Parameters),Parameters)
        if isok==True and len(Parameters)>0 :
            #print('checking parameters')
            isok=self.check_Parameters_for_Format(aFormat,Parameters)                 
        return isok

    def get_all_info_from_Format(self,aFormat):
        aFormat=str(aFormat)
        All_data={}
        
        All_data.update({'Format':aFormat})
        regexcmd='' 
        # if regex code
        isregex=False
        if "r'" in aFormat:
            #rlist=self.get_list_in_between_txt(aFormat,"'","'")
            #p2list,Nump2=self.Format_which_Inside_Parenthesees(p1,r"r\'",r'\]')
            rm=re.search("r'(.*)'",aFormat)
            try:                
                regexcmd=rm.group(1)
                isregex=True
            except:
                isregex=False
                pass    
        #print(regexcmd)        
            
        
        if isregex==True:
            MainComm=regexcmd
            newFormat=aFormat.replace(MainComm,'')
            optionslist,paramlist,minnumoptions=self.Format_Get_optionlist_parameterlist(newFormat)
            
        else:
            isok=self.check_format(aFormat)
            if isok==False:
                log.error('Bad Format Entangled Parenthesees')
                return All_data
            MainComm=self.Format_Get_main_Command(aFormat)
            newFormat=self.Format_replace_actions(aFormat)
            optionslist,paramlist,minnumoptions=self.Format_Get_optionlist_parameterlist(newFormat)   
                
            #Parameters={}
            #for iii in paramlist:
            #    Parameters.update({iii})
            #newFormat=self.Format_select_options_ored_parameters(newFormat,Parameters)        
        
        isored=False        
        if '||' in newFormat:
            isored=True        
        ParamsNeed=self.Get_Parameters_Needed_for_Format(newFormat)           
        All_data.update({'ReqOpParamsdict':ParamsNeed})        
        All_data.update({'IsOred':isored})    
        All_data.update({'IsRegex':isregex})
        All_data.update({'MainCommand':MainComm})
        self.Get_only_the_Parameters_in_list
        All_data.update({'RegexCommand':regexcmd})  
        #if '<' in  regexcmd: 
        #    print(regexcmd)
        All_data.update({'processedFormat':newFormat})

        All_data.update({'Parameterlist':paramlist})
        All_data.update({'Optionlist':optionslist})
        All_data.update({'minRequiredOptions':minnumoptions})
        
        opttxtlist=self.Get_option_text(paramlist,optionslist)
        All_data.update({'Optiontxtlist':opttxtlist})

        P_regex=self.get_regex_codes_to_find_parameters(newFormat)         
        All_data.update({'AllOptiontxt':P_regex['all_var_txt']})
        All_data.update({'lenOptionlist':P_regex['num_var']}) 
        All_data.update({'AllParametersavailable':P_regex['paramslist']})         

        #print(optionslist)
        #print(paramlist)

        #print(P_regex['paramslist'])
        return All_data
    
    def get_read_fast_info_from_Format(self,aFormat):  
        '''
        Instead of all info only the minimum to make the read.
        '''      
        All_data={}                
        regexcmd=''         
        isregex=False
        if "r'" in aFormat:            
            rm=re.search("r'(.*)'",aFormat)
            try:                
                regexcmd=rm.group(1)
                isregex=True
            except:
                isregex=False
                pass     
        All_data.update({'IsRegex':isregex})                   
        if isregex==False:            
            return All_data            
        else:
            MainComm=regexcmd
            newFormat=aFormat.replace(MainComm,'')
            optionslist,paramlist,minnumoptions=self.Format_Get_optionlist_parameterlist(newFormat)
        
        All_data.update({'RegexCommand':regexcmd})
        All_data.update({'Parameterlist':paramlist})
        opttxtlist=self.Get_option_text(paramlist,optionslist)
        All_data.update({'Optiontxtlist':opttxtlist})
        
        return All_data

    def Get_option_text(self,paramlist,optionlist):
        txtoplist=[]        
        for op in optionlist:
            for ppp in paramlist:            
                if '{'+ppp+'}' in op:
                    optiontxt=op.replace('{'+ppp+'}','')                    
                    txtoplist.append(optiontxt)   
        return txtoplist      

    def read_from_format(self,receivedline,aFormat,logerr=False):
        ParamRead={}
        if aFormat=='' or receivedline=='':
            All_data={'IsRegex':False}
        else:
            All_data=self.get_read_fast_info_from_Format(str(aFormat))
        success_=-1
        if All_data['IsRegex']==True:
            rgexcmd=All_data['RegexCommand']
            rmatch=re.search(rgexcmd,receivedline)
            success_=0
            try:
                num_match=len(rmatch.groups())
                paramlist=All_data['Parameterlist']
                optiontxtlist=All_data['Optiontxtlist']                
                nump=len(paramlist)
                numo=len(optiontxtlist)
                if numo==nump:
                    for iii in range(numo):
                        opttxt=optiontxtlist[iii]
                        ppp=paramlist[iii]
                        mmm=int(opttxt.strip())
                        ParamRead.update({ppp:rmatch.group(mmm)})
                        success_=success_+1
            except Exception as e:
                if logerr==True:
                    log.error(e) 
                    log.error('Read From Format!') 
                pass
        ParamRead.update({'__success__':success_})  #-1 No regex format, 0 No matches in format, # of matches found          
        return ParamRead

    def replace_action_format_in_file(self, filename, anaction, a_new_value, anid, data, log_value=False):
        """
        Replace the value of an existing command for a specific interface ID.

        This function:
        - Locates the section/subtype where the command already exists
        - Updates only that specific value
        - Saves the YAML file if filename is provided

        Args:
            filename (str): YAML file path. If None, uses self.yaml_filename.
            anaction (str): Command name to update.
            a_new_value (any): New value to assign.
            anid (any): Interface ID whose column should be updated.
            data (dict): Unused (kept for backward compatibility).
            log_value (bool): If True, logs the replacement.

        Returns:
            bool: True if replaced, False otherwise.
        """
        replaced = False

        if filename is None:
            filename = self.yaml_filename

        if any(x is None for x in (a_new_value, anaction, anid)):
            return replaced

        if anaction == "":
            return replaced

        section, subtype = self.get_section_subtype_of_command(anaction)
        if not section or not subtype:
            if log_value:
                log.error(f"Command {anaction} does not exist!")
            return replaced

        self._update_value(section, subtype, anaction, anid, a_new_value, filename, log_value)
        return True
    
        

    # def get_new_line_old_line_for_action(self,data,anaction,aFormat,anid,typeofload=0):
    #     idlist=data['interfaceId']
    #     #oldFormat=self.get_action_format_from_id(data,anaction,anid)       
    #     if anaction == None or anaction == '':
    #         return '','' 
    #     newFormat=aFormat
    #     oldline='<'+anaction+'>'
    #     newline='<'+anaction+'>'        
    #     if typeofload!=-1:
    #         if '_info' in anaction:
    #             anaction=anaction.replace('_info','')
    #         if '_type' in anaction:
    #             anaction=anaction.replace('_type','')    
    #     for ids in idlist:        
    #         oldFormat=self.get_action_format_from_id(data,anaction,ids)   
    #         if oldFormat==None:
    #             oldFormat=''             
    #         if str(ids) == str(anid):
    #             oldline=oldline+'_<'+oldFormat+'>'
    #             newline=newline+'_<'+newFormat+'>'                
    #         else:
    #             oldline=oldline+'_<'+oldFormat+'>'
    #             newline=newline+'_<'+oldFormat+'>'
    #     return oldline, newline

    def create_action_format_in_file(self, filename, anaction, a_new_value, anid,
                                 log_value=False, section='actions'):
        """
        Create or overwrite a command in the YAML configuration.

        If the command already exists:
            - It will be overwritten in its original section/subtype.
        If it does not exist:
            - The subtype is inferred from the command name.
            - The command is created in the given section.

        Args:
            filename (str): YAML file path. If None, uses self.yaml_filename.
            anaction (str): Command name to create or overwrite.
            a_new_value (any): Value to assign at the given interface ID.
            anid (any): Interface ID whose column should be updated.
            log_value (bool): If True, logs creation/overwrite.
            section (str): Default section ('actions') for new commands.

        Returns:
            bool: True if created/overwritten, False otherwise.
        """
        replaced = False

        if filename is None:
            filename = self.yaml_filename

        if any(x is None for x in (a_new_value, anaction, anid)):
            return replaced

        if anaction == "":
            return replaced

        old_section, subtype = self.get_section_subtype_of_command(anaction)

        if old_section and subtype:
            if log_value:
                log.warning(f"Command {anaction} already exists! Will be overwritten.")
            section = old_section
        else:
            subtype = self._get_subtype_from_command(anaction)

        self._update_value(section, subtype, anaction, anid, a_new_value, filename, log_value)
        return True


    def create_empty_action_in_file(self, filename, anaction, log_value=False, section='actions'):
        """
        Create a new command with empty values for all interfaces.

        If the command already exists:
            - It will be overwritten in its original section/subtype.

        Args:
            filename (str): YAML file path. If None, uses self.yaml_filename.
            anaction (str): Command name to create.
            log_value (bool): If True, logs creation/overwrite.
            section (str): Default section ('actions') for new commands.

        Returns:
            bool: True if created, False otherwise.
        """
        created = False

        if filename is None:
            filename = self.yaml_filename

        if anaction == "":
            return created

        old_section, subtype = self.get_section_subtype_of_command(anaction)

        if old_section and subtype:
            if log_value:
                log.warning(f"Command {anaction} already exists! Will be overwritten.")
            section = old_section
        else:
            subtype = self._get_subtype_from_command(anaction)

        # Use the first interface ID for initialization
        anid = self.get_id_list()[0]

        self._update_value(section, subtype, anaction, anid, '', filename, log_value)
        return True
    
    def delete_action_in_file(self, filename, anaction, data=None, log_value=False):
        """
        Delete a command from whichever section/subtype it belongs to.

        Args:
            filename (str): YAML file path. If None, uses self.yaml_filename.
            anaction (str): Command name to delete.
            data (dict): Unused (kept for backward compatibility).
            log_value (bool): If True, logs deletion.

        Returns:
            bool: True if deleted, False otherwise.
        """
        if filename is None:
            filename = self.yaml_filename

        if anaction == "":
            return False

        return self._remove_command(anaction,filename,log_value)
        

    # def Init_Read_Interface_Configurations(self,Reqactions_ic={'interfaceId'},Reqactions_ir={'interfaceId'},Logcheck=False): 
    #     self.Required_read=Reqactions_ir   
    #     self.Required_interface=Reqactions_ic
    #     try:            
    #         isok=self.check_command_config_file_Content(self.Interfacefilename,Reqactions_ic,False,Logcheck)
    #         if isok==True:
    #             self.InterfaceConfigallids=self.Load_command_config_from_file(filename=self.Interfacefilename,Logopen=False,typeofload=0)
    #             self.InterfaceConfigallids_info=self.Load_command_config_from_file(filename=self.Interfacefilename,Logopen=False,typeofload=1)                
    #             self.InterfaceConfigallids_type=self.Load_command_config_from_file(filename=self.Interfacefilename,Logopen=False,typeofload=2)
    #             isok=self.check_id_match_configs(self.Configdata,self.InterfaceConfigallids)
    #             #print(isok)
    #             if isok==True:
    #                 self.Int_Config=self.get_interface_config(self.InterfaceConfigallids,self.id)
    #                 self.Int_Config_info=self.get_interface_config(self.InterfaceConfigallids_info,self.id)                    
    #                 self.Int_Config_type=self.get_interface_config(self.InterfaceConfigallids_type,self.id)
    #                 #print(self.Int_Config)
    #                 #print(self.Int_Config_info)
    #         if isok==False:
    #             self.Int_Config={}
    #             self.Int_Config_info={}
    #             self.Int_Config_type={}
    #     except:
    #         self.InterfaceConfigallids={}  
    #         self.InterfaceConfigallids_info={}  
    #         self.InterfaceConfigallids_type={}  
    #         isok=False                               
    #         pass        
    #     isokic=isok
        
    #     try:            
    #         isok=self.check_command_config_file_Content(self.Readfilename,Reqactions_ir,False,Logcheck)
    #         if isok==True:
    #             self.ReadConfigallids=self.Load_command_config_from_file(filename=self.Readfilename,Logopen=False,typeofload=0)
    #             self.ReadConfigallids_info=self.Load_command_config_from_file(filename=self.Readfilename,Logopen=False,typeofload=1)
    #             self.ReadConfigallids_type=self.Load_command_config_from_file(filename=self.Readfilename,Logopen=False,typeofload=2)
    #             isok=self.check_id_match_configs(self.Configdata,self.ReadConfigallids)
    #             if isok==True:
    #                 self.Read_Config=self.get_interface_config(self.ReadConfigallids,self.id)
    #                 self.Read_Config_info=self.get_interface_config(self.ReadConfigallids_info,self.id)
    #                 self.Read_Config_type=self.get_interface_config(self.ReadConfigallids_type,self.id)
    #         if isok==False:
    #             self.Read_Config={}
    #             self.Read_Config_info={}
    #             self.Read_Config_type={}
    #     except:
    #         self.ReadConfigallids={}   
    #         self.ReadConfigallids_info={} 
    #         self.ReadConfigallids_type={} 
    #         isok=False         
    #         pass
    #     isokrc=isok
    #     return isokrc,isokic
    
    def create_new_interface_in_file(self, filename, newname='New Interface', cloneid=None, log_value: bool = True):
        """
        Create a new interface and save the updated configuration to a YAML file.

        This function:
        - Creates a new interface entry, either empty or cloned from an existing one.
        - Logs the operation if requested.
        - Saves the updated configuration to the YAML file.

        Args:
            filename (str): Path to the YAML file. If None, uses self.yaml_filename.
            newname (str): Name of the new interface. Defaults to 'New Interface'.
            cloneid (any, optional): If provided, the new interface is cloned from
                                    the interface with this ID. If None, an empty
                                    interface is created.
            log_value (bool): If True, logs the creation process.

        Returns:
            bool: True if the interface was created and saved, False otherwise.
        """
        self._logcheck(f'Creating {newname} interface cloned={cloneid is not None}', log_value, 'info')

        if not self.add_interface(newname, cloneid):
            return False

        if filename is None:
            filename = self.yaml_filename

        if filename is not None:
            self.save_all_configs_to_yaml(filename)

        return True


    def get_name_from_id(self, anid):
        """
        Retrieve the interface name corresponding to a given interface ID.

        Args:
            anid (any): The interface ID whose name should be returned.

        Returns:
            str or None: The name of the interface if found, otherwise None.
        """
        id_list = self.get_id_list()
        if id_list is None:
            return None

        if anid in id_list:
            index = self.get_interface_column_from_id(self.Configdata,anid)
            names = self.Configdata.get("interfaceName", [])
            if isinstance(names, list) and index < len(names):
                return names[index]

        return None


    def delete_interface_in_file(self, filename, anid, log_value: bool = True):
        """
        Remove an interface from all configuration dictionaries and save the result.

        This function:
        - Logs the removal request.
        - Removes the interface from all internal dictionaries.
        - Saves the updated configuration to the YAML file.

        Args:
            filename (str): Path to the YAML file. If None, uses self.yaml_filename.
            anid (any): The interface ID to remove.
            log_value (bool): If True, logs the removal process.

        Returns:
            bool: True if the interface was removed and saved, False otherwise.
        """
        self._logcheck(f'Removing {self.get_name_from_id(anid)} interface', log_value, 'info')

        if not self.remove_interface(anid):
            return False

        if filename is None:
            filename = self.yaml_filename

        if filename is not None:
            self.save_all_configs_to_yaml(filename)

        return True

    
    def get_info_type_from_id(self,data,action,anid):
        '''
        Returns the info id *(id) returns the correspondant id info
        '''
        try:
            infolist=data[action]            
            info=str(self.getGformatforActiondataid(data,action,anid))
            
        except Exception as e:
            #log.error(e)
            #log.error('get info type id')
            info=''
            pass
        #print('before:',info)
        if info == '':
            return info    
        readid=anid    
        #print('here ',readid)
        rm=re.search("[*]\((.*)\)",info)
        try:                
            readid=rm.group(1)                
        except:
            readid=anid
            pass  
        if readid!=anid:
            info=self.getGformatforActiondataid(data,action,readid)
        #print('after:',info)       
        return info        


class Parenthesees:
    """
    Utility class for validating and analyzing parentheses/brackets/braces
    in text formats. Supports (), [], {}, and arbitrary/multi-character
    delimiters via regex.
    """

    def __init__(self):
        # Cache for compiled regex patterns (optimization A)
        self._regex_cache = {}

    def _get_regex(self, pattern):
        """
        Get a compiled regex object from cache, compiling if necessary.
        """
        if pattern not in self._regex_cache:
            self._regex_cache[pattern] = re.compile(pattern)
        return self._regex_cache[pattern]

    def Split_text(self, separator, line):
        """
        Split a string using a regex separator and count occurrences.

        Parameters
        ----------
        separator : str
            Regex pattern used to split the text.
        line : str
            Input text.

        Returns
        -------
        tuple (list, int)
            - List of split segments.
            - Number of occurrences of the separator.
        """
        try:
            regex = self._get_regex(separator)
            parts = regex.split(line)
            count = len(regex.findall(line))
            return parts, count
        except Exception as e:
            log.error(e)
            log.error("split text")
            return [line], 0

    def Nums_Parenthesees(self, txt, IniP, EndP):
        """
        Count opening and closing parentheses/brackets/braces.

        Returns
        -------
        list [int, int]
            [number_of_opening, number_of_closing]
        """
        _, n_ini = self.Split_text(IniP, txt)
        _, n_end = self.Split_text(EndP, txt)
        return [n_ini, n_end]

    def check_one_Parenthesees(self, aFormat, IniP=r'\[', EndP=r'\]', logerr=True):
        """
        Check if a specific type of parentheses is balanced.

        Returns
        -------
        bool
            True if balanced, False otherwise.
        """
        aFormat = str(aFormat)
        try:
            inisep = self.get_text_split_separatorfromregex(IniP)
            endsep = self.get_text_split_separatorfromregex(EndP)

            n_ini, n_end = self.Nums_Parenthesees(aFormat, IniP, EndP)

            if n_ini != n_end:
                if logerr:
                    log.error(f'Bad Format {inisep} {endsep} in <{aFormat}>')
                return False
            return True

        except Exception:
            log.error(f'Bad Parenthesees Format {inisep} {endsep} in <{aFormat}>')
            return False

    def check_entangled_Parenthesees(self, txt, logerr=False):
        """
        Recursively check for correct nesting of {}, [], ().

        Returns
        -------
        bool
            True if nesting is valid, False otherwise.
        """
        p1 = self.Nums_Parenthesees(txt, r'\{', r'\}')
        p2 = self.Nums_Parenthesees(txt, r'\[', r'\]')
        p3 = self.Nums_Parenthesees(txt, r'\(', r'\)')

        # Basic mismatch
        if p1[0] != p1[1] or p2[0] != p2[1] or p3[0] != p3[1]:
            if logerr:
                log.error("Different amounts of opening and closing Parenthesees")
            return False

        # No parentheses at all
        if p1[0] == p2[0] == p3[0] == 0:
            return True

        # Recursive entanglement checks
        for ini, end in [(r'\{', r'\}'), (r'\[', r'\]'), (r'\(', r'\)')]:
            sublist, _ = self.Format_which_Inside_Parenthesees(txt, ini, end)
            for sub in sublist:
                if sub != txt:
                    if not self.check_entangled_Parenthesees(sub, False):
                        return False

        return True

    def check_Parenthesees_in_all_Formats(self, data):
        """
        Validate parentheses for all formats in a dictionary.

        Parameters
        ----------
        data : dict
            { action_name : [format1, format2, ...] }

        Returns
        -------
        bool
            True if all formats are valid.
        """
        allok = True

        for action, formats in data.items():
            for fmt in formats:
                if not self.check_one_Parenthesees(fmt, r'\[', r'\]', False):
                    log.error(f'Parenthesees Mismatch "[ ]" in action: {action} Format <{fmt}>')
                    allok = False
                if not self.check_one_Parenthesees(fmt, r'\(', r'\)', False):
                    log.error(f'Parenthesees Mismatch "( )" in action: {action} Format <{fmt}>')
                    allok = False
                if not self.check_one_Parenthesees(fmt, r'\{', r'\}', False):
                    log.error(f'Parenthesees Mismatch "{{ }}" in action: {action} Format <{fmt}>')
                    allok = False

        if allok:
            for action, formats in data.items():
                for fmt in formats:
                    if not self.check_entangled_Parenthesees(fmt, False):
                        log.error(f'Parenthesees Entangled {{[( }}]) in action: {action} Format <{fmt}>')
                        allok = False

        return allok

    def check_Parenthesees_in_one_Format(self, aFormat):
        """
        Validate parentheses for a single format string.

        Returns
        -------
        bool
            True if valid.
        """
        aFormat = str(aFormat)
        allok = True

        if not self.check_one_Parenthesees(aFormat, r'\[', r'\]', False):
            log.error(f'Parenthesees Mismatch "[ ]" in Format <{aFormat}>')
            allok = False
        if not self.check_one_Parenthesees(aFormat, r'\(', r'\)', False):
            log.error(f'Parenthesees Mismatch "( )" in Format <{aFormat}>')
            allok = False
        if not self.check_one_Parenthesees(aFormat, r'\{', r'\}', False):
            log.error(f'Parenthesees Mismatch "{{ }}" in Format <{aFormat}>')
            allok = False

        if allok:
            if not self.check_entangled_Parenthesees(aFormat, False):
                log.error(f'Parenthesees Entangled {{[( }}]) in Format <{aFormat}>')
                allok = False

        return allok

    def get_text_split_separatorfromregex(self, regex_sep):
        """
        Extract the literal character represented by a regex, if it matches
        one of a small set of known bracket-like characters.

        Returns
        -------
        str
            The literal character if found, otherwise the regex itself.
        """
        regex = self._get_regex(regex_sep)
        found = regex.findall('[({<>})]')
        return found[0] if found else regex_sep

    def Format_which_Inside_Parenthesees(self, aFormat, IniP=r'\[', EndP=r'\]'):
        """
        Extract all substrings inside a specific type of parentheses.

        IniP and EndP are regex patterns; the actual literal delimiters are
        resolved via get_text_split_separatorfromregex.

        Returns
        -------
        tuple (list, int)
            - List of inner substrings.
            - Number of such substrings.
        """
        aFormat = str(aFormat)
        try:
            inisep = self.get_text_split_separatorfromregex(IniP)
            endsep = self.get_text_split_separatorfromregex(EndP)

            items = self.get_list_in_between_txt(aFormat, inisep, endsep)
            return items, len(items)

        except Exception as e:
            log.error(e)
            log.error("Inside Parentheses")
            return [], 0

    def get_list_in_between_txt(self, txt:str, inis, ends):
        """
        Extract substrings between matching delimiters, supporting
        multi-character delimiters and nesting (optimization E).

        Parameters
        ----------
        txt : str
            Input text.
        inis : str
            Opening delimiter (literal string, not regex).
        ends : str
            Closing delimiter (literal string, not regex).

        Returns
        -------
        list of str
            All substrings found inside the given delimiters at depth 1.
        """
        alist = []
        depth = 0
        i = 0
        n = len(txt)
        start = None
        len_ini = len(inis)
        len_end = len(ends)

        # If delimiters are identical (rare but possible), we treat them as
        # toggling regions: inis == ends means "on/off" delimiter.
        same = (inis == ends)

        while i < n:
            if not same and txt.startswith(inis, i):
                depth += 1
                if depth == 1:
                    start = i + len_ini
                i += len_ini
                continue
            if not same and txt.startswith(ends, i):
                if depth > 0:
                    depth -= 1
                    if depth == 0 and start is not None:
                        alist.append(txt[start:i])
                        start = None
                i += len_end
                continue

            if same and txt.startswith(inis, i):
                # toggle mode
                if depth == 0:
                    depth = 1
                    start = i + len_ini
                else:
                    depth = 0
                    if start is not None:
                        alist.append(txt[start:i])
                        start = None
                i += len_ini
                continue

            i += 1

        return alist
     

            


            



   