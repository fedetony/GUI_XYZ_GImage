from .plugin_base import GImageTechniqueBase
from PIL import Image

class RasterTechnique(GImageTechniqueBase):
    name = "laser_engrave"

    def process(self):

        cfg = self.config
        interface_name=self.ch.get_name_from_id(self.ch.id)
        self.emit_action(self.machine.a_set("Comment",msg=f"Using interface {interface_name}"))
        # --- CONFIG ---
        lines_per_mm = cfg.get_value(["technique","lines_per_mm","value"])
        direction     = cfg.get_value(["technique","direction","value"])
        recovery_mm   = cfg.get_value(["technique","recovery_distance","value"])
        mode          = "continuous" # cfg.get_value(["image","mode","value"])  # "continuous" or "threshold"

        min_power, max_power = cfg.get_value(["technique","power_range","value"])
        feedrate = cfg.get_value(["technique","rate","value"])

        width_mm, height_mm, _ = cfg.get_value(["output","image_size","value"])
        offset_x, offset_y, _  = cfg.get_value(["output","image_offset","value"])
        gcode_floating_decimals  = cfg.get_value(["output","gcode_floating_decimals","value"]) or 3
        gcode_minimize_code= cfg.get_value(["output","gcode_minimize_code","value"]) or True
        
        #origin_x, origin_y, _ =cfg.get_value(["output","image_origin","value"])

        # --- COMPUTE RASTER GRID ---
        W = max(1, int(width_mm  * lines_per_mm))
        H = max(1, int(height_mm * lines_per_mm))
        step = 1.0 / lines_per_mm
        
        # set feedrate
        self.emit_action(self.machine.move(rapid=False,F=feedrate))

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
        # PIL’s y=0 (top) becomes machine y=0 (bottom)
        img = img.transpose(Image.Transpose.FLIP_TOP_BOTTOM)

        # --- SELECT SCAN PATTERN ---
        scan = self._scan_generator(direction, W, H)

        total_lines = W + H if direction == "diagonal" else max(W, H)

        def rr(value:float):
            """Helper to set number of decimals to the gcode coordinates"""
            return float(f"{value:.{gcode_floating_decimals}f}")

        # --- MAIN LOOP ---
        last_power=0
        last_Xmm=-1e9
        last_Ymm=-1e9
        for line_index, line in enumerate(scan):

            self.check_stop()
            if not line:
                continue

            # Determine overscan
            xs = [p[0] for p in line]
            ys = [p[1] for p in line]
            x_min, x_max = min(xs), max(xs)
            y_min, y_max = min(ys), max(ys)

            # Default start/end
            start_x = rr(offset_x + x_min * step)
            start_y = rr(offset_y + y_min * step)
            end_x   = rr(offset_x + x_max * step)
            end_y   = rr(offset_y + y_max * step)

            # Overscan only for horizontal/vertical
            if direction == "horizontal" and all(y == y_min for y in ys):
                start_x -= recovery_mm
                end_x   += recovery_mm

            if direction == "vertical" and all(x == x_min for x in xs):
                start_y -= recovery_mm
                end_y   += recovery_mm

            # Move to start of line
            self.emit_action(self.tool.up())
            self.emit_action(self.machine.move(rapid=True,X=start_x, Y=start_y))
            last_Xmm=start_x
            last_Ymm=start_y
            drawing = False

            # --- PROCESS PIXELS IN THIS LINE ---
            for (x, y) in line:
                pixel = img.getpixel((x, y))
                power = self._pixel_to_power(pixel, min_power, max_power, mode)

                Xmm = rr(offset_x + x * step)
                Ymm = rr(offset_y + y * step)

                if power > 0:
                    if not drawing:
                        self.emit_action(self.tool.down(power=power))
                        drawing = True

                    if not gcode_minimize_code:
                        # Full G-code always
                        self.emit_action(self.machine.move(
                            rapid=False, X=Xmm, Y=Ymm, S=int(power)
                        ))
                    else:
                        # --- MINIMIZED G-CODE MODE ---
                        dx = (Xmm != last_Xmm)
                        dy = (Ymm != last_Ymm)
                        dp = (power != last_power)

                        # Nothing changed → skip
                        if not dx and not dy and not dp:
                            pass

                        else:
                            params = {}
                            if dx: params["X"] = Xmm
                            if dy: params["Y"] = Ymm
                            if dp: params["S"] = int(power)

                            self.emit_action(self.machine.move(
                                rapid=False, **params
                            ))

                    # Update last values
                    last_power = power
                    last_Xmm = Xmm
                    last_Ymm = Ymm

                else:
                    # Power == 0 → lift tool if needed
                    if drawing:
                        self.emit_action(self.tool.up())
                        drawing = False

            # End of line
            if drawing:
                self.emit_action(self.tool.up())

            # Move to overscan end
            self.emit_action(self.machine.move(rapid=True,X=end_x, Y=end_y))
            last_Xmm=end_x 
            last_Ymm=end_y

            # Progress
            percent = int((line_index / max(1, total_lines - 1)) * 100)
            self.emit_progress(percent, {"line": line_index, "lines_total": total_lines})

        self.emit_status("Raster finished")

    # ---------------- SCAN PATTERNS ----------------

    def _scan_generator(self, direction, W, H):
        direction = direction.lower()

        if direction == "horizontal":
            for y in range(H):
                if y % 2 == 0:
                    yield [(x, y) for x in range(W)]
                else:
                    yield [(x, y) for x in reversed(range(W))]

        elif direction == "vertical":
            for x in range(W):
                if x % 2 == 0:
                    yield [(x, y) for y in range(H)]
                else:
                    yield [(x, y) for y in reversed(range(H))]

        elif direction == "diagonal":
            for d in range(W + H - 1):
                line = []
                for x in range(max(0, d - (H - 1)), min(W - 1, d) + 1):
                    y = d - x
                    if 0 <= y < H:
                        line.append((x, y))
                if d % 2 == 1:
                    line.reverse()
                yield line

        elif direction in ("spiralin", "spiralout"):
            lines = self._spiral_lines(W, H)
            if direction == "spiralout":
                lines.reverse()
            for line in lines:
                yield line

        else:
            # fallback
            for y in range(H):
                yield [(x, y) for x in range(W)]

    def _spiral_lines(self, W, H):
        lines = []
        left, right = 0, W - 1
        top, bottom = 0, H - 1

        while left <= right and top <= bottom:
            lines.append([(x, top) for x in range(left, right + 1)])
            top += 1

            lines.append([(right, y) for y in range(top, bottom + 1)])
            right -= 1

            if top <= bottom:
                lines.append([(x, bottom) for x in range(right, left - 1, -1)])
                bottom -= 1

            if left <= right:
                lines.append([(left, y) for y in range(bottom, top - 1, -1)])
                left += 1

        return lines

    # ---------------- PIXEL → POWER ----------------

    def _pixel_to_power(self, pixel, min_p, max_p, mode):
        if isinstance(pixel, tuple):
            pixel = sum(pixel) / len(pixel)

        if mode == "threshold":
            return max_p if pixel < 128 else 0

        # continuous grayscale
        brightness = pixel / 255.0
        inv = 1.0 - brightness
        return int(min_p + inv * (max_p - min_p))
