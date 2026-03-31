
import pyclipper._pyclipper
from .plugin_base import GImageTechniqueBase
from thread_Vectorize import *
import os
import tempfile
import pyclipper
from ._math_tranforming_helpers import *

class VectorizeFillTechnique(GImageTechniqueBase):
    name = "vectorize_fill" #must match the name in the technique combo

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
        self.fill_method  = cfg.get_value(["technique","fill_method","value"])
        self.emit_action(self.machine.a_set("Comment",msg=f"Using fill method {self.fill_method}"))
        self.fill_area_factor = cfg.get_value(["technique","fill_area_factor","value"]) or 4
        self.fill_min_lines = cfg.get_value(["technique","fill_min_lines","value"]) or 3
        self.mode = "continuous" # cfg.get_value(["image","mode","value"])  # "continuous" or "threshold"
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
        
        
        #origin_x, origin_y, _ =cfg.get_value(["output","image_origin","value"])

        # --- COMPUTE resolution using lines per mm ---
        W = max(1, int(width_mm  * lines_per_mm))
        H = max(1, int(height_mm * lines_per_mm))
        self.step = 1.0 / lines_per_mm

        self.spacing=self.step*self.overlap

        
        # set feedrate
        self.emit_action(self.machine.move(rapid=False,F=self.feedrate))

        # Home
        self.emit_action(self.machine.home())

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

        self._to_gcode_contiguous_emit(img,vectorize_thread.last_color_joined_pieces)
        
        vectorize_thread.join()
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

            for shape in shapes:
                self.check_stop()
                brightness = pixel / 255 # [0-1]
                new_shape = None
                if self.fill_method == "none":
                    new_shape = self.generate_none_fill(shape, self.spacing)

                elif self.fill_method == "hatch":
                    angle = 90 * brightness
                    new_shape = self.generate_hatch_fill(shape, self.spacing, angle)

                elif self.fill_method == "crosshatch":
                    angle = 45 + 90 * brightness
                    spacing = self.spacing * (1 + brightness)
                    new_shape = self.generate_crosshatch_fill(shape, spacing, angle)

                # elif self.fill_method == "spiral":
                #     spacing = self.spacing * (1 + brightness)
                #     new_shape = self.generate_spiral_fill(shape, spacing)

                elif self.fill_method == "offset":
                    spacing = self.spacing * (1 + brightness)
                    new_shape = self.generate_offset_fill(shape, spacing)

                else:
                    new_shape = shape

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
            self.emit_action(self.tool.down(power))
        self.is_up=False

        rapid = False

        # Follow segment
        for (x, y) in pts[1:]:
            self.check_stop()
            x, y = self.transform_px_to_im_xy(im, x, y, img_ini_pos, robot_xyz, resolution)

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

        # --- Tool OFF ---
        if not self.is_up:
            self.emit_action(self.tool.up())
        self.is_up=True

    def merge_fragments_serpentine(self, fragments):
        # Remove empty or tiny fragments
        fragments = [f for f in fragments if len(f) >= 2]

        if not fragments:
            return []

        # Sort by Y coordinate (or X depending on angle)
        fragments.sort(key=lambda seg: (seg[0][1] + seg[-1][1]) / 2)

        # Reverse every second fragment to create serpentine path
        for i in range(len(fragments)):
            if i % 2 == 1:
                fragments[i] = list(reversed(fragments[i]))

        # Merge into one continuous polyline
        merged = []
        for seg in fragments:
            merged.extend(seg)

        return [merged]  # return as a single subshape


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
    
    def subshape_to_points(self, sub_shape):
        return [sub_shape[0][0]] + [e[1] for e in sub_shape]

    def points_to_subshape(self, pts):
        # pts = [(x0,y0), (x1,y1), (x2,y2), ...]
        # return [ ((x0,y0),(x1,y1)), ((x1,y1),(x2,y2)), ... ]
        return [ (pts[i], pts[i+1]) for i in range(len(pts)-1) ]

    def merge_serpentine(self, segments):
        if not segments:
            return []

        # sort by y
        segments.sort(key=lambda s: (s[0][1] + s[-1][1]) / 2)

        # reverse every second
        for i in range(len(segments)):
            if i % 2 == 1:
                segments[i].reverse()

        # merge into one polyline
        merged = []
        for seg in segments:
            merged.extend(seg)

        return merged

    def generate_hatch_fill(self, shape, spacing, angle_deg=0):

        new_shape = []

        for subshape in shape:
            self.check_stop()

            # Convert subshape → point list 
            pts = self.subshape_to_points(subshape)

            # Compute polygon area
            area = polygon_area(pts)

            # Minimum area threshold
            hatch_distance = spacing * self.overlap

            # must fit at least 2 hatch lines
            min_thickness = self.fill_min_lines * max(hatch_distance,spacing)

            # area threshold
            min_hatch_area = self.fill_area_factor * (min_thickness ** 2)

            # If too small → keep original contour
            if area < min_hatch_area:
                new_shape.append(subshape)
                continue

            # Rotate THIS subshape
            rot_pts = rotate_polygon(pts, angle_deg)

            # Bounding box
            minx, maxx, miny, maxy = bbox(rot_pts)

            # If shape is too thin → don't hatch
            if maxy - miny <= min_thickness or maxx - minx <= min_thickness:
                new_shape.append(subshape)
                continue

            # Generate scanlines
            segments = []
            y = miny
            while y <= maxy:
                xs = polygon_intersections(rot_pts, y)
                xs.sort()
                for i in range(0, len(xs), 2):
                    segments.append([(xs[i], y), (xs[i+1], y)])
                y += hatch_distance

            # Rotate segments back
            segments = rotate_segments(segments, -angle_deg)

            # Merge into serpentine
            merged = self.merge_serpentine(segments)

            # Convert to subshape format
            new_shape.append(self.points_to_subshape(merged))

        return new_shape
    
    def generate_crosshatch_fill(self, shape, spacing, angle_deg=45):
        s1 = self.generate_hatch_fill(shape, spacing, angle_deg)
        s2 = self.generate_hatch_fill(shape, spacing, angle_deg + 90)
        return s1 + s2


    def generate_spiral_fill(self, shape, spacing):
        scale = 1000

        # 1. Flatten polygon
        flat = self.flatten_shape_to_polygon(shape)
        flat = list(dict.fromkeys(flat))  # remove duplicates

        if len(flat) < 3:
            return []

        # 2. Simplify polygon (scaled)
        tolerance = spacing * scale
        scaled = [(int(x*scale), int(y*scale)) for x,y in flat]
        cleaned = pyclipper.CleanPolygon(scaled, tolerance)

        if not cleaned or len(cleaned) < 3:
            return []

        # unscale
        flat = [(x/scale, y/scale) for x,y in cleaned]

        # 3. Compute centroid safely
        cx, cy = polygon_centroid(flat)

        # 4. Generate spiral
        spiral = generate_spiral(cx, cy, spacing)

        # 5. Decimate spiral BEFORE clipping
        spiral = spiral[::5]

        # 6. Clip spiral to polygon
        clipped = clip_polyline_to_polygon(spiral, flat)

        # 7. Decimate clipped segments
        final = []
        for seg in clipped:
            if len(seg) > 3:
                final.append(seg[::3])

        return final

    def generate_offset_fill(self, shape, spacing):
        return shape
        scale = 1000

        # 1. Flatten
        flat = self.flatten_shape_to_polygon(shape)

        # 2. Simplify polygon
        tolerance = spacing * scale
        scaled = [(int(x*scale), int(y*scale)) for x,y in flat]
        cleaned = pyclipper.CleanPolygon(scaled, tolerance)

        if not cleaned or len(cleaned) < 3:
            return []

        current = [cleaned]
        result = []

        # 3. Limit number of layers
        max_layers = int(2000 / spacing)
        layers = 0

        while current and layers < max_layers:
            next_level = []

            for p in current:
                off = pyclipper.PyclipperOffset()
                off.AddPath(p, pyclipper.JT_ROUND, pyclipper.ET_CLOSEDPOLYGON)
                res = off.Execute(-spacing * scale)

                for r in res:
                    # unscale
                    pts = [(x/scale, y/scale) for x,y in r]

                    # decimate
                    pts = pts[::3]

                    if len(pts) > 3:
                        # convert to subshape format
                        subshape = self.points_to_subshape(pts)
                        result.append(subshape)

                next_level.extend(res)

            current = next_level
            layers += 1

        return result


    
    def flatten_shape_to_polygon(self,shape):
        """
        shape = [ [((x0,y0),(x1,y1)), ((x1,y1),(x2,y2)), ...], ... ]
        returns: [(x0,y0), (x1,y1), (x2,y2), ...]
        """
        pts = []

        for sub in shape:
            if not sub:
                continue
            # first point of first segment
            pts.append(sub[0][0])
            # then all segment endpoints
            for seg in sub:
                pts.append(seg[1])

        return pts

    
    def generate_none_fill(self,shape, spacing, **kwargs):
        return shape


    
class ProgressWrapper:
    def __init__(self,emit_progress):
        self.emit_progress = emit_progress
        
    def SetStatus(self,percent:int):
        # Progress
        percent=min(max(int(percent),0),100)
        self.emit_progress(int(percent), {})
