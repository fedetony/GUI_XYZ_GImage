from PyQt6.QtWidgets import *
from PyQt6 import QtWidgets, QtGui, QtCore

class EmergencyStopDialog(QtWidgets.QDialog):
    closed = QtCore.pyqtSignal()
    pressed= QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Emergency Stop")
        self.setWindowFlag(QtCore.Qt.WindowType.WindowStaysOnTopHint)
        self.setWindowFlag(QtCore.Qt.WindowType.Tool)

        layout = QtWidgets.QVBoxLayout(self)

        self.stop_button = QtWidgets.QPushButton("STOP")
        self.stop_button.setStyleSheet("font-size: 24px; background: red; color: white;")
        layout.addWidget(self.stop_button)

        self.resize(200, 100)
        self.stop_button.clicked.connect(self.stop_button_pressed)
    
    def stop_button_pressed(self):
        self.pressed.emit()
    
    def closeEvent(self, event):
        self.closed.emit()
        super().closeEvent(event)
# To connect in main window
# self.stop_dialog = EmergencyStopDialog(self)
# self.stop_dialog.stop_button.clicked.connect(self.handle_emergency_stop)


class LogWindow(QtWidgets.QMainWindow):
    closed = QtCore.pyqtSignal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Application Log")
        self.resize(600, 400)

        self.text_edit = QtWidgets.QTextEdit()
        self.text_edit.setReadOnly(True)
        self.setCentralWidget(self.text_edit)

    def write_GUI_Log(self, text):
        """Called by ConsolePanelHandler"""
        self.text_edit.append(text)

    def closeEvent(self, event):
        self.closed.emit()
        super().closeEvent(event)


# self.log_window = LogWindow(self) 
# Example: whenever you log something 
# self.log_window.append_text("System started")