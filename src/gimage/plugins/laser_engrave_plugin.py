from .plugin_base import GImageTechniqueBase
from PIL import Image

class RasterTechnique(GImageTechniqueBase):
    name = "laser_engrave"

    # ------------------------------------------------------------
    # PROCESS ENTRY POINT
    # ------------------------------------------------------------
    def process(self):
        self._emit_header()
        self._load_config()
        self._emit_parameters()
        self._prepare_raster_grid()
        self._prepare_image()
        self._prepare_scan_pattern()
        self._run_raster_loop()
        self.set_exit_config()
        self.emit_status("Raster finished")

    # ------------------------------------------------------------
    # CONFIG
    # ------------------------------------------------------------
    def _load_config(self):
        cfg = self.config

        interface_name = self.ch.get_name_from_id(self.ch.id)
        mytechnique = cfg.get_value(["technique","technique_type","value"])
        self.emit_action(self.machine.a_set("Comment", msg=f"Technique {mytechnique}"))
        self.emit_action(self.machine.a_set("Comment", msg=f"Using interface {interface_name}"))

        # Technique parameters
        self.lines_per_mm = cfg.get_value(["technique","lines_per_mm","value"])
        self.direction     = cfg.get_value(["technique","direction","value"])
        self.recovery_mm   = cfg.get_value(["technique","recovery_distance","value"])
        self.mode          = "continuous"

        self.min_power, self.max_power = cfg.get_value(["technique","power_range","value"])
        self.feedrate = cfg.get_value(["technique","rate","value"])

        # Output geometry
        self.width_mm, self.height_mm, _ = cfg.get_value(["output","image_size","value"])
        self.offset_x, self.offset_y, _  = cfg.get_value(["output","image_offset","value"])

        # G-code formatting
        self.gcode_floating_decimals = cfg.get_value(["output","gcode_floating_decimals","value"]) or 3
        self.gcode_minimize_code = cfg.get_value(["output","gcode_minimize_code","value"]) or True

    # ------------------------------------------------------------
    # HEADER
    # ------------------------------------------------------------
    def _emit_header(self):
        self.emit_action(self.machine.set_units())
        self.emit_action(self.machine.move(rapid=False, F=self.config.get_value(["technique","rate","value"])))
        self.emit_action(self.tool.up())

        # Move to origin
        self.emit_action(self.machine.move(rapid=True, X=0, Y=0))
        self.emit_action(self.machine.set_position(X=0, Y=0))
    
    def _emit_parameters(self):
        params_msg = (
            f"Settings rate:{self.feedrate}, "
            f"lpmm:{self.lines_per_mm}, "
            f"dir:{self.direction}, "
            f"rec:{self.recovery_mm}, "
            f"minp:{self.min_power}, "
            f"maxp:{self.max_power}, "
            f"offset:({self.offset_x},{self.offset_y}), "
            f"size:({self.width_mm}x{self.height_mm}), "
            f"gdec:{self.gcode_floating_decimals}, "
            f"mincode:{self.gcode_minimize_code}"
        )
        self.emit_action(self.machine.a_set("Comment", msg=params_msg))


    # ------------------------------------------------------------
    # RASTER GRID
    # ------------------------------------------------------------
    def _prepare_raster_grid(self):
        self.W = max(1, int(self.width_mm  * self.lines_per_mm))
        self.H = max(1, int(self.height_mm * self.lines_per_mm))
        self.step = 1.0 / self.lines_per_mm

    # ------------------------------------------------------------
    # IMAGE PREPARATION
    # ------------------------------------------------------------
    def _prepare_image(self):
        img = self.image.convert("RGB")
        img = img.resize((self.W, self.H), resample=Image.Resampling.LANCZOS)
        img = img.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
        self.img = img

    # ------------------------------------------------------------
    # SCAN PATTERN
    # ------------------------------------------------------------
    def _prepare_scan_pattern(self):
        self.scan = self._scan_generator(self.direction, self.W, self.H)
        self.total_lines = self.W + self.H if self.direction == "diagonal" else max(self.W, self.H)

    # ------------------------------------------------------------
    # MAIN RASTER LOOP
    # ------------------------------------------------------------
    def _run_raster_loop(self):
        rr = self._rr
        last_power = 0
        last_Xmm = -1e9
        last_Ymm = -1e9

        for line_index, line in enumerate(self.scan):
            self.check_stop()
            if not line:
                continue

            start_x, start_y, end_x, end_y = self._compute_line_bounds(line)

            # Move to start
            self.emit_action(self.tool.up())
            self.emit_action(self.machine.move(rapid=True, X=start_x, Y=start_y))
            last_Xmm, last_Ymm = start_x, start_y
            drawing = False

            # Process pixels
            for (x, y) in line:
                pixel = self.img.getpixel((x, y))
                power = self._pixel_to_power(pixel)

                Xmm = rr(self.offset_x + x * self.step)
                Ymm = rr(self.offset_y + y * self.step)

                if power > 0:
                    if not drawing:
                        self.emit_action(self.tool.down(power=power))
                        drawing = True

                    self._emit_move_minimized(Xmm, Ymm, power, last_Xmm, last_Ymm, last_power)

                    last_power = power
                    last_Xmm = Xmm
                    last_Ymm = Ymm

                else:
                    if drawing:
                        self.emit_action(self.tool.up())
                        drawing = False

            if drawing:
                self.emit_action(self.tool.up())

            # Move to overscan end
            self.emit_action(self.machine.move(rapid=True, X=end_x, Y=end_y))
            last_Xmm, last_Ymm = end_x, end_y

            # Progress
            percent = int((line_index / max(1, self.total_lines - 1)) * 100)
            self.emit_progress(percent, {"line": line_index, "lines_total": self.total_lines})

    # ------------------------------------------------------------
    # HELPERS
    # ------------------------------------------------------------
    def _rr(self, value: float) -> float:
        return float(f"{value:.{self.gcode_floating_decimals}f}")

    def _compute_line_bounds(self, line):
        rr = self._rr
        xs = [p[0] for p in line]
        ys = [p[1] for p in line]

        x_min, x_max = min(xs), max(xs)
        y_min, y_max = min(ys), max(ys)

        start_x = rr(self.offset_x + xs[0] * self.step)
        start_y = rr(self.offset_y + ys[0] * self.step)
        end_x   = rr(self.offset_x + xs[-1] * self.step)
        end_y   = rr(self.offset_y + ys[-1] * self.step)

        is_horizontal = (y_min == y_max)
        is_vertical   = (x_min == x_max)

        xdir = 1 if xs[-1] >= xs[0] else -1
        ydir = 1 if ys[-1] >= ys[0] else -1

        # Overscan logic
        if self.direction == "horizontal" and is_horizontal:
            end_x += xdir * self.recovery_mm

        if self.direction == "vertical" and is_vertical:
            end_y += ydir * self.recovery_mm

        if self.direction in ("diagonal"):
            end_x += xdir * self.recovery_mm
            end_y += ydir * self.recovery_mm

        if self.direction in ("spiralin", "spiralout"):
            end_x += xdir * self.recovery_mm
            end_y += ydir * self.recovery_mm

        return start_x, start_y, end_x, end_y

    def _emit_move_minimized(self, Xmm, Ymm, power, last_Xmm, last_Ymm, last_power):
        if not self.gcode_minimize_code:
            self.emit_action(self.machine.move(rapid=False, X=Xmm, Y=Ymm, S=int(power)))
            return

        dx = (Xmm != last_Xmm)
        dy = (Ymm != last_Ymm)
        dp = (power != last_power)

        if not dx and not dy and not dp:
            return

        params = {}
        if dx: params["X"] = Xmm
        if dy: params["Y"] = Ymm
        if dp: params["S"] = int(power)

        self.emit_action(self.machine.move(rapid=False, **params))

    # ------------------------------------------------------------
    # PIXEL → POWER
    # ------------------------------------------------------------
    def _pixel_to_power(self, pixel):
        if isinstance(pixel, tuple):
            pixel = sum(pixel) / len(pixel)

        brightness = pixel / 255.0
        inv = 1.0 - brightness
        return int(self.min_power + inv * (self.max_power - self.min_power))
    
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
