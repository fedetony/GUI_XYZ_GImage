from .plugin_base import GImageTechniqueBase
import numpy as np
from PIL import Image
import os, tempfile
from skimage import measure # pip install scikit-image
from ._vectorize_shared import *

class VectorizeCutTechnique(GImageTechniqueBase):
    name = "vectorize_cut"

    def process(self):
        print(f"Entered {self.name} plugin")
        mytechnique=self.config.get_value(["technique","technique_type","value"])
        self.emit_action(self.machine.a_set("Comment",msg=f"Technique {mytechnique}"))
        cfg = self.config
        interface_name = self.ch.get_name_from_id(self.ch.id)
        self.emit_action(self.machine.a_set("Comment", msg=f"Using interface {interface_name}"))

        # --- CONFIG ---
        self.min_power_cut, self.max_power_cut = cfg.get_value(["technique","cut_power_range","value"])
        self.power = self.max_power_cut

        self.feedrate = cfg.get_value(["technique", "rate", "value"])
        if self.feedrate is None:
            self.feedrate = 800

        self.gcode_floating_decimals = cfg.get_value(["output","gcode_floating_decimals","value"])
        if self.gcode_floating_decimals is None:
            self.gcode_floating_decimals = 3

        width_mm, height_mm, _ = cfg.get_value(["output","image_size","value"])
        self.offset_x, self.offset_y, _ = cfg.get_value(["output","image_offset","value"])

        lines_per_mm = cfg.get_value(["technique","lines_per_mm","value"])
        if lines_per_mm is None:
            lines_per_mm = 1

        # NEW CONFIG PARAMETERS
        threshold = cfg.get_value(["technique","threshold","value"])
        if threshold is None:
            threshold = 128

        contour_level = cfg.get_value(["technique","contour_level","value"])
        if contour_level is None:
            contour_level = 0.5

        simplify_tol = cfg.get_value(["technique","rdp_shape_simplification","value"])
        if simplify_tol is None:
            simplify_tol = 2.0

        smooth_passes = cfg.get_value(["technique","smooth_passes","value"])
        if smooth_passes is None:
            smooth_passes = 1

        invert = cfg.get_value(["technique","invert","value"])
        if invert is None:
            invert = False

        params_msg = (
            f"Settings rate:{self.feedrate},lpmm:{lines_per_mm},"
            f"th:{threshold},c_l:{contour_level},rdp:{simplify_tol},"
            f"s_p:{smooth_passes},inv:{invert}"
        )
        self.emit_action(self.machine.a_set("Comment", msg=params_msg))

        # resolution
        W = max(1, int(width_mm  * lines_per_mm))
        H = max(1, int(height_mm * lines_per_mm))
        self.step = 1.0 / lines_per_mm

        # --- Prepare image ---
        img = self.image.convert("L")  # grayscale
        img = img.resize((W, H), resample=Image.Resampling.LANCZOS)

        arr = np.array(img)

        # invert if needed
        if invert:
            arr = 255 - arr

        # binary mask
        bw = arr < threshold

        # --- Vectorize using skimage ---
        contours = measure.find_contours(bw, level=contour_level) # 0.5

        # Simplify + smooth
        processed = []
        for c in contours:
            if len(c) < 3:
                continue

            # simplify
            if simplify_tol > 0:
                c = measure.approximate_polygon(c, tolerance=simplify_tol)

            # smooth
            if smooth_passes > 0:
                c = chaikin(c, smooth_passes)

            processed.append(c)

        #Sort the paths
        processed = sort_contours_by_proximity(processed)

        # Output paths
        filename = f"{self.name}_output"
        self.svg_path   = os.path.join(tempfile.gettempdir(), f"{filename}.svg")
        self.gcode_path = os.path.join(tempfile.gettempdir(), f"{filename}.gcode")

        # --- Generate SVG ---
        svg_text = self._contours_to_svg(processed, W, H)
        with open(self.svg_path, "w") as f:
            f.write(svg_text)

        # --- Generate G-code ---
        self.emit_action(self.machine.set_units())
        self.emit_action(self.tool.up())
        self.emit_action(self.machine.move(rapid=True, X=0, Y=0))
        self.emit_action(self.machine.set_position(X=0, Y=0))

        self._contours_to_gcode(processed, img)
        self.set_exit_config()
        self.emit_status(f"Finished vectorize_cut.\nSVG: {self.svg_path}\nGCODE: {self.gcode_path}")

    # ----------------------------------------------------------------------

    def _contours_to_svg(self, contours, W, H):
        """Convert skimage contours to SVG."""
        svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">']

        for contour in contours:
            if len(contour) < 2:
                continue

            d = []
            y0, x0 = contour[0]
            d.append(f"M {x0:.2f} {y0:.2f}")

            for (y, x) in contour[1:]:
                d.append(f"L {x:.2f} {y:.2f}")

            d.append("Z")
            svg.append(f'<path d="{" ".join(d)}" fill="none" stroke="black"/>')

        svg.append("</svg>")
        return "\n".join(svg)

    # ----------------------------------------------------------------------

    def _contours_to_gcode(self, contours, im):
        """Convert skimage contours to G-code."""
        for contour in contours:
            if len(contour) < 2:
                continue

            # First point
            y0, x0 = contour[0]
            x0, y0 = self._px_to_xy(im, x0, y0)

            self.emit_action(self.tool.up())
            self.emit_action(self.machine.move(rapid=True, X=x0, Y=y0, F=self.feedrate))
            self.emit_action(self.tool.down(power=self.power))

            # Follow contour
            for (y, x) in contour[1:]:
                x, y = self._px_to_xy(im, x, y)
                self.emit_action(self.machine.move(rapid=False, X=x, Y=y, F=self.feedrate, S=self.power))

            # close
            self.emit_action(self.tool.up())

    # ----------------------------------------------------------------------

    def _px_to_xy(self, im, x, y):
        """Convert pixel → machine coordinates."""
        y = (im.height - 1) - y
        x = x * self.step + self.offset_x
        y = y * self.step + self.offset_y
        return (self._rr(x), self._rr(y))

    def _rr(self, v):
        return float(f"{v:.{self.gcode_floating_decimals}f}")
    

