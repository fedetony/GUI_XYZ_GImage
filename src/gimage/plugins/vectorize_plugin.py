
from .plugin_base import GImageTechniqueBase

class LineingTechnique(GImageTechniqueBase):
    name = "vectorize" #must match the name in the technique combo

    def process(self):
        print(f"Entered {self.name} plugin")
        #Get configuration Value
        mytechnique=self.config.get_value(["technique","technique_type","value"])
        #self.root_node=self.config.get_root()
        # validation=self.config.validate_node(["technique"])
        # self.technique_node=self.config.([])
        available_actions=self.ch.getListofActions()
        available_parameters=self.ch.Get_list_of_all_parameters_in_interface(self.ch.id)
        print("Interface:",self.ch.get_name_from_id(self.ch.id))
        print("available_actions",available_actions)
        print("available_parameters",available_parameters)
        #Add action to queue
        setattr(self.tool,"min_power",1)
        setattr(self.tool,"max_power",1000)
        down=self.tool.down()
        print("ch->",dir(self.ch))
        self.emit_action({"action": "Message", "parameters":{"msg": "Starting Vectorize"}})
        self.emit_action(down)