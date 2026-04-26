from .plugin_base import GImageTechniqueBase
from PIL import Image

class CNCRasterTechnique(GImageTechniqueBase):
    name = "cnc_engrave"

    def process(self):
        self._emit_header()
        self._load_config()
        self._emit_parameters()
        self._prepare_raster_grid()
        self._prepare_image()
        self._prepare_scan_pattern()

        self._run_raster_loop()

        self.set_exit_config()
        self.emit_status("CNC Raster finished")

    def _emit_header(self):
        interface_name = self.ch.get_name_from_id(self.ch.id)
        mytechnique = self.config.get_value(["technique","technique_type","value"])

        self.emit_action(self.machine.a_set("Comment", msg=f"Technique {mytechnique}"))
        self.emit_action(self.machine.a_set("Comment", msg=f"Using interface {interface_name}"))

    def _load_config(self):
        cfg = self.config

        self.tool_tip_size = cfg.get_value(["tool","tool_tip_size","value"]) or 1
        self.overlap = cfg.get_value(["technique","overlap","value"]) or 1
        self.lines_per_mm = self.overlap  / self.tool_tip_size

        self.direction = cfg.get_value(["technique","direction","value"])
        self.recovery_mm = cfg.get_value(["technique","recovery_distance","value"])

        _, self.max_power = cfg.get_value(["technique","power_range","value"])
        self.feedrate = cfg.get_value(["technique","rate","value"])

        self.width_mm, self.height_mm, _ = cfg.get_value(["output","image_size","value"])
        self.offset_x, self.offset_y, _  = cfg.get_value(["output","image_offset","value"])

        self.gcode_floating_decimals = cfg.get_value(["output","gcode_floating_decimals","value"]) or 3
        self.gcode_minimize_code = cfg.get_value(["output","gcode_minimize_code","value"]) or True

        self.touch_pos = cfg.get_value(["tool","touch_z","value"])
        self.retract_pos = cfg.get_value(["tool","retract_z","value"])
        # Infer machine Z direction
        self.z_positive_is_up = self.retract_pos > self.touch_pos
        # Normalize Z range
        z1, z2 = cfg.get_value(["technique","z_depth_range","value"])
        self.min_z = min(z1, z2)
        self.max_z = max(z1, z2)

        # Pixel inversion (brightness mapping only)
        self.invert_depth = cfg.get_value(["technique","invert_depth","value"]) or False

        # Enforce retract safety based on machine direction
        if self.z_positive_is_up:
            # Tool moves DOWN into material
            # retract_pos must be ABOVE max_z
            if self.retract_pos < self.max_z:
                self.emit_action(self.machine.a_set(
                    "Comment",
                    msg=f"Warning: Retract Z {self.retract_pos} inside work range, correcting to {self.max_z}"
                ))
                self.retract_pos = self.max_z
        else:
            # Tool moves UP into material
            # retract_pos must be BELOW min_z
            if self.retract_pos > self.min_z:
                self.emit_action(self.machine.a_set(
                    "Comment",
                    msg=f"Warning: Retract Z {self.retract_pos} inside work range, correcting to {self.min_z}"
                ))
                self.retract_pos = self.min_z

        

    
    def _emit_parameters(self):
        # parameters message
        params_msg = (
            f"Settings rate:{self.feedrate},lpmm:{self.lines_per_mm},dir:{self.direction},"
            f"rec:{self.recovery_mm},minz:{self.min_z},maxz:{self.max_z},"
            f"p:{self.max_power},overlap:{self.overlap},inv:{self.invert_depth}"
        )
        self.emit_action(self.machine.a_set("Comment", msg=params_msg))

    def _prepare_raster_grid(self):
        self.W = max(1, int(self.width_mm  * self.lines_per_mm))
        self.H = max(1, int(self.height_mm * self.lines_per_mm))
        self.step = 1.0 / self.lines_per_mm

        self.emit_action(self.machine.set_units())
        self.emit_action(self.machine.move(rapid=False, F=self.feedrate))

        self.emit_action(self.tool.up(z=self.retract_pos))
        self.is_up = True

        self.emit_action(self.machine.move(rapid=True, X=0, Y=0))
    
    def _prepare_image(self):
        img = self.image.convert("RGB")
        img = img.resize((self.W, self.H), resample=Image.Resampling.LANCZOS)
        img = img.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
        self.img = img

    def _prepare_scan_pattern(self):
        self.scan = self._scan_generator(self.direction, self.W, self.H)
        self.total_lines = (
            self.W + self.H if self.direction == "diagonal" else max(self.W, self.H)
        )

    def _run_raster_loop(self):
        rr = self._rr

        last_Xmm = last_Ymm = -1e9
        last_Zmm = self.retract_pos

        for line_index, line in enumerate(self.scan):
            self.check_stop()
            if not line:
                continue

            start_x, start_y, end_x, end_y = self._compute_line_bounds(line)

            # Move to start
            if not self.is_up:
                self.emit_action(self.tool.up(z=self.retract_pos))
                self.is_up = True

            self.emit_action(self.machine.move(rapid=True, X=start_x, Y=start_y))

            drawing = False

            for (x, y) in line:
                pixel = self.img.getpixel((x, y))
                depth = self._pixel_to_depth(pixel)

                Xmm = rr(self.offset_x + x * self.step)
                Ymm = rr(self.offset_y + y * self.step)
                Zmm = rr(depth)

                if not drawing:
                    self.emit_action(self.tool.down(z=Zmm))
                    self.is_up = False
                    drawing = True

                self._emit_move_minimized(Xmm, Ymm, Zmm, last_Xmm, last_Ymm, last_Zmm)

                last_Xmm, last_Ymm, last_Zmm = Xmm, Ymm, Zmm

            # End of line
            if drawing and not self.is_up:
                self.emit_action(self.tool.up())
                self.is_up = True

            self.emit_action(self.machine.move(rapid=True, X=end_x, Y=end_y))

            percent = int((line_index / max(1, self.total_lines - 1)) * 100)
            self.emit_progress(percent, {"line": line_index, "lines_total": self.total_lines})
    
    def _rr(self, value: float) -> float:
        return float(f"{value:.{self.gcode_floating_decimals}f}")

    def _emit_move_minimized(self, Xmm, Ymm, Zmm, last_Xmm, last_Ymm, last_Zmm):
        # Full G-code mode → always emit all axes
        if not self.gcode_minimize_code:
            self.emit_action(self.machine.move(
                rapid=False, X=Xmm, Y=Ymm, Z=Zmm
            ))
            return

        dx = (Xmm != last_Xmm)
        dy = (Ymm != last_Ymm)
        dz = (Zmm != last_Zmm)

        # Nothing changed → skip
        if not dx and not dy and not dz:
            return

        params = {}
        if dx: params["X"] = Xmm
        if dy: params["Y"] = Ymm
        if dz: params["Z"] = Zmm

        self.emit_action(self.machine.move(rapid=False, **params))

    def _compute_line_bounds(self, line):
        rr = self._rr
        step = self.step
        direction = self.direction
        recovery_mm = self.recovery_mm

        xs = [p[0] for p in line]
        ys = [p[1] for p in line]

        x_min, x_max = min(xs), max(xs)
        y_min, y_max = min(ys), max(ys)

        # Default start/end
        start_x = rr(self.offset_x + xs[0] * step)
        start_y = rr(self.offset_y + ys[0] * step)
        end_x   = rr(self.offset_x + xs[-1] * step)
        end_y   = rr(self.offset_y + ys[-1] * step)

        is_horizontal = (y_min == y_max)
        is_vertical   = (x_min == x_max)

        xdir = 1 if (xs[-1] - xs[0]) >= 0 else -1
        ydir = 1 if (ys[-1] - ys[0]) >= 0 else -1

        # Horizontal / vertical overscan
        if direction == "horizontal" and is_horizontal:
            end_x += xdir * recovery_mm

        if direction == "vertical" and is_vertical:
            end_y += ydir * recovery_mm

        # Spiral overscan
        if direction in ("spiralin", "spiralout"):
            if is_horizontal and xdir == 1:
                end_x = rr(self.offset_x + xs[-1] * step + xdir * recovery_mm)
                end_y = rr(self.offset_y + ys[-1] * step - ydir * recovery_mm)
            elif is_vertical and ydir == 1:
                end_x = rr(self.offset_x + xs[-1] * step + xdir * recovery_mm)
                end_y = rr(self.offset_y + ys[-1] * step + ydir * recovery_mm)
            elif is_horizontal and xdir == -1:
                end_x = rr(self.offset_x + xs[-1] * step + xdir * recovery_mm)
                end_y = rr(self.offset_y + ys[-1] * step + ydir * recovery_mm)
            elif is_vertical and ydir == -1:
                end_x = rr(self.offset_x + xs[-1] * step - xdir * recovery_mm)
                end_y = rr(self.offset_y + ys[-1] * step + ydir * recovery_mm)

        # Diagonal overscan
        if direction == "diagonal":
            end_x = rr(self.offset_x + xs[-1] * step + xdir * recovery_mm)
            end_y = rr(self.offset_y + ys[-1] * step + ydir * recovery_mm)

        return start_x, start_y, end_x, end_y

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

    def _pixel_to_depth(self, pixel):
        if isinstance(pixel, tuple):
            pixel = sum(pixel) / len(pixel)
        # continuous grayscale
        brightness = pixel / 255.0
        if self.invert_depth:
            inv=brightness
        else:
            inv = 1.0 - brightness
        return self.min_z + inv * (self.max_z - self.min_z)

    