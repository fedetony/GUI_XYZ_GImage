import logging
import queue
import threading
import class_ST
import os
import sys
from pathlib import Path


class LoggerManager:
    def __init__(self, log_file):
        self.log_file = Path(log_file)
        self.log_queue = queue.Queue()
        self.root = logging.getLogger()
        self.root.setLevel(logging.DEBUG)

        if not self.root.handlers:
            self._setup_file_handler()
            self._setup_queue_handler()

        self.gui_handler = None
        self.update_thread = None

    def attach_gui_handler(self, gui_panel):
        # Create the list the first time
        if not hasattr(self, "gui_handlers"):
            self.gui_handlers = []

        # Create a new handler for this GUI panel
        handler = ConsolePanelHandler(gui_panel)
        handler.setLevel(logging.DEBUG)
        handler.setFormatter(logging.Formatter(
            "%(asctime)s [%(levelname)s] (%(threadName)-10s) %(message)s",
            "%y-%m-%d %H:%M"
        ))

        # Add to root logger
        self.root.addHandler(handler)

        # Store it so you can manage/remove later
        self.gui_handlers.append(handler)

    def start_gui_update_thread(self, killer_event):
        if self.update_thread is None:
            self.update_thread = Log_Update(killer_event)
            self.update_thread.start()

    def _setup_file_handler(self):
        fh = logging.FileHandler(self.log_file, mode="a", encoding="utf-8")
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(logging.Formatter(
            "%(asctime)s [%(levelname)s] (%(threadName)-10s) %(message)s",
            "%y-%m-%d %H:%M:%S"
        ))
        self.root.addHandler(fh)

    def _setup_queue_handler(self):
        qh = QueueHandler(self.log_queue)
        qh.setLevel(logging.DEBUG)
        qh.setFormatter(logging.Formatter(
            "%(asctime)s [%(levelname)s] (%(threadName)-10s) %(message)s",
            "%y-%m-%d %H:%M"
        ))
        self.root.addHandler(qh)

    def get_logger(self, name):
        return logging.getLogger(name)

'''
# How to use it
LM = LoggerManager(log_file)
LM.start_gui_update_thread(killer_event)

log = LM.get_logger("main")
log.info("Application started")

'''

class QueueHandler(logging.Handler):
    """Class to send logging records to a queue
    It can be used from different threads
    The ConsoleUi class polls this queue to display records in a ScrolledText widget
    """
    # Example from Moshe Kaplan: https://gist.github.com/moshekaplan/c425f861de7bbf28ef06
    # (https://stackoverflow.com/questions/13318742/python-logging-to-tkinter-text-widget) is not thread safe!
    # See https://stackoverflow.com/questions/43909849/tkinter-python-crashes-on-new-thread-trying-to-log-on-main-thread

    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record):
        self.log_queue.put(self.format(record))

class ConsolePanelHandler(logging.Handler):    
    def __init__(self, parent):
        logging.Handler.__init__(self)
        self.parent = parent

    def emit(self, record):
        self.parent.write_GUI_Log(self.format(record))
        #self.ui.write_GUI_Log(self.format(record))
        #self.textedit.append(self.format(record))

class ToFileLogger:
    def __init__(self, name):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)

        stream_handler = logging.StreamHandler(sys.stderr)
        formatter = logging.Formatter(
            "[%(asctime)s][%(levelname)s] (%(threadName)-10s) %(message)s", "%Y-%m-%d %H:%M:%S"
        )
        stream_handler.setFormatter(formatter)

        stream_handler.setLevel(logging.DEBUG)
        self.logger.addHandler(stream_handler)
        # self.logger.propagate = False

class Log_Update(threading.Thread):
    def __init__(self,killer_event):
        threading.Thread.__init__(self, name="Log Update")
        #log.info("Log Update Started")
        self.killer_event=killer_event
        self.cycle_time=0.1
        self.ST=class_ST.SignalTracker()    
    def run(self):    
        print('Logging Thread initialized')                       
        while not self.killer_event.wait(self.cycle_time):   
            self.ST.Log_Update()
        print('Logging Thread Exit')  
    def quit(self):
        print('quit received')                                   
        self.killer_event.set()                      

def get_appPath():
    # determine if application is a script file or frozen exe
    if getattr(sys, 'frozen', False):
        application_path = os.path.dirname(sys.executable)
    elif __file__:
        application_path = os.path.dirname(__file__)
    return application_path