
import pyclipper._pyclipper
from .plugin_base import GImageTechniqueBase
from thread_Vectorize import *
import os
import tempfile
import pyclipper
from ._math_tranforming_helpers import *
from ._vectorize_shared import *

# 🎯 Preset 1: High Detail Fill
#     RDP = 0.5
#     Merge = 0
#     Fill spacing = 1×
#     Min lines = 1
#     Result: beautiful, slow, huge G‑code

# 🎯 Preset 2: Balanced Fill
#     RDP = 1.5
#     Merge = 1
#     Fill spacing = 1.5×
#     Min lines = 3
#     Result: good quality, reasonable G‑code

# 🎯 Preset 3: Fast Fill
#     RDP = 3
#     Merge = 3
#     Fill spacing = 2×
#     Min lines = 5
#     Result: fast, small G‑code, less detail

# 🎯 Preset 4: Posterize Fill
#     Quantize colors to 4
#     RDP = 5
#     Merge = 5
#     Fill spacing = 3×
#     Min lines = 10
#     Result: stylized, very fast, minimal G‑code

class VectorizeFillTechnique(GImageTechniqueBase):
    name = "vectorize_fill" #must match the name in the technique combo

    def process(self):
        print(f"Entered {self.name} plugin")
        #Get configuration Value
        mytechnique=self.config.get_value(["technique","technique_type","value"])
        self.emit_action(self.machine.a_set("Comment",msg=f"Technique {mytechnique}"))
        self.emit_action({"action": "Message", "parameters":{"msg": "Starting vectorize_thread"}})
        cfg = self.config
        interface_name=self.ch.get_name_from_id(self.ch.id)
        self.emit_action(self.machine.a_set("Comment",msg=f"Using interface {interface_name}"))
        # --- CONFIG ---
        lines_per_mm = cfg.get_value(["technique","lines_per_mm","value"])
        self.fill_method  = cfg.get_value(["technique","fill_method","value"])
        self.emit_action(self.machine.a_set("Comment",msg=f"Using fill method {self.fill_method}"))
        self.fill_area_factor = cfg.get_value(["technique","fill_area_factor","value"]) or 4
        self.fill_min_lines = cfg.get_value(["technique","fill_min_lines","value"]) or 3
        self.p_mode = "continuous" # cfg.get_value(["image","mode","value"])  # "continuous" or "threshold"
        self.fr_mode = "threshold" 
        rdp_shape_simplification= cfg.get_value(["technique","rdp_shape_simplification","value"]) or 1

        self.min_power, self.max_power = cfg.get_value(["technique","power_range","value"])
        feedrange = cfg.get_value(["technique","feedrate_range","value"])
        self.feedrate = cfg.get_value(["technique","rate","value"])

        self.overlap = cfg.get_value(["technique","overlap","value"]) or 1
        if feedrange:
            self.min_rate,self.max_rate=feedrange
        else:
            self.min_rate,self.max_rate=(self.feedrate,self.feedrate)

        width_mm, height_mm, _ = cfg.get_value(["output","image_size","value"])
        self.offset_x, self.offset_y, _  = cfg.get_value(["output","image_offset","value"])
        self.gcode_floating_decimals  = cfg.get_value(["output","gcode_floating_decimals","value"]) or 3
        self.gcode_minimize_code= cfg.get_value(["output","gcode_minimize_code","value"]) or True
        
        self.invert = cfg.get_value(["technique","invert","value"])
        if self.invert is None:
            self.invert = False
        
        # parameters message
        params_msg = (
            f"Settings rate:{self.feedrate},lpmm:{lines_per_mm},inv:{self.invert},"
            f"rdp:{rdp_shape_simplification},over:{self.overlap},"
            f"{self.fill_method},faf:{self.fill_area_factor},fml:{self.fill_min_lines}"
        )
        self.emit_action(self.machine.a_set("Comment", msg=params_msg))
        
        #origin_x, origin_y, _ =cfg.get_value(["output","image_origin","value"])

        # --- COMPUTE resolution using lines per mm ---
        W = max(1, int(width_mm  * lines_per_mm))
        H = max(1, int(height_mm * lines_per_mm))
        self.step = 1.0 / lines_per_mm

        self.spacing=self.step*self.overlap

        # set feedrate
        self.emit_action(self.machine.set_units())
        self.emit_action(self.machine.move(rapid=False,F=self.feedrate))

        # Raise tool to moving height
        self.emit_action(self.tool.up())
        self.is_up=True
        
        origin_x, origin_y, = (0 , 0)
        # Move to origin
        self.emit_action(self.machine.move(rapid=True,X=origin_x,Y=origin_y))
        
        # Set origin
        self.emit_action(self.machine.set_position(X=0,Y=0))

        # --- PREPARE IMAGE ---
        img = self.image.convert("RGB")
        img = img.resize((W, H), resample=Image.Resampling.LANCZOS)
        
        filename=f"{self.name}_gimage_output"
        self.actions_path = os.path.join(tempfile.gettempdir(), f"{filename}.jsonl")
        self.svg_path   = os.path.join(tempfile.gettempdir(), f"{filename}.svg")
        self.gcode_path   = os.path.join(tempfile.gettempdir(), f"{filename}.gcode")
          
        print('Processing image of size',img.size)    
        
        progress_bar=ProgressWrapper(self.emit_progress)
        vectorize_thread=Vectorization(img,self.killer_event,Pbar=progress_bar)
        vectorize_thread.start()
        vectorize_thread.printprocess=True #debugging
                            
        svg_image = vectorize_thread.vectorizer_rgba_image_to_svg_contiguous(im=img,epsilon=rdp_shape_simplification)
        vectorize_thread.Save_svg_text_file(svg_image,self.svg_path)

        vectorize_thread.last_color_joined_pieces=vectorize_thread.sort_color_joined_pieces_to_shortest_path(vectorize_thread.last_color_joined_pieces)

        self._to_gcode_contiguous_emit(img,vectorize_thread.last_color_joined_pieces)
        
        vectorize_thread.join()
        self.set_exit_config()
        self.emit_status(f"Finished .... check \n{self.gcode_path}\n{self.svg_path}\n{self.actions_path}")
        
    
    def _to_gcode_contiguous_emit(self, im, color_joined_pieces:dict):
        img_ini_pos = [self.offset_x, self.offset_y]
        robot_xyz   = [0, 0, 0]
        resolution  = self.step

        lenlist = len(color_joined_pieces)
        sss = 0

        for color, shapes in color_joined_pieces.items():

            self.check_stop()
            
            # --- Compute power + feedrate from color ---
            pixel = safe_pixel_from_color(color) # color is rgba
            power = pixel_to_power(pixel, self.min_power, self.max_power, self.p_mode, self.invert)

            # IMPORTANT: use base feedrate, not previous feedrate
            feedrate = pixel_to_feedrate(pixel, self.feedrate,
                                            self.min_rate, self.max_rate, self.fr_mode, self.invert)
            self.emit_action(self.machine.a_set("Message",msg=f"New Color({color})/Layer with S{power} F{feedrate}"))
            # --- Progress ---
            percent = int((sss / max(1, lenlist - 1)) * 100)
            self.emit_progress(percent, {"color_index": sss, "colors_total": lenlist})
            sss += 1

            for shape in shapes:
                self.check_stop()
                brightness = pixel / 255 # [0-1]
                new_shape = None
                closed_shape = generate_none_fill(shape, self.spacing)
                if self.fill_method == "hatch":
                    angle = 90 * brightness
                    new_shape = generate_hatch_fill(closed_shape, self.spacing, angle)

                elif self.fill_method == "crosshatch":
                    angle = 45 + 90 * brightness
                    spacing = self.spacing * (1 + brightness)
                    new_shape = generate_crosshatch_fill(closed_shape, spacing, angle)

                elif self.fill_method == "spiral":
                    spacing = self.spacing * (1 + brightness)
                    new_shape = generate_spiral_fill(closed_shape, spacing)

                elif self.fill_method == "offset":
                    spacing = self.spacing * (1 + brightness)
                    new_shape = generate_offset_fill(closed_shape, spacing)
                
                elif self.fill_method == "concentric":
                    spacing = self.spacing * (1 + brightness)
                    new_shape = generate_concentric_fill(closed_shape, spacing)
                
                elif self.fill_method == "contour_hatch":
                    angle = 90 * brightness
                    new_shape = generate_contour_hatched_fill(closed_shape, self.spacing, angle,False)

                elif self.fill_method == "contour_crosshatch":
                    angle = 45 + 90 * brightness
                    spacing = self.spacing * (1 + brightness)
                    new_shape = generate_contour_hatched_fill(closed_shape, spacing, angle,True)

                else:
                    new_shape = closed_shape

                # NOW iterate over subshapes
                for sub_shape in new_shape:
                    self.check_stop()
                    # draw each segment
                    self.draw_subshapes(sub_shape, power, feedrate, im, img_ini_pos, robot_xyz, resolution)

    def draw_subshapes(self, sub_shape, power, feedrate, im, img_ini_pos, robot_xyz, resolution):
        if not sub_shape:
            return

        # Build ordered point list
        pts = [sub_shape[0][0]] + [e[1] for e in sub_shape]

        # Move to first point
        x, y = pts[0]
        x, y = self.transform_px_to_im_xy(im, x, y, img_ini_pos, robot_xyz, resolution)
        if not self.is_up:
            self.emit_action(self.tool.up())
        self.is_up=True
        rapid = True
        self.emit_action(self.machine.move(rapid=rapid, X=x, Y=y, F=feedrate))

        last_xmm = x
        last_ymm = y
        last_power = None
        last_rate = feedrate
        last_modal = rapid

        # Tool ON
        if self.is_up:
            self.emit_action(self.tool.down(power=power))
        self.is_up=False

        rapid = False

        # Follow segment
        for (x, y) in pts[1:]:
            self.check_stop()
            x, y = self.transform_px_to_im_xy(im, x, y, img_ini_pos, robot_xyz, resolution)

            last_vect=(last_xmm,last_ymm,last_power,last_rate,last_modal)
            last_vect=self._do_draw(rapid,x,y,power,feedrate,last_vect)
            last_xmm,last_ymm,last_power,last_rate,last_modal=last_vect

        # --- Tool OFF ---
        if not self.is_up:
            self.emit_action(self.tool.up())
        self.is_up=True

    def _do_draw(self,
                 rapid,
                 x,
                 y,
                 power,
                 feedrate,last_vect):
        last_xmm,last_ymm,last_power,last_rate,last_modal=last_vect
        if not self.gcode_minimize_code:
            self.emit_action(self.machine.move(
                rapid=rapid, X=x, Y=y, S=int(power), F=feedrate
            ))
        else:
            dx = (x != last_xmm)
            dy = (y != last_ymm)
            dp = (power != last_power)
            df = (feedrate != last_rate)
            dmod = (rapid != last_modal) 

            if dx or dy or dp or df:
                params = {}
                if dx: params["X"] = x
                if dy: params["Y"] = y
                if dp: params["S"] = int(power)
                if df: params["F"] = int(feedrate)

                if dmod:
                    self.emit_action(self.machine.move(
                        rapid=rapid, **params
                    ))
                else:
                    self.emit_action(self.machine.a_set(
                        "modalcoordSet", **params
                    ))

        # update last values
        last_xmm = x
        last_ymm = y
        last_power = power
        last_rate = feedrate
        last_modal = rapid
        return last_xmm,last_ymm,last_power,last_rate,last_modal

    def transform_px_to_im_xy(self, im, x, y, img_ini_pos, robot_xyz, resolution=1):
        """
        Convert pixel coordinates from image space into robot/world-space coordinates.

        This function takes a pixel coordinate (x, y) from an image where (0, 0) is
        the top-left corner, applies a resolution scaling factor, flips the Y-axis
        to convert from image coordinates to Cartesian-style coordinates, and then
        offsets the result by the robot's image origin and robot XYZ position.
        """

        # Flip Y (image → Cartesian)
        y = (im.height - 1) - y

        # Scale
        x = x * resolution
        y = y * resolution

        # Add offsets
        x += img_ini_pos[0] + robot_xyz[0]
        y += img_ini_pos[1] + robot_xyz[1]

        # Round here so all downstream code gets clean values
        return (self.rr(x), self.rr(y))
    
    def rr(self,value:float):
            """Helper to set number of decimals to the gcode coordinates"""
            return float(f"{value:.{self.gcode_floating_decimals}f}")
    
    
class ProgressWrapper:
    def __init__(self,emit_progress):
        self.emit_progress = emit_progress
        
    def SetStatus(self,percent:int):
        # Progress
        percent=min(max(int(percent),0),100)
        self.emit_progress(int(percent), {})
