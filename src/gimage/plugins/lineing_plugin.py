
from .plugin_base import GImageTechniqueBase

class LineingTechnique(GImageTechniqueBase):
    name = "lineing" #must match the name in the technique combo

    def process(self):
        print("Entered plugin")
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
        self.emit_action({"action": "Message", "parameters":{"msg": "Starting Lineing"}})

        # Need to add killer events in every loop like this:
        # for layer in layers:
        #     self.check_stop()
        #     for x in range(width):
        #         self.check_stop()
        #         for y in range(height):
        #             self.check_stop()
        #             # process pixel


    #     cfg = self.config
    #     pimg_val_range = cfg["pimg_val_range"]      # [min_layer, start, end]
    #     Zinfo = cfg["Zinfo"]                        # [deltaZ, Zmove_pos, Ztouch_pos, Resolution, Process_rate]
    #     TCinfo = cfg["TCinfo"]                      # tool-change info

    #     [deltaZ, Zmove_pos, Ztouch_pos, Resolution, Process_rate] = Zinfo

    #     width, height = self.image.width, self.image.height
    #     is_up = True
    #     total_layers = pimg_val_range[2] - pimg_val_range[1]
    #     processed_layers = 0

    #     # Example: initial message
    #     self.emit_action({"action": "message", "msg": "Starting Lineing"})

    #     for aaa in range(pimg_val_range[1], pimg_val_range[2]):
    #         if TCinfo["T_Ch"] and aaa in TCinfo["T_Ch_in_Layers"]:
    #             self._emit_tool_change(TCinfo, Zinfo)

    #         if aaa == pimg_val_range[1]:
    #             # go to initial position
    #             pimg_X, pimg_Y = self._transform_pixel_to_image(0, 0, Resolution)
    #             self.emit_action({
    #                 "action": "movement",
    #                 "type": "goto",
    #                 "X": pimg_X,
    #                 "Y": pimg_Y,
    #                 "F": Process_rate,
    #             })
    #             self._emit_move_down_to_touch(Zinfo, is_up=False)
    #         else:
    #             if aaa % 2 == 0:
    #                 for xxx in range(0, width):
    #                     if xxx % 2 == 0:
    #                         y_iter = range(0, height)
    #                     else:
    #                         y_iter = reversed(range(0, height))
    #                     for yyy in y_iter:
    #                         is_up = self._process_pixel_lineing(
    #                             aaa, pimg_val_range, xxx, yyy, Zinfo, is_up
    #                         )
    #             else:
    #                 for yyy in range(0, height):
    #                     if yyy % 2 == 0:
    #                         x_iter = range(0, width)
    #                     else:
    #                         x_iter = reversed(range(0, width))
    #                     for xxx in x_iter:
    #                         is_up = self._process_pixel_lineing(
    #                             aaa, pimg_val_range, xxx, yyy, Zinfo, is_up
    #                         )

    #         self._emit_move_down_to_touch(Zinfo, is_up=False)
    #         processed_layers += 1
    #         percent = processed_layers / max(1, total_layers) * 100
    #         self.emit_progress(percent, {
    #             "layer": processed_layers,
    #             "layers_total": total_layers,
    #         })

    #     self._emit_move_down_to_touch(Zinfo, is_up=False)
    #     self.emit_status("Lineing finished")

    # # --- helper methods ---

    # def _transform_pixel_to_image(self, x, y, res):
    #     # call your old Transform_pixel_coordinates_to_image_coordinates
    #     # here you can either re-implement or inject a helper
    #     return x * res, y * res

    # def _emit_tool_change(self, TCinfo, Zinfo):
    #     # instead of G-code, emit a high-level action
    #     self.emit_action({
    #         "action": "toolChange",
    #         "tool": TCinfo["T"],
    #         "xyz_pos": TCinfo["T_Ch_XYZpos"],
    #         "script": TCinfo["T_Ch_Script"],
    #         "Zinfo": Zinfo,
    #     })

    # def _emit_move_down_to_touch(self, Zinfo, is_up):
    #     # previously Move_Down_to_Touch returned G-code; now emit actions
    #     [deltaZ, Zmove_pos, Ztouch_pos, Resolution, Process_rate] = Zinfo
    #     targetZ = Ztouch_pos if is_up else Zmove_pos
    #     self.emit_action({
    #         "action": "movementZ",
    #         "Z": targetZ,
    #         "F": Process_rate,
    #     })

    # def _process_pixel_lineing(self, layer, pimg_val_range, x, y, Zinfo, is_up):
    #     # here you use pixel color to decide if you draw or move
    #     pixel = self.image.getpixel((x, y))
    #     # compute S, or decide to draw / skip, etc.
    #     # Example: if pixel is dark enough, draw:
    #     if self._should_draw(pixel, layer, pimg_val_range):
    #         Ximg, Yimg = self._transform_pixel_to_image(x, y, Zinfo[3])
    #         self.emit_action({
    #             "action": "movement",
    #             "X": Ximg,
    #             "Y": Yimg,
    #             "F": Zinfo[4],
    #             "S": self._power_from_pixel(pixel),
    #         })
    #         return False  # or True depending on your "is_up" semantics
    #     else:
    #         # maybe rapid move or nothing
    #         return is_up

    # def _should_draw(self, pixel, layer, pimg_val_range):
    #     # your old logic based on grayscale / thresholds
    #     return True

    # def _power_from_pixel(self, pixel):
    #     # map pixel to S power
    #     return 1000
