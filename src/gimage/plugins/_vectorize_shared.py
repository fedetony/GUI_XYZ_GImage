# fill_shared.py
# Shared geometry + fill utilities for vectorization plugins.

import math
import pyclipper
from skimage import measure
from ._math_tranforming_helpers import *


# ------------------------------------------------------------
# Pixel utilities
# ------------------------------------------------------------

def safe_pixel_from_color(color):
    """Return grayscale brightness from RGBA color."""
    try:
        r, g, b = color[:3]
        return (int(r) + int(g) + int(b)) / 3.0
    except Exception:
        return 128.0


def pixel_to_power(pixel, min_p, max_p, mode, invert=False):
    """Map pixel brightness to laser power."""
    if mode == "threshold":
        if invert:
            return max_p if pixel > 128 else 0
        return max_p if pixel < 128 else 0

    brightness = pixel / 255.0

    # invert brightness if needed
    if invert:
        brightness = 1.0 - brightness

    inv = 1.0 - brightness
    return int(min_p + inv * (max_p - min_p))


def pixel_to_feedrate(pixel, actual_rate, min_rate, max_rate, mode, invert=False):
    """Map pixel brightness to feedrate."""
    if mode == "threshold":
        return actual_rate

    brightness = pixel / 255.0

    # invert brightness if needed
    if invert:
        brightness = 1.0 - brightness

    inv = 1.0 - brightness
    return int(min_rate + inv * (max_rate - min_rate))



# ------------------------------------------------------------
# Subshape helpers
# ------------------------------------------------------------

def subshape_to_points(sub):
    """Convert subshape segments into a list of points."""
    return [sub[0][0]] + [e[1] for e in sub]


def points_to_subshape(pts):
    """Convert list of points into subshape segments."""
    return [(pts[i], pts[i+1]) for i in range(len(pts)-1)]


# ------------------------------------------------------------
# Geometry helpers
# ------------------------------------------------------------

def polygon_area(pts):
    """Compute signed polygon area."""
    area = 0.0
    for i in range(len(pts)):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % len(pts)]
        area += x1 * y2 - x2 * y1
    return area / 2.0


def polygon_centroid(pts):
    """Compute polygon centroid."""
    A = polygon_area(pts)
    if abs(A) < 1e-9:
        return pts[0]
    cx = 0.0
    cy = 0.0
    for i in range(len(pts)):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % len(pts)]
        cross = x1 * y2 - x2 * y1
        cx += (x1 + x2) * cross
        cy += (y1 + y2) * cross
    return (cx / (6 * A), cy / (6 * A))


def rotate_polygon(pts, angle_deg):
    """Rotate polygon around origin."""
    ang = math.radians(angle_deg)
    ca, sa = math.cos(ang), math.sin(ang)
    return [(x * ca - y * sa, x * sa + y * ca) for x, y in pts]


def rotate_segments(segments, angle_deg):
    """Rotate list of segments."""
    ang = math.radians(angle_deg)
    ca, sa = math.cos(ang), math.sin(ang)
    out = []
    for seg in segments:
        (x1, y1), (x2, y2) = seg
        p1 = (x1 * ca - y1 * sa, x1 * sa + y1 * ca)
        p2 = (x2 * ca - y2 * sa, x2 * sa + y2 * ca)
        out.append([p1, p2])
    return out


def bbox(pts):
    """Return bounding box of points."""
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return min(xs), max(xs), min(ys), max(ys)


# ------------------------------------------------------------
# Fill generators
# ------------------------------------------------------------

def generate_none_fill(shape, spacing):
    """Ensure polygons are closed."""
    closed = []
    for sub in shape:
        if not sub:
            continue
        start = sub[0][0]
        end   = sub[-1][1]
        if start != end:
            sub = sub + [((end[0], end[1]), (start[0], start[1]))]
        closed.append(sub)
    return closed


def classify_subshapes(shape):
    """Split shape into outer rings and holes."""
    outers = []
    holes = []
    for sub in shape:
        pts = subshape_to_points(sub)
        area = polygon_area(pts)
        if area >= 0:
            outers.append(sub)
        else:
            holes.append(sub)
    return outers, holes

def normalize_winding(shape):
    """normalizes the direction of the shape/polygon"""
    normalized = []
    for sub in shape:
        pts = subshape_to_points(sub)
        area = polygon_area(pts)

        # Outer boundary should be CW (area < 0)
        if area > 0:
            sub = reverse_subshape(sub)

        normalized.append(sub)

    return normalized

def reverse_subshape(sub):
    """Reverses direction of subshape"""
    return [(b, a) for (a, b) in reversed(sub)]

def generate_hatch_fill(shape, spacing, angle_deg):
    """Fills shapes using parallel lines at a fixed angle."""

    outers, holes = classify_subshapes(shape)
    new_shape = []

    # sweep direction vector
    ang = math.radians(angle_deg)
    dx = math.cos(ang)
    dy = math.sin(ang)

    # perpendicular (sweep) vector
    nx = -dy
    ny = dx

    for outer in outers:
        pts = subshape_to_points(outer)

        # rotate polygon
        rot = rotate_polygon(pts, angle_deg)
        minx, maxx, miny, maxy = bbox(rot)

        segments = []
        y = miny
        while y <= maxy:
            xs = polygon_intersections(rot, y)
            xs.sort()
            for i in range(0, len(xs), 2):
                segments.append([(xs[i], y), (xs[i+1], y)])
            y += spacing

        # rotate back
        segments = rotate_segments(segments, -angle_deg)

        # subtract holes
        if holes:
            segments = subtract_holes_from_segments(segments, holes)

        # sort segments by sweep direction
        def sweep_key(seg):
            (x1, y1), (x2, y2) = seg
            mx = (x1 + x2) * 0.5
            my = (y1 + y2) * 0.5
            return mx * nx + my * ny

        segments.sort(key=sweep_key)

        # serpentine merge
        merged = merge_serpentine(segments)
        new_shape.append(points_to_subshape(merged))

    return new_shape


def generate_crosshatch_fill(shape, spacing, angle_deg):
    """Generate crosshatch fill."""
    s1 = generate_hatch_fill(shape, spacing, angle_deg)
    s2 = generate_hatch_fill(shape, spacing, angle_deg + 90)
    return s1 + s2


def generate_concentric_fill(shape, spacing):
    """Generate concentric rings."""
    outers, _ = classify_subshapes(shape)
    rings = generate_offset_fill(shape, spacing)
    return outers + rings


# def generate_offset_fill(shape, spacing):
#     """Generate inward offset rings."""
#     scale = 1000
#     spacing = spacing

#     outers, holes = classify_subshapes(shape)

#     def scale_path(sub):
#         pts = subshape_to_points(sub)
#         return [(int(x * scale), int(y * scale)) for x, y in pts]

#     outer_paths = [scale_path(o) for o in outers]
#     hole_paths  = [scale_path(h) for h in holes]

#     outer_paths = [pyclipper.CleanPolygon(p, spacing * scale) for p in outer_paths]
#     hole_paths  = [pyclipper.CleanPolygon(p, spacing * scale) for p in hole_paths]

#     outer_paths = [p for p in outer_paths if len(p) >= 3]
#     hole_paths  = [p for p in hole_paths if len(p) >= 3]

#     if not outer_paths:
#         return []

#     pc = pyclipper.Pyclipper()
#     pc.AddPaths(outer_paths, pyclipper.PT_SUBJECT, True)
#     pc.AddPaths(hole_paths,  pyclipper.PT_SUBJECT, True)

#     result = []
#     current = outer_paths + hole_paths
#     max_layers = 2000 // max(1, int(spacing * scale))
#     layers = 0

#     while current and layers < max_layers:
#         off = pyclipper.PyclipperOffset()
#         off.AddPaths(current, pyclipper.JT_ROUND, pyclipper.ET_CLOSEDPOLYGON)
#         res = off.Execute(-spacing * scale)

#         if not res:
#             break

#         for r in res:
#             pts = [(x/scale, y/scale) for x, y in r]
#             pts = pts[::3]
#             if len(pts) > 3:
#                 result.append(points_to_subshape(pts))

#         current = res
#         layers += 1

#     return result

def generate_offset_fill(shape, spacing):
    """Generate inward offset rings."""
    scale = 1000

    outers, holes = classify_subshapes(shape)

    def scale_path(sub):
        pts = subshape_to_points(sub)
        return [(int(x * scale), int(y * scale)) for x, y in pts]

    outer_paths = [scale_path(o) for o in outers]

    outer_paths = [pyclipper.CleanPolygon(p, spacing * scale) for p in outer_paths]
    outer_paths = [p for p in outer_paths if len(p) >= 3]

    if not outer_paths:
        return []

    result = []
    current = outer_paths
    max_layers = 2000 // max(1, int(spacing * scale))
    layers = 0

    while current and layers < max_layers:
        off = pyclipper.PyclipperOffset()
        off.AddPaths(current, pyclipper.JT_ROUND, pyclipper.ET_CLOSEDPOLYGON)
        res = off.Execute(-spacing * scale)

        if not res:
            break

        new_current = []
        for r in res:
            pts = [(x/scale, y/scale) for x, y in r]
            pts = pts[::3]
            if len(pts) > 3:
                result.append(points_to_subshape(pts))
                new_current.append(r)

        current = new_current
        layers += 1

    return result


def generate_contour_hatched_fill(shape, spacing, angle_deg, is_crosshatch):
    """Generate contour + hatch or crosshatch fill."""
    outers, _ = classify_subshapes(shape)
    hatched = list(outers)

    if not is_crosshatch:
        fills = generate_hatch_fill(shape, spacing, angle_deg)
    else:
        fills = generate_crosshatch_fill(shape, spacing, angle_deg)

    hatched.extend(fills)
    return hatched


def generate_spiral_fill(shape, spacing):
    """Generate clipped spiral fill."""
    scale = 1000
    outers, holes = classify_subshapes(shape)
    final = []

    for outer in outers:
        pts = subshape_to_points(outer)
        pts = list(dict.fromkeys(pts))
        if len(pts) < 3:
            continue

        scaled = [(int(x*scale), int(y*scale)) for x, y in pts]
        cleaned = pyclipper.CleanPolygon(scaled, spacing * scale)
        if not cleaned or len(cleaned) < 3:
            continue

        flat = [(x/scale, y/scale) for x, y in cleaned]
        cx, cy = polygon_centroid(flat)

        minx, maxx, miny, maxy = bbox(flat)
        max_radius = max(maxx - minx, maxy - miny) * 1.5

        spiral = generate_spiral(cx, cy, spacing, max_radius)

        clipped = []
        for i in range(len(spiral)-1):
            seg = [spiral[i], spiral[i+1]]
            clipped_seg = clip_polyline_to_polygon(seg, flat)
            if clipped_seg:
                clipped.extend(clipped_seg)

        if holes:
            clipped = subtract_holes_from_segments(clipped, holes)

        for seg in clipped:
            if len(seg) > 3:
                final.append(seg[::3])

    return final

# ------------------------------------------------------------
# Smoothing
# ------------------------------------------------------------

def chaikin(pts, passes=1):
    pts = np.array(pts)
    for _ in range(passes):
        new = []
        for i in range(len(pts)-1):
            p = pts[i]
            q = pts[i+1]
            new.append(0.75*p + 0.25*q)
            new.append(0.25*p + 0.75*q)
        pts = np.array(new)
    return pts

# ------------------------------------------------------------
# Sorting
# ------------------------------------------------------------

def sort_contours_by_proximity(contours):
        """Sort contours to minimize travel distance (nearest-neighbor)."""

        if not contours:
            return contours

        # Convert to list of numpy arrays
        contours = [np.array(c) for c in contours]

        # Start with the first contour
        ordered = [contours.pop(0)]

        while contours:
            last = ordered[-1]
            last_end = last[-1]  # last point of previous contour

            # Find nearest contour (start or end)
            best_i = None
            best_dist = float("inf")
            best_reverse = False

            for i, c in enumerate(contours):
                d_start = np.linalg.norm(c[0] - last_end)
                d_end   = np.linalg.norm(c[-1] - last_end)

                if d_start < best_dist:
                    best_dist = d_start
                    best_i = i
                    best_reverse = False

                if d_end < best_dist:
                    best_dist = d_end
                    best_i = i
                    best_reverse = True

            # Take the best contour
            next_c = contours.pop(best_i)

            # Reverse if needed
            if best_reverse:
                next_c = next_c[::-1]

            ordered.append(next_c)

        return ordered


# ------------------------------------------------------------
# Serpentine + clipping helpers
# ------------------------------------------------------------

def merge_serpentine(segments):
    """Merge segments into serpentine polyline."""
    if not segments:
        return []
    segments.sort(key=lambda s: (s[0][1] + s[-1][1]) / 2)
    for i in range(len(segments)):
        if i % 2 == 1:
            segments[i].reverse()
    merged = []
    for seg in segments:
        merged.extend(seg)
    return merged

def merge_fragments_serpentine(fragments):
    """Remove empty or tiny fragments"""
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


def subtract_holes_from_segments(segments, holes):
    """Clip hatch lines against holes."""
    result = []
    for seg in segments:
        clipped = [seg]
        for hole in holes:
            clipped2 = []
            for c in clipped:
                clipped2.extend(clip_polyline_to_polygon(c, subshape_to_points(hole), invert=True))
            clipped = clipped2
        result.extend(clipped)
    return result
    
def flatten_shape_to_polygon(shape):
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

def subshape_to_points(sub_shape):
    """ [ ((x0,y0),(x1,y1)), ((x1,y1),(x2,y2)), ... ]
    return pts = [(x0,y0), (x1,y1), (x2,y2), ...] """   
    return [sub_shape[0][0]] + [e[1] for e in sub_shape]

def points_to_subshape(pts):
    """ pts = [(x0,y0), (x1,y1), (x2,y2), ...]
    return [ ((x0,y0),(x1,y1)), ((x1,y1),(x2,y2)), ... ]"""
    return [ (pts[i], pts[i+1]) for i in range(len(pts)-1) ]

def classify_subshapes(shape):
    """Classify in outer or inner the shapes"""
    outers = []
    holes = []
    for sub in shape:
        pts = subshape_to_points(sub)
        area = polygon_area(pts)

        # If your coordinate system is image-like (y down), flip the logic:
        if area >= 0:
            outers.append(sub)   # outer
        else:
            holes.append(sub)    # hole

    return outers, holes
# ------------------------------------------------------------
# Spiral generator
# ------------------------------------------------------------

def generate_spiral(cx, cy, spacing, max_radius):
    """Generate simple outward spiral."""
    pts = []
    t = 0.0
    r = 0.0
    while r < max_radius:
        x = cx + r * math.cos(t)
        y = cy + r * math.sin(t)
        pts.append((x, y))
        t += 0.3
        r += spacing * 0.05
    return pts

