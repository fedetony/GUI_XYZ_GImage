from PyQt6 import QtWidgets, QtGui, QtCore

class SyncedScrollZoomController(QtCore.QObject):
    """
    A generalized N‑view synchronization controller for QGraphicsView.

    Each registered view declares how its local scrollbars map to a shared
    global coordinate system (X, Y, Z, ...). This allows arbitrary
    orthographic projections such as XY, XZ, YZ, or custom views.

    The controller synchronizes:
        • Scroll positions (per‑axis, with sign)
        • Zoom level (uniform across all views)

    Example mapping for a view:
        {
            "h": ("X", +1),   # horizontal scrollbar → +X axis
            "v": ("Y", -1),   # vertical scrollbar → -Y axis (flipped)
        }

    This allows:
        • Flipped views (scale(1, -1))
        • Rotated views (rotate(90/180/270))
        • Arbitrary projections
        • Any number of views
    """

    zoom_changed = QtCore.pyqtSignal(float)

    def __init__(self):
        super().__init__()
        self.views = []               # list of (view, mapping)
        self.global_scroll = {"X": 0, "Y": 0, "Z": 0}      # {"X": value, "Y": value, "Z": value}
        self.current_zoom = 1.0
        self.min_zoom = 0.001
        self.max_zoom = 50.0
        self.extents = {"X": 1000, "Y": 1000, "Z": 1000}

    # ------------------------------------------------------------------
    # View Registration
    # ------------------------------------------------------------------
    def register_view(self, view: QtWidgets.QGraphicsView, mapping:dict):
        """
        Register a QGraphicsView with an axis mapping.

        Parameters
        ----------
        view : QGraphicsView
            The view to synchronize.
        mapping : dict
            A dictionary describing how the view's scrollbars map to
            global axes. Keys:
                "h" → horizontal scrollbar
                "v" → vertical scrollbar
            Values:
                (axis_name: str, sign: int)
            Example:
                {"h": ("X", +1), "v": ("Y", -1)}
        """
        self.views.append((view, mapping))
        self.update_global_scroll(view,view.height(),view.width(),True)
        # Initialize global axes
        for axis, sign in mapping.values():
            if axis not in self.global_scroll:
                # self.update_global_scroll(view,view.height(),view.width(),False)
                self.global_scroll[axis] = 0
    
    def remove_view(self, view: QtWidgets.QGraphicsView):
        """
        Unregister a view from synchronization.

        Parameters
        ----------
        view :
            The view to remove. If not registered, this is a no‑op.
        """
        self.views = [(v, m) for (v, m) in self.views if v is not view]

    # ------------------------------------------------------------------
    # Scroll Synchronization
    # ------------------------------------------------------------------
    def update_global_scroll(self, source_view, h, v, push_to_others=True):
        """
        Update the global scroll state based on a view's local scrollbars.

        Parameters
        ----------
        source_view : QGraphicsView
            The view that triggered the scroll event.
        h : int
            Horizontal scrollbar value.
        v : int
            Vertical scrollbar value.
        """
        mapping = None
        for view, m in self.views:
            if view is source_view:
                mapping = m
                break
        if mapping is None:
            return

        z = self.current_zoom

        # Horizontal axis
        if "h" in mapping:
            axis, sign = mapping["h"]
            # convert pixels → scene units
            self.global_scroll[axis] = (h * sign) / z

        # Vertical axis
        if "v" in mapping:
            axis, sign = mapping["v"]
            # convert pixels → scene units
            self.global_scroll[axis] = (v * sign) / z

        # Push to all other views
        if not push_to_others:
            return
        for view, m in self.views:
            if view is not source_view:
                view.apply_global_scroll(self.global_scroll, m)

    # ------------------------------------------------------------------
    # Size Synchronization
    # ------------------------------------------------------------------
    def update_extents(self, axis_sizes: dict):
        # axis_sizes: {"X": new_w, "Y": new_h, "Z": new_d}
        for k,v in axis_sizes.items():
            self.extents[k] = max(self.extents.get(k, 0), v)
        self._apply_scene_rects_to_views()

    def _apply_scene_rects_to_views(self):
        for view, mapping in self.views:
            # determine which global axes map to h and v

            if "h" in mapping and "v" in mapping:
                h_axis, _ = mapping["h"]
                v_axis, _ = mapping["v"]
                w = self.extents[h_axis]
                h = self.extents[v_axis]                
                view.scene().setSceneRect(0, 0, w, h)
                self._update_scrollbar_ranges(view)

    def _update_scrollbar_ranges(self, view:QtWidgets.QGraphicsView):
        zoom = self.current_zoom
        
        sr = view.sceneRect()
        vp = view.viewport().size()
        # horizontal
        h_max = max(0, sr.width()*zoom - vp.width())
        v_max = max(0, sr.height()*zoom - vp.height())
        view.horizontalScrollBar().setRange(0, int(h_max))
        view.horizontalScrollBar().setPageStep(int(vp.width()))
        view.verticalScrollBar().setRange(0, int(v_max))
        view.verticalScrollBar().setPageStep(int(vp.height()))
    
    def convert_scene_to_view_coords(self,view:QtWidgets.QGraphicsView,global_x, global_y):
        # convert scene units → view units
        vx, vy = view.base_transform.map(global_x, global_y)
        zoom= self.current_zoom
        # subtract transformed origin
        vx -= view.origin_x
        vy -= view.origin_y

        # convert to pixels
        px = int(vx * zoom)
        py = int(vy * zoom)

        return px,py
        



    # ------------------------------------------------------------------
    # Zoom Synchronization
    # ------------------------------------------------------------------
    def set_zoom(self, factor):
        """
        Set the global zoom factor and notify all views.

        Parameters
        ----------
        factor : float
            The new zoom factor (clamped to min/max).
        """
        factor = max(self.min_zoom, min(factor, self.max_zoom))
        self.current_zoom = factor
        self.zoom_changed.emit(factor)

    def zoom_by(self, multiplier):
        """Multiply the current zoom by a factor."""
        self.set_zoom(self.current_zoom * multiplier)

    def reset_zoom(self):
        """Reset zoom to 1.0."""
        self.set_zoom(1.0)

    # ------------------------------------------------------------------
    # Utility Zoom Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def zoom_to_fit_height(view, scene_rect):
        """Return zoom factor so scene height fits view height."""
        if scene_rect.height() == 0:
            return 1.0
        return view.viewport().height() / scene_rect.height()

    @staticmethod
    def zoom_to_fit_width(view, scene_rect):
        """Return zoom factor so scene width fits view width."""
        if scene_rect.width() == 0:
            return 1.0
        return view.viewport().width() / scene_rect.width()
    
    @staticmethod
    def zoom_to_fit_height(view: QtWidgets.QGraphicsView,
                        scene_rect: QtCore.QRectF) -> float:
        """
        Compute the zoom factor required so the scene's height fits exactly
        inside the view's viewport height.

        Parameters
        ----------
        view : QGraphicsView
            The view whose viewport is used for the calculation.
        scene_rect : QRectF
            The bounding rectangle of the scene.

        Returns
        -------
        float
            The zoom factor needed to fit the height.
        """
        if scene_rect.height() == 0:
            return 1.0

        viewport_h = view.viewport().height()
        return viewport_h / scene_rect.height()
    
    @staticmethod
    def zoom_to_fit_width(view: QtWidgets.QGraphicsView,
                        scene_rect: QtCore.QRectF) -> float:
        """
        Compute the zoom factor required so the scene's width fits exactly
        inside the view's viewport width.

        Parameters
        ----------
        view : QGraphicsView
            The view whose viewport is used for the calculation.
        scene_rect : QRectF
            The bounding rectangle of the scene.

        Returns
        -------
        float
            The zoom factor needed to fit the width.
        """
        if scene_rect.width() == 0:
            return 1.0

        viewport_w = view.viewport().width()
        return viewport_w / scene_rect.width()

    def best_fit_zoom(self, view: QtWidgets.QGraphicsView,
                  scene: QtWidgets.QGraphicsScene) -> float:
        """
        Compute the best zoom factor so the scene fits entirely inside the view,
        preserving aspect ratio.

        Parameters
        ----------
        view : QGraphicsView
            The view to fit.
        scene : QGraphicsScene
            The scene whose bounding rect is used.

        Returns
        -------
        float
            The zoom factor that fits both width and height.
        """
        rect = scene.sceneRect()
        zoom_h = self.zoom_to_fit_height(view, rect)
        zoom_w = self.zoom_to_fit_width(view, rect)
        return min(zoom_h, zoom_w)

    def set_fit_width(self, view: QtWidgets.QGraphicsView,
                  scene: QtWidgets.QGraphicsScene):
        zoom = self.zoom_to_fit_width(view, scene.sceneRect())
        self.set_zoom(zoom)

    def set_fit_height(self, view: QtWidgets.QGraphicsView,
                  scene: QtWidgets.QGraphicsScene):
        zoom = self.zoom_to_fit_height(view, scene.sceneRect())
        self.set_zoom(zoom)
    
    def set_best_fit(self, view: QtWidgets.QGraphicsView,
                  scene: QtWidgets.QGraphicsScene):
        zoom = self.best_fit_zoom(view, scene)
        self.set_zoom(zoom)
    
    def fit_all(self):
        for view, mapping in self.views:
            scene = view.scene()
            zoom = self.best_fit_zoom(view, scene)
            self.set_zoom(zoom)


