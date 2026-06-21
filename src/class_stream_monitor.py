######################
# With coffee and love by F.G
# 21.06.2026
######################

import resources_rc
from PyQt6.QtWidgets import *
from PyQt6 import QtWidgets, QtGui, QtCore
from collections import deque
from datetime import datetime 

MAX_BLOCK_COUNT = 20000

class StreamMonitorDialog(QtWidgets.QDialog):
    closed = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            QtCore.Qt.WindowType.Window |
            QtCore.Qt.WindowType.WindowTitleHint |
            QtCore.Qt.WindowType.WindowCloseButtonHint
        )
        self.setWindowTitle("Machine Stream Monitor")
        self.resize(1000, 500)
        #------- Variables --------#
        self._pending_tx = deque(maxlen=MAX_BLOCK_COUNT)
        self._pending_rx = deque(maxlen=MAX_BLOCK_COUNT)
        self.is_empty_read=False
        
        #------------------

        self.tx_console = QtWidgets.QPlainTextEdit()
        self.rx_console = QtWidgets.QPlainTextEdit()
        # self._tx_cursor = self.tx_console.textCursor()
        # self._rx_cursor = self.rx_console.textCursor()

        # self._tx_cursor.beginEditBlock()
        # self._rx_cursor.beginEditBlock()

        # self._batching = False
        
        # Highlighter
        self.tx_highlighter = MonitorHighlighter(self.tx_console.document())
        self.rx_highlighter = MonitorHighlighter(self.rx_console.document())

        for console in (self.tx_console, self.rx_console):
            console.setReadOnly(True)

            font = QtGui.QFont("Consolas")
            font.setStyleHint(QtGui.QFont.StyleHint.Monospace)
            console.setFont(font)

            # Optional: disable line wrap for long commands
            console.setLineWrapMode(
                QtWidgets.QPlainTextEdit.LineWrapMode.NoWrap
            )
        self.tx_console.setMaximumBlockCount(MAX_BLOCK_COUNT)
        self.rx_console.setMaximumBlockCount(MAX_BLOCK_COUNT)
        # ------------------------------------------------------------------
        # Scroll Synchronization
        # ------------------------------------------------------------------

        self.scroll_sync = SyncedScrollController(
            self.tx_console,
            self.rx_console
        )

        # ------------------------------------------------------------------
        # Layout
        # ------------------------------------------------------------------

        splitter = QtWidgets.QSplitter(
            QtCore.Qt.Orientation.Horizontal
        )

        splitter.addWidget(self.tx_console)
        splitter.addWidget(self.rx_console)

        splitter.setSizes([500, 500])

        self.show_timestamp = QtWidgets.QCheckBox("Show timestamps")
        self.show_timestamp.setChecked(True)    

        self.show_empty_read = QtWidgets.QCheckBox("Show Empty Read")
        self.show_empty_read.setChecked(False)   

        self.clear_btn = QtWidgets.QPushButton("Clear")
        self.clear_btn.setIcon(QtGui.QIcon(":/img/Clear-icon.png"))
        
        self.scroll_bottom_btn = QtWidgets.QPushButton("Scroll to Bottom")
        self.scroll_bottom_btn.setIcon(QtGui.QIcon(":/img/Actions-go-next-view-icon_Zdown.png"))

        self.pause_display = QtWidgets.QCheckBox("Pause Display")
        self.pause_display.setIcon(QtGui.QIcon(":/img/Button-Pause-icon.png"))

        controls_layout = QtWidgets.QHBoxLayout()
        controls_layout.addWidget(self.show_timestamp)
        controls_layout.addWidget(self.show_empty_read)
        controls_layout.addWidget(self.clear_btn)
        controls_layout.addStretch()
        controls_layout.addWidget(self.pause_display)
        controls_layout.addWidget(self.scroll_bottom_btn)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(splitter)
        layout.addLayout(controls_layout)

        self._do_connections()
        # sync scroll
        self._scroll_both_to_bottom()
        self._show_empty(self.is_empty_read)
    
    def _do_connections(self):
        """Connects all actions"""
        self.clear_btn.clicked.connect(self.clear)
        self.scroll_bottom_btn.clicked.connect(self._scroll_both_to_bottom)
        # Pause
        self.pause_display.toggled.connect(self._pause_toggled)
        self.show_empty_read.toggled.connect(self._show_empty)
    
    def _scroll_both_to_bottom(self):
        """Scrolls both consoles to last entry"""
        sb1 = self.tx_console.verticalScrollBar()
        sb2 = self.rx_console.verticalScrollBar()

        sb1.setValue(sb1.maximum())
        sb2.setValue(sb2.maximum())
    
    def _pause_toggled(self, paused):
        self._update_pause_state(paused)
        if paused:
            return

        self._flush_pending()
    
    def _show_empty(self, show_empty):        
        self.is_empty_read=not bool(show_empty)
    
    def _update_pause_state(self, paused):
        if paused:
            self.pause_display.setIcon(
                QtGui.QIcon(":/img/Button-Play-icon.png")
            )
            self.pause_display.setText("Resume")
        else:
            self.pause_display.setIcon(
                QtGui.QIcon(":/img/Button-Pause-icon.png")
            )
            self.pause_display.setText("Pause Display")
    
    def _flush_pending(self):
        for line in self._pending_tx:
            self.tx_console.appendPlainText(line)

        for line in self._pending_rx:
            self.rx_console.appendPlainText(line)

        self._pending_tx.clear()
        self._pending_rx.clear()

    def clear(self):
        """Cleasr the Console's text"""
        self.tx_console.clear()
        self.rx_console.clear()

    def _timestamp(self, timestamp=None):
        """Returns formatted timestamp text"""

        # If external timestamp is provided (epoch float)
        if isinstance(timestamp, (float, int)):
            dt = datetime.fromtimestamp(timestamp)
            return dt.strftime("%H:%M:%S.%f")[:-3]  # ms precision

        # Otherwise use Qt current time (UI-time)
        return QtCore.QDateTime.currentDateTime().toString(
            "hh:mm:ss.zzz"
        )
    
    def _format_line(self, timestamp, prefix, text=""):
        """Gets formatted text"""
        if self.show_timestamp.isChecked():
            return f"{timestamp} {prefix} {text}"
        return f"{prefix} {text}"

    def append_tx(self, text:str, timestamp:float=None):
        """Appends Transmitted text to the monitor

        Args:
            text (str): Text to be dispayed
        """
        ts = self._timestamp(timestamp)
        tx_line = self._format_line(ts,">>>",text.rstrip()
        )
        rx_line = self._format_line(ts,">>>")

        if self.pause_display.isChecked():

            self._pending_tx.append(tx_line)
            self._pending_rx.append(rx_line)
            return

        self.tx_console.appendPlainText(tx_line)
        self.rx_console.appendPlainText(rx_line)

    def append_rx(self, text:str,timestamp:float=None):
        """Appends Received text to the monitor

        Args:
            text (str): Text to be dispayed
        """      
        ts = self._timestamp(timestamp)
        lines = text.splitlines() or [""]

        for line in lines:
            txt=line.rstrip()
            if self.is_empty_read and not txt:
                continue
            rx_line = self._format_line(ts,"<<<",line.rstrip())
            tx_line = self._format_line(ts,"<<<")

            if self.pause_display.isChecked():
                self._pending_tx.append(tx_line)
                self._pending_rx.append(rx_line)

            else:
                self.tx_console.appendPlainText(tx_line)
                self.rx_console.appendPlainText(rx_line)
    
    def begin_batch(self):
        self._batching = True
        self._tx_cursor.beginEditBlock()
        self._rx_cursor.beginEditBlock()


    def end_batch(self):
        self._tx_cursor.endEditBlock()
        self._rx_cursor.endEditBlock()
        self._batching = False
    
    def closeEvent(self, event):
        self.closed.emit()
        super().closeEvent(event)


class MonitorHighlighter(QtGui.QSyntaxHighlighter):

    def __init__(self, document):
        super().__init__(document)

        self.rules = []

        # ---------------------------------------------------------
        # TX >>>  (light blue)
        # ---------------------------------------------------------
        fmt_tx = QtGui.QTextCharFormat()
        fmt_tx.setForeground(QtGui.QColor("#6CB6FF"))

        self.rules.append(
            (QtCore.QRegularExpression(r".*>>>.*"), fmt_tx)
        )

        # ---------------------------------------------------------
        # RX <<<  (light green)
        # ---------------------------------------------------------
        fmt_rx = QtGui.QTextCharFormat()
        fmt_rx.setForeground(QtGui.QColor("#7EE787"))

        self.rules.append(
            (QtCore.QRegularExpression(r".*<<<.*"), fmt_rx)
        )

        # ---------------------------------------------------------
        # error: (red)
        # ---------------------------------------------------------
        fmt_error = QtGui.QTextCharFormat()
        fmt_error.setForeground(QtGui.QColor("#FF6B6B"))
        fmt_error.setFontWeight(QtGui.QFont.Weight.Bold)

        self.rules.append(
            (QtCore.QRegularExpression(r"(?i)error.*"), fmt_error)
        )

        # ---------------------------------------------------------
        # ALARM: (orange)
        # ---------------------------------------------------------
        fmt_alarm = QtGui.QTextCharFormat()
        fmt_alarm.setForeground(QtGui.QColor("#FFA657"))
        fmt_alarm.setFontWeight(QtGui.QFont.Weight.Bold)

        self.rules.append(
            (QtCore.QRegularExpression(r"(?i)alarm.*"), fmt_alarm)
        )

        # ---------------------------------------------------------
        # ok (gray)
        # ---------------------------------------------------------
        fmt_ok = QtGui.QTextCharFormat()
        fmt_ok.setForeground(QtGui.QColor("#8B949E"))

        self.rules.append(
            (QtCore.QRegularExpression(r"(?i)\bok\b.*$"), fmt_ok)
        )

    def highlightBlock(self, text):

        for regex, fmt in self.rules:

            it = regex.globalMatch(text)

            while it.hasNext():
                match = it.next()

                self.setFormat(
                    match.capturedStart(),
                    match.capturedLength(),
                    fmt
                )

class SyncedScrollController(QtCore.QObject):

    def __init__(self, left_widget, right_widget):
        super().__init__()

        self.left = left_widget
        self.right = right_widget

        self._syncing = False

        self.left.verticalScrollBar().valueChanged.connect(
            self._left_changed
        )

        self.right.verticalScrollBar().valueChanged.connect(
            self._right_changed
        )

    def _left_changed(self, value):

        if self._syncing:
            return

        self._syncing = True

        try:
            self.right.verticalScrollBar().setValue(value)
        finally:
            self._syncing = False

    def _right_changed(self, value):

        if self._syncing:
            return

        self._syncing = True

        try:
            self.left.verticalScrollBar().setValue(value)
        finally:
            self._syncing = False