######################
# With coffee and love by F.G
# 19.09.2025
######################

import serial
import serial.tools.list_ports
import resources_rc
import class_File_Dialogs

from PyQt6.QtWidgets import *
from PyQt6 import QtWidgets, QtGui, QtCore

class SerialReader(QtCore.QThread):
    received = QtCore.pyqtSignal(str)

    def __init__(self, ser):
        super().__init__()
        self.ser = ser
        self.running = True

    def run(self):
        while self.running:
            try:
                line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                if line:
                    self.received.emit(line)
            except Exception as e:
                self.received.emit(f"[Error reading] {e}")
                break

    def stop(self):
        self.running = False
        self.wait()

class SerialTerminalDialog(QtWidgets.QDialog):
    closed = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Serial Terminal")
        self.resize(650, 450)

        # Widgets
        self.text_console = QtWidgets.QTextEdit()
        self.text_console.setReadOnly(True)

        self.input_line = QtWidgets.QLineEdit()
        self.input_line.returnPressed.connect(self.send_data)

        # --- NEW: Baudrate Combo ---
        self.combo_baud = QtWidgets.QComboBox()
        # baudrates = [
        #     "9600", "14400", "19200", "28800", "38400",
        #     "57600", "91600", "115200", "250000"
        # ]
        supported_baudrates = serial.Serial.BAUDRATES 
        baudrates = [str(b) for b in supported_baudrates]
        self.combo_baud.addItems(baudrates)
        
        # Set default baudrate
        default_baud = "115200"
        index = self.combo_baud.findText(default_baud, QtCore.Qt.MatchFlag.MatchFixedString)
        if index >= 0:
            self.combo_baud.setCurrentIndex(index)

        # --- Port Combo ---
        self.port_box = QtWidgets.QComboBox()
        
        # Filter checkbox
        self.filter_checkbox = QtWidgets.QCheckBox("USB only")
        self.filter_checkbox.setChecked(True)   # default ON
        self.filter_checkbox.setToolTip("Show only real USB serial devices")
        self.filter_checkbox.stateChanged.connect(self.refresh_ports)
        # Connect button
        self.connect_btn = QtWidgets.QPushButton("Connect")
        self.connect_btn.setIcon(QtGui.QIcon(":/img/connect-icon.png"))
        self.connect_btn.clicked.connect(self.toggle_connection)
        self.refresh_btn = QtWidgets.QPushButton("Refresh")
        self.refresh_btn.setIcon(QtGui.QIcon(":/img/Actions-view-refresh-icon.png"))
        self.refresh_btn.clicked.connect(self.refresh_ports)
        self.clear_btn = QtWidgets.QPushButton("Clear")
        self.clear_btn.setIcon(QtGui.QIcon(":/img/Clear-icon.png"))
        self.clear_btn.clicked.connect(self.clear_text)
        self.save_btn = QtWidgets.QPushButton("Save")
        self.save_btn.setIcon(QtGui.QIcon(":/img/Floppy-Small-icon.png"))
        self.save_btn.clicked.connect(self.save_text)

        # Layout (top bar)
        top = QtWidgets.QHBoxLayout()
        top.addWidget(self.filter_checkbox)
        
        top.addWidget(QtWidgets.QLabel("Port:"))
        top.addWidget(self.port_box)
        top.addWidget(QtWidgets.QLabel("Baud:"))
        top.addWidget(self.combo_baud)
        top.addWidget(self.connect_btn)

        tools = QtWidgets.QHBoxLayout()
        tools.addWidget(self.refresh_btn)
        tools.addWidget(self.clear_btn)
        tools.addStretch()
        tools.addWidget(self.save_btn)

        # Main layout
        layout = QtWidgets.QVBoxLayout(self)
        layout.addLayout(top)
        layout.addLayout(tools)
        layout.addWidget(self.text_console)
        layout.addWidget(self.input_line)

        # Serial objects
        self.ser = None
        self.reader = None
        self.refresh_ports()

    def clear_text(self):
        self.text_console.setText("")

    def refresh_ports(self):
        ports = serial.tools.list_ports.comports()
        self.port_box.clear()

        usb_only = self.filter_checkbox.isChecked()

        for p in ports:
            dev = p.device

            if usb_only:
                # Only show real USB serial devices
                if p.vid is None:
                    continue

            self.port_box.addItem(dev)


    def save_text(self):
        dialog=class_File_Dialogs.Dialogs()
        filename=dialog.saveFileDialog(2)
        if filename is not None and filename!='':
            with open(filename, "w", encoding="utf-8") as f:
                f.write(self.text_console.toPlainText())

    def toggle_connection(self):
        if self.ser and self.ser.is_open:
            self.disconnect_serial()
        else:
            self.connect_serial()

    def connect_serial(self):
        port = self.port_box.currentText()
        baud = int(self.combo_baud.currentText())   # <-- NEW

        try:
            self.ser = serial.Serial(port, baudrate=baud, timeout=0.1)
            self.reader = SerialReader(self.ser)
            self.reader.received.connect(self.append_text)
            self.reader.start()

            self.connect_btn.setText("Disconnect")
            self.append_text(f"[Connected to {port} @ {baud} baud]")

        except Exception as e:
            self.append_text(f"[Connection error] {e}")

    def disconnect_serial(self):
        if self.reader:
            self.reader.stop()
        if self.ser and self.ser.is_open:
            self.ser.close()

        self.connect_btn.setText("Connect")
        self.append_text("[Disconnected]")

    def append_text(self, text):
        self.text_console.append(text)

    def send_data(self):
        if self.ser and self.ser.is_open:
            data = self.input_line.text()
            try:
                self.ser.write((data + "\n").encode("utf-8"))
                self.append_text(f"[TX] {data}")
            except Exception as e:
                self.append_text(f"[Error writing] {e}")
        self.input_line.clear()

    def closeEvent(self, event):
        self.disconnect_serial()
        self.closed.emit()
        super().closeEvent(event)
