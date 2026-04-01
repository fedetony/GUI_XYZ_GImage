'''
Code originally from Javier Rodriguez Second function
https://github.com/IngJavierR/PngToSvg.git
Latest commit a46b860 on May 7 
'''
from PIL import Image
import operator
from collections import deque
from io import StringIO
import threading
import numpy as np
from collections import defaultdict
import os
import cv2 # opencv pip install opencv-python-headless or pip install opencv-python with imshow
import copy
import pyclipper
from gimage.plugins._math_tranforming_helpers import *

#from Scipy.ndimage import label
EPSILON = 0 #0.05 # RDP resolution 
DIRS = np.array([
        [0, 1],
        [1, 0],
        [0, -1],
        [-1, 0]
    ])
#import numba  # for GPU compile and usage
 
class Vectorization(threading.Thread):
    """
        A thread class Get vector data out of pillow and images in rgba form
    """
    def __init__(self, The_Image, kill_event,plaintextEdit_GcodeScript=None,Pbar=None):
        threading.Thread.__init__(self, name="Vectorize thread")        
        self.killer_event = kill_event
        self.im=The_Image
        self.improcess_percentage=0
        self.printprocess=False
        self.plaintextEdit_GcodeScript=plaintextEdit_GcodeScript
        self.Pbarupdate=Pbar
        self.Pbar_Set_Status(0)
        self.Pbarini=0
        self.Pbarend=100
        self.last_color_joined_pieces=None # store result in class

    def Pbar_Set_Status(self,val):
        if  self.Pbarupdate is not None and int(val)>=0 and int(val)<=100:      
            self.Pbarupdate.SetStatus(int(val))    

    def Get_Im_Process_state(self):
        return self.improcess_percentage

    def sub_vec(self, a, b):
        return np.asarray(a) - np.asarray(b)

    def neg_vec(self, a):
        return -np.asarray(a)

    def direction(self, edge):
        e = np.asarray(edge)
        return e[1] - e[0]

    def magnitude(self, a):
        a = np.asarray(a)
        return np.linalg.norm(a)

    def normalize(self, a):
        a = np.asarray(a)
        mag = np.linalg.norm(a)
        if mag == 0:
            raise ValueError("Cannot normalize zero-length vector")
        return a / mag

    def sub_tuple(self,a, b):
        return tuple(map(operator.sub, a, b))



    def svg_header(self,width, height):
        return """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
        <!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" 
        "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
        <svg width="%d" height="%d"
            xmlns="http://www.w3.org/2000/svg" version="1.1">
        """ % (width, height)    
    
    def sort_shapes_by_shortest_path(self, shapes):
        """
        Sort vector shapes so that the machine travels the shortest distance
        between consecutive paths (nearest-neighbor ordering).

        Parameters
        ----------
        shapes : list
            List of shapes, where each shape is a list of edges:
                [ ((x0,y0),(x1,y1)), ((x1,y1),(x2,y2)), ... ]

        Returns
        -------
        list
            Shapes reordered so that each shape begins near where the previous ended.
        """
        # Remove empty shapes
        shapes = [s for s in shapes if len(s) > 0 and len(s[0]) > 0]
        if not shapes:
            return shapes

        # Extract start/end points safely
        def get_start(shape):
            try:
                return shape[0][0][0]
            except:
                return None

        def get_end(shape):
            try:
                return shape[-1][-1][1]
            except:
                return None

        # Build info list
        shape_info = []
        for shape in shapes:
            start = get_start(shape)
            end = get_end(shape)
            if start is None or end is None:
                continue
            shape_info.append({"shape": shape, "start": start, "end": end})

        if not shape_info:
            return []

        # Start with the first shape
        ordered = [shape_info.pop(0)]

        # Greedy nearest-neighbor
        while shape_info:
            last_end = ordered[-1]["end"]

            best_idx = None
            best_dist = float("inf")

            for i, info in enumerate(shape_info):
                sx, sy = info["start"]
                lx, ly = last_end
                d2 = (sx - lx)**2 + (sy - ly)**2
                if d2 < best_dist:
                    best_dist = d2
                    best_idx = i

            ordered.append(shape_info.pop(best_idx))

        return [info["shape"] for info in ordered]

    def _merge_collinear_edges(self, edges):
        """Merge consecutive collinear edges into a single edge."""
        if len(edges) <= 1:
            return edges

        merged = [edges[0]]

        for e in edges[1:]:
            (x0, y0), (x1, y1) = merged[-1]
            (x2, y2) = e[1]

            dx1, dy1 = x1 - x0, y1 - y0
            dx2, dy2 = x2 - x1, y2 - y1

            # Check collinearity via cross product
            if dx1 * dy2 == dy1 * dx2:
                merged[-1] = ((x0, y0), (x2, y2))
            else:
                merged.append(e)
        return merged



    def joined_edges(self, assorted_edges, keep_every_point=False):
        """
        Join unordered boundary edges into continuous polylines or loops.

        Parameters
        ----------
        assorted_edges : iterable
            A collection of edges, where each edge is:
                ((x0, y0), (x1, y1))
        keep_every_point : bool
            If False, collinear edges are merged into longer segments.

        Returns
        -------
        list
            A list of joined shapes. Each shape is a list of edges:
                [ ((x0,y0),(x1,y1)), ((x1,y1),(x2,y2)), ... ]
        """
        # Convert to a list so we can iterate multiple times
        edges = list(assorted_edges)
        # Build adjacency: start_point → list of edges starting here
        from collections import defaultdict
        start_map = defaultdict(list)
        for e in edges:
            start_map[e[0]].append(e)
        # Track which edges are used
        used = set()
        shapes = []
        for e in edges:
            if e in used:
                continue
            # Start a new polyline
            poly = [e]
            used.add(e)
            current_end = e[1]
            # Follow forward
            while True:
                next_edges = start_map.get(current_end)
                if not next_edges:
                    break
                # Find the first unused edge starting here
                nxt = None
                for cand in next_edges:
                    if cand not in used:
                        nxt = cand
                        break
                if nxt is None:
                    break

                poly.append(nxt)
                used.add(nxt)
                current_end = nxt[1]

                # Stop if we loop back to the start
                if current_end == poly[0][0]:
                    break
            # Optional simplification: merge collinear edges
            if not keep_every_point:
                poly = self._merge_collinear_edges(poly)
            shapes.append(poly)
        return shapes


    def rgba_image_to_svg_contiguous(self, an_image, opaque=None, keep_every_point=False,epsilon=None):
        """
        Full vectorization pipeline: convert an RGBA image into a contiguous SVG.

        This function orchestrates the entire image‑to‑vector conversion process.
        It performs four major stages:

        1. **Connected‑component extraction**
        Uses `collect_contiguous_pixel_groups` to group pixels of identical
        RGBA color into contiguous regions (4‑connected). Each region becomes
        a “piece” of the final vector output.

        2. **Boundary extraction**
        Uses `calculate_clockwise_edges_of_pixel_groups` to compute the
        clockwise boundary edges for each pixel group. Each pixel contributes
        0–4 edges depending on which of its sides lie on the boundary.

        3. **Edge joining**
        Uses `join_edges_of_pixel_groups` to merge unordered boundary edges
        into continuous polylines or closed loops. These joined paths represent
        the final vector outlines of each region.

        4. **SVG generation**
        Uses `write_color_joined_pieces_to_svg_contiguous` to convert the
        joined vector paths into SVG `<path>` elements, filled with the
        corresponding RGBA color.

        Progress bar ranges (`Pbarini`, `Pbarend`) are updated for each stage so
        the UI can reflect progress through the pipeline.

        Parameters
        ----------
        an_image : PIL.Image
            The input image in RGBA mode.
        opaque : bool, optional
            If True, fully transparent pixels (alpha == 0) are ignored during
            connected‑component extraction. If False or None, all pixels are used.
        keep_every_point : bool, optional
            Passed through to the edge‑joining stage. If True, prevents merging of
            collinear edges and preserves all intermediate points. If False,
            straight segments may be simplified.

        Returns
        -------
        str
            A complete SVG document as a string, containing filled vector shapes
            corresponding to all contiguous color regions in the input image.

        Notes
        -----
        - This is the main entry point for raster‑to‑vector conversion.
        - The output SVG contains one `<path>` per region, filled with the region's
        original RGBA color.
        - If `killer_event` is set at any stage, processing stops early and a
        partial SVG may be returned.
        - The function prints the number of processed color layers if
        `self.printprocess` is True.
        """
        # collect contiguous pixel groups
        self.Pbarini = 0
        self.Pbarend = 25
        color_pixel_lists = self.collect_contiguous_pixel_groups(an_image, opaque, keep_every_point)

        # calculate clockwise edges of pixel groups
        self.Pbarini = 25
        self.Pbarend = 50
        color_edge_lists = self.calculate_clockwise_edges_of_pixel_groups(
            color_pixel_lists, opaque, keep_every_point
        )

        # join edges of pixel groups
        self.Pbarini = 50
        self.Pbarend = 75
        color_joined_pieces = self.join_edges_of_pixel_groups(color_edge_lists, opaque, keep_every_point)
        if epsilon is not None:
            color_joined_pieces = self.simplify_color_joined_pieces_rdp(color_joined_pieces, epsilon)
       
        for color in color_joined_pieces:
            color_joined_pieces[color] = self.sort_shapes_by_shortest_path(color_joined_pieces[color])
        
        self.last_color_joined_pieces=color_joined_pieces
        
        # Write svg format
        self.Pbarini = 75
        self.Pbarend = 100
        svg = self.write_color_joined_pieces_to_svg_contiguous(an_image, color_joined_pieces)

        self.Pbarini = 0
        self.Pbarend = 100

        if self.printprocess:
            print('Amount of color layers processed:', len(color_joined_pieces))

        return svg
    
    def vectorizer_rgba_image_to_svg_contiguous(self, im, epsilon = 0, merge_strength=0, do_sort=True):
        """
        Full vectorization pipeline: convert an RGBA image into a contiguous SVG.

        This function orchestrates the entire image‑to‑vector conversion process.
        It performs 2 major stages:

        1. **Uses Opencv to vectorize**
            
        - STEP 1: Quantize image to reduce colors (16)
        - STEP 2: Build mask for a given color 
        - STEP 3: Extract contours using OpenCV 
        - STEP 4: Convert contours to shape/sub-shape/edge format 
        - STEP 5: RDP simplification.
        - STEP 6: Sort shapes by nearest neighbor 

        2. **Converts to svg**
        
        Progress bar ranges (`Pbarini`, `Pbarend`) are updated for each stage so
        the UI can reflect progress through the pipeline.

        Parameters
        ----------
        im : PIL.Image
            The input image in RGBA mode.
        epsilon : 
            RDP resolution value for excluding lost pixels connections [0,1] 

        Returns
        -------
        str
            A complete SVG document as a string, containing filled vector shapes
            corresponding to all contiguous color regions in the input image.

        Notes
        -----
        - This is the main entry point for raster‑to‑vector conversion.
        - The output SVG contains one `<path>` per region, filled with the region's
        original RGBA color.
        - If `killer_event` is set at any stage, processing stops early and a
        partial SVG may be returned.
        - The function prints the number of processed color layers if
        `self.printprocess` is True.
        """
        if epsilon is None:
            epsilon=EPSILON
        vect=Vectorizer(self.Set_Progress_Percentage,pini=0,pend=100)
        color_joined_pieces=vect.vectorize(im,16,epsilon,merge_strength,do_sort=do_sort)
        self.last_color_joined_pieces=color_joined_pieces
        svg = self.write_color_joined_pieces_to_svg_contiguous(im, color_joined_pieces)

        self.Pbarini = 0
        self.Pbarend = 100
        self.Set_Progress_Percentage(100,100,0,100)

        if self.printprocess:
            print('Amount of color layers processed:', len(color_joined_pieces))

        return svg
  
    def collect_contiguous_pixel_groups(self, im, opaque=None, keep_every_point=False):
        """
        Identify and group contiguous pixels of identical RGBA color.

        This function converts the input Pillow image into a NumPy array and groups
        pixels by their exact RGBA value. For each unique color, it performs
        connected-component labeling (4-connectivity) to extract contiguous pixel
        regions ("pieces"). Each piece is returned as a list of (x, y) pixel
        coordinates.

        Parameters
        ----------
        im : PIL.Image
            The input image in RGBA mode.
        opaque : bool, optional
            If True, fully transparent pixels (alpha == 0) are ignored entirely.
            If False or None, all pixels are considered.
        keep_every_point : bool, optional
            Currently unused in this stage, but kept for API compatibility.

        Returns
        -------
        dict
            A dictionary mapping RGBA tuples to a list of pixel groups.
            Example:
                {
                    (255, 0, 0, 255): [ [(x1,y1), (x2,y2), ...], [...], ... ],
                    (0, 255, 0, 255): [ [...], ... ],
                    ...
                }

        Notes
        -----
        - This implementation uses SciPy's `ndimage.label`, which is highly optimized
        and dramatically faster than manual BFS flood-fill in Python.
        - All operations are vectorized; no per-pixel Python loops are used.
        """
        img = np.array(im)  # shape (H, W, 4)
        H, W = img.shape[:2]

        # Mask for opaque pixels if needed
        if opaque:
            opaque_mask = img[:, :, 3] > 0
        else:
            opaque_mask = np.ones((H, W), dtype=bool)

        # Find unique colors
        flat = img.reshape(-1, 4)
        colors, inverse = np.unique(flat, axis=0, return_inverse=True)
        inverse = inverse.reshape(H, W)

        color_pixel_groups = {}

        # 4-neighborhood
        neighbors = np.array([[1,0], [-1,0], [0,1], [0,-1]])

        for idx, color in enumerate(colors):
            if opaque and color[3] == 0:
                continue

            # Mask for this color
            mask = (inverse == idx) & opaque_mask
            if not mask.any():
                continue

            visited = np.zeros_like(mask, dtype=bool)
            groups = []

            ys, xs = np.where(mask)
            pixel_set = set(zip(xs, ys))

            for x0, y0 in pixel_set:
                if visited[y0, x0]:
                    continue

                queue = deque([(x0, y0)])
                visited[y0, x0] = True
                group = [(x0, y0)]

                while queue:
                    x, y = queue.popleft()

                    for dx, dy in neighbors:
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < W and 0 <= ny < H:
                            if mask[ny, nx] and not visited[ny, nx]:
                                visited[ny, nx] = True
                                queue.append((nx, ny))
                                group.append((nx, ny))

                groups.append(group)

            color_pixel_groups[tuple(color)] = groups

        return color_pixel_groups

    def calculate_clockwise_edges_of_pixel_groups(self, color_pixel_lists, opaque=None, keep_every_point=False):
        """
        Compute clockwise boundary edges for each contiguous pixel group.

        For each pixel group (a list of (x, y) coordinates), this function builds a
        boolean mask and uses vectorized neighbor comparisons to determine which
        pixel sides lie on the boundary of the shape. Each boundary side is converted
        into an oriented edge defined by two corner points.

        The result is a set of edges for each pixel group, suitable for downstream
        vectorization steps such as polygon tracing or G-code generation.

        Parameters
        ----------
        color_pixel_lists : dict
            Output from `collect_contiguous_pixel_groups`. Maps RGBA tuples to lists
            of pixel groups, where each group is a list of (x, y) coordinates.
        opaque : bool, optional
            Included for API compatibility; not used here.
        keep_every_point : bool, optional
            Included for API compatibility; not used here.

        Returns
        -------
        dict
            A dictionary mapping each RGBA color to a list of edge sets.
            Each edge set corresponds to one pixel group and contains tuples:
                ((x_start, y_start), (x_end, y_end))

        Notes
        -----
        - Fully vectorized: no Python loops over pixels.
        - Boundary detection is done via mask shifting and boolean logic.
        - Produces edges in clockwise order based on the defined neighbor offsets.
        - This is a major performance improvement over the original per-pixel,
        per-neighbor Python implementation.
        """
        # Offsets for neighbor directions
        offsets = np.array([
            [-1, 0],   # left
            [0, 1],    # up
            [1, 0],    # right
            [0, -1],   # down
        ])

        # Edge corner offsets (start_offset, end_offset)
        edge_offsets = np.array([
            [[0, 0], [0, 1]],   # left
            [[0, 1], [1, 1]],   # up
            [[1, 1], [1, 0]],   # right
            [[1, 0], [0, 0]],   # down
        ])

        color_edge_lists = {}

        total_colors = len(color_pixel_lists)
        color_index = 0

        for rgba, pieces in color_pixel_lists.items():
            self.improcess_percentage = self.Set_Progress_Percentage(
                color_index, total_colors, self.Pbarini, self.Pbarend
            )
            if self.killer_event.is_set():
                break
            color_index += 1

            edge_sets_for_color = []

            for piece_pixel_list in pieces:
                # Convert pixel list to NumPy array
                coords = np.array(piece_pixel_list, dtype=int)
                if coords.size == 0:
                    edge_sets_for_color.append(set())
                    continue

                # Build a mask for this piece
                xs = coords[:, 0]
                ys = coords[:, 1]
                W = xs.max() + 2
                H = ys.max() + 2

                mask = np.zeros((H, W), dtype=bool)
                mask[ys, xs] = True

                # Vectorized neighbor detection
                boundary_edges = set()

                for i, (dx, dy) in enumerate(offsets):
                    # Shifted mask
                    shifted = np.zeros_like(mask)
                    shifted[max(0, dy):H+min(0, dy), max(0, dx):W+min(0, dx)] = \
                        mask[max(0, -dy):H-max(0, dy), max(0, -dx):W-max(0, dx)]

                    # Boundary pixels: mask == True AND shifted == False
                    boundary = mask & (~shifted)

                    ys_b, xs_b = np.where(boundary)

                    # Compute edges for all boundary pixels in this direction
                    start_offsets = edge_offsets[i, 0]
                    end_offsets   = edge_offsets[i, 1]

                    starts = np.stack([xs_b + start_offsets[0], ys_b + start_offsets[1]], axis=1)
                    ends   = np.stack([xs_b + end_offsets[0],   ys_b + end_offsets[1]],   axis=1)

                    # Add edges to set
                    for s, e in zip(starts, ends):
                        boundary_edges.add((tuple(s), tuple(e)))

                edge_sets_for_color.append(boundary_edges)

            color_edge_lists[rgba] = edge_sets_for_color

        return color_edge_lists

    #@numba.jit
    def join_edges_of_pixel_groups(self, color_edge_lists, opaque=None, keep_every_point=False):
        """
        Join boundary edges of each pixel group into continuous vector paths.

        This function takes the output of `calculate_clockwise_edges_of_pixel_groups`,
        where each pixel group is represented as a set of boundary edges. For each
        group, it calls `joined_edges` to merge individual edges into ordered,
        connected polylines (closed or open). These polylines represent the final
        vectorized outlines of each contiguous pixel region.

        Parameters
        ----------
        color_edge_lists : dict
            A dictionary mapping RGBA tuples to lists of edge sets.
            Example:
                {
                    (255,0,0,255): [ {edge1, edge2, ...}, {edgeA, edgeB, ...} ],
                    (0,255,0,255): [ {...}, ... ],
                    ...
                }
            Each edge is a tuple: ((x_start, y_start), (x_end, y_end)).

        opaque : bool, optional
            Included for API compatibility; not used here.

        keep_every_point : bool, optional
            Passed directly to `joined_edges`. If True, prevents merging
            collinear edges and keeps all intermediate points. If False, straight
            segments may be simplified.

        Returns
        -------
        dict
            A dictionary mapping each RGBA color to a list of joined edge paths.
            Example:
                {
                    (255,0,0,255): [
                        [ ((x1,y1),(x2,y2)), ((x2,y2),(x3,y3)), ... ],   # piece 1
                        [ ... ],                                         # piece 2
                    ],
                    ...
                }

        Notes
        -----
        - This function does not perform geometric analysis itself; it delegates
        the actual edge-joining logic to `joined_edges`.
        - Progress updates are performed per color.
        - If `killer_event` is set, processing stops early.
        """
        color_joined_pieces = {}
        lenlist = len(color_edge_lists.items())
        sss = 0

        for color, pieces in color_edge_lists.items():
            if self.killer_event.is_set():
                break

            self.improcess_percentage = self.Set_Progress_Percentage(
                sss, lenlist, self.Pbarini, self.Pbarend
            )
            sss += 1

            color_joined_pieces[color] = []
            for assorted_edges in pieces:
                color_joined_pieces[color].append(
                    self.joined_edges(assorted_edges, keep_every_point)
                )

        return color_joined_pieces

    def write_color_joined_pieces_to_svg_contiguous(self, im, color_joined_pieces):
        """
        Convert joined vector paths into an SVG document with filled contiguous shapes.

        This function takes the output of `join_edges_of_pixel_groups`, where each
        color maps to a list of joined edge paths (polylines or closed loops).
        It writes these shapes into an SVG `<path>` element using move (`M`) and
        line (`L`) commands, closing each sub-path with `Z`. Each color group is
        rendered as a filled shape with no stroke.

        Parameters
        ----------
        im : PIL.Image
            The original image. Only its size is used to set the SVG canvas
            dimensions.
        color_joined_pieces : dict
            A dictionary mapping RGBA tuples to lists of shapes. Each shape is a
            list of sub-shapes, and each sub-shape is a list of edges:
                [
                    [ ((x0,y0),(x1,y1)), ((x1,y1),(x2,y2)), ... ],   # sub-shape 1
                    [ ... ],                                         # sub-shape 2
                    ...
                ]
            This structure is produced by `join_edges_of_pixel_groups()`.

        Returns
        -------
        str
            A complete SVG document as a string, containing one `<path>` element
            per shape, filled with the corresponding RGBA color.

        Notes
        -----
        - Each sub-shape is assumed to be a closed loop or a polyline that can be
        closed with `Z`.
        
        - Shapes are filled using the RGB components of the color, with alpha
        converted to a 0–1 opacity value.
        - No stroke is drawn; shapes are filled only.
        - Progress updates occur per color.
        - If `killer_event` is set, the function stops early and returns a partial
        SVG.
        """
        s = StringIO()
        s.write(self.svg_header(*im.size))

        for color, shapes in color_joined_pieces.items():
            r, g, b, a = color

            # group per color
            #s.write(f'<g id="color_{r}_{g}_{b}" fill="rgb({r},{g},{b})" fill-opacity="{a/255:.3f}">\n')

            s.write(f'<g id="color_{r}_{g}_{b}" fill="rgb({r},{g},{b})" fill-opacity="{a/255:.3f}" stroke="none">\n')

            for shape in shapes:
                for sub_shape in shape:
                    if not sub_shape:
                        continue

                    # starting point
                    start = sub_shape[0][0]
                    s.write(f'<path d="M {start[0]:.3f},{start[1]:.3f} ')

                    # edges
                    for edge in sub_shape:
                        x, y = edge[1]
                        s.write(f'L {x:.3f},{y:.3f} ')

                    s.write('Z" />\n')

            s.write('</g>\n')

        s.write('</svg>')
        return s.getvalue()
 

    def Transform_pixel_coord_to_image_coord(self, im, x, y, Img_ini_pos, Robot_XYZ, Resolution=1):
        """
        Convert pixel coordinates from image space into robot/world-space coordinates.

        This function takes a pixel coordinate (x, y) from an image where (0, 0) is
        the top-left corner, applies a resolution scaling factor, flips the Y-axis
        to convert from image coordinates to Cartesian-style coordinates, and then
        offsets the result by the robot's image origin and robot XYZ position.

        The transformation steps are:
        1. Flip Y because image coordinates grow downward, but robot coordinates
        typically grow upward.
        2. Scale X and Y by the given resolution (e.g., pixels → millimeters).
        3. Add the image's initial position offset.
        4. Add the robot's XYZ offset (only X and Y are used here).

        Parameters
        ----------
        im : PIL.Image
            The image from which the pixel coordinates originate. Only `im.height`
            is used to flip the Y-axis.
        x : int or float
            Pixel X coordinate in image space.
        y : int or float
            Pixel Y coordinate in image space.
        Img_ini_pos : tuple or list of length 2
            The (x, y) offset of the image origin in robot/world coordinates.
        Robot_XYZ : tuple or list of length 3
            The robot's current (X, Y, Z) position. Only X and Y are applied.
        Resolution : float, optional
            Scaling factor converting pixel units into world units. Default is 1.

        Returns
        -------
        list
            A two-element list [X_world, Y_world] representing the transformed
            coordinate in robot/world space.

        Notes
        -----
        - This function assumes a simple linear transformation with no rotation.
        - The returned coordinates are suitable for downstream robot motion or
        G-code generation.
        """
        # (0,0) is the upper left corner
        # Flip Y (image → Cartesian)
        y = (im.height - 1) - y

        # Scale
        x = x * Resolution
        y = y * Resolution

        # Add offsets
        x += Img_ini_pos[0] + Robot_XYZ[0]
        y += Img_ini_pos[1] + Robot_XYZ[1]

        return [x, y]
           
    def Get_color_joined_pieces_from_rgba_image(self, im, opaque=None, keep_every_point=False,epsilon=None):
        """
        Run the full vectorization pipeline and return joined vector paths
        without generating SVG output.

        This function performs the first three stages of the raster‑to‑vector
        pipeline:

        1. **Connected‑component extraction**
        Uses `collect_contiguous_pixel_groups` to group pixels of identical
        RGBA color into contiguous 4‑connected regions.

        2. **Boundary extraction**
        Uses `calculate_clockwise_edges_of_pixel_groups` to compute the
        clockwise boundary edges for each pixel group.

        3. **Edge joining**
        Uses `join_edges_of_pixel_groups` to merge unordered boundary edges
        into continuous polylines or closed loops.

        Unlike `rgba_image_to_svg_contiguous`, this function does *not* convert
        the resulting vector paths into SVG. It simply returns the joined shapes
        for further processing (e.g., G‑code generation, shape sorting, analysis).

        Parameters
        ----------
        im : PIL.Image
            The input RGBA image.
        opaque : bool, optional
            If True, fully transparent pixels (alpha == 0) are ignored during
            connected‑component extraction. If False or None, all pixels are used.
        keep_every_point : bool, optional
            Passed to the edge‑joining stage. If True, prevents merging of
            collinear edges and preserves all intermediate points. If False,
            straight segments may be simplified.

        Returns
        -------
        dict
            A dictionary mapping RGBA tuples to lists of joined vector shapes.
            Structure:
                {
                    (r,g,b,a): [
                        [ [((x0,y0),(x1,y1)), ...],   # sub‑shape 1
                        [...],                       # sub‑shape 2
                        ],
                        ...
                    ],
                    ...
                }

        Notes
        -----
        - This function is ideal when the caller wants to generate G‑code,
        perform shape sorting, or apply additional geometric processing
        instead of producing SVG output.
        - Progress bar ranges (`Pbarini`, `Pbarend`) are updated for each stage.
        - If `killer_event` is set, processing stops early and returns partial data.
        """
        color_joined_pieces = {}

        # collect contiguous pixel groups
        self.Pbarini = 0
        self.Pbarend = 25
        color_pixel_lists = self.collect_contiguous_pixel_groups(im, opaque, keep_every_point)

        # calculate clockwise edges of pixel groups
        self.Pbarini = 25
        self.Pbarend = 75
        color_edge_lists = self.calculate_clockwise_edges_of_pixel_groups(
            color_pixel_lists, opaque, keep_every_point
        )

        # join edges of pixel groups
        self.Pbarini = 75
        self.Pbarend = 100
        
        color_joined_pieces = self.join_edges_of_pixel_groups(color_edge_lists, opaque, keep_every_point)
        if epsilon is not None:
            color_joined_pieces = self.simplify_color_joined_pieces_rdp(color_joined_pieces, epsilon)

        for color in color_joined_pieces:
            color_joined_pieces[color] = self.sort_shapes_by_shortest_path(color_joined_pieces[color])

        self.Pbarini = 0
        self.Pbarend = 100

        return color_joined_pieces
    
    def vectorizer_get_color_joined_pieces_from_rgba_image(self, im,epsilon=None,merge_strength=0,do_sort=True):
        """
        Run the full vectorization pipeline and return joined vector paths
        without generating SVG output.

        This function performs vectorization with opencv. And Sorts them by path proximity.

        It simply returns the joined shapes
        for further processing (e.g., G‑code generation, shape sorting, analysis).

        Parameters
        ----------
        im : PIL.Image
            The input RGBA image.
        epsilon : RDP resolution value for excluding lost pixels connections [0,1] 

        Returns
        -------
        dict
            A dictionary mapping RGBA tuples to lists of joined vector shapes.
            Structure:
                {
                    (r,g,b,a): [
                        [ [((x0,y0),(x1,y1)), ...],   # sub‑shape 1
                        [...],                       # sub‑shape 2
                        ],
                        ...
                    ],
                    ...
                }

        Notes
        -----
        - This function is ideal when the caller wants to generate G‑code,
        perform shape sorting, or apply additional geometric processing
        instead of producing SVG output.
        - Progress bar ranges (`Pbarini`, `Pbarend`) are updated for each stage.
        - If `killer_event` is set, processing stops early and returns partial data.
        """
        color_joined_pieces = {}

        # collect contiguous pixel groups
        self.Pbarini = 0
        self.Pbarend = 100
        if epsilon is None:
            epsilon=EPSILON
        vect=Vectorizer(self.Set_Progress_Percentage,self.Pbarini,self.Pbarend)
        color_joined_pieces=vect.vectorize(im,16,epsilon,merge_strength,do_sort=do_sort)
        self.last_color_joined_pieces=color_joined_pieces
      
        self.Set_Progress_Percentage(100,100,0,100)
        return color_joined_pieces

    def _circle_from_3_points(self, p1, p2, p3):
        """
        Given three non-collinear points, return (cx, cy, r).
        Returns None if points are collinear or nearly so.
        """
        (x1, y1) = p1
        (x2, y2) = p2
        (x3, y3) = p3

        temp = x2*x2 + y2*y2
        bc = (x1*x1 + y1*y1 - temp) / 2.0
        cd = (temp - x3*x3 - y3*y3) / 2.0
        det = (x1 - x2) * (y2 - y3) - (x2 - x3) * (y1 - y2)

        if abs(det) < 1e-8:
            return None  # nearly collinear

        # Center of circle
        cx = (bc*(y2 - y3) - cd*(y1 - y2)) / det
        cy = ((x1 - x2)*cd - (x2 - x3)*bc) / det

        r = ((x1 - cx)**2 + (y1 - cy)**2) ** 0.5
        return (cx, cy, r)

    def _clean_shapes(self, shapes):
        """Remove empty shapes or malformed sub-shapes."""
        cleaned = []
        for shape in shapes:
            # Remove empty sub-shapes
            subs = [sub for sub in shape if len(sub) > 0]
            if not subs:
                continue
            cleaned.append(subs)
        return cleaned

    def rgba_image_to_svg_pixels(self, im, opaque=None):
        """
        Convert every pixel of an RGBA image into individual 1×1 SVG rectangles.

        This function iterates over all pixels in the input image and writes each
        visible pixel as a `<rect>` element in an SVG document. Each rectangle is
        positioned at the corresponding (x, y) coordinate, has size 1×1, and is
        filled with the pixel's RGB color and alpha-derived opacity.

        This produces a literal pixel-by-pixel SVG representation of the image,
        useful for debugging, visualization, or exporting raster images into a
        vector container without geometric simplification.

        Parameters
        ----------
        im : PIL.Image
            The input image in RGBA mode.
        opaque : bool, optional
            If True, fully transparent pixels (alpha == 0) are skipped.
            If False or None, all pixels are included.

        Returns
        -------
        str
            A complete SVG document as a string, containing one `<rect>` element
            per pixel (except transparent ones if `opaque=True`).

        Notes
        -----
        - This function is intentionally non-vectorized and iterates pixel-by-pixel.
        It is simple but slow for large images.
        - The output SVG may be extremely large (one element per pixel).
        - The opacity is derived from the alpha channel as `alpha / 255`.
        - The SVG canvas size matches the input image dimensions.
        """
        s = StringIO()
        s.write(self.svg_header(*im.size))

        width, height = im.size
        for x in range(width):
            for y in range(height):
                rgba = im.getpixel((x, y))
                if opaque and not rgba[3]:
                    continue
                s.write(
                    """  <rect x="%d" y="%d" width="1" height="1" """
                    """style="fill:rgb%s; fill-opacity:%.3f; stroke:none;" />\n"""
                    % (x, y, rgba[0:3], float(rgba[3]) / 255)
                )

        s.write("""</svg>\n""")
        return s.getvalue()
       
    def Vectorized_color_joined_pieces_to_gcode_contiguous(
        self, im, color_joined_pieces, Gimageinfo,
        TouchONgcode, TouchOFFgcode, addon='\n'):
        """
        Convert joined vector paths into contiguous G‑code toolpaths.

        This function takes the output of `join_edges_of_pixel_groups`—a dictionary
        mapping RGBA colors to lists of joined edge paths—and converts each path
        into a sequence of G‑code commands suitable for plotting, engraving, or
        robotic drawing.

        For each color layer:
            • The tool is lifted (TouchOFFgcode)
            • A rapid move (G1) is issued to the first point of each sub‑shape
            • The tool is lowered (TouchONgcode)
            • All subsequent points of the sub‑shape are traced with G1 moves
            • The tool is lifted again at the end of the sub‑shape

        Pixel coordinates are transformed into robot/world coordinates using
        `Transform_pixel_coord_to_image_coord`, applying resolution scaling and
        robot offsets.

        Parameters
        ----------
        im : PIL.Image
            The original image. Only its height is used indirectly by the coordinate
            transformation function.
        color_joined_pieces : dict
            A dictionary mapping RGBA tuples to lists of shapes. Each shape is a
            list of sub‑shapes, and each sub‑shape is a list of edges:
                [
                    [ ((x0,y0),(x1,y1)), ((x1,y1),(x2,y2)), ... ],   # sub‑shape 1
                    [ ... ],                                         # sub‑shape 2
                    ...
                ]
            This structure is produced by `join_edges_of_pixel_groups()`.
        Gimageinfo : list or tuple
            A 4‑element structure: [Img_ini_pos, Robot_XYZ, Resolution, Feedrate]
            where:
                Img_ini_pos : (x, y) offset of the image origin in robot space
                Robot_XYZ   : (X, Y, Z) robot position (only X,Y used)
                Resolution  : pixel‑to‑world scaling factor
                Feedrate    : G‑code feedrate for motion commands
        TouchONgcode : str
            G‑code snippet that activates the tool (e.g., pen down, laser on).
        TouchOFFgcode : str
            G‑code snippet that deactivates the tool (e.g., pen up, laser off).
        addon : str, optional
            Line ending or additional formatting appended after each G‑code command.
            Defaults to a newline.

        Returns
        -------
        str
            A complete G‑code program as a string, containing all toolpaths for all
            color layers.

        """
        [Img_ini_pos, Robot_XYZ, Resolution, Feedrate] = Gimageinfo
        s = StringIO()

        lenlist = len(color_joined_pieces)
        sss = 0

        for color, shapes in color_joined_pieces.items():
            if self.killer_event.is_set():
                break

            self.improcess_percentage = self.Set_Progress_Percentage(
                sss, lenlist, self.Pbarini, self.Pbarend
            )
            sss += 1

            for shape in shapes:
                for sub_shape in shape:

                    if not sub_shape:
                        continue

                    # --- Build ordered point list from edges ---
                    pts = [sub_shape[0][0]] + [e[1] for e in sub_shape]

                    # --- Move to first point with tool OFF ---
                    s.write(TouchOFFgcode)
                    x, y = pts[0]
                    x, y = self.Transform_pixel_coord_to_image_coord(
                        im, x, y, Img_ini_pos, Robot_XYZ, Resolution
                    )
                    s.write(f"G0 X{x:.3f} Y{y:.3f} F{Feedrate:.3f}{addon}")

                    # --- Tool ON ---
                    s.write(TouchONgcode)

                    # --- Trace remaining points ---
                    for (x, y) in pts[1:]:
                        x, y = self.Transform_pixel_coord_to_image_coord(
                            im, x, y, Img_ini_pos, Robot_XYZ, Resolution
                        )
                        s.write(f"G1 X{x:.3f} Y{y:.3f} F{Feedrate:.3f}{addon}")

                    # --- Tool OFF at end ---
                    s.write(TouchOFFgcode)

        return s.getvalue()    
    
    def Vectorized_color_joined_pieces_to_gcode_contiguous_file(
        self, im, color_joined_pieces, Gimageinfo,
        TouchONgcode, TouchOFFgcode,
        output_path,
        addon="\n"
    ):
        """
        Convert joined vector paths into contiguous, streamed G‑code toolpaths.

        This function takes the output of the vectorizer—`color_joined_pieces`, a
        dictionary mapping RGBA colors to lists of vector shapes—and converts each
        shape into a continuous G‑code toolpath. The output is written incrementally
        to a file, allowing extremely large toolpaths (hundreds of thousands of
        lines) to be generated without storing the entire G‑code program in memory.

        Each color entry contains one or more shapes, and each shape contains one or
        more sub‑shapes. A sub‑shape is represented as a list of edges:

            [
                [ ((x0,y0),(x1,y1)), ((x1,y1),(x2,y2)), ... ],   # sub‑shape 1
                [ ... ],                                         # sub‑shape 2
                ...
            ]

        This function reconstructs each sub‑shape into an ordered point list:
            [p0, p1, p2, ...]
        where p0 = first edge start, and each subsequent point is the end of the
        corresponding edge. This produces a clean, continuous polyline suitable for
        plotting, engraving, or robotic drawing.

        For each sub‑shape:
            • The tool is lifted (TouchOFFgcode)
            • A rapid move (G0) is issued to the first point
            • The tool is lowered (TouchONgcode)
            • All remaining points are traced using G1 moves
            • The tool is lifted again at the end

        Pixel coordinates are transformed into robot/world coordinates using
        `Transform_pixel_coord_to_image_coord`, which:
            1. Flips the Y‑axis (image → Cartesian)
            2. Applies resolution scaling (pixels → world units)
            3. Applies image‑origin offsets
            4. Applies robot XY offsets

        Parameters
        ----------
        im : PIL.Image
            The original RGBA image. Only its height is used for Y‑axis flipping.
        color_joined_pieces : dict
            Mapping RGBA tuples → list of shapes → list of sub‑shapes → list of edges.
        Gimageinfo : list or tuple
            [Img_ini_pos, Robot_XYZ, Resolution, Feedrate]
                Img_ini_pos : (x, y) world‑space origin of the image
                Robot_XYZ   : (X, Y, Z) robot position (X,Y used)
                Resolution  : pixel‑to‑world scaling factor
                Feedrate    : default G‑code feedrate
        TouchONgcode : str
            G‑code snippet that activates the tool (pen down, laser on, etc.).
        TouchOFFgcode : str
            G‑code snippet that deactivates the tool (pen up, laser off, etc.).
        output_path : str
            Path to the output .gcode file. G‑code is streamed directly to this file.
        addon : str, optional
            Line ending or extra formatting appended after each G‑code command.

        Returns
        -------
        str
            The path to the generated G‑code file.

        Notes
        -----
        - This function streams G‑code directly to disk, making it suitable for very
        large vectorized images (hundreds of thousands of lines).
        - The function respects `killer_event` and stops early if cancellation is
        requested.
        - The vectorizer output preserves contour order; this function preserves that
        order unless additional sorting is applied upstream.
        """
        [Img_ini_pos, Robot_XYZ, Resolution, Feedrate] = Gimageinfo

        lenlist = len(color_joined_pieces)
        sss = 0

        with open(output_path, "w", encoding="utf-8") as f:

            for color, shapes in color_joined_pieces.items():

                if self.killer_event.is_set():
                    break

                self.improcess_percentage = self.Set_Progress_Percentage(
                    sss, lenlist, self.Pbarini, self.Pbarend
                )
                sss += 1

                for shape in shapes:
                    for sub_shape in shape:

                        if not sub_shape:
                            continue

                        # Build ordered point list
                        pts = [sub_shape[0][0]] + [e[1] for e in sub_shape]

                        # Move to first point with tool OFF
                        f.write(TouchOFFgcode)
                        x, y = pts[0]
                        x, y = self.Transform_pixel_coord_to_image_coord(
                            im, x, y, Img_ini_pos, Robot_XYZ, Resolution
                        )
                        f.write(f"G0 X{x:.3f} Y{y:.3f} F{Feedrate:.3f}{addon}")

                        # Tool ON
                        f.write(TouchONgcode)

                        # Trace remaining points
                        for (x, y) in pts[1:]:
                            x, y = self.Transform_pixel_coord_to_image_coord(
                                im, x, y, Img_ini_pos, Robot_XYZ, Resolution
                            )
                            f.write(f"G1 X{x:.3f} Y{y:.3f} F{Feedrate:.3f}{addon}")

                        # Tool OFF
                        f.write(TouchOFFgcode)

        return output_path


    
    def Sort_color_joined_pieces_by_color(self,color_joined_pieces):
        #Structure oreder is:
        #shapes=color_joined_pieces[color] # dictionary of colors
        #shape=shapes[0]
        #xylinesegments=shape[0]
        #one_xylinesegment=xylinesegments[0] #tuple of two (x,y) points making a line
        #xytuple=one_xylinesegment[0] #tuple of (x,y)

        print(len(color_joined_pieces))
        acol_list=self.get_list_of_colors(color_joined_pieces)
        
        #is already sorted by colors!!!!
        #print(len(acol_list))
        #print(acol_list)

        return color_joined_pieces

    def get_list_of_colors(self, color_joined_pieces):
        """
        Extract a unique list of RGBA colors from the joined‑pieces structure.

        Iterates through all color keys in `color_joined_pieces`, applies progress
        updates, and returns a list of unique RGBA tuples. Uses `is_color_in_list`
        to avoid duplicates.

        Parameters
        ----------
        color_joined_pieces : dict
            Mapping of RGBA tuples to lists of joined vector shapes.

        Returns
        -------
        list
            A list of unique RGBA color tuples.
        """
        col_list = []
        sss = 0
        lenlist = len(color_joined_pieces.items())

        for color, shapes in color_joined_pieces.items():
            if self.killer_event.is_set():
                break

            self.improcess_percentage = self.Set_Progress_Percentage(
                sss, lenlist, self.Pbarini, self.Pbarend
            )
            sss += 1

            if not self.is_color_in_list(color, col_list):
                col_list.append(color)

        return col_list

    def _rdp_simplify_points(self, points, epsilon):
        """
        Ramer–Douglas–Peucker simplification on a list of (x, y) points.
        epsilon is the max allowed deviation.
        """
        if len(points) < 3:
            return points

        # Line from first to last
        (x1, y1) = points[0]
        (x2, y2) = points[-1]

        # Find point with max distance from this line
        max_dist = -1.0
        index = -1

        dx = x2 - x1
        dy = y2 - y1
        denom = (dx*dx + dy*dy) or 1.0  # avoid division by zero

        for i in range(1, len(points) - 1):
            (x0, y0) = points[i]
            # perpendicular distance from point to line
            num = abs(dy * x0 - dx * y0 + x2*y1 - y2*x1)
            dist = num / (denom ** 0.5)
            if dist > max_dist:
                max_dist = dist
                index = i

        # If max distance is greater than epsilon, recursively simplify
        if max_dist > epsilon:
            left = self._rdp_simplify_points(points[:index+1], epsilon)
            right = self._rdp_simplify_points(points[index:], epsilon)
            return left[:-1] + right
        else:
            # Replace segment with straight line between endpoints
            return [points[0], points[-1]]

    def _edges_to_points(self, edges, closed=False):
        """
        Convert a list of edges [((x0,y0),(x1,y1)), ...] to a list of points.
        If closed is True, ensure last point loops back to first.
        """
        if not edges:
            return []

        pts = [edges[0][0]]
        for e in edges:
            pts.append(e[1])

        if closed and pts[0] != pts[-1]:
            pts.append(pts[0])

        return pts

    def _points_to_edges(self, points):
        """
        Convert a list of points [p0, p1, ...] to edges [(p0,p1), (p1,p2), ...].
        """
        edges = []
        for i in range(len(points) - 1):
            edges.append((points[i], points[i+1]))
        return edges

    def simplify_color_joined_pieces_rdp(self, color_joined_pieces, epsilon=1.0):
        """
        Apply RDP simplification to all sub-shapes in color_joined_pieces.
        epsilon is in pixel units.
        """
        new_cjp = {}

        for color, shapes in color_joined_pieces.items():
            new_shapes = []
            for shape in shapes:
                new_subs = []
                for sub_shape in shape:
                    # sub_shape: list of edges
                    pts = self._edges_to_points(sub_shape, closed=False)
                    simp_pts = self._rdp_simplify_points(pts, epsilon)
                    simp_edges = self._points_to_edges(simp_pts)
                    new_subs.append(simp_edges)
                new_shapes.append(new_subs)
            new_cjp[color] = new_shapes

        return new_cjp
        
    def is_color_in_list(self, acolor, alist):
        """
        Check whether a given RGBA color already exists in a list.

        Performs a linear search using `is_same_color` to compare colors.

        Parameters
        ----------
        acolor : tuple
            The RGBA color to search for.
        alist : list
            List of RGBA tuples.

        Returns
        -------
        bool
            True if the color is present, False otherwise.
        """
        for ccc in alist:
            if self.is_same_color(ccc, acolor):
                return True
        return False
            
    def is_same_color(self, color1, color2):
        """
        Compare two RGBA colors for exact equality.

        Parameters
        ----------
        color1 : tuple    First RGBA color.
        color2 : tuple    Second RGBA color.

        Returns
        -------
        bool
            True if all channels match, False otherwise.
        """
        lenc = len(color1)
        for iii in range(lenc):
            if color1[iii] != color2[iii]:
                return False
        return True

            
    def Sort_color_joined_pieces_to_radial(self, color_joined_pieces, xp=0, yp=0):
        """
        Sort shapes for each color by radial distance from a reference point.

        Parameters
        ----------
        color_joined_pieces : dict
            Mapping of RGBA colors to lists of shapes. Each shape is a list of
            sub-shapes, and each sub-shape is a list of edges:
                [ [ ((x0,y0),(x1,y1)), ... ], ... ]
        xp, yp : float
            Center point used for radial sorting.

        Returns
        -------
        dict
            Same structure as input, but shapes sorted by increasing radius.
        """

        new_color_joined_pieces = {}

        for color, shapes in color_joined_pieces.items():

            # Compute radius for each shape based on its first point
            shape_info = []
            for shape in shapes:
                # shape[0] = first sub-shape
                # shape[0][0] = first edge
                # shape[0][0][0] = first point (x, y)
                (x, y) = shape[0][0][0]
                r2 = (x - xp) * (x - xp) + (y - yp) * (y - yp)
                shape_info.append((r2, shape))

            # Sort by radius
            shape_info.sort(key=lambda t: t[0])

            # Extract sorted shapes
            new_color_joined_pieces[color] = [shape for (_, shape) in shape_info]

        return new_color_joined_pieces

    def Set_Progress_Percentage(self,sss,Numsss,Perini=0,Perend=100):
        if sss>Numsss:
            self.Pbar_Set_Status(Perend)
            return Perend
        if sss<0 or Numsss<=0:
            self.Pbar_Set_Status(Perini)
            return Perini
        if (Perend-Perini)<=0:
            Per=min(abs(Perini),abs(Perend))  
            self.Pbar_Set_Status(Per)
            return Per 
        Per=round(Perini+(sss/Numsss)*(Perend-Perini),2)
        if self.printprocess==True:
            print('Image Processed '+str(Per)+'%')
        self.Pbar_Set_Status(Per)
        return Per

    def Save_svg_text_file(self,svg_image,Filename):
        with open(Filename, "w") as text_file:
            text_file.write(svg_image)

    ############################ Contour tracing algorithms ##########################

    def _build_mask_from_pixels(self, im, pixels):
        """
        Build a binary mask (numpy array) from a list of (x,y) pixels.
        1 = foreground, 0 = background.
        """
        w, h = im.size
        mask = np.zeros((h, w), dtype=np.uint8)
        for (x, y) in pixels:
            if 0 <= x < w and 0 <= y < h:
                mask[y, x] = 1
        return mask
    
    def _moore_contours(self, mask):
        """
        Moore-Neighbor contour tracing.
        mask: 2D numpy array, 1=foreground, 0=background.
        Returns a list of contours; each contour is a list of (x,y) points.
        """
        h, w = mask.shape
        visited = np.zeros_like(mask, dtype=bool)
        contours = []

        # 8-neighborhood (clockwise)
        neighbors = [(-1,  0), (-1, -1), (0, -1), (1, -1),
                    (1,  0), (1,  1), (0,  1), (-1, 1)]

        for y in range(h):
            for x in range(w):
                if mask[y, x] == 1 and not visited[y, x]:
                    # Start contour
                    contour = []
                    start = (x, y)
                    current = (x, y)
                    # previous neighbor index (backtracking direction)
                    prev_dir = 0  # arbitrary

                    while True:
                        contour.append(current)
                        visited[current[1], current[0]] = True

                        found_next = False
                        # search neighbors starting from prev_dir
                        for i in range(8):
                            idx = (prev_dir + i) % 8
                            nx = current[0] + neighbors[idx][0]
                            ny = current[1] + neighbors[idx][1]

                            if 0 <= nx < w and 0 <= ny < h and mask[ny, nx] == 1:
                                # next contour point
                                current = (nx, ny)
                                # next search starts from (idx + 6) mod 8 (Moore rule)
                                prev_dir = (idx + 6) % 8
                                found_next = True
                                break

                        if not found_next:
                            break

                        if current == start:
                            # closed loop
                            break

                    if len(contour) > 1:
                        contours.append(contour)

        return contours

    def _contours_to_color_joined_pieces(self, contours):
        """
        Convert list of contours (each a list of (x,y) points) to your
        [shape][sub_shape][edges] format.
        """
        shapes = []
        for pts in contours:
            if len(pts) < 2:
                continue

            # Optional: use half-pixel offsets to make contours “between pixels”
            # For now we keep integer coords.
            edges = []
            for i in range(len(pts) - 1):
                p0 = pts[i]
                p1 = pts[i+1]
                edges.append((p0, p1))
            # close the loop
            if pts[0] != pts[-1]:
                edges.append((pts[-1], pts[0]))

            # one sub_shape per contour
            shape = [edges]
            shapes.append(shape)

        return shapes
    
    def Get_color_joined_pieces_from_rgba_image_contours(self, im, opaque=None):
        """
        New version: use contour tracing + contours → shapes, instead of
        pixel-edge boundary extraction and joining.
        """
        w, h = im.size
        pixels = np.array(im)  # shape (h, w, 4)

        color_joined_pieces = {}

        # Build color → list of pixels mapping (simple, can be optimized)
        color_pixel_lists = {}
        if self.printprocess:
            print("Starting contours...")
        for y in range(h):
            if self.printprocess:
                print(f"Processed...{y/h*50:.2f}%")
            for x in range(w):
                r, g, b, a = pixels[y, x]
                if opaque is True and a == 0:
                    continue
                color = (int(r), int(g), int(b), int(a))
                color_pixel_lists.setdefault(color, []).append((x, y))

        # For each color, build mask → contours → shapes
        size=len(color_pixel_lists)
        if self.printprocess:
            print(f"Dictionary of {size} formed...")
        
        for iii,(color, pix_list) in enumerate(color_pixel_lists.items()):
            if self.printprocess:
                print(f"Processing {iii+1} of {size}...{50+iii/size*50:.2f}%")
            if not pix_list:
                continue

            mask = self._build_mask_from_pixels(im, pix_list)
            contours = self._moore_contours(mask)
            shapes = self._contours_to_color_joined_pieces(contours)
            if shapes:
                color_joined_pieces[color] = shapes

        return color_joined_pieces

class Vectorizer:
    def __init__(self, progress_function=None,pini=None,pend=None):
        self.pini=pini
        self.pend=pend
        self.progress=progress_function
    
    def set_progress(self,val,total):
        if self.progress:
            try:
                _=self.progress(val,total,self.pini,self.pend)
            except:
                pass
        
    # --- STEP 1: Quantize image to reduce colors ---
    def quantize_image(self, im, colors=16):
        """
        Reduce image to a limited palette for faster vectorization.
        """
        return im.convert("RGBA").quantize(colors=colors, method=2).convert("RGBA")

    # --- STEP 2: Build mask for a given color ---
    def build_mask(self, pixels, color):
        """
        Create binary mask for a specific RGBA color.
        """
        mask = np.all(pixels == color, axis=2).astype(np.uint8)
        return mask

    # --- STEP 3: Extract contours using OpenCV ---
    def find_contours(self, mask):
        """
        Use OpenCV's fast contour tracing.
        """
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        return contours

    # --- STEP 4: Convert contours to your shape/sub-shape/edge format ---
    def contours_to_shapes(self, contours):
        shapes = []
        for contour in contours:
            pts = contour[:,0,:]  # Nx2 array
            edges = []
            for i in range(len(pts)-1):
                p0 = tuple(pts[i])
                p1 = tuple(pts[i+1])
                edges.append((p0, p1))
            # close loop
            if len(pts) > 1:
                edges.append((tuple(pts[-1]), tuple(pts[0])))
            shape = [edges]  # one sub-shape
            shapes.append(shape)
        return shapes

    # --- STEP 5: RDP simplification ---
    def rdp(self, points, epsilon):
        if len(points) < 3:
            return points
        (x1, y1) = points[0]
        (x2, y2) = points[-1]
        dx, dy = x2 - x1, y2 - y1
        denom = (dx*dx + dy*dy)**0.5 or 1.0
        max_dist, index = -1, -1
        for i in range(1, len(points)-1):
            (x0, y0) = points[i]
            num = abs(dy*x0 - dx*y0 + x2*y1 - y2*x1)
            dist = num / denom
            if dist > max_dist:
                max_dist, index = dist, i
        if max_dist > epsilon:
            left = self.rdp(points[:index+1], epsilon)
            right = self.rdp(points[index:], epsilon)
            return left[:-1] + right
        else:
            return [points[0], points[-1]]

    def simplify_shapes(self, shapes, epsilon=1.0):
        new_shapes = []
        for shape in shapes:
            new_subs = []
            for sub in shape:
                if not sub:   
                    continue
                # build point list safely
                pts = [sub[0][0]] + [e[1] for e in sub]
                if len(pts) < 3:
                    new_subs.append(sub)
                    continue
                simp = self.rdp(pts, epsilon)
                # prevent collapse
                if len(simp) < 3:
                    simp = pts
                edges = [(simp[i], simp[i+1]) for i in range(len(simp)-1)]
                new_subs.append(edges)
            if new_subs:   # only keep non-empty shapes
                new_shapes.append(new_subs)
        return new_shapes


    # --- STEP 6: Sort shapes by nearest neighbor ---
    def sort_shapes(self, shapes):
        def start(shape): return shape[0][0][0]
        def end(shape): return shape[-1][-1][1]
        shapes = [s for s in shapes if s and s[0]]
        if not shapes: return []
        ordered = [shapes.pop(0)]
        while shapes:
            last_end = end(ordered[-1])
            best_idx, best_dist = None, float("inf")
            for i, s in enumerate(shapes):
                sx, sy = start(s)
                lx, ly = last_end
                d2 = (sx-lx)**2 + (sy-ly)**2
                if d2 < best_dist:
                    best_dist, best_idx = d2, i
            ordered.append(shapes.pop(best_idx))
        return ordered

    # --- MAIN ENTRY ---
    def vectorize(self, im, colors=16, epsilon=1.0, merge_strength=1.0, clockwise=False, do_sort=True):
        """
        Full pipeline: quantize → mask → contours → shapes → simplify → sort
        merge_strength : float
            Controls how aggressively shapes are merged.
            - 0.0 → no merging (raw OpenCV contours)
            - 0.5 → light merging (remove speckles)
            - 1.0 → moderate merging (merge small gaps)
            - 2.0+ → strong merging (behaves like flood‑fill) 

        """
        im_q = self.quantize_image(im, colors)
        pixels = np.array(im_q)
        h, w, _ = pixels.shape

        color_joined_pieces = {}
        unique_colors = np.unique(pixels.reshape(-1,4), axis=0)
        num_ucolors=len(unique_colors)
        for iii,color in enumerate(unique_colors):
            self.set_progress(iii+1,num_ucolors)
            mask = self.build_mask(pixels, color)
            contours = self.find_contours(mask)
            shapes = self.contours_to_shapes(contours)
            shapes = self.simplify_shapes(shapes, epsilon)
            shapes = self.merge_shapes(shapes, merge_strength,clockwise)
            if do_sort:
                shapes = self.sort_shapes(shapes)
            shapes = self.remove_empty_shapes(shapes)
            if shapes:
                color_joined_pieces[tuple(color)] = shapes
        if len(color_joined_pieces)==0:
            return color_joined_pieces
        color_joined_pieces=self.reorder_colors_by_area(color_joined_pieces)
        color_joined_pieces=self.small_detail_removal(color_joined_pieces)
        return color_joined_pieces

    def reorder_colors_by_area(self, color_joined_pieces):
        """
        Reorder colors by the area of their largest outer polygon.
        Largest area = background (bottom layer)
        Smallest area = top layer
        """

        def polygon_area_of_shape(shape):
            # shape[0] is the outer ring
            outer = shape[0]
            pts = [outer[0][0]] + [e[1] for e in outer]
            # Shoelace formula
            area = 0
            for i in range(len(pts)):
                x1, y1 = pts[i]
                x2, y2 = pts[(i+1) % len(pts)]
                area += x1 * y2 - x2 * y1
            return abs(area) / 2

        # Compute max area per color
        color_areas = {}
        for color, shapes in color_joined_pieces.items():
            if not shapes:
                color_areas[color] = 0
            else:
                color_areas[color] = max(polygon_area_of_shape(s) for s in shapes)

        # Sort by area descending (largest = background)
        ordered_colors = sorted(color_areas.keys(), key=lambda c: -color_areas[c])

        # Rebuild dictionary
        new_dict = {color: color_joined_pieces[color] for color in ordered_colors}
        return new_dict

    def reorder_colors_by_containment(self, color_joined_pieces):
        """
        (Slow)
        Reorder colors based on geometric containment:
        - Large shapes that contain others go BELOW
        - Small shapes inside others go ABOVE
        - Produces correct layer order for subtraction and rendering
        """

        if not color_joined_pieces:
            return color_joined_pieces

        # --- STEP 1: Extract bounding boxes for each color -------------------------
        def get_bounds_for_color(shapes):
            bounds = []
            for shape in shapes:
                outer = shape[0]  # outer ring
                pts = [outer[0][0]] + [e[1] for e in outer]
                xs = [p[0] for p in pts]
                ys = [p[1] for p in pts]
                bounds.append((min(xs), min(ys), max(xs), max(ys)))
            return bounds

        color_bounds = {
            color: get_bounds_for_color(shapes)
            for color, shapes in color_joined_pieces.items()
        }

        # --- STEP 2: Bounding-box containment test --------------------------------
        def box_contains(a, b):
            ax1, ay1, ax2, ay2 = a
            bx1, by1, bx2, by2 = b
            return ax1 <= bx1 and ay1 <= by1 and ax2 >= bx2 and ay2 >= by2

        # --- STEP 3: Build containment graph --------------------------------------
        colors = list(color_joined_pieces.keys())
        graph = {c: set() for c in colors}

        for A in colors:
            for B in colors:
                if A == B:
                    continue
                # If ANY shape of A contains ANY shape of B → A must be BELOW B
                if any(box_contains(a_box, b_box)
                    for a_box in color_bounds[A]
                    for b_box in color_bounds[B]):
                    graph[A].add(B)

        # --- STEP 4: Topological sort (bottom → top) ------------------------------
        visited = set()
        order = []

        def dfs(node):
            if node in visited:
                return
            visited.add(node)
            for nxt in graph[node]:
                dfs(nxt)
            order.append(node)

        for c in colors:
            dfs(c)

        # order is bottom → top
        ordered_colors = order

        # --- STEP 5: Rebuild dictionary in correct order --------------------------
        new_dict = {color: color_joined_pieces[color] for color in ordered_colors}
        return new_dict

    def small_detail_removal(self,color_joined_pieces):
        mcjp={}
        for color in color_joined_pieces:
            cjp = self.subtract_nested_shapes(
                color_joined_pieces,
                background_color=color, 
                clockwise=True)
            mcjp[color]=cjp[color]
        return mcjp

    def subtract_nested_shapes(self, color_joined_pieces, background_color, clockwise=True):
        """
        Subtract all shapes of other colors from the background color.
        This gives the background proper holes so it no longer covers everything.

        Parameters
        ----------
        color_joined_pieces : dict
            { (r,g,b,a) : [shapes] }
        background_color : tuple
            The color tuple (r,g,b,a) representing the background.
        clockwise : bool
            Orientation for output rings.

        Returns
        -------
        dict
            Updated color_joined_pieces with background shapes corrected.
        """

        if background_color not in color_joined_pieces:
            return color_joined_pieces  # nothing to do

        # --- 1. Collect background polygons ---------------------------------------
        bg_shapes = color_joined_pieces[background_color]
        bg_polys = []

        for shape in bg_shapes:
            for sub in shape:
                pts = [sub[0][0]] + [e[1] for e in sub]
                if len(pts) >= 3:
                    bg_polys.append([(int(p[0]), int(p[1])) for p in pts])

        if not bg_polys:
            return color_joined_pieces

        # --- 2. Collect all other polygons ----------------------------------------
        other_polys = []

        for color, shapes in color_joined_pieces.items():
            if color == background_color:
                continue
            for shape in shapes:
                for sub in shape:
                    pts = [sub[0][0]] + [e[1] for e in sub]
                    # if len(pts) >= 3:
                    other_polys.append([(int(p[0]), int(p[1])) for p in pts])

        # If no other shapes, nothing to subtract
        if not other_polys:
            return color_joined_pieces

        # --- 3. Boolean difference: background - others ---------------------------
        clip = pyclipper.Pyclipper()
        clip.AddPaths(bg_polys, pyclipper.PT_SUBJECT, True)
        clip.AddPaths(other_polys, pyclipper.PT_CLIP, True)

        result_tree = clip.Execute2(
            pyclipper.CT_DIFFERENCE,
            pyclipper.PFT_NONZERO,
            pyclipper.PFT_NONZERO
        )

        # --- 4. Convert PolyTree → shapes (outer + holes) -------------------------
        new_bg_shapes = []
        for child in result_tree.Childs:
            rings = self.extract_rings_from_tree(child, clockwise)
            if rings:
                new_bg_shapes.append(rings)

        # --- 5. Replace background entry ------------------------------------------
        color_joined_pieces[background_color] = new_bg_shapes

        return color_joined_pieces

    
    def remove_empty_shapes(self, shapes):
        cshapes=[]
        for iii,sub_shape in enumerate(shapes):
            if isinstance(sub_shape,(list,tuple)) and len(sub_shape)>0:
               cshapes.append(sub_shape)
        return cshapes 
    
    def polygon_to_shape(self, poly , clockwise=True):
        """
        Convert a pyclipper polygon (list of [x,y]) into your internal
        shape/subshape/edge format:
            shape = [ subshape ]
            subshape = [ (p0,p1), (p1,p2), ... ]
        """
        if not poly or len(poly) < 3:
            return None

        # ensure tuples
        pts = [(float(x), float(y)) for (x, y) in poly]
        # enforce clockwise orientation
        pts = self.ensure_direction(pts,clockwise)

        # build edges
        edges = [(pts[i], pts[i+1]) for i in range(len(pts)-1)]

        return [edges]   # one subshape
    
    def ensure_direction(self, pts, clockwise=True):
        """
        Ensure polygon points follow the desired winding direction.

        SVG uses winding direction to determine fill behavior:
        - Clockwise (CW) polygons are treated as filled regions.
        - Counter-clockwise (CCW) polygons are treated as holes.

        Parameters
        ----------
        pts : list of (x, y)
            Polygon vertices in order.
        clockwise : bool
            True  → enforce clockwise orientation
            False → enforce counter-clockwise orientation

        Returns
        -------
        list of (x, y)
            Polygon with enforced winding direction.
        """
        if len(pts) < 3:
            return pts

        # Compute signed area (shoelace-like test)
        area = 0.0
        for i in range(len(pts)):
            x1, y1 = pts[i]
            x2, y2 = pts[(i + 1) % len(pts)]
            area += (x2 - x1) * (y2 + y1)

        is_ccw = area > 0

        # If we want CW but got CCW → reverse
        if clockwise and is_ccw:
            pts = list(reversed(pts))

        # If we want CCW but got CW → reverse
        if not clockwise and not is_ccw:
            pts = list(reversed(pts))

        return pts

    def merge_shapes(self, shapes, merge_strength=0.0,clockwise=True):
        """
            Merge nearby or fragmented shapes into larger unified regions.

        Uses polygon offset + union + reverse offset to merge shapes that are
        close together. merge_strength controls how aggressively shapes are merged.

        This function performs polygon union on all shapes of the same color.
        It works by:
            1. Converting each shape (list of subshapes/edges) into a polygon.
            2. Offsetting (inflating) polygons by `merge_strength` to close gaps.
            3. Performing a union operation to merge overlapping/adjacent shapes.
            4. Offsetting (deflating) the merged polygons back to original size.
            5. Converting the merged polygons back into your shape/subshape format.

        Parameters
        ----------
        shapes : list
            A list of shapes, where each shape is a list of subshapes,
            and each subshape is a list of edges [(p0,p1), (p1,p2), ...].
        merge_strength : float
            Controls how aggressively shapes are merged.
            - 0.0 → no merging (raw OpenCV contours)
            - 0.5 → light merging (remove speckles)
            - 1.0 → moderate merging (merge small gaps)
            - 2.0+ → strong merging (behaves like flood‑fill)

        Returns
        -------
        list
            A new list of merged shapes in the same format as the input.
        """
        if merge_strength <= 0:
            return shapes

        # --- Convert shapes → polygons -----------------------------------------
        polygons = []
        for shape in shapes:
            for sub in shape:
                if not sub:
                    continue
                pts = [sub[0][0]] + [e[1] for e in sub]
                if len(pts) < 3:
                    continue
                poly = [(int(p[0]), int(p[1])) for p in pts]
                polygons.append(poly)

        if not polygons:
            return []

        # --- Inflate polygons ---------------------------------------------------
        pc = pyclipper.PyclipperOffset()
        for poly in polygons:
            pc.AddPath(poly, pyclipper.JT_MITER, pyclipper.ET_CLOSEDPOLYGON)
        inflated = pc.Execute(merge_strength)

        # --- CLEAN + FILTER inflated polygons (critical!) -----------------------
        cleaned = []
        for p in inflated:
            p = pyclipper.CleanPolygon(p)
            if len(p) >= 3:
                cleaned.append(p)

        # If nothing survives, skip merging for this color
        if not cleaned:
            return []

        inflated = cleaned

        # --- Union inflated polygons (tree version) -------------------------------
        clip = pyclipper.Pyclipper()
        clip.AddPaths(inflated, pyclipper.PT_SUBJECT, True)
        tree = clip.Execute2(pyclipper.CT_UNION, pyclipper.PFT_NONZERO, pyclipper.PFT_NONZERO)

        # --- Deflate back ---------------------------------------------------------
        pc2 = pyclipper.PyclipperOffset()
        pc2.AddPaths(pyclipper.PolyTreeToPaths(tree), pyclipper.JT_MITER, pyclipper.ET_CLOSEDPOLYGON)
        final_tree = pc2.Execute2(-merge_strength)

        # --- Convert polygons → shapes (outer + holes) ----------------------------
        merged_shapes = []
        for child in final_tree.Childs:
            rings = self.extract_rings_from_tree(child, clockwise)
            if rings:
                merged_shapes.append(rings)


        return merged_shapes
    
    def extract_rings_from_tree(self, node, clockwise=True):
        """
        Recursively extract outer and hole rings from a pyclipper PolyTree node.
        Returns a list of subshapes (each subshape is a list of edges).
        """
        rings = []

        # Extract this contour
        if node.Contour:
            pts = [(float(x), float(y)) for x, y in node.Contour]

            # Outer rings must be CW, holes must be CCW
            if node.IsHole:
                pts = self.ensure_direction(pts, clockwise=False)
            else:
                pts = self.ensure_direction(pts, clockwise=True)

            # Convert to edges
            edges = [(pts[i], pts[i+1]) for i in range(len(pts)-1)]
            rings.append(edges)

        # Recurse into children
        for child in node.Childs:
            rings.extend(self.extract_rings_from_tree(child, clockwise))

        return rings
    


def main():
    import class_LogHandler
    filepath=os.path.join(class_LogHandler.get_appPath(),'test')
    fileinput=os.path.join(filepath,'wp9102708.jpg')
    # fileinput=os.path.join(filepath,'Actions-arrow-up-icon.png')
    if not os.path.exists(fileinput):
        print(f"File {fileinput} does not exist")
        return 
    fileoutput=fileinput.replace('.jpg','.svg').replace('.png','.svg')
    gcodefileoutput=fileinput.replace('.jpg','.gcode').replace('.png','.gcode')
    imageRGBA = Image.open(fileinput).quantize(colors=16, method=2).convert('RGBA')    
    print('Processing image of size',imageRGBA.size)    
    kill_ev = threading.Event()
    kill_ev.clear()
    Vectorize=Vectorization(imageRGBA,kill_ev)
    Vectorize.start()
    Vectorize.printprocess=True
    # Works but is veeeeeeeeeeeery sloooooooow
    #svg_image = Vectorize.rgba_image_to_svg_contiguous(an_image=imageRGBA)
    Img_ini_pos=(0,0)
    Robot_XYZ=[0,0,5]
    Resolution=100/3840
    Feedrate= 333
    Gimageinfo =[Img_ini_pos, Robot_XYZ, Resolution, Feedrate]
                # Img_ini_pos : (x, y) world‑space origin of the image
                # Robot_XYZ   : (X, Y, Z) robot position (X,Y used)
                # Resolution  : pixel‑to‑world scaling factor
                # Feedrate    : default G‑code feedrate
    svg_image = Vectorize.vectorizer_rgba_image_to_svg_contiguous(im=imageRGBA,epsilon=0,merge_strength=0)
    if Vectorize.last_color_joined_pieces:
        Vectorize.Vectorized_color_joined_pieces_to_gcode_contiguous_file(
            imageRGBA,
            Vectorize.last_color_joined_pieces,
            Gimageinfo,
            'G1 Z0',
            'G1 Z3.3',
            gcodefileoutput,
            )
    #svg_image = rgba_image_to_svg_pixels(image)
    Vectorize.Save_svg_text_file(svg_image,fileoutput)
    Vectorize.join()
    print(f"Finished .... check \n{fileoutput}\n{gcodefileoutput}")
    

        
if __name__ == '__main__':
    main()
