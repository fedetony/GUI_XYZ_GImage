from .plugin_base import GImageTechniqueBase
from ._vectorize_shared import *
from PIL import Image
import numpy as np
from skimage import measure
import os, tempfile

class VectorizeFillPerColorTechnique(GImageTechniqueBase):
    name = "vectorize_cut_fill"

    def process(self):
        print(f"Entered {self.name} plugin")
        mytechnique=self.config.get_value(["technique","technique_type","value"])
        self.emit_action(self.machine.a_set("Comment",msg=f"Technique {mytechnique}"))
        cfg = self.config
        interface_name = self.ch.get_name_from_id(self.ch.id)
        self.emit_action(self.machine.a_set("Comment", msg=f"Using interface {interface_name}"))

        # --- CONFIG ---
        lines_per_mm = cfg.get_value(["technique","lines_per_mm","value"])
        if lines_per_mm is None:
            lines_per_mm = 1
        contour_level = cfg.get_value(["technique","contour_level","value"])
        if contour_level is None:
            contour_level = 0.5
        smooth_passes = cfg.get_value(["technique","smooth_passes","value"])
        if smooth_passes is None:
            smooth_passes = 1

        self.fill_method  = cfg.get_value(["technique","fill_method","value"])
        self.fill_area_factor = cfg.get_value(["technique","fill_area_factor","value"]) or 4
        self.fill_min_lines = cfg.get_value(["technique","fill_min_lines","value"]) or 3
        self.p_mode = "continuous" # vary power
        self.fr_mode = "threshold" # fixed feedrate
        rdp_shape_simplification = cfg.get_value(["technique","rdp_shape_simplification","value"]) or 1.0

        self.min_power, self.max_power = cfg.get_value(["technique","power_range","value"])
        feedrange = cfg.get_value(["technique","feedrate_range","value"])
        self.feedrate = cfg.get_value(["technique","rate","value"]) or 800

        self.overlap = cfg.get_value(["technique","overlap","value"]) or 1
        if feedrange:
            self.min_rate, self.max_rate = feedrange
        else:
            self.min_rate, self.max_rate = (self.feedrate, self.feedrate)

        width_mm, height_mm, _ = cfg.get_value(["output","image_size","value"])
        self.offset_x, self.offset_y, _  = cfg.get_value(["output","image_offset","value"])
        self.gcode_floating_decimals  = cfg.get_value(["output","gcode_floating_decimals","value"]) or 3
        self.gcode_minimize_code = cfg.get_value(["output","gcode_minimize_code","value"]) or True

        number_of_colors = cfg.get_value(["image","number_of_colors","value"]) or 4

        invert = cfg.get_value(["technique","invert","value"])
        if invert is None:
            invert = False

        # parameters message
        params_msg = (
            f"Settings rate:{self.feedrate},lpmm:{lines_per_mm},inv:{invert},"
            f"c_l:{contour_level},rdp:{rdp_shape_simplification},over:{self.overlap},"
            f"s_p:{smooth_passes},{self.fill_method},faf:{self.fill_area_factor},fml:{self.fill_min_lines}"
        )
        self.emit_action(self.machine.a_set("Comment", msg=params_msg))

        # resolution
        W = max(1, int(width_mm  * lines_per_mm))
        H = max(1, int(height_mm * lines_per_mm))
        self.step = 1.0 / lines_per_mm
        self.spacing = self.step * self.overlap

        # --- PREPARE IMAGE (quantized) ---
        img = self.image.convert("RGB")
        img = img.resize((W, H), resample=Image.Resampling.LANCZOS)
        img_q = (
            self.image.convert("RGBA")
                .resize((W, H), resample=Image.Resampling.LANCZOS)
                .convert("P", palette=Image.Palette.ADAPTIVE, colors=number_of_colors)
                .convert("RGBA")
        )
        arr = np.array(img_q)  # H x W x 4

        # Collect unique colors
        flat = arr.reshape(-1, 4)
        unique_colors = np.unique(flat, axis=0)


        filename = f"{self.name}_output"
        self.actions_path = os.path.join(tempfile.gettempdir(), f"{filename}.jsonl")
        self.svg_path   = os.path.join(tempfile.gettempdir(), f"{filename}.svg")
        self.gcode_path = os.path.join(tempfile.gettempdir(), f"{filename}.gcode")

        # Basic machine setup
        self.emit_action(self.machine.set_units())
        self.emit_action(self.machine.move(rapid=False, F=self.feedrate))
        self.emit_action(self.tool.up())
        self.is_up = True
        self.emit_action(self.machine.move(rapid=True, X=0, Y=0))
        self.emit_action(self.machine.set_position(X=0, Y=0))

        img_ini_pos = [self.offset_x, self.offset_y]
        robot_xyz   = [0, 0, 0]

        color_shapes = {}  # (r,g,b) -> [shape, shape, ...]

        # --- PER-COLOR VECTORIZATION ---
        for u_c,color in enumerate(unique_colors):
            self.check_stop()
            # progress per color
            percent = int((u_c / max(1, len(unique_colors) - 1)) * 100)
            self.emit_progress(percent, {"color": color, "lines_total": len(unique_colors)})
            #r, g, b, a = map(int, color)
            mask = np.all(arr == color, axis=-1)  # True where pixel == this RGBA
            #self.emit_action(self.machine.a_set("Comment", msg=f"Vectorizing color {r},{g},{b},{a}"))

            # Build mask for this color
            mask = np.all(arr == color, axis=-1)  # H x W bool

            if not mask.any():
                continue

            # find contours on mask
            contours = measure.find_contours(mask.astype(float), level=contour_level)
            contours = sort_contours_by_proximity(contours)

            shapes_for_color = []
            for n_c, c in enumerate(contours):
                self.check_stop()
                if len(c) < 3:
                    continue
                # simplify if needed
                if rdp_shape_simplification > 0:
                    c = measure.approximate_polygon(c, tolerance=rdp_shape_simplification)
                    if len(c) < 3:
                        continue
                    # smooth
                    if smooth_passes > 0:
                        c = chaikin(c, smooth_passes)
                pts = [(float(x), float(y)) for (y, x) in c]
                # close loop
                if pts[0] != pts[-1]:
                    pts.append(pts[0])
                sub = []
                for i in range(len(pts)-1):
                    sub.append((pts[i], pts[i+1]))
                shapes_for_color.append(sub)


            if shapes_for_color:
                color_shapes[tuple(color)] = shapes_for_color

        # color_shapes: { (r,g,b,a): [subshape, ...], ... }

        # --- OPTIONAL: SAVE SVG PER COLOR OR COMBINED ---
        # You can reuse your SVG helpers from vectorize_fill or vectorize_cut here.

        # --- APPLY FILLS USING YOUR EXISTING FILL LOGIC ---
        # This mirrors _to_gcode_contiguous_emit from VectorizeFillTechnique,
        # but now per color using color_shapes.

        for color, shapes in color_shapes.items():
            self.check_stop()

            pixel = safe_pixel_from_color(color)
            power = pixel_to_power(pixel, self.min_power, self.max_power, self.p_mode, invert)
            feedrate = pixel_to_feedrate(pixel, self.feedrate,
                                               self.min_rate, self.max_rate, self.fr_mode, invert)

            self.emit_action(self.machine.a_set(
                "Message",
                msg=f"Color {color} with S{power} F{feedrate}"
            ))

            for shape in shapes:
                self.check_stop()
                brightness = pixel / 255.0
                closed_shape = generate_none_fill([shape], self.spacing)

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
                    new_shape = generate_contour_hatched_fill(closed_shape, self.spacing, angle, False)
                elif self.fill_method == "contour_crosshatch":
                    angle = 45 + 90 * brightness
                    spacing = self.spacing * (1 + brightness)
                    new_shape = generate_contour_hatched_fill(closed_shape, spacing, angle, True)
                else:
                    new_shape = closed_shape

                # draw subshapes same as in vectorize_fill
                for n_s,sub_shape in enumerate(new_shape):
                    self.check_stop()
                    # progress per color
                    percent = int((n_s / max(1, len(new_shape) - 1)) * 100)
                    self.emit_progress(percent, {"color": color, "lines_total": len(unique_colors)})
                    self.draw_subshapes(sub_shape, power, feedrate, img_q, img_ini_pos, robot_xyz, self.step)

        self.emit_status(f"Finished {self.name}.\nGCODE: {self.gcode_path}")
    
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
    
        

