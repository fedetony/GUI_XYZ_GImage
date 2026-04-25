
from .plugin_base import GImageTechniqueBase

class LineingTechnique(GImageTechniqueBase):
    name = "lineing"   # must match config

    def process(self):
        """
        Perform a line-by-line raster traversal of the image, emitting
        abstract movement and tool actions. The machine and tool plugins
        determine how these actions translate into real motion or tool
        engagement.
        """

        self.emit_status("Starting Lineing")
        self.emit_action({"action": "Message", "parameters": {"msg": "Starting Lineing"}})

        # --- Load configuration ---
        cfg = self.config
        resolution = cfg.get_value(["technique","resolution", "value"])
        direction   = cfg.get_value(["technique", "direction", "value"])  # e.g. "horizontal"
        threshold   = cfg.get_value(["technique", "threshold", "value"])  # grayscale threshold
        feedrate    = cfg.get_value(["technique", "feedrate", "value"])

        width, height = self.image.width, self.image.height
        # Set machine Feedrate
        self.emit_action(self.machine.set_units())
        self.emit_action(self.machine.move(rapid=False,F=feedrate))
        # Raise tool to moving height
        self.emit_action(self.tool.up())
        self.is_up=True

        # --- Main raster loop ---
        for y in range(height):

            self.check_stop()  # allow cancellation

            # serpentine pattern
            if y % 2 == 0:
                x_range = range(width)
            else:
                x_range = reversed(range(width))

            # Move to start of line
            x0 = next(iter(x_range))
            Ximg, Yimg = self._pixel_to_xy(x0, y, resolution)
            self.emit_action(self.machine.move(rapid=True, X=Ximg, Y=Yimg))

            # Tool up at start of each line
            if not self.is_up:
                self.emit_action(self.tool.up())
                self.is_up=True

            drawing = False

            for x in x_range:
                self.check_stop()

                pixel = self.image.getpixel((x, y))
                should_draw = self._pixel_is_dark(pixel, threshold)

                Ximg, Yimg = self._pixel_to_xy(x, y, resolution)

                if should_draw:
                    if not drawing:
                        # start stroke
                        self.emit_action(self.tool.down(power=self._power_from_pixel(pixel)))
                        self.is_up=False
                        drawing = True

                    # draw move
                    self.emit_action(self.machine.move(rapid=False,X=Ximg, Y=Yimg))

                else:
                    if drawing:
                        # end stroke
                        self.emit_action(self.tool.up())
                        self.is_up=True
                        drawing = False

            # ensure tool is up at end of line
            if drawing:
                if not self.is_up:
                    self.emit_action(self.tool.up())
                    self.is_up=True

            # optional: progress per line
            percent = int((y / max(1, height - 1)) * 100)
            self.emit_progress(percent, {"line": y, "lines_total": height})

        self.emit_status("Lineing finished")

    def _pixel_to_xy(self, x, y, res):
        return x * res, y * res

    def _pixel_is_dark(self, pixel, threshold):
        # pixel may be grayscale or RGB
        if isinstance(pixel, tuple):
            pixel = sum(pixel) / len(pixel)
        return pixel < threshold

    def _power_from_pixel(self, pixel):
        # map pixel brightness to tool power
        if isinstance(pixel, tuple):
            pixel = sum(pixel) / len(pixel)
        return int(255 - pixel)  # example mapping
