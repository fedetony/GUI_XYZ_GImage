# plugins/machines/cnc_3axis_plugin.py

from gimage.plugins.plugin_machine_base import GImageMachineBase

class CNC3AxisMachine(GImageMachineBase):
    """
    CNC XYZ and spindle machine
    """
    name = "cnc_3axis" #must match the name in the machine combo

    def set_units(self):
        self.units = self.config.get_value(["machine","machine_units","value"]) or "mm"
        if self.units == "mm":
            return self.a_set('setUnitstomm')  # millimeters
        return self.a_set('setUnitstoinches')  # inches

    def home(self):
        return self.a_set('Home')

    def move_to(self,x=None,y=None,z=None,f=None,s=None,e=None,a=None,b=None,c=None,rapid=False):
        if rapid:
            cmd='rapidMove'
        else:     
            cmd='linearMove'
        parnamelist=[]
        parvallist=[]
        if x!=None:
            parnamelist.append('X')
            parvallist.append(x)
        if y!=None:
            parnamelist.append('Y')
            parvallist.append(y)
        if z!=None:
            parnamelist.append('Z')
            parvallist.append(z)  
        if a!=None:
            parnamelist.append('A')
            parvallist.append(a)
        if b!=None:
            parnamelist.append('B')
            parvallist.append(b) 
        if c!=None:
            parnamelist.append('C')
            parvallist.append(c)
        if e!=None:
            parnamelist.append('E')
            parvallist.append(e)
        if s!=None:
            parnamelist.append('S')
            parvallist.append(s)
        if f!=None:
            parnamelist.append('F')
            parvallist.append(f)        
            cmd='linearMove'
        params=self.ch.fill_parameters(parnamelist,parvallist)
        return {"action": cmd, "parameters": params}
        
    def dwell(self, ms):
        params=self.ch.Get_Parameters_Needed_for_action('dwell',self.ch.id)
        param_dict={}
        for par,req in params.items(): # can be P or S
            if req == 'required':
                param_dict={par:ms}
        return {"action": 'dwell', "parameters": param_dict}

    def comment(self, text):
        return self.a_set('Comment',msg=text)
