import logging
import queue
import threading
import class_ST
import os
import sys


'''
# set up logging to file - see previous section for more details
log = logging.getLogger('') #root logger
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s [%(levelname)s] (%(threadName)-10s) %(message)s',
                    datefmt='%y-%m-%d %H:%M',
                    filename='/temp/__last_run__.log',
                    filemode='w')
# define a Handler which writes INFO messages or higher to the sys.stderr
console = logging.StreamHandler()
console.setLevel(logging.INFO)
# set a format which is simpler for console use
formatter = logging.Formatter('[%(levelname)s] (%(threadName)-10s) %(message)s')
# tell the handler to use this format
console.setFormatter(formatter)
# add the handler to the root logger
logging.getLogger('').addHandler(console)
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