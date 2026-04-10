from .plugin_base import GImageTechniqueBase
import potrace
import numpy as np
from PIL import Image
import os, tempfile

class VectorizeCutTechnique(GImageTechniqueBase):
    name = "vectorize_cut"

    def process(self):
        print(f"Entered {self.name} plugin")

        cfg = self.config
        interface_name = self.ch.get_name_from_id(self.ch.id)
        self.emit_action(self.machine.a_set("Comment", msg=f"Using interface {interface_name}"))

        # --- CONFIG ---
        self.power = cfg.get_value(["technique", "cut_power", "value"]) or 1000
        self.feedrate = cfg.get_value(["technique", "cut_feedrate", "value"]) or 800
        self.gcode_floating_decimals = cfg.get_value(["output","gcode_floating_decimals","value"]) or 3

        width_mm, height_mm, _ = cfg.get_value(["output","image_size","value"])
        self.offset_x, self.offset_y, _ = cfg.get_value(["output","image_offset","value"])
        lines_per_mm = cfg.get_value(["technique","lines_per_mm","value"]) or 1

        # resolution
        W = max(1, int(width_mm  * lines_per_mm))
        H = max(1, int(height_mm * lines_per_mm))
        self.step = 1.0 / lines_per_mm

        # --- Prepare image ---
        img = self.image.convert("L")  # grayscale
        img = img.resize((W, H), resample=Image.Resampling.LANCZOS)
        bw = img.point(lambda p: 0 if p < 128 else 255, '1')

        bitmap = potrace.Bitmap(np.array(bw))
        traced = bitmap.trace()

        # Output paths
        filename = f"{self.name}_output"
        self.svg_path   = os.path.join(tempfile.gettempdir(), f"{filename}.svg")
        self.gcode_path = os.path.join(tempfile.gettempdir(), f"{filename}.gcode")

        # --- Generate SVG ---
        svg_text = self._paths_to_svg(traced, W, H)
        with open(self.svg_path, "w") as f:
            f.write(svg_text)

        # --- Generate G-code ---
        self.emit_action(self.machine.home())
        self.emit_action(self.tool.up())
        self.emit_action(self.machine.move(rapid=True, X=0, Y=0))
        self.emit_action(self.machine.set_position(X=0, Y=0))

        self._paths_to_gcode(traced, img)

        self.emit_status(f"Finished vectorize_cut.\nSVG: {self.svg_path}\nGCODE: {self.gcode_path}")

    # ----------------------------------------------------------------------

    def _paths_to_svg(self, path, W, H):
        """Convert potrace paths to a simple SVG."""
        svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">']

        p = path
        while p:
            curve = p.curve
            d = []

            # Move to first point
            x0, y0 = curve.c[0][1]
            d.append(f"M {x0} {y0}")

            for i in range(curve.n):
                tag = curve.tag[i]
                pts = curve.c[i]

                if tag == potrace.POTRACE_CORNER:
                    # corner: two points
                    d.append(f"L {pts[1][0]} {pts[1][1]}")
                    d.append(f"L {pts[2][0]} {pts[2][1]}")
                else:
                    # curve: 3 control points
                    d.append(f"C {pts[0][0]} {pts[0][1]} {pts[1][0]} {pts[1][1]} {pts[2][0]} {pts[2][1]}")

            d.append("Z")
            svg.append(f'<path d="{" ".join(d)}" fill="none" stroke="black"/>')

            p = p.next

        svg.append("</svg>")
        return "\n".join(svg)

    # ----------------------------------------------------------------------

    def _paths_to_gcode(self, path, im):
        """Convert potrace paths to G-code using your movement system."""
        p = path
        while p:
            curve = p.curve

            # First point
            x0, y0 = curve.c[0][1]
            x0, y0 = self._px_to_xy(im, x0, y0)

            self.emit_action(self.tool.up())
            self.emit_action(self.machine.move(rapid=True, X=x0, Y=y0, F=self.feedrate))
            self.emit_action(self.tool.down(power=self.power))

            # Follow segments
            for i in range(curve.n):
                pts = curve.c[i]
                # end point of segment
                x, y = pts[-1]
                x, y = self._px_to_xy(im, x, y)
                self.emit_action(self.machine.move(rapid=False, X=x, Y=y, F=self.feedrate, S=self.power))

            # close
            self.emit_action(self.tool.up())
            p = p.next

    # ----------------------------------------------------------------------

    def _px_to_xy(self, im, x, y):
        """Convert pixel → machine coordinates."""
        y = (im.height - 1) - y
        x = x * self.step + self.offset_x
        y = y * self.step + self.offset_y
        return (self._rr(x), self._rr(y))

    def _rr(self, v):
        return float(f"{v:.{self.gcode_floating_decimals}f}")
