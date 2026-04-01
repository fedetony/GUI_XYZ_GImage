
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
                closed_shape = self.generate_none_fill(shape, self.spacing)
                if self.fill_method == "hatch":
                    angle = 90 * brightness
                    new_shape = self.generate_hatch_fill(closed_shape, self.spacing, angle)

                elif self.fill_method == "crosshatch":
                    angle = 45 + 90 * brightness
                    spacing = self.spacing * (1 + brightness)
                    new_shape = self.generate_crosshatch_fill(closed_shape, spacing, angle)

                elif self.fill_method == "spiral":
                    spacing = self.spacing * (1 + brightness)
                    new_shape = self.generate_spiral_fill(closed_shape, spacing)

                elif self.fill_method == "offset":
                    spacing = self.spacing * (1 + brightness)
                    new_shape = self.generate_offset_fill(closed_shape, spacing)
                
                elif self.fill_method == "concentric":
                    spacing = self.spacing * (1 + brightness)
                    new_shape = self.generate_concentric_fill(closed_shape, spacing)
                
                elif self.fill_method == "contour_hatch":
                    angle = 90 * brightness
                    new_shape = self.generate_contour_hatched_fill(closed_shape, self.spacing, angle,False)

                elif self.fill_method == "contour_crosshatch":
                    angle = 45 + 90 * brightness
                    spacing = self.spacing * (1 + brightness)
                    new_shape = self.generate_contour_hatched_fill(closed_shape, spacing, angle,True)

                else:
                    new_shape = closed_shape

                # NOW iterate over subshapes
                for sub_shape in new_shape:
                    self.check_stop()
                    # draw each segment
                    self.draw_subshapes(sub_shape, power, feedrate, im, img_ini_pos, robot_xyz, resolution)

    def normalize_winding(self, shape):
        normalized = []
        for sub in shape:
            pts = self.subshape_to_points(sub)
            area = polygon_area(pts)

            # Outer boundary should be CW (area < 0)
            if area > 0:
                sub = self.reverse_subshape(sub)

            normalized.append(sub)

        return normalized
    
    def classify_subshapes(self, shape):
        outers = []
        holes = []
        for sub in shape:
            pts = self.subshape_to_points(sub)
            area = polygon_area(pts)

            # If your coordinate system is image-like (y down), flip the logic:
            if area >= 0:
                outers.append(sub)   # outer
            else:
                holes.append(sub)    # hole

        return outers, holes


    def reverse_subshape(self, sub):
        return [(b, a) for (a, b) in reversed(sub)]
       

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

        # 1. Split into outer boundaries and holes
        outers, holes = self.classify_subshapes(shape)

        for outer in outers:
            self.check_stop()

            pts = self.subshape_to_points(outer)
            area = polygon_area(pts)

            hatch_distance = spacing * self.overlap
            min_thickness = self.fill_min_lines * max(hatch_distance, spacing)
            min_hatch_area = self.fill_area_factor * (min_thickness ** 2)

            if area < min_hatch_area:
                new_shape.append(outer)
                continue

            # Rotate polygon
            rot_pts = rotate_polygon(pts, angle_deg)

            # Bounding box
            minx, maxx, miny, maxy = bbox(rot_pts)

            if maxy - miny <= min_thickness or maxx - minx <= min_thickness:
                new_shape.append(outer)
                continue

            # 2. Generate scanlines
            segments = []
            y = miny
            while y <= maxy:
                xs = polygon_intersections(rot_pts, y)
                xs.sort()
                for i in range(0, len(xs), 2):
                    segments.append([(xs[i], y), (xs[i+1], y)])
                y += hatch_distance

            # Rotate back
            segments = rotate_segments(segments, -angle_deg)

            # 3. Subtract holes from hatch lines
            if holes:
                segments = self.subtract_holes_from_segments(segments, holes)

            # 4. Merge serpentine
            merged = self.merge_serpentine(segments)

            new_shape.append(self.points_to_subshape(merged))

        return new_shape

    def subtract_holes_from_segments(self, segments, holes):
        result = []
        for seg in segments:
            clipped = [seg]
            for hole in holes:
                clipped2 = []
                for c in clipped:
                    clipped2.extend(clip_polyline_to_polygon(c, hole, invert=True))
                clipped = clipped2
            result.extend(clipped)
        return result
    
    def generate_crosshatch_fill(self, shape, spacing, angle_deg=45):
        s1 = self.generate_hatch_fill(shape, spacing, angle_deg)
        s2 = self.generate_hatch_fill(shape, spacing, angle_deg + 90)
        return s1 + s2

    def generate_concentric_fill(self, shape, spacing):
        # 1. Split into outer boundaries and holes
        outers, holes = self.classify_subshapes(shape)

        concentric = []

        # 2. Draw only outer contours (SVG behavior)
        for outer in outers:
            concentric.append(outer)

        # 3. Generate inward offset rings (hole-aware)
        rings = self.generate_offset_fill(shape, spacing)

        # 4. Add rings
        concentric.extend(rings)

        return concentric

    def generate_contour_hatched_fill(self, shape, spacing, angle_deg, is_crosshatch=False):
        outers, holes = self.classify_subshapes(shape)

        hatched = []

        # 1) Draw only outer contours (SVG behavior)
        for sub in outers:
            hatched.append(sub)

        # 2) Add hatch or crosshatch (already hole-aware)
        if not is_crosshatch:
            fills = self.generate_hatch_fill(shape, spacing, angle_deg)
        else:
            fills = self.generate_crosshatch_fill(shape, spacing, angle_deg)

        hatched.extend(fills)
        return hatched

    def generate_spiral_fill(self, shape, spacing):
        scale = 1000

        # 1. Split into outer boundaries and holes
        outers, holes = self.classify_subshapes(shape)

        final = []

        # Process each outer boundary independently
        for outer in outers:

            # Flatten outer ring
            flat = self.subshape_to_points(outer)
            flat = list(dict.fromkeys(flat))

            if len(flat) < 3:
                continue

            # 2. Simplify polygon (scaled)
            tolerance = spacing * scale
            scaled = [(int(x*scale), int(y*scale)) for x,y in flat]
            cleaned = pyclipper.CleanPolygon(scaled, tolerance)

            if not cleaned or len(cleaned) < 3:
                continue

            # unscale
            flat = [(x/scale, y/scale) for x,y in cleaned]

            # 3. Compute centroid safely
            cx, cy = polygon_centroid(flat)

            # 4. Generate a dense spiral
            minx = min(p[0] for p in flat)
            maxx = max(p[0] for p in flat)
            miny = min(p[1] for p in flat)
            maxy = max(p[1] for p in flat)

            max_radius = max(maxx - minx, maxy - miny) * 1.5
            spiral = generate_spiral(cx, cy, spacing * self.overlap, max_radius=max_radius)

            # 5. Clip spiral to outer boundary, segment-by-segment
            clipped = []
            for i in range(len(spiral)-1):
                seg = [spiral[i], spiral[i+1]]
                clipped_seg = clip_polyline_to_polygon(seg, flat)
                if clipped_seg:
                    clipped.extend(clipped_seg)

            # 6. Subtract holes
            if holes:
                clipped = self.subtract_holes_from_segments(clipped, holes)

            # 7. Decimate AFTER clipping
            for seg in clipped:
                if len(seg) > 3:
                    final.append(seg[::3])

        return final

    def generate_offset_fill(self, shape, spacing):
        scale = 1000
        spacing = spacing * self.overlap

        # 1. Split into outer boundaries and holes
        outers, holes = self.classify_subshapes(shape)

        # Convert all rings to scaled integer paths
        def scale_path(sub):
            pts = self.subshape_to_points(sub)
            return [(int(x*scale), int(y*scale)) for x,y in pts]

        outer_paths = [scale_path(o) for o in outers]
        hole_paths  = [scale_path(h) for h in holes]

        # 2. Clean each ring
        tolerance = spacing * scale
        outer_paths = [pyclipper.CleanPolygon(p, tolerance) for p in outer_paths]
        hole_paths  = [pyclipper.CleanPolygon(p, tolerance) for p in hole_paths]

        # Remove empties
        outer_paths = [p for p in outer_paths if len(p) >= 3]
        hole_paths  = [p for p in hole_paths if len(p) >= 3]

        if not outer_paths:
            return []

        # 3. Build a compound polygon (outer + holes)
        pc = pyclipper.Pyclipper()
        pc.AddPaths(outer_paths, pyclipper.PT_SUBJECT, True)
        pc.AddPaths(hole_paths,  pyclipper.PT_SUBJECT, True)

        # 4. Offset inward repeatedly
        result = []
        current = outer_paths + hole_paths
        max_layers = int(2000 / spacing)
        layers = 0

        while current and layers < max_layers:
            off = pyclipper.PyclipperOffset()
            off.AddPaths(current, pyclipper.JT_ROUND, pyclipper.ET_CLOSEDPOLYGON)
            res = off.Execute(-spacing * scale)

            if not res:
                break

            # Convert each offset ring to subshape
            for r in res:
                pts = [(x/scale, y/scale) for x,y in r]
                pts = pts[::3]  # decimate
                if len(pts) > 3:
                    result.append(self.points_to_subshape(pts))

            current = res
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
    
    def generate_none_fill(self, shape, spacing, **kwargs):
        closed = []
        if not shape:
            return shape

        for sub in shape:
            if not sub:
                continue

            # A valid polygon needs at least 3 points (i.e., 3 edges)
            if len(sub) < 3:
                closed.append(sub)
                continue

            start = sub[0][0]
            end   = sub[-1][1]

            # Already closed?
            if start == end:
                closed.append(sub)
                continue

            # Close loop
            sub = sub + [ ((end[0], end[1]), (start[0], start[1])) ]
            closed.append(sub)

        return closed

    
class ProgressWrapper:
    def __init__(self,emit_progress):
        self.emit_progress = emit_progress
        
    def SetStatus(self,percent:int):
        # Progress
        percent=min(max(int(percent),0),100)
        self.emit_progress(int(percent), {})
