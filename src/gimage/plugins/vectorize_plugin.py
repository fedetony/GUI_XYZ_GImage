
from .plugin_base import GImageTechniqueBase
from thread_Vectorize import *
import os
import tempfile

class VectorizeTechnique(GImageTechniqueBase):
    name = "vectorize" #must match the name in the technique combo

    def process(self):
        print(f"Entered {self.name} plugin")
        #Get configuration Value
        mytechnique=self.config.get_value(["technique","technique_type","value"])
        
        self.emit_action({"action": "Message", "parameters":{"msg": "Starting vectorize_thread"}})
        cfg = self.config
        interface_name=self.ch.get_name_from_id(self.ch.id)
        self.emit_action(self.machine.a_set("Comment",msg=f"Using interface {interface_name}"))
        # --- CONFIG ---
        lines_per_mm = cfg.get_value(["technique","lines_per_mm","value"])
        self.mode = "continuous" # cfg.get_value(["image","mode","value"])  # "continuous" or "threshold"
        rdp_shape_simplification= cfg.get_value(["technique","rdp_shape_simplification","value"]) or 1
        self.min_power, self.max_power = cfg.get_value(["technique","power_range","value"])
        feedrange = cfg.get_value(["technique","feedrate_range","value"])
        vectorization_method = cfg.get_value(["technique","vectorization_method","value"]) or "opencv"
        merging_shape_factor = cfg.get_value(["technique","merging_shape_factor","value"]) or 0
        self.feedrate = cfg.get_value(["technique","rate","value"])
        if feedrange:
            self.min_rate,self.max_rate=feedrange
        else:
            self.min_rate,self.max_rate=(self.feedrate,self.feedrate)

        width_mm, height_mm, _ = cfg.get_value(["output","image_size","value"])
        self.offset_x, self.offset_y, _  = cfg.get_value(["output","image_offset","value"])
        self.gcode_floating_decimals  = cfg.get_value(["output","gcode_floating_decimals","value"]) or 3
        self.gcode_minimize_code= cfg.get_value(["output","gcode_minimize_code","value"]) or True
        
        
        #origin_x, origin_y, _ =cfg.get_value(["output","image_origin","value"])

        # --- COMPUTE resolution using lines per mm ---
        W = max(1, int(width_mm  * lines_per_mm))
        H = max(1, int(height_mm * lines_per_mm))
        self.step = 1.0 / lines_per_mm
        
        # set feedrate
        self.emit_action(self.machine.move(rapid=False,F=self.feedrate))

        # Home
        self.emit_action(self.machine.home())

        # Raise tool to moving height
        self.emit_action(self.tool.up())
        
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
        if vectorization_method == "opencv":                    
            svg_image = vectorize_thread.vectorizer_rgba_image_to_svg_contiguous(
                im=img,
                epsilon=rdp_shape_simplification,
                merge_strength=merging_shape_factor
                )
            vectorize_thread.Save_svg_text_file(svg_image,self.svg_path)
        elif vectorization_method == "classic":                    
            svg_image = vectorize_thread.rgba_image_to_svg_contiguous(im=img, epsilon=rdp_shape_simplification)
            vectorize_thread.Save_svg_text_file(svg_image,self.svg_path)

        self._to_gcode_contiguous_emit(img,vectorize_thread.last_color_joined_pieces)
        
        vectorize_thread.join()
        self.emit_status(f"Finished .... check \n{self.gcode_path}\n{self.svg_path}\n{self.actions_path}")
        
    
    def _to_gcode_contiguous_emit(self, im, color_joined_pieces:dict):
        img_ini_pos = [self.offset_x, self.offset_y]
        robot_xyz   = [0, 0, 0]
        resolution  = self.step
        gcode_minimize_code = self.gcode_minimize_code

        lenlist = len(color_joined_pieces)
        sss = 0

        for color, shapes in color_joined_pieces.items():

            self.check_stop()
            
            # --- Compute power + feedrate from color ---
            pixel = self.safe_pixel_from_color(color) # color is rgba
            power = self._pixel_to_power(pixel, self.min_power, self.max_power, self.mode)

            # IMPORTANT: use base feedrate, not previous feedrate
            feedrate = self._pixel_to_feedrate(pixel, self.feedrate,
                                            self.min_rate, self.max_rate, self.mode)
            self.emit_action(self.machine.a_set("Message",msg=f"New Color({color})/Layer with S{power} F{feedrate}"))
            # --- Progress ---
            percent = int((sss / max(1, lenlist - 1)) * 100)
            self.emit_progress(percent, {"color_index": sss, "colors_total": lenlist})
            sss += 1

            # minimization state
            last_xmm = None
            last_ymm = None
            last_power = None
            last_rate = feedrate
            last_modal = None

            for shape in shapes:
                self.check_stop()
                for sub_shape in shape:
                    self.check_stop()

                    if not sub_shape:
                        continue

                    # Build ordered point list
                    pts = [sub_shape[0][0]] + [e[1] for e in sub_shape]

                    # --- Move to first point with tool OFF ---
                    x, y = pts[0]
                    x, y = self.transform_px_to_im_xy(
                        im, x, y, img_ini_pos, robot_xyz, resolution
                    )

                    self.emit_action(self.tool.up())
                    rapid=True
                    self.emit_action(self.machine.move(rapid=rapid, X=x, Y=y, F=feedrate))

                    last_xmm = x
                    last_ymm = y
                    last_power = None
                    last_rate = feedrate
                    last_modal = rapid

                    # --- Tool ON ---
                    self.emit_action(self.tool.down(power))
                    rapid=False
                    # --- Trace remaining points ---
                    for (x, y) in pts[1:]:
                        self.check_stop()

                        x, y = self.transform_px_to_im_xy(
                            im, x, y, img_ini_pos, robot_xyz, resolution
                        )

                        if not gcode_minimize_code:
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

                    # --- Tool OFF ---
                    self.emit_action(self.tool.up())

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
    
    def _pixel_to_power(self, pixel, min_p, max_p, mode):
        if isinstance(pixel, tuple):
            pixel = sum(pixel) / len(pixel)

        if mode == "threshold":
            return max_p if pixel < 128 else 0

        # continuous grayscale
        brightness = pixel / 255.0
        inv = 1.0 - brightness
        return int(min_p + inv * (max_p - min_p))
    
    def _pixel_to_feedrate(self, pixel,actual_rate, min_rate, max_rate, mode):
        if mode == "threshold":
            return actual_rate
        if isinstance(pixel, tuple):
            pixel = sum(pixel) / len(pixel)
        # continuous grayscale
        brightness = pixel / 255.0
        inv = 1.0 - brightness
        return int(min_rate + inv * (max_rate - min_rate))
    
    def safe_pixel_from_color(self, color):
        try:
            r, g, b = color[:3]
            r = max(0, min(255, int(r)))
            g = max(0, min(255, int(g)))
            b = max(0, min(255, int(b)))
            return (r + g + b) / 3.0
        except Exception:
            return 128  # neutral gray fallback


    
class ProgressWrapper:
    def __init__(self,emit_progress):
        self.emit_progress = emit_progress
        
    def SetStatus(self,percent:int):
        # Progress
        percent=min(max(int(percent),0),100)
        self.emit_progress(int(percent), {})
