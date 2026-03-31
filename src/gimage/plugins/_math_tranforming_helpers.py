import numpy as np
from shapely.geometry import LineString, MultiLineString, Polygon

def rotate_polygon(poly, angle_deg):
    pts = np.array(poly, dtype=float)
    a = np.radians(angle_deg)
    R = np.array([[np.cos(a), -np.sin(a)],
                  [np.sin(a),  np.cos(a)]])
    return (pts @ R.T).tolist()

def rotate_segments(segments, angle_deg):
    return [rotate_polygon(seg, angle_deg) for seg in segments]

def bbox(poly):
    pts = np.array(poly)
    minx = pts[:,0].min()
    maxx = pts[:,0].max()
    miny = pts[:,1].min()
    maxy = pts[:,1].max()
    return minx, maxx, miny, maxy

def polygon_area(pts):
    area = 0
    for i in range(len(pts)):
        x1, y1 = pts[i]
        x2, y2 = pts[(i+1) % len(pts)]
        area += x1*y2 - x2*y1
    return abs(area) / 2

def polygon_centroid(pts):
    # pts must be a list of (x,y)
    if len(pts) < 3:
        # fallback: average of available points
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        return (sum(xs)/len(xs), sum(ys)/len(ys))

    arr = np.array(pts, dtype=float)

    # Standard polygon centroid formula
    x = arr[:,0]
    y = arr[:,1]

    a = np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1))
    A = a.sum() / 2.0

    if abs(A) < 1e-9:
        # degenerate polygon → fallback to average
        return (x.mean(), y.mean())

    cx = ( (x + np.roll(x, -1)) * a ).sum() / (6*A)
    cy = ( (y + np.roll(y, -1)) * a ).sum() / (6*A)

    return (cx, cy)


def polygon_intersections(poly, y):
    pts = np.array(poly)
    x1 = pts[:,0]
    y1 = pts[:,1]
    x2 = np.roll(x1, -1)
    y2 = np.roll(y1, -1)

    # Check if scanline intersects segment
    cond = ((y1 <= y) & (y < y2)) | ((y2 <= y) & (y < y1))

    # Avoid division by zero
    dy = (y2 - y1)
    dy[dy == 0] = 1e-12

    t = (y - y1) / dy
    xs = x1 + t * (x2 - x1)

    return xs[cond].tolist()


def clip_polyline_to_polygon(polyline, polygon):
    line = LineString(polyline)
    poly = Polygon(polygon)

    clipped = line.intersection(poly)

    if clipped.is_empty:
        return []

    # Single LineString
    if isinstance(clipped, LineString):
        return [list(clipped.coords)]

    # MultiLineString
    if isinstance(clipped, MultiLineString):
        return [list(ls.coords) for ls in clipped.geoms]

    # GeometryCollection
    if hasattr(clipped, "geoms"):
        out = []
        for geom in clipped.geoms:
            if isinstance(geom, LineString):
                out.append(list(geom.coords))
        return out

    return []


def decimate(poly, step=3):
    return poly[::step]

def generate_spiral(cx, cy, spacing, max_radius=None, turns=2000):
    """
    Generate an Archimedean spiral centered at (cx, cy).
    spacing = distance between spiral arms
    max_radius = optional limit (otherwise auto)
    turns = number of parametric steps (higher = smoother)
    """

    # Spiral equation: r = k * theta
    # spacing between arms = 2πk  →  k = spacing / (2π)
    k = spacing / (2 * np.pi)

    # theta range
    theta = np.linspace(0, turns * np.pi, turns)

    # radius
    r = k * theta

    # optional radius limit
    if max_radius is not None:
        r = r[r <= max_radius]
        theta = theta[:len(r)]

    # convert to cartesian
    x = cx + r * np.cos(theta)
    y = cy + r * np.sin(theta)

    # return as list of (x,y)
    return list(zip(x, y))
