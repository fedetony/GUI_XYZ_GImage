import math

class ShapeFactory:
    """
    Generates normalized polygon shapes (0..1 space).
    Useful for QGraphicsPolygonItem scaling inside a parent item.
    """

    # -----------------------------
    # Public API
    # -----------------------------
    @staticmethod
    def make(shape, direction="down", **kwargs):
        shape = shape.lower()

        if shape == "triangle":
            return ShapeFactory.triangle(direction)

        if shape == "polygon":
            sides = kwargs.get("sides", 6)
            return ShapeFactory.regular_polygon(sides, rotation=kwargs.get("rotation", 0))

        if shape == "pencil":
            return ShapeFactory.pencil(direction)

        if shape == "pen":
            return ShapeFactory.pen_nib(direction)

        if shape == "brush":
            return ShapeFactory.brush_tip(direction)

        if shape == "cnc":
            bit_type = kwargs.get("bit", "vbit")
            return ShapeFactory.cnc_bit(bit_type, direction)

        if shape == "laser":
            return ShapeFactory.laser_cone(direction)

        raise ValueError(f"Unknown shape '{shape}'")

    # -----------------------------
    # Basic shapes
    # -----------------------------
    @staticmethod
    def triangle(direction):
        direction = direction.lower()
        if direction == "up":
            return [(0.5, 0.0), (1.0, 1.0), (0.0, 1.0)]
        if direction == "down":
            return [(0.0, 0.0), (1.0, 0.0), (0.5, 1.0)]
        if direction == "left":
            return [(0.0, 0.5), (1.0, 0.0), (1.0, 1.0)]
        if direction == "right":
            return [(1.0, 0.5), (0.0, 0.0), (0.0, 1.0)]
        raise ValueError("Invalid triangle direction")

    # -----------------------------
    # Regular polygons (4–24 sides)
    # -----------------------------
    @staticmethod
    def regular_polygon(sides, rotation=0):
        """
        sides: number of sides (4..24)
        rotation: degrees
        """
        if sides < 3:
            raise ValueError("Polygon must have at least 3 sides")

        pts = []
        rot = math.radians(rotation)

        for i in range(sides):
            angle = 2 * math.pi * i / sides + rot
            x = 0.5 + 0.5 * math.cos(angle)
            y = 0.5 + 0.5 * math.sin(angle)
            pts.append((x, y))

        return pts

    # -----------------------------
    # Pencil shape
    # -----------------------------
    @staticmethod
    def pencil(direction):
        direction = direction.lower()
        if direction == "down":
            return [ (0.0, 1.0), (0.0, 0.2), (0.5, 0.0), (1.0, 0.2), (1.0, 1.0) ]
        if direction == "up":
            return [ (0.0, 0.0), (0.0, 0.8), (0.5, 1.0), (1.0, 0.8), (1.0, 0.0) ]
        raise ValueError("Invalid pencil direction")

    # -----------------------------
    # Pen nib (classic fountain pen)
    # -----------------------------
    @staticmethod
    def pen_nib(direction):
        direction = direction.lower()
        if direction == "down":
            return [
                (0.3, 0.0), (0.7, 0.0),
                (0.85, 0.5), (0.7, 1.0),
                (0.3, 1.0), (0.15, 0.5)
            ]
        if direction == "up":
            return [
                (0.3, 1.0), (0.7, 1.0),
                (0.85, 0.5), (0.7, 0.0),
                (0.3, 0.0), (0.15, 0.5)
            ]
        raise ValueError("Invalid pen direction")

    # -----------------------------
    # Brush tip (rounded)
    # -----------------------------
    @staticmethod
    def brush_tip(direction):
        # Just a semicircle + rectangle
        if direction == "down":
            return ShapeFactory.regular_polygon(12, rotation=90)  # semicircle-ish
        if direction == "up":
            return ShapeFactory.regular_polygon(12, rotation=-90)
        raise ValueError("Invalid brush direction")

    # -----------------------------
    # CNC bits
    # -----------------------------
    @staticmethod
    def cnc_bit(bit_type, direction):
        bit_type = bit_type.lower()
        direction = direction.lower()

        # V-bit (like a triangle)
        if bit_type == "vbit":
            return ShapeFactory.triangle(direction)

        # Endmill (rectangle)
        if bit_type == "endmill":
            return [(0.2, 0.0), (0.8, 0.0), (0.8, 1.0), (0.2, 1.0)]

        # Ball-nose (rounded bottom)
        if bit_type == "ball":
            top = [(0.2, 0.0), (0.8, 0.0)]
            bottom = ShapeFactory.regular_polygon(12, rotation=90)
            return top + bottom

        raise ValueError("Unknown CNC bit type")

    # -----------------------------
    # Laser cone
    # -----------------------------
    @staticmethod
    def laser_cone(direction):
        direction = direction.lower()
        if direction == "down":
            return [(0.4, 0.0), (0.6, 0.0), (0.8, 1.0), (0.2, 1.0)]
        if direction == "up":
            return [(0.2, 0.0), (0.8, 0.0), (0.6, 1.0), (0.4, 1.0)]
        raise ValueError("Invalid laser direction")
    
    @staticmethod    
    def rotate_points(points, angle_deg, center=(0.5, 0.5)):
        """
        Rotate normalized polygon points around a center point.
        
        points: list of (x, y)
        angle_deg: rotation angle in degrees
        center: rotation center (default = normalized center)
        """
        angle = math.radians(angle_deg)
        cx, cy = center

        rotated = []
        for x, y in points:
            # translate to origin
            tx = x - cx
            ty = y - cy

            # rotate
            rx = tx * math.cos(angle) - ty * math.sin(angle)
            ry = tx * math.sin(angle) + ty * math.cos(angle)

            # translate back
            rotated.append((rx + cx, ry + cy))

        return rotated

    @staticmethod
    def validate_polygon(points):
        """
        Validates a polygon for use in ShapeFactory.
        Checks:
            - at least 3 points
            - all points in 0..1 range
            - polygon is closed (or closable)
            - no self-intersections
            - first point is on the outline (not inside)
        Returns:
            (True, None) if valid
            (False, "reason") if invalid
        """

        # --- 1. Must have at least 3 points ---
        if len(points) < 3:
            return False, "Polygon must have at least 3 points"

        # --- 2. Points must be normalized ---
        for x, y in points:
            if not (0.0 <= x <= 1.0 and 0.0 <= y <= 1.0):
                return False, f"Point {(x,y)} is outside 0..1 range"

        # --- 3. Ensure polygon is closed ---
        if points[0] != points[-1]:
            # auto-close is fine, but warn
            pass

        # --- 4. Check for self-intersections ---
        def segments_intersect(a, b, c, d):
            # Basic 2D segment intersection test
            def ccw(p, q, r):
                return (r[1]-p[1]) * (q[0]-p[0]) > (q[1]-p[1]) * (r[0]-p[0])
            return (ccw(a, c, d) != ccw(b, c, d)) and (ccw(a, b, c) != ccw(a, b, d))

        n = len(points)
        for i in range(n - 1):
            a1, a2 = points[i], points[i+1]
            for j in range(i + 2, n - 1):
                b1, b2 = points[j], points[j+1]
                # Skip adjacent edges (they share a vertex)
                if a1 in (b1, b2) or a2 in (b1, b2):
                    continue
                if segments_intersect(a1, a2, b1, b2):
                    return False, "Polygon has self-intersections"

        # --- 5. First point should be on the outline ---
        # (simple heuristic: first point must be an extreme)
        x0, y0 = points[0]
        if not (x0 in (0,1) or y0 in (0,1)):
            return False, "First point should be on the outline, not inside"

        return True, None
